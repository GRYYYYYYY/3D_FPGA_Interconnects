"""One routing process across independently validated STA feedback epochs."""
import os
from pathlib import Path
import select
import signal
import subprocess
import time


def quoted_path(path):
    value = str(Path(path).resolve())
    if '\n' in value or '\r' in value:
        raise ValueError('Newlines are not supported in session paths')
    return '"'+value.replace('\\', '\\\\').replace('"', '\\"')+'"'


class TargetSession:
    def __init__(self, command, directory, env):
        self.command = list(map(str, command))+['--session', '1']
        self.started = time.perf_counter()
        self.log = (Path(directory)/'session.log').open('w')
        try:
            self.process = subprocess.Popen(self.command, cwd=directory, env=env,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.log, start_new_session=True)
        except Exception:
            self.log.close(); raise
        self.buffer = b''
        self.epoch = 0

    def _terminate_child(self):
        # This is the owned router subprocess's declared timeout, not a platform
        # job cancellation. Preserve its files and the enclosing experiment.
        if self.process.poll() is None:
            os.killpg(self.process.pid, signal.SIGTERM)
            try: self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(self.process.pid, signal.SIGKILL); self.process.wait()

    def wait_checkpoint(self, timeout, started=None, session_command=None):
        started = self.started if started is None else started
        record = dict(command=self.command, session_command=session_command,
                      session_pid=self.process.pid, process_kind='persistent_checkpoint',
                      timeout_seconds=timeout, checkpoint_code=None, returncode=None)
        deadline = started+timeout
        while True:
            if b'\n' in self.buffer:
                line, self.buffer = self.buffer.split(b'\n', 1)
                fields = line.decode().split()
                if len(fields) != 3 or fields[0] != 'TARGET_READY' or int(fields[1]) != self.epoch or fields[2] not in ('0', '1'):
                    raise ValueError('Invalid routing checkpoint acknowledgement: '+repr(line))
                record.update(status='completed', checkpoint_code=0 if fields[2]=='1' else 2)
                break
            remaining = deadline-time.perf_counter()
            if remaining <= 0:
                self._terminate_child(); record.update(status='timeout', returncode=self.process.returncode); break
            ready, _, _ = select.select([self.process.stdout], [], [], remaining)
            if not ready: continue
            chunk = os.read(self.process.stdout.fileno(), 4096)
            if not chunk:
                record.update(status='failed', returncode=self.process.wait()); break
            self.buffer += chunk
        record['process_seconds'] = time.perf_counter()-started
        return record

    def refine(self, criticalities, output, timeout, threshold=700, max_connections=2048, mode='legal'):
        if mode not in ('legal','negotiate'):raise ValueError('Invalid refinement mode')
        command = f'REFINE {quoted_path(criticalities)} {quoted_path(output)} {threshold} {max_connections}'
        if mode!='legal':command+=' '+mode
        started = time.perf_counter(); self.epoch += 1
        try:
            self.process.stdin.write((command+'\n').encode()); self.process.stdin.flush()
        except BrokenPipeError:
            pass  # wait_checkpoint records the actual exit without an ACK
        return self.wait_checkpoint(timeout, started, command)

    def close(self):
        try:
            if self.process.poll() is None:
                try:
                    self.process.stdin.write(b'STOP\n'); self.process.stdin.flush()
                except BrokenPipeError:
                    pass
                try: self.process.wait(timeout=10)
                except subprocess.TimeoutExpired: self._terminate_child()
            return dict(returncode=self.process.returncode,
                        status='completed' if self.process.returncode==0 else 'failed')
        finally:
            self.process.stdin.close(); self.process.stdout.close(); self.log.close()

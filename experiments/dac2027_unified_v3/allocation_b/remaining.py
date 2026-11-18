"""Execute the LSTM cells skipped by the original per-workload routing gate."""
import ctypes
import fcntl
import os
from pathlib import Path
import signal
import socket
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import worker


def complete():
    run = worker.run
    env = worker.envrec
    assert env['host'] == socket.gethostname()
    assert env['boot'] == Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    assert worker.read(run/'finished.json')['eligible'] == ['bnn', 'gemm']
    gate = worker.read(run/'qualification/lstm/gate.json')
    assert gate == dict(routes=False, strict_map=True, alt_map=True, complete_capture=True, cpu_verify=True)
    assert worker.read(run/'qualification/lstm/0/stock/record.json')['returncode'] == -11
    with (run/'formal.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert worker.digest(worker.__file__) == worker.read(run/'protocol.json')['worker_sha256']
        os.sched_setaffinity(0, env['cpus'])
        mask = ctypes.c_ulong(1)
        libc = ctypes.CDLL(None, use_errno=True)
        if libc.syscall(238, 2, ctypes.byref(mask), 64) != 0:
            raise OSError(ctypes.get_errno(), 'could not bind memory to NUMA 0')
        uuid = env['gpu'].split(',')[0]
        assert worker.gpu(['--query-gpu=uuid']) == uuid
        assert Path('/sys/fs/cgroup/cpu.max').read_text().strip() == env['cpu_max']
        assert Path('/sys/fs/cgroup/memory.max').read_text().strip() == env['memory_max']
        os.environ['CUDA_VISIBLE_DEVICES'] = uuid
        signal.signal(signal.SIGALRM, lambda *_: sys.exit('allocation deadline'))
        signal.alarm(max(1, int((worker.deadline - worker.utc()).total_seconds())))
        note = dict(host=socket.gethostname(), gpu=uuid, start=worker.utc().isoformat(),
                    cpus=sorted(os.sched_getaffinity(0)), memory_policy=env['memory_policy'],
                    before=worker.snapshot(), reason='LSTM Stock qualification failed after producing the native map')
        worker.save(run/'lstm_continuation.json', note)
        for family in (worker.full, worker.controls):
            for repeat in range(3):
                offset = repeat % len(family)
                for arm in family[offset:] + family[:offset]:
                    d = run/'formal/lstm'/str(repeat)/arm
                    if not d.exists():
                        worker.launch('lstm', arm, 'formal', repeat)
                    elif not (d/'record.json').is_file():
                        raise RuntimeError(f'Interrupted invocation retained at {d}')
        for record in sorted((run/'formal/lstm').glob('*/*/record.json')):
            d = record.parent
            if not (d/'readback/record.json').is_file():
                worker.readback(d)
        note['finished'] = worker.utc().isoformat()
        note['formal_records'] = len(list((run/'formal/lstm').glob('*/*/record.json')))
        worker.save(run/'lstm_continuation.json', note)


if __name__ == '__main__':
    complete()

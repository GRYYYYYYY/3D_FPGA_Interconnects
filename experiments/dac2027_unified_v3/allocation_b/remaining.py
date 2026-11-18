"""Execute the LSTM cells skipped by the original per-workload routing gate."""
import ctypes
import fcntl
import os
from pathlib import Path
import shutil
import signal
import socket
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import worker


def verify_original_stock(run):
    # A separate, untimed qualification with the original executable checks whether
    # this worker also sees a downstream routing failure without the E2 wrapper.
    directory = run/'diagnostic/lstm_original_stock'
    if (directory/'record.json').is_file():
        return
    directory.mkdir(parents=True, exist_ok=False)
    original = worker.bins['stock']
    assert worker.digest(original['path']) == original['sha256']
    timed_directory = run/'qualification/lstm/0/stock'
    invocation = worker.read(timed_directory/'invocation.json')
    args = invocation['command'].copy()
    args[0] = original['path']
    for flag in ('--net_file','--place_file','--route_file','--write_router_lookahead'):
        index = args.index(flag) + 1
        assert Path(args[index]).parent == timed_directory
        args[index] = str(directory/Path(args[index]).name)
    inputs = worker.cases['lstm']['inputs']
    for role, name in [('packed_netlist','packed.net'),('placement','fixed.place')]:
        shutil.copyfile(inputs[role]['path'], directory/name)
    for item in inputs.values():
        with open(item['path'],'rb') as stream:
            while stream.read(8 << 20):
                pass
    env = worker.environment('stock',directory,False)
    diagnostic = dict(case='lstm',arm='stock',phase='untimed_diagnostic',host=socket.gethostname(),
                      command=args,source_binary=original, before=worker.snapshot(),
                      purpose='Uninstrumented downstream route and native map qualification')
    worker.save(directory/'invocation.json',diagnostic)
    result, _ = worker.execute(args,directory,env)
    diagnostic.update(result, after=worker.snapshot())
    for key, filename in [('route_sha256','routed.route'),('map_sha256','wire_map.bin')]:
        path=directory/filename
        diagnostic[key] = worker.digest(path) if path.is_file() else None
    diagnostic['matches_archived_map'] = diagnostic['map_sha256'] == worker.gold['lstm']['strict']
    worker.save(directory/'record.json',diagnostic)
    worker.readback(directory)


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
        verify_original_stock(run)
        note['finished'] = worker.utc().isoformat()
        note['formal_records'] = len(list((run/'formal/lstm').glob('*/*/record.json')))
        worker.save(run/'lstm_continuation.json', note)


if __name__ == '__main__':
    complete()

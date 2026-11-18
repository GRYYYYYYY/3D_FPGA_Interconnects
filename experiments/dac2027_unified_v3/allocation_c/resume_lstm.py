"""Resume the unstarted LSTM formal cells from the frozen allocation B records."""
import csv
import fcntl
import os
from pathlib import Path
import signal
import socket
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import worker
from allocation_b.remaining import verify_original_stock


def verify_checkpoint():
    frozen = worker.here.parents[2]/'3D_FPGA_Interconnects_EXPERIMENT_V3'/worker.here.relative_to(worker.repo)
    previous = frozen/'allocation_b'
    verification = worker.read(previous/'audit/verification.json')
    assert verification['formal_records'] == 36 and verification['independently_passed_routes'] == 47
    assert not verification['missing_readbacks']
    gate = verification['cases']['lstm']['qualification']
    assert all(gate[k] for k in ('strict_map','alt_map','complete_capture','cpu_verify'))
    assert verification['cases']['lstm']['formal'] == 0
    qualification = previous/'run/qualification/lstm/0'
    with (previous/'audit/qualification.csv').open() as stream:
        bindings = {r['arm']:r for r in csv.DictReader(stream) if r['case']=='lstm'}
    for arm in worker.full:
        assert worker.digest(qualification/arm/'record.json') == bindings[arm]['record_sha256']
    timer_hashes = worker.read(frozen/'audit/timer_build.json')
    for path, expected in timer_hashes.items():
        assert worker.digest(path) == expected, path
    for rel in ('worker.py','cases.json','golden_maps.json'):
        assert worker.digest(frozen/rel) == worker.digest(worker.here/rel), rel
    for rel in ('scripts/scaling_common.py','scripts/report_native_joint.py'):
        assert worker.digest(frozen.parents[1]/rel) == worker.digest(worker.repo/rel), rel
    with (frozen/'audit/bindings.csv').open() as stream:
        for row in csv.DictReader(stream):
            if not row['role'].startswith(('bnn.','gemm.')):
                assert worker.digest(row['file']) == row['expected'], row['file']
    receipt = dict(parent_experiment='671a31e1c9fd18d2242a5c32c4d53ac5f50ec992',
                   parent_job='job-689b8169-b778-4c53-85e2-794f910f020e',
                   parent_proof_sha256=worker.digest(previous/'audit/verification.json'),
                   lstm_qualification=gate, qualification_records=bindings,
                   input_manifest_sha256=worker.digest(worker.here/'cases.json'),
                   worker_sha256=worker.digest(worker.here/'worker.py'), binaries=timer_hashes,
                   initially_pending=18)
    worker.save(worker.run/'checkpoint.json', receipt)
    return qualification


def main():
    run = worker.run
    with (run/'formal.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert worker.envrec['host'] == socket.gethostname()
        assert sorted(os.sched_getaffinity(0)) == worker.envrec['cpus']
        signal.signal(signal.SIGALRM, lambda *_: sys.exit('allocation deadline'))
        signal.alarm(max(1, int((worker.deadline - worker.utc()).total_seconds())))
        qualification = verify_checkpoint()
        print('LSTM checkpoint and run bindings verified', flush=True)
        for family in (worker.full, worker.controls):
            for repeat in range(3):
                offset = repeat % len(family)
                for arm in family[offset:] + family[:offset]:
                    worker.launch('lstm', arm, 'formal', repeat)
        for p in sorted((run/'formal/lstm').glob('*/*/record.json')):
            worker.readback(p.parent)
        verify_original_stock(run, qualification/'stock')
        worker.save(run/'finished.json', dict(utc=worker.utc().isoformat(), eligible=['lstm']))


if __name__ == '__main__':
    main()

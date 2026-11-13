"""Resume only unstarted tests after the precisely diagnosed missing-argv bug.

Never changes an original pipeline receipt or restarts a build/native batch.
Waiting observes an already running pipeline; any other failure stops recovery.
"""
from pathlib import Path
import datetime, hashlib, json, subprocess, sys, time

root = Path(__file__).resolve().parents[4]
s = root / 'accel/lookahead/fpga_sparse_stream_r2'
r = root / 'results/fpga_sparse_stream_r2_20261112'
variant = sys.argv[1]
original = r / 'rtl' / (variant + '_pipeline_receipt.json')
out = r / 'rtl' / (variant + '_boundary_resume_0209.json')
if out.exists():
    raise RuntimeError('append-only recovery already exists')
state = dict(variant=variant, status='waiting_for_original_pipeline', steps=[],
             started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
def save():
    out.write_text(json.dumps(state, indent=2) + '\n')
save()
try:
    while True:
        try:
            prior = json.loads(original.read_text())
        except json.JSONDecodeError:
            time.sleep(5)
            continue
        if prior['status'] != 'running':
            break
        time.sleep(5)
    steps = prior['steps']
    assert prior['status'] == 'failed' and len(steps) == 9
    assert all(x['returncode'] == 0 for x in steps[:8])
    cmd = steps[-1]['command']
    assert len(cmd) == 3 and Path(cmd[1]) == s / 'tests/many_hot_capacity.py' and cmd[2] == variant
    assert steps[-1]['returncode'] != 0
    assert 'ValueError: not enough values to unpack (expected 2, got 1)' in original.with_suffix('.log').read_text()
    assert not (r / 'rtl' / (variant + '_hot_capacity8192')).exists()
    model = prior['model']
    assert not (r / 'model' / model / ('boundary_calibration_' + variant)).exists()
    state.update(status='running_missing_tail_only', model=model,
                 original_receipt_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),
                 original_failure='missing model argv; no capacity DUT run occurred',
                 completed_build_and_first8_steps_reused=True)
    save()
    commands = [
        [sys.executable, str(s / 'tests/many_hot_capacity.py'), variant, model],
        [sys.executable, str(s / 'sim/calibrate_many_boundaries.py'), model, variant],
    ]
    with out.with_suffix('.log').open('w') as log:
        for command in commands:
            rc = subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT).returncode
            state['steps'].append(dict(command=command, returncode=rc))
            save()
            if rc:
                raise RuntimeError('resumed boundary test failed; no automatic retry')
    state['status'] = 'passed'
except Exception as e:
    state['status'] = 'failed'
    state['error'] = str(e)
    raise
finally:
    state['ended_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    save()
print('BOUNDARY_RESUME', variant, state['status'])

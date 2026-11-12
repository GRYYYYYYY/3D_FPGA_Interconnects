"""Wait for both real native batches, then run the complete-work audit.

Elapsed time and partial progress never satisfy this gate. It does not restart
models, alter workload parameters, qualify clocks or write to external services.
"""
from pathlib import Path
import datetime, json, subprocess, sys, time

root = Path(__file__).resolve().parents[4]
r = root / 'results/fpga_sparse_stream_r2_20261112'
model, tag, output = sys.argv[1:4]
directory = r / 'model' / model / tag
receipt = directory / 'work_audit_gate.json'
if receipt.exists():
    raise RuntimeError('audit gate already exists; inspect before resuming')
state = {'model': model, 'run': tag, 'status': 'waiting_for_both_complete_batches',
         'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}

def save():
    receipt.write_text(json.dumps(state, indent=2) + '\n')

save()
while True:
    runs = [json.loads((directory / case / 'receipt.json').read_text())
            for case in ['bnn_export', 'lstm_s2']]
    if any(x['status'].startswith('failed') for x in runs):
        state['status'] = 'failed_batch_producer'
        save()
        sys.exit(1)
    if all(x['status'] == 'passed' and x.get('returncode') == 0 for x in runs):
        break
    time.sleep(5)
cmd = [sys.executable, str(Path(__file__).with_name('audit_complete_work.py')),
       output, '8192', '8192'] + [
           f'model/{model}/{tag}/{case}={case}' for case in ['bnn_export', 'lstm_s2']]
state.update(status='auditing_complete_work', command=cmd)
save()
with (directory / 'complete_work_audit.log').open('w') as log:
    rc = subprocess.run(cmd, cwd=root, stdout=log, stderr=subprocess.STDOUT).returncode
state.update(status='passed' if rc == 0 else 'failed_audit', returncode=rc,
             ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
save()
print(model, tag, state['status'], flush=True)
sys.exit(rc)

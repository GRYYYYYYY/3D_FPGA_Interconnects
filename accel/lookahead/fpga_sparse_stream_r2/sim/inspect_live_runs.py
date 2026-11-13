"""Read-only recovery/status view. A live receipt is never a completed result."""
from pathlib import Path
import datetime, json, sys

root = Path(__file__).resolve().parents[4]
r = root / 'results/fpga_sparse_stream_r2_20261112'
checkpoint = json.loads((r / 'checkpoint.json').read_text())
result = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'complete_batches': [], 'active_OOC': [], 'recent_calibrations': []}
for receipt in sorted((r / 'model').glob('*/large*/*/receipt.json')):
    x = json.loads(receipt.read_text())
    proc = Path('/proc') / str(x.get('pid', 0)) / 'cmdline'
    try:
        live = str(x['command'][0]).encode() in proc.read_bytes().split(b'\0')
    except OSError:
        live = False
    p = receipt.parent / 'progress.json'
    try:
        progress = json.loads(p.read_text()) if p.exists() else None
    except json.JSONDecodeError:
        progress = {'status': 'writer in progress; retry next observation'}
    result['complete_batches'].append({'run': str(receipt.parent.relative_to(r)),
        'recorded_status': x['status'], 'process_alive_and_executable_matches': live,
        'progress_is_not_performance_result': progress,
        'output_sha256': x.get('output_sha256')})
jobs = checkpoint.get('active_physical_jobs')
sessions = ({name: job['session'] for name, job in jobs.items()} if jobs is not None
            else checkpoint['vivado_sessions'])
for version, session in sessions.items():
    p = r / 'timing' / version
    run_name = jobs[version].get('implementation_run', 'impl_1') if jobs is not None else 'impl_1'
    runs = list(p.glob('project/*.runs/' + run_name + '/runme.log')) or list(p.glob('project/*.runs/synth_1/runme.log'))
    for log in runs:
        with log.open('rb') as f:
            f.seek(max(0, log.stat().st_size - 32768))
            tail = f.read().decode(errors='replace')
        sta = {str(x.relative_to(p)): x.read_text() for x in p.glob('routed_sta*/tested_periods.csv')}
        result['active_OOC'].append({'version': version, 'MCP_session': session,
            'stage': log.parent.name, 'end_marker_observed': 'Exiting Vivado' in tail,
            'error_marker_observed': (log.parent / '.vivado.error.rst').exists(),
            'tail': '\n'.join(tail.splitlines()[-3:]),
            'STA_pending_review': sta})
for f in sorted((r / 'model').glob('*/*calibration*/calibration.json')):
    x = json.loads(f.read_text())
    result['recent_calibrations'].append({'path': str(f.relative_to(r)),
        'all_pass': x.get('all_pass'), 'cases': len(x.get('results', []))})
if len(sys.argv) > 1:
    out = r / 'supervision' / sys.argv[1]
    out.parent.mkdir(exist_ok=True)
    if out.exists():
        raise RuntimeError('append-only status artifact already exists')
    out.write_text(json.dumps(result, indent=2) + '\n')
for x in result['complete_batches']:
    q = x['progress_is_not_performance_result'] or {}
    print('BATCH', x['run'], x['recorded_status'], 'live=' + str(x['process_alive_and_executable_matches']),
          'qid=' + str(q.get('sample')), 'cycles=' + str(q.get('cycles')))
for x in result['active_OOC']:
    print('OOC', x['version'], x['stage'], 'ended=' + str(x['end_marker_observed']),
          'error=' + str(x['error_marker_observed']), x['tail'].replace('\n', ' | '))
print('CALIBRATIONS', len(result['recent_calibrations']),
      'all_pass=' + str(all(x['all_pass'] for x in result['recent_calibrations'])))

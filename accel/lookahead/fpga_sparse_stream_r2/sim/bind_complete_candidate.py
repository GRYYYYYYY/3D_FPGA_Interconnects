"""Bind complete native model results to one exact, calibrated physical kernel.

Missing routed qualification leaves seconds null. A unit/prototype clock, a
different executable or a different native output can never supply that clock.
All inputs are existing evidence; this script launches no experiment.
"""
from pathlib import Path
import argparse, datetime, hashlib, json, re

root = Path(__file__).resolve().parents[4]
r = root / 'results/fpga_sparse_stream_r2_20261112'
p = argparse.ArgumentParser()
p.add_argument('output', help='new JSON below analysis/')
for name in ['rtl', 'model', 'calibration', 'ooc', 'binding']:
    p.add_argument('--' + name, required=True)
p.add_argument('--work-audit', action='append', required=True)
p.add_argument('--native-binding', action='append', required=True)
a = p.parse_args()
out = r / 'analysis' / a.output
if out.exists():
    raise RuntimeError('append-only output already exists')
hashes = {}

def digest(f):
    h = hashlib.sha256()
    with f.open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()

def read(rel):
    f = r / rel
    hashes[str(rel)] = digest(f)
    return json.loads(f.read_text())

def require(ok, reason):
    if not ok:
        raise RuntimeError(reason)

bindings = read(a.binding)
bound = [b for b in bindings['bindings'] if b['RTL'] == a.rtl and b['OOC'] == a.ooc]
require(bindings['all_pass'] and len(bound) == 1 and bound[0]['all_pass'], 'no exact RTL/OOC binding')
params = bound[0]['effective_RTL_parameters']
require(params['L'] in [32, 64], 'small prototype cannot qualify complete native candidate')
require(params == bound[0]['effective_physical_parameters'], 'physical parameter mismatch')
for folder in [Path('rtl') / (a.rtl + '_build'), Path('timing') / a.ooc]:
    b = read(folder / 'source_binding.json')
    for name, expected in b['source_sha256'].items():
        if name.endswith('.sv'):
            require(digest(r / folder / 'source' / name) == expected, 'modified frozen RTL: ' + name)

mp = Path('model') / a.model
mb = read(mp / 'source_binding.json')
macros = dict(arg[2:].split('=', 1) for arg in mb['command'] if arg.startswith('-D') and '=' in arg)
for macro, param in [('TILE_L', 'L'), ('TILE_P', 'PHYS'), ('TILE_MC', 'MEMBER_CAP'),
                     ('TILE_CC', 'CHANGED_LIMIT'), ('TILE_CACHE', 'CACHE_ENABLE'),
                     ('R2_REQUEST_STAGE', 'REQUEST_STAGE')]:
    require(int(macros[macro]) == params[param], 'model/RTL parameter mismatch: ' + param)
for name, expected in mb['source_sha256'].items():
    require(digest(r / mp / 'source' / name) == expected, 'modified frozen model source: ' + name)
exe = digest(r / mp / 'model')
cal_path = str(mp / a.calibration / 'calibration.json')
cal = read(cal_path)
require(cal['all_pass'] and cal['expected_cases'] == len(cal['results']) == 97,
        'complete97 calibration missing/failed')
require(cal['model_executable_sha256'] == exe, 'calibrated executable differs')
for row in cal['results']:
    require(row['cycle_log_exact'] and row['outputs_exact'] and row['all_traffic_histogram_phase_summary_exact'],
            'incomplete calibration comparison')
    require(Path(row['reference']).relative_to(r / 'rtl').parts[0].startswith(a.rtl + '_'),
            'calibration belongs to another RTL')
fixed_path = 'rtl/' + a.rtl + '_fixed_time/calibration.json'
fixed = read(fixed_path)
require(fixed['all_pass'] and fixed['cases'] == len(fixed['results']) == 36, 'fixed-time36 calibration missing/failed')
for row in fixed['results']:
    require(row['all_pass'] and row['results'][1]['executable_sha256'] == exe, 'fixed-time model differs')
boundary = read(mp / ('boundary_calibration_' + a.rtl) / 'calibration.json')
require(boundary['all_pass'] and len(boundary['results']) == 4 and boundary['executable_sha256'] == exe,
        'complete capacity/batch calibration missing/failed')
require(all(x['passed'] and x['cycle_log_exact'] for x in boundary['results']), 'capacity/batch comparison failed')

qualified = False
period = None
qpath = 'timing/' + a.ooc + '/routed_sta_v2/qualification_review.json'
if (r / qpath).is_file():
    q = read(qpath)
    require(q['functional_calibration_97'] == cal_path and q['fixed_ns_calibration_36'] == fixed_path,
            'clock review does not bind exact functional calibration')
    require(q['scope_binding'] == a.binding, 'clock review binding differs')
    require(min(q['setup_slack_ns'], q['hold_slack_ns'], q['pulse_width_slack_ns']) >= 0,
            'negative timing slack')
    require(q['check_timing_all_zero'] and q['route_errors'] == 0 and q['routable_nets'] > 0,
            'incomplete physical review')
    for rel, expected in q['evidence_sha256'].items():
        f = r / 'timing' / a.ooc / rel
        if not f.exists():
            f = r / rel
        require(digest(f) == expected, 'changed physical qualification evidence: ' + rel)
    period = q['period_ns']
    require(period > 0 and abs(q['qualified_OOC_mhz'] * period - 1000) < 1e-8,
            'inconsistent qualified clock')
    qualified = True

native = {}
for f in a.native_binding:
    b = read(f)
    require(b['all_pass'], 'native ALT identity failed')
    native.update({x['run']: x for x in b['results'] if x['all_pass']})
rows = []
for f in a.work_audit:
    w = read(f)
    require(w['all_pass'], 'complete work/capacity audit failed')
    for x in w['results']:
        run = Path(x['run'])
        require(run.parts[:2] == ('model', a.model), 'work audit belongs to another model')
        s = read(run / 'summary.json')
        receipt = read(run / 'receipt.json')
        require(receipt['status'] == 'passed' and receipt['returncode'] == 0, 'incomplete native batch')
        require(receipt['executable_sha256'] == exe, 'native executable differs from calibrated model')
        require(digest(r / run / 'summary.json') == x['summary_sha256'], 'native summary changed after audit')
        require(s['jobs'] == 40 and s['batch_starts'] == 1 and s['all_outputs_exact'], 'not one complete native40 batch')
        require(str(run) in native and native[str(run)]['output_sha256'] == x['output_sha256']
                == digest(r / run / 'output.bin'), 'native ALT output identity missing/different')
        require(not (r / run / 'physical_time_contract.json').exists(),
                'fixed-nanosecond native run requires its explicit time-contract binding')
        rows.append({'run': str(run), 'case': run.name, 'resident_cycles': s['resident_cycles'],
                     'simulated_resident_seconds': s['resident_cycles'] * period * 1e-9 if qualified else None,
                     'memory_base_latency_cycles': s['latency_cycles'],
                     'memory_base_latency_ns': s['latency_cycles'] * period if qualified else None,
                     'memory_min_gap_cycles': s['service_gap_cycles'],
                     'memory_min_gap_ns': s['service_gap_cycles'] * period if qualified else None,
                     'memory_jitter_cycles': [0, 12],
                     'memory_jitter_ns': [0, 12 * period] if qualified else None,
                     'memory_seed': s['seed'], 'output_sha256': x['output_sha256'],
                     'full_work_capacity_ACK_audit': f})
result = {'updated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'RTL': a.rtl, 'model': a.model, 'OOC': a.ooc, 'parameters': params,
          'complete97_fixed36_boundaries4_calibrated': True,
          'complete_kernel_clock_qualified': qualified, 'qualified_period_ns': period,
          'qualified_clock_mhz': 1000 / period if qualified else None,
          'main_seconds_publishable': qualified, 'rows': rows, 'evidence_sha256': hashes,
          'board_measured': False, 'shell_qualified': False,
          'memory_contract': 'hypothetical shared synchronous32B ports,64IDs/port,seeded6/7ready when gap/credit permit; latency/gap/jitter fixed in kernel cycles, no independent memory clock or CDC',
          'scope': 'RESIDENT_COMPLETE_BATCH_V2; simulated time only after exact full-kernel OOC qualification; no hardware measured speedup'}
out.write_text(json.dumps(result, indent=2) + '\n')
print('COMPLETE_CANDIDATE_BOUND', len(rows), 'qualified_clock', qualified)

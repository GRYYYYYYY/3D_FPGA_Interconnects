"""Wait for exact candidate gates, run complete batches, then audit and bind.

Usage: PLAN.json NEW_SUPERVISION_TAG [--check-only]
No timeout grants a pass. Check-only never creates or launches a batch. Failed
dependencies stop the plan; independent batches already launched are preserved.
"""
from pathlib import Path
import argparse
import concurrent.futures
import datetime
import hashlib
import json
import os
import subprocess
import sys
import threading
import time

root = Path(__file__).resolve().parents[4]
r = root / 'results/fpga_sparse_stream_r2_20261112'
scripts = Path(__file__).resolve().parent
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('plan')
ap.add_argument('tag')
ap.add_argument('--check-only', action='store_true')
args = ap.parse_args()
plan_path = Path(args.plan).resolve()
plan = json.loads(plan_path.read_text())
for value in [args.tag, plan['RTL'], plan['model'], plan['OOC'], plan['prefix'], plan['calibration']]:
    if Path(value).name != value or value in ['.', '..']:
        raise ValueError('local names required')
scenarios = [(int(x['latency_cycles']), int(x['gap_cycles'])) for x in plan['scenarios']]
assert scenarios and len(scenarios) == len(set(scenarios))
assert all(latency > 0 and gap > 0 for latency, gap in scenarios)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def gates():
    evidence = {}

    def read(rel):
        path = r / rel
        data = json.loads(path.read_text())
        evidence[str(rel)] = sha(path)
        return data

    try:
        pipeline = read('rtl/' + plan['RTL'] + '_pipeline_receipt.json')
        if pipeline['status'] == 'failed':
            raise RuntimeError('RTL validation dependency failed')
        if plan.get('extra_parent_receipt'):
            extra_parent = read(plan['extra_parent_receipt'])
            if extra_parent['status'] in ['failed', 'not_run_dependency_failed']:
                raise RuntimeError('extra fixed-time dependency failed')
        if pipeline['status'] != 'passed':
            return None
        assert pipeline['model'] == plan['model'] and pipeline['variant'] == plan['RTL'], 'pipeline/model/RTL identity mismatch'
        assert all(x['returncode'] == 0 for x in pipeline['steps'])
        context = read(plan['binding'])
        bound = [x for x in context['bindings'] if x['RTL'] == plan['RTL'] and x['OOC'] == plan['OOC']]
        assert context['all_pass'] and len(bound) == 1 and bound[0]['all_pass']
        params = bound[0]['effective_RTL_parameters']
        assert params == bound[0]['effective_physical_parameters']
        assert params['L'] == 32 and params['PHYS'] == 8
        for folder in [Path('rtl') / (plan['RTL'] + '_build'), Path('timing') / plan['OOC'],
                       Path('model') / plan['model']]:
            source = read(folder / 'source_binding.json')
            for name, digest in source['source_sha256'].items():
                assert sha(r / folder / 'source' / name) == digest, 'modified frozen source'
        model = Path('model') / plan['model']
        mb = read(model / 'source_binding.json')
        macros = dict(x[2:].split('=', 1) for x in mb['command'] if x.startswith('-D') and '=' in x)
        for macro, param in [('TILE_L', 'L'), ('TILE_P', 'PHYS'), ('TILE_MC', 'MEMBER_CAP'),
                             ('TILE_CC', 'CHANGED_LIMIT'), ('TILE_CACHE', 'CACHE_ENABLE'),
                             ('R2_REQUEST_STAGE', 'REQUEST_STAGE')]:
            assert int(macros[macro]) == params[param], 'model/RTL parameter mismatch: ' + param
        exe = sha(r / model / 'model')
        full = read(model / plan['calibration'] / 'calibration.json')
        assert full['all_pass'] and full['expected_cases'] == len(full['results']) == 97
        assert full['model_executable_sha256'] == exe
        assert all(x['cycle_log_exact'] and x['outputs_exact'] and x['all_traffic_histogram_phase_summary_exact'] for x in full['results'])
        for tag, count in [('fixed_time', 36), ('fixed_time_10ns_a', 18)]:
            fixed = read('rtl/' + plan['RTL'] + '_' + tag + '/calibration.json')
            assert fixed['all_pass'] and fixed['cases'] == len(fixed['results']) == count
            assert all(x['all_pass'] and x['results'][1]['executable_sha256'] == exe for x in fixed['results'])
        boundary = read(model / ('boundary_calibration_' + plan['RTL']) / 'calibration.json')
        assert boundary['all_pass'] and len(boundary['results']) == 4 and boundary['executable_sha256'] == exe
        assert all(x['passed'] and x['cycle_log_exact'] for x in boundary['results'])
        synth = read(plan['synthesis_review'])
        assert synth['resources_within_device_totals'] and synth['parent_wait_exit_code'] == 0
        assert synth['source_binding'] == plan['binding']
        for rel, digest in synth['evidence_sha256'].items():
            assert sha(r / 'timing' / plan['OOC'] / rel) == digest, 'modified synthesis evidence'
        return dict(evidence_sha256=evidence, parameters=params, executable_sha256=exe,
                    clock_qualification_not_required_for_cycle_simulation=True)
    except FileNotFoundError as error:
        pending = [
            'rtl/' + plan['RTL'] + '_pipeline_receipt.json', plan['binding'], plan['synthesis_review'],
            'model/' + plan['model'] + '/' + plan['calibration'] + '/calibration.json',
            'model/' + plan['model'] + '/boundary_calibration_' + plan['RTL'] + '/calibration.json',
            *['rtl/' + plan['RTL'] + '_' + tag + '/calibration.json'
              for tag in ['fixed_time', 'fixed_time_10ns_a']],
        ]
        if plan.get('extra_parent_receipt'):
            pending.append(plan['extra_parent_receipt'])
        if Path(error.filename).resolve() not in {(r / x).resolve() for x in pending}:
            raise
        return None
    except json.JSONDecodeError:
        return None


if args.check_only:
    checked = gates()
    print('GATES_PASS' if checked else 'GATES_PENDING')
    sys.exit(0 if checked else 2)

state_path = r / 'supervision' / (args.tag + '.json')
state = dict(status='waiting_candidate_gates', pid=os.getpid(), plan=plan,
             plan_path=str(plan_path), plan_sha256=sha(plan_path), launcher_sha256=sha(Path(__file__)),
             started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), runs={})
with state_path.open('x') as f:
    json.dump(state, f, indent=2)
lock = threading.Lock()


def save():
    tmp = state_path.with_suffix('.tmp')
    tmp.write_text(json.dumps(state, indent=2) + '\n')
    tmp.replace(state_path)


def execute(latency, gap):
    run = f'large_l{latency}_g{gap}'
    audit = f"complete_work_{plan['model']}_{run}.json"
    native = f"{plan['prefix']}_{run}_outputs_terminal.json"
    binding = f"{plan['prefix']}_{run}_bound_terminal.json"
    commands = [
        ['run_large_model.py', plan['model'], str(latency), str(gap)],
        ['audit_complete_work.py', audit, str(state['gates']['parameters']['MEMBER_CAP']),
         str(state['gates']['parameters']['CHANGED_LIMIT']),
         *[f"model/{plan['model']}/{run}/{case}={case}" for case in ['bnn_export', 'lstm_s2']]],
        ['audit_model_native_reuse.py', native, plan['model'] + '/' + run],
        ['bind_complete_candidate.py', binding, '--rtl', plan['RTL'], '--model', plan['model'],
         '--calibration', plan['calibration'], '--ooc', plan['OOC'], '--binding', plan['binding'],
         '--work-audit', 'analysis/' + audit, '--native-binding', 'baselines/native_reuse/' + native],
    ]
    for step, argv in enumerate(commands):
        cmd = [sys.executable, str(scripts / argv[0]), *argv[1:]]
        entry = dict(command=cmd, script_sha256=sha(scripts / argv[0]), returncode=None)
        with lock:
            state['runs'][run]['status'] = ['running_native', 'auditing_work', 'auditing_native', 'binding'][step]
            state['runs'][run]['steps'].append(entry)
            save()
        with (r / 'supervision' / f'{args.tag}_{run}_step{step}.log').open('x') as log:
            rc = subprocess.run(cmd, cwd=root, stdout=log, stderr=subprocess.STDOUT).returncode
        with lock:
            entry['returncode'] = rc
            if rc:
                state['runs'][run]['status'] = 'failed_step_' + str(step)
            save()
        if rc:
            return False
    with lock:
        state['runs'][run]['status'] = 'completed_audited_bound'
        state['runs'][run]['ended_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        save()
    print('NATIVE_PLAN_AUDITED_BOUND', run, flush=True)
    return True


try:
    while True:
        result = gates()
        if result:
            break
        time.sleep(30)
    for latency, gap in scenarios:
        run = f'large_l{latency}_g{gap}'
        assert not (r / 'model' / plan['model'] / run).exists(), 'existing native run; refusing duplicate'
        state['runs'][run] = {'status': 'ready', 'steps': []}
    state.update(status='running_validated_plan', gates=result)
    save()
    print('NATIVE_PLAN_GATES_PASSED', plan['model'], flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(scenarios)) as pool:
        passed = list(pool.map(lambda x: execute(*x), scenarios))
    state['status'] = 'completed_audited_bound' if all(passed) else 'failed_preserved'
except Exception as error:
    state['status'] = 'failed_preserved'
    state['error'] = repr(error)
state['ended_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
save()
sys.exit(state['status'] != 'completed_audited_bound')

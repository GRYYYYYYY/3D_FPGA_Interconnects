"""One serial-router feasibility diagnostic; immutable width120 inputs, no speed claim."""
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import resource
import shutil
import sys

from native_cpu_budget import audited_process, pin_budget
from prepare import sha256, write_json
from report_native_joint import log_evidence
from run_native_cpu_study import cpu_command, set_option
from run_native_hybrid import route_body
from scaling_common import metrics, verified, vpr_command, vpr_environment

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'results/native_cpu_width120_20261104'
OUT = ROOT/'results/native_lstm_width120_serial_20261104'


def read(path): return json.loads(Path(path).read_text())
def now(): return datetime.now(timezone.utc).isoformat()
def binding(path): return dict(path=str(Path(path).resolve()), sha256=sha256(path))


def freeze():
    assert read(BASE/'summary.json')['status'] == 'completed'
    assert read(BASE/'audit.json')['status'] == 'passed'
    OUT.mkdir(exist_ok=False)
    parent = read(BASE/'plan.json')
    case = read(BASE/'lstm_s1/vpr_case.json')
    command = cpu_command(parent['binaries']['cpu']['path'], case, OUT,
                          {'router': 'timing_driven'}, 1,
                          cache=BASE/'lstm_s1/wire_map.bin', iterations=200)
    set_option(command, '--write_router_lookahead', OUT/'wire_map.bin')
    files = ['diagnose_lstm_width120.py', 'native_cpu_budget.py', 'prepare.py',
             'report_native_joint.py', 'run_native_cpu_study.py', 'run_native_hybrid.py', 'scaling_common.py']
    plan = dict(status='frozen', created_utc=now(), command=command,
                source_summary=binding(BASE/'summary.json'), source_audit=binding(BASE/'audit.json'),
                case=binding(BASE/'lstm_s1/vpr_case.json'), cache=binding(BASE/'lstm_s1/wire_map.bin'),
                binaries=parent['binaries'], runtime=parent['runtime_binding'],
                runner_bindings={f: binding(ROOT/'scripts'/f) for f in files},
                cpu_pool=[32], workers=1, timeout_seconds=900, max_iterations=200,
                environment={'VPR_HYBRID_LOOKAHEAD_TASKS': '0', 'VPR_HYBRID_LOOKAHEAD_PARALLEL': '0'},
                scope='One serial native router with the same corrected ELF, fixed placement, width120 RR and wire cache. Wire cache still recomputes src/opin. No timing comparison to eight-core parallel routing.',
                interpretation='A legal run establishes existence of a route on this graph; failure is not proof of intrinsic unroutability. Neither outcome alone proves a parallel-state defect.',
                stop_policy='Exactly one attempt; retain numerical failure. No automatic retries, width escalation, or performance matrix.',
                default_changed=False, performance_claim=False)
    write_json(OUT/'plan.json', plan)
    print('Frozen one LSTM serial diagnostic', flush=True)


def run():
    plan = read(OUT/'plan.json')
    with (OUT/'owner.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (OUT/'summary.json').exists(): raise RuntimeError('Existing attempt; observe, never implicitly restart')
        bindings = list(plan['runner_bindings'].values()) + list(plan['binaries'].values())
        bindings += [plan[k] for k in ['source_summary', 'source_audit', 'case', 'cache', 'runtime']]
        for entry in bindings: verified(entry)
        case = read(verified(plan['case']))
        for entry in case['inputs'].values(): verified(entry)
        for role, name in [('packed_netlist', 'packed.net'), ('placement', 'fixed.place')]:
            shutil.copyfile(case['inputs'][role]['path'], OUT/name)
        assert shutil.disk_usage(OUT).free > 30*1024**3
        resource.setrlimit(resource.RLIMIT_AS, (64*1024**3, 64*1024**3))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        os.sched_setaffinity(0, plan['cpu_pool'])
        budget = pin_budget(1)
        env = {k: v for k, v in vpr_environment(read(plan['runtime']['path'])).items()
               if not k.startswith(('VPR_CPU_', 'VPR_HYBRID_', 'H3D_GPU_'))}
        env.update(plan['environment'])
        state = dict(status='running', pid=os.getpid(), started_utc=now(),
                     plan_binding=binding(OUT/'plan.json'), performance_claim=False, default_changed=False)
        row = dict(case='lstm_s1', success=False, status='running', cpu_budget=budget,
                   environment=plan['environment'], directory=str(OUT))
        state['measurement'] = row
        write_json(OUT/'summary.json', state)
        try:
            row.update(audited_process(plan['command'], OUT, env, 900))
            row.update(metrics((OUT/'process.log').read_text(errors='replace')))
            write_json(OUT/'measurement.json', row)
            row['log_evidence'] = log_evidence(OUT)
            row['wire_map_sha256'] = sha256(OUT/'wire_map.bin')
            assert row['wire_map_sha256'] == plan['cache']['sha256'], 'Cache mismatch'
            assert row['log_evidence']['stage_seconds']['lookahead_build'] is None, 'Unexpected wire rebuild'
            assert row['cpu_budget_audit']['verified'] and row['cpu_budget_audit']['permitted_cpu_set'] == [32]
            if row['returncode'] == 0 and row['routing_success'] and row['full_check']:
                assert row['log_evidence']['final_overused_nodes'] == 0
                row['route_sha256'] = sha256(OUT/'routed.route')
                row['route_body_sha256'] = route_body(OUT/'routed.route')
                command = vpr_command(plan['binaries']['original']['path'], case, OUT, 200, route=False)
                row['independent_check'] = audited_process(command, OUT, env, 900, 'independent_check.log')
                checked = metrics((OUT/'independent_check.log').read_text(errors='replace'))
                row['independent_metrics'] = checked
                row['success'] = bool(row['independent_check']['returncode'] == 0 and checked['full_check']
                    and row['independent_check']['cpu_budget_audit']['verified']
                    and all(checked[k] == row[k] for k in ['critical_path_ns', 'wirelength']))
                assert sha256(OUT/'routed.route') == row['route_sha256']
            for entry in bindings + list(case['inputs'].values()) + [state['plan_binding']]: verified(entry)
            for role, name in [('packed_netlist', 'packed.net'), ('placement', 'fixed.place')]:
                assert sha256(OUT/name) == case['inputs'][role]['sha256']
            write_json(OUT/'measurement.json', row)
            artifact_names = ['measurement.json', 'process.log', 'process.log.resources.json', 'wire_map.bin',
                              'routed.route', 'report_overused_nodes.rpt', 'independent_check.log', 'independent_check.log.resources.json']
            write_json(OUT/'audit.json', dict(status='passed', bindings={n: binding(OUT/n) for n in artifact_names if (OUT/n).exists()},
                scope='Frozen provenance, CPU affinity, cache identity and native/independent checks. Numerical failure remains a failure, not an audit failure.'))
            state['status'] = 'completed'
        except Exception as exc:
            state.update(status='stopped_for_review', error=repr(exc))
            raise
        finally:
            state['finished_utc'] = now()
            write_json(OUT/'measurement.json', row)
            write_json(OUT/'summary.json', state)
            print(json.dumps({k: row.get(k) for k in ['case', 'returncode', 'success', 'iterations', 'critical_path_ns', 'wirelength']}), flush=True)


if __name__ == '__main__':
    {'freeze': freeze, 'run': run}[sys.argv[1]]()

"""Run slice/storage/scheduler ablations through the frozen CPU study runner.

All process variants serialize a map and compare it to the original serial
qualification. Diagnostic lanes are explicitly marked and excluded from timing.
"""
import json
from pathlib import Path
import sys

from prepare import sha256, write_json
import run_native_cpu_study as study


def main():
    plan_path = Path(sys.argv[sys.argv.index('--plan') + 1])
    plan = json.loads(plan_path.read_text())
    base_process = study.audited_process
    expected = None

    def checked_process(command, directory, env, timeout, log_name='process.log'):
        nonlocal expected
        command = list(command)
        env = dict(env)
        is_process = log_name == 'process.log'
        selected = None
        if is_process:
            for variant_id, variant in plan['variants'].items():
                if any(directory.name.endswith('_' + variant_id + '_' + cache) for cache in ['rebuild', 'reuse']):
                    selected = variant
                    break
            if directory.name.endswith('_cache_optimized'):
                selected = {'env': plan.get('qualification_env', {})}
            if selected:
                env.update(selected.get('env', {}))
            if plan.get('diagnostics', False) and '_cache_' not in directory.name:
                env['VPR_CPU_TRACE'] = str(directory/'cpu_trace.jsonl')
                env['VPR_HYBRID_LOOKAHEAD_REPORT'] = str(directory/'lookahead_profile.jsonl')
            if '--write_router_lookahead' not in command:
                study.set_option(command, '--write_router_lookahead', directory/'wire_map.bin')
            map_path = Path(command[command.index('--write_router_lookahead') + 1])
        else:
            map_path = None
        outcome = base_process(command, directory, env, timeout, log_name)
        outcome['diagnostic_sample'] = bool(is_process and plan.get('diagnostics', False) and '_cache_' not in directory.name)
        outcome['candidate_environment'] = {k:v for k,v in env.items() if k.startswith(('VPR_CPU_', 'VPR_HYBRID_LOOKAHEAD'))}
        if map_path and map_path.exists():
            actual = sha256(map_path)
            if directory.name.endswith('_cache_original'):
                expected = actual
            outcome['wire_map_sha256'] = actual
            outcome['wire_map_matches_serial'] = actual == expected
            write_json(directory/'wire_map_check.json', {'sha256':actual, 'expected_sha256':expected,
                                                       'matches':actual==expected})
            if actual != expected:
                raise RuntimeError(f'Map differs from original serial: {directory}')
        return outcome

    study.audited_process = checked_process
    study.main()


if __name__ == '__main__':
    main()

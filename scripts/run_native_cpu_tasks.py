"""Qualify the bounded sample pipeline without altering frozen CPU controls.

All timed variants write the same map artifact, so serialization is symmetric.
Every emitted map must match the original serial qualification bytes, at every
core count. Profiling is enabled only during candidate cache qualification.
"""
import json
from pathlib import Path
import sys

from prepare import sha256, write_json
import run_native_cpu_study as study


def main():
    plan_path = Path(sys.argv[sys.argv.index('--plan') + 1])
    plan = json.loads(plan_path.read_text())
    candidate = Path(plan['binaries']['cpu']['path']).resolve()
    original = Path(plan['binaries']['original']['path']).resolve()
    base_process = study.audited_process
    expected = None

    def checked_process(command, directory, env, timeout, log_name='process.log'):
        nonlocal expected
        command = list(command)
        env = dict(env)
        task_mode = Path(command[0]).resolve() == candidate and env.get('VPR_HYBRID_LOOKAHEAD_PARALLEL') == '1'
        if task_mode:
            env['VPR_HYBRID_LOOKAHEAD_TASKS'] = '1'
            if directory.name.endswith('_cache_optimized'):
                env['VPR_HYBRID_LOOKAHEAD_REPORT'] = str(directory / 'pipeline_profile.jsonl')
        if log_name == 'process.log':
            if '--write_router_lookahead' not in command:
                study.set_option(command, '--write_router_lookahead', directory / 'wire_map.bin')
            map_path = Path(command[command.index('--write_router_lookahead') + 1])
        else:
            map_path = None
        outcome = base_process(command, directory, env, timeout, log_name)
        outcome['lookahead_scheduler'] = ('global_ordered_pipeline' if task_mode else
                                         'per_group_samples' if env.get('VPR_HYBRID_LOOKAHEAD_PARALLEL') == '1' else 'serial')
        if map_path and map_path.exists():
            actual = sha256(map_path)
            if directory.name.endswith('_cache_original') and Path(command[0]).resolve() == original:
                expected = actual
            outcome['wire_map_sha256'] = actual
            outcome['wire_map_matches_serial'] = actual == expected
            write_json(directory / 'wire_map_check.json', {'path': str(map_path), 'sha256': actual,
                                                         'expected_sha256': expected, 'matches': actual == expected})
            if actual != expected:
                raise RuntimeError(f'Pipeline map mismatch: {directory}')
        return outcome

    study.audited_process = checked_process
    study.main()


if __name__ == '__main__':
    main()

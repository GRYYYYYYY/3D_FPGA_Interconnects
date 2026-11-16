#!/usr/bin/env python3
"""Freeze and reuse the existing bounded dispatcher XSim regression unchanged."""
from pathlib import Path
import argparse, datetime, hashlib, json, os, subprocess, sys

CANDIDATE = Path(__file__).resolve().parent
DISPATCH = CANDIDATE.parent
ROOT = CANDIDATE.parents[4]
F_SHA = 'bf78b3d09ac0bd4ead802d1f4d7105a1119ad74bcd74f01c88a2e18c52eff7fb'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def dump(p, value):
    p.write_text(json.dumps(value, indent=2) + '\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('out', type=Path)
    args = ap.parse_args()
    assert sha(DISPATCH / 'cp_pop_dispatch_restructured.sv') == F_SHA
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    inputs = out / 'inputs'
    inputs.mkdir()
    stat = Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()
    dump(out / 'process_birth.json', {
        'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'pid': os.getpid(), 'start_ticks': int(stat[19]),
        'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        'argv': sys.argv, 'cwd': str(Path.cwd()),
        'owner': 'parent_cpu_primary_task', 'automatic_restart_queue': None,
    })
    names = ['cp_pop_dispatch.sv', 'run_restructured.py', 'run_lifecycle_miter.py',
             'tb_pop_dispatch_miter.sv', 'tb_dispatch_reject_miter.sv',
             'tb_dispatch_selectors.sv', 'tb_pop_dispatch.sv',
             'tb_dispatch_reject.sv', 'tb_dispatch_lifecycle_miter.sv']
    source_bindings = {}
    for name in names:
        src = DISPATCH / name
        (inputs / name).write_bytes(src.read_bytes())
        source_bindings[str(src.relative_to(ROOT))] = sha(src)
    variant = CANDIDATE / 'cp_pop_dispatch_restructured.sv'
    (inputs / variant.name).write_bytes(variant.read_bytes())
    source_bindings[str(variant.relative_to(ROOT))] = sha(variant)
    (out / 'run_local.py').write_bytes(Path(__file__).read_bytes())
    binding = {
        'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'backend': 'XSim2022.2', 'mode': 'behavioral',
        'prior_f_sha256': F_SHA, 'source': source_bindings,
        'runner_sha256': sha(Path(__file__)),
        'reference_scope': 'Existing original dispatcher reference and existing tests unchanged. Prior f passed the same reference miters. No direct formal f equivalence claim.',
        'clock_is_timing_proof': False,
        'commands': [],
    }
    dump(out / 'binding.json', binding)
    try:
        for driver, name in [('run_restructured.py', 'protocol_selectors'),
                             ('run_lifecycle_miter.py', 'lifecycle')]:
            cmd = [sys.executable, str(inputs / driver), str(out / name)]
            row = {'argv': cmd, 'cwd': str(ROOT),
                   'start_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
            binding['commands'].append(row)
            dump(out / 'binding.json', binding)
            print('RUN', name, flush=True)
            with (out / (name + '.log')).open('x') as log:
                result = subprocess.run(cmd, cwd=ROOT, stdout=log,
                                        stderr=subprocess.STDOUT, timeout=3600)
            row['returncode'] = result.returncode
            row['end_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            dump(out / 'binding.json', binding)
            assert result.returncode == 0, name
            terminal = json.loads((out / name / 'terminal.json').read_text())
            assert terminal['status'] == 'PASS', terminal
            print(name, 'PASS', flush=True)
        assert sha(DISPATCH / 'cp_pop_dispatch_restructured.sv') == F_SHA
        for name, digest in source_bindings.items():
            assert sha(ROOT / name) == digest, name
        dump(out / 'terminal.json', {
            'status': 'PASS', 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'all_sources_unchanged_during_run': True,
            'prior_f_source_unchanged': True,
            'formal_equivalence': False, 'timing_qualified': False,
            'subruns': ['protocol_selectors', 'lifecycle'],
        })
    except BaseException as exc:
        dump(out / 'failure.json', {'error': str(exc), 'commands': binding['commands']})
        raise


if __name__ == '__main__':
    main()

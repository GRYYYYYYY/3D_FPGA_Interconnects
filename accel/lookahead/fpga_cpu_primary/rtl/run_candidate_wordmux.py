"""Freeze and run the fixed-size candidate-only behavioral miter, XSim 2022.2.

Uses the existing dispatch/run_lifecycle_miter.py non-project command flow.
Refuses to reuse an output directory; preserves each command's raw transcript.
No synthesis, top integration, historical-source mutation or model execution.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess

HERE = Path(__file__).resolve().parent
BIN = Path('/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin')
ORIGINAL = '14ce8922c0c8de3c134fef34b5fa6f6a2519c218c99beac68e59625f7b07ab4f'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('out', type=Path)
    args = parser.parse_args()
    original = HERE.parent.parent / 'fpga_descriptor_front/services/df_rr_router.sv'
    network = HERE / 'cp_candidate_network.sv'
    assert sha(original) == ORIGINAL
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    local_names = ['cp_candidate_wordmux_router.sv', 'tb_candidate_wordmux_miter.sv',
                   'run_candidate_wordmux.py']
    sources = {name: HERE / name for name in local_names}
    # The current network is context only, not compiled into this router miter.
    # Snapshot/hash it and enforce the same before/after stability as other files.
    sources.update({'df_rr_router.sv': original, 'cp_candidate_network.sv': network})
    for name, path in sources.items():
        (out / name).write_bytes(path.read_bytes())
    (out / 'run.tcl').write_text('run all\nquit\n')
    seeds = [1103515245, 1, 2147483647]
    commands = [
        [str(BIN / 'xvlog'), '--sv', 'df_rr_router.sv',
         'cp_candidate_wordmux_router.sv', 'tb_candidate_wordmux_miter.sv'],
        [str(BIN / 'xelab'), 'tb_candidate_wordmux_miter', '-s', 'snapshot',
         '-mt', '2', '--timescale', '1ns/1ps'],
    ]
    commands += [[str(BIN / 'xsim'), 'snapshot', '-tclbatch', 'run.tcl',
                  '-testplusarg', f'SEED={seed}', '-log', f'xsim_seed_{seed}.log']
                 for seed in seeds]
    env = dict(os.environ, LD_PRELOAD='/lib/x86_64-linux-gnu/libudev.so.1')
    binding = {
        'start_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'tool': 'Vivado XSim 2022.2', 'mode': 'behavioral non-project',
        'source_sha256': {name: sha(path) for name, path in sources.items()},
        'context_only_not_compiled': ['cp_candidate_network.sv'],
        'commands': commands, 'seeds': seeds,
        'environment': {'LD_PRELOAD': env['LD_PRELOAD']},
        'stage_timeout_seconds': 600, 'testbench_watchdog_ns': 2000000,
        'scope': 'Fixed 64x64x96 router, reachable defined-valid protocol, '
                 'cycle miter plus independent cyclic scan scoreboard. '
                 'No formal, arbitrary-X, network/full-core or timing claim.',
    }
    save(out / 'binding.json', binding)
    markers = []
    warnings = []
    try:
        for index, command in enumerate(commands):
            log = out / f'stage_{index}.log'
            with log.open('w') as stream:
                subprocess.run(command, cwd=out, env=env, stdout=stream,
                               stderr=subprocess.STDOUT, check=True, timeout=600)
            transcript = log.read_text()
            assert not re.search(r'(?im)^(?:ERROR:|FATAL:|Fatal:)', transcript), log
            warnings.extend({'stage': index, 'line': line} for line in transcript.splitlines()
                            if 'WARNING' in line)
            if index >= 2:
                assert transcript.count('TEST_PASS tb_candidate_wordmux_miter') == 1, log
                rows = [line for line in transcript.splitlines()
                        if line.startswith(('COVERAGE ', 'MITER_EDGES ', 'TEST_PASS '))]
                markers.append({'seed': seeds[index - 2], 'markers': rows})
                print(rows, flush=True)
        for name, path in sources.items():
            assert sha(path) == binding['source_sha256'][name], name
        result = {
            'status': 'PASS', 'tests': markers, 'warnings': warnings,
            'source_hashes_unchanged': True,
            'historical_router_unchanged': True, 'network_context_unchanged': True,
            'log_sha256': {f'stage_{i}.log': sha(out / f'stage_{i}.log')
                           for i in range(len(commands))},
            'end_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
    except BaseException as exc:
        save(out / 'terminal.json', {'status': 'FAIL', 'exception': str(exc)})
        raise
    save(out / 'terminal.json', result)


if __name__ == '__main__':
    main()

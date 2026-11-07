"""Generate native Hecate graphs and immutable 2D/width controls in this project."""
import argparse
import copy
import json
from pathlib import Path
import shutil

from native_cpu_budget import audited_process, pin_budget
from prepare import sha256, write_json
from scaling_common import verified, vpr_environment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--plan', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    root.mkdir(exist_ok=False)
    plan = json.loads(args.plan.read_text())
    binary = verified(plan['binaries']['cpu'])
    env = vpr_environment(json.loads(Path(plan['runtime']).read_text()))
    env = {k: v for k, v in env.items() if not k.startswith(('VPR_HYBRID_', 'H3D_GPU_'))}
    env['VPR_HYBRID_LOOKAHEAD_PARALLEL'] = '1'
    import os
    os.sched_setaffinity(0, [56, 57, 58, 59])
    budget = pin_budget(4)
    workspace = Path.cwd()
    arch2d = workspace / 'vendor/vtr_cpu_paper/vtr_flow/arch/multi_die/hecate/2d/hecate_2d_k6FracN10LB_mem20K_complexDSP_customSB_7nm.xml'
    suite = {x['id']: x for x in json.loads((workspace / 'jobs/target_suite_20261027.json').read_text())['cases']}
    receipt = {'status': 'running', 'cpu_budget': budget, 'cases': [], 'note': 'Preparation only; not a timing sample. Native XML graph generation, no edge/delay editing.'}
    write_json(root / 'preparation.json', receipt)
    for name in ['ex5p', 'elliptic']:
        source_case = json.loads(Path(suite[name]['vpr_case']).read_text())
        for layers, width in [(1, 100), (2, 80), (2, 100), (2, 120)]:
            case_id = f'{name}_native_l{layers}_w{width}'
            directory = root / case_id
            directory.mkdir()
            arch = arch2d if layers == 1 else verified(source_case['inputs']['architecture'])
            circuit = verified(source_case['inputs']['circuit'])
            command = [binary, arch, circuit, '--route_chan_width', str(width), '--device_width', '30',
                       '--target_utilization', '0.1', '--seed', '1', '--num_workers', '4', '--router_algorithm', 'parallel',
                       '--router_lookahead', 'map', '--flat_routing', 'off', '--check_route', 'full',
                       '--net_file', directory / 'packed.net', '--place_file', directory / 'fixed.place',
                       '--route_file', directory / 'routed.route', '--write_rr_graph', directory / 'rr_graph.xml',
                       '--routing_failure_predictor', 'off', '--max_router_iterations', '1',
                       '--congested_routing_iteration_threshold', '0.25', '--timing_report_npaths', '10', '--analysis', '--route']
            if layers == 1:
                command.extend(['--pack', '--place'])
            else:
                for role, filename in [('packed_netlist', 'packed.net'), ('placement', 'fixed.place')]:
                    shutil.copyfile(verified(source_case['inputs'][role]), directory / filename)
            outcome = audited_process(command, directory, env, 1200)
            row = {'case': case_id, 'layers': layers, 'width': width, **outcome}
            # A legal fixed placement and a complete graph are required. Routing
            # failure may be the intended congestion challenge, and is retained.
            text = (directory / 'process.log').read_text(errors='replace')
            ready = (outcome['returncode'] in [0, 2] and 'Completed placement consistency check successfully' in text
                     and (directory / 'rr_graph.xml').is_file() and (directory / 'fixed.place').is_file())
            row['case_ready'] = ready
            if ready:
                case = copy.deepcopy(source_case)
                case.update(id=case_id, route_chan_width=width, device_width=30, layers=layers,
                            provenance='Native Hecate XML graph generation; 2D uses freshly packed/placed seed-1 inputs; 3D retains the prior fixed placement.',
                            preparation_route_success=outcome['returncode'] == 0)
                paths = {'architecture': arch, 'circuit': circuit, 'packed_netlist': directory / 'packed.net',
                         'placement': directory / 'fixed.place', 'rr_graph': directory / 'rr_graph.xml'}
                case['inputs'] = {role: {'path': str(path), 'sha256': sha256(path)} for role, path in paths.items()}
                case.pop('reference', None)
                case.pop('scope', None)
                write_json(directory / 'vpr_case.json', case)
                row['vpr_case'] = str(directory / 'vpr_case.json')
            receipt['cases'].append(row)
            write_json(root / 'preparation.json', receipt)
            print(json.dumps({'case': case_id, 'ready': ready, 'returncode': outcome['returncode']}), flush=True)
    receipt['status'] = 'completed'
    write_json(root / 'preparation.json', receipt)


if __name__ == '__main__':
    main()

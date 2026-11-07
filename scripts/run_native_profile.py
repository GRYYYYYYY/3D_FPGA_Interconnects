"""Capture native VPR queries without changing its path/commit decisions.

Diagnostic runs are explicitly excluded from performance claims. Original VPR
and an unmodified same-toolchain rebuild are retained as controls.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import time

from prepare import sha256, write_json
from scaling_common import metrics, run_process, verified, vpr_command, vpr_environment


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--binary', type=Path, required=True)
    p.add_argument('--suite', type=Path, default=Path('jobs/target_suite_20261027.json'))
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--cases', default='ex5p,softmax,clstm_large,reduction,gemm,elliptic')
    p.add_argument('--timeout', type=float, default=1200)
    p.add_argument('--control', action='store_true')
    args = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve(); output.mkdir(parents=True, exist_ok=False)
    binary = args.binary.resolve()
    env = vpr_environment(json.loads((root/'data/vpr_runtime_20261025/runtime.json').read_text()))
    env = {k:v for k,v in env.items() if not k.startswith('VPR_HYBRID_')}
    record = {'status':'running', 'diagnostic':not args.control,
              'binary':str(binary), 'binary_sha256':sha256(binary), 'cases':[]}
    write_json(output/'summary.json',record)
    requested = args.cases.split(',')
    suite = json.loads(args.suite.read_text())['cases']
    assert set(requested) <= {c['id'] for c in suite}
    for item in suite:
        if item['id'] not in requested: continue
        directory=output/item['id']; directory.mkdir()
        case=json.loads(Path(item['vpr_case']).read_text())
        # Bind the actual architecture, circuit, RRG, packed netlist and layout.
        for r in case['inputs'].values(): verified(r)
        started=time.perf_counter()
        for role,name in [('packed_netlist','packed.net'),('placement','fixed.place')]:
            shutil.copyfile(case['inputs'][role]['path'],directory/name)
        run_env=env.copy()
        if not args.control: run_env['VPR_HYBRID_PROFILE']=str(directory/'queries')
        row=run_process(vpr_command(binary,case,directory,200),directory,run_env,args.timeout)
        row.update(id=item['id'], workflow_seconds=time.perf_counter()-started,
                   inputs=case['inputs'], route_chan_width=case['route_chan_width'], seed=case['seed'])
        row.update(metrics((directory/'process.log').read_text(errors='replace')))
        row['success']=row['returncode']==0 and row['full_check'] and row['routing_success']
        if (directory/'routed.route').exists(): row['route_sha256']=sha256(directory/'routed.route')
        if (directory/'queries').exists():
            row['snapshots']=[{'path':str(f),'sha256':sha256(f),'bytes':f.stat().st_size}
                              for f in sorted((directory/'queries').glob('*.bin'))]
        write_json(directory/'measurement.json',row)
        record['cases'].append(row);write_json(output/'summary.json',record)
        print(item['id'],row['status'],row['success'],row['critical_path_ns'],row['workflow_seconds'],flush=True)
    if sha256(binary)!=record['binary_sha256']: raise RuntimeError('binary changed during native profiling')
    record['status']='completed' if all(c['success'] for c in record['cases']) else 'failed'
    write_json(output/'summary.json',record)
    if record['status']!='completed':raise SystemExit(1)


if __name__=='__main__':main()

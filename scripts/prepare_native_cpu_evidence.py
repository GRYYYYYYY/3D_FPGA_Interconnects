"""Generate fresh packed netlists, placements and native 3D RR graphs."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import resource
from native_cpu_budget import audited_process, pin_budget
from prepare import sha256, write_json
from scaling_common import metrics, verified, vpr_environment

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/native_cpu_evidence_20261102'


def main():
    protocol=json.loads((OUT/'protocol.json').read_text())
    plan=json.loads((OUT/'triad_plan.json').read_text())
    # This stage must not overlap the measured triad.
    receipt=json.loads((OUT/'triad/supervisor.json').read_text())
    assert receipt['status']=='completed'
    prepared=OUT/'prepared';prepared.mkdir(exist_ok=False)
    binary=verified(plan['binaries']['original']);arch=verified(protocol['architecture'])
    env=vpr_environment(json.loads(Path(plan['runtime']).read_text()))
    env={k:v for k,v in env.items() if not k.startswith(('VPR_HYBRID_','VPR_CPU_','H3D_GPU_'))}
    resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3))
    resource.setrlimit(resource.RLIMIT_CORE,(512*1024**2,512*1024**2))
    os.sched_setaffinity(0,set(range(32,40)));budget=pin_budget(1)
    summary={'status':'running','started_utc':datetime.now(timezone.utc).isoformat(),'cpu_budget':budget,'runs':[]}
    write_json(OUT/'preparation.json',summary)
    for circuit in protocol['selected_circuits']:
        blif=verified(circuit)
        for seed in protocol['placement_seeds']:
            case_id=f"{circuit['id']}_s{seed}";directory=prepared/case_id;directory.mkdir()
            command=list(map(str,[binary,arch,blif,'--pack','--place','--route','--analysis',
                '--route_chan_width',protocol['route_chan_width'],'--device_width',protocol['device_width'],
                '--target_utilization',protocol['target_utilization'],'--seed',seed,'--num_workers',1,
                '--router_algorithm','timing_driven','--flat_routing','off','--check_route','full',
                '--net_file',directory/'packed.net','--place_file',directory/'fixed.place',
                '--route_file',directory/'routed.route','--write_rr_graph',directory/'rr_graph.xml',
                '--max_router_iterations',200,'--routing_failure_predictor','off',
                '--congested_routing_iteration_threshold','.25','--timing_report_npaths',10]))
            row={'case':case_id,'status':'running','command':command,'directory':str(directory)}
            summary['runs'].append(row);write_json(OUT/'preparation.json',summary)
            row.update(audited_process(command,directory,env,1800))
            row['finished_utc']=datetime.now(timezone.utc).isoformat()
            row['metrics']=metrics((directory/'process.log').read_text(errors='replace'))
            names={'architecture':arch,'circuit':blif,'packed_netlist':directory/'packed.net',
                   'placement':directory/'fixed.place','rr_graph':directory/'rr_graph.xml'}
            row['inputs_ready']=row['returncode'] in [0,2] and all(f.is_file() and f.stat().st_size for f in names.values())
            row['serial_route_legal']=bool(row['metrics']['routing_success'] and row['metrics']['full_check'])
            if row['inputs_ready']:
                case=dict(id=case_id,circuit_id=circuit['id'],placement_seed=seed,seed=seed,
                    inputs={k:dict(path=str(v),sha256=sha256(v)) for k,v in names.items()},
                    route_chan_width=protocol['route_chan_width'],device_width=protocol['device_width'],
                    target_utilization=protocol['target_utilization'],
                    scope='Fresh original-VPR pack and place for this seed; each comparison reuses these exact files. Preparation is outside measured routing process.')
                write_json(directory/'vpr_case.json',case)
                row['case_sha256']=sha256(directory/'vpr_case.json')
            write_json(directory/'preparation_receipt.json',row);write_json(OUT/'preparation.json',summary)
            print(json.dumps({'case':case_id,'inputs_ready':row['inputs_ready'],'serial_route_legal':row['serial_route_legal']}),flush=True)
    summary['status']='completed' if all(r['inputs_ready'] for r in summary['runs']) else 'failed'
    summary['finished_utc']=datetime.now(timezone.utc).isoformat()
    write_json(OUT/'preparation.json',summary)
    if summary['status']!='completed':raise SystemExit(1)


if __name__=='__main__':main()

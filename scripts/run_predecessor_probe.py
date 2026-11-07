"""Bounded CPU diagnosis and independently checked quality runs; not GPU timings."""
import argparse
import json
import os
from pathlib import Path
import shutil
from native_cpu_budget import pin_budget, audited_process
from prepare import sha256, write_json
from scaling_common import verified, vpr_command, vpr_environment, metrics

p=argparse.ArgumentParser()
p.add_argument('--output',type=Path,required=True)
p.add_argument('--mode',choices=['parallel','serial','guard'],default='parallel')
p.add_argument('--audit',action='store_true')
p.add_argument('--lookahead-profile',action='store_true')
p.add_argument('--write-lookahead',action='store_true')
p.add_argument('--parallel-lookahead',action='store_true')
p.add_argument('--case',default='elliptic')
p.add_argument('--suite',type=Path,default=Path('jobs/target_suite_20261027.json'))
p.add_argument('--runtime',type=Path,default=Path('data/vpr_runtime_20261025/runtime.json'))
p.add_argument('--vpr-lock',type=Path,default=Path('../FPGA_accelerate_FPGA/G_3d_routing/configs/vpr.lock.json'))
p.add_argument('--timeout',type=float,default=600)
p.add_argument('--binary',type=Path,default=Path('build_native/vpr/vpr'))
args=p.parse_args();root=Path(__file__).resolve().parents[1];out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
suite=json.loads(args.suite.read_text())['cases'];case=json.loads(Path(next(c for c in suite if c['id']==args.case)['vpr_case']).read_text())
for value in case['inputs'].values():verified(value)
runtime=json.loads(args.runtime.read_text());env=vpr_environment(runtime)
env={k:v for k,v in env.items() if not k.startswith(('VPR_HYBRID_','H3D_GPU_'))}
if args.audit:env['VPR_HYBRID_LABEL_AUDIT']=str(out/'label_collisions.jsonl')
if args.lookahead_profile:env['VPR_HYBRID_LOOKAHEAD_REPORT']=str(out/'lookahead.jsonl')
if args.parallel_lookahead:env['VPR_HYBRID_LOOKAHEAD_PARALLEL']='1'
if args.mode=='guard':env.update(VPR_HYBRID_MODE='guard',VPR_HYBRID_REPORT=str(out/'hybrid.json'))
binary=args.binary.resolve();record={'status':'running','mode':args.mode,'diagnostic':args.audit or args.lookahead_profile or args.write_lookahead,'parallel_lookahead':args.parallel_lookahead,'cpu_budget':pin_budget(4),'binary':str(binary),'binary_sha256':sha256(binary),'inputs':case['inputs']};write_json(out/'summary.json',record)
for role,name in [('packed_netlist','packed.net'),('placement','fixed.place')]:shutil.copyfile(case['inputs'][role]['path'],out/name)
command=vpr_command(binary,case,out,200)+['--generate_rr_node_overuse_report','on']
if args.write_lookahead:command+=['--write_router_lookahead',str(out/'lookahead.bin')]
if args.mode!='serial':
    command[command.index('--router_algorithm')+1]='parallel';command[command.index('--num_workers')+1]='4'
result=audited_process(command,out,env,args.timeout);record.update(result);record['metrics']=metrics((out/'process.log').read_text(errors='replace'));record['success']=False
if (out/'lookahead.bin').is_file():record['lookahead_sha256']=sha256(out/'lookahead.bin')
if result['returncode']==0 and record['metrics']['full_check'] and record['metrics']['routing_success']:
    lock=json.loads(args.vpr_lock.read_text())
    original=verified(lock['binary']);record['independent_binary']=lock['binary'];record['route_sha256']=sha256(out/'routed.route')
    check=audited_process(vpr_command(original,case,out,200,route=False),out,env,args.timeout,'independent_check.log')
    quality=metrics((out/'independent_check.log').read_text(errors='replace'));record.update(independent_check=check,independent_metrics=quality)
    record['success']=check['returncode']==0 and quality['full_check'] and all(quality[k]==record['metrics'][k] for k in ['critical_path_ns','wirelength'])
    assert sha256(out/'routed.route')==record['route_sha256']
write_json(out/'summary.json',record);print(json.dumps({k:record[k] for k in ['status','success','returncode','process_seconds','metrics']}))

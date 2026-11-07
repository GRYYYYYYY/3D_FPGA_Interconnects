"""Predeclared architecture and real cache-batch experiments; no solver edits."""
import fcntl,json,os,resource,shutil,sys,statistics,math,socket
from pathlib import Path
from datetime import datetime,timezone
from prepare import write_json,sha256
from scaling_common import verified,vpr_environment,vpr_command,metrics
from run_native_cpu_study import cpu_command,set_option
from run_native_lookahead_component import captured_process
from report_native_joint import log_evidence
from qualify_native_cpu_width120 import quality
from native_cpu_budget import pin_budget
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/native_paper_closure_20261105'
ARMS=['stock','fixed_serial','per_group','pipeline']
SW={'stock':('0','0'),'fixed_serial':('0','0'),'per_group':('0','1'),'pipeline':('1','1')}
def read(p):return json.loads(Path(p).read_text())
def bind(p):return {'path':str(Path(p).resolve()),'sha256':sha256(p)}
def now():return datetime.now(timezone.utc).isoformat()
def freeze():
 p=read(ROOT/'results/native_lookahead_component_20261104/plan.json')
 arch=ROOT/'vendor/vtr_cpu_slices/vtr_flow/arch/timing/k6_N10_mem32K_40nm.xml'
 circuits=Path(read(ROOT/'data/scaling_20261025/ex5p/vpr_case.json')['inputs']['circuit']['path']).parent
 cases={f'{c}_s{s}':{'circuit':bind(circuits/(c+'.blif')),'architecture':bind(arch),'seed':s,'device_width':w,'route_chan_width':100,'target_utilization':0.5} for c,w in [('tseng',30),('des',40)] for s in [1,2]}
 jobs=[]
 for phase,reps,modes in [('qualification',1,['rebuild']),('formal',3,['rebuild','reuse'])]:
  for r in range(reps):
   names=list(cases);names=names[r%4:]+names[:r%4]
   for i,c in enumerate(names):
    for j,mode in enumerate(modes if (i+r)%2==0 else modes[::-1]):
     for k in range(4):
      arm=ARMS[(k+i+j+r)%4];jobs.append(dict(key=f'{phase}_{c}_{mode}_r{r}_{arm}',phase=phase,case=c,mode=mode,repeat=r,arm=arm))
 # Reuse is a real sequence: first build creates the cache used by later runs.
 # Each K=5 sequence supplies explicitly correlated K=1,2,5 prefix outcomes.
 batches=[dict(key=f'batch_{c}_r{r}_{a}',case=c,repeat=r,arm=a,length=5) for r in range(3) for c in ['tseng_s1','des_s1'] for a in ['stock','per_group','pipeline']]
 plan=dict(status='frozen',created_utc=now(),cases=cases,jobs=jobs,batches=batches,binaries=p['binaries'],runtime=p['runtime'],workers=8,cpu_pool=list(range(32,40)),timeout_seconds=900,min_disk_gib=60,repeats=3,source_plan=bind(ROOT/'results/native_lookahead_component_20261104/plan.json'),
  selection='Two held-out BLIF circuits tseng/des, native k6_N10_mem32K_40nm family; widths30/40, channel100, seeds1/2 fixed before timing. Native pack/place preparation is not a speed sample; all failed layouts retained. No retry or width escalation.',
  qualification='All four arms must be legal, wire-map-identical to stock, independently original FULL/STA checked; corrected QoR <=5% stock and pipeline <=5% per_group/fixed_serial. Otherwise skip formal for that layout, preserve denominator4.',
  timing='Native route/analysis process reads frozen packed/place/RR inputs, writes map in both modes. Not full compilation. Rebuild is not filesystem cold-cache.',
  batch_scope='Repeated routing requests for the same fixed design. One real cache miss followed by four hits, matching K=1,2,5 prefixes. Not five independent designs and not three independent K experiments. Each arm generates its own equal cache; includes map write/read in process time.',
  architecture_exploration='Sum paired rebuild process times over distinct graph cases; analytical aggregation of measured runs, not an independently timed batch.',
  statistics='Pair case/mode/repeat, three ratios median/range. Equal circuit then equal layout weighting; no pooling historical runs. Separate stage and process. Require legality and <=5% QoR per comparison.',
  scaling=dict(status='awaiting_verified_cpu_allocation',cores=[1,2,4,8,16],repeats=3,exclusive_host=False),default_changed=False,exclusive_host=False,
  runner_bindings={n:bind(ROOT/'scripts'/n) for n in ['run_native_paper_closure.py','run_native_lookahead_component.py','run_native_cpu_study.py','scaling_common.py','native_cpu_budget.py','prepare.py','report_native_joint.py','qualify_native_cpu_width120.py']})
 assert not (OUT/'plan.json').exists();write_json(OUT/'plan.json',plan)
 print('Frozen4 preparations,16 qualifications,conditional96 formal and18 real length5 batches',flush=True)
def environment(plan,arm):
 env={k:v for k,v in vpr_environment(read(plan['runtime']['path'])).items() if not k.startswith(('VPR_CPU_','VPR_HYBRID_','H3D_GPU_'))}
 t,p=SW[arm];return env|{'VPR_HYBRID_LOOKAHEAD_TASKS':t,'VPR_HYBRID_LOOKAHEAD_PARALLEL':p}
def check_capture(row,cmd,env,cpus):
 a=row['actual_process'];wanted={k:v for k,v in env.items() if k.startswith(('VPR_','H3D_GPU_')) or k in ['OMP_NUM_THREADS','LC_ALL']}
 assert a.get('command')==list(map(str,cmd)) and a.get('environment')==wanted,'Actual command/env mismatch'
 assert a.get('cpu_set')==cpus and row['cpu_budget_audit']['verified'],'CPU affinity mismatch'
def process(plan,cmd,d,arm):
 assert shutil.disk_usage(OUT).free>plan['min_disk_gib']*1024**3,'Disk floor'
 env=environment(plan,arm);row=captured_process(cmd,d,env,plan['timeout_seconds']);check_capture(row,cmd,env,plan['cpu_pool']);return row

def run_one(plan,state,job,case,cache=None,model='map'):
 d=OUT/job['key'];d.mkdir();arm=job['arm'];b=plan['binaries']['original' if arm=='stock' else 'cpu']['path']
 for role,name in [('packed_netlist','packed.net'),('placement','fixed.place')]:shutil.copyfile(case['inputs'][role]['path'],d/name)
 cmd=cpu_command(b,case,d,{'router':'parallel','lookahead':model},8,cache=cache,iterations=200)
 if model=='map':set_option(cmd,'--write_router_lookahead',d/'wire_map.bin')
 row=job|dict(directory=str(d),started_utc=now(),success=False,loadavg_before=os.getloadavg(),command=cmd)
 state['measurements'].append(row);write_json(OUT/'summary.json',state)
 row.update(process(plan,cmd,d,arm));row.update(metrics((d/'process.log').read_text(errors='replace')));write_json(d/'measurement.json',row)
 ev=log_evidence(d);row['evidence']=ev;row['build_seconds']=ev['stage_seconds']['lookahead_build']
 row['map_sha256']=sha256(d/'wire_map.bin') if (d/'wire_map.bin').exists() else None
 expected=state['prepared'][job['case']].get('reference_map')
 if expected and model=='map' and row['map_sha256']:assert row['map_sha256']==expected['sha256'],'Map mismatch'
 if row['returncode']==0 and row['routing_success'] and row['full_check']:
  assert ev['final_overused_nodes']==0
  if model=='map':
   assert row['map_sha256'] is not None
   assert (row['build_seconds'] is None) if cache else (row['build_seconds'] is not None)
  h=sha256(d/'routed.route');row['route_sha256']=h
  cd=d/'independent';cd.mkdir();ic=vpr_command(plan['binaries']['original']['path'],case,d,200,route=False)
  ir=process(plan,ic,cd,arm);im=metrics((cd/'process.log').read_text(errors='replace'))
  row.update(independent=ir,independent_metrics=im)
  row['success']=ir['returncode']==0 and im['full_check'] and all(im[k]==row[k] for k in ['critical_path_ns','wirelength'])
  assert h==sha256(d/'routed.route')
  row['workflow_seconds']=row['process_seconds']+ir['process_seconds']
 for role,name in [('packed_netlist','packed.net'),('placement','fixed.place')]:assert sha256(d/name)==case['inputs'][role]['sha256']
 row['finished_utc']=now();row['loadavg_after']=os.getloadavg();write_json(d/'measurement.json',row);write_json(OUT/'summary.json',state)
 print(json.dumps({k:row.get(k) for k in ['key','returncode','success','build_seconds','process_seconds']}),flush=True)
 return row

def run():
 plan=read(OUT/'plan.json');lock=(OUT/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not (OUT/'summary.json').exists(),'No implicit restart'
 for v in list(plan['runner_bindings'].values())+list(plan['binaries'].values())+[plan['runtime']]:verified(v)
 for c in plan['cases'].values():verified(c['architecture']);verified(c['circuit'])
 resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3))
 os.sched_setaffinity(0,plan['cpu_pool']);budget=pin_budget(8)
 state=dict(status='running',pid=os.getpid(),hostname=socket.gethostname(),started_utc=now(),plan=bind(OUT/'plan.json'),cpu_budget=budget,prepared={},measurements=[],skipped=[],gates={})
 write_json(OUT/'summary.json',state)
 try:
  for name,c in plan['cases'].items():
   d=OUT/('prepare_'+name);d.mkdir();cmd=[plan['binaries']['original']['path'],c['architecture']['path'],c['circuit']['path'],'--pack','--place','--route','--analysis','--route_chan_width','100','--device_width',str(c['device_width']),'--target_utilization','0.5','--seed',str(c['seed']),'--num_workers','8','--router_algorithm','parallel','--router_lookahead','map','--flat_routing','off','--check_route','full','--net_file',str(d/'packed.net'),'--place_file',str(d/'fixed.place'),'--route_file',str(d/'routed.route'),'--write_rr_graph',str(d/'rr_graph.xml'),'--write_router_lookahead',str(d/'wire_map.bin'),'--max_router_iterations','1','--routing_failure_predictor','off','--timing_report_npaths','0']
   pr=process(plan,cmd,d,'stock');pr['ready']=pr['returncode'] in [0,2] and all((d/n).exists() for n in ['packed.net','fixed.place','rr_graph.xml','wire_map.bin'])
   state['prepared'][name]=pr
   if pr['ready']:
    paths={'architecture':c['architecture']['path'],'circuit':c['circuit']['path'],'packed_netlist':d/'packed.net','placement':d/'fixed.place','rr_graph':d/'rr_graph.xml'}
    case={k:c[k] for k in ['seed','device_width','target_utilization','route_chan_width']}|dict(id=name,inputs={k:bind(v) for k,v in paths.items()})
    write_json(d/'vpr_case.json',case);pr.update(case=bind(d/'vpr_case.json'),reference_map=bind(d/'wire_map.bin'))
   write_json(d/'preparation.json',pr);write_json(OUT/'summary.json',state);print('Prepared',name,pr['ready'],flush=True)
  for job in plan['jobs']:
   name=job['case'];p=state['prepared'][name]
   if not p['ready']:state['skipped'].append(job|{'reason':'preparation_failed'});continue
   if job['phase']=='formal' and name not in state['gates']:
    rows={r['arm']:r for r in state['measurements'] if r['phase']=='qualification' and r['case']==name}
    legal=len(rows)==4 and all(r['success'] for r in rows.values())
    qs={a:quality(rows[a],rows['stock']) for a in ARMS[1:]} if legal else {}
    inc={a:quality(rows['pipeline'],rows[a]) for a in ['fixed_serial','per_group']} if legal else {}
    state['gates'][name]=dict(passed=legal and all(q['passed'] for q in list(qs.values())+list(inc.values())),quality=qs,incremental=inc)
   if job['phase']=='formal' and not state['gates'][name]['passed']:state['skipped'].append(job|{'reason':'qualification_rejected'});continue
   run_one(plan,state,job,read(p['case']['path']),p['reference_map']['path'] if job['mode']=='reuse' else None)
  # Alternative model: source-confirmed 2D compressed_map, no byte-equality to map claim.
  for name in ['tseng_s1','des_s1']:
   if not state['gates'].get(name,{}).get('passed'):continue
   for r in range(3):run_one(plan,state,dict(key=f'compressed_{name}_r{r}',case=name,phase='compressed',arm='stock',repeat=r,mode='rebuild'),read(state['prepared'][name]['case']['path']),model='compressed_map')
  for batch in plan['batches']:
   name=batch['case']
   if not state['gates'].get(name,{}).get('passed'):state['skipped'].append(batch|{'reason':'qualification_rejected'});continue
   cache=None
   for i in range(batch['length']):
    job=dict(key=batch['key']+f'_i{i}',case=name,arm=batch['arm'],repeat=batch['repeat'],phase='batch',batch=batch['key'],index=i,mode='rebuild' if i==0 else 'reuse')
    r=run_one(plan,state,job,read(state['prepared'][name]['case']['path']),cache)
    if not r['success']:state['skipped'].append(batch|dict(reason='batch_failed',remaining=batch['length']-i-1));break
    if i==0:cache=str(OUT/job['key']/'wire_map.bin')
  state['status']='completed'
 except Exception as e:state.update(status='stopped_for_review',error=repr(e));raise
 finally:
  state['finished_utc']=now();write_json(OUT/'summary.json',state)
if __name__=='__main__':{'freeze':freeze,'run':run}[sys.argv[1]]()

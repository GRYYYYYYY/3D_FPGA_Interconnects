"""Portable, single-owner component scaling under an actual CPU allocation."""
import os,sys,json,socket,fcntl,resource,shutil,subprocess,threading,time
from pathlib import Path
from datetime import datetime,timezone
from prepare import sha256,write_json
from scaling_common import metrics,verified,vpr_environment
from run_native_cpu_study import cpu_command,set_option
from run_native_lookahead_component import captured_process,component_evidence
from native_cpu_budget import pin_budget
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/native_paper_closure_20261105/scaling'
def read(p):return json.loads(Path(p).read_text())
def bind(p):return dict(path=str(Path(p).resolve()),sha256=sha256(p))
def now():return datetime.now(timezone.utc).isoformat()
def freeze():
 p=read(ROOT/'results/native_lookahead_component_20261104/plan.json');fresh=read(ROOT/'results/native_paper_closure_20261105/summary.json')
 cases={n:p['cases'][n] for n in ['bnn','dla_like.medium']}
 f=fresh['prepared']['tseng_s1'];assert f['ready'];cases['tseng_2d']=dict(case=f['case'],reference_map=f['reference_map'])
 OUT.mkdir(exist_ok=False)
 jobs=[]
 for r in range(3):
  for gi,g in enumerate(cases):
   cores=[1,2,4,8,16];cores=cores[r:]+cores[:r]
   for w in cores:
    for arm in (['per_group','pipeline'] if (r+gi)%2==0 else ['pipeline','per_group']):jobs.append(dict(key=f'formal_{g}_w{w}_r{r}_{arm}',phase='formal',graph=g,workers=w,repeat=r,arm=arm))
 for g in cases:
  for a in ['per_group','pipeline']:jobs.append(dict(key=f'diagnostic_{g}_w8_{a}',phase='diagnostic',graph=g,workers=8,repeat=0,arm=a))
 write_json(OUT/'plan.json',dict(status='frozen',created_utc=now(),cases=cases,jobs=jobs,binaries=p['binaries'],runtime=p['runtime'],
  bindings={n:bind(ROOT/'scripts'/n) for n in ['run_native_cpu_allocated_scaling.py','run_native_cpu_study.py','run_native_lookahead_component.py','scaling_common.py','native_cpu_budget.py','prepare.py','report_native_joint.py']},
  formal_count=90,diagnostic_count=6,timeout_seconds=900,min_disk_gib=60,repeats=3,selection='Small native tseng2D; medium BNN and large DLA width120 distinct RR graphs, chosen without new candidate timing. Retain failed routing tails separately.',
  allocation_gate='At least16 distinct allowed physical cores on one NUMA node and cgroup CPU quota >=16. Record allocation/Slurm/cpuset; gate alone does not certify exclusive host or core ownership. Classification reviewed from provider and runtime evidence.',
  statistics='Complete lookahead timer only. Pair per graph/cores/repeat. Speedup T_arm_1/T_arm_P and efficiency speedup/P; incremental per_group/pipeline paired. Report three ratios median/range; no historical pooling. Sampled HWM/RSS are not exact peak bounds.',
  tail='Exactly1 route iteration; expected rc2 may be component-valid but not a legal end-to-end sample. Byte match frozen reference, actual env and affinity mandatory.',default_changed=False))
 print('Frozen90 component timings +6 separate diagnostics',flush=True)
def run():
 p=read(OUT/'plan.json');lock=(OUT/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert not (OUT/'summary.json').exists(),'No implicit retry'
 for x in list(p['bindings'].values())+list(p['binaries'].values())+[p['runtime']]:verified(x)
 allowed=set(os.sched_getaffinity(0));top=[]
 for cpu in sorted(allowed):
  d=Path(f'/sys/devices/system/cpu/cpu{cpu}');nodes=list(d.glob('node[0-9]*'))
  top.append(dict(cpu=cpu,core=int((d/'topology/core_id').read_text()),socket=int((d/'topology/physical_package_id').read_text()),node=int(nodes[0].name[4:]) if nodes else -1))
 groups={}
 for x in top:groups.setdefault(x['node'],{}).setdefault((x['socket'],x['core']),x['cpu'])
 pools=[sorted(x.values()) for x in groups.values() if len(x)>=16]
 state=dict(status='running',pid=os.getpid(),hostname=socket.gethostname(),started_utc=now(),plan=bind(OUT/'plan.json'),topology=top,initial_affinity=sorted(allowed),measurements=[],allocation_classification='pending_provider_and_runtime_review',exclusive_host=False)
 write_json(OUT/'summary.json',state)
 if not pools:state.update(status='allocation_rejected',reason='No single NUMA node has16 allowed physical cores');write_json(OUT/'summary.json',state);return
 pool=sorted(pools,key=lambda x:x[0])[0][:16];state['pool']=pool
 os.sched_setaffinity(0,pool);state['budget']=pin_budget(16)
 resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3))
 cases={}
 for g,e in p['cases'].items():
  verified(e['case']);verified(e['reference_map']);c=read(e['case']['path']);cases[g]=c
  for v in c['inputs'].values():verified(v)
 env={k:v for k,v in vpr_environment(read(p['runtime']['path'])).items() if not k.startswith(('VPR_CPU_','VPR_HYBRID_','H3D_GPU_'))}
 try:
  for job in p['jobs']:
   assert shutil.disk_usage(OUT).free>p['min_disk_gib']*1024**3,'Disk floor'
   cpus=pool[:job['workers']];os.sched_setaffinity(0,cpus);budget=pin_budget(job['workers']);d=OUT/job['key'];d.mkdir();case=cases[job['graph']]
   for role,n in [('packed_netlist','packed.net'),('placement','fixed.place')]:shutil.copyfile(case['inputs'][role]['path'],d/n)
   cmd=cpu_command(p['binaries']['cpu']['path'],case,d,{'router':'parallel'},job['workers'],iterations=1);cmd.remove('--analysis');set_option(cmd,'--generate_rr_node_overuse_report','off');set_option(cmd,'--write_router_lookahead',d/'wire_map.bin')
   local=env|{'VPR_HYBRID_LOOKAHEAD_TASKS':'1' if job['arm']=='pipeline' else '0','VPR_HYBRID_LOOKAHEAD_PARALLEL':'1'}
   if job['phase']=='diagnostic':local['VPR_HYBRID_LOOKAHEAD_REPORT']=str(d/'lookahead_profile.jsonl')
   row=job|dict(directory=str(d),started_utc=now(),component_valid=False,cpu_budget=budget,loadavg_before=os.getloadavg());state['measurements'].append(row);write_json(OUT/'summary.json',state)
   row.update(captured_process(cmd,d,local,900));row.update(metrics((d/'process.log').read_text(errors='replace')));write_json(d/'measurement.json',row)
   row.update(component_evidence(row,d,p['cases'][job['graph']]['reference_map']['sha256']))
   wanted={k:v for k,v in local.items() if k.startswith(('VPR_','H3D_GPU_')) or k in ['OMP_NUM_THREADS','LC_ALL']}
   a=row['actual_process'];assert a.get('command')==cmd and a.get('environment')==wanted and a.get('cpu_set')==cpus and row['cpu_budget_audit']['verified'],'Actual process drift'
   if row.get('wire_map_sha256'):assert row['map_matches_reference'],'Map mismatch'
   row['finished_utc']=now();row['loadavg_after']=os.getloadavg();write_json(d/'measurement.json',row);write_json(OUT/'summary.json',state);print(json.dumps({k:row.get(k) for k in ['key','component_valid','build_seconds']}),flush=True)
  state['status']='completed'
 except Exception as e:state.update(status='stopped_for_review',error=repr(e));raise
 finally:state['finished_utc']=now();write_json(OUT/'summary.json',state)
if __name__=='__main__':{'freeze':freeze,'run':run}[sys.argv[1]]()

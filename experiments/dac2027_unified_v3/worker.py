"""Single-worker V3 protocol. Every invocation has its own directory and receipt."""
import csv, datetime, fcntl, hashlib, json, os, re, shutil, signal, socket, subprocess, sys, time
from pathlib import Path
here=Path(__file__).resolve().parent
repo=here.parents[1]
sys.path.insert(0,str(repo/'scripts'))
from scaling_common import metrics, vpr_command
from report_native_joint import log_evidence
prior=repo/'accel/lookahead/gemm_bnn_native_completion'
run=here/'run'
def read(p): return json.loads(p.read_text())
def save(p,data):
    tmp=p.with_suffix('.tmp')
    tmp.write_text(json.dumps(data,indent=2)+'\n')
    tmp.replace(p)
def digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(8<<20),b''): h.update(block)
    return h.hexdigest()
def utc(): return datetime.datetime.now(datetime.timezone.utc)
def gpu(args):
    return subprocess.check_output(['nvidia-smi',*args,'--format=csv,noheader,nounits'],text=True).strip()
def snapshot():
    return dict(gpu=gpu(['--query-gpu=uuid,memory.free,clocks.sm,clocks.mem,pstate,power.limit']),
                compute=gpu(['--query-compute-apps=gpu_uuid,pid,process_name']),
                cpus=sorted(os.sched_getaffinity(0)),cpu_stat=Path('/sys/fs/cgroup/cpu.stat').read_text())
envrec=read(run/'environment.json')
deadline=datetime.datetime.fromisoformat(envrec['deadline'])
cases=read(here/'cases.json')
bins=read(prior/'source_binding.json')['binary']
runtime=read(prior/'runtime.json')
full=['stock','pipeline','alt_cpu','alt_cuda']
controls=['group','flat']
case_order=['bnn','gemm','lstm']
gold=read(here/'golden_maps.json')
def environment(arm,d,qual):
    env={k:v for k,v in os.environ.items() if not k.startswith(('VPR_','H3D_','R61_','R62_','OMP_','LA_','LD_PRELOAD'))}
    env.update(LC_ALL='C',LD_LIBRARY_PATH=runtime['library_directory'],OMP_NUM_THREADS='8',
               VPR_HYBRID_LOOKAHEAD_PARALLEL='0' if arm=='stock' else '1',
               VPR_HYBRID_LOOKAHEAD_TASKS='0' if arm in ['stock','group'] else '1')
    if arm not in ['stock','group']:
        env['VPR_CPU_GLOBAL_SCHEDULER']='pipeline' if arm=='pipeline' else 'flat'
    if arm.startswith('alt_'):
        env.update(VPR_LA_MODE='ALT_BUCKET_FP32_V1',VPR_LA_CONTEXTS='8',VPR_LA_BUCKET_SHIFT='20',
                   VPR_LA_BACKEND=bins[arm]['path'])
        if qual:
            env['R61_CAPTURE']=str(d/'capture')
            if arm=='alt_cuda': env['R61_VERIFY_CPU']='1'
    return env
def execute(cmd,cwd,env):
    with (cwd/'process.log').open('wb') as f:
        begin=time.monotonic_ns()
        process=subprocess.Popen(cmd,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT)
        try: code=process.wait()
        except BaseException:
            process.kill();process.wait();raise
        end=time.monotonic_ns()
    text=(cwd/'process.log').read_text(errors='replace')
    return dict(returncode=code,begin_ns=begin,end_ns=end,wall_ns=end-begin,metrics=metrics(text)),text
def option(cmd,k,v):
    if k in cmd: cmd[cmd.index(k)+1]=str(v)
    else: cmd.extend([k,str(v)])
def launch(case,arm,phase,rep):
    d=run/phase/case/str(rep)/arm
    d.mkdir(parents=True,exist_ok=False)
    data=cases[case]
    exe=here/'build'/('stock/vpr_stock' if arm=='stock' else 'candidate/vpr')
    cmd=vpr_command(str(exe),data,d,200)
    for k,v in {'--num_workers':8,'--router_algorithm':'parallel','--router_lookahead':'map',
                '--write_router_lookahead':d/'wire_map.bin','--generate_rr_node_overuse_report':'off'}.items():
        option(cmd,k,v)
    qual=phase=='qualification'
    env=environment(arm,d,qual)
    for role,name in [('packed_netlist','packed.net'),('placement','fixed.place')]:
        shutil.copyfile(data['inputs'][role]['path'],d/name)
    for item in data['inputs'].values():
        with open(item['path'],'rb') as f:
            while f.read(8<<20): pass
    state=snapshot()
    assert not state['compute'] and state['cpus']==envrec['cpus'] and state['gpu'].startswith(env['CUDA_VISIBLE_DEVICES'])
    rec=dict(case=case,arm=arm,phase=phase,repeat=rep,host=socket.gethostname(),gpu=env['CUDA_VISIBLE_DEVICES'],
             start=utc().isoformat(),before=state,command=cmd,environment={k:v for k,v in env.items() if k.startswith(('VPR_','OMP_','R61_','CUDA_VISIBLE','LD_LIBRARY'))})
    save(d/'invocation.json',rec)
    result,text=execute(cmd,d,env);rec.update(result,after=snapshot())
    e2=re.findall(r'V3_COMPUTE_NS (\d+)',text)
    internal=re.findall(r'Computing router lookahead map took ([\d.]+)',text)
    rec.update(e2_ns=int(e2[0]) if len(e2)==1 else None,native_e2_s=internal,
               internal_e2_s=re.findall(r'R61_NATIVE_BUILD .*?E2_wall_s=([\d.]+)',text),
               stage_times=log_evidence(d)['stage_seconds'],overuse=log_evidence(d)['last_observed_overused_nodes'])
    for key,file in [('map_sha256','wire_map.bin'),('route_sha256','routed.route'),('capture_sha256','capture.bin')]:
        rec[key]=digest(d/file) if (d/file).is_file() else None
    rec['dispatch']=[s for s in text.splitlines() if s.startswith(('CPU_GLOBAL_SCHEDULER=','R61_BACKEND','R61_IDENTITY','R61_NATIVE_PAIR_VERIFY','LA_LIVE'))]
    dispatch='\n'.join(rec['dispatch'])
    ok=(('samples=40' in dispatch and 'backend='+arm[4:].upper() in dispatch and 'fallback=0' in dispatch) if arm.startswith('alt_')
        else (f'CPU_GLOBAL_SCHEDULER={arm} samples=40' in dispatch if arm in ['pipeline','flat'] else 'CPU_GLOBAL_SCHEDULER=' not in dispatch and 'LA_LIVE' not in dispatch))
    rec['matches_archived_map']=rec['map_sha256']==gold[case]['alt' if arm.startswith('alt_') else 'strict']
    rec['local_pass']=bool(rec['returncode']==0 and ok and rec['e2_ns'] and rec['e2_ns']<rec['wall_ns'] and rec['matches_archived_map'] and rec['route_sha256'] and rec['metrics']['routing_success'] and rec['metrics']['full_check'] and rec['metrics']['critical_path_ns'] and rec['overuse']==0)
    save(d/'record.json',rec)
    print(case,phase,rep,arm,rec['local_pass'],flush=True)
    return rec
def readback(d):
    rec=read(d/'record.json')
    if not rec['route_sha256']: return
    rb=d/'readback';rb.mkdir()
    cmd=vpr_command(bins['stock']['path'],cases[rec['case']],d,200,route=False);option(cmd,'--num_workers',8)
    result,_=execute(cmd,rb,environment('stock',rb,False))
    valid=(result['returncode']==0 and result['metrics']['full_check'] and
           all(result['metrics'][k]==rec['metrics'][k] for k in ['wirelength','critical_path_ns']) and
           digest(d/'routed.route')==rec['route_sha256'])
    save(rb/'record.json',dict(command=cmd,original_sha=rec['route_sha256'],passed=valid,**result))
def main():
    lock=(run/'formal.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert envrec['host']==socket.gethostname() and sorted(os.sched_getaffinity(0))==envrec['cpus']
    signal.signal(signal.SIGALRM,lambda *_:sys.exit('deadline'))
    signal.alarm(max(1,int((deadline-utc()).total_seconds())))
    for row in csv.DictReader((here/'audit/bindings.csv').open()):
        assert digest(row['file'])==row['expected'],row['file']
    for p,h in read(here/'audit/timer_build.json').items(): assert digest(p)==h,p
    save(run/'protocol.json',dict(input_manifest_sha256=digest(here/'cases.json'),worker_sha256=digest(__file__),
                                 binaries=read(here/'audit/timer_build.json'),environment=envrec,cache='pre-read all originals, fresh map, no OS flush',
                                 formal_order='rotate by repeat within case',qor_fraction=0.05))
    eligible=[]
    for case in case_order:
        q={a:launch(case,a,'qualification',0) for a in full}
        gate=dict(routes=all(x['local_pass'] for x in q.values()),strict_map=q['stock']['map_sha256']==q['pipeline']['map_sha256'],
                  alt_map=q['alt_cpu']['map_sha256']==q['alt_cuda']['map_sha256'],
                  complete_capture=bool(q['alt_cpu']['capture_sha256']) and q['alt_cpu']['capture_sha256']==q['alt_cuda']['capture_sha256'],
                  cpu_verify=any('all_pairs_equal=1' in l and 'qids=40' in l for l in q['alt_cuda']['dispatch']))
        save(run/'qualification'/case/'gate.json',gate)
        if all(gate.values()): eligible.append(case)
    for arms in (full,controls):
        for case in eligible:
            for r in range(3):
                offset=r%len(arms)
                for a in arms[offset:]+arms[:offset]: launch(case,a,'formal',r)
    for phase in ['qualification','formal']:
        for rec in sorted((run/phase).glob('*/*/*/record.json')): readback(rec.parent)
    save(run/'finished.json',dict(utc=utc().isoformat(),eligible=eligible))
if __name__=='__main__': main()

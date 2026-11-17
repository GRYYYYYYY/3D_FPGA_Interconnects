"""Run the predeclared ALT CPU comparison using the frozen native runner."""
from pathlib import Path
import ctypes
import datetime
import hashlib
import json
import os
import socket
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REFERENCE = ROOT.parent/'3D_FPGA_Interconnects_GEMM_BNN_V2/accel/lookahead/gemm_bnn_native_completion'
sys.path.insert(0, str(REFERENCE))
import runner as native

RUN = ROOT/'results/native_alt_cpu_ablation_20261118'/sys.argv[1]
RUN.mkdir(exist_ok=False)
bounds = native.read(HERE/'p1_budget.json')
deadline = bounds['end']['epoch']
plan = native.read(HERE/'plan.json')
states = {'gemm':'NOT_STARTED','bnn':'NOT_STARTED'}
rows = []
cohort = socket.gethostname()+'_'+RUN.name+'_alt_cpu_20261118'

def save(name, obj):
    path=RUN/name
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(obj,indent=2)+'\n')
    temp.replace(path)

def flush():
    save('rows.json', rows)
    save('states.json', states)

def query(*args):
    return subprocess.check_output(args,text=True,timeout=25).strip()

def admit():
    supplied = native.read(HERE/'worker_binding.json')
    for name, digest in supplied['local'].items():
        assert native.sha(HERE/name)==digest, name
    freeze=native.read(REFERENCE/'worker_freeze.json')
    assert native.sha(REFERENCE/'worker_freeze.json')==supplied['prior_worker_freeze']
    for name,digest in freeze['files'].items():
        assert native.sha(REFERENCE/name)==digest, name
    for item in list(native.bins.values())+native.runtime['libraries']:
        assert native.sha(item['path'])==item['sha256'], item['path']
    for case in native.inputs.values():
        for item in case['case']['inputs'].values():
            assert native.sha(item['path'])==item['sha256'],item['path']
    topo={}
    for cpu in sorted(os.sched_getaffinity(0)):
        folder=Path(f'/sys/devices/system/cpu/cpu{cpu}')
        key=tuple((folder/'topology'/name).read_text().strip() for name in ('physical_package_id','core_id'))
        node=int(next(folder.glob('node*')).name[4:])
        topo.setdefault(node,{}).setdefault(key,cpu)
    node,cores=max(topo.items(),key=lambda kv:len(kv[1]))
    cpus=list(cores.values())[:8]
    quota=Path('/sys/fs/cgroup/cpu.max').read_text().split()
    assert len(cpus)==8 and (quota[0]=='max' or int(quota[0])>=8*int(quota[1]))
    os.sched_setaffinity(0,cpus)
    libc=ctypes.CDLL(None,use_errno=True)
    mask=ctypes.c_ulong(1<<node)
    assert os.uname().machine=='x86_64' and libc.syscall(238,2,ctypes.byref(mask),ctypes.c_ulong(64))==0
    inventory=query('nvidia-smi','--query-gpu=uuid,name,memory.total,memory.free,driver_version','--format=csv,noheader,nounits').splitlines()
    assert len(inventory)==1
    gpu,model,total,free,driver=map(str.strip,inventory[0].split(','))
    assert 'H100' in model and float(total)>=80000
    os.environ['CUDA_VISIBLE_DEVICES']=gpu
    meta={case:native.read(REFERENCE/'metadata'/f'{case}.json') for case in states}
    for key,item in meta.items():
        assert item['J']==40 and item['cuda_estimated_bytes']<=float(free)*1024**2*.8 and not item['invalid_admitted_cost_nodes']
    assert time.time()<bounds['admission_deadline']['epoch'], 'admission deadline'
    env=dict(cohort=cohort,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),hostname=socket.gethostname(),
             physical_cores={str(k):v for k,v in cores.items() if v in cpus},numa_node=node,MPOL_BIND=True,
             affinity=cpus,quota=quota,gpu_uuid=gpu,gpu_model=model,gpu_free_MiB=free,
             driver=driver,compiler=query('nvcc','--version'),cpu=query('lscpu'),admitted_at=time.time(),
             runner_sha256=native.sha(REFERENCE/'runner.py'))
    save('environment.json',env)
    return gpu

# The existing launch/measurement and readback functions retain their original timing brackets.
original_execute=native.execute
def bounded_execute(command,directory,environment,timeout):
    remaining=deadline-time.time()-3
    if remaining<=0:
        raise TimeoutError('Immutable P1 deadline reached before process launch')
    return original_execute(command,directory,environment,min(remaining,timeout))

def measure(case,arm,label,gpu,formal=False):
    apps=query('nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader')
    assert not apps, 'GPU occupied before new process'
    before=time.time()
    row=native.run(case,arm,label,formal=formal,capture=not formal and arm.startswith('alt'))
    row.update(cohort_id=cohort,gpu_uuid=gpu,elapsed_with_readback_s=time.time()-before,finish_epoch=time.time())
    directory=RUN/('formal' if formal else 'qualification')/case/label/arm
    # The original runner stamps its historical suffix. Record the actual cohort on both new records.
    inv=native.read(directory/'invocation.json')
    native.save(directory/'invocation.json',inv|{'cohort_id':cohort})
    native.save(directory/'measurement.json',row)
    rows.append(row)
    flush()
    assert row['qualified'] and row['E2_s']>0 and row['Process_wall_s']>row['E2_s'], (case,arm,label,'failed dispatch, route or readback')
    assert 'R61_CAPTURE' not in row['environment'] if formal else True
    assert 'R61_VERIFY_CPU' not in row['environment'] if formal else True
    if arm.startswith('alt'):
        assert len(row['backend_lines'])==len(row['live_lines'])==1 and 'representation=original' in row['backend_lines'][0]
        assert 'shift=20' in row['backend_lines'][0] and 'samples=40 contexts=8' in row['live_lines'][0]
    if time.time()>deadline:raise TimeoutError('P1 deadline during validation')
    return row

def run_case(case,gpu):
    states[case]='QUALIFYING'
    flush()
    golden=native.read(HERE/'golden.json')[case]
    qual={}
    for arm in plan['arms']:
        q=measure(case,arm,'qualification',gpu)
        assert q['map_sha256']==golden[arm]['map_sha256'], (case,arm,'historical map mismatch')
        if arm.startswith('alt'):
            assert q['native_capture']['sha256']==golden[arm]['capture_sha256'], 'full capture mismatch'
        qual[arm]=q
    assert qual['alt_cpu']['native_capture']['sha256']==qual['alt_cuda']['native_capture']['sha256']
    assert qual['alt_cuda']['map_sha256']==qual['alt_cpu']['map_sha256']
    verify=qual['alt_cuda']['pair_verify_lines']
    assert len(verify)==1 and 'all_pairs_equal=1' in verify[0] and 'coverage_equal=1' in verify[0]
    save(case+'_qualification.json',dict(golden_match=True,full_captures_equal=True,coverage_equal=True,all_pairs_equal=True))
    states[case]='FORMAL_RUNNING'
    flush()
    for repeat,order in enumerate(plan['rotations']):
        group={}
        for arm in order:
            row=measure(case,arm,str(repeat),gpu,formal=True)
            assert row['map_sha256']==qual[arm]['map_sha256']
            row.update(repeat=repeat,qualification_map_equal=True)
            group[arm]=row
        control=group['pipeline']['metrics']
        for row in group.values():
            row['quality_delta_pct']={k:100*(row['metrics'][k]/control[k]-1) for k in ['wirelength','critical_path_ns']}
            row['paired_qor_passed']=all(v<=5 for v in row['quality_delta_pct'].values())
        flush()
        assert all(r['paired_qor_passed'] for r in group.values()), 'QoR gate'
    states[case]='COMPLETE'
    flush()

def estimate_bnn():
    previous=native.read(HERE/'historical_wall_estimates.json')
    observed=sum(r['elapsed_with_readback_s'] for r in rows if r['case']=='gemm')
    return previous['bnn']*max(1,observed/previous['gemm'])*1.2+120

if __name__=='__main__':
    native.R=RUN
    native.execute=bounded_execute
    flush()
    try:
        gpu=admit()
        for case in states:
            if case=='bnn':
                estimate=estimate_bnn()
                remaining=deadline-time.time()
                save('bnn_budget_decision.json',dict(estimated_seconds=estimate,remaining_seconds=remaining))
                if estimate>remaining:
                    states[case]='NOT_STARTED_BUDGET'
                    break
            run_case(case,gpu)
    except Exception as error:
        for case in states:
            if states[case] in ('QUALIFYING','FORMAL_RUNNING'):
                states[case]='TIMEOUT' if isinstance(error,TimeoutError) else 'FAILED'
        save('failure.json',dict(error=repr(error),type=type(error).__name__,time=time.time()))
        raise
    finally:
        flush()
        save('finished.json',dict(states=states,completed_at=time.time(),formal_count=sum(r['formal'] for r in rows)))


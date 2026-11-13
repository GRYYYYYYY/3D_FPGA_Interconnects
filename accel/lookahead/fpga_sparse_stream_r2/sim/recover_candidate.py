"""Append-only recovery of missing tail gates; never rewrite old receipts.

Usage: PLAN.json NEW_TAG. The inventory is frozen before any new experiment.
Each step has a new output directory and an immutable terminal receipt.
"""
from pathlib import Path
import argparse, datetime, fcntl, json, os, subprocess, sys
from recovery_evidence import RESULTS as r, ROOT as root, sha, load, inspect_reusable, validate_recovery

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('plan'); p.add_argument('tag'); a = p.parse_args()
assert Path(a.tag).name == a.tag and a.tag not in ['.','..']
plan = load(a.plan); v, m = plan['RTL'], plan['model']
s = root/'accel/lookahead/fpga_sparse_stream_r2'
out = r/'recovery'/a.tag
out.mkdir(parents=True, exist_ok=False)
# Kernel-held candidate lock prevents another recovery owner, even after a
# supervising terminal disconnects. No old artifact is removed on failure.
lock = (r/'recovery'/(v+'.lock')).open('a')
fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
def write_new(path, value):
    with path.open('x') as f: json.dump(value,f,indent=2); f.write('\n')
def rel(path): return str(path.relative_to(r))
def utc(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
write_new(out/'started.json', {'utc':utc(),'pid':os.getpid(),'proc_start_ticks':Path('/proc/self/stat').read_text().split()[21],
          'plan':plan,'plan_sha256':sha(a.plan),'runner_sha256':sha(__file__),
          'recovery_checker_sha256':sha(Path(__file__).with_name('recovery_evidence.py'))})
try:
    inventory = inspect_reusable(plan)
    inventory['observed_at'] = utc()
    write_new(out/'inventory.json', inventory)
    hot_tag = 'hot_'+a.tag
    boundary_tag = 'boundary_'+a.tag
    fixed_tag = 'fixed10ns_'+a.tag
    artifacts = {
        'hot_summary':f'rtl/{v}_{hot_tag}/summary.json',
        'boundary_calibration':f'model/{m}/{boundary_tag}/calibration.json',
        'fixed10ns_calibration':f'rtl/{v}_{fixed_tag}/calibration.json',
    }
    stages = [
        ('hot8192_8193', ['tests/many_hot_capacity.py',v,m,'--tag',hot_tag], artifacts['hot_summary']),
        ('boundary4', ['sim/calibrate_many_boundaries.py',m,v,'--hot-tag',hot_tag,'--tag',boundary_tag],artifacts['boundary_calibration']),
        ('fixed10ns18', ['sim/sweep_fixed_time.py',v,m,'--period-ps','10000','--tag',fixed_tag],artifacts['fixed10ns_calibration']),
    ]
    records = {}
    for name, argv, result in stages:
        command = [sys.executable,str(s/argv[0]),*argv[1:]]
        write_new(out/(name+'_started.json'), {'utc':utc(),'command':command,'script_sha256':sha(s/argv[0])})
        print('RECOVERY_START',name,flush=True)
        with (out/(name+'.log')).open('x') as log:
            rc = subprocess.run(command,cwd=root,stdout=log,stderr=subprocess.STDOUT).returncode
        passed = rc == 0 and (r/result).exists() and load(r/result)['all_pass']
        record = out/(name+'_terminal.json')
        write_new(record, {'utc':utc(),'command':command,'returncode':rc,'passed':passed,'artifact':result,
                           'artifact_sha256':sha(r/result) if (r/result).exists() else None})
        records[name] = rel(record)
        if not passed: raise RuntimeError('recovery tail failed: '+name)
        print('RECOVERY_PASS',name,flush=True)
    hashes = {}
    # Bind the complete new tails, including negative overflow logs and every
    # raw comparison file, not merely a Boolean in their summary.
    for folder in [r/'rtl'/(v+'_'+hot_tag),r/'model'/m/boundary_tag,r/'rtl'/(v+'_'+fixed_tag),out]:
        for file in sorted(folder.rglob('*')):
            if file.is_file(): hashes[rel(file)] = sha(file)
    qualification = dict(status='passed',observed_at=utc(),RTL=v,model=m,OOC=plan['OOC'],
        inventory=rel(out/'inventory.json'),inventory_sha256=sha(out/'inventory.json'),
        tail_stages=records,evidence_sha256=hashes,**artifacts)
    write_new(out/'qualification.json',qualification)
    validate_recovery(rel(out/'qualification.json'),plan,require_terminal=False)
    write_new(out/'terminal.json',{'status':'passed','utc':utc(),'qualification_sha256':sha(out/'qualification.json')})
    print('RECOVERY_QUALIFIED',rel(out/'qualification.json'),flush=True)
except Exception as error:
    write_new(out/'failed.json', {'status':'failed_preserved','utc':utc(),'error':repr(error)})
    raise

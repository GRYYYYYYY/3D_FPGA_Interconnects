"""One isolated construction observation per case, with exact backing hashes.

Run only after formal CPU and all model/EDA work are terminal. These observations
measure conversion, not repeated statistical CPU resident performance.
"""
import importlib.util,json,os,subprocess,time,datetime
from pathlib import Path
s=Path(__file__).with_name('formal.py');spec=importlib.util.spec_from_file_location('formal',s);f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
r=f.R;out=r/'construction_isolated_a';out.mkdir(exist_ok=False)
bind=json.loads((f.D/'binding.json').read_text());binary=f.D/'bin/convert';assert f.sha(binary)==bind['binary_sha256']['convert']
a=f.activity();time.sleep(1);b=f.activity();assert not f.changed(a,b),'Competing process: preserve rejected attempt'
rows=[]
for case in ['bnn_export','lstm_s2']:
 dest=out/case;cmd=['taskset','-c',str(min(os.sched_getaffinity(0))),str(binary),bind['inputs'][case]['workload'],str(dest)];start=datetime.datetime.now(datetime.timezone.utc).isoformat();t=time.monotonic();observed=[];last=f.activity()
 with (out/(case+'.log')).open('x') as log:
  p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
  while p.poll() is None:
   time.sleep(.5);current=f.activity();observed+=f.changed(last,current,[p.pid]);last=current
 wall=time.monotonic()-t
 assert p.returncode==0
 a=json.loads((dest/'admission.json').read_text());old=json.loads((f.D/'receipts'/(case+'_conversion.json')).read_text());hashes={name:f.sha(dest/name) for name in ['descriptors.bin','edges.bin','rows.bin']}
 for name,h in hashes.items():assert h==old['output_sha256'][str(f.D/'cases'/case/name)]
 row={'case':case,'command':cmd,'start_utc':start,'total_process_wall_seconds':wall,'returncode':p.returncode,'binary_sha256':f.sha(binary),'workload_sha256':bind['inputs'][case]['workload_sha256'],'output_sha256':hashes,'admission':a,'observed_active_competitors':observed,'timing_contention_qualified':not observed,'independent_process_observations':1,'note':'Converter admission JSON retains its conservative default contention=false; this external observer qualifies only this isolated run, not older construction measurements.'};rows.append(row);f.dump(out/(case+'_receipt.json'),row)
f.dump(out/'terminal.json',{'all_exact':True,'all_isolated':all(x['timing_contention_qualified'] for x in rows),'rows':rows});print('ISOLATED_CONSTRUCTION_COMPLETED')

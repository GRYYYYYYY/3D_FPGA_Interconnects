"""Read-only job supervision and automatic analysis of completed paired controls."""
from pathlib import Path
import datetime,fcntl,json,os,subprocess,sys,time
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_r2_20261112'
config=json.loads(Path(sys.argv[1]).read_text());d=r/'supervision'/sys.argv[2];d.mkdir(exist_ok=False)
helper='/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/skills/inspire-gpu-submit/scripts/inspire_gpu.py';job=config['job_id'];o=r/'software'/config['run_tag'];last=None;count=0
def write(name,x):
 with (d/(name+'.json')).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
write('started',{'pid':os.getpid(),'job_id':job,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'read-only supervision; no resubmission, cancellation or resource changes'})
while True:
 if (o/'failed.json').exists():
  write('terminal',{'status':'worker_failed_preserved','worker_failure':json.loads((o/'failed.json').read_text())});sys.exit(1)
 if (o/'completed.json').exists():
  cmd=[sys.executable,str(Path(__file__).with_name('analyze_private_inf_software.py')),config['run_tag']]
  with (d/'analysis.log').open('x') as log:rc=subprocess.run(cmd,cwd=root,stdout=log,stderr=subprocess.STDOUT).returncode
  write('terminal',{'status':'analyzed' if rc==0 else 'analysis_failed_preserved','returncode':rc,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'summary':str(o/'summary.json')});sys.exit(rc)
 p=subprocess.run([sys.executable,helper,'status',job],cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 try:state=json.loads(p.stdout);status=state['Result']['status']
 except (ValueError,KeyError):state={'returncode':p.returncode,'stderr':p.stderr};status='status_unavailable'
 if status!=last:
  write(f'observation_{count}',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':status,'response':state});last=status;count+=1
 if status in ['job_failed','job_stopped','job_cancelled']:
  write('terminal',{'status':'job_failed_preserved','job_status':status,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()});sys.exit(1)
 # Completed.json is written by the worker after all verified output closes.
 if status=='job_succeeded' and not (o/'completed.json').exists():
  write('terminal',{'status':'missing_worker_terminal','utc':datetime.datetime.now(datetime.timezone.utc).isoformat()});sys.exit(1)
 time.sleep(60)

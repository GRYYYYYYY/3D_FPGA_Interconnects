"""Independent GPU chain: wait, audit/paired stats, byte-verified archive and push."""
from pathlib import Path
import datetime,fcntl,hashlib,json,os,subprocess,sys,time,traceback
from publish_evidence_subset import ROOT,R,publish
cfg_path=Path(sys.argv[1]).resolve();cfg=json.loads(cfg_path.read_text());tag=sys.argv[2];d=R/'supervision'/tag;d.mkdir(exist_ok=False)
lock=(R/'supervision'/('software_finalize_'+cfg['run_tag']+'.lock')).open('a');fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
def write(name,x):
 with (d/(name+'.json')).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
write('started',{'pid':os.getpid(),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'config':cfg,'config_sha256':hashlib.sha256(cfg_path.read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'HEAD':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()})
try:
 o=R/'software'/cfg['run_tag'];watch=R/'supervision'/cfg['watch_tag']
 while not (o/'completed.json').exists() and not (o/'failed.json').exists() and not (watch/'terminal.json').exists():time.sleep(30)
 successful=(o/'completed.json').exists()
 if successful:
  with (d/'analysis.log').open('x') as f:subprocess.run([sys.executable,str(Path(__file__).with_name('analyze_private_inf_software.py')),cfg['run_tag']],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
  summary=json.loads((o/'summary.json').read_text());assert summary['receipt_count']==254 and summary['all_receipts_pass']
 roots=[cfg['source_snapshot'],str(Path(cfg['submission']).parent),'supervision/'+cfg['watch_tag']]
 if o.exists():roots.append('software/'+cfg['run_tag'])
 delivery=publish('software_'+cfg['run_tag']+'_terminal',roots,'Independent software chain; '+('254 qualified execution receipts and paired statistics; stronger historical/new target retained' if successful else 'failed attempt preserved; not qualified timing'),d)
 write('terminal',{'status':'qualified_archived_remote_verified' if successful else 'failed_archived_remote_verified','delivery':delivery,'other_chains_not_implied_complete':True})
except BaseException as error:
 write('failed_preserved',{'error':repr(error),'traceback':traceback.format_exc()});raise

from pathlib import Path
import subprocess,json,hashlib,gzip,datetime,concurrent.futures
ROOT=Path(__file__).resolve().parents[4];S=ROOT/'accel/lookahead/fpga_enum_commit/front';R=ROOT/'results/fpga_enum_commit_20261114/front_compare_a';BASE='1e312d6e4ffc5ea96f25c0b97931ad028e710584'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def blob(p):return subprocess.check_output(['git','show',BASE+':'+p],cwd=ROOT)
def restore(manifest,prefix,outroot):
 for x in manifest['files']:
  if not x['raw_path'].startswith(prefix):continue
  raw=blob('results/fpga_pending_stream_20261114/evidence_snapshot/'+x['archive']);raw=gzip.decompress(raw) if x['archive'].endswith('.gz') else raw
  assert hashlib.sha256(raw).hexdigest()==x['sha256'];p=outroot/Path(x['raw_path']).name;p.write_bytes(raw)
def main():
 R.mkdir(parents=True,exist_ok=False);(R/'source').mkdir()
 for p in S.glob('*'):
  if p.is_file():(R/'source'/p.name).write_bytes(p.read_bytes())
 cmd=['g++','-O3','-std=c++17','-ffp-contract=off',*['-I'+str(ROOT/'accel/lookahead'/x) for x in ['include','round6_1','fpga_sparse_stream_r2']],str(S/'frontend_model.cpp'),'-o',str(R/'front')]
 with (R/'build.log').open('x') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
 (R/'build_binding.json').write_text(json.dumps({'base':BASE,'command':cmd,'source_sha256':{p.name:sha(p) for p in (R/'source').iterdir()},'binary_sha256':sha(R/'front'),'compiler':subprocess.check_output(['g++','--version'],text=True)},indent=2))
 bind=json.loads(blob('results/fpga_decoupled_front_20261114/evidence_snapshot/profile_a/reused_binding.json'))
 oldman=json.loads(blob('results/fpga_pending_stream_20261114/evidence_snapshot/manifest.json'));newman=json.loads(blob('results/fpga_decoupled_front_20261114/evidence_snapshot/manifest.json'));cases=[]
 for rec in bind['input_receipts']:
  case=Path(rec['command'][3]).name;d=R/case;d.mkdir();restore(oldman,'capture_a/'+case+'/wave_',d)
  for p in d.glob('*.bin'):cases.append((case,p,rec['command'][1],False))
  if case in ['bnn_export','lstm_s2']:
   x=next(x for x in newman['files'] if x['raw_path']=='front_stress_b/'+case+'.bin');raw=blob('results/fpga_decoupled_front_20261114/evidence_snapshot/'+x['archive']);raw=gzip.decompress(raw) if x['archive'].endswith('.gz') else raw;assert hashlib.sha256(raw).hexdigest()==x['sha256'];p=d/'stress.bin';p.write_bytes(raw);cases.append((case,p,rec['command'][1],True))
 assert len(cases)==19
 tasks=[(case,trace,workload,jitter,mode,width) for case,trace,workload,jitter in cases for mode in ['FIRST_FREE','LANE_RR'] for width in [0,8]]
 def run(task):
  case,trace,w,j,mode,width=task;p=trace.parent/(trace.stem+'_'+mode+'_d'+str(width));cmd=[str(R/'front'),w,str(trace),'B',str(p)+'.json','jitter' if j else 'fixed',mode,str(width)];start=datetime.datetime.now(datetime.timezone.utc).isoformat()
  with Path(str(p)+'.log').open('x') as log:
   proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT);Path(str(p)+'.running.json').write_text(json.dumps({'pid':proc.pid,'command':cmd,'start_utc':start}));rc=proc.wait()
  row={'command':cmd,'returncode':rc,'start_utc':start,'end_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'binary_sha256':sha(R/'front'),'trace_sha256':sha(trace),'input_sha256':next(x['workload_sha256'] for x in bind['input_receipts'] if x['command'][1]==w)};Path(str(p)+'.receipt.json').write_text(json.dumps(row,indent=2));return row
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(run,tasks))
 assert all(x['returncode']==0 for x in rows)
 comparisons=[]
 for case,trace,w,j in cases:
  vs={(mode,width):json.loads((trace.parent/(trace.stem+'_'+mode+'_d'+str(width)+'.json')).read_text()) for mode in ['FIRST_FREE','LANE_RR'] for width in [0,8]}
  if trace.stem!='stress':oldpath='front_b/'+case+'/'+trace.stem+'_B.json'
  else:oldpath='front_stress_b/'+case+'_B.json'
  x=next(x for x in newman['files'] if x['raw_path']==oldpath);raw=blob('results/fpga_decoupled_front_20261114/evidence_snapshot/'+x['archive']);raw=gzip.decompress(raw) if x['archive'].endswith('.gz') else raw;old=json.loads(raw)
  assert vs['FIRST_FREE',0]['cycles']==old['cycles'],(case,trace.stem,'compat cycles')
  assert vs['FIRST_FREE',0]['lane_emit']==old['lane_emit']
  for v in vs.values():
   assert v['all_operand_candidates_and_target_outputs_exact'];assert sum(v['lane_emit'])==v['candidates'];assert v['metadata_requests']==v['parents']
   assert v['traffic_by_kind_port']==old['traffic_by_kind_port'];assert all(sum(h)==v['cycles'] for h in v['occupancy_H_E_M_slots_fork_ready_histograms'])
  comparisons.append({'case':case,'wave':trace.stem,'trace_sha256':sha(trace),'old_compatibility_exact':True,'cycles':{m+'_d'+str(width):v['cycles'] for (m,width),v in vs.items()},'zero_emission_lanes':{m+'_d'+str(width):sum(n==0 for n in v['lane_emit']) for (m,width),v in vs.items()}})
 (R/'terminal.json').write_text(json.dumps({'all_pass':True,'count':len(rows),'comparisons':comparisons,'receipts':rows,'scope':'front-only paired allocation mechanism; no full hardware qualification','fpga_seconds':None,'board_measured':False},indent=2));print('FRONT_COMPARE_PASS cases=19 paired_runs=76 compatibility=19')
if __name__=='__main__':main()

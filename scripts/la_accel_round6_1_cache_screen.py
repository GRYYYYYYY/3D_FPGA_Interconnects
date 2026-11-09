"""Finite cache diagnostics, gated on completed updated software budget."""
import json,sys,time,subprocess,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];r=Path(sys.argv[1]).resolve();o=r/'cache_screen';o.mkdir(exist_ok=False);deadline=time.monotonic()+7200
while True:
 p=r/'gpu_worker/measurements.json'
 if p.exists():
  try:rows=json.load(open(p))
  except json.JSONDecodeError:rows=[]
  if len(rows)==87:break
 if (r/'gpu_worker/finished.json').exists() and json.load(open(r/'gpu_worker/finished.json'))['status']=='failed':raise RuntimeError('updated software failed; cache screen not started')
 if time.monotonic()>deadline:raise RuntimeError('updated budget unavailable')
 time.sleep(15)
import statistics
values={}
for x in rows:
 key=(x['case'],x['kind'],x['workers']);values.setdefault(key,[]).append(statistics.median(z.get('E1_s',z.get('resident_s')) for z in x['measurements'][1:]))
target=min(statistics.median(v) for (case,kind,w),v in values.items() if case=='bnn_export');edges=1286937147
necessary=[dict(lanes=l,frequency_hz=f,ideal_s=edges/(l*f),required_utilization_20percent=edges/(l*f*target*.8)) for l in [16,32,64] for f in [125000000,200000000]]
gate=dict(updated_best_E1_s=target,necessary_sensitivity=necessary,selected_lanes=64,selected_banks=64,frequency_status='unknown, references are sensitivity only',bandwidth_status='unknown; no controller/random-RMW measurement',headers_bytes=4096*8*16,bitmap_bytes=4096,chunk_pool_per_qid=16384,member_capacity_per_qid=524288,chunk_metadata_bytes=16384*8*32,member_bytes=524288*8*4,full_cycle_gate='UNRESOLVED; no supported memory service parameters; only functional transaction replay below')
(o/'necessary_gate.json').write_text(json.dumps(gate,indent=2))
if edges/(64*200000000)>target*.8:
 (o/'finished.json').write_text(json.dumps(dict(status='NO_GO',reason='even ideal64lane200MHz edge budget lacks20percent margin')));sys.exit(0)
paths={c:R/'results/lookahead_accel_20261108T125500Z'/c/'workload.bin' for c in ['tseng_export','bnn_export']};samples=[];commands=[]
def run(name,cmd,timeout):
 begin=time.monotonic()
 with (o/(name+'.log')).open('w') as f:
  try:p=subprocess.run(list(map(str,cmd)),stdout=f,stderr=subprocess.STDOUT,timeout=timeout);rc=p.returncode
  except subprocess.TimeoutExpired:rc=124
 commands.append(dict(name=name,command=list(map(str,cmd)),returncode=rc,elapsed_s=time.monotonic()-begin));(o/'commands.json').write_text(json.dumps(commands,indent=2))
 if rc:return None
 return [json.loads(x) for x in (o/(name+'.log')).read_text().splitlines() if x.startswith('{')]
for capacity in [16,32,64,128]:
 z=run('window_'+str(capacity),[r/'cache61',paths['bnn_export'],capacity,'sample'],120)
 if z is None:
  (o/'finished.json').write_text(json.dumps(dict(status='UNRESOLVED',reason='bounded window failed')));sys.exit(0)
 assert sum(x['events'] for x in z)<=5000000
 samples.append(dict(capacity=capacity,rows=z,hit_rate=sum(x['cache_hits'] for x in z)/sum(x['events'] for x in z)))
best=samples[-1]['hit_rate'];chosen=next(x['capacity'] for x in samples if x['hit_rate']>=best-.02);(o/'selection.json').write_text(json.dumps(dict(rule='smallest capacity within2percentagepoints of128 hit rate; <=5M candidates/config; qid0 waves1,10,30,50,59; no full-input parameter sweep',samples=samples,chosen=chosen),indent=2))
full=[]
for case,path in paths.items():
 z=run(case+'_full',[r/'cache61',path,chosen,'full'],1200)
 if z is None:
  (o/'finished.json').write_text(json.dumps(dict(status='UNRESOLVED',reason='full functional transaction replay failed or timed out',case=case)));sys.exit(0)
 assert len(z)==(8 if case=='tseng_export' else 40) and all(x['whole_pair_home_equal'] and x['status']==0 for x in z)
 full.append(dict(case=case,rows=z))
(o/'full_transactions.json').write_text(json.dumps(full,indent=2));(o/'finished.json').write_text(json.dumps(dict(status='UNRESOLVED',functional_full_batch_replay_complete=True,finite_timed_full_batch_model_complete=False,reason='proposal/chunk capacity and pair semantics replayed; DRAM latency/bandwidth, outstanding transactions, FIFO backpressure, RAW forwarding and achieved frequency have no supported cycle contract; no positive hardware gate'),indent=2))

from pathlib import Path
import csv,json,statistics,hashlib,shutil,datetime,sys
ROOT=Path(__file__).resolve().parents[4];RAW=ROOT/'results/fpga_enum_commit_integration_20261114_a/fixtures';OUT=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'results/fpga_enum_commit_integration_20261114_fixed/sim_c'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def summary(a):return {'n':len(a),'mean':statistics.mean(a) if a else None,'median':statistics.median(a) if a else None,'min':min(a) if a else None,'max':max(a) if a else None}
def main():
 OUT.mkdir(exist_ok=False)
 sim=OUT.parent/'project/backend_fixed.sim/sim_1/behav/xsim'
 for p in sim.glob('*.log'):shutil.copy2(p,OUT/p.name)
 for glob in ['metrics*','trace*','transactions*','calibration*','port_cycle_replay.json']:
  for p in RAW.glob(glob):shutil.copy2(p,OUT/p.name)
 log=(OUT/'simulate.log').read_text();assert 'TEST_PASS matched_backend_native_and_stress' in log and 'Fatal' not in log
 files=[ROOT/'accel/lookahead/fpga_sparse_stream_r2/rtl'/x for x in ['sync_fifo.sv','inf_flat_bank.sv','inf_scratch_boundary.sv','pending17_service.sv']]
 files += [ROOT/'accel/lookahead/fpga_enum_commit'/x for x in ['enumerator/enum2_bank.sv','enumerator/scratch_finalize.sv','canonical/ec_pending_k8.sv','canonical/ec_tagged_port.sv','integration/ec_backend_owner.sv','integration/tb_backend.sv',('integration/run_sim_final.tcl' if OUT.name=='sim_d' else 'integration/run_sim_fixed.tcl')]]
 binding={}
 for p in files:
  rel=p.relative_to(ROOT);q=OUT/'source'/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q);binding[str(rel)]=sha(p)
 versions=[];compared=[]
 for variant in [0,1]:
  rows=list(csv.DictReader((OUT/f'metrics_{variant}.csv').open()));transactions=list(csv.DictReader((OUT/f'transactions_{variant}.csv').open()));previous=[0,0,0,0]
  assert len(rows)==19
  for row in rows:
   d={k:(v if k=='case' else int(v)) for k,v in row.items()}
   ts=[{k:(v if k=='case' else int(v)) for k,v in t.items()} for t in transactions if t['case']==d['case'] and int(t['wave'])==d['wave']]
   assert len(ts)==d['commits']==d['retired'] and d['requests']==d['responses']
   assert all(t['accept']<=t['feedback']<=t['retire'] for t in ts)
   assert sum(t['mask'].bit_count() for t in ts)==d['directory']
   current=[d[x] for x in ['spill0','spill1','enum0','enum1']];delta=[a-b for a,b in zip(current,previous)];previous=current
   d['actual_spill_delta']=delta[:2];d['resident_fragments_delta']=delta[2:]
   d['enum_fragment_interval_mean']=[d[f'scan_span{b}']/(delta[b+2]-1) if delta[b+2]>1 else None for b in [0,1]]
   d['commit_accept_interval_mean']=[d[f'commit_span{b}']/(sum(t['bank']==b for t in ts)-1) if sum(t['bank']==b for t in ts)>1 else None for b in [0,1]]
   d['fully_retired_interval_mean']=[d[f'retire_span{b}']/(sum(t['bank']==b for t in ts)-1) if sum(t['bank']==b for t in ts)>1 else None for b in [0,1]]
   d['transaction_feedback_cycles']=summary([t['feedback']-t['accept'] for t in ts]);d['transaction_full_retirement_cycles']=summary([t['retire']-t['accept'] for t in ts]);d['feedback_to_retire_cycles']=summary([t['retire']-t['feedback'] for t in ts])
   compared.append({'variant':variant,**d})
  versions.append(rows)
 for a,b in zip(*versions):assert (a['case'],a['wave'],a['candidates'],a['commits'],a['directory'])==(b['case'],b['wave'],b['candidates'],b['commits'],b['directory'])
 latency_hist=[]
 for variant in [0,1]:
  from collections import Counter
  live={};hist=Counter()
  for row in csv.DictReader((OUT/f'trace_{variant}.csv').open()):
   t=int(row['cycle'])
   if int(row['response']):hist[t-live.pop(int(row['response_tag']))]+=1
   if int(row['request']):live[int(row['tag'])]=t
  assert not live and set(hist)=={16},hist
  latency_hist.append(dict(hist))
 (OUT/'analysis.json').write_text(json.dumps({'status':'LOCAL_FUNCTIONAL_AND_CYCLE_QUALIFIED_TIMING_PENDING','scope':'two-subbank owner0 projection; labels preloaded, PV actual clear; excludes fullgraph/front/initialize timing','contract':{'latency_ns':80,'gap_ns':5,'frequency_hz':200000000,'ports':1,'credits':32,'response_available_cycles':16,'response_acceptance':'after sr, may later','baseline':'actual old enum5/serial scratch/pending17_service K1','candidate':'enum2/scratch fast+merge/K8','strict_directory_retirement':True},'physical_handshake_latency_histograms':latency_hist,'variants':compared,'fpga_seconds':None,'board_measured':False},indent=2)+'\n')
 receipt={'status':'PASS','tool':'Vivado/XSim2022.2','fixtures':16,'waves_per_variant':19,'variants':2,'source_sha256':binding,'command':'source accel/lookahead/fpga_enum_commit/integration/'+('run_sim_final.tcl' if OUT.name=='sim_d' else 'run_sim_fixed.tcl'),'terminal_observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'fixture_manifest_sha256':sha(RAW/'manifest.json'),'output_sha256':{p.name:sha(p) for p in OUT.iterdir() if p.is_file()},'no_complete_wiremap_claim':True,'board_measured':False}
 (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 print('INTEGRATION_ANALYSIS_PASS',len(compared),'rows')
 for x in compared:
  if x['case'].startswith(('bnn','lstm')):print(x['variant'],x['case'],x['cycles'],x['transaction_feedback_cycles'],x['fully_retired_interval_mean'])
if __name__=='__main__':main()

import pathlib,json,tarfile,statistics,hashlib
root=pathlib.Path(__file__).resolve().parents[4];r=root/'results/fpga_sim_restart_20261111T231000Z/closed_loop';out=r/'baselines';out.mkdir(exist_ok=True)
p=root/'results/lookahead_accel_round6_1_20261109T160000Z/evidence_snapshot/run_logs.tar.gz'
with tarfile.open(p) as t:
 raw=t.extractfile('gpu_worker/measurements.json').read();worker=t.extractfile('gpu_worker/worker.json').read()
(out/'historical_measurements.json').write_bytes(raw);(out/'historical_worker.json').write_bytes(worker)
rows=json.loads(raw);summary=[]
for case in sorted({x['case'] for x in rows}):
 for kind in ['gpu_compact','early','strict']:
  selected=[x for x in rows if x['case']==case and x['kind']==kind and x['workers'] in ([0] if kind=='gpu_compact' else [8])]
  if not selected:continue
  values=[];proc=[]
  for x in selected:
   vals=[m['resident_s'] for m in x['measurements'] if m['repeat']>0];assert len(vals)==3;values+=vals;proc.append({'id':x['process'],'raw_s':vals,'mean_s':statistics.mean(vals)})
  assert len(proc)==3
  summary.append({'case':case,'backend':kind,'source_timer':'resident_s','processes':proc,'mean_s':statistics.mean(values),'sample_sd_s':statistics.stdev(values),'between_process_mean_sample_sd_s':statistics.stdev(x['mean_s'] for x in proc),'scope':'RESIDENT_COMPLETE_BATCH_V2','output_destination':'device_DRAM' if kind=='gpu_compact' else 'host_DRAM','cohort':'historical R6.1 GPU worker, source timer boundary inspected','algorithm':'ALT compact shift20' if kind=='gpu_compact' else 'STRICT full/early CPU; existing semantic track'})
for case in ['native_d3_w8','native_d4_w8','bnn_export','lstm_s2']:
 proc=[];values=[]
 for i in range(3):
  data=[json.loads(x) for x in (r/f'cpu/{case}_p{i}.jsonl').read_text().splitlines()];assert len(data)==4 and all(x['output_equal'] for x in data)
  vals=[x['resident_s'] for x in data if not x['warmup']];values+=vals;proc.append({'id':i,'raw_s':vals,'mean_s':statistics.mean(vals)})
 summary.append({'case':case,'backend':'original_ALT_CPU','source_timer':'resident_s','processes':proc,'mean_s':statistics.mean(values),'sample_sd_s':statistics.stdev(values),'between_process_mean_sample_sd_s':statistics.stdev(x['mean_s'] for x in proc),'scope':'RESIDENT_COMPLETE_BATCH_V2','output_destination':'host_DRAM','cohort':'new local FPGA tooling host; not paired with historical GPU host'})
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
(out/'scope_audit.json').write_text(json.dumps({'historical_archive_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_entry':'gpu_worker/measurements.json','basic_cuda6_old_timer':'both E1_s and device_timeline_including_host_gaps_s include final packed D2H; excluded from V2 ratios','compact_cuda61_timer':'resident_s ends before final D2H, contains all wave host controls and completion copies','strict61_timer':'resident_s includes per-sample reset, search, target/output writes, parallel batch completion; Prepared/input admission outside','original_VPR_multithread':'not_evaluated_same_scope; E2 retained separately','new_GPU_measurement_block':'Inspire doctor returned session expired invalid_grant; no job submitted'},indent=2)+'\n')
print(json.dumps([{k:x[k] for k in ['case','backend','mean_s','sample_sd_s']} for x in summary],indent=2))

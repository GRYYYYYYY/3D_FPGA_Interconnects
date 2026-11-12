"""A necessary work bound for this fixed service structure, NOT a prediction."""
from pathlib import Path
import csv,json,math,hashlib
root=Path(__file__).resolve().parents[3];run=root/'results/fpga_sparse_stream_20261112'
gpu=json.load(open(root/'results/fpga_sim_restart_20261111T231000Z/gpu_v2_supplement/summary.json'))
rows=[]
for name in ['bnn_export','lstm_s2']:
 waves=list(csv.DictReader(open(run/name/'waves.csv')))
 expand=closure=closed_ids=0
 per_wave=[]
 for i,w in enumerate(waves):
  end=i+1==len(waves) or (waves[i+1]['sample'],waves[i+1]['bucket'])!=(w['sample'],w['bucket'])
  c=int(w['closed']) if end else 0
  # Every candidate consumes distinct IDLE and TAG cycles in its owner.
  # Eight best-case tile closure engines; each record consumes states 0,1,3
  # even with an immediately available row-cache hit and no target update.
  e=math.ceil(2*int(w['candidates'])/64);cl=math.ceil(3*c/8)
  expand+=e;closure+=cl;closed_ids+=c
  per_wave.append({'sample':int(w['sample']),'wave':int(w['wave']),'expand_min_cycles':e,'closure_min_cycles':cl})
 baseline=next(x for x in gpu['rows'] if x['case']==name and x['backend']=='compact')['mean_s']
 rows.append({'case':name,'complete_jobs':40,'candidate_lanes':64,'candidate_owners':64,'optimistic_independent_closure_engines':8,
  'max_candidates_per_cycle':32,'max_closed_records_per_cycle':8/3,'expand_min_cycles':expand,'closure_min_cycles':closure,'closed_records':closed_ids,
  'sum_min_cycles_ignoring_commit_init_memory_and_drain':expand+closure,'frequency_assumed_hz':200000000,
  'necessary_seconds_not_prediction':(expand+closure)/200000000,'compact_cuda_resident_seconds':baseline,
  'necessary_frequency_to_equal_GPU_ignoring_other_work_hz':(expand+closure)/baseline,
  'fails_at_declared_200MHz':(expand+closure)/200000000>baseline,'per_wave':per_wave})
result={'candidate':'SPARSE_STREAMED_ALT_V2','revision':'resident_batch_commit16','board_measured':False,
 'type':'optimistic necessary bound; NOT measured service rate or architecture simulation prediction',
 'proof':['sparse_owner IDLE consumes one request, TAG consumes a separate cycle even for an MSHR merge; thus <=1 candidate/2 owner cycles',
 'sparse_tile closed record is accepted only in close_state0 and must visit1 and3 before another can be accepted; minimum3 cycles even without external latency',
 'grant eight independent closure engines to the proposed eight-tile64owner replication, ignoring output conflicts and communication',
 'wave expansion, commit and bucket closure are separated by required barriers; sum bounds across waves and all40samples, Q=1',
 'commit, initialization, memory traffic, route conflicts, output and drain omitted to make the bound optimistic'],
 'gate':'do not expand this structure to a full64lane OOC at200MHz; no claim that other service structures or FPGA architectures are impossible',
 'rows':rows,'source_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [root/'accel/lookahead/fpga_sparse_stream/rtl/owner_sync.sv',root/'accel/lookahead/fpga_sparse_stream/rtl/sparse_tile.sv',run/'bnn_export/waves.csv',run/'lstm_s2/waves.csv']}}
(run/'optimistic_bound.json').write_text(json.dumps(result,indent=2)+'\n')
for row in rows:print(row['case'],row['necessary_seconds_not_prediction'],row['compact_cuda_resident_seconds'])

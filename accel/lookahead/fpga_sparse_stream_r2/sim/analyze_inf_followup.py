"""Complete explicit storage reservation and measured/simulated evidence separation."""
from pathlib import Path
import hashlib,json,sys,csv
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_r2_20261112';out=r/'inf_followup_5af9908'/sys.argv[1]
rows=[]
for case,target in [('bnn_export',.151799969444),('lstm_s2',.159888578444)]:
 for tag in ['inf_finite_native_a','inf_finite_native_b','inf_finite_native_c_gap10ns','inf_finite_native_d_125MHz']:
  d=r/'accumulator'/tag/case
  if not (d/'receipt.json').exists():continue
  receipt=json.loads((d/'receipt.json').read_text());assert receipt['returncode']==0 and receipt['output_exact']
  m=json.loads((d/'finite_service.json').read_text());cap=json.loads((d/'capacity.json').read_text());bounds={}
  for kind in ['member','active']:
   peaks=cap[kind]['line_hash_64_peak'];bounds[kind]=max(peaks[i]+peaks[i+32] for i in range(32));assert bounds[kind]<=8192
  assert m['peak_spill_list']<=2048 and m['peak_fragment_queue']<=8 and m['peak_port_credits']<=32
  rows.append({'case':case,'variant':tag,'model_sha256':hashlib.sha256((d/'finite_service.json').read_bytes()).hexdigest(),'cycles':m['cycles'],'assumed_MHz':m.get('assumed_MHz',200),'conditional_schedule_seconds':m['cycles']/(m.get('assumed_MHz',200)*1e6),'prepared_POP_target_s':target,'exceeds_target_for_this_schedule':m['cycles']>target*m.get('assumed_MHz',200)*1e6,'capacity_per_owner_upper_bounds':bounds,'total_external_bytes':32*sum(sum(x) for x in m['traffic32B_by_operation_by_physical_port']),'spill_peak':m['peak_spill_list'],'fpga_seconds':None,'board_measured':False})
# Every allocation below has one owner. Removed state128/changed structures are
# listed explicitly, not silently retained alongside packed64 state.
ledger=[
 {'module':'flat payload','count':64,'shape':'4 columns4096x64/subbank','URAM':256,'BRAM36eq':0,'basis':'two-bank synth8URAM'},
 {'module':'pending17','count':64,'shape':'4 columns4096x68/subbank; whole-word1R1W; ECCoff','URAM':256,'BRAM36eq':0,'basis':'two-bank synth8URAM'},
 {'module':'tag+mask','count':64,'shape':'4ways1024x36','URAM':0,'BRAM36eq':256,'basis':'two-bank synth8BRAM36'},
 {'module':'occupied slot list','count':64,'shape':'4096x12','URAM':0,'BRAM36eq':96,'basis':'two-bank synth2BRAM36+2BRAM18'},
 {'module':'spill and consumed bitmap','count':64,'shape':'256x128','URAM':0,'BRAM36eq':128,'basis':'two-bank synth4BRAM36'},
 {'module':'spilled IDs','count':64,'shape':'2048x20','URAM':0,'BRAM36eq':96,'basis':'two-bank synth2BRAM36+2BRAM18'},
 {'module':'directory/member/header/next/free pool','count':32,'shape':'existing5 direct+2pool URAM perowner','URAM':224,'BRAM36eq':0,'basis':'old actual9URAM/owner less2 changed-list URAM; no state128 mirror'},
 {'module':'phase-separated active parents','count':32,'shape':'8192x96 perowner;2width x2depth URAM','URAM':128,'BRAM36eq':0,'basis':'reservation required by finite model POP-before-expansion; not present in micro'},
 {'module':'physical request and response FIFOs','count':128,'shape':'64x320 request +64x288 response; pessimistic72bit BRAM width packing','URAM':0,'BRAM36eq':1152,'basis':'explicit future reservation9blocks/client; existing old-router BRAM NOT added'},
 {'module':'front-end queues','count':64,'shape':'64x96','URAM':0,'BRAM36eq':96,'basis':'1BRAM36+1BRAM18/client; no double counting active storage'},
 {'module':'runtime cost table','count':64,'shape':'16x64 duplicated registers/LUTRAM','URAM':0,'BRAM36eq':0,'basis':'65536bits register reservation; mandatory HBM load counted'},
 {'module':'output/control buffers','count':1,'shape':'64BRAM36 reserved; no graph-sized onchip output mirror','URAM':0,'BRAM36eq':64,'basis':'external output lines and final drain count in finite model'}]
tot={k:sum(x[k] for x in ledger) for k in ['URAM','BRAM36eq']}
value={'scope':'explicit finite storage reservation and uncalibrated event schedules; not a full-candidate OOC or measured speed','ledger':ledger,'totals':tot,'device_capacity':{'URAM':960,'BRAM36eq':2016},'removed':['old128bit canonical cache/mirror','old changed-list URAM64 and four mark FIFOs perowner','old owner random-RMW cache','old router FIFO allocations replaced by explicit new allocation'],'external_storage':{'MAX_N':4194304,'canonical_bytes':33554432,'scratch_bytes':33554432,'scratch_validity':'two finite per-subbank bitmaps; no uninitialized read','graph_CSR':'finite input-bound allocations, eligible prepared CSR identity preserved; no hidden onchip full graph','output':'input.cells x jobs x8, external bound checked by workload loader'},'clock_contract':{'assumed_MHz':200,'latency_ns':80,'gap_ns':5,'board_measured':False,'full_kernel_FPGA_seconds':None},'finite_schedule_rows':rows,'limitations':['Resource reservation is not physical placement. LUT/FF/global fanout/arbitration timing require full integration; no full integration passes the performance gate.','Schedule A retains conservative source-order reservations as a negative diagnostic. Schedule B uses64 finite chronological contexts and recomputes spills; neither inherits old calibration.','Model PV/control latencies and phase-separated active-list scheduling are assumptions; no exact full-candidate RTL cycle calibration.','Micro has serial pending service and one outstanding scratch command per subbank; it proves finite protocols and atomicity, not high-throughput integrated finalization.','Remaining router/global-controller costs cannot be assumed free. Model schedules already miss the strongest old software target by a large margin.','The partial0.143656/0.145130s bounds are neither full prediction nor measurements.']}
with out.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
print(tot)
for x in rows:print(x['case'],x['variant'],x['cycles'],x['conditional_schedule_seconds'])

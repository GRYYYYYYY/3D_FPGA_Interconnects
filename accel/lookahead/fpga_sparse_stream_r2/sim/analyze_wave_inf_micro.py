from pathlib import Path
import csv,hashlib,json,struct,sys
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_r2_20261112';out=r/'analysis'/(sys.argv[1] if len(sys.argv)>1 else 'wave_inf_micro_verification.json');rows=[]
for tag in ['rtl_micro_a','rtl_micro_occupied_b','rtl_micro_capacity_c','rtl_micro_ram_d']:
 d=r/'accumulator'/tag;rec=json.loads((d/'receipt.json').read_text());assert rec['all_pass']
 for row in rec['results']:
  name=row['case'];m=json.loads(row['log']);trace=d/(name+'_cycles.csv');count=accepts=duals=0;first=None;last=0;peak_retire=0;oldret=(0,0)
  for x in csv.DictReader(trace.open()):
   c=int(x['cycle']);mask=int(x['accept_mask']);n=mask.bit_count();count+=1;accepts+=n;duals+=mask==3
   if n:first=c if first is None else first;last=c
   ret=(int(x['retire0']),int(x['retire1']));delta=sum(ret)-sum(oldret);assert 0<=delta<=2;peak_retire=max(peak_retire,delta);oldret=ret
  assert accepts==m['accepted'] and duals==m['dual_accept_cycles'];assert sum(oldret)==accepts
  # Independent sequential 4-way model for every recorded real wave.
  cache_check=None
  if name not in ['directed','empty','capacity4096','capacity4097']:
   raw=Path(row['command'][1]).read_bytes();h=struct.unpack_from('<6Q',raw);cache={};rr={};spills=0
   for i in range(h[4]):
    node,pair=struct.unpack_from('<IQ',raw,48+12*i);line=node>>2;bank=(line>>5)&1;key=(bank,(line>>6)&1023);ways=cache.setdefault(key,[None]*4)
    if line in ways:continue
    if None in ways:way=ways.index(None)
    else:way=rr[key];spills+=1
    ways[way]=line;rr[key]=(way+1)%4
   occupied=sum(sum(y is not None for y in ways) for ways in cache.values());assert spills==m['spill_fragments'];assert spills+occupied==m['total_fragments']
   if tag!='rtl_micro_a':assert occupied==m['enumerated_slots']
   cache_check={'spills_exact':True,'resident_count_exact':True,'table_input_sha256':hashlib.sha256(raw).hexdigest()}
  rows.append({'variant':tag,'case':name,'all_outputs_exact':True,'unit_total_simulated_cycles_including_init_drain':count,'candidate_accepts':accepts,'accept_span_cycles':0 if first is None else last-first+1,'peak_retire_per_cycle':peak_retire,'dual_accept_cycles':duals,'spill_fragments':m['spill_fragments'],'enumerated_slots':m['enumerated_slots'],'finite_fragment_queue_peak':m['queue_peak'],'scratch_requests32B_testbench':m['scratch_requests32B'],'physical_RAM_way_reads':4*accepts+(m['enumerated_slots'] if tag=='rtl_micro_a' else 4*m['enumerated_slots']),'physical_RAM_way_writes':8192+accepts+m['enumerated_slots'],'independent_functional_cache_check':cache_check,'trace_sha256':hashlib.sha256(trace.read_bytes()).hexdigest(),'board_measured':False,'fpga_seconds':None})
with out.open('x') as f:json.dump({'all_pass':True,'scope':'actual Verilator RTL cycles; clock unconstrained here. Independent cache event counts calibrated, NOT a complete candidate cycle model. Real-wave stress feeds all owner IDs to only two test subbanks; does not claim a 32-owner router.','rows':rows},f,indent=2);f.write('\n')
print('MICRO_VERIFIED',len(rows))

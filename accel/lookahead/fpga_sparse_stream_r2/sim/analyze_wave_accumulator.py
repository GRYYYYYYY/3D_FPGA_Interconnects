"""Bounded measured table traffic and necessary phase/port budgets, never FPGA seconds."""
from pathlib import Path
import json,hashlib,math
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_r2_20261112';out=r/'analysis/wave_accumulator_bounded_a.json'
rows=[]
for case,target in [('bnn_export',.151799969444),('lstm_s2',.159888578444)]:
 path=r/'accumulator/private_inf_bounded_a'/case/'wave_lines.jsonl';waves=[json.loads(x) for x in path.read_text().splitlines()]
 profile=json.loads((r/'accumulator/private_inf_bounded_a'/case/'line_profile.json').read_text())
 metrics={k:sum(sum(x[k]) for x in waves) for k in ['cache_hits','cache_misses','cache_spills','unique_spilled_lines','cache_occupancy']}
 for ports,gap in [(32,1),(32,2),(8,1)]:
  for layout in ['flush_all_fragments','hybrid_resident_direct_optimistic']:
   totals={k:[0]*ports for k in ['spill_scratch_read','spill_scratch_write','flush_scratch_read','flush_scratch_write','final_scratch_read','canonical_state_read','canonical_state_write','external_enumeration_read','external_enumeration_write']};phases=[0,0,0];enumeration_cycles=0
   for x in waves:
    spill=[0]*ports;flush=[0]*ports;final=[0]*ports
    for b in range(64):
     p=(b//2)%ports;sp=x['cache_spills'][b];oc=x['cache_occupancy'][b];us=x['unique_spilled_lines'][b];t4=x['touched4_by_owner_subbank'][b];t2=x['touched2_by_owner_subbank'][b];c2=x['changed2_by_owner_subbank'][b]
     a={'spill_scratch_read':2*sp,'spill_scratch_write':2*sp,'flush_scratch_read':2*oc if layout=='flush_all_fragments' else 0,'flush_scratch_write':2*oc if layout=='flush_all_fragments' else 0,'final_scratch_read':2*(t4 if layout=='flush_all_fragments' else us),'canonical_state_read':t2,'canonical_state_write':c2,'external_enumeration_read':math.ceil((t4 if layout=='flush_all_fragments' else us)/8),'external_enumeration_write':math.ceil((t4 if layout=='flush_all_fragments' else us)/8)}
     for k,v in a.items():totals[k][p]+=v
     spill[p]+=4*sp;flush[p]+=a['flush_scratch_read']+a['flush_scratch_write'];final[p]+=a['final_scratch_read']+t2+c2+a['external_enumeration_read']+a['external_enumeration_write']
    issue=lambda n:max(0,(n-1)*gap+1)
    en=3*max(x['cache_occupancy']);enumeration_cycles+=en
    phases[0]+=max(max(x['candidates_by_owner_subbank']),max(map(issue,spill)))
    if layout=='flush_all_fragments':phases[1]+=max(en,max(map(issue,flush)));phases[2]+=max(map(issue,final))
    else:phases[2]+=max(en,max(map(issue,final)))
   for f in [125,200]:
    cycles=sum(phases);rows.append({'case':case,'layout':layout,'physical_ports':ports,'gap_cycles':gap,'assumed_frequency_MHz':f,'profile_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'candidates':profile['candidates'],'finite_table_metrics':metrics,'traffic_32B_by_operation_by_physical_port':totals,'total_requests32B':sum(sum(x) for x in totals.values()),'phase_lower_bound_cycles_expand_flush_finalize':phases,'enumeration_cycles_at_three_per_occupied_slot':enumeration_cycles,'necessary_cycles_lower_bound':cycles,'conditional_seconds_lower_bound':cycles/(f*1e6),'prepared_POP_GPU_seconds':target,'fails_necessary_budget':cycles>target*f*1e6,'full_candidate_cycle_prediction':None,'fpga_seconds':None,'board_measured':False})
result={'scope':'C1 necessary bounds from exact full native40 finite-table instrumentation. Negative bound is a rejection; positive bound is NOT a qualified prediction or permission to claim speedup.','configuration':{'owners':32,'candidate_lanes':64,'subbanks_per_owner':2,'sets_per_subbank':1024,'ways':4,'data_bytes_per_entry':32,'tag_mask_bits_per_entry':36,'candidate_queue_depth_assumed':16,'fragment_fifo_depth_tested':8,'scratch_capacity_lines':1048576,'scratch_bytes_per_line':64,'occupied_slots_per_subbank':4096,'spilled_bitmap_bits_assumed':1048576,'external_enumeration_capacity_ids':1048576},'finite_storage_explanation':'Dirty fragment scratch RMW reads two32B rows and writes two32B rows. No packed80B assumption, no free sorting. Sparse external enumeration is allocated for every touched/spilled line; its row traffic is charged. Canonical state128 uses one32B row per two nodes and only real sector masks. Each physical port shares reads/writes.','limitations':['Micro RTL implements fragment accumulation and occupied enumeration; scratch merge/final-state hardware is represented only by finite testbench, not integrated.','Hybrid row is a hypothetical optimization: spilled-line bitmap, final probes, collision arbitration and FIFOs are NOT yet implemented.','The lower bound omits latency/credits/RAW/switch stalls, parent POP/control/CSR traffic, cost loading, mutable initialization, bucket append, output drain and complete-kernel timing; these cannot be assumed free in a prediction.','No calibration error from P8/P32/R1 applies.','Four-node accumulator ownership and canonical two-node physical rows are explicitly separate; no contiguous64B owner layout assumed.'],'rows':rows}
with out.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(out)
for x in rows:
 if x['physical_ports']==32 and x['gap_cycles']==1 and x['assumed_frequency_MHz']==200:print(x['case'],x['layout'],x['conditional_seconds_lower_bound'],x['fails_necessary_budget'])

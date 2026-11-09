"""Collect R5 evidence without assigning FPGA time to an unimplemented clock."""
import argparse,json,re,math,statistics,xml.etree.ElementTree as ET
from pathlib import Path
from prepare import sha256
p=argparse.ArgumentParser();p.add_argument('--experiment',type=Path,required=True);a=p.parse_args();r=a.experiment.resolve();manifest=json.loads((r/'workload_manifest.json').read_text());old=json.loads(Path('results/lookahead_accel_round4_20261108T182500Z/report_final.json').read_text());samples=[];workloads=[]
for w in manifest:
 f=r/'profiles_layers'/(w['case']+'.jsonl')
 if not f.exists():f=r/'profiles'/(w['case']+'.jsonl')
 rows=[json.loads(l) for l in f.read_text().splitlines()]
 for x in rows:
  x.update(case=w['case'],workload_sha256=w['sha256'],actual_edge_reads=x['original_edges'],static_eligible_candidates=x['actual_candidates'],csr_row_reads=2*x['expanded'],cost_reads=x['fp_adds']//2,label_reads=x['fp_adds']//2,label_commits=max(0,x['pushes']-1),last_target_completion_pop=x['last_target_pop'] if x['recorded']==x['targets'] else None)
  samples.append(x)
 for mode in ['full','early']:
  known=[s for s in old['software'] if s['case']==w['case'] and s['mode']==mode]
  if known:
   rs=[x for x in rows if bool(x['early'])==(mode=='early')]
   assert all((sum(x['pops'] for x in rs),sum(x['pushes'] for x in rs),sum(x['original_edges'] for x in rs))==(s['pops'],s['pushes'],s['edges']) for s in known)
 er=[x for x in rows if x['early']];pop=[x['pops'] for x in er];workloads.append(dict(**w,evidence_type='logical_CXX_measurement',working_set_byte_estimate_evidence='model-estimated from fixed record sizes; excludes allocator/tool overhead',early=dict(pops=sum(pop),pushes=sum(x['pushes'] for x in er),original_edges=sum(x['original_edges'] for x in er),static_eligible_candidates=sum(x['actual_candidates'] for x in er),heap_peak=max(x['heap_peak'] for x in er),cross_edges=sum(x['cross_edges'] for x in er) if all(x['cross_edges'] is not None for x in er) else None,pop_min=min(pop),pop_max=max(pop),pop_median=statistics.median(pop))))
(r/'per_sample_stats.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in samples))
hardware=[]
for ctx in [2,4]:
 h=r/f'hls_ctx{ctx}_clean';b=json.loads((h/'binding.json').read_text());log=(h/'csynth.log').read_text();match=re.search(r'Final II = (\d+), Depth = (\d+), loop \'DISPATCH\'',log);assert match
 root=ET.parse(h/'project/solution/syn/report/lookahead_interleave5_csynth.xml').getroot();res=root.find('AreaEstimates/Resources');resources={x.tag:int(x.text) for x in res};csim=(h/'csim.log').read_text();metrics=[[int(x) for x in line.split(' ',1)[1].strip(',').split(',')] for line in csim.splitlines() if line.startswith('METRICS ')];assert len(metrics)==9
 row=dict(contexts=ctx,evidence='model-estimated',schedule_evidence='HLS synthesis, not post-route',dispatch_ii=int(match[1]),pipeline_depth=int(match[2]),resources_hls_estimated=resources,verified_mhz=None,board_measured=False,calls=[])
 for i,w in enumerate(b['workloads']):
  case=Path(w['path']).parent.name;m=metrics[i*3+1];best=min(x['warm_e1_s']['median'] for x in old['software'] if x['case']==case and x['mode']=='early');ops=next(x['early'] for x in workloads if x['case']==case);budget=best*125e6
  call=dict(case=case,evidence='model-estimated',logical_dispatch_visits=m[31],phase_visits=m[:24],schedule_only_search_cycles=m[31]*int(match[1]),ideal_II1_search_cycles=m[31],cpu_early_measured_s=best,old125mhz_equal_time_cycle_budget=budget,old125mhz_strictly_faster_cycle_budget=math.ceil(budget)-1,minimum_frequency_MHz_if_II1=m[31]/best/1e6,required_heap_ops_per_s=(ops['pops']+ops['pushes'])/best,required_original_edges_per_s=ops['original_edges']/best,rtl_cycles=None,fpga_s=None,phase_wait_cycles='unmeasured; observer gives state visits and end-to-end feedback, not isolated queue residence',ooc_gate='stop: even ideal dispatcher II1 needs GHz-scale clocks far beyond the fixed 200MHz target to beat matched C1; no OOC, no frequency sweep')
  row['calls'].append(call)
 probe=r/f'rtl_ctx{ctx}'
 if (probe/'cosim.json').exists():
  result=json.loads((probe/'cosim.json').read_text());row['rtl_probe']=result
  if result['status']=='passed':
   xml=probe/'project/solution/sim/verilog/lookahead_interleave5.performance.result.transaction.xml';cycles=[int(v) for v in re.findall(r'transaction\s+\d+:\s+(\d+)',xml.read_text())];assert len(cycles)==4;row['rtl_cycles']=cycles;row['calls'][0].update(rtl_cycles=cycles[1],rtl_evidence='RTL-derived',fpga_s=None)
 monitor=r/f'monitor_ctx{ctx}'/'result.json'
 if monitor.exists():
  obs=json.loads(monitor.read_text());row['monitor']=obs
  if obs['status']=='passed':
   assert obs['cycles']==row['rtl_cycles'];tx=obs['transactions'][1];assert tx['phases']==metrics[1][:24];assert tx['issues']==metrics[1][31]
   row['calls'][0].update(dispatch_observed_gap_mean=tx['gap_sum']/(tx['issues']-1),dispatch_observed_gap_min=tx['gap_min'],dispatch_observed_gap_max=tx['gap_max'],pop_feedback_mean=tx['pop_feedback_sum']/tx['pops'],push_feedback_mean=tx['push_feedback_sum']/tx['pushes'],pipeline_overlap_cycles=tx['pipeline_overlap_cycles'])
   row['calls'][0].update(retired_dead_slot_visits=tx['phases'][23],useful_visit_fraction=1-tx['phases'][23]/tx['issues'],rtl_minus_schedule_product_cycles=row['rtl_cycles'][1]-tx['issues']*int(match[1]),residual_attribution='unmeasured; no arbitrary allocation to output, control or memory stalls',heap_operations_per_batch_cycle=(tx['pops']+tx['pushes']+tx['phases'][3])/row['rtl_cycles'][1],original_edges_per_batch_cycle=tx['phases'][16]/row['rtl_cycles'][1])
 hardware.append(row)
summary=dict(board_measured=False,primary='Single real complete native batch warm E1',workloads=workloads,software=json.loads((r/'software_latency_throughput.json').read_text()),hardware=hardware,model=json.loads((r/'model/dependency_service_model.json').read_text()),unmeasured=['New candidate implemented frequency and FPGA seconds','B0/B1 native same-scope E1 (C1 gate not reached)','Native complete lookahead E2','RRG build performance','Host-to-device complete service','True sustained multiple distinct builds throughput','New held-out 8x8 hardware (N exceeds capacity)'],all_baselines_superiority_verified=False)
(r/'report_final.json').write_text(json.dumps(summary,indent=2)+'\n');print([(h['contexts'],h['dispatch_ii'],h['calls'][0]['minimum_frequency_MHz_if_II1']) for h in hardware])

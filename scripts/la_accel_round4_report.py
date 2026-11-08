"""Collect matched R4 measurements; never convert unverified target clocks to time."""
import argparse,json,math,re,statistics
from pathlib import Path
from prepare import sha256
from la_accel_round3_report import hardware,distribution

def collect(root,partial=False):
 data=dict(evidence_policy='Software measured on worker; FPGA functional RTL cycles at timing-clean implemented OOC clocks; no board or calibrated HBM measurement.',board_measured=False,software=[],hardware=[],comparisons=[],decomposition=[],unmeasured=['B0/B1 native same-scope E1','native complete lookahead E2','host-to-FPGA service latency','capacity-exceeding hardware graphs'])
 for worker in sorted(root.glob('gpu_worker_*')):
  finished=worker/'finished.json'
  if not finished.exists():
   assert partial,'Incomplete worker '+str(worker)
   continue
  assert json.loads(finished.read_text())['status']=='passed'
  records=json.loads((worker/'measurements.json').read_text());meta=json.loads((worker/'worker.json').read_text())
  for key in sorted({(r['case'],r['mode'],r['kind'],r['parallel']) for r in records}):
   rows=[r for r in records if (r['case'],r['mode'],r['kind'],r['parallel'])==key]
   assert len(rows)==meta['process_repeats']
   assert all(m['all_golden_bits_match'] for r in rows for m in r['measurements'])
   counts={(m['pops'],m['edges'],m['pushes']) for r in rows for m in r['measurements']};assert len(counts)==1
   pop,edge,push=next(iter(counts))
   row=dict(case=key[0],mode=key[1],backend=key[2],parallel=key[3],cohort=worker.name,workload_sha256=rows[0]['workload_sha256'],pops=pop,edges=edge,pushes=push,
    cold_e1_s=distribution([r['measurements'][0]['resident_s'] for r in rows]),
    warm_e1_s=distribution([statistics.median(m['resident_s'] for m in r['measurements'][1:]) for r in rows]),
    prepare_s=distribution([r['measurements'][0]['prepare_s'] for r in rows]),
    target_prepare_s=distribution([r['measurements'][0]['target_prepare_s'] for r in rows]),
    estimator='Median of fresh-process medians; each warm process median excludes its first call.')
   data['software'].append(row)
 for name in ['full_1','full_4','early_1','early_4']:
  folder=root/('hls_'+name);h=hardware(folder);h['name']=name;h['cycles']=[];h['calls']=[]
  timing=root/('timing125_'+name)/'result.json'
  if timing.exists():
   t=json.loads(timing.read_text());assert t['status']=='passed_internal_OOC' and t['binding_sha256']==sha256(folder/'binding.json')
   h['original_target_verified_mhz']=h['verified_mhz'];h['timing_recheck']=t;h['verified_mhz']=t['verified_mhz']
  if h['phases']['cosim']=='passed':
   report=folder/'project/solution/sim/verilog/lookahead_onchip4.performance.result.transaction.xml'
   h['cycles']=[int(x) for x in re.findall(r'transaction\s+\d+:\s+(\d+)',report.read_text())];assert len(h['cycles'])==12
  monitor=root/('monitor_'+name)/'result.json'
  if monitor.with_name('verification_v2.json').exists():monitor=monitor.with_name('verification_v2.json')
  if monitor.exists():
   h['monitor']=json.loads(monitor.read_text());assert h['monitor']['status']=='passed'
   assert h['monitor']['cycles']==h['cycles'],'Instrumented/uninstrumented cycle drift'
   for i,w in enumerate(h['binding']['workloads']):
    case=Path(w['path']).parent.name;mode='early' if h['binding']['early'] else 'full'
    matching=[s for s in data['software'] if s['workload_sha256']==w['sha256'] and s['mode']==mode]
    assert matching
    counts={s['pops'] for s in matching};assert len(counts)==1
    for t in h['monitor']['transactions'][4*i:4*i+3]:assert sum(e['pops'] for e in t['engines'])==next(iter(counts))
    tx=h['monitor']['transactions'][4*i+1];warm=h['cycles'][4*i+1];assert warm==h['cycles'][4*i+2]
    call=dict(case=case,mode=mode,workload_sha256=w['sha256'],load_static_to_onchip_cycles=h['cycles'][4*i+3],warm_e1_cycles=warm,first_call_from_device_memory_cycles=h['cycles'][4*i],warm_graph_axi_zero=h['monitor']['warm_graph_axi_zero'],warm_output_bytes=sum(p['write_bytes'] for p in tx['ports']),
     warm_e1_s=None,first_call_from_device_memory_s=None,load_static_to_onchip_s=None,engine_statistics=tx['engines'],search_overlap_cycles=tx['search_overlap_cycles'])
    assert all(p['read_requests']==p['read_completions'] and p['write_requests']==p['write_responses'] for p in tx['ports'])
    if h['verified_mhz']:
     clock=h['verified_mhz']*1e6
     for s,c in [('warm_e1_s','warm_e1_cycles'),('load_static_to_onchip_s','load_static_to_onchip_cycles'),('first_call_from_device_memory_s','first_call_from_device_memory_cycles')]:call[s]=call[c]/clock
     best=min(matching,key=lambda s:s['warm_e1_s']['median']);t=best['warm_e1_s']['median']
     comparison=dict(case=case,mode=mode,hardware=name,verified_mhz=h['verified_mhz'],warm_fpga_s=call['warm_e1_s'],best_software_backend=best['backend'],best_software_parallel=best['parallel'],best_software_warm_s=t,strictly_faster_cycle_budget=math.ceil(t*clock)-1,same_algorithm_speedup=t/call['warm_e1_s'],fpga_faster=call['warm_e1_s']<t)
     data['comparisons'].append(comparison)
    h['calls'].append(call)
  if not partial:assert h['phases']['impl']=='passed' and monitor.exists(),'Missing required implementation/RTL monitor'
  data['hardware'].append(h)
 # Algorithm gains keep the same worker and parallelism. Selecting the best CPU
 # separately for each mode is reported separately, not mislabeled a fixed control.
 for full in data['software']:
  if full['mode']!='full':continue
  early=next(s for s in data['software'] if s['case']==full['case'] and s['mode']=='early' and s['backend']==full['backend'] and s['parallel']==full['parallel'] and s['cohort']==full['cohort'])
  data['decomposition'].append(dict(kind='software_algorithm_fixed_configuration',case=full['case'],backend=full['backend'],parallel=full['parallel'],warm_speedup=full['warm_e1_s']['median']/early['warm_e1_s']['median']))
 byname={h['name']:h for h in data['hardware']}
 for engines in [1,4]:
  f=byname['full_'+str(engines)];e=byname['early_'+str(engines)]
  for fc,ec in zip(f['calls'],e['calls']):
   if fc['warm_e1_s'] and ec['warm_e1_s']:
    baseline=min(s['warm_e1_s']['median'] for s in data['software'] if s['case']==ec['case'] and s['mode']=='full')
    data['decomposition'].append(dict(kind='hardware_algorithm_fixed_engines',case=ec['case'],engines=engines,full_to_early_time_gain=fc['warm_e1_s']/ec['warm_e1_s'],full_to_early_cycle_gain=fc['warm_e1_cycles']/ec['warm_e1_cycles'],overall_vs_current_software_full_e1=baseline/ec['warm_e1_s'],not_native_E2=True))
 # The older external-full implementation is a separately frozen architecture control.
 old=root.parent/'lookahead_accel_round3_20261108T141500Z'
 for case,old_name in [('native_d3_w8','hls_quad'),('native_d4_w8','hls_quad_d4')]:
  if not (old/old_name).exists():continue
  before=hardware(old/old_name)
  for call in byname['full_4']['calls']:
   if call['case']!=case:continue
   same_input=before['binding']['workload']==call['workload_sha256'];assert same_input
   row=dict(kind='architecture_external_to_onchip_full',case=case,engines=4,old_cycles=before['functional_cycles'],new_cycles=call['warm_e1_cycles'],cycle_gain=before['functional_cycles']/call['warm_e1_cycles'],model='functional AESL AXI; distinct graph residence; no board claim',time_gain=None)
   if before['verified_mhz'] and call['warm_e1_s']:row['time_gain']=(before['functional_cycles']/(before['verified_mhz']*1e6))/call['warm_e1_s']
   data['decomposition'].append(row)
   combined=next((c for c in byname['early_4']['calls'] if c['case']==case),None)
   if combined and before['verified_mhz'] and combined['warm_e1_s']:
    data['decomposition'].append(dict(kind='combined_architecture_and_algorithm_vs_external_full',case=case,engines=4,warm_speedup=(before['functional_cycles']/(before['verified_mhz']*1e6))/combined['warm_e1_s'],not_native_E2=True))
 data['expansion_gate']=[]
 for h in data['hardware']:
  if h['name']!='early_4' or not h['verified_mhz']:continue
  for call in h['calls']:
   matching=[s for s in data['software'] if s['workload_sha256']==call['workload_sha256'] and s['mode']=='early'];best=min(s['warm_e1_s']['median'] for s in matching)
   w=next(w for w in h['binding']['workloads'] if w['sha256']==call['workload_sha256']);jobs=w['dimensions']['j'];total=sum(e['search_cycles'] for e in call['engine_statistics'])
   # This scheduling-only bound keeps the measured per-task datapath work fixed.
   # It excludes all dispatch/output overhead and is deliberately optimistic.
   data['expansion_gate'].append(dict(case=call['case'],evidence_type='conditional_scheduling_bound_from_verified_RTL',assumption='Fixed per-task search datapath work; perfect balancing, no dispatch or output overhead, up to one engine per actual sample. Not a simulated ready-task scheduler.',observed_search_work_cycles=total,actual_jobs=jobs,perfect_four_engine_lower_bound_cycles=math.ceil(total/4),perfect_J_engine_lower_bound_cycles=math.ceil(total/jobs),software_cycle_budget=math.ceil(best*h['verified_mhz']*1e6)-1,expand_engines=math.ceil(total/jobs)<best*h['verified_mhz']*1e6))
 data['fpga_superiority_over_all_baselines_verified']=False # B0/B1/E2 are not measured here.
 return data

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--experiment',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--allow-partial',action='store_true');a=p.parse_args()
 a.output.write_text(json.dumps(collect(a.experiment.resolve(),a.allow_partial),indent=2)+'\n')
if __name__=='__main__':main()

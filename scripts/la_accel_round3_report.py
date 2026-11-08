"""Collect matched measured E1 and RTL evidence; use only timing-clean OOC periods."""
import argparse,json,math,re,statistics,xml.etree.ElementTree as ET
from pathlib import Path
from prepare import sha256

def distribution(values):
 return dict(values=values,median=statistics.median(values),minimum=min(values),maximum=max(values))

def hardware(folder):
 binding=json.loads((folder/'binding.json').read_text());top=binding['top']
 result=dict(name=folder.name,binding=binding,phases={},functional_cycles=None,verified_mhz=None)
 rtl=folder/f'project/solution/syn/verilog/{top}.v'
 if rtl.exists():
  result['rtl_top_sha256']=sha256(rtl);result['adapter_configuration']={}
  for port,body in re.findall(re.escape(top)+r'_(\w+)_m_axi\s*#\((.*?)\)\s*\w+_m_axi_U',rtl.read_text(),re.S):
   values={k:int(v) for k,v in re.findall(r'\.(\w+)\(\s*(\d+)\s*\)',body)}
   result['adapter_configuration'][port]={k:values[k] for k in ['NUM_READ_OUTSTANDING','NUM_WRITE_OUTSTANDING','MAX_READ_BURST_LENGTH','MAX_WRITE_BURST_LENGTH','USER_DW']}
 for phase in ['csim','csynth','cosim','impl']:
  p=folder/(phase+'.json');result['phases'][phase]=json.loads(p.read_text())['status'] if p.exists() else 'pending_or_not_run'
 if result['phases']['cosim']=='passed':
  p=folder/f'project/solution/sim/verilog/{top}.performance.result.transaction.xml'
  result['functional_cycles']=int(re.search(r'transaction\s+0:\s+(\d+)',p.read_text())[1]);result['cycle_report_sha256']=sha256(p)
 p=folder/'project/solution/impl/report/verilog/export_impl.xml'
 if result['phases']['impl']=='passed' and p.exists():
  x=ET.parse(p).getroot();result['resources']={e.tag:int(e.text) for e in x.findall('./AreaReport/Resources/*')};result['timing']={e.tag:e.text for e in x.findall('./TimingReport/*')}
  p=next((folder/'project/solution/impl/verilog/report').glob('*_timing_routed.rpt'));text=p.read_text();lines=text.splitlines()
  result['constraints']={k:int(v) for k,v in re.findall(r'checking ([a-z_]+) \((\d+)\)',text)}
  for i,line in enumerate(lines):
   if 'WNS(ns)' in line and 'WHS(ns)' in line:
    for row in lines[i+1:i+5]:
     cells=row.split()
     if len(cells)==12:
      try:result['slack_ns']={'setup':float(cells[0]),'hold':float(cells[4]),'pulse':float(cells[8])};break
      except ValueError:pass
    break
  good=result.get('slack_ns') and all(v>=0 for v in result['slack_ns'].values()) and result['constraints'].get('no_clock')==0 and result['constraints'].get('unconstrained_internal_endpoints')==0
  if good and result['timing'].get('TIMING_MET')=='TRUE':result['verified_mhz']=1000/float(result['timing']['CP_TARGET'])
 return result

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--experiment',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();root=a.experiment.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
 data=dict(goal='FPGA faster than each baseline; software ordering unrestricted',fpga_superiority_verified=False,board_measured=False,software=[],hardware=[],bounded=[],workloads={},comparisons=[])
 for d in root.glob('native_d*'):
  if (d/'manifest.json').exists():data['workloads'][d.name]=json.loads((d/'manifest.json').read_text())
 raw=[];data['workers']={}
 for worker in sorted(root.glob('gpu_worker*')):
  if not (worker/'finished.json').exists():continue
  assert json.loads((worker/'finished.json').read_text())['status']=='passed'
  data['workers'][worker.name]=json.loads((worker/'worker.json').read_text())
  for record in json.loads((worker/'measurements.json').read_text()):record['cohort']=worker.name;raw.append(record)
 assert raw,'No completed measured software cohort'
 for case,kind,parallel,cohort in sorted({(v['case'],v['kind'],v['parallel'],v['cohort']) for v in raw}):
  rows=[v for v in raw if (v['case'],v['kind'],v['parallel'],v['cohort'])==(case,kind,parallel,cohort)]
  assert len(rows)==5 and all(len(v['measurements'])==6 and all(m['all_golden_bits_match'] for m in v['measurements']) for v in rows)
  record=dict(case=case,kind=kind,parallel=parallel,cohort=cohort,workload_sha256=rows[0]['workload_sha256'],
    cold_e1_s=distribution([v['measurements'][0]['resident_s'] for v in rows]),
    warm_e1_s=distribution([statistics.median(m['resident_s'] for m in v['measurements'][1:]) for v in rows]),
    cold_service_s=distribution([v['measurements'][0]['service_to_result_s'] for v in rows]),
    warm_service_s=distribution([statistics.median(m['service_to_result_s'] for m in v['measurements'][1:]) for v in rows]))
  data['software'].append(record)
 for d in sorted(root.glob('hls_*')):
  if d.is_dir() and (d/'binding.json').exists():data['hardware'].append(hardware(d))
 byname={x['name']:x for x in data['hardware']}
 for d in sorted(root.glob('bounded_*')):
  if not d.is_dir() or not (d/'result.json').exists():continue
  result=json.loads((d/'result.json').read_text());config=json.loads((d/'config.json').read_text());name=Path(config['source_hls']).name;h=byname[name]
  row=dict(name=d.name,source_hls=name,result=result,config=config,rtl_time_s=None)
  if result.get('memory'):
   m=result['memory'];row['post_done_drain_cycles']=max(0,m['cycle']-m['done_observed'])
   row['e1_cycles_including_drain']=result['rtl_cycles'][0]+row['post_done_drain_cycles']
   row['total_native_beats']=sum(p['read_beats']+p['write_beats'] for p in m['ports'])
   row['bank_slot_utilization']=row['total_native_beats']*config['cycles_per_bank_beat']/(row['e1_cycles_including_drain']*config['shared_banks'])
   bank_beats=[0]*config['shared_banks']
   for port,p in zip(config['ports'],m['ports']):bank_beats[config['bank_mapping'][port]]+=p['read_beats']+p['write_beats']
   row['observed_traffic_service_lower_bound_cycles']=max(max(0,(b-1)*config['cycles_per_bank_beat']+1) for b in bank_beats)
   if result.get('engine_overlap'):
    engines=result['engine_overlap']['engines'];continuous=all(e['active_cycles']==e['last_active']-e['first_active']+1 for e in engines)
    row['activity_summary']={'continuous_intervals_verified':continuous,'average_active_engines':sum(e['active_cycles'] for e in engines)/row['e1_cycles_including_drain'],
     'active_cycle_imbalance':max(e['active_cycles'] for e in engines)/min(e['active_cycles'] for e in engines),
     'finish_spread_cycles':max(e['last_active'] for e in engines)-min(e['last_active'] for e in engines)}
    if continuous:
     row['activity_summary']['all_engines_overlap_cycles']=max(0,min(e['last_active'] for e in engines)-max(e['first_active'] for e in engines)+1)
     row['activity_summary']['pairwise_overlap_cycles']=[[max(0,min(x['last_active'],y['last_active'])-max(x['first_active'],y['first_active'])+1) for y in engines] for x in engines]
  if result['status']=='passed' and h['verified_mhz']:
   row['rtl_time_s']=row['e1_cycles_including_drain']/(h['verified_mhz']*1e6)
   row['bank_capacity_native_beats_per_s']=h['verified_mhz']*1e6*config['shared_banks']/config['cycles_per_bank_beat']
   row['observed_traffic_service_lower_bound_s']=row['observed_traffic_service_lower_bound_cycles']/(h['verified_mhz']*1e6)
   candidates=[v for v in data['software'] if v['workload_sha256']==h['binding']['workload']]
   if candidates:
    best=min(candidates,key=lambda v:v['warm_e1_s']['median']);limit=best['warm_e1_s']['median']*h['verified_mhz']*1e6
    row['strongest_measured_resident_software']=dict(kind=best['kind'],parallel=best['parallel'],warm_e1_s=best['warm_e1_s']['median'])
    row['strictly_faster_cycle_budget']=math.ceil(limit)-1;row['time_ratio_to_best_warm_software']=row['rtl_time_s']/best['warm_e1_s']['median']
  data['bounded'].append(row)
 runs={v['name']:v for v in data['bounded']}
 for baseline,candidate,purpose in [('bounded_single_family','bounded_dual','replicated resident engines'),('bounded_single_family','bounded_packed_wt','packed-label layout'),('bounded_packed_wt','bounded_packed_wb','label write-back policy'),('bounded_dual','bounded_quad','four-engine scaling'),('bounded_dual_d4','bounded_quad_d4','four engines, next complete 3D rung')]:
  if baseline not in runs or candidate not in runs:continue
  b,c=runs[baseline],runs[candidate];hb,hc=byname[b['source_hls']],byname[c['source_hls']]
  keys=['latency_cycles','shared_banks','cycles_per_bank_beat','outstanding_per_port_per_direction','total_read_credits','total_write_credits','interposer_sha256']
  matched=hb['binding']['workload']==hc['binding']['workload'] and all(b['config'][k]==c['config'][k] for k in keys)
  for flag in ['LA_HEAP_TOP','LA_LABEL_LINES','LA_COST_LINES']:
   matched=matched and re.search(r'-D'+flag+r'=(\d+)',hb['binding']['flags'])[1]==re.search(r'-D'+flag+r'=(\d+)',hc['binding']['flags'])[1]
  ready=matched and b['rtl_time_s'] is not None and c['rtl_time_s'] is not None
  data['comparisons'].append(dict(baseline=baseline,candidate=candidate,purpose=purpose,matched_controls=matched,timing_ready=ready,
   speedup=b['rtl_time_s']/c['rtl_time_s'] if ready else None,actual_rtl_time_improved=c['rtl_time_s']<b['rtl_time_s'] if ready else None))
 lines=['# Lookahead round 3 — matched resident experiments','',
  'Goal remains unverified. CPU wall times, CUDA event times, and RTL cycle-derived times are identified separately. C simulation host elapsed time is never a hardware timing datum.','',
  '## Measured software E1','',
  '| Workload | Backend | Workers / CTAs | Cold first E1 μs | Warm E1 μs | Cold service μs |',
  '|---|---|---:|---:|---:|---:|']
 for v in data['software']:
  lines.append(f'| {v["case"]} | {v["kind"]} | {v["parallel"]} | {v["cold_e1_s"]["median"]*1e6:.3f} | {v["warm_e1_s"]["median"]*1e6:.3f} | {v["cold_service_s"]["median"]*1e6:.3f} |')
 lines+=['','Five fresh processes per configuration. Cold is the first measured kernel invocation, with no warmup. Warm is the median of five subsequent complete batches per process, then the median over five processes. Allocations/uploads persist within a process; labels, queue counts and outputs reset inside every E1. Cold service adds preparation and compact readback, excludes workload file I/O and golden comparison, and is not full native E2. CUDA first E1 includes first-launch/lazy-module overhead between the event timestamps. CPU is the independent compact-CSR std::priority_queue/OpenMP baseline, not a substituted native-builder E2 measurement.','',
  '## Complete native workloads: functional RTL and OOC implementation','',
  '| Core | Workload SHA prefix | Functional cycles | Routed setup / hold ns | Verified MHz | LUT / FF / DSP / BRAM18 |',
  '|---|---|---:|---|---:|---|']
 for h in data['hardware']:
  slack=h.get('slack_ns',{});timing=f'{slack["setup"]:+.3f} / {slack["hold"]:+.3f}' if slack else 'not completed'
  res=h.get('resources',{});area=' / '.join(str(res.get(k,'—')) for k in ['LUT','FF','DSP','BRAM'])
  lines.append(f'| {h["name"]} | {h["binding"]["workload"][:12]} | {h["functional_cycles"]} | {timing} | {h["verified_mhz"] or "—"} | {area} |')
 lines+=['','No time is derived at the target frequency when routed setup/hold fails. Verified MHz is the timing-clean implementation target, not an inferred fmax; core OOC does not establish shell or board timing.','',
  '## Bounded synthetic memory','',
  '| Run | Status | Cycles | RTL time at verified OOC period, ms | Cycles needed to beat strongest measured warm E1 |',
  '|---|---|---:|---:|---:|']
 for v in data['bounded']:
  t=f'{v["rtl_time_s"]*1000:.6f}' if v['rtl_time_s'] is not None else 'unverified'
  lines.append(f'| {v["name"]} | {v["result"]["status"]} | {v.get("e1_cycles_including_drain",v["result"]["rtl_cycles"])} | {t} | {v.get("strictly_faster_cycle_budget","—")} |')
 lines+=['','## Controlled comparisons','',
  '| Change | Baseline → candidate | Matching input/cache/memory controls | Time speedup at verified frequencies |',
  '|---|---|---|---:|']
 for v in data['comparisons']:
  speed=f'{v["speedup"]:.4f}x' if v['timing_ready'] else 'pending verified timing'
  lines.append(f'| {v["purpose"]} | {v["baseline"]} → {v["candidate"]} | {v["matched_controls"]} | {speed} |')
 lines+=['','## Memory traffic and engine overlap','',
  '| Run | Port | Data bits | Read / write requests | Read / write beats | Peak reads / writes |',
  '|---|---|---:|---|---|---|']
 for v in data['bounded']:
  if not v['result'].get('memory'):continue
  c=v['config'];m=v['result']['memory']
  for port,p in zip(c['ports'],m['ports']):
   lines.append(f'| {v["name"]} | {port} | {c.get("port_data_bits",{}).get(port,"see RTL")} | {p["reads"]} / {p["writes"]} | {p["read_beats"]} / {p["write_beats"]} | {p["max_reads"]} / {p["max_writes"]} |')
 for v in data['bounded']:
  if not v['result'].get('memory'):continue
  m=v['result']['memory'];o=v['result'].get('engine_overlap')
  lines+=['',f'{v["name"]}: total peak outstanding R/W = {m["max_total_reads"]}/{m["max_total_writes"]}; shared bank slot utilization = {v["bank_slot_utilization"]:.2%}; post-completion drain = {v["post_done_drain_cycles"]} cycles.']
  if o:
   active=[e['active_cycles'] for e in o['engines']];lines.append(f'At least two engines overlap for {o["overlap_cycles"]} cycles; per-engine active cycles {active}, max/min = {max(active)/min(active):.6f}. Exact first/last activity is retained in JSON.')
   activity=v['activity_summary']
   if activity['continuous_intervals_verified']:lines.append(f'Each active interval is verified continuous from its observed count and endpoints: all engines overlap for {activity["all_engines_overlap_cycles"]} cycles; average active engines = {activity["average_active_engines"]:.4f}, finish spread = {activity["finish_spread_cycles"]} cycles. Pairwise intersections are derived from these RTL intervals in JSON.')
  lines.append(f'With these observed beat counts unchanged, bank service alone needs at least {v["observed_traffic_service_lower_bound_cycles"]} cycles, even with perfect compute overlap. This is a small-input model bound, not a hardware measurement or a large-graph forecast.')
 for h in data['hardware']:
  ports=h.get('adapter_configuration',{})
  if ports:
   reads=sum(p['NUM_READ_OUTSTANDING'] for p in ports.values());writes=sum(p['NUM_WRITE_OUTSTANDING'] for p in ports.values())
   lines+=['',f'{h["name"]}: {len(ports)} generated AXI masters provision {reads}/{writes} total internal read/write outstanding slots. The external bounded model still admits only the fixed global 8/8 requests, with 2/2 per port. Full per-port RTL parameters are retained in JSON.']
 lines+=['','Primary controls: 64-cycle minimum request latency; one shared bank; one R/W native beat every four clocks; two outstanding requests per direction per port; fixed global pools of eight read and eight write credits. A held address reserves a global credit. Each return port has one finite skid slot. Port widths, actual peak outstanding, stalls, beat counts and engine overlap are retained in JSON. This is a synthetic sensitivity model, not measured HBM.','',
  'At 200 MHz the shared bank supplies at most 50 million native beats/s (at most 3.2 GB/s for exclusively 512-bit beats); effective transferred bytes depend on each recorded port width and byte strobes. Replication does not increase this beat budget or the global credit pools. E1 adds any post-completion drain recorded by the model.','',
  'Engine overlap measures deasserted ap_idle intervals and includes AXI waits. It proves concurrent in-flight searches, not simultaneous useful arithmetic on every counted cycle.','',
  'The cycle budget uses the strongest warm CPU/CUDA configuration actually measured on this exact workload. It is a necessary target for this cohort, not evidence of superiority over every original/native software implementation. FPGA large-graph prediction and complete lookahead E2 remain outside this phase.']
 (out/'report.json').write_text(json.dumps(data,indent=2)+'\n');(out/'report.md').write_text('\n'.join(lines)+'\n');print(out/'report.md')
if __name__=='__main__':main()

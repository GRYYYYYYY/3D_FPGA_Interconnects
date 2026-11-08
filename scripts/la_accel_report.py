"""Collect measured/functional/OOC evidence without mixing timing scopes or fabricating missing values."""
import argparse,json,re,statistics,xml.etree.ElementTree as ET,datetime,struct
from pathlib import Path
from prepare import sha256

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--experiment',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();root=a.experiment.resolve();o=a.output.resolve();o.mkdir(parents=True,exist_ok=False)
 result=dict(schema_version='la_accel_v1',generated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),experiment=str(root),target_ordering='unverified',hardware_board_measured=False,fpga_large_graph_model=None,workloads={},hls=[],measurements=[])
 for d in ['tseng_export','bnn_export','tiny_native','tseng_eligible','tiny_eligible']:
  folder=root/d
  if not folder.exists():continue
  result['workloads'][d]={p.stem:json.loads(p.read_text()) for p in [folder/'manifest.json',folder/'workload_layout.json'] if p.exists()}
  with (folder/'workload.bin').open('rb') as f:result['workloads'][d]['binary_dimensions']=dict(zip(['magic','nodes','edges','jobs','costs','cells','groups'],struct.unpack('<7Q',f.read(56))))
 for folder in sorted(root.glob('hls_*')):
  if not folder.is_dir():continue
  rec=dict(variant=folder.name,phases={},core_cycles=None,implemented_frequency_hz=None,resources=None,memory_model='automatic HLS functional AXI; no bounded-memory calibration',evidence_type='fpga_rtl_functional',resident_elapsed_s=None,implementation_report=None)
  for phase in ['csim','csynth','cosim','impl']:
   path=folder/(phase+'.json');rec['phases'][phase]=json.loads(path.read_text())['status'] if path.exists() else 'not_run'
  path=folder/'binding.json'
  if path.exists():rec['source_binding']=json.loads(path.read_text())
  rpt=folder/'project/solution/sim/report/verilog/result.transaction.rpt'
  if rpt.exists() and rec['phases']['cosim']=='passed':
   rec['transactions']=[dict(transaction=int(i),cycles=int(v)) for i,v in re.findall(r'transaction\s+(\d+):\s+(\d+)',rpt.read_text())];rec['core_cycles']=rec['transactions'][0]['cycles'] if rec['transactions'] else None;rec['cycle_report']=str(rpt)
  for synth_xml in (folder/'project/solution/syn/report').glob('*_csynth.xml'):
   if synth_xml.stem not in ['lookahead_top_csynth','lookahead_dual_csynth']:continue
   x=ET.parse(synth_xml).getroot();rec['synthesis_estimates']={e.tag:e.text for e in x.findall('./AreaEstimates/Resources/*')};rec['synthesis_estimated_period_ns']=x.findtext('./PerformanceEstimates/SummaryOfTimingAnalysis/EstimatedClockPeriod');rec['synthesis_report']=str(synth_xml)
  xml=folder/'project/solution/impl/report/verilog/export_impl.xml'
  if xml.exists() and rec['phases']['impl']=='passed':
   x=ET.parse(xml).getroot();rec['implementation_report']=str(xml);rec['resources']={e.tag:int(e.text) for e in x.findall('./AreaReport/Resources/*')};rec['timing']={e.tag:e.text for e in x.findall('./TimingReport/*')}
   if x.findtext('./TimingReport/TIMING_MET')=='TRUE':rec['implemented_frequency_hz']=1e9/float(x.findtext('./TimingReport/CP_TARGET'))
   timing_report=next((folder/'project/solution/impl/verilog/report').glob('*_timing_routed.rpt'),None)
   if timing_report:
    timing_text=timing_report.read_text();rec['timing_constraint_checks']={k:int(v) for k,v in re.findall(r'checking ([a-z_]+) \((\d+)\)',timing_text)}
    timing_lines=timing_text.splitlines()
    for i,line in enumerate(timing_lines):
     if 'WNS(ns)' in line and 'WHS(ns)' in line:
      for candidate in timing_lines[i+1:i+5]:
       parts=candidate.split()
       if len(parts)==12:
        try:rec['routed_slacks_ns']=dict(setup=float(parts[0]),hold=float(parts[4]),pulse_width=float(parts[8]));break
        except ValueError:pass
      break
    rec['core_internal_timing_passed']=bool(rec.get('routed_slacks_ns')) and all(v>=0 for v in rec['routed_slacks_ns'].values()) and rec['timing_constraint_checks'].get('no_clock')==0 and rec['timing_constraint_checks'].get('unconstrained_internal_endpoints')==0
    if not rec['core_internal_timing_passed']:rec['implemented_frequency_hz']=None
   rec['clock_limitations']='core OOC only; inspect HD.CLK_SRC/IO constraints; no shell guarantee'
   if rec['core_cycles'] is not None and rec['implemented_frequency_hz']:rec['functional_time_at_ooc_clock_s']=rec['core_cycles']/rec['implemented_frequency_hz']
  result['hls'].append(rec)
 summary=next((root/n for n in ['software_summary_confirm.json','software_summary_pinned.json','software_summary.json'] if (root/n).exists()),root/'software_summary.json')
 result['software_summary']=json.loads(summary.read_text()) if summary.exists() else None
 result['preferred_software_cohort']=str(summary)
 native_summary=root/('software_summary_confirm.json' if (root/'software_summary_confirm.json').exists() else 'software_summary.json')
 result['native_software_summary']=json.loads(native_summary.read_text()) if native_summary.exists() else None
 result['native_cohort_path']=str(native_summary)
 result['latency_probes']={d.name:json.loads((d/('result_corrected.json' if (d/'result_corrected.json').exists() else 'result.json')).read_text()) for d in root.glob('memory64_*') if (d/'result.json').exists()}
 for path in root.rglob('runs.json'):
  if 'project' in path.parts:continue
  for r in json.loads(path.read_text()):
   r['record_path']=str(path);result['measurements'].append(r)
 lines=['# Lookahead acceleration experiment evidence','',f'Generated: {result["generated_utc"]}', '', 'Target FPGA better than each baseline remains **unverified**; GPU may be slower than CPU. CPU wall times, CUDA event times and RTL functional cycles are kept separate. No board measurement or calibrated large-graph FPGA prediction is reported.','', '## Native workload correctness','', '| Workload | Nodes | Edges | Samples | Final native wire map |','|---|---:|---:|---:|---|']
 for name,entry in result['workloads'].items():
  m=entry.get('manifest',{});layout=entry.get('workload_layout',{});d=entry['binary_dimensions'];lines.append(f'| {name} | {d.get("nodes",m.get("nodes","—"))} | {d.get("edges",m.get("eligible_edges","—"))} | {d.get("jobs","—")} | {m.get("wire_map_matches_reference","not a frozen-map comparison")} |')
 lines+=['','tseng CPU and HLS C replay match native sample/group bits. tseng HLS output imported through the native adapter reproduces the final wire map. BNN CPU and HLS C replay match all 40 native sample maps. These are correctness checks, not FPGA time measurements. One-iteration component routing is not a route-success claim.','','## RTL and OOC','', '| Variant | csim / synth / cosim / impl | Functional cycles (transaction 0) | Verified target clock MHz | LUT / FF / DSP / BRAM18 equivalents / URAM |','|---|---|---:|---:|---|']
 for r in result['hls']:
  res=r['resources'];est=r.get('synthesis_estimates');area=' / '.join(str(res.get(k,'—')) for k in ['LUT','FF','DSP','BRAM','URAM']) if res else ('HLS est: '+' / '.join(str(est.get(k,'—')) for k in ['LUT','FF','DSP','BRAM_18K','URAM']) if est else '—');freq=r['implemented_frequency_hz']/1e6 if r['implemented_frequency_hz'] else '—';lines.append(f'| {r["variant"]} | {" / ".join(r["phases"].values())} | {r["core_cycles"] if r["core_cycles"] is not None else "—"} | {freq} | {area} |')
 lines+=['','| Implemented core | Setup WNS ns | Hold WHS ns | Internal endpoints unconstrained |','|---|---:|---:|---:|']
 for r in result['hls']:
  if r.get('routed_slacks_ns'):lines.append(f'| {r["variant"]} | {r["routed_slacks_ns"]["setup"]} | {r["routed_slacks_ns"]["hold"]} | {r["timing_constraint_checks"].get("unconstrained_internal_endpoints")} |')
 lines+=['','Automatic HLS co-sim memory is functional. Cycles include initialization, heap/CSR/labels, IPIN recording and drain, but do not establish real HBM service time. The first adversarial transaction contains three samples; tiny-native transactions contain four. Do not compare these as the same workload. Empty/error transactions are kept separately. OOC target frequency is reported only when place/route met that constraint, never the reciprocal of an estimated critical path.','','## Resident software measurements','', '| Record | Evidence | Workers / contexts | Scope | Seconds | Matches native |','|---|---|---|---|---:|---|']
 for r in result['measurements']:
  values=[m.get('resident_elapsed_s') for m in r.get('measurements',[r]) if m.get('resident_elapsed_s') is not None];val=statistics.median(values) if values else '—';name=str(Path(r['record_path']).relative_to(root));lines.append(f'| {name} | {r.get("evidence_type","failed")} | {r.get("cpu_workers")} / {r.get("contexts")} | {r.get("timing_scope")} | {val} | {r.get("matches_reference")} |')
 if result['software_summary']:
  lines+=['','## Preferred E1 cohort: same worker and eight physical cores','', '| Workload/backend | Median seconds | Range |','|---|---:|---|']
  for name,row in result['software_summary']['E1_resident'].items():lines.append(f'| {name} | {row["median"]} | {row["range"]} |')
  lines+=['',result['software_summary']['E1_cpu_affinity_limit']]
 if result['native_software_summary']:
  lines+=['','## Full native lookahead builder E2 (cohort identified in report.json)','', '| Native variant, 8 physical cores | Median seconds | Range |','|---|---:|---|']
  for name,row in result['native_software_summary']['E2_native'].items():lines.append(f'| {name} | {row["median"]} | {row["range"]} |')
  lines+=['', 'E2 log timer resolution is 0.01 s; these small differences require caution. '+result['native_software_summary']['E1_cpu_affinity_limit']]
 result['ablations']=[]
 by_name={r['variant']:r for r in result['hls']}
 for label,control,variant in [('eligible CSR','hls_tiny','hls_eligible'),('label cache 64','hls_cache_off','hls_label64'),('heap top 31','hls_cache_off','hls_heap31'),('four AXI masters vs one','hls_one_port','hls_cache_off'),('parallel dual engines','hls_dual_serial_dependency','hls_dual_ports_v3')]:
  c=by_name.get(control,{}).get('core_cycles');v=by_name.get(variant,{}).get('core_cycles')
  if c and v:result['ablations'].append(dict(name=label,control=control,variant=variant,control_cycles=c,variant_cycles=v,speedup=c/v,cycle_reduction_pct=100*(1-v/c),evidence_type='fpga_rtl_functional'))
 lines+=['','## Matched tiny-native ablations','', '| Change | Control | Cycles before → after | Cycle reduction |','|---|---|---:|---:|']
 for row in result['ablations']:lines.append(f'| {row["name"]} | {row["control"]} | {row["control_cycles"]} → {row["variant_cycles"]} | {row["cycle_reduction_pct"]:.2f}% |')
 lines+=['','Removing DATAFLOW alone did not serialize independent calls (`hls_dual_serial`: 208948 cycles). The valid serial control uses the first engine completion status to gate the second. The serial dependency also lets HLS share arithmetic (4 DSP estimated versus 8 in the parallel version); report this as parallel engine replication, not isolated scheduler benefit or proof of shared-pipeline latency hiding.','', '## Request-latency sensitivity (uncalibrated)','', '| Variant | Request latency | Functional cycles | Output ports match |','|---|---:|---:|---|']
 for name,row in result['latency_probes'].items():lines.append(f'| {name} | 64 | {row["cycles"]} | {all(row["rtl_result_ports_match_c"].values())} |')
 lines+=['','The memory probe changes request latency only. Read/write service remains independent; there is no calibrated shared-bandwidth arbitration. Original stale-report parser outputs are retained and superseded by result_corrected.json from fresh XSim records. No cycles are extrapolated to large graphs.','', 'Heap recurrence diagnosis: `heap_ii_diagnosis.json`, csynth.log lines 100–115 and the authoritative verbose schedule. Automatic heap sift-down achieved II=29; dependent AXI queue requests/responses constrain the recurrence. This is not a demonstrated memory-port shortage.']
 lines+=['','CUDA uses one warmup and three measured batches per process; CPU measures one batch per process with OpenMP startup included. Preserve this methodological difference. CPU formal comparisons require the same host, worker/NUMA budget and scope; use the preferred completed worker cohort for same-host GPU comparisons. Local pilot measurements overlapped development/tool flows and are diagnostic. Native B0/B1 component records are E2; C1 and CUDA are E1, so no cross-scope speedup is calculated.','','## Boundaries and outstanding work','', '- Pinned E1 CPU/CUDA measurements all passed. The pinned job failed its native-control affinity audit because OMP_PROC_BIND pinned the native main thread; that E2 cohort is excluded. The first worker retains valid E2 results; when present, the repaired confirmation cohort is preferred for both E1 and E2. The future runner clears binding variables for native controls; all four local native controls passed the repaired environment audit. A separate confirmation job records CPU topology/compiler and rechecks E1/E2 together; its success is determined from its receipt and command records, not inferred from this text.','- Two-context prototype duplicates complete engines and uses eight logical AXI masters; it is not yet a shared-pipeline interleaver. Shared-bundle synthesis failure and the first adapter-padding cosim failure are retained.','- Top-cache, label-cache, CSR and port studies use the same tiny complete native RRG and functional memory assumptions. Their benefits must be compared to the matching cache-off control.','- Physical HBM mapping, bounded latency/bandwidth/backpressure modeling, calibrated large-graph prediction, cost LUT residency and compact geometry mapping remain unimplemented.','- GPU/FPGA E2 online service integration and representative full downstream FULL/STA validation remain outstanding. Offline map import is only a correctness bridge.','- Existing results/native_* and CPU paper files remain frozen.','', 'Reproduction and format: `accel/lookahead/README.md`. Logs, commands, return codes, input/source/binary hashes and phase snapshots are under the experiment directory.']
 (o/'report.json').write_text(json.dumps(result,indent=2));(o/'report.md').write_text('\n'.join(lines)+'\n');print(o/'report.md')
if __name__=='__main__':main()

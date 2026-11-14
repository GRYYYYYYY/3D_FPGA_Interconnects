"""Derive delivery tables from bound outputs; never execute a performance path."""
from pathlib import Path
import collections,csv,hashlib,json,re
ROOT=Path(__file__).resolve().parents[4]; R=ROOT/'results/fpga_local_fabric_20261115'
GPU={'bnn_export':0.15179996944444446,'lstm_s2':0.15949799988888888}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_text())
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def timing():
 result={}
 for name in ['front_ooc_a','publication_ooc_a','backend_ooc_a','backend_ooc_b']:
  d=R/name;s=(d/'timing_summary.rpt').read_text();a=re.search(r'WNS\(ns\).*?\n.*?\n\s*([-\d.]+.*?)\n',s,re.S).group(1).split();a=list(map(float,a))
  c={k:int(v) for k,v in re.findall(r'checking (\w+) \((\d+)\)',s)}
  x={'tool':'Vivado2022.2','part':'xcu280-fsvh2892-2L-e','clock_period_ns':5,'input_min_ns':.1,'input_max_ns':.8,'output_min_ns':.1,'output_max_ns':.8,'setup_WNS_ns':a[0],'setup_TNS_ns':a[1],'hold_WHS_ns':a[4],'hold_THS_ns':a[5],'pulse_WPWS_ns':a[8],'coverage':c,'methodology_violations':int(re.search(r'Violations found:\s*(\d+)',(d/'methodology.rpt').read_text()).group(1)),'route_status':(d/'route_status.rpt').read_text(),'scope':'routed OOC context, real launch/capture and ready/valid loads; no full kernel or external physical clock/IO placement qualification','OOC_limits':['HD.CLK_SRC and HD.PARTPIN_LOCS absent: upstream clock and external interface routing not established','No arbitrary input-min changes or false paths; original .100/.800 ns constraints retained'],'complete_kernel_clock_qualified':False,'reports_sha256':{p.name:sha(p) for p in d.iterdir() if p.suffix in ['.rpt','.xdc','.tcl','.dcp']}}
  if (d/'rtstat10_connectivity.csv').exists():
   rows=list(csv.DictReader((d/'rtstat10_connectivity.csv').open()));x['RTSTAT10']={'nets':len(rows),'all_hierarchical_output_only':all(z['route_status']=='HIERPORT'and z['leaf_input_pins']=='0'and z['output_ports']=='1'for z in rows),'sha256':sha(d/'rtstat10_connectivity.csv')}
  assert all(v==0 for v in c.values()) and len(c)==12
  save(d/'timing_qualification.json',x);result[name]=x
 save(R/'timing_summary.json',result)
def warnings():
 result=[]
 for p in sorted((R/'.vivado-ai').glob('vivado_*.log')):
  s=p.read_text(errors='replace');starts=list(re.finditer(r'^# synth_design -top (\S+).*$',s,re.M))
  for i,m in enumerate(starts):
   end=starts[i+1].start()if i+1<len(starts)else len(s);segment=s[m.start():end];ids=collections.Counter(re.findall(r'^(?:CRITICAL )?WARNING: \[([^\]]+)\]',segment,re.M));examples={}
   for line in segment.splitlines():
    a=re.match(r'(?:CRITICAL )?WARNING: \[([^\]]+)\]',line)
    if a:examples.setdefault(a.group(1),line)
   result.append({'log':str(p.relative_to(ROOT)),'top':m.group(1),'start_line':s.count('\n',0,m.start())+1,'scope':'synth command through next synth command; includes implementation and read-only audits if present','warning_occurrences_by_id':dict(ids),'first_example':examples,'errors':re.findall(r'^ERROR:.*$',segment,re.M),'critical':re.findall(r'^CRITICAL WARNING:.*$',segment,re.M)})
 save(R/'warnings_analysis.json',{'segments':result,'classification':{'network_implicit_generate':'Synth8-10643/10744 accepted named generate syntax in2022.2; actual mapped netlist and protocol tests retained','adapter_unused_line':'adapter checks only low5 port bits; full32-bit line goes separately to request payload, not truncated','radix_hold_trim':'Synth8-3936 destination6 bits dead after final stage; output data/identity retained','old_local_port_ram_style':'ec_tagged_port multidimensional queues map to registers (8-7186). Actual context LUT/FF included; local fabric is removed when composing common-network budget, not added twice','enum_masks0':'enum2_bank masks[0]/hits[0]/ways[0] are undriven pipeline placeholders overwritten at stage1 from selected metadata before any valid stage2/3 use; actual native oracle passes. No functional output intentionally tied off','scratch_ram_style':'spilled RAM maps LUTRAM; replacement copies produce32 SYNTH-5 mapped-LUTRAM methodology warnings. Actual mapped usage included','pending_uram':'no extra output pipeline (Synth8-6057); real5ns context postroute measured instead of assigning a free extra latency','journal_registers':'acked table multiwrite/reset requires registers, included in real resources','OOC_boundaries':'Route35-197/198 and Timing38-242 restrict external physical clock/IO qualification; no full-kernel frequency claimed','connectivity_queries':'Vivado12-1023 empty get_pins for output-only nets; rtstat10_connectivity.csv explicitly classifies all1794 as HIERPORT, zero leaf sinks, one output port'}})
def full():
 rows=[]
 for case,gpu in GPU.items():
  p=R/'model_d'/f'L1_{case}_summary.json'
  if not p.exists():continue
  s=read(p);assert s['all_pass']and s['complete_batch']and len(s['sample_receipts'])==40
  assert s['full_output_sha256']==s['golden_sha256'] and sha(R/'model_d'/f'L1_{case}_output.bin')==s['full_output_sha256']
  fs=[read(Path(x['finite_path']))for x in s['sample_receipts']];ps=[read(Path(x['finite_path']).parent/'pool_service.json')for x in s['sample_receipts']]
  stages=ps[0]['stages'];causes=ps[0]['cause_columns'];life={};groups=[g for a in ps for g in a['groups']]
  for k,name in enumerate(stages):
   z=[g['lifetimes'][k]for g in groups if g['lifetimes'][k]['n']];n=sum(x['n']for x in z);sm=sum(x['sum']for x in z);life[name]={'n':n,'sum_cycles':sm,'min':min((x['min']for x in z),default=0),'max':max((x['max']for x in z),default=0),'mean':sm/n if n else None}
  cause={name:sum(g['causes'][k]for g in groups) for k,name in enumerate(causes)}
  target=[sum(g['target_occupancy'][k]for g in groups)for k in range(9)]
  phases=s['phase_cycles'];budget=gpu*200e6;expand_budget=budget-sum(v for k,v in phases.items()if k!='pop_expand')
  pool={'lifetimes':life,'cause_group_cycles':cause,'target_occupancy_histogram':target,'warning':'cause totals sum group observations, may overlap; not batch wall cycles or independent causal proof','conditional_expand_budget_to_match_GPU':expand_budget,'observed_parents_per_expand_cycle':s['counts']['parents']/phases['pop_expand'],'required_valid_parent_rate_if_other_phases_fixed':s['counts']['parents']/expand_budget if expand_budget>0 else None,'required_T_admission_rate_including_stale_POP':s['counts']['pop_transactions']/expand_budget if expand_budget>0 else None,'no_capacity_extension':'Ready and E backpressure accompanies much of D-full time. T-full/D-free is not sufficient proof; no sole pool enlargement selected. Original means include queues and cannot be treated as invariant Little-law latency.'}
  if expand_budget>0:
   pool['Q_from_observed_minima_only_not_sizing_recommendation']={name:(s['counts']['pop_transactions']if i==0 else s['counts']['parents'])*life[name]['min']/expand_budget for i,name in enumerate(stages[:2])}
  tail=[0]*8;hist=[0]*65
  for obj in fs:
   for z in obj['critical_final_bank_observers']:
    tail=[a+b for a,b in zip(tail,z['exclusive_histogram'])]
   hist=[a+b for a,b in zip(hist,obj['emit_population_histogram'])]
  pool['critical_final_bank_histogram']=tail;pool['emit_population_histogram']=hist
  pool['critical_final_labels']=['actual_retire','publication_held','K8_full','scratch_busy','input_pending','enum_active','phase_busy_other','idle']
  net={side:[{'link_handshakes':0,'output_blocked_cycles':0,'head_not_granted_cycles':0,'fifo_peak':0}for _ in range(3)]for side in ['request','return']}
  for receipt in s['sample_receipts']:
   n=read(Path(receipt['finite_path']).parent/'radix_service.json')
   for side in net:
    for i,stage in enumerate(n[side]):
     for e in stage:
      for k,v in e.items():net[side][i][k]=max(net[side][i][k],v)if k=='fifo_peak'else net[side][i][k]+v
  pool['radix_per_stage_all_endpoint_counts']=net
  pool['conditional_candidate_rate_if_other_phases_fixed']=s['counts']['candidates']/expand_budget if expand_budget>0 else None
  save(R/f'full_pool_{case}.json',pool)
  row={'case':case,'configuration':'L1','cycles':s['conditional_cycles'],'conditional_seconds_200MHz':s['conditional_seconds'],'resident_GPU_seconds':gpu,'conditional_FPGA_over_GPU':s['conditional_seconds']/gpu,'phase_cycles':phases,'counts':s['counts'],'complete_output_sha256':s['full_output_sha256'],'summary_sha256':sha(p),'complete_kernel_clock_qualified':False,'estimated_seconds_at_qualified_clock':None,'board_measured':False,'board_measured_seconds':None}
  rows.append(row)
 if len(rows)==2:
  save(R/'fullbatch_analysis.json',{'results':rows,'full_kernel_gate':'not_entered_performance_no_go'if all(x['conditional_FPGA_over_GPU']>1 for x in rows)else'needs_review','L2_fullbatch':'not_entered_resource_no_go_1794_LUT_over_capacity','capacity_extension_points_tested':0})
  print(json.dumps(rows,indent=2))
if __name__=='__main__':timing();warnings();full()

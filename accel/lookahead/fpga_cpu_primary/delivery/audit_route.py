"""Bounded read-only audit of existing Vivado reports. Never launches EDA/signs off.

python3 audit_route.py REPORT_DIR --out NEW_JSON [--files MAP_JSON]
--files explicitly maps logical report names to paths for historical parser tests.
The output must be new and may not overwrite any report. Unknowns remain null.
"""
from pathlib import Path
import argparse, collections, csv, datetime, hashlib, io, json, math, re

FILES = {
 'timing':'route_timing.rpt','setup':'setup_paths.rpt','hold':'hold_paths.rpt',
 'route':'route_status.rpt','utilization':'route_utilization.rpt',
 'hierarchy':'route_hierarchy.rpt','drc':'route_drc.rpt',
 'methodology':'methodology.rpt','check_timing':'check_timing.rpt',
 'clocks':'clocks.rpt','exceptions':'exceptions.rpt',
 'constraints':'actual_constraints.xdc','binding':'binding.json',
 'census':'primitive_census.csv','surviving_hierarchy':'surviving_hierarchy.txt',
 'connectivity':'output_connectivity.csv','blackboxes':'blackboxes.txt',
 'checkpoint':'full_route.dcp',
 'synth_log':'project/cp_full.runs/synth_1/runme.log',
 'impl_log':'project/cp_full.runs/impl_1/runme.log',
 'route_script':'route_reports.tcl','census_script':'census.tcl',
}
CHECKS = ['no_clock','constant_clock','pulse_width_clock',
 'unconstrained_internal_endpoints','no_input_delay','no_output_delay',
 'multiple_clock','generated_clocks','loops','partial_input_delay',
 'partial_output_delay','latch_loops']
NUM = r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?'
TIMING_FIELDS = ['WNS_ns','TNS_ns','setup_failing_endpoints','setup_total_endpoints',
 'WHS_ns','THS_ns','hold_failing_endpoints','hold_total_endpoints',
 'WPWS_ns','TPWS_ns','pulse_failing_endpoints','pulse_total_endpoints']
RESOURCE_NAMES = ['CLB LUTs','CLB Registers','LUT as Logic','LUT as Memory',
 'Block RAM Tile','URAM','DSPs','BUFGCE','BUFGCTRL','BUFGCE_DIV']

def number(s):
 s=s.strip().replace(',','')
 if not re.fullmatch(NUM,s):return None
 v=float(s)
 return (int(v)if v.is_integer()else v)if math.isfinite(v)else None

def headers(text):
 return {m[1].strip():m[2].strip()for m in re.finditer(r'^\|\s*([^|:\n]+?)\s*:\s*(.*?)\s*$',text,re.M)}

def timing(text):
 out={k:None for k in TIMING_FIELDS};out['evidence']=None
 lines=text.splitlines();start=next((i for i,l in enumerate(lines)if 'Design Timing Summary'in l),None)
 if start is not None:
  h=next((i for i in range(start,min(start+20,len(lines)))if 'WNS(ns)'in lines[i]and'WPWS(ns)'in lines[i]),None)
  if h is not None:
   for i in range(h+1,min(h+8,len(lines))):
    tokens=lines[i].split()
    if len(tokens)==12 and all(number(t)is not None for t in tokens):
     out.update(zip(TIMING_FIELDS,map(number,tokens)));out['evidence']={'line':i+1,'text':lines[i]};break
 out['unconstrained_paths_requested']='-report_unconstrained'in headers(text).get('Command','')
 out['tool_says_constraints_met']='All user specified timing constraints are met.'in text
 return out

def check_timing(text):
 all_=collections.defaultdict(set);raw=[]
 for i,l in enumerate(text.splitlines(),1):
  m=re.search(r'\bchecking\s+(\w+)\s+\((\d+)\)',l)
  if m:all_[m[1]].add(int(m[2]));raw.append({'line':i,'check':m[1],'count':int(m[2])})
 return {'counts':{k:next(iter(all_[k]))if len(all_[k])==1 else None for k in CHECKS},
  'all_logged_checks':{k:sorted(v)for k,v in all_.items()},
  'conflicting_counts':[k for k,v in all_.items()if len(v)>1],'evidence':raw}

def paths(text):
 out=[]
 for block in re.split(r'(?=^Slack \()',text,flags=re.M):
  m=re.match(r'Slack \(([^)]+)\)\s*:\s*('+NUM+r')ns',block)
  if not m:continue
  row={'slack_ns':number(m[2]),'reported_state':m[1]}
  for key,label in [('source','Source'),('destination','Destination'),('path_group','Path Group'),('path_type','Path Type'),('requirement','Requirement'),('data_path_delay','Data Path Delay')]:
   f=re.search(r'^\s*'+label+r':\s*(.+)$',block,re.M);row[key]=f[1].strip()if f else None
  row['source_scope']='cell_pin'if row['source']and'/'in row['source']else'port_or_unknown'
  row['destination_scope']='cell_pin'if row['destination']and'/'in row['destination']else'port_or_unknown'
  row['unset_net_lines']=[l.strip()for l in block.splitlines()if re.search(r'net\s+\([^)]*\bunset\b',l)]
  out.append(row)
 return {'reported_path_count':len(out),'paths':out,'worst_reported_slack_ns':min((p['slack_ns']for p in out),default=None),'scope':'Only paths emitted by the report; not a complete path census.'}

def route(text):
 vals={};evidence=[]
 for i,l in enumerate(text.splitlines(),1):
  m=re.match(r'\s*# of (.*?)\.+\s*:\s*([\d,]+)\s*:',l)
  if m:vals[m[1]]=number(m[2]);evidence.append({'line':i,'label':m[1],'count':number(m[2])})
 required=['logical nets','routable nets','fully routed nets','nets with routing errors']
 known=all(k in vals for k in required)
 return {'counts':vals,'required_counts_present':known,
  'routable_minus_fully_routed':vals['routable nets']-vals['fully routed nets']if known else None,
  'evidence':evidence,'external_boundary_routing_qualified':False}

def utilization(text):
 out={}
 lut_notes=[{'line':i,'text':l}for i,l in enumerate(text.splitlines(),1)if 'LUT combining'in l or 'Final LUT count'in l]
 for i,l in enumerate(text.splitlines(),1):
  cols=[s.strip()for s in l.split('|')[1:-1]]
  label=cols[0].rstrip('*').rstrip()if cols else''
  if len(cols)==6 and label in RESOURCE_NAMES and label not in out:
   out[label]={'used':number(cols[1]),'fixed':number(cols[2]),'prohibited':number(cols[3]),'available':number(cols[4]),'util_percent':number(cols[5]),'line':i,'text':l,'raw_label':cols[0]}
   if label=='CLB LUTs':
    out[label]['report_footnotes']=lut_notes
    out[label]['footnote_interpretation']='Reported LUT count is adjusted for LUT combining; opt_design/physical optimization may reduce the count. This is not a routed count or timing/fit qualification.'if lut_notes else None
 return out

def violations(text):
 totals=[int(m)for m in re.findall(r'Violations found:\s*(\d+)',text)]
 rules=[]
 for i,l in enumerate(text.splitlines(),1):
  c=[x.strip()for x in l.split('|')[1:-1]]
  if len(c)>=4 and re.fullmatch(r'[A-Za-z][\w-]*-\d+',c[0])and number(c[-1])is not None:
   rules.append({'rule':c[0],'severity':c[1],'description':' | '.join(c[2:-1]),'count':number(c[-1]),'line':i})
 # A recognized explicit total is required; absence of ERROR text is not zero.
 explicit_none=bool(re.search(r'\bNo (?:DRC |methodology )?violations (?:were )?found\b',text,re.I))
 total=totals[0]if totals and len(set(totals))==1 else(0 if explicit_none else None)
 return {'violations_found':total,'rules':rules,'conflicting_totals':len(set(totals))>1,'counted_rule_violations':sum(r['count']for r in rules)}

def clocks(text):
 out=[]
 for i,l in enumerate(text.splitlines(),1):
  # Clock Summary (waveform first) and report_clocks (period first).
  m=re.match(r'^\s*(\S+)\s+\{([^}]+)\}\s+('+NUM+r')\s+('+NUM+r')\s*$',l)
  if m:out.append({'name':m[1],'period_ns':number(m[3]),'waveform':m[2],'reported_frequency_MHz':number(m[4]),'line':i});continue
  m=re.match(r'^\s*(\S+)\s+('+NUM+r')\s+\{([^}]+)\}(.*)$',l)
  if m:out.append({'name':m[1],'period_ns':number(m[2]),'waveform':m[3],'attributes_sources':m[4].strip(),'line':i})
 return out

def exception_scan(text):
 pats=r'set_false_path|set_multicycle_path|set_max_delay|set_min_delay|set_clock_groups|inferred exception|Synth 8-326|set_disable_timing|set_logic_(?:zero|one|unconnected)'
 lines=[{'line':i,'text':l}for i,l in enumerate(text.splitlines(),1)if re.search(pats,l)]
 return {'evidence':lines,'inferred_loop_exception':any('inferred exception'in x['text']or'Synth 8-326'in x['text']for x in lines),'auto_waived':False}

def audit(report_dir, overrides, max_bytes, expected_top, parser_only):
 root=report_dir.resolve();artifacts={};texts={};missing=[];review=[];violated=[]
 for key,default in FILES.items():
  p=Path(overrides.get(key,default));p=p if p.is_absolute()else root/p
  entry={'path':str(p),'present':p.is_file(),'sha256':None};artifacts[key]=entry
  if not p.is_file():missing.append('missing_file:'+key);texts[key]='';continue
  before=p.stat();entry.update(bytes=before.st_size,mtime_ns=before.st_mtime_ns)
  if before.st_size>max_bytes:entry['read_status']='over_size_limit';missing.append('bounded_read_skipped:'+key);texts[key]='';continue
  if key=='checkpoint':
   # DCP can exceed 1 GiB. Retain only one 1 MiB chunk, with a cap+1 probe.
   texts[key]='';digest=hashlib.sha256();read_bytes=0
   with p.open('rb',buffering=0) as f:
    while read_bytes<=max_bytes:
     chunk=f.read(min(1024*1024,max_bytes+1-read_bytes))
     if not chunk:break
     read_bytes+=len(chunk)
     if read_bytes>max_bytes:break
     digest.update(chunk)
   after=p.stat();stable=before.st_size==after.st_size==read_bytes and before.st_mtime_ns==after.st_mtime_ns
   entry.update(bytes_read=read_bytes,mtime_ns_after=after.st_mtime_ns,bytes_after=after.st_size,stable_during_read=stable)
   if read_bytes>max_bytes or after.st_size>max_bytes:
    entry['read_status']='grew_over_size_limit';missing.append('bounded_read_skipped:'+key)
   elif not stable:
    entry['read_status']='changed_during_read';missing.append('changed_during_read:'+key)
   else:
    entry.update(sha256=digest.hexdigest(),read_status='streamed')
    if not read_bytes:missing.append('empty_file:'+key)
   continue
  with p.open('rb') as f:data=f.read(max_bytes+1)
  if len(data)>max_bytes:entry['read_status']='grew_over_size_limit';missing.append('bounded_read_skipped:'+key);texts[key]='';continue
  after=p.stat();entry.update(sha256=hashlib.sha256(data).hexdigest(),stable_during_read=before.st_size==after.st_size and before.st_mtime_ns==after.st_mtime_ns)
  if not entry['stable_during_read']:missing.append('changed_during_read:'+key)
  texts[key]=''if key=='checkpoint'else data.decode('utf-8',errors='replace')
  if key!='checkpoint':entry['header']=headers(texts[key])
  if not data and key!='blackboxes':missing.append('empty_file:'+key)
 t=timing(texts['timing']);ct=check_timing(texts['check_timing']);embedded=check_timing(texts['timing']);rs=route(texts['route']);util=utilization(texts['utilization']);sp=paths(texts['setup']);hp=paths(texts['hold']);dr=violations(texts['drc']);mt=violations(texts['methodology']);clock_rows=clocks(texts['clocks']);summary_clocks=clocks(texts['timing'])
 if any(t[k]is None for k in TIMING_FIELDS):missing.append('unparsed_design_timing_summary')
 if not t['unconstrained_paths_requested']:review.append('timing_summary_not_explicitly_report_unconstrained')
 for k in ['WNS_ns','WHS_ns','WPWS_ns']:
  if t[k]is not None and t[k]<0:violated.append('negative_'+k)
 for k in ['setup_failing_endpoints','hold_failing_endpoints','pulse_failing_endpoints']:
  if t[k]is not None and t[k]!=0:violated.append(k)
 for k,v in ct['counts'].items():
  if v is None:missing.append('unknown_check_timing:'+k)
  elif v>0:review.append('nonzero_check_timing:'+k)
  if v is not None and embedded['counts'][k]is not None and v!=embedded['counts'][k]:review.append('inconsistent_check_timing:'+k)
 if ct['conflicting_counts']:review.append('conflicting_check_timing_counts')
 if not rs['required_counts_present']:missing.append('unknown_route_counts')
 else:
  if rs['routable_minus_fully_routed']!=0:violated.append('not_all_routable_nets_fully_routed')
  if rs['counts']['nets with routing errors']!=0:violated.append('routing_errors')
 if rs['counts'].get('implicitly routed ports',0)>0:review.append('implicit_OOC_port_routing_is_not_external_route_qualification')
 for name in ['CLB LUTs','CLB Registers','Block RAM Tile','URAM','DSPs']:
  if name not in util or util[name]['used']is None or util[name]['available']is None:missing.append('unknown_resource:'+name)
  elif util[name]['used']>util[name]['available']:violated.append('resource_over_capacity:'+name)
 if 'Routed'not in headers(texts['utilization']).get('Design State',''):review.append('utilization_not_reported_routed')
 for key,obj in [('setup',sp),('hold',hp)]:
  if not obj['reported_path_count']:missing.append('no_parsed_'+key+'_paths')
  if obj['worst_reported_slack_ns'] is not None and obj['worst_reported_slack_ns']<0:violated.append('negative_'+key+'_reported_path')
  if any(p['unset_net_lines']for p in obj['paths']):review.append(key+'_path_contains_unset_nets')
 for key,obj in [('drc',dr),('methodology',mt)]:
  if obj['violations_found']is None:missing.append('unknown_'+key+'_violation_total')
  elif obj['violations_found']>0:review.append(key+'_violations_present')
  if obj['conflicting_totals']:review.append(key+'_conflicting_totals')
  if obj['counted_rule_violations']>0:review.append(key+'_rule_violations_present')
  if obj['rules'] and obj['counted_rule_violations']!=obj['violations_found']:review.append(key+'_rule_count_differs_from_total')
 if not clock_rows:missing.append('unknown_clock_report')
 scans={k:exception_scan(texts[k])for k in ['exceptions','constraints','synth_log','impl_log']}
 if any(v['inferred_loop_exception']for v in scans.values()):violated.append('inferred_timing_loop_exception_not_waived')
 if any(v['evidence']for v in scans.values()):review.append('timing_boundary_or_exception_commands_require_manual_review')
 ex_none=bool(re.search(r'\bno (?:timing )?exceptions\b',texts['exceptions'],re.I))
 if not scans['exceptions']['evidence']and not ex_none:review.append('exception_report_semantics_not_fully_parsed')
 diagnostics={k:[{'line':i,'text':l}for i,l in enumerate(texts[k].splitlines(),1)if l.startswith(('ERROR:','CRITICAL WARNING:'))]for k in ['synth_log','impl_log']}
 if any(diagnostics.values()):review.append('EDA_errors_or_critical_warnings_present')
 design_names=sorted({h['Design']for a in artifacts.values()if(h:=a.get('header',{})).get('Design')})
 if not design_names:missing.append('report_design_identity_missing')
 if design_names!=[expected_top]:review.append('report_design_identity_not_expected_top')
 tools=sorted({h['Tool Version']for a in artifacts.values()if(h:=a.get('header',{})).get('Tool Version')})
 if len(tools)>1:review.append('mixed_report_tool_versions')
 binding=None;source_checks=[]
 if texts['binding']:
  try:
   binding=json.loads(texts['binding']);bound=binding.get('source',binding.get('sources',{}))
   if not bound and all(isinstance(v,str)and re.fullmatch('[0-9a-f]{64}',v)for v in binding.values()):bound=binding
   for file,h in bound.items():
    p=root/'source'/Path(file).name;z={'source':file,'expected_sha256':h,'frozen_path':str(p),'match':None};source_checks.append(z)
    if not p.is_file()or p.stat().st_size>max_bytes:missing.append('frozen_source_unavailable:'+file);continue
    before=p.stat()
    with p.open('rb') as f:data=f.read(max_bytes+1)
    after=p.stat()
    if len(data)>max_bytes or before.st_size!=after.st_size or before.st_mtime_ns!=after.st_mtime_ns:missing.append('frozen_source_unstable_or_oversize:'+file);continue
    z['actual_sha256']=hashlib.sha256(data).hexdigest();z['match']=z['actual_sha256']==h
    if not z['match']:violated.append('frozen_source_hash_mismatch:'+file)
   if not bound:missing.append('unrecognized_source_binding')
  except (ValueError,TypeError,AttributeError):missing.append('unparsed_binding_json')
 census=[];connectivity=[]
 for key,target,cols in [('census',census,{'scope','primitive','count'}),('connectivity',connectivity,{'port','leaf_driver_count','driver_refs'})]:
  if texts[key]:
   reader=csv.DictReader(io.StringIO(texts[key]))
   if not cols.issubset(reader.fieldnames or []):missing.append('unrecognized_'+key+'_schema')
   else:target.extend(reader)
 blackboxes=texts['blackboxes'].split()if artifacts['blackboxes'].get('sha256') and artifacts['blackboxes'].get('stable_during_read') else None
 if blackboxes:violated.append('blackboxes_present')
 if connectivity and any(number(x.get('leaf_driver_count',''))in (None,0)or all(y in ('GND','VCC')for y in x.get('driver_refs','').split('|'))for x in connectivity):review.append('output_connectivity_has_missing_constant_or_unknown_drivers')
 hd=[{'line':i,'text':l}for i,l in enumerate(texts['constraints'].splitlines(),1)if'HD.CLK_SRC'in l]
 review.extend(['clock_source_and_external_boundary_context_require_human_review','report_checkpoint_source_association_requires_human_review','no_formal_equivalence_or_full_functional_proof_from_reports'])
 if parser_only:review.append('historical_parser_test_only_not_current_design_evidence')
 return {'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'INCOMPLETE'if missing else'MANUAL_REVIEW','signoff':False,'timing_qualified':False,'board_measured':False,'parser_only':parser_only,'report_dir':str(root),'expected_top':expected_top,'limits':{'max_bytes_per_file':max_bytes,'artifact_count':len(artifacts)},'artifacts':artifacts,'design_names':design_names,'tool_versions':tools,'timing':t,'setup_paths':sp,'hold_paths':hp,'check_timing':ct,'embedded_check_timing':embedded,'routing':rs,'utilization':util,'drc':dr,'methodology':mt,'clocks':clock_rows,'summary_clocks':summary_clocks,'exceptions':scans,'diagnostics':diagnostics,'clock_source_constraints':hd,'source_binding':binding,'source_checks':source_checks,'primitive_census':census,'output_connectivity':connectivity,'blackboxes':blackboxes,'missing_or_unknown':sorted(set(missing)),'observed_violations':sorted(set(violated)),'manual_review_reasons':sorted(set(review)),'limitations':['No fit/frequency/signoff is inferred from WNS, one bank, an old DCP or a different run.','No false-path, disabled-timing or inferred-loop exception is automatically waived.','Counts absent from a report remain unknown, never zero.','Routing all routable nets does not establish external OOC boundary or shell routing.','Raw hashes identify files; matching filenames/timestamps alone do not prove common checkpoint provenance.']}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('report_dir',type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--files',type=Path);p.add_argument('--expected-top',default='cp_full_top');p.add_argument('--parser-only',action='store_true');p.add_argument('--max-bytes',type=int,default=64*1024*1024);a=p.parse_args()
 if a.max_bytes<=0:p.error('--max-bytes must be positive')
 overrides=json.loads(a.files.read_text())if a.files else{}
 if not isinstance(overrides,dict) or not all(isinstance(k,str) and isinstance(v,str) for k,v in overrides.items()):p.error('--files must map report keys to string paths')
 if set(overrides)-set(FILES):p.error('unknown report keys: '+str(set(overrides)-set(FILES)))
 out=a.out.resolve();inputs={((Path(v)if Path(v).is_absolute()else a.report_dir/Path(v)).resolve())for v in {**FILES,**overrides}.values()}
 if out in inputs or out.exists():p.error('--out must be a new file, not an input or existing result')
 result=audit(a.report_dir,overrides,a.max_bytes,a.expected_top,a.parser_only)
 result['auditor']={'path':str(Path(__file__).resolve()),'sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
 if a.files:result['mapping_manifest']={'path':str(a.files.resolve()),'sha256':hashlib.sha256(a.files.read_bytes()).hexdigest()}
 out.parent.mkdir(parents=True,exist_ok=True)
 with out.open('x')as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({'status':result['status'],'signoff':False,'missing_or_unknown':len(result['missing_or_unknown']),'observed_violations':result['observed_violations'],'output':str(out)},indent=2))

if __name__=='__main__':main()

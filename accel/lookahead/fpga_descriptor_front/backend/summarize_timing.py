#!/usr/bin/env python3
from pathlib import Path
import json,re,csv,sys,hashlib,collections
r=Path(sys.argv[1]);raw=(r/'timing_summary.rpt').read_text();lines=raw.splitlines();numbers=None
for i,line in enumerate(lines):
 if 'WNS(ns)' in line and 'WPWS(ns)' in line:
  for x in lines[i+1:i+5]:
   p=x.split()
   if len(p)==12 and re.fullmatch(r'-?\d+\.\d+',p[0]):numbers=p;break
  if numbers:break
assert numbers
keys=['setup_wns_ns','setup_tns_ns','setup_failing_endpoints','setup_total_endpoints','hold_whs_ns','hold_ths_ns','hold_failing_endpoints','hold_total_endpoints','pulse_wpws_ns','pulse_tpws_ns','pulse_failing_endpoints','pulse_total_endpoints']
timing={k:(float(v) if k.endswith('_ns') else int(v)) for k,v in zip(keys,numbers)}
checks={k:int(v) for k,v in re.findall(r'checking (\w+) \((\d+)\)',(r/'check_timing.rpt').read_text())};assert len(checks)==12
resources={};rawutil=(r/'utilization.rpt').read_text()
for field in ['CLB LUTs','CLB Registers','LUT as Memory','Block RAM Tile','RAMB36/FIFO*','RAMB18','URAM','DSPs']:
 match=re.search(r'^\|\s+'+re.escape(field)+r'\s*\|\s*([\d.]+)\s*\|',rawutil,re.M)
 if match:resources[field]=float(match[1])
methodology=collections.Counter(re.findall(r'^([A-Z]+-\d+)#\d+\s', (r/'methodology.rpt').read_text(),re.M))
failures=collections.Counter(row['classification'] for row in csv.DictReader((r/'hold_failure_classification.csv').open()))
netclasses=collections.Counter(row['classification'] for row in csv.DictReader((r/'net_connectivity.csv').open()))
internal={}
for mode in ['setup','hold']:
 text=(r/('internal_'+mode+'.rpt')).read_text();m=re.search(r'Slack \([^)]*\)\s*:\s*(-?[\d.]+)ns',text);assert m;internal[mode+'_worst_slack_ns']=float(m[1])
contexts=collections.Counter();bad=[]
for row in csv.DictReader((r/'context_cells.csv').open()):
 contexts[row['primitive']]+=1
 if row['primitive'].startswith(('RAM','SRL')):bad.append(row)
result={'status':'ROUTED_LOCAL_TIMING_QUALIFIED' if min(timing[k] for k in ['setup_wns_ns','hold_whs_ns','pulse_wpws_ns'])>=0 and not any(checks.values()) else 'ROUTED_LOCAL_TIMING_FAIL','clock_ns':5,'input_min_ns':0.1,'input_max_ns':0.8,'output_min_ns':0.1,'output_max_ns':0.8,'timing':timing,'register_to_register':internal,'check_timing':checks,'resources':resources,'methodology':methodology,'negative_hold_classification':failures,'RTSTAT10_net_classification':netclasses,'context_storage_primitives':contexts,'non_FF_context_storage_count':len(bad),'source_binding':'source_binding.json','post_route_dcp_sha256':hashlib.sha256((r/'post_route.dcp').read_bytes()).hexdigest(),'complete_kernel_clock_qualified':False,'board_measured':False}
(r/'timing_resource_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

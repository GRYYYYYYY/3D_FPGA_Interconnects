"""Extract terminal OOC evidence. A completed route is not a timing pass."""
from pathlib import Path
import hashlib,json,re

root=Path(__file__).resolve().parents[3]
r=root/'results/fpga_sparse_stream_20261112';o=r/'tile_ooc_resident_batch'
assert json.loads((o/'receipt.json').read_text())['returncode']==0
post=json.loads((o/'postroute_receipt.json').read_text())
assert post['returncode']==0 and post['checkpoint_unchanged']

def timing(name):
 text=(o/name).read_text().split('| Design Timing Summary',1)[1]
 row=next(l.split() for l in text.splitlines() if re.match(r'^\s*-?\d+\.\d+\s+-?\d+\.\d+\s+\d+',l))
 assert len(row)==12
 keys=['WNS_ns','TNS_ns','setup_failing_endpoints','setup_total_endpoints','WHS_ns','THS_ns','hold_failing_endpoints','hold_total_endpoints','WPWS_ns','TPWS_ns','pulse_failing_endpoints','pulse_total_endpoints']
 return {k:(float(v) if k.endswith('_ns') else int(v)) for k,v in zip(keys,row)}

def path(name):
 text=(o/name).read_text()
 out={k:re.search(r'^\s*'+label+r':\s*(.+)$',text,re.M).group(1).strip() for k,label in [('source','Source'),('destination','Destination')]}
 out['slack_ns']=float(re.search(r'Slack \(\w+\)\s*:\s*(-?[\d.]+)ns',text).group(1))
 out['data_delay_ns']=float(re.search(r'Data Path Delay:\s*([\d.]+)ns',text).group(1))
 out['logic_levels']=int(re.search(r'Logic Levels:\s*(\d+)',text).group(1))
 for field in ['logic','route']:
  m=re.search(field+r' ([\d.]+)ns \(([\d.]+)%\)',text)
  out[field+'_ns']=float(m.group(1));out[field+'_percent']=float(m.group(2))
 return out

line=next(l for l in (o/'routed_utilization.rpt').read_text().splitlines() if re.match(r'\| sparse_tile\s*\|',l))
values=[int(x.strip()) for x in line.split('|')[3:-1]]
resources=dict(zip(['LUT','logic_LUT','LUTRAM','SRL','FF','RAMB36','RAMB18','URAM','DSP'],values))
assert len(values)==9
resources['BRAM_tiles']=resources['RAMB36']+resources['RAMB18']/2
route=(o/'route_status.rpt').read_text()
routes={name:int(re.search(re.escape(label)+r'\.+\s*:\s*(\d+)',route).group(1)) for name,label in [('routable','of routable nets'),('fully_routed','of fully routed nets'),('routing_errors','of nets with routing errors')]}
checks={name:int(n) for name,n in re.findall(r'^\d+\. checking (\w+) \((\d+)\)',(o/'check_timing.rpt').read_text(),re.M)}
assert checks
drc=[]
for l in (o/'drc.rpt').read_text().splitlines():
 parts=[s.strip() for s in l.split('|')]
 if len(parts)==6 and parts[2] in ['Warning','Advisory','Error','Critical Warning']:
  drc.append({'rule':parts[1],'severity':parts[2],'description':parts[3],'violations':int(parts[4])})
t200=timing('timing_200.rpt');t125=timing('timing_125_same_route.rpt')
qualified=routes['routable']==routes['fully_routed'] and routes['routing_errors']==0 and not any(checks.values()) and not any(d['severity'] in ['Error','Critical Warning'] for d in drc)
def meets(t):return qualified and all(t[k]>=0 for k in ['WNS_ns','WHS_ns','WPWS_ns'])
data={'candidate':'SPARSE_STREAMED_ALT_V2','revision':'resident_batch_commit16','actual_lanes':8,'actual_owners':8,
 'tool':'Vivado2022.2','part':'xcu280-fsvh2892-2L-e','shell_integrated':False,'board_measured':False,
 'route_completed':True,'routed_resources':resources,'route_status':routes,'check_timing':checks,'DRC':drc,
 'timing_200MHz':t200,'timing_125MHz_same_route':t125,'target_200MHz_timing_supported':meets(t200),
 '125MHz_same_route_timing_supported':meets(t125),'125MHz_scope':'constraint recheck of same route; no reimplementation or architecture performance rescaling',
 'setup_worst':path('setup_paths.rpt'),'hold_worst':path('hold_paths.rpt'),
 'internal_setup_worst':path('internal_setup_200.rpt'),'internal_hold_worst':path('internal_hold_200.rpt'),
 'input_output_delays_ns':{'max':0.5,'min':0.1},'false_paths_added':False,
 'shell_clock_source_location_defined':False,
 'postroute_query_warning_counts':{code:(o/'postroute_console.log').read_text().count('['+code+']') for code in ['Vivado 12-4439','Timing 38-242']},
 'limitations':['HD.CLK_SRC clock source locations are not provided by a shell; OOC results are not full-platform clock/skew qualification','Vivado12-4439 concerns large report query collections; all requested reports completed','hold worst is an input-boundary path under the declared0.1ns minimum input delay; internal hold is reported separately'],
 'checkpoint_sha256':post['checkpoint_sha256_after'],
 'report_sha256':{str(p.relative_to(o)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(o.glob('*.rpt'))}}
(r/'physical_audit.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps({k:data[k] for k in ['routed_resources','timing_200MHz','timing_125MHz_same_route','target_200MHz_timing_supported','125MHz_same_route_timing_supported','internal_hold_worst']},indent=2))

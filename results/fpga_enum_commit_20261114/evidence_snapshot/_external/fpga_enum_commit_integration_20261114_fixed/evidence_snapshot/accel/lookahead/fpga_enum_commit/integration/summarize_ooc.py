from pathlib import Path
import re,json,sys,hashlib,datetime
p=Path(sys.argv[1]);timing=(p/'timing_summary.rpt').read_text();start=timing.index('WNS(ns)');row=None
for line in timing[start:].splitlines():
 parts=line.split()
 if len(parts)==12:
  try:row=[float(x) for x in parts]
  except ValueError:continue
  break
assert row is not None
checks={k:int(v) for k,v in re.findall(r'checking\s+(\w+)\s+\((\d+)\)',timing)}
source=json.loads((p/'source_binding.json').read_text());hier=(p/'hierarchical_utilization.rpt').read_text();resources=[]
for line in hier.splitlines():
 cols=[x.strip() for x in line.split('|')]
 if len(cols)!=13:continue
 try:nums=list(map(int,cols[3:12]))
 except ValueError:continue
 resources.append({'instance':cols[1],'module':cols[2],**dict(zip(['LUT','logicLUT','LUTRAM','SRL','FF','BRAM36','BRAM18','URAM','DSP'],nums))})
reportfiles=[x for x in p.glob('*.rpt') if x.is_file()]
slack={'setup_WNS_ns':row[0],'setup_TNS_ns':row[1],'setup_failing_endpoints':int(row[2]),'hold_WHS_ns':row[4],'hold_THS_ns':row[5],'hold_failing_endpoints':int(row[6]),'pulse_WPWS_ns':row[8],'pulse_TPWS_ns':row[9],'pulse_failing_endpoints':int(row[10])}
passed=min(row[0],row[4],row[8])>=0 and row[2]==row[6]==row[10]==0
body={'status':'ROUTED_LOCAL_TIMING_PASS_REQUIRES_REPORT_AUDIT' if passed else 'ROUTED_LOCAL_TIMING_FAIL','tool':'Vivado2022.2','part':'xcu280-fsvh2892-2L-e','clock_ns':5,'memory_controller_included':False,'board_measured':False,'complete_kernel_clock_qualified':False,'slack':slack,'check_timing':checks,'hierarchical_resources':resources,'source_binding':'source_binding.json','report_sha256':{x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in reportfiles},'post_route_sha256':hashlib.sha256((p/'post_route.dcp').read_bytes()).hexdigest(),'terminal_observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'interface_limit':'OOC parent-context PARTPIN locations and board routes not included; declared IOdelaybudget only'}
(p/'terminal.json').write_text(json.dumps(body,indent=2)+'\n');print(json.dumps({'status':body['status'],'slack':slack,'check_timing':checks,'resources':resources[:1]},indent=2))

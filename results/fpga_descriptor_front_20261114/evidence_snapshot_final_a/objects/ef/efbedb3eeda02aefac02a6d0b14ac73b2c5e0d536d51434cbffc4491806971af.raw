from pathlib import Path
import re,json,hashlib,sys
p=Path(sys.argv[1]);f=p/'timing_summary.rpt';s=f.read_text();part=s[s.index('Design Timing Summary'):];v=next(x.split() for x in part.splitlines() if re.match(r'^\s*-?\d+\.\d+\s+-?\d+\.\d+\s+\d+',x));assert len(v)==12
checks={k:int(n) for k,n in re.findall(r'checking ([a-z_]+) \((\d+)\)',s)}
resources={};u=(p/('utilization_flat.rpt' if (p/'utilization_flat.rpt').exists() else 'utilization.rpt')).read_text()
for key in ('CLB LUTs','CLB Registers','LUT as Memory','Block RAM Tile','URAM','DSPs'):
 match=re.search(r'^\|\s*'+re.escape(key)+r'\*?\s*\|\s*([\d.,]+)',u,re.M)
 resources[key]=float(match.group(1).replace(',','')) if match else None
r={'source_binding':str(p/'binding.json'),'report':str(f),'WNS_ns':float(v[0]),'TNS_ns':float(v[1]),'setup_failing_endpoints':int(v[2]),'WHS_ns':float(v[4]),'THS_ns':float(v[5]),'hold_failing_endpoints':int(v[6]),'WPWS_ns':float(v[8]),'pulse_failing_endpoints':int(v[10]),'check_timing':checks,'resources':resources,'all_timing_pass':float(v[0])>=0 and float(v[4])>=0 and float(v[8])>=0 and len(checks)>0 and all(n==0 for n in checks.values()),'complete_kernel_clock_qualified':False,'board_measured':False,'sha256':{x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in p.glob('*.rpt')}}
(p/'timing_result.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))

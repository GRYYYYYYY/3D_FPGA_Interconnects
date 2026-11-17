#!/usr/bin/env python3
"""Archive completed natural placement evidence without submitting Vivado commands."""
import pathlib,json,hashlib,zipfile,xml.etree.ElementTree as ET,time,shutil,re
ROOT=pathlib.Path(__file__).resolve().parents[3];R=ROOT/'results/fpga_device_migration_20261117/migration_a';O=R/'placement_audit_20261117';O.mkdir(exist_ok=False)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
p=R/'place.dcp';before=p.stat();expected,length,_=(R/'place.dcp.sha256').read_text().split(maxsplit=2);actual=sha(p)
assert actual==expected and before.st_size==int(length) and before.st_mtime_ns==p.stat().st_mtime_ns
with zipfile.ZipFile(p) as z:
 xml=z.read('dcp.xml');meta=ET.fromstring(xml);assert meta.find('Part').get('Name')=='xcu250-figd2104-2L-e' and meta.find('Top').get('Name')=='cp_full_top' and meta.find('OutOfContext').get('Name')=='1'
 (O/'dcp.xml').write_bytes(xml)
 (O/'checkpoint_qor_summary.json').write_bytes(z.read('cp_full_top_rda.json'))
 for n in z.namelist():
  if n.endswith('.xdc'):(O/pathlib.Path(n).name).write_bytes(z.read(n))
t=(R/'place/utilization.rpt').read_text();global_rows={};slr_rows={};header=None
for line in t.splitlines():
 if not line.startswith('|'):continue
 c=[x.strip().rstrip('*') for x in line.strip('|').split('|')]
 if 'Site Type' in c:header=c;continue
 if header and len(c)==len(header) and 'Used' in header and c[0] not in global_rows:
  try:used=float(c[header.index('Used')])
  except ValueError:continue
  cap=c[header.index('Available')] if 'Available' in header else ''
  global_rows[c[0]]={'used':used,'available':float(cap) if cap else None}
 if header and 'SLR0' in header and len(c)==len(header) and c[0] not in slr_rows:
  try:counts={f'SLR{i}':int(c[header.index(f'SLR{i}')]) for i in range(4)}
  except ValueError:continue
  slr_rows[c[0]]={'used':counts,'reported_percent':{f'SLR{i}':c[header.index(f'SLR{i} %')] for i in range(4)}}
keys=['CLB','CLBL','CLBM','CLB LUTs','LUT as Logic','LUT as Distributed RAM','LUT as Shift Register','CLB Registers','Block RAM Tile','URAM','DSPs']
for k in keys:assert sum(slr_rows[k]['used'].values())==global_rows[k]['used'],k
sll={m.group(1):{'used':int(m.group(2)),'available':int(m.group(3)),'percent':float(m.group(4))} for m in re.finditer(r'\|\s*(SLR\d <-> SLR\d)\s*\|\s*(\d+)\s*\|\s*\|\s*(\d+)\s*\|\s*([\d.]+)',t)}
assert len(sll)==3
log=(R/'worker.log').read_text();start=log.index('INFO: [Place 30-612] Post-Placement Estimated Congestion');end=log.index('place_design: Time (s):',start);(O/'placement_completion_log.txt').write_text(log[start:end])
for name in ['utilization.rpt','hierarchy.rpt','drc.rpt','blackboxes.txt','ports.tsv']:shutil.copyfile(R/'place'/name,O/name)
result={'utc_epoch':time.time(),'checkpoint':{'path':str(p),'bytes':before.st_size,'sha256':actual,'part_top_ooc_verified':True},'stage_status_at_observation':{'place_design':{'return_code':0,'completed_utc':'2026-11-17T15:43:45Z'},'phys_opt_design':{'return_code':None,'state':'RUNNING','started_utc':'2026-11-17T15:55:19Z'},'route_design':{'return_code':None,'state':'NOT_STARTED'}},'global_resources':{k:global_rows[k] for k in keys},'SLR_resources':{k:slr_rows[k] for k in keys},'SLR_sums_match_global':True,'SLR_connectivity':sll,'SLL_status':'Post-placement connectivity accounting, not completed routed-crossing qualification','memory_capable_CLB_occupied':84394,'SLICEM_site_specific_audit':'Pending terminal DB query; retain direct report label CLBM instead of asserting an independently measured SLICEM site census. Preflight reports98880SLICEM sites.','congestion':'See original post-placement estimated Region Size table in placement_completion_log.txt; no routed congestion percentage inferred.','setup_hold_path_details':None,'path_details_status':'NOT_NATURALLY_REPORTED_AT_THIS_STAGE. Original terminal collector will emit bounded timing paths; missing SLR/fanout fields collected serially after worker terminal. No busy session commands.','drc':'Placement DRC contains1RTSTAT-13 insufficient-routing critical warning. Routing not attempted yet; neither final route failure nor route success.','clock_warning':'Timing38-242 reset HD.CLK_SRC missing observed during phys_opt, also present in old h logs. Final actual clock/control-buffer load and skew audit required; no clock or exception added to reset.','qualification':'Unqualified: phys_opt active, no route terminal, no qualified frequency. Estimated−18.525ns WNS is not signoff.'}
result['checkpoint_qor_summary']=json.loads((O/'checkpoint_qor_summary.json').read_text())
result['congestion']='DCP-embedded natural QoR summary supplies placement-estimated congestion levels in N-E-S-W order; not routed congestion or percentage. Raw region-size table also retained.'
(O/'audit.json').write_text(json.dumps(result,indent=2));manifest={str(p.relative_to(O)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in O.iterdir() if p.is_file()};(O/'manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps({'audit':str(O/'audit.json'),'global':result['global_resources'],'SLR_connectivity':sll},indent=2))

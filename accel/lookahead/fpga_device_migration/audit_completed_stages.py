#!/usr/bin/env python3
"""Read-only audit of completed synthesis/opt; never opens a Vivado design."""
import pathlib,json,hashlib,zipfile,xml.etree.ElementTree as ET,csv,re,collections,time
ROOT=pathlib.Path(__file__).resolve().parents[3]
R=ROOT/'results/fpga_device_migration_20261117/migration_a'
OLD=ROOT.parent/'3D_FPGA_Interconnects_CPU_PRIMARY/results/fpga_cpu_primary_20261115/full_synth_h_return_wordmux'
OUT=R/'continuation_audit_20261117';OUT.mkdir(exist_ok=False)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def util(p):
 rows={};header=None
 for line in p.read_text().splitlines():
  if not line.startswith('|'):continue
  c=[s.strip().rstrip('*') for s in line.strip('|').split('|')]
  if 'Used' in c and 'Available' in c:header=c;continue
  if not header or len(c)!=len(header) or c[0] in rows:continue
  try:used=float(c[header.index('Used')].replace(',',''))
  except ValueError:continue
  cap=c[header.index('Available')].replace(',','')
  rows[c[0]]={'used':used,'available':float(cap) if cap else None}
 return rows
bind=json.loads((R/'source_binding.json').read_text())
for s in bind['sources']:
 assert sha(ROOT/s['path'])==sha(R/'source'/pathlib.Path(s['path']).name)==s['sha256']
for p,h in json.loads((R/'flow_binding.json').read_text())['files'].items():assert sha(R/p)==h,p
result={'utc_epoch':time.time(),'source_count':31,'source_and_frozen_flow_verified':True,'formal_equivalence_proven':False,'stages':{}}
for stage,oldsub in [('synth',''),('opt','post_opt')]:
 p=R/(stage+'.dcp');before=p.stat();actual=sha(p);expected,length,_=(R/(stage+'.dcp.sha256')).read_text().split(maxsplit=2)
 assert actual==expected and before.st_size==int(length) and p.stat().st_mtime_ns==before.st_mtime_ns
 with zipfile.ZipFile(p) as z:
  xml=z.read('dcp.xml');meta=ET.fromstring(xml);(OUT/(stage+'_dcp.xml')).write_bytes(xml)
  assert meta.find('Part').get('Name')==bind['target_part'] and meta.find('Top').get('Name')=='cp_full_top' and meta.find('OutOfContext').get('Name')=='1'
  for name in z.namelist():
   if name.endswith('.xdc'): (OUT/(stage+'_'+pathlib.Path(name).name)).write_bytes(z.read(name))
 u=util(R/stage/'utilization.rpt');old=util(OLD/oldsub/'utilization.rpt')
 keys=['CLB LUTs','LUT as Logic','LUT as Distributed RAM','LUT as Shift Register','CLB Registers','Register as Latch','Block RAM Tile','URAM','DSPs']
 same={k:{'old_h':old[k]['used'],'new_target':u[k]['used'],'equal':old[k]['used']==u[k]['used']} for k in keys}
 assert all(v['equal'] for v in same.values())
 assert not (R/stage/'blackboxes.txt').read_text().strip()
 result['stages'][stage]={'dcp_path':str(p),'sha256':actual,'bytes':before.st_size,'metadata_verified':True,'blackboxes':0,'same_stage_resource_comparison':same,'resources':u}
new={x['port']:x for x in csv.DictReader((R/'synth/output_connectivity.csv').open())};old={x['port']:x for x in csv.DictReader((OLD/'output_connectivity.csv').open())}
assert new.keys()==old.keys()
changes={k:{'old':old[k],'new':v} for k,v in new.items() if v!=old[k]}
result['output_driver_census']={'entries':len(new),'changed_entries':changes}
newcounts={x['primitive']:int(x['count']) for x in csv.DictReader((R/'synth/primitive_census.csv').open()) if x['scope']=='TOTAL'}
oldcounts={x['primitive']:int(x['count']) for x in csv.DictReader((OLD/'primitive_census.csv').open()) if x['scope']=='TOTAL'}
result['synth_primitive_counts_identical']=newcounts==oldcounts
log=(R/'worker.log').read_text();oldlog=(OLD/'project/cp_full.runs/synth_1/runme.log').read_text()
count=lambda s:dict(collections.Counter(re.findall(r'(?:WARNING|ERROR): \[([^\]]+)\]',s)))
result['observed_warning_counts']={'old_synth':count(oldlog),'new_through_current_place':count(log),'limitation':'New log suppresses repeated messages at100; old log uses higher limit. Counts cannot be compared as incidence reductions. No new observed Synth diagnostic IDs; suppressed text is unavailable without rerun, which is not authorized.'}
result['new_observed_synth_ids']=sorted({k for k in count(log) if k.startswith('Synth ')}-set(count(oldlog)))
result['derived_gate_json_limitation']='Frozen gate.json skips rows with blank Available and can later record zero-valued unplaced SLR subrows for LUTRAM/SRL. Use original utilization.rpt and this header-aware parser for those metrics. Capacity gate main totals unaffected. Frozen flow not changed.'
result['scope']='Synthesis/opt audit only; placement active, no legal routing/timing/performance qualification.'
(OUT/'audit.json').write_text(json.dumps(result,indent=2))
print(json.dumps({'output':str(OUT),'synth_LUTRAM':result['stages']['synth']['resources']['LUT as Distributed RAM'],'output_census_changes':len(changes),'primitive_counts_identical':result['synth_primitive_counts_identical'],'new_synth_warning_ids':result['new_observed_synth_ids']},indent=2))

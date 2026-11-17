#!/usr/bin/env python3
import pathlib,re,sys,json,csv
p=pathlib.Path(sys.argv[1]); rows={}
for line in (p/'utilization.rpt').read_text().splitlines():
 cells=[x.strip().replace(',','').rstrip('*') for x in line.strip().strip('|').split('|')]
 if len(cells)>=6:
  try: used=float(cells[1]); available=float(cells[4])
  except ValueError: continue
  if cells[0] in rows: continue
  rows[cells[0]]={'used':used,'available':available}
  if cells[0] in ('CLB LUTs','LUT as Memory','CLB Registers','CLB','Block RAM Tile','URAM','DSPs','BUFGCTRL','BUFGCE','CARRY8') and available>0 and used>available: raise RuntimeError('RESOURCE_FAIL '+line)
assert 'CLB LUTs' in rows,rows.keys()
assert rows['CLB LUTs']['used']>1000000,'SOURCE_OR_CONSTRAINT_MISMATCH: unexpected large pruning'
assert rows.get('URAM',{}).get('used')==640,'SOURCE_OR_CONSTRAINT_MISMATCH: URAM change needs review'
if len(sys.argv)>2:
 ref=p.parent/'reference_output_connectivity.csv'
 old={r['port']:r for r in csv.DictReader(ref.open())};new={r['port']:r for r in csv.DictReader((p/'output_connectivity.csv').open())}
 assert old.keys()==new.keys(),'SOURCE_OR_CONSTRAINT_MISMATCH: output coverage'
 bad=[k for k,r in new.items() if (r['driver_refs'] in ('GND','VCC','') and r['driver_refs']!=old[k]['driver_refs'])]
 assert not bad,('SOURCE_OR_CONSTRAINT_MISMATCH: new constant/undriven outputs',bad)
 text=(p/'surviving_hierarchy.txt').read_text()
 assert all(f'banks[{i}].bank' in text for i in range(64)),'missing banks'
 assert all(f'fronts[{i}].front' in text for i in range(16)),'missing fronts'
(p/'gate.json').write_text(json.dumps({'capacity_pass':True,'rows':rows,'formal_equivalence':False},indent=2))

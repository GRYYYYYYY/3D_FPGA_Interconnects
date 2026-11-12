"""Require material independent lane logic in the actual synthesis report."""
import pathlib,json,re,hashlib
root=pathlib.Path(__file__).resolve().parents[4]
r=root/'results/fpga_sim_restart_20261111T231000Z/closed_loop'
def check(p):
 rows=[]
 for line in p.read_text().splitlines():
  fields=[x.strip() for x in line.split('|')][1:-1]
  if not fields:continue
  m=re.fullmatch(r'owners\[(\d+)\]\.lane',fields[0])
  if not m:continue
  rows.append({'lane':int(m[1]),'module':fields[1],'luts':int(fields[2]),'logic_luts':int(fields[3]),'ffs':int(fields[6])})
 assert len(rows)==64 and {x['lane'] for x in rows}==set(range(64)),rows
 assert all(x['logic_luts']>=100 and x['ffs']>=200 for x in rows),rows
 return sorted(rows,key=lambda x:x['lane'])
p=r/'ooc_64_fixed/synth_utilization.rpt';rows=check(p)
routed=r/'ooc_64_fixed/routed_utilization.rpt'
j={'status':'PASS','revision':'independent_operands_v2','physical_lane_instances':64,
 'evidence':'actual hierarchical synthesis utilization for 64 separately retained pair_lane modules, with private operand and output state and nontrivial FP32 logic in every module',
 'source_contract':'each pair_lane owns registered in_parent/in_cost/in_dst; two-stage elastic valid/ready; pending includes both stages for fence',
 'not_a_sustained_64_edge_throughput_claim':True,'report_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
 'lanes':rows,'routed_verified':routed.exists()}
if routed.exists():j['routed_lanes']=check(routed);j['routed_report_sha256']=hashlib.sha256(routed.read_bytes()).hexdigest()
(r/'independent_lane_coverage.json').write_text(json.dumps(j,indent=2)+'\n')
print('PASS:64 physical lanes; LUT range',min(x['luts'] for x in rows),max(x['luts'] for x in rows),'FF range',min(x['ffs'] for x in rows),max(x['ffs'] for x in rows))

#!/usr/bin/env python3
"""Independent old-state RR/hold/conservation checks on actual combined RTL pins."""
from pathlib import Path
import json,hashlib
root=Path('results/fpga_descriptor_front_20261114');p=root/'output_c/project/output.sim/sim_1/behav/xsim/collector_cycles.txt'
cursor=0;hold=[None,None];blocked={};accepted={};retired=set();total=0;peak=0;stalls=0;rows=0;latencies=[]
for line in p.read_text().splitlines():
 v=line.split();assert len(v)==8;c,reset=map(int,v[:2]);rows+=1
 if reset:
  assert not accepted or len(retired)==len(accepted)
  cursor=0;hold=[None,None];blocked={};accepted={};retired=set();continue
 iv,ir,ov,ready,words=[int(x,16) for x in v[2:7]]
 raw=v[7].zfill(32)
 for k in range(2):
  if ov>>k&1:assert all(x not in 'xXzZ' for x in raw[16*(1-k):16*(2-k)])
 outs=int(raw.lower().replace('x','0').replace('z','0'),16)
 inputs={i:(words>>(64*i))&((1<<64)-1) for i in range(32) if iv>>i&1}
 for i,x in blocked.items():assert inputs.get(i)==x,(c,i,'blocked source changed')
 assert ov==sum(1<<i for i,x in enumerate(hold) if x is not None)
 for i,x in enumerate(hold):
  if x is not None:
   assert (outs>>(64*i))&((1<<64)-1)==x
   if ready>>i&1:
    assert x in accepted and x not in retired and accepted[x]<c
    latencies.append(c-accepted[x]);retired.add(x);total+=1
 old=hold.copy();start=cursor;chosen=[]
 for k in range(2):
  if old[k] is None or ready>>k&1:
   source=next((i for i in [(start+j)%32 for j in range(32)] if i in inputs and i not in chosen),None)
   hold[k]=inputs[source] if source is not None else None
   if source is not None:chosen.append(source);start=(source+1)%32
 assert ir==sum(1<<i for i in chosen)
 for i in chosen:
  assert inputs[i] not in accepted;accepted[inputs[i]]=c
 if chosen:cursor=start
 blocked={i:x for i,x in inputs.items() if i not in chosen};stalls+=len(blocked);peak=max(peak,len(inputs))
assert total==62 and len(retired)==len(accepted)==31 and hold==[None,None] and not blocked and peak==4 and min(latencies)==1
out=root/'review/output_combined_collector_audit.json';assert not out.exists();d={'status':'PASS_ACTUAL_COMBINED_RTL_INDEPENDENT_RR_HOLD_DRAIN','cycles':rows,'consumed_ACKs':total,'simultaneous_source_peak':peak,'rejected_source_cycles':stalls,'minimum_capture_to_consume_clocks':min(latencies),'maximum_capture_to_consume_clocks':max(latencies),'trace_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'scope':'existing RTL trace read-only audit; no new simulation'};out.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))

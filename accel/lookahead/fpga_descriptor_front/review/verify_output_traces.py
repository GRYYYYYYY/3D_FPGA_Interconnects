#!/usr/bin/env python3
"""Independent read-only boundary and RR-vector audit of existing RTL evidence."""
from pathlib import Path
import hashlib,json
root=Path('results/fpga_descriptor_front_20261114')
trace=root/'output_b/project/output.sim/sim_1/behav/xsim/output_cycles.txt'
vec=root/'output_ack_a/ack.vec'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
epochs=[];cur=None;peak=0
for line in trace.read_text().splitlines():
 v=line.split();assert len(v)==73
 c=int(v[0]);reset=int(v[1])
 if reset:cur=None;continue
 start=int(v[58]);ready=int(v[59]);wv=int(v[60],16);wr=int(v[61],16);av=int(v[66],16);ar=int(v[67],16);done=int(v[68]);occ=int(v[70])
 assert occ<=16;peak=max(peak,occ)
 if reset:cur=None;continue
 if start and ready:
  assert cur is None
  cur={'start':c,'first_write_valid':None,'last_ACK':None,'done_visible':None,'writes':0,'ACKs':0}
 if cur:
  if wv and cur['first_write_valid'] is None:cur['first_write_valid']=c
  cur['writes']+=(wv&wr).bit_count();cur['ACKs']+=(av&ar).bit_count()
  if av&ar:cur['last_ACK']=c
  if done:
   cur['done_visible']=c
   assert cur['first_write_valid']==cur['start']+3
   assert cur['done_visible']==cur['last_ACK']+2
   assert cur['writes']==cur['ACKs']==31
   epochs.append(cur);cur=None
assert len(epochs)==2 and peak==16
cursor=0;holders=[None,None];accepted=retired=blocked=0;source_next=[0]*32;source_seen=[0]*32
for c,line in enumerate(vec.read_text().splitlines()):
 iv,words,r,ir,ov,outs=[int(x,16) for x in line.split()]
 inputs=[(words>>(64*i))&((1<<64)-1) if iv>>i&1 else None for i in range(32)]
 assert ov==sum(1<<k for k,x in enumerate(holders) if x is not None)
 for k,x in enumerate(holders):
  if x is not None:assert x==(outs>>(64*k))&((1<<64)-1)
 old=holders.copy();chosen=[];begin=cursor
 for k in range(2):
  if old[k] is None or r>>k&1:
   found=next((i for i in [(begin+d)%32 for d in range(32)] if inputs[i] is not None and i not in chosen),None)
   holders[k]=inputs[found] if found is not None else None
   if found is not None:chosen.append(found);begin=(found+1)%32
 assert ir==sum(1<<i for i in chosen) and len(chosen)<=2
 for i in chosen:
  assert inputs[i]==0xa5a5000000000000|(i<<16)|source_next[i]
  source_next[i]+=1;accepted+=1
 for k,x in enumerate(old):
  if x is not None and r>>k&1:
   i=(x>>16)&31;assert (x&65535)==source_seen[i];source_seen[i]+=1;retired+=1
 if chosen:cursor=begin
 if ov==3 and r==0:blocked+=1
assert accepted==retired==384 and holders==[None,None] and blocked==44
logs=[root/'output_b/project/output.sim/sim_1/behav/xsim/simulate.log',root/'output_ack_a/project/ack.sim/sim_1/behav/xsim/simulate.log']
for p in logs:assert 'TEST_PASS' in p.read_text() and 'Fatal' not in p.read_text()
result={'status':'PASS_EXISTING_RTL_BOUNDARIES_AND_INDEPENDENT_RR_AUDIT','scope':'read-only trace/vector/log audit, no new simulation; ACK vectors checked against independent Python policy and existing RTL comparison log','epochs':epochs,'packing_peak':peak,'ACK_sources':32,'ACK_holders':2,'ACK_cycles':c+1,'ACK_accepted':accepted,'ACK_retired':retired,'both_holders_blocked':blocked,'sha256':{str(p):sha(p) for p in [trace,vec]+logs}}
out=root/'review/output_boundary_ack_audit.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='sha256'},indent=2))

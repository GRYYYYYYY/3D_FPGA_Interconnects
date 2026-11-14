#!/usr/bin/env python3
"""Replay canonical scheduling solely from boundary accepts/responses/readiness.
Compare actual internal observable stage grants; never use them to advance state.
"""
import csv,json,sys,collections
from pathlib import Path
class Canonical:
 def __init__(self):
  self.records=[None]*8;self.gen=[0]*8;self.cursors=[0]*4;self.req=None;self.pub=None;self.cap=None;self.n=0;self.accepts=0;self.retires=0;self.changed=0;self.peak=0;self.last=None;self.retire_events=[]
 def tick(self,row):
  c=int(row['cycle']);b=int(row['bank']);integer=lambda k:int(row[k],16)
  def eq(k,v):assert integer(k)==v,(c,b,k,integer(k),v)
  if self.last is not None:assert c==self.last+1,(c,self.last)
  self.last=c
  R=self.records
  def select(states,cur):
   return next((i for d in range(8) if R[i:=(cur+d)%8] and R[i]['s'] in states),None)
  req=select((2,5),self.cursors[0]);apply=select((4,),self.cursors[1]);pv=select((7,),self.cursors[2]);pub=select((8,),self.cursors[3])
  eq('mv',int(self.req is not None));eq('ov',int(self.pub is not None));eq('rr',1)
  for name,slot in [('apply',apply),('pv',pv),('pub',pub)]:
   eq(name,int(slot is not None))
   if slot is not None:eq(name+'_slot',slot)
  eq('cap',int(self.cap is not None))
  if self.cap is not None:eq('cap_slot',self.cap)
  if self.pub is not None:eq('outslot',self.pub)
  if self.req is not None:
   slot,write,tag,line=self.req;eq('mw',write);eq('mid',tag);eq('ml',line)
  free=next((i for i,r in enumerate(R) if r is None),None)
  node=integer('node') if integer('iv') else None
  if node is not None:
   hazard=any(r and r['node']>>8==node>>8 for r in R)
   eq('ir',int(free is not None and not hazard))
  accepted=bool(integer('iv') and integer('ir'))
  retire=self.pub is not None and integer('ordy')
  fill_req=(self.req is None or integer('mr')) and req is not None
  fill_pub=(self.pub is None or integer('ordy')) and pub is not None
  self.peak=max(self.peak,sum(r is not None for r in R))
  if accepted:
   assert R[free] is None
   self.gen[free]=(self.gen[free]+1)%256
   R[free]={'s':1,'node':node,'op':integer('op'),'pair':integer('pair'),'line':integer('line'),'arg':integer('arg')};self.accepts+=1
  previous_cap=self.cap;self.cap=free if accepted else None
  if previous_cap is not None:R[previous_cap]['s']=2
  if self.req is None or integer('mr'):
   self.req=None
   if fill_req:
    write=int(R[req]['s']==5);self.req=(req,write,self.gen[req]*8+req,R[req]['node']>>2)
    R[req]['s']=6 if write else 3;self.cursors[0]=(req+1)%8
  if integer('rv') and integer('rr'):
   tag=integer('rid');slot=tag%8;assert tag//8==self.gen[slot] and R[slot]['s'] in (3,6)
   if R[slot]['s']==3:R[slot]['label']=integer('rd');R[slot]['s']=4
   else:R[slot]['s']=7
  if apply is not None:
   r=R[apply];old=r['label'];sector=r['node']%4;oldpair=(old>>(64*sector))&((1<<64)-1);op=r['op']
   changed=(r['pair']<oldpair) if op==3 else oldpair!=0 if op==5 else any(((r['line']>>(64*i))&((1<<64)-1))<((old>>(64*i))&((1<<64)-1)) for i in range(4)) if op==7 else False
   r['s']=5 if changed else 7;self.changed+=changed;self.cursors[1]=(apply+1)%8
  if pv is not None:R[pv]['s']=8;self.cursors[2]=(pv+1)%8
  oldpub=self.pub
  if self.pub is None or integer('ordy'):
   self.pub=pub if fill_pub else None
   if fill_pub:R[pub]['s']=9;self.cursors[3]=(pub+1)%8
  if retire:
   self.retire_events.append({'bank':b,'line':R[oldpub]['node']>>2,'cycle':c});R[oldpub]=None;self.retires+=1
  self.n+=1
models=[Canonical(),Canonical()]
for row in csv.DictReader(Path(sys.argv[1]).open()):models[int(row['bank'])].tick(row)
for m in models:assert m.accepts==m.retires==1024 and not any(m.records) and m.req is None and m.pub is None
ack_proof=None
if len(sys.argv)>2:
 expected=sorted((int(r['bank']),int(r['line']),int(r['retire'])+1) for r in csv.DictReader(Path(sys.argv[2]).open()))
 actual=sorted((r['bank'],r['line'],r['cycle']) for m in models for r in m.retire_events)
 assert expected==actual,'word release must follow actual consumer by exactly one ACK edge'
 ack_proof={'events':len(actual),'actual_core_release_after_external_result_consumption_edges':1}
print(json.dumps({'deferred_ack_proof':ack_proof,'status':'PASS','scope':'exact K8 slot/PV capture/request/apply/PVwrite/publication arbitration inside real parent context; boundary memory/ready supplied, no full-network qualification','banks':[{'cycles':m.n,'accepted':m.accepts,'retired':m.retires,'changed_writes':m.changed,'peak_K':m.peak} for m in models]},indent=2))

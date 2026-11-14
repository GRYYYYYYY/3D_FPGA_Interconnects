"""Executable finite four-client shared-port contract; exact edge-by-edge replay.

Boundary inputs are observed valid payloads and ready/physical responses. All
DUT ready, arbitration, registered issue/tag and response outputs are predicted.
No internal queue/count signal is used to advance the model.
"""
from pathlib import Path
from collections import deque
import csv,json,sys
MASK=(1<<256)-1
class Port:
 def __init__(self,cursor=0):
  self.q=[deque() for _ in range(4)];self.busy={};self.req=None;self.back=deque();self.client=[None]*4;self.cursor=cursor;self.n=0;self.peak=[0,0,0]
 def check(self,d):
  c=d['cycle'];cv=d['cv'];rr=d['rr'];mr=d['mr'];sv=d['sv'];tag=d['stag'];row=lambda field: d[field]
  def equal(field,value):
   if row(field)!=value:raise AssertionError(f'cycle{c} {field}: RTL={row(field):x},model={value:x}')
  cr=sum((len(self.q[k])<4 and ((d['cl']>>(32*k))&31)==0)<<k for k in range(4))&cv
  equal('cr',cr);equal('cursor',self.cursor);equal('sr',int(len(self.back)<4));equal('mv',int(self.req is not None))
  if self.req:
   w,l,local,data,tag_out=self.req;equal('mw',w);equal('ml',l);equal('mtag',tag_out);equal('md',data)
  rv=sum((x is not None)<<i for i,x in enumerate(self.client));equal('rv',rv)
  for k,v in enumerate(self.client):
   if v:equal_value=[(d['rid']>>(11*k))&2047,(d['rd']>>(256*k))&MASK];assert equal_value==list(v),(c,k,equal_value,v)
  chosen=next((k for j in range(4) if self.q[k:=(self.cursor+j)&3]),None)
  free=next((i for i in range(32) if i not in self.busy),None)
  fill=(self.req is None or mr) and chosen is not None and free is not None
  pop=bool(self.back and (self.client[self.back[0][0]] is None or (rr>>self.back[0][0])&1))
  push=bool(sv and len(self.back)<4)
  delivered=self.back[0] if pop else None
  accepted_return=(self.busy[tag],d['sd']) if push else None
  if push:assert tag in self.busy
  if self.req is None or mr:
   self.req=None
   if fill:
    w,l,local,data=self.q[chosen].popleft();self.req=(w,l,local,data,free);self.busy[free]=(chosen,local);self.cursor=(chosen+1)&3
  for k in range(4):
   if (cv&cr)&(1<<k):
    self.q[k].append(((d['cw']>>k)&1,(d['cl']>>(32*k))&0xffffffff,(d['cid']>>(11*k))&2047,(d['cd']>>(256*k))&MASK))
   if self.client[k] is not None and (rr>>k)&1:self.client[k]=None
  if delivered:
   k,local,data=self.back.popleft();self.client[k]=(local,data)
  if accepted_return:
   (k,local),data=accepted_return;del self.busy[tag];self.back.append((k,local,data))
  assert max(map(len,self.q))<=4 and len(self.back)<=4 and len(self.busy)<=32
  self.peak=[max(self.peak[0],len(self.busy)),max(self.peak[1],len(self.back)),max(self.peak[2],max(map(len,self.q)))];self.n+=1

def main():
 root=Path(sys.argv[1]);rows=[]
 for p in sorted(root.glob('calibration_*.csv')):
  model=None;first=None;last=None
  for row in csv.DictReader(p.open()):
   d={k:int(v,10 if k=='cycle' else 16) for k,v in row.items()}
   if model is None:model=Port(d['cursor']);first=d['cycle']
   if last is not None:assert d['cycle']==last+1
   model.check(d);last=d['cycle']
  assert model and model.n>1000
  rows.append({'trace':str(p),'cycles':model.n,'first':first,'last':last,'all_ready_issue_tag_payload_return_outputs_exact':True,'peak_credit_returnQ_clientQ':model.peak})
 (root/'port_cycle_replay.json').write_text(json.dumps({'all_pass':True,'scope':'exact shared arbiter cycle replay; not complete-kernel model calibration','cases':rows},indent=2)+'\n')
 print('PORT_CYCLE_REPLAY_PASS',[(x['cycles'],x['peak_credit_returnQ_clientQ']) for x in rows])
if __name__=='__main__':main()

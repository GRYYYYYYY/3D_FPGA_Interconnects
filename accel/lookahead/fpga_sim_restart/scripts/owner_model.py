#!/usr/bin/env python3
"""Finite cycle model of ONE owner and the declared stress memory server.
Not a full graph model. Stimulus drives functionality; RTL logs are not inputs.
"""
from collections import deque
import pathlib,json,sys,hashlib
INF=0x7f8000007f800000
class Model:
 def __init__(self,folder,latency,write_latency,bits=0,n=2048):
  self.folder=pathlib.Path(folder);self.lat=latency;self.wlat=write_latency;self.bits=bits
  self.memory=[[INF]*4 for _ in range(n)]
  p=self.folder/'initial.hex'
  if p.exists():self.memory=[[int(l,16)>>(64*s)&((1<<64)-1) for s in range(4)] for l in p.read_text().splitlines()]
  self.expected=[int(l,16) for l in (self.folder/'expected.hex').read_text().splitlines()]
  self.pending=[None]*64;self.rsp=None;self.link=0;self.bank=[0]*16;self.lastdir=0;self.lastservice=-1000
  self.cycle=0;self.rows=[];self.transactions=[];self.reset()
 def reset(self):
  assert not any(self.pending) and self.rsp is None
  self.q=deque();self.rq=deque();self.cache=[None]*128;self.rr=[0]*32
  self.m=[None]*32;self.d=[None]*16;self.cmd=None;self.init=132;self.draining=False;self.scan=None
  self.accepted=self.retired=self.hits=self.merges=self.reads=self.writes=0
 def tick(self,req=None,fence=False):
  c=self.cycle;oldcmd=self.cmd;oldrsp=self.rsp;oldq=self.q[0] if self.q else None;oldrq=self.rq[0] if self.rq else None
  ready=len(self.q)<64 and not self.init and not self.draining and not fence
  accept=req is not None and ready;done=False
  # Freeze combinational choices from old state before any register writes.
  sm=next((i for i,x in enumerate(self.m) if x is not None and not x['sent']),None)
  sd=next((i for i,x in enumerate(self.d) if x is not None and not x['sent']),None)
  fm=next((i for i,x in enumerate(self.m) if x is None),None)
  fd=next((i for i,x in enumerate(self.d) if x is None),None)
  nq=len(self.q);nr=len(self.rq)
  memready=False
  fs=next((i for i,x in enumerate(self.pending) if x is None),None)
  if oldcmd is not None:
   wr,line,data,ident=oldcmd;b=(line//32)%16
   memready=fs is not None and c>=self.link and c>=self.bank[b] and (wr==self.lastdir or c-self.lastservice>=4) and c%19!=0
   if memready:
    self.transactions.append(dict(cycle=c,event='request',write=wr,line=line,id=ident))
    assert not any(x and x['line']==line and (x['wr'] or wr) for x in self.pending)
    self.pending[fs]=dict(wr=wr,line=line,data=data[:] if wr else self.memory[line][:],id=ident,due=c+(self.wlat if wr else self.lat)+line%7)
    self.bank[b]=c+8;self.link=c+2;self.lastdir=wr;self.lastservice=c
    self.cmd=None
    if wr:self.writes+=1
    else:self.reads+=1
  # The external server keeps a response stable until the 64-entry FIFO accepts it.
  rspaccept=oldrsp is not None and nr<64
  if rspaccept:
   idx,p=oldrsp
   self.transactions.append(dict(cycle=c,event='response',write=p['wr'],line=p['line'],id=p['id']))
   if p['wr']:self.memory[p['line']]=p['data'][:]
   self.pending[idx]=None;self.rsp=None
  if oldrsp is None and c%13!=0:
   choice=None
   for i,p in enumerate(self.pending):
    if p and p['due']<=c:choice=(i,p)
   if choice is not None:self.rsp=choice
  # One memory command register, shared read/write port, immutable while stalled.
  if not self.init and oldcmd is None:
   if sd is not None:
    x=self.d[sd];self.cmd=(True,x['line'],x['data'][:],32+sd);x['sent']=True
   elif sm is not None:
    x=self.m[sm];self.cmd=(False,x['line'],[0]*4,sm);x['sent']=True
  if self.init:self.init-=1
  elif oldrq is not None:
   self.rq.popleft();ident,data=oldrq
   if ident>=32:
    assert self.d[ident-32] is not None;self.d[ident-32]=None
   else:
    x=self.m[ident];assert x is not None
    merged=[min(a,b) for a,b in zip(x['acc'],data)]
    self.cache[x['slot']]=dict(line=x['line'],data=merged,dirty=merged!=data,locked=False)
    self.m[ident]=None
  elif self.scan is not None:
   if self.scan<128:
    e=self.cache[self.scan]
    if e is None or not e['dirty'] or fd is not None:
     if e and e['dirty']:self.d[fd]=dict(line=e['line'],data=e['data'][:],sent=False)
     self.cache[self.scan]=None;self.scan+=1
   elif not any(self.d) and oldcmd is None and nr==0:
    done=True;self.scan=None;self.draining=False
  elif oldq is not None:
   line,sector,pair=oldq;s=(line>>self.bits)%32
   mm=next((i for i,x in enumerate(self.m) if x is not None and x['line']==line),None)
   hit=next((w*32+s for w in range(4) if self.cache[w*32+s] is not None and not self.cache[w*32+s]['locked'] and self.cache[w*32+s]['line']==line),None)
   v=next((w*32+s for w in range(4) if self.cache[w*32+s] is None),None)
   if v is None:
    z=self.rr[s]*32+s
    if not self.cache[z]['locked']:v=z
   raw=any(x and x['line']==line for x in self.d)
   feasible=not raw and (mm is not None or hit is not None or (fm is not None and v is not None and (not self.cache[v] or not self.cache[v]['dirty'] or fd is not None)))
   if feasible:
    self.q.popleft();self.retired+=1
    if mm is not None:self.m[mm]['acc'][sector]=min(self.m[mm]['acc'][sector],pair);self.merges+=1
    elif hit is not None:
     e=self.cache[hit];old=e['data'][sector];e['data'][sector]=min(old,pair);e['dirty']|=old!=e['data'][sector];self.hits+=1
    else:
     e=self.cache[v]
     if e and e['dirty']:self.d[fd]=dict(line=e['line'],data=e['data'][:],sent=False)
     a=[INF]*4;a[sector]=pair
     self.m[fm]=dict(line=line,acc=a,slot=v,sent=False)
     self.cache[v]=dict(line=line,data=[INF]*4,dirty=False,locked=True);self.rr[s]=(v//32+1)%4
  elif self.draining and not any(self.m) and oldcmd is None:self.scan=0
  if fence and not self.init:self.draining=True
  if accept:self.q.append(req);self.accepted+=1
  if rspaccept:self.rq.append((oldrsp[1]['id'],oldrsp[1]['data'][:]))
  self.cycle+=1
  if self.cycle>1000000:raise RuntimeError('watchdog')
  return accept,done
 def run(self):
  phase=0
  for row in (self.folder/'stimulus.txt').read_text().splitlines():
   op,l,s,p=row.split();op=int(op)
   if op==0:
    req=(int(l,16),int(s,16),int(p,16))
    while not self.tick(req)[0]:pass
   elif op==1:
    self.tick();self.tick(fence=True)
    while not self.tick()[1]:pass
    assert not any(self.pending) and self.rsp is None and not self.q and self.accepted==self.retired
    observed=[sum(v<<(64*s) for s,v in enumerate(a)) for a in self.memory]
    expected=self.expected[phase*len(self.memory):(phase+1)*len(self.memory)]
    assert observed==expected,'full memory mismatch'
    self.rows.append(dict(phase=phase,cycle=self.cycle,accepted=self.accepted,retired=self.retired,hits=self.hits,merges=self.merges,reads32B=self.reads,writes32B=self.writes,output_equal=True));phase+=1
   elif op==2:self.reset()
   else:raise ValueError(op)
  result=dict(classification='one_owner_cycle_model; not closed_loop_graph',parameters=dict(read_cycles=self.lat,write_cycles=self.wlat,owner_bits=self.bits,request_fifo=64,response_fifo=64,mshr=32,dirty=16),phases=self.rows)
  result['configuration']={'owner_modules':1,'address_owner_count':1<<self.bits,'edge_pair_generator_implemented':False,'cache_sets':32,'cache_ways':4,'line_bytes':32,'replacement':'RR; lowest invalid way first','request_FIFO':64,'response_FIFO':64,'MSHR':32,'dirty_buffer':16,'memory_channels_in_this_test':1,'memory_outstanding':64,'link_gap_cycles':2,'bank_reissue_cycles':8,'banks':16,'turnaround_cycles':4,'read_cycles':self.lat,'write_cycles':self.wlat,'response_stall_modulus':13,'request_stall_modulus':19}
  result['configuration_sha256']=hashlib.sha256(json.dumps(result['configuration'],sort_keys=True).encode()).hexdigest()
  (self.folder/'model_transactions.json').write_text(json.dumps(self.transactions)+'\n')
  (self.folder/'model.json').write_text(json.dumps(result,indent=2)+'\n');print(self.folder.name,self.rows)
if __name__=='__main__':Model(sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4]) if len(sys.argv)>4 else 0,int(sys.argv[5]) if len(sys.argv)>5 else 2048).run()

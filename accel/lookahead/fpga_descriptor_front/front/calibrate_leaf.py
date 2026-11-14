"""Clock-step state machines driven ONLY by interface stimulus, checked each edge.
Composition: descriptor model uses observed E-ready; edge model independently proves
that E-ready plus every allocation/request/return/FP32 output for the same trace.
No observed internal selector/state is used as the expected model state.
"""
from pathlib import Path
import sys,struct,json,hashlib,copy
R=Path(sys.argv[1]);L=int(sys.argv[2]);SIM=R/'project/df_leaf.sim/sim_1/behav/xsim'
def fp(x):return struct.unpack('<f',struct.pack('<I',x))[0]
def bits(x):return struct.unpack('<I',struct.pack('<f',x))[0]
def add(a,b):return bits(fp(a>>32)+fp(b>>32))<<32|bits(fp(a&0xffffffff)+fp(b&0xffffffff))
def num(x,base=10):return int(x.lower().replace('x','0').replace('z','0'),base)
# Pure descriptor state and two held branch selectors.
T=2*L;t=[dict(s=0,g=0) for _ in range(T)];eh=th=None;q=None;rq=eq=tq=0;counts=[0]*4;countpeak=0
for raw in (SIM/'token_cycles.txt').read_text().splitlines():
 x=raw.split();c=int(x[0]);av,ar=map(int,x[1:3]);at=num(x[3],16);pv,pr=map(int,x[4:6]);pt,pn,pp=map(lambda z:num(z,16),x[6:9]);stale,mode=map(int,x[9:11]);ep=num(x[11],16);dv,dr=map(int,x[12:14]);da,dt=map(lambda z:num(z,16),x[14:16]);rv,rr=map(int,x[16:18]);rt,rd=map(lambda z:num(z,16),x[18:20]);yv,yr=map(int,x[20:22]);yc,yp,yt=map(lambda z:num(z,16),x[22:25]);ev,er=map(int,x[25:27]);en,epa,eb,ee,eep=map(lambda z:num(z,16),x[27:32]);observedcounts=list(map(int,x[32:36]))
 alloc=next((i for i,d in enumerate(t) if d['s']==0),None);req=next(((rq+k)%T for k in range(T) if t[(rq+k)%T]['s']==2),None);dec=next((i for i,d in enumerate(t) if d['s']==4),None)
 ec=next(((eq+k)%T for k in range(T) if t[(eq+k)%T]['s']==5 and not t[(eq+k)%T]['ed'] and (eq+k)%T!=eh),None)
 tc=next(((tq+k)%T for k in range(T) if t[(tq+k)%T]['s']==5 and not t[(tq+k)%T]['td'] and (tq+k)%T!=th),None)
 retire=next((i for i,d in enumerate(t) if d['s']==5 and d['ed'] and d['td']),None)
 assert ar==(alloc is not None) and at==(0 if alloc is None else (((t[alloc]['g']+1)&255)<<8|alloc)),(c,'reserve')
 assert pr==(pt&255<T and t[pt&255]['s']==1 and t[pt&255]['g']==pt>>8),(c,'popready')
 assert rr==(rt&255<T and t[rt&255]['s']==3 and t[rt&255]['g']==rt>>8),(c,'returnready')
 assert dv==(q is not None),(c,'requestvalid')
 if dv:assert (da,dt)==q,(c,'requestpayload')
 assert ev==(eh is not None),(c,'Evalid')
 if ev:
  d=t[eh];assert (en,epa,eb,ee,eep)==(d['n'],d['p'],d['begin'],d['end'],d['ep']),(c,'E payload')
 assert yv==(th is not None and t[th]['valid']),(c,'targetvalid')
 if yv:assert (yc,yp,yt)==(t[th]['cell'],t[th]['p'],t[th]['g']<<8|th),(c,'targetpayload')
 assert observedcounts==counts,(c,'counts',observedcounts,counts)
 old=copy.deepcopy(t);old_eh,old_th=eh,th
 if eh is None or ev and er:eh=ec
 if th is None or not old[th]['valid'] or yr:th=tc
 if av and ar:t[alloc].update(s=1,g=(old[alloc]['g']+1)&255);counts[0]+=1
 if pv and pr:
  i=pt&255
  if stale:t[i]['s']=0;counts[1]+=1
  else:t[i].update(s=2,n=pn,p=pp,ep=ep,mode=mode,ed=False,td=False)
 if dv and dr:q=None;counts[2]+=1
 if (not dv or dr) and req is not None:
  d=old[req];q=(d['n']//(2 if d['mode'] else 4),d['g']<<8|req);t[req]['s']=3;rq=(req+1)%T
 if rv and rr:
  i=rt&255;d=old[i];shift=(d['n']%(2 if d['mode'] else 4))*(128 if d['mode'] else 64);t[i].update(s=4,raw=(rd>>shift)&((1<<128)-1))
 if dec is not None:
  d=old[dec];w=d['raw'];b=w&0xffffffff;end=((w>>32)&0xffffffff) if d['mode'] else b+((w>>32)&65535);cell=((w>>64)&0xffffffff) if d['mode'] else ((w>>48)&32767);valid=bool((w>>(96 if d['mode'] else 63))&1)
  assert b<=end<=0xffffffff and (not valid or cell<8)
  t[dec].update(s=5,begin=b,end=end,cell=cell,valid=valid)
 if ev and er:t[old_eh]['ed']=True;eq=(old_eh+1)%T
 if old_th is not None and (not old[old_th]['valid'] or yr):t[old_th]['td']=True;tq=(old_th+1)%T;counts[3]+=int(old[old_th]['valid'])
 if retire is not None:t[retire]['s']=0;counts[1]+=1
 countpeak=max(countpeak,sum(d['s']!=0 for d in t))
assert counts==[128,128,120,80] and all(d['s']==0 for d in t)
token_result={'cycles':c,'counts':counts,'token_peak':countpeak,'all_request_return_target_and_E_handoffs_cycle_exact':True}
# Edge/E/slot scheduler and six-register elastic pair datapaths.
cost=[int(x,16) for x in (R/'cost.hex').read_text().split()];desc=[dict(live=False,inflight=False,gen=0) for _ in range(L*4)];slots=[dict(state=0) for _ in range(L*8)];pipe=[[None]*6 for _ in range(L)];consume=[0]*L;held=[None]*L;ap=rp=0;q=None;accepted=emitted=retired=nr=ns=0;issue={};lat=[];peak=0;queue_events={"empty_enqueue":0,"one_pop_enqueue":0,"many_pop_enqueue":0,"pop_only":0}
for raw in (SIM/'edge_cycles.txt').read_text().splitlines():
 x=raw.split();c=int(x[0]);pv,pr=map(int,x[1:3]);node,pp,begin,end,ep=[num(z,16) for z in x[3:8]];mr,mv=map(int,x[8:10]);ml,mt=map(lambda z:num(z,16),x[10:12]);rv,rr=map(int,x[12:14]);rt,rd=map(lambda z:num(z,16),x[14:16]);oready,ov,od,op=map(lambda z:num(z,16),x[16:20]);av=int(x[20]);ac=num(x[21],16);ot=num(x[22],16)
 alloc=next((((ap+k)%L)*4+j for k in range(L) for j in range(4) if not desc[((ap+k)%L)*4+j]['live']),None)
 expectedpr=begin<=end<=0xffffffff and (begin==end or alloc is not None)
 assert (pr,av,ac)==(expectedpr,pv and expectedpr and begin<end,255 if alloc is None else alloc),(c,'Eallocation')
 assert mv==(q is not None),(c,'EDGE valid')
 if mv:assert (ml,mt)==q,(c,'EDGE payload')
 exprr=rv and rt&255<L*8 and slots[rt&255]['state']==1 and slots[rt&255]['gen']==rt>>8
 assert rr==bool(exprr),(c,'EDGE return')
 assert ov==sum((p[5] is not None)<<l for l,p in enumerate(pipe)),(c,'FPvalid')
 ready=[];candidates=[]
 for l,p in enumerate(pipe):
  if p[5] is not None:
   assert ((od>>(l*32))&0xffffffff,(op>>(l*64))&0xffffffffffffffff,(ot>>(l*32))&0xffffffff)==p[5],(c,l,'FPvalue')
   if oready>>l&1:retired+=1
  r=[False]*6;r[5]=p[5] is None or bool(oready>>l&1)
  for k in range(4,-1,-1):r[k]=p[k] is None or r[k+1]
  ready.append(r);found=held[l]
  if found is None:
   for k in range(4):
    i=l*4+(consume[l]+k)%4;d=desc[i]
    if not d['live']:continue
    s=next((s for s in range(l*8,l*8+8) if slots[s]['state']==2 and slots[s]['context']==i and slots[s]['beat']==d['pos']//8),None)
    if s is not None:found=(i,s);break
  candidates.append(found)
 request=None
 for k in range(L):
  l=(rp+k)%L
  i=next((l*4+j for j in range(4) if desc[l*4+j]['live'] and not desc[l*4+j]['inflight'] and desc[l*4+j]['next']<=(desc[l*4+j]['end']-1)//8),None)
  s=next((s for s in range(l*8,l*8+8) if slots[s]['state']==0),None)
  if i is not None and s is not None:request=(i,s,desc[i]['next']);break
 # Count linked-slot corner cases using independent physical slot ownership.
 push_i=request[0] if request is not None and (not mv or mr) else None
 for i,d in enumerate(desc):
  queued=sum(z['state']!=0 and z.get('context')==i for z in slots)
  found=candidates[i//4];pop=bool(found is not None and found[0]==i and ready[i//4][0] and (d['pos']==d['end']-1 or d['pos']%8==7))
  if push_i==i and queued==0:queue_events['empty_enqueue']+=1
  if push_i==i and pop:queue_events['one_pop_enqueue' if queued==1 else 'many_pop_enqueue']+=1
  if push_i!=i and pop:queue_events['pop_only']+=1
 old=copy.deepcopy(desc);olds=copy.deepcopy(slots)
 if pv and pr:
  accepted+=1
  if begin<end:desc[alloc].update(live=True,inflight=False,gen=(old[alloc]['gen']+1)&255,parent=pp,pos=begin,end=end,next=begin//8,epoch=ep);ap=(alloc//4+1)%L
 if mv and mr:assert mt not in issue;issue[mt]=c;nr+=1;q=None
 if (not mv or mr) and request is not None:
  i,s,beat=request;q=(1041696+beat,old[i]['gen']<<8|s);rp=(i//4+1)%L;slots[s]=dict(state=1,context=i,gen=old[i]['gen'],beat=beat);desc[i]['inflight']=True;desc[i]['next']=old[i]['next']+1
 if rv and rr:
  s=rt&255;slots[s]['state']=2;slots[s]['data']=rd;desc[olds[s]['context']]['inflight']=False;ns+=1;lat.append(c-issue.pop(rt))
 for l in range(L):
  prev=pipe[l][:];r=ready[l];found=candidates[l]
  for k in range(5,0,-1):
   if r[k]:pipe[l][k]=prev[k-1]
  if found is not None and not r[0]:held[l]=found
  if r[0]:
   pipe[l][0]=None
   if found is not None:
    i,s=found;d=old[i];w=(olds[s]['data']>>(32*(d['pos']%8)))&0xffffffff;last=d['pos']==d['end']-1;tag=(d['epoch']&255)<<24|d['gen']<<16|s<<8|i<<1|last
    pipe[l][0]=(w&0xfffffff,add(d['parent'],cost[w>>28]),tag);emitted+=1;desc[i]['pos']=d['pos']+1;consume[l]=(i%4+1)%4;held[l]=None
    if last or d['pos']%8==7:slots[s]['state']=0
    if last:desc[i]['live']=False
 peak=max(peak,len(issue))
assert accepted==120 and emitted==retired==1735 and nr==ns==309 and not issue and min(lat)>=16
result={'pass':True,'lanes':L,'token':token_result,'edge':{'cycles':c,'parents':accepted,'candidates':retired,'requests':nr,'returns':ns,'minimum_memory_latency_edges':min(lat),'peak_inflight':peak,'linked_slot_corner_events':queue_events,'all_allocation_request_return_FP32_cycle_exact':True},'scope':'complete descriptor/dual-branch+E/beat+FP32 leaf composition, external memory/target/candidate readiness replayed; excludes global network/POP/directory/outputbank and registercontext qualification','traces_sha256':{n:hashlib.sha256((SIM/n).read_bytes()).hexdigest() for n in ('token_cycles.txt','edge_cycles.txt')}}
(R/'cycle_calibration.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

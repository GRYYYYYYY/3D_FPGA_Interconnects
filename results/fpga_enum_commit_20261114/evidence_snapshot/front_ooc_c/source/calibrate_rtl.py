"""Independent clock-step model, replaying external stimulus and checking DUT outputs."""
from pathlib import Path
import struct,json,hashlib,copy
ROOT=Path(__file__).resolve().parents[4];R=ROOT/'results/fpga_enum_commit_20261114/front_rtl_c';SIM=R/'project/front_group.sim/sim_1/behav/xsim'
def unpack(n):return struct.unpack('<f',struct.pack('<I',n))[0]
def pack(f):return struct.unpack('<I',struct.pack('<f',f))[0]
def add(a,b):return (pack(unpack(a>>32)+unpack(b>>32))<<32)|pack(unpack(a&0xffffffff)+unpack(b&0xffffffff))
def main():
 vectors=json.loads((R/'vectors.json').read_text());cost=vectors['cost'];rows=[]
 for mode,name in enumerate(['first_free','lane_rr']):
  desc=[{'live':False,'inflight':False,'gen':0} for _ in range(32)];slots=[{'state':0} for _ in range(64)];pair=[{'full':False,'ov':False,'dst':0,'out':0} for _ in range(8)];consume=[0]*8;pointer=0;qvalid=False;qline=0;qtag=0;emitted=accepted=retired=physical_req=physical_rsp=0;last_emit=0;allocations=[0]*8;zero=0;issue_t={};latencies=[];max_inflight=0
  lines=(SIM/(name+'_cycles.txt')).read_text().splitlines()
  for line in lines:
   x=line.split();cycle=int(x[0]);pv,actual_pr=map(int,x[1:3]);node,pp,begin,end,ep=[int(v,16) for v in x[3:8]];mr,actual_mv=map(int,x[8:10]);actual_ml,actual_mt=int(x[10],16),int(x[11],16);rv,actual_rr=map(int,x[12:14]);rt,rd=int(x[14],16),int(x[15],16);outready,actual_ov=int(x[16],16),int(x[17],16);actual_av=int(x[20]);actual_ac=int(x[21],16)
   allocation=-1
   for k in range(8):
    lane=(pointer+k)%8 if mode else k
    for j in range(4):
     if not desc[lane*4+j]['live']:
      allocation=lane*4+j;break
    if allocation>=0:break
   pr=begin==end or allocation>=0;av=pv and pr and begin<end
   assert (actual_pr,actual_av,actual_ac)==(pr,av,allocation&255),(mode,cycle,'allocation')
   assert (actual_mv,actual_ml,actual_mt)==(qvalid,qline,qtag),(mode,cycle,'registered request',(actual_mv,actual_ml,actual_mt),(qvalid,qline,qtag))
   rr=rv and rt&255<64 and slots[rt&255]['state']==1 and slots[rt&255]['gen']==rt>>8
   assert actual_rr==bool(rr),(mode,cycle,'return')
   ov=sum(int(p['ov'])<<l for l,p in enumerate(pair));assert ov==actual_ov,(mode,cycle,'pair valid',ov,actual_ov)
   for l,p in enumerate(pair):
    if not p['ov']:continue
    dst=int(x[18][-(l+1)*8:len(x[18])-l*8 or None],16);value=int(x[19][-(l+1)*16:len(x[19])-l*16 or None],16)
    assert (dst,value)==(p['dst'],p['out']),(mode,cycle,l,'pair bits',(dst,value),(p['dst'],p['out']))
    if outready>>l&1:retired+=1;last_emit=cycle
   request=None
   for i,d in enumerate(desc):
    if not d['live'] or d['inflight'] or d['next']>=(d['end']+7)//8:continue
    for s in range(i//4*8,i//4*8+8):
     if slots[s]['state']==0:request=(i,s,d['next']);break
    if request:break
   candidates=[]
   for l in range(8):
    found=None
    for k in range(4):
     i=l*4+(consume[l]+k)%4;d=desc[i]
     if not d['live']:continue
     for s in range(l*8,l*8+8):
      if slots[s]['state']==2 and slots[s]['context']==i and slots[s]['beat']==d['pos']//8:found=(i,s);break
     if found:break
    candidates.append(found)
   # Sequential updates use pre-clock snapshots for all concurrently active paths.
   before=copy.deepcopy(desc);oldslots=copy.deepcopy(slots)
   if pv and pr:
    accepted+=1
    if begin<end:
     d=desc[allocation];d.update(live=True,inflight=False,gen=(d['gen']+1)&255,parent=pp,pos=begin,end=end,next=begin//8,epoch=ep);allocations[allocation//4]+=1
     if mode:pointer=(allocation//4+1)%8
    else:zero+=1
   if qvalid and mr:
    physical_req+=1;assert qtag not in issue_t;issue_t[qtag]=cycle
   if qvalid and mr:qvalid=False
   if (not actual_mv or mr) and request:
    i,s,beat=request;qvalid=True;qline=beat;qtag=(before[i]['gen']<<8)|s;slots[s]={'state':1,'context':i,'gen':before[i]['gen'],'beat':beat};desc[i]['inflight']=True;desc[i]['next']=before[i]['next']+1
   if rv and rr:
    s=rt&255;slots[s]['state']=2;slots[s]['data']=rd;desc[oldslots[s]['context']]['inflight']=False;physical_rsp+=1;latencies.append(cycle-issue_t.pop(rt))
   for l,p in enumerate(pair):
    old=dict(p);advance=not old['ov'] or bool(outready>>l&1);ir=not old['full'] or advance;found=candidates[l]
    if advance:
     p['ov']=old['full']
     if old['full']:p['dst']=old['in_dst'];p['out']=add(old['parent'],old['cost'])
    if ir:
     p['full']=found is not None
     if found:
      i,s=found;d=before[i];descriptor=(oldslots[s]['data']>>(d['pos']%8*32))&0xffffffff;p.update(in_dst=descriptor&0xfffffff,parent=d['parent'],cost=cost[descriptor>>28]);emitted+=1
      desc[i]['pos']=d['pos']+1;consume[l]=(i%4+1)%4
      if d['pos']+1==d['end'] or d['pos']%8==7:slots[s]['state']=0
      if d['pos']+1==d['end']:desc[i]['live']=False
   max_inflight=max(max_inflight,len(issue_t))
  assert accepted==144 and emitted==retired==vectors['candidate_count'] and not issue_t
  assert physical_req==physical_rsp==378 and max_inflight<=32
  assert min(latencies)>=16
  rows.append({'mode':name,'cycles_checked':len(lines),'last_cycle':int(lines[-1].split()[0]),'last_output_retired_cycle':last_emit,'parents':accepted,'zero_degree':zero,'candidates_computed_and_retired':retired,'physical_requests_and_responses':physical_req,'latency_min_cycles':min(latencies),'latency_max_cycles':max(latencies),'physical_credit_peak':max_inflight,'lane_allocations':allocations,'trace_sha256':hashlib.sha256((SIM/(name+'_cycles.txt')).read_bytes()).hexdigest(),'allocation_return_request_FP32_cycle_exact':True})
 log=(SIM/'simulate.log').read_text();assert 'TEST_PASS frontend_group two_epochs=2 parents=144 candidates=2136' in log and 'Fatal:' not in log
 (R/'calibration.json').write_text(json.dumps({'all_pass':True,'rows':rows,'scope':'8 lanes 4contexts/lane 8slots/lane, D1,1header-ready parent/cycle,1registered request stage; one shared tagged physical port, two-stage real pair_lane; headers/meta/pending/route outside','full_kernel_qualified':False,'board_measured':False},indent=2));print(json.dumps(rows,indent=2))
if __name__=='__main__':main()

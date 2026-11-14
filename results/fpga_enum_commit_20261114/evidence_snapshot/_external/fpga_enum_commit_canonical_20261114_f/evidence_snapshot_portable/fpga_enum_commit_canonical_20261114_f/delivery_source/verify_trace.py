"""Independent cycle replay of canonical stages with observed boundary handshakes.

Does not infer batch performance. Consumer-ready and physical memory environment
come from the RTL trace; internal RR selections and registered stage cycles are
predicted from that boundary trace and checked exactly, transaction by transaction.
"""
from pathlib import Path
import collections,json,re,sys
root=Path(__file__).resolve().parents[4]
r=Path(sys.argv[1]) if len(sys.argv)>1 else root/'results/fpga_enum_commit_canonical_20261114_f'
log=r/'project/canonical_k8.sim/sim_1/behav/xsim/simulate.log'
if not log.exists():log=r/'logs/simulate.log'
raw=log.read_text()
assert 'TEST_PASS K8 samples=2 operations=1472' in raw and not re.search(r'(?i)fatal:|error:',raw)
by=collections.defaultdict(lambda:collections.defaultdict(list))
for line in raw.splitlines():
 name=line.split(' ',1)[0]
 if 'cycle=' not in line:continue
 data={k:int(v,16) if k=='mask' else int(v) for k,v in re.findall(r'(\w+)=(\w+)',line)}
 by[data['cycle']][name].append(data)
normal_start={sample:min(c for c,events in by.items() for e in events.get('ACCEPT',[]) if e['sample']==sample) for sample in [0,1]}
vectors=[[int(x,16) for x in (r/f'bank{b}.mem').read_text().splitlines()] for b in range(2)]
changes={};lines=[[int('7f8000007f800000'*4,16)]*64 for _ in range(2)]
for b in range(2):
 for i,v in enumerate(vectors[b]):
  node=(v>>860)&((1<<22)-1);word=node>>8;word=word-12288 if word>=12288 else word
  nl=v&((1<<256)-1);changes[b,i]=nl!=lines[b][word];lines[b][word]=nl
records=[{},{}];reqbuf=[None,None];pubbuf=[None,None];cur_req=[0,0];cur_apply=[0,0];cur_pv=[0,0];cur_pub=[0,0];generations=[[0]*8 for _ in range(2)]
logical_queue=[collections.deque(),collections.deque()];physical={};physical_to_local={};stats=collections.defaultdict(list)
count=collections.Counter();pending_capture=[{},{}]
def select(bank,state,cycle,cursor):
 for d in range(8):
  slot=(cursor+d)&7;rec=records[bank].get(slot)
  if rec is not None and rec['state']==state and rec['ready']<=cycle:return slot
 return None
def one(events,name,b):
 rows=[x for x in events.get(name,[]) if x['bank']==b];assert len(rows)<=1,(name,b,rows)
 return rows[0] if rows else None
for c in range(max(by)+1):
 ev=by[c]
 # Physical request FIFO order and two registered response boundaries.
 for e in ev.get('MEM_ISSUE',[]):
  tag=e['tag'];assert tag not in physical
  line=e['line'];client=((line-4096)>>5)&1 if 4096<=line<4096+(1<<20) else None
  if client is not None and c>=normal_start[e['sample']]:
   assert logical_queue[client],('physical without local request',c,e)
   req=logical_queue[client].popleft();assert req['line']==line and req['write']==e['write'],(c,req,e)
   assert c>=req['cycle']+2
   physical_to_local[tag]=req;stats['local_request_to_physical_issue'].append(c-req['cycle'])
  physical[tag]=c;count['physical_issue']+=1
 for e in ev.get('MEM_RETURN',[]):
  tag=e['tag'];assert tag in physical and c>=physical[tag]+16
  stats['physical_latency'].append(c-physical.pop(tag))
  if tag in physical_to_local:
   req=physical_to_local.pop(tag);req['physical_response_cycle']=c
   # ID can be reused only once the previous record and all returns have retired.
   key=(req['bank'],req['id']);assert key not in pending_capture[req['bank']]
   pending_capture[req['bank']][key]=req
  count['physical_response']+=1
 for b in range(2):
  acc=one(ev,'ACCEPT',b);tx=one(ev,'TX_SLOT',b);cap=one(ev,'PV_READ_CAPTURE',b)
  local=one(ev,'LOCAL_REQUEST',b);rsp=one(ev,'LOCAL_RESPONSE',b);ap=one(ev,'APPLY',b);pv=one(ev,'PV_WRITE',b);pub=one(ev,'RESULT_ENQUEUE',b);ret=one(ev,'RETIRE',b)
  # Snapshot the old state at this edge; all predicted transitions apply after it.
  want_apply=select(b,'APPLY',c,cur_apply[b]);want_pv=select(b,'PV',c,cur_pv[b])
  allow_req=reqbuf[b] is None or local is not None
  want_req=select(b,'RREQ',c,cur_req[b]) if allow_req else None
  if allow_req:
   # READ and WRITE requests share one RR selection, not separate priority classes.
   want_req=None
   for d in range(8):
    slot=(cur_req[b]+d)&7;rec=records[b].get(slot)
    if rec and rec['state'] in ['RREQ','WREQ'] and rec['ready']<=c:want_req=slot;break
  want_pub=select(b,'PUB',c,cur_pub[b]) if pubbuf[b] is None or ret is not None else None
  for name,want,actual in [('APPLY',want_apply,ap),('PV_WRITE',want_pv,pv),('RESULT_ENQUEUE',want_pub,pub)]:
   assert (actual['slot'] if actual else None)==want,(c,b,name,want,actual)
  if acc:
   assert tx and min(set(range(8))-set(records[b]))==tx['slot']
   slot=tx['slot'];generations[b][slot]=(generations[b][slot]+1)&255;assert tx['generation']==generations[b][slot]
   node=acc['node'];assert all(rec['node']>>8!=node>>8 for rec in records[b].values())
   records[b][slot]={'state':'CAP','ready':c+1,'index':acc['index'],'sample':acc['sample'],'node':node,'id':tx['generation']*8+slot,'accept':c};count['accept']+=1
  else:assert tx is None
  expected_caps=[slot for slot,rec in records[b].items() if rec['state']=='CAP' and rec['ready']==c]
  assert ([cap['slot']] if cap else [])==expected_caps,(c,b,'PV capture',expected_caps,cap)
  if cap:
   rec=records[b][cap['slot']];assert c==rec['accept']+1;rec.update(state='RREQ',ready=c+1);count['pv_read_capture']+=1
  # Boundary handshake for the previously registered local request.
  if local:
   assert reqbuf[b] is not None,(c,b,'missing request register')
   slot,write,fillcycle=reqbuf[b];rec=records[b][slot]
   assert local['id']==rec['id'] and local['write']==write and c>=fillcycle+1
   assert local['line']==4096+(rec['node']>>2)
   rec['last_local_request']=c;logical_queue[b].append(local);reqbuf[b]=None;count['local_request']+=1
  if want_req is not None:
   rec=records[b][want_req];write=int(rec['state']=='WREQ');rec['state']='WWAIT' if write else 'RWAIT';reqbuf[b]=(want_req,write,c);cur_req[b]=(want_req+1)&7
  if rsp:
   slot=rsp['id']&7;rec=records[b][slot];assert rec['id']==rsp['id']
   key=(b,rsp['id']);req=pending_capture[b].pop(key);assert req['id']==rsp['id'] and c>=req['physical_response_cycle']+2
   stats['physical_response_to_local_capture'].append(c-req['physical_response_cycle']);stats['local_roundtrip'].append(c-rec['last_local_request'])
   if rec['state']=='RWAIT':rec.update(state='APPLY',ready=c+1)
   else:assert rec['state']=='WWAIT';rec.update(state='PV',ready=c+1)
   count['local_response']+=1
  if ap:
   rec=records[b][want_apply];rec.update(state='WREQ' if changes[b,rec['index']] else 'PV',ready=c+1);cur_apply[b]=(want_apply+1)&7;count['apply']+=1
  if pv:
   rec=records[b][want_pv];rec.update(state='PUB',ready=c+1);rec['pvwrite']=c;cur_pv[b]=(want_pv+1)&7;count['pv_write']+=1
  oldpub=pubbuf[b]
  if ret:
   assert oldpub is not None;rec=records[b][oldpub];assert ret['index']==rec['index'] and ret['sample']==rec['sample'] and c>=rec['pub_enqueue']+1
   stats['accept_to_retire'].append(c-rec['accept']);stats['PV_write_to_retire'].append(c-rec['pvwrite']);records[b].pop(oldpub);pubbuf[b]=None;count['retire']+=1
  if pub:
   rec=records[b][want_pub];rec.update(state='PUBLISH',ready=c+1);rec['pub_enqueue']=c;pubbuf[b]=want_pub;cur_pub[b]=(want_pub+1)&7;count['result_register_enqueue']+=1
assert all(not x for x in records+logical_queue+pending_capture) and not physical and not physical_to_local and reqbuf==[None,None] and pubbuf==[None,None]
assert count['accept']==count['retire']==count['pv_read_capture']==count['apply']==count['pv_write']==count['result_register_enqueue']==1472
assert count['physical_issue']==count['physical_response']==1988 and count['local_request']==count['local_response']
summary={'all_pass':True,'scope':'exact canonical internal RR/stage replay from observed interface handshakes; shared-interface minimum registered latencies and transaction mapping verified; not full integrated model calibration','counts':dict(count),'cycles':max(by),'distributions':{k:{'min':min(v),'max':max(v),'mean':sum(v)/len(v),'histogram':dict(sorted(collections.Counter(v).items()))} for k,v in stats.items()}}
(r/'cycle_replay.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='distributions'},indent=2))

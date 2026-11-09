"""Observe independently synthesized service FIFO handshakes, without modifying DUT."""
import argparse, collections, hashlib, json, os, re, shlex, shutil, statistics, subprocess, signal
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--hls',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--zero-hold',action='store_true');a=p.parse_args();o=a.output.resolve();h=a.hls.resolve();o.mkdir(parents=True,exist_ok=False)
assert json.loads((h/'cosim.json').read_text())['passed']
sim=o/'sim';shutil.copytree(h/'project/solution/sim',sim,ignore=shutil.ignore_patterns('*.wdb','xsim.dir','*.log','*.jou'));v=sim/'verilog';top='lookahead_services51'
for f in (sim/'tv/rtldatafile').glob('*'):f.unlink()
rtl=(v/(top+'.v')).read_text();inst=re.search(r'lookahead_services51_network\s+(\w+)\s*\(',rtl)[1];path='`AUTOTB_DUT_INST.'+inst
channels={}
for s in range(2):channels['h'+str(s)]=('commit_U0','heap_'+str(s)+'_U0');channels['r'+str(s)]=('heap_'+str(s)+'_U0','commit_U0');channels['c'+str(s)]=('edge_U0','commit_U0')
channels.update(er=('commit_U0','edge_U0'),mr=('commit_U0','map_service_U0'),ma=('map_service_U0','commit_U0'))
lines=['integer obs_fd,obs_clk=0,obs_tx=0,obs_live=0;', 'initial obs_fd=$fopen("events.csv","w");','always @(posedge AESL_clock) if(!AESL_reset)begin','obs_clk=obs_clk+1;','if(!obs_live && ap_start)begin obs_live=1;$fwrite(obs_fd,"%0d,%0d,begin,-,0\\n",obs_tx,obs_clk);end','if(obs_live)begin']
for ch,(wr,rd) in channels.items():
 for event,cond,data in [('enqueue',f'{wr}_{ch}_write && {ch}_full_n',f'{wr}_{ch}_din'),('accept',f'{rd}_{ch}_read && {ch}_empty_n',f'{ch}_dout')]:
  cond=' && '.join(path+'.'+q for q in cond.split(' && '));lines.append(f'if({cond})$fwrite(obs_fd,"%0d,%0d,{event},{ch},%h\\n",obs_tx,obs_clk,{path}.{data});')
 lines.append(f'if(!{path}.{ch}_full_n)$fwrite(obs_fd,"%0d,%0d,full,{ch},0\\n",obs_tx,obs_clk);')
lines+=['if(ap_done)begin $fwrite(obs_fd,"%0d,%0d,done,-,0\\n",obs_tx,obs_clk);$fflush(obs_fd);obs_tx=obs_tx+1;obs_live=0;end','end end']
tb=v/(top+'.autotb.v');txt=tb.read_text();tb.write_text(txt.replace('endmodule','\n'.join(lines)+'\nendmodule'))
if a.zero_hold:
 # Change only scalar testbench stimuli. Same DUT, same expected maps/stats.
 # Hold metrics are intentionally different and excluded from equality below.
 for name in ['heap_hold','map_hold']:
  for f in (sim/'tv/cdatafile').glob('*autotvin_'+name+'.dat'):
   f.write_text(re.sub(r'0x[0-9a-fA-F]+','0x00000000',f.read_text()))
tcl=v/(top+'.tcl');tcl.write_text('\n'.join(l for l in tcl.read_text().splitlines() if not any(x in l for x in ['log_wave','save_wave_config','add_wave']))+'\n')
run=v/'run_xsim.sh';lines=[]
for line in run.read_text().splitlines():
 args=shlex.split(line)
 for flag in ['-view','-protoinst']:
  if flag in args:i=args.index(flag);del args[i:i+2]
 if '-debug' in args:args[args.index('-debug')+1]='typical'
 lines.append(shlex.join(args))
run.write_text('\n'.join(lines)+'\n');env=os.environ.copy();env['LD_PRELOAD']='/lib/x86_64-linux-gnu/libudev.so.1'
with (o/'simulation.log').open('w') as f:
 proc=subprocess.Popen(['bash','-e','run_xsim.sh'],cwd=v,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
 try:rc=proc.wait(timeout=300)
 except subprocess.TimeoutExpired:
  os.killpg(proc.pid,signal.SIGTERM)
  try:proc.wait(timeout=10)
  except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
  rc=124
# Compare the value tokens (memory testbench formatting is insignificant).
matches={}
for f in (sim/'tv/cdatafile').glob('c.*autotvout_*.dat'):
 g=sim/'tv/rtldatafile'/f.name.replace('c.lookahead','rtl.lookahead');skip=a.zero_hold and any('_'+x in f.name for x in ['hm0','hm1','mm'])
 if not skip:matches[f.name]=g.exists() and f.read_bytes()==g.read_bytes()
events=[]
for line in (v/'events.csv').read_text().splitlines():
 tx,clk,event,ch,bits=line.split(',');x=dict(tx=int(tx),cycle=int(clk),event=event,channel=ch);val=int(bits,16) if not re.search('[xz]',bits) else 0
 x['bits']=bits
 if ch!='-' and event!='full':
  x.update(generation=val&0xffffffff,qid=(val>>32)&0xffffffff,context=(val>>64)&0xffffffff,parent=(val>>96)&0xffffffff,ordinal=(val>>128)&0xffffffff)
  if ch.startswith('c'):x.update(kind='candidate',end=bool(val>>288),node=(val>>160)&0xffffffff)
  elif ch=='ma':x['kind']='map_reply'
  else:x.update(kind=(val>>160)&0xffffffff,node=(val>>192)&0xffffffff)
 events.append(x)
(o/'events.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in events))
def dist(a):return dict(count=len(a),min=min(a) if a else None,max=max(a) if a else None,mean=statistics.mean(a) if a else None)
summary=[]
for tx in sorted({e['tx'] for e in events}):
 es=[e for e in events if e['tx']==tx];fifos={k:collections.deque() for k in channels};active={};ops=[];witness=[];occupancy=collections.Counter();maxocc=collections.Counter();full=collections.Counter();useful=collections.defaultdict(set);start=es[0]['cycle'];end=es[-1]['cycle'];barriers=[];last_ord={};raw_order=True
 for e in es:
  ch=e['channel'];t=e['cycle']
  if e['event']=='full':full[ch]+=1;continue
  if e['event'] not in ['enqueue','accept']:continue
  if e['event']=='enqueue':fifos[ch].append(e);occupancy[ch]+=1;maxocc[ch]=max(maxocc[ch],occupancy[ch]);assert occupancy[ch]<=4
  else:
   assert fifos[ch],(ch,e);original=fifos[ch].popleft();assert original['bits']==e['bits'];occupancy[ch]-=1
  if ch.startswith('h') and e['kind'] in [1,2]:
   if e['event']=='enqueue':
    if e['kind']==2:barriers.append(dict(cycle=t,qid=e['qid'],parent=e['parent'],pending_prior_pushes=sum(z['kind']==1 and z['qid']==e['qid'] and 'feedback' not in z for z in ops)));assert barriers[-1]['pending_prior_pushes']==0
    key=(e['qid'],e['parent']);
    if e['kind']==1 and e['parent']>0:
     if key in last_ord:raw_order &= e['ordinal']>last_ord[key]
     last_ord[key]=e['ordinal']
    ops.append(dict(enqueue=t,kind=e['kind'],qid=e['qid'],parent=e['parent'],ordinal=e['ordinal'],partition=int(ch[1]),bits=e['bits']))
   else:
    z=next(z for z in ops if z['partition']==int(ch[1]) and 'start' not in z);z['start']=t;useful[t].add('heap')
  if ch.startswith('r') and e['kind'] in [1,2]:
   key='retire' if e['event']=='enqueue' else 'feedback';z=next(z for z in ops if z['partition']==int(ch[1]) and key not in z);z[key]=t
   if key=='retire':z['response_bits']=e['bits']
   if key=='retire':useful[t].add('heap')
  if ch.startswith('c') and e['event']=='enqueue' and not e['end']:
   useful[t].add('edge')
   prior=[z for z in ops if z['kind']==1 and z['qid']==e['qid'] and z['parent']==e['parent'] and z['ordinal']<e['ordinal'] and 'start' in z and 'retire' not in z]
   if prior:witness.append(dict(edge=e,push=prior[0].copy()))
  if ch.startswith('c') and e['event']=='accept':useful[t].add('commit')
  if ch in ['mr','ma']:useful[t].add('map')
 assert all(not f for f in fifos.values()),'undrained'
 def gaps(field):
  vals=[]
  for q in [0,1]:
   ts=[z[field] for z in ops if z['partition']==q];vals.extend(y-x for x,y in zip(ts,ts[1:]))
  return dist(vals)
 # Replay the accepted ordered PQ stream to bind latency to actual traversed levels.
 heaps={}
 for z in ops:
  hp=heaps.setdefault(z['qid'],[]);z['heap_size_before']=len(hp);z['down']=0;z['up_compares']=0;z['up_moves']=0
  value=(int(z['bits'],16)>>192)&((1<<96)-1)
  key=lambda w:(w>>32)&0xffffffff
  if z['kind']==1:
   hole=len(hp);hp.append(value)
   while hole:
    z['up_compares']+=1;par=(hole-1)//2
    if key(hp[par])<=key(value):break
    hp[hole]=hp[par];hole=par;z['up_moves']+=1
   hp[hole]=value
  else:
   assert hp;root=hp[0];value=hp.pop();hole=0;child=2
   assert root==((int(z['response_bits'],16)>>192)&((1<<96)-1))
   if hp:
    while child<len(hp):
     if key(hp[child])>key(hp[child-1]):child-=1
     hp[hole]=hp[child];hole=child;child=2*(hole+1);z['down']+=1
    if child==len(hp):hp[hole]=hp[child-1];hole=child-1;z['down']+=1
    while hole:
     z['up_compares']+=1;par=(hole-1)//2
     if key(hp[par])<=key(value):break
     hp[hole]=hp[par];hole=par;z['up_moves']+=1
    hp[hole]=value
 busy_gaps=[];reaccept=[]
 for part in [0,1]:
  stream=[z for z in ops if z['partition']==part]
  for prev,nxt in zip(stream,stream[1:]):
   if nxt['enqueue']<=prev['retire']:
    busy_gaps.append(nxt['start']-prev['start']);reaccept.append(nxt['start']-prev['retire'])
 full_progress=sum(e['event']=='full' and any(k in useful[e['cycle']] for k in ['heap','edge','commit','map']) for e in es)
 summary.append(dict(transaction=tx,operation_start_gap_when_queued=dist(busy_gaps),retire_to_start_when_queued=dist(reaccept),fifo_full_with_other_service_handshakes=full_progress,latency_by_kind={str(k):dict(execute=dist([z['retire']-z['start'] for z in ops if z['kind']==k]),feedback=dist([z['feedback']-z['enqueue'] for z in ops if z['kind']==k])) for k in [1,2]},cycles=end-start+1,ops=len(ops),fifo_enqueue_gap=gaps('enqueue'),pq_operation_start_gap=gaps('start'),operation_retire_gap=gaps('retire'),operation_retire_ops_per_cycle=len(ops)/(end-start+1),full_feedback_latency=dist([z['feedback']-z['enqueue'] for z in ops]),execution_latency=dist([z['retire']-z['start'] for z in ops]),max_fifo_occupancy=dict(maxocc),fifo_full_cycles=dict(full),same_parent_overlap_count=len(witness),same_parent_overlap_witness=witness[:8],simultaneous_useful_handshake_cycles=sum(len(s)>1 for s in useful.values()),ordered_push_ordinals=raw_order,parent_barriers_checked=len(barriers),all_fifos_drained=True,operations=ops))
passed=rc==0 and matches and all(matches.values()) and len(summary)==2
result=dict(passed=bool(passed),scope='synthetic 12-node mechanism, not native batch E1',zero_hold=a.zero_hold,output_matches=matches,transactions=summary,source_binding_sha256=hashlib.sha256((h/'binding.json').read_bytes()).hexdigest(),new_implemented_frequency_hz=None,board_measured=False)
(o/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('observer',bool(passed));raise SystemExit(not passed)

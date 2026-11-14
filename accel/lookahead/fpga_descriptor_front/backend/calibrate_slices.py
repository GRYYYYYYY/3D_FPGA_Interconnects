#!/usr/bin/env python3
"""External-pin cycle replay. State comes only from prior boundary inputs."""
import csv,json,sys
from pathlib import Path
states={};n=0;peaks={};stall={};events={};last={}
for r in csv.DictReader(Path(sys.argv[1]).open()):
 name=r['name'];cycle=int(r['cycle']);kind=int(r['kind']);width=int(r['width'])
 iv,ir,ov,empty=[int(r[k],16) for k in ('iv','ir','ov','empty')]
 # Preserve four-state payload symbols exactly (read-request write-data is don't-care).
 data,out=r['id'].lower(),r['od'].lower()
 ready=int(r['ordy'],16) if ov else 0
 # Independent traced cases start fully drained; skipped sample initialization has no input.
 if name not in states:states[name]=[] if kind==0 else {'phase':0,'payload':0}
 s=states[name]
 if name in last and cycle>last[name]+1:
  assert (not s if kind==0 else s['phase']==0),(name,'gap with live data',s)
 last[name]=cycle
 if kind==0:
  assert ir==(len(s)<2) and ov==bool(s) and empty==(not s),(cycle,name,'controls',r,s)
  if ov:assert out==s[0],(cycle,name,'payload')
  peaks[name]=max(peaks.get(name,0),len(s));pop=ov and ready;push=iv and ir
  if pop:s.pop(0)
  if push:s.append(data)
 else:
  phase=s['phase'];assert ir==(phase==2) and ov==(phase==1) and empty==(phase==0),(cycle,name,'ackcontrols',r,s)
  if ov:assert out==s['payload'],(cycle,name,'ackpayload')
  if phase==0 and iv:s.update(phase=1,payload=data)
  elif phase==1 and ready:s['phase']=2
  elif phase==2:
   assert iv and data==s['payload'],(cycle,name,'upstream must hold through ACK')
   s['phase']=0
  peaks[name]=max(peaks.get(name,0),phase!=0)
 stall[name]=stall.get(name,0)+bool(ov and not ready)
 events[name]=events.get(name,0)+bool(ov and ready);n+=1
for name,s in states.items():assert not s if isinstance(s,list) else s['phase']==0,(name,'not drained',s)
print(json.dumps({'status':'PASS','boundary_rows':n,'peaks':peaks,'stall_cycles':stall,'consumptions':events,'scope':'FIFO2/deferredACK boundary pins; excludes canonical algorithm and full global fabric'},indent=2))

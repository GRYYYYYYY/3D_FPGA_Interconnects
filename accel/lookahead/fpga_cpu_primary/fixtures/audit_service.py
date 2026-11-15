#!/usr/bin/env python3
"""Audit measured physical service and compare native batches across contracts."""
from pathlib import Path
import argparse,collections,csv,hashlib,json

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('run',type=Path);ap.add_argument('--baseline',type=Path);a=ap.parse_args();t=json.loads((a.run/'terminal.json').read_text());assert t['status']=='PASS';cfg=json.loads((a.run/'service_config.json').read_text());binding=json.loads((a.run/'binding.json').read_text());rows=[]
 if a.baseline:
  bt=json.loads((a.baseline/'terminal.json').read_text());assert bt['status']=='PASS';bb=json.loads((a.baseline/'binding.json').read_text());assert bb['source']==binding['source'];assert bb['fixture_manifest_sha256']==binding['fixture_manifest_sha256'];assert bb['service']['period_ps']==cfg['period_ps'];base_rows={(r['case'],r['stress']):r for r in bt['results']if r['negative']=='none'}
 for r in t['results']:
  if r['negative']!='none':continue
  if a.baseline:assert(r['case'],r['stress'])in base_rows
  name=r['case']+'_none'+('_stress'if r['stress']else'');rd=a.run/name;last={};gaps=[];pending={};latencies=[];requests=0;responses=0
  for e in csv.DictReader((rd/'events.csv').open()):
   event=e['event'];cy=int(e['cycle']);port=int(e['source_or_port_or_bank']);tag=int(e['id_or_cookie'],16)
   if event=='physical_issue':
    requests+=1
    if port in last:gaps.append(cy-last[port]);assert cy-last[port]>=cfg['memory_issue_cycles'],f'Physical gap below contract: {e}'
    last[port]=cy;assert(port,tag)not in pending;pending[(port,tag)]=cy
   elif event=='physical_ack':
    responses+=1;born=pending.pop((port,tag));latency=cy-born;assert latency>=cfg['memory_latency_cycles'],f'Physical ACK before contract: {e}';latencies.append(latency)
  assert not pending and requests==responses
  cal=json.loads((rd/'calibration.json').read_text());assert cal['status']=='PASS';samples=list(cal['samples'].values());totals=collections.Counter();phases=collections.Counter()
  for s in samples:totals.update({k:s[k]for k in ['cycles','waves','parents','candidates','commits','op_retired','events','physical_requests','physical_responses']});phases.update(s['phase_cycles'])
  row={'case':r['case'],'stress':r['stress'],'physical_requests':requests,'physical_responses':responses,'observed_issue_gap_min_cycles':min(gaps)if gaps else None,'observed_ack_latency_min_cycles':min(latencies),'observed_ack_latency_max_cycles':max(latencies),'observed_ack_latency_mean_cycles':sum(latencies)/len(latencies),'totals':dict(totals),'phase_cycles':dict(phases),'output_sha256':sha(rd/'output.bin'),'trace_sha256':sha(rd/'events.csv')}
  assert requests==totals['physical_requests']and responses==totals['physical_responses']
  if a.baseline:
   br=a.baseline/name;bc=json.loads((br/'calibration.json').read_text());before=bc['samples'];assert(rd/'output.bin').read_bytes()==(br/'output.bin').read_bytes();pairs=[]
   for s in samples:
    old=before[str(s['sample'])];pairs.append({'sample':s['sample'],'baseline_cycles':old['cycles'],'new_cycles':s['cycles'],'cycle_delta':s['cycles']-old['cycles'],'phase_deltas':{p:v-old['phase_cycles'][p]for p,v in s['phase_cycles'].items()},'counter_deltas':{k:s[k]-old[k]for k in ['waves','parents','candidates','commits','op_retired','events','physical_requests','physical_responses']}})
   old_cycles=sum(v['cycles']for v in before.values());row['baseline_cycles']=old_cycles;row['cycle_delta']=totals['cycles']-old_cycles;row['cycle_ratio']=totals['cycles']/old_cycles;row['baseline_output_identical']=True;row['per_sample_vs_baseline']=pairs
  rows.append(row)
 out={'status':'PASS','scope':'measured behavioral RTL physical handshakes at declared service assumptions; no achieved clock qualification','service':cfg,'binding_sha256':sha(a.run/'binding.json'),'baseline_binding_sha256':sha(a.baseline/'binding.json')if a.baseline else None,'results':rows};(a.run/'service_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':'PASS','results':[{k:r[k]for k in ['case','physical_requests','observed_issue_gap_min_cycles','observed_ack_latency_min_cycles','observed_ack_latency_max_cycles']}for r in rows]},indent=2))
if __name__=='__main__':main()

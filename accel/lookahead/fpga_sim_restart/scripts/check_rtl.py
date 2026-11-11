#!/usr/bin/env python3
"""Fail closed: simulator exit alone is insufficient."""
import sys,pathlib,json,csv,hashlib
p=pathlib.Path(sys.argv[1]);log=(p/'simulate.log').read_text()
assert 'TEST_PASS whole memory exact' in log and 'Fatal:' not in log
actual=(p/'actual.hex').read_bytes();expected=(p/'expected.hex').read_bytes();assert actual==expected
rows=[json.loads(s) for s in (p/'summary.jsonl').read_text().splitlines()];assert len(rows)==2
assert all(r['accepted']==r['retired'] and r['diff_words']==0 for r in rows)
last_accept=None;intervals={};accepted=0;mem_stalls=0;rsp_stalls=0;accept_cycles=[]
with (p/'cycles.csv').open() as f:
 for row in csv.DictReader(f):
  c=int(row['cycle'])
  if c==0:continue # Before the first synchronous reset edge only.
  valid=int(row['req_valid']);ready=int(row['req_ready'])
  if valid and ready:
   if last_accept is not None:gap=c-last_accept;intervals[gap]=intervals.get(gap,0)+1
   last_accept=c;accepted+=1;accept_cycles.append(c)
  mem_stalls+=int(row['mem_valid']) and not int(row['mem_ready'])
  rsp_stalls+=int(row['rsp_valid']) and not int(row['rsp_ready'])
assert accepted == sum(row.split()[0]=='0' for row in (p/'stimulus.txt').read_text().splitlines())
assert accepted >= max(x['accepted'] for x in rows)
if p.name.startswith('directed'):
 assert max(x['request_hwm'] for x in rows)==64
 assert max(x['mshr_hwm'] for x in rows)==32
 assert max(x['dirty_hwm'] for x in rows)==16
 assert sum(x['raw_stall'] for x in rows)>0 and sum(x['merges'] for x in rows)>0
result=dict(status='PASS',scope='owner service only; not complete sample/batch',phases=rows,accepted_on_interface=accepted,accept_interval_histogram=intervals,memory_request_backpressure_cycles=mem_stalls,memory_response_backpressure_cycles=rsp_stalls,output_sha256=hashlib.sha256(actual).hexdigest(),compared_32B_lines=len(actual.splitlines()),first_cycle_includes_reset=True)
if (p/'actions.csv').exists():
 retire_cycles=[int(x['cycle']) for x in csv.DictReader(open(p/'actions.csv')) if x['event']=='reduce']
 assert len(retire_cycles)==len(accept_cycles)
 latency=[b-a for a,b in zip(accept_cycles,retire_cycles)];assert min(latency)>=1
 result['accept_to_reduce_cycles']={'min':min(latency),'max':max(latency),'mean':sum(latency)/len(latency),'definition':'FIFO acceptance to whole-pair reduction; persistence requires fence'}
if (p/'transactions.csv').exists():
 pending={};feedback=[]
 for x in csv.DictReader(open(p/'transactions.csv')):
  key=int(x['id']);c=int(x['cycle'])
  if x['event']=='request':
   assert key not in pending;pending[key]=c
  else:
   assert key in pending;feedback.append(c-pending.pop(key))
 assert not pending
 result['memory_feedback_cycles']={'min':min(feedback),'max':max(feedback),'mean':sum(feedback)/len(feedback)}
(p/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',p,accepted,'accepted; entire',result['compared_32B_lines'],'lines equal')

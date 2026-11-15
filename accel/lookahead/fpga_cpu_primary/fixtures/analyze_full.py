#!/usr/bin/env python3
"""Audit complete-core event conservation and publish measured RTL calibration."""
from pathlib import Path
import argparse,collections,csv,hashlib,json,math

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def distribution(values):
 if not values:return {'count':0}
 a=sorted(values);return {'count':len(a),'min':a[0],'mean':sum(a)/len(a),'p50':a[(len(a)-1)//2],'p95':a[math.ceil(.95*len(a))-1],'max':a[-1]}
def analyze(path,partial=False):
 sample_rows=list(csv.DictReader((path/"samples.csv").open()));completed={int(r["sample"])for r in sample_rows}
 if not partial:assert "TEST_PASS FULL_NATIVE_BATCH" in (path/"run.log").read_text(),"No complete-batch PASS"
 logical={};physical={};latency=collections.defaultdict(list);physical_latency=collections.defaultdict(list);occ=collections.Counter();peak=collections.Counter();physical_peak=collections.Counter();counts=collections.Counter();completions=collections.Counter();retire=collections.Counter();samples={};errors=[]
 for r in csv.DictReader((path/'events.csv').open()):
  cy=int(r['cycle']);q=int(r['sample']);
  if partial and q not in completed:continue
  e=r['event'];s=int(r['source_or_port_or_bank']);k=int(r['kind_or_opcode']);identifier=int(r['id_or_cookie'],16);g=int(r['generation'],16);counts[(q,e)]+=1
  if e=='request':
   key=(s,k,identifier,g)
   if key in logical:errors.append(f'duplicate logical live identity cycle{cy} {key}')
   logical[key]=(cy,q);occ[(q,k)]+=1;peak[(q,k)]=max(peak[(q,k)],occ[(q,k)])
  elif e=='return':
   key=(s,k,identifier,g)
   if key not in logical:errors.append(f'unowned logical return cycle{cy} {key}');continue
   born,owner=logical.pop(key)
   if owner!=q:errors.append('logical transaction crosses sample')
   latency[(q,k)].append(cy-born);occ[(q,k)]-=1
  elif e=='physical_issue':
   key=(s,identifier)
   if key in physical:errors.append(f'duplicate physical live tag cycle{cy} {key}')
   physical[key]=(cy,q,k);physical_peak[(q,s)]=max(physical_peak[(q,s)],sum(p==s for p,t in physical))
  elif e=='physical_ack':
   key=(s,identifier)
   if key not in physical:errors.append(f'unowned physical ACK cycle{cy} {key}');continue
   born,owner,write=physical.pop(key)
   if owner!=q:errors.append('physical transaction crosses sample')
   physical_latency[(q,write)].append(cy-born)
  elif e=='external_completion':completions[(q,k)]+=1
  elif e=='canonical_retire':retire[(q,k)]+=1
 if logical or physical:errors.append(f'undrained logical={len(logical)} physical={len(physical)}')
 phases=collections.defaultdict(dict)
 for r in csv.DictReader((path/'phase_cycles.csv').open()):phases[int(r['sample'])][r['phase']]=int(r['cycles'])
 for r in sample_rows:
  d={k:int(v)for k,v in r.items()};q=d['sample'];d['phase_cycles']=phases[q]
  if sum(phases[q].values())!=d['cycles']:errors.append(f'phase sum sample{q}: {sum(phases[q].values())} != {d["cycles"]}')
  if counts[(q,'physical_issue')]!=d['physical_requests'] or counts[(q,'physical_ack')]!=d['physical_responses']:errors.append(f'physical summary mismatch sample{q}')
  if sum(retire[(q,k)]for k in range(8))!=d['op_retired']:errors.append(f'retirement trace mismatch sample{q}')
  d['logical_service']={str(k):dict(distribution(latency[(q,k)]),peak_outstanding=peak[(q,k)])for k in range(12)}
  d['physical_read_latency']=distribution(physical_latency[(q,0)]);d['physical_write_ack_latency']=distribution(physical_latency[(q,1)])
  d['physical_peak_credits_by_port']={str(p):physical_peak[(q,p)]for p in range(32)}
  d['external_completions_by_opcode']={str(k):completions[(q,k)]for k in range(8)};d['canonical_retire_by_opcode']={str(k):retire[(q,k)]for k in range(8)};samples[str(q)]=d
 return {'status':('PARTIAL_PASS'if partial else'PASS')if not errors else'FAIL','scope':'measured behavioral complete-core trace; no achieved frequency claim','source_files':{n:sha(path/n)for n in ['events.csv','samples.csv','phase_cycles.csv','request_kinds.csv']},'samples':samples,'errors':errors}
def main():
 p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('--allow-partial',action='store_true');a=p.parse_args();out=analyze(a.run,a.allow_partial);(a.run/('calibration_partial.json'if a.allow_partial else'calibration.json')).write_text(json.dumps(out,indent=2)+'\n');print(out['status'],len(out['samples']),'samples',out['errors']);assert out['status'] in ['PASS','PARTIAL_PASS']
if __name__=='__main__':main()

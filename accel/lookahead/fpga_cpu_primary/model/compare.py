#!/usr/bin/env python3
"""Compare independent complete RTL traces against finite model, without scaling."""
from pathlib import Path
import argparse,csv,json,hashlib,struct
PHASES=['IDLE','SRST','LOAD','INIT','COST','SEED','SEED_WAIT','MIN_START','MIN_WAIT','WAVE_START','EXPAND','FLUSH','FINALIZE','REOPEN','REOPEN_WAIT','EXPORT_START','EXPORT_WAIT','COMPLETE','FAULT']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('model',type=Path);p.add_argument('rtl',type=Path);p.add_argument('case');p.add_argument('output',type=Path);a=p.parse_args();assert not a.output.exists()
 rtl_requests={}
 for e in csv.DictReader((a.rtl/'events.csv').open()):
  if e['event']=='request':rtl_requests.setdefault(int(e['sample']),[]).append((int(e['cycle']),int(e['source_or_port_or_bank']),int(e['kind_or_opcode']),int(e['line_or_node'],16),int(e['id_or_cookie'],16),int(e['generation'],16)))
 rows=list(csv.DictReader((a.rtl/'samples.csv').open()));phase={};requests={}
 for r in csv.DictReader((a.rtl/'phase_cycles.csv').open()):phase.setdefault(int(r['sample']),[0]*19)[int(r['phase'])]=int(r['cycles'])
 for r in csv.DictReader((a.rtl/'request_kinds.csv').open()):requests.setdefault(int(r['sample']),[0]*12)[int(r['kind'])]=int(r['requests']);assert r['requests']==r['responses']
 result=[]
 for row in rows:
  q=int(row['sample']);mroot=a.model/a.case/f'sample_{q}';m=json.loads((mroot/'finite.json').read_text());mp=json.loads((mroot/'core_phases.json').read_text());output=(mroot/'output.bin').read_bytes()
  words=[]
  for line in (a.rtl/f'sample_{q}_actual_beats.hex').read_text().splitlines():
   v=int(line,16);words.extend((v>>(i*64))&((1<<64)-1)for i in range(4))
  actual=b''.join(struct.pack('<II',v>>32,v&0xffffffff)for v in words)[:len(output)];assert actual==output,'RTL_MODEL_OUTPUT_DIFFERENCE'
  counter={'waves':m['waves'],'parents':m['parents'],'candidates':m['candidates'],'commits':m['canonical_lines'],'events':m['events'],'stale':m['stale'],'recorded':m['recorded'],'output_beats':m['output_ACKs'],'op_retired':sum(x['tx_retired']for x in m['bank_stats']),'physical_requests':sum(sum(x)for x in m['traffic'])}
  disagreements={k:{'rtl':int(row[k]),'model':v}for k,v in counter.items()if int(row[k])!=v}
  assert sum(phase[q])==int(row['cycles']) and sum(mp['phase_cycles'])==m['cycles']
  expected_requests=sorted((x[0]-int(row['start']),*x[1:])for x in rtl_requests.get(q,[]));actual_requests=[]
  if(mroot/'events.csv').exists():
   for e in csv.DictReader((mroot/'events.csv').open()):
    if e['event']=='logical_request':actual_requests.append(tuple(int(e[k])for k in ['cycle','source','kind','line','id','gen']))
  actual_requests.sort();first_differences=[{'rtl':r,'model':m}for r,m in zip(expected_requests,actual_requests)if r!=m][:4]
  delta=m['cycles']-int(row['cycles']);phase_rows={name:{'rtl':phase[q][i],'model':mp['phase_cycles'][i],'delta':mp['phase_cycles'][i]-phase[q][i]}for i,name in enumerate(PHASES)}
  result.append({'sample':q,'rtl_cycles':int(row['cycles']),'model_cycles':m['cycles'],'delta_cycles':delta,'relative_delta':delta/int(row['cycles']),'non_init_relative_delta':delta/max(1,int(row['cycles'])-phase[q][3]),'outputs_byte_exact':True,'logical_request_schedule_exact':expected_requests==actual_requests,'first_logical_request_differences':first_differences,'output_sha256':sha(mroot/'output.bin'),'counter_disagreements':disagreements,'requests_by_kind_rtl':requests[q],'requests_by_kind_model':[sum(x)for x in m['traffic']],'phases':phase_rows})
 out={'scope':'independent RTL/model outputs, phase counts, request kinds and retire counters; no average correction','rtl_model_calibrated':False,'clock_qualified':False,'completed_samples':len(result),'model_binding_sha256':sha(a.model/'binding.json'),'rtl_trace_sha256':{n:sha(a.rtl/n)for n in ['samples.csv','phase_cycles.csv','request_kinds.csv','events.csv']},'all_logical_request_schedules_exact':all(x['logical_request_schedule_exact']for x in result),'all_outputs_exact':all(x['outputs_byte_exact']for x in result),'all_counter_totals_exact':all(not x['counter_disagreements']for x in result),'all_request_kinds_exact':all(x['requests_by_kind_rtl']==x['requests_by_kind_model']for x in result),'maximum_absolute_cycle_delta':max(abs(x['delta_cycles'])for x in result),'maximum_absolute_relative_delta':max(abs(x['relative_delta'])for x in result),'maximum_non_init_relative_delta':max(abs(x['non_init_relative_delta'])for x in result),'samples':result}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k not in ['samples','rtl_trace_sha256']},indent=2))
if __name__=='__main__':main()

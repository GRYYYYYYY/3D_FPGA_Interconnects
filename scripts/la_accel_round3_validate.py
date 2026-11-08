"""Audit immutable input/source bindings and completed round-three evidence."""
import argparse,json,re
from pathlib import Path
from prepare import sha256

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--experiment',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=a.experiment.resolve()
 assert not a.output.exists();checks=[]
 def check(condition,name):
  checks.append({'check':name,'passed':bool(condition)})
 for worker in r.glob('gpu_worker*'):
  if not worker.is_dir() or not (worker/'worker.json').exists():continue
  meta=json.loads((worker/'worker.json').read_text())
  for rel,digest in meta['sources'].items():check(sha256(worker/'source'/rel)==digest,worker.name+':snapshot:'+rel)
  finish=json.loads((worker/'finished.json').read_text());rows=json.loads((worker/'measurements.json').read_text())
  check(finish['status']=='passed' and finish['processes']==len(rows),worker.name+':completed')
  for row in rows:check(len(row['measurements'])==6 and row['measurements'][0]['phase']=='cold_first_call' and all(m['all_golden_bits_match'] for m in row['measurements']),worker.name+':'+row['log'])
 for d in r.glob('native_d*'):
  p=d/'manifest.json'
  if not p.exists():continue
  m=json.loads(p.read_text())
  for key,name in [('architecture_sha256','architecture.xml'),('workload_sha256','workload.bin'),('rr_graph_sha256','rr.xml'),('layer_map_sha256','layers.bin'),('native_wire_map_sha256','wire_map.bin')]:check(sha256(d/name)==m[key],d.name+':'+name)
  s=json.loads((d/'spill.json').read_text());nontrivial=[q for q in s['samples'] if q['edges']]
  check(s['all_native_golden_bits_match'] and len(s['samples'])==m['dimensions']['jobs'],d.name+':all_native_samples')
  check(any(q['cross_pushed'] and q['expanded_layers']>1 and q['external_queue_reads'] and q['external_queue_writes'] for q in nontrivial),d.name+':actual_3d_spill')
 for d in r.glob('hls_*'):
  if not d.is_dir() or not (d/'binding.json').exists():continue
  b=json.loads((d/'binding.json').read_text())
  for key,value in b.items():
   if key.startswith('/'):
    snapshot=d/'source_snapshot'/Path(key).name
    check(snapshot.exists() and sha256(snapshot)==value,d.name+':snapshot:'+Path(key).name)
    # The first cohort deliberately froze the original 5ns Tcl before period support was added.
    if not key.endswith('.tcl'):check(Path(key).exists() and sha256(Path(key))==value,d.name+':source:'+Path(key).name)
  check(any(sha256(p)==b['testbench'] for p in (d/'source_snapshot').glob('*.cpp')),d.name+':testbench')
  if 'dual_header' in b:check(sha256(d/'source_snapshot/dual_kernel.hpp')==b['dual_header'],d.name+':dual_interface_header')
  for phase in ['csim','csynth','cosim','impl']:
   p=d/(phase+'.json');check(p.exists() and json.loads(p.read_text())['status']=='passed',d.name+':'+phase)
 for d in r.glob('bounded_*'):
  if not d.is_dir() or not (d/'config.json').exists():continue
  c=json.loads((d/'config.json').read_text());p=d/'result.json';check(p.exists(),d.name+':completed')
  if not p.exists():continue
  v=json.loads(p.read_text());check(v['status']=='passed' and all(v['rtl_result_ports_match_c'].values()),d.name+':fresh_bitwise_RTL')
  check(sha256(d/'config.json')==v['config_sha256'] and sha256(d/'simulation.log')==v['log_sha256'],d.name+':result_binding')
  check(sha256(d/'sim/verilog/bounded_axi3.sv')==c['interposer_sha256'],d.name+':memory_model')
  memory=v['memory'];check(memory['drained'] and memory['max_total_reads']<=c['total_read_credits'] and memory['max_total_writes']<=c['total_write_credits'],d.name+':global_credits_and_drain')
  for entry in memory['ports']:check(entry['max_reads']<=c['outstanding_per_port_per_direction'] and entry['max_writes']<=c['outstanding_per_port_per_direction'],d.name+':port_credits:'+str(entry['port']))
  if 'engine_idle_signals' in c:check(v['engine_overlap']['overlap_cycles']>0 and all(e['active_cycles']>0 for e in v['engine_overlap']['engines']),d.name+':engine_overlap')
 result={'status':'passed' if all(x['passed'] for x in checks) else 'failed','checks':checks,'note':'Timing-clean frequency and speedup gate are assessed separately; synthesis success alone is not timing closure.'}
 a.output.write_text(json.dumps(result,indent=2)+'\n');print(result['status'],len(checks),'checks');return result['status']!='passed'
if __name__=='__main__':raise SystemExit(main())

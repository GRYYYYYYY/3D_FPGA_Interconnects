"""Summarize one completed worker cohort; do not mix E1 and E2 denominators."""
import argparse,json,statistics
from pathlib import Path

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--worker',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--job-id',required=True);p.add_argument('--resident-only',action='store_true');a=p.parse_args();w=a.worker.resolve()
 assert not a.output.exists();finished=json.loads((w/'finished.json').read_text())
 if not a.resident_only:assert finished['all_commands_successful']
 native=json.loads((w/'native_controls/summary.json').read_text());worker=json.loads((w/'worker.json').read_text()) if (w/'worker.json').exists() else None
 result=dict(hostname=native['hostname'],gpu_job_id=a.job_id,E2_native={},E1_resident={},worker=worker,target_ordering_verified=False)
 result['job_status']=finished;result['excluded_native_controls']=a.resident_only
 for arm in ([] if a.resident_only else sorted({r['arm'] for r in native['measurements']})):
  rows=[r for r in native['measurements'] if r['arm']==arm]
  assert all(r['component_valid'] and r['map_matches_reference'] and r['cpu_budget_audit']['verified'] for r in rows)
  values=[r['build_seconds'] for r in rows];result['E2_native'][arm]=dict(seconds=values,median=statistics.median(values),range=[min(values),max(values)],all_maps_match=True,timer_resolution_s=.01,cpu_workers=rows[0]['workers'],cpu_set=rows[0]['cpu_budget']['cpu_set'],routing_success_claimed=False)
 for path in sorted(w.glob('*/runs.json')):
  rows=json.loads(path.read_text());assert all(r['status']=='passed' and r['matches_reference'] for r in rows)
  values=[m['resident_elapsed_s'] for r in rows for m in r.get('measurements',[r])]
  if worker and worker['requested_physical_cores']:assert all(r['cpu_affinity']==worker['affinity'] for r in rows)
  result['E1_resident'][path.parent.name]=dict(seconds=values,median=statistics.median(values),range=[min(values),max(values)],all_maps_match=True,evidence_type=rows[0]['evidence_type'],workload_sha256=rows[0]['workload_sha256'],cpu_affinity=rows[0]['cpu_affinity'],cpu_workers=rows[0]['cpu_workers'],contexts=rows[0]['contexts'])
 if worker and worker['requested_physical_cores']:
  assert a.resident_only or worker['affinity']==native['pool'];result['affinity_matched']=True
 else:result['affinity_matched']=False
 result['E1_cpu_affinity_limit']='Same physical core set, one NUMA node, same job quota; shared host, no exclusivity claim.' if result['affinity_matched'] else 'C1 not pinned to native NUMA subset; pilot only.'
 a.output.write_text(json.dumps(result,indent=2));print(a.output)
if __name__=='__main__':main()

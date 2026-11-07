"""Joint gains use matched original_parallel controls, not GPU-only gates."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import statistics
from prepare import write_json


def cpu_set(row):
    return row.get('cpu_budget_audit',{}).get('permitted_cpu_set',[])


def validity(row):
    reasons=[]
    if not row.get('success'):reasons.append('route_or_readback_failed')
    if row.get('diagnostic'):reasons.append('diagnostic_measurement')
    settings=row.get('execution_settings',{})
    if settings.get('gpu_timing')!='0' or settings.get('diagnostics')!='0' or settings.get('capture'):reasons.append('diagnostic_settings_enabled_or_missing')
    command=row.get('command',[])
    try:
        if command[command.index('--num_workers')+1]!='4' or command[command.index('--router_algorithm')+1]!='parallel':reasons.append('not_four_worker_parallel')
    except (ValueError,IndexError):reasons.append('missing_parallel_settings')
    audit=row.get('cpu_budget_audit',{})
    if len(cpu_set(row))!=4 or not audit.get('verified') or audit.get('affinity_violations'):reasons.append('cpu_budget_audit_failed')
    if settings.get('cpu_affinity')!=cpu_set(row):reasons.append('runner_process_affinity_mismatch')
    if not row.get('full_check') or not row.get('independent_metrics',{}).get('full_check'):reasons.append('full_checks_missing')
    if not row.get('independent_check',{}).get('cpu_budget_audit',{}).get('verified'):reasons.append('readback_cpu_budget_audit_failed')
    if row.get('hybrid',{}).get('errors') or row.get('hybrid',{}).get('fallbacks'):reasons.append('native_gpu_error_or_fallback')
    if row['variant']=='batch' and not (row.get('hybrid',{}).get('gpu_initialized') and row.get('hybrid',{}).get('committed',0)>0):reasons.append('no_actual_gpu_commits')
    return reasons


def compare(reference,candidate):
    reasons=['reference:'+v for v in validity(reference)]+['candidate:'+v for v in validity(candidate)]
    if reference['case']!=candidate['case'] or reference['repeat']!=candidate['repeat']:reasons.append('unmatched_case_or_repeat')
    if cpu_set(reference)!=cpu_set(candidate):reasons.append('different_cpu_sets')
    result={'case':candidate['case'],'repeat':candidate['repeat'],'reference':reference['variant'],'variant':candidate['variant'],'eligible':not reasons,'reasons':reasons}
    if reasons:return result
    cpd=candidate['critical_path_ns']/reference['critical_path_ns']-1;wire=candidate['wirelength']/reference['wirelength']-1
    result.update(cpd_change_fraction=cpd,wirelength_change_fraction=wire,quality_passed=cpd<=.05+1e-9 and wire<=.05+1e-9,
                  process_speedup=reference['native_process_seconds']/candidate['native_process_seconds'],workflow_speedup=reference['workflow_seconds']/candidate['workflow_seconds'],
                  process_saving_seconds=reference['native_process_seconds']-candidate['native_process_seconds'],workflow_saving_seconds=reference['workflow_seconds']-candidate['workflow_seconds'])
    if not result['quality_passed']:result.update(eligible=False,reasons=['quality_budget_exceeded'])
    return result


def repeated_claim(comparisons,expected=3):
    primary=[c for c in comparisons if c['reference']=='original_parallel' and c['variant']=='batch']
    complete=len(primary)>=expected and len({p['repeat'] for p in primary})==len(primary)
    eligible=complete and all(p['eligible'] for p in primary)
    process=eligible and all(p['process_speedup']>1 for p in primary)
    workflow=eligible and all(p['workflow_speedup']>1 for p in primary)
    return {'expected_minimum_repeats':expected,'matched_repeats':len(primary),'complete':complete,'all_eligible':eligible,
            'process_faster_every_repeat':process,'workflow_faster_every_repeat':workflow,'positive_joint_candidate':process and workflow,
            'scope':'Case-specific matched repetitions only. CPU/guard comparisons explain costs and do not gate joint gains; no statistical significance claim from three samples.'}


def log_evidence(directory):
    path=directory/'process.log'
    if not path.exists():return {}
    text=path.read_text(errors='replace');trace=[]
    for line in text.splitlines():
        m=re.match(r'\s*(\d+)\s+([\d.]+)\s+([\d.eE+-]+)\s+(\d+)\s+([\d.eE+]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+\(',line)
        if m:trace.append({'iteration':int(m[1]),'seconds':float(m[2]),'present_factor':float(m[3]),'rerouted_nets':int(m[6]),'rerouted_connections':int(m[7]),'overused_nodes':int(m[8])})
    stages={name:float(values[-1]) if values else None for name,pattern in [
        ('rr_graph_load',r'Loading routing resource graph took ([\d.]+) seconds'),('lookahead_build',r'Computing router lookahead map took ([\d.]+) seconds'),('routing',r'# Routing took ([\d.]+) seconds')]
        for values in [re.findall(pattern,text)]}
    counts=re.findall(r'Total number of overused nodes:\s*(\d+)',text)
    measurement=directory/'measurement.json'
    outcome=json.loads(measurement.read_text()) if measurement.exists() else {}
    interrupted=outcome.get('status')=='timeout' or outcome.get('returncode',0)<0
    final=int(counts[-1]) if counts else (trace[-1]['overused_nodes'] if trace and outcome.get('routing_success') else None)
    return {'stage_seconds':stages,'iterations':trace,'final_overused_nodes':None if interrupted else final,
            'last_observed_overused_nodes':trace[-1]['overused_nodes'] if trace else None,
            'overuse_report':str(directory/'report_overused_nodes.rpt') if (directory/'report_overused_nodes.rpt').exists() else None}


def analyze(run):
    records=[];budgets={};seen=set()
    for name in ['gemm','elliptic_initial','elliptic_repeats']:
        path=run/name/'summary.json'
        if not path.exists():continue
        data=json.loads(path.read_text());budgets[name]=data.get('cpu_budget')
        for row in data['measurements']:
            key=(row['case'],row['repeat'],row['variant'])
            if key in seen:raise ValueError('duplicate matrix measurement')
            seen.add(key);directory=run/name/Path(row['directory']).name
            records.append({**row,'local_evidence_directory':str(directory),'log_evidence':log_evidence(directory),'validity_reasons':validity(row)})
    grouped=defaultdict(dict)
    for row in records:grouped[(row['case'],row['repeat'])][row['variant']]=row
    comparisons=[]
    for _,group in sorted(grouped.items()):
        for target in ['native_parallel','guard','batch']:
            if 'original_parallel' in group and target in group:comparisons.append(compare(group['original_parallel'],group[target]))
        for ref,target in [('native_parallel','guard'),('native_parallel','batch'),('guard','batch')]:
            if ref in group and target in group:comparisons.append(compare(group[ref],group[target]))
    aggregate=[]
    for case,variant in sorted({(r['case'],r['variant']) for r in records}):
        rows=[r for r in records if r['case']==case and r['variant']==variant]
        entry={'case':case,'variant':variant,'measurements':len(rows),'successes':sum(r['success'] for r in rows),'valid_measurements':sum(not r['validity_reasons'] for r in rows)}
        for key in ['native_process_seconds','workflow_seconds','routing_seconds']:
            values=[r[key] for r in rows if not r['validity_reasons'] and r.get(key) is not None]
            entry[key]={'values':values,'median':statistics.median(values),'min':min(values),'max':max(values)} if values else None
        aggregate.append(entry)
    return {'scope':'Same-job equal-CPU-budget joint comparison; failures retained, no cross-job ratios','cpu_budgets':budgets,'measurements':records,'comparisons':comparisons,'aggregates':aggregate,
            'claims':{case:repeated_claim([c for c in comparisons if c['case']==case]) for case in sorted({r['case'] for r in records})}}


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    write_json(args.output,analyze(args.run))


if __name__=='__main__':main()

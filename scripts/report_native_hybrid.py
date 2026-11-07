"""Summarize measured native-VPR comparisons without promoting diagnostics.

Ratios are formed only within one submission/case/repetition. Failed runs remain
in the output. A small warm-query win is not an end-to-end acceleration claim.
"""
import argparse
import csv
import json
import math
from pathlib import Path
import signal
import statistics

from prepare import sha256, write_json
from scaling_common import metrics


def measurement_outcome(row):
    """Keep failures distinct from ordinary routing infeasibility."""
    result = {key: row.get(key) for key in (
        'case', 'repeat', 'variant', 'directory', 'status', 'success',
        'returncode', 'diagnostic', 'native_process_seconds', 'workflow_seconds',
        'routing_seconds', 'critical_path_ns', 'wirelength')}
    code = row.get('returncode')
    if row.get('success'):
        result['outcome'] = 'legal_route'
    elif row.get('status') == 'timeout':
        result['outcome'] = 'timeout'
    elif isinstance(code, int) and code < 0:
        result['outcome'] = 'terminated_by_signal'
        try:
            result['signal'] = signal.Signals(-code).name
        except ValueError:
            result['signal'] = str(-code)
        result['cause'] = 'Not established by return code alone'
    elif row.get('status') is None:
        result['outcome'] = 'pending'
    else:
        result['outcome'] = 'unsuccessful_run'
    return result


def paired(directory):
    path = Path(directory) / 'hybrid.json.queries.csv'
    if not path.exists():
        return None
    rows = list(csv.DictReader(path.open()))
    rows = [r for r in rows if r.get('mode') == 'pair' and r.get('status') == '0'
            and int(r['search_ns'])>0 and math.isfinite(float(r['gpu_cost']))]
    if not rows:
        return None
    # Initialization is a reported part of full-run time; exclude it only from
    # the explicitly named warm-query diagnostic, never the main comparison.
    warm = [r for r in rows if int(r['init_ns']) < 1_000_000]
    bands = []
    for low, high in [(0, 100_000), (100_000, 1_000_000), (1_000_000, 10_000_000), (10_000_000, math.inf)]:
        group = [r for r in warm if low <= int(r['cpu_remaining_ns']) < high]
        if not group:
            continue
        bands.append({'cpu_remaining_ns_from':low, 'cpu_remaining_ns_to':high if math.isfinite(high) else None,
                      'queries':len(group), 'gpu_wins':sum(int(r['dispatch_ns']) < int(r['cpu_remaining_ns']) for r in group),
                      'median_cpu_us':statistics.median(int(r['cpu_remaining_ns']) / 1000 for r in group),
                      'median_gpu_dispatch_us':statistics.median(int(r['dispatch_ns']) / 1000 for r in group)})
    return {'csv':str(path), 'sha256':sha256(path), 'queries':len(rows), 'warm_queries':len(warm),
            'warm_gpu_wins':sum(int(r['dispatch_ns']) < int(r['cpu_remaining_ns']) for r in warm),
            'bands':bands, 'scope':'Actual remaining native CPU search versus full GPU dispatch on the same partial-search snapshot. Paired mode does not commit GPU paths.'}


def comparisons(record):
    output = []
    rows = record['measurements']
    for row in rows:
        if row.get('diagnostic') or row['variant'] in ['original_vpr', 'original_parallel']:
            continue
        refs = ['original_vpr']
        if row['variant'] in ['batch', 'native_parallel', 'guard']:
            refs.append('original_parallel')
        if row['variant']=='batch':refs.append('guard')
        for reference in refs:
            baseline = next((r for r in rows if r['case'] == row['case'] and r['repeat'] == row['repeat'] and r['variant'] == reference), None)
            if baseline is None:
                continue
            result = {'case':row['case'], 'repeat':row['repeat'], 'variant':row['variant'], 'reference':reference,
                      'success':bool(row.get('success')), 'reference_success':bool(baseline.get('success')),
                      'native_process_seconds':row.get('native_process_seconds'), 'workflow_seconds':row.get('workflow_seconds'),
                      'directory':row['directory'], 'same_submission':True,
                      'limited_offload_smoke':record.get('max_offloads') is not None}
            for label,item in [('candidate',row),('reference',baseline)]:
                log=Path(item['directory'])/'process.log'
                if log.exists():
                    parsed=metrics(log.read_text(errors='replace'))
                    result[label+'_search_worker_seconds']=parsed['search_seconds']
                    result[label+'_search_timer_seconds']=parsed['search_timer_seconds']
            if row.get('success') and baseline.get('success'):
                cpd = row['critical_path_ns'] / baseline['critical_path_ns'] - 1
                wire = row['wirelength'] / baseline['wirelength'] - 1
                result.update(cpd_delta=cpd, wirelength_delta=wire, within_5pct_budget=max(cpd,wire) <= .05,
                              process_speedup=baseline['native_process_seconds']/row['native_process_seconds'],
                              workflow_speedup=baseline['workflow_seconds']/row['workflow_seconds'],
                              routing_speedup=baseline['routing_seconds']/row['routing_seconds'] if row.get('routing_seconds') else None)
                result['positive_single_run'] = result['workflow_speedup'] > 1 and result['within_5pct_budget'] and not result['limited_offload_smoke']
            if row.get('hybrid'):
                result['hybrid'] = row['hybrid']
            attempts = row.get('hybrid', {}).get('offload_attempts', 0)
            result['gpu_executed'] = attempts > 0
            # A parallel CPU speedup, or ordinary run-to-run noise in a control,
            # must not be presented as a gain attributable to GPU offload.
            guarded_control=any(r['variant']=='guard' and r['case']==row['case'] and r['repeat']==row['repeat'] for r in rows)
            result['positive_gpu_candidate'] = bool(
                result.get('positive_single_run') and attempts > 0 and not row.get('hybrid', {}).get('errors')
                # Faster independent rereading must not mask a slower router
                # process and turn it into a claimed GPU contribution.
                and result.get('process_speedup', 0) > 1
                and ((row['variant']=='hybrid' and reference=='original_vpr')
                     or (row['variant']=='batch' and reference==('guard' if guarded_control else 'original_parallel'))))
            output.append(result)
    return output


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--run', type=Path, action='append', required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    out = {'scope':'Native in-process CPU/GPU router; do not pool with standalone target-router timings',
           'quality_budget':.05, 'runs':[], 'measurements':[], 'comparisons':[], 'paired':[], 'positive_claim_requires_three_repeats':True,
           'search_time_scope':'Reparsed sum of per-router elapsed timers; worker-seconds include GPU/queue waits, not parallel critical-path wall time. Older raw summaries stored only the last timer; those artifacts are preserved.'}
    for directory in args.run:
        summary = directory / 'summary.json'
        record = json.loads(summary.read_text())
        out['runs'].append({'path':str(summary.resolve()), 'sha256':sha256(summary), 'status':record['status']})
        out['measurements'].extend(measurement_outcome(row) for row in record['measurements'])
        out['comparisons'].extend(comparisons(record))
        for row in record['measurements']:
            if row.get('diagnostic') and row.get('success'):
                analysis = paired(row['directory'])
                if analysis:
                    analysis.update(case=row['case'], run=str(directory.resolve()))
                    out['paired'].append(analysis)
    write_json(args.output, out)


if __name__ == '__main__':
    main()

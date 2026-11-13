"""Describe measured complete-model traffic and its trace-specific service bound.

The bound is conditional on the observed traffic and stated minimum port gap;
it is neither a new performance prediction nor a bound on other architectures.
Usage: COMPLETED_SUMMARY.json OUTPUT.json
"""
from pathlib import Path
import datetime
import hashlib
import json
import sys

root = Path(__file__).resolve().parents[4]
r = root / 'results/fpga_sparse_stream_r2_20261112'
source = r / 'analysis' / sys.argv[1]
out = r / 'analysis' / sys.argv[2]
if out.exists():
    raise RuntimeError('append-only analysis already exists')
rows = []
for item in json.loads(source.read_text())['completed']:
    d = r / item['run']
    s = json.loads((d / 'summary.json').read_text())
    receipt = json.loads((d / 'receipt.json').read_text())
    assert receipt.get('returncode') == 0 and receipt.get('status', 'passed') == 'passed'
    n = [c['reads'] + c['writes'] for c in s['channels']]
    cycles, gap = s['resident_cycles'], s['service_gap_cycles']
    bound = max((x - 1) * gap + 1 if x else 0 for x in n)
    assert bound <= cycles and sum(n) * 32 == item['internal_traffic_bytes']
    row = {'run': item['run'], 'resident_cycles': cycles,
           'observed_internal_bytes': sum(n) * 32,
           'observed_32byte_transactions_per_cycle': sum(n) / cycles,
           'maximum_transactions_per_cycle_from_minimum_gap': len(n) / gap,
           'observed_transfer_utilization_of_gap_only_limit': sum(n) * gap / (len(n) * cycles),
           'trace_specific_minimum_transfer_cycles': bound,
           'minimum_transfer_cycles_fraction_of_observed_cycles': bound / cycles,
           'physical_ID_peaks': [c['peak'] for c in s['channels']],
           'candidate_issue_peak_per_cycle': item['issue']['peak_per_cycle'],
           'candidate_issue_per_resident_cycle': item['issue']['per_resident_cycle'],
           'main_seconds': None, 'board_measured': False,
           'scope': 'actual completed model/RTL counters; service bound assumes this observed traffic and the hypothetical synchronous port gap; excludes no resident work from observed cycles'}
    rows.append(row)
out.write_text(json.dumps({'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'source_summary_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'clock_assigned': False, 'results': rows}, indent=2) + '\n')
for x in rows:
    print(x['run'], x['resident_cycles'], 'cycles;',
          round(x['observed_internal_bytes'] / 1e9, 3), 'GB;',
          round(x['observed_transfer_utilization_of_gap_only_limit'], 4), 'gap-limit utilization')

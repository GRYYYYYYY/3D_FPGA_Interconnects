"""Check a saved routed STA period; never derive a clock from negative slack.

This is a mechanical guard for the report review, not a substitute for reviewing
the RTL, source binding, resource scope or functional calibration. Unknown
methodology/DRC rules require a separate review; they are never waived here.
"""
from pathlib import Path
import csv, hashlib, json, re, sys

root = Path(__file__).resolve().parents[4]
version, tag, period_text, output_name = sys.argv[1:5]
p = root / 'results/fpga_sparse_stream_r2_20261112/timing' / version
d = p / tag
period = float(period_text)
stem = 'p' + str(round(period * 1000)) + 'ps'
out = d / output_name
if out.exists():
    raise RuntimeError('append-only result already exists')

def read(name):
    return (d / name).read_text()

def rules(text):
    return {m[0]: {'severity': m[1], 'count': int(m[2])}
            for m in re.findall(r'^\|\s*([A-Z]+-\d+)\s*\|\s*(\w+)\s*\|[^\n|]*\|\s*(\d+)\s*\|', text, re.M)}

checks = {}
binding = json.loads((p / 'source_binding.json').read_text())
checks['physical_context'] = binding.get('context_resource_overhead_included') is True
periods = list(csv.DictReader(read('tested_periods.csv').splitlines()))
rows = [x for x in periods if float(x['period_ns']) == period]
checks['exact_period_tested'] = len(rows) == 1
timing = read(stem + '_timing.rpt')
numeric_row = re.search(r'WNS\(ns\).*?\n\s*[- ]+\n([^\n]+)', timing)
if not numeric_row:
    raise RuntimeError('unrecognized timing summary')
values = numeric_row[1].split()
checks['summary_columns'] = len(values) == 12
wns, whs, wpws = [float(values[x]) for x in [0, 4, 8]]
checks['setup_hold_pulse_width_nonnegative'] = min(wns, whs, wpws) >= 0
checks['zero_failing_endpoints'] = all(int(values[x]) == 0 for x in [2, 6, 10])
checks['all_constraints_met'] = 'All user specified timing constraints are met.' in timing
checks['csv_matches_report'] = len(rows) == 1 and abs(float(rows[0]['setup_slack_ns']) - wns) < .0005 and abs(float(rows[0]['hold_slack_ns']) - whs) < .0005
ct = dict(re.findall(r'^\d+\. checking (\w+) \((\d+)\)', read(stem + '_check_timing.rpt'), re.M))
checks['twelve_check_timing_categories_zero'] = len(ct) == 12 and all(int(x) == 0 for x in ct.values())
route = read('route_status.rpt')
counts = {}
for name in ['routable nets', 'fully routed nets', 'nets with routing errors']:
    m = re.search(re.escape('# of ' + name) + r'\.+\s*:\s*(\d+)', route)
    counts[name] = int(m[1]) if m else -1
checks['all_routable_nets_routed'] = counts['routable nets'] > 0 and counts['routable nets'] == counts['fully routed nets'] and counts['nets with routing errors'] == 0
methodology = rules(read(stem + '_methodology.rpt'))
drc_text = read(stem + '_drc.rpt')
drc = rules(drc_text)
checks['reviewed_methodology_only'] = set(methodology) <= {'XDCC-4', 'XDCC-8', 'CLKC-3'} and all(x['severity'] in ['Warning', 'Advisory'] for x in methodology.values())
clean_drc = not drc and re.search(r'^\s*Violations found:\s*0\s*$', drc_text, re.M) is not None
terminal_drc = set(drc) == {'RTSTAT-10'} and drc['RTSTAT-10'] == {'severity': 'Warning', 'count': 1} and 'signature[31:0]' in drc_text
checks['reviewed_terminal_OOC_DRC_only'] = clean_drc or terminal_drc
xdc = read(stem + '.xdc')
checks['no_timing_exception'] = not re.search(r'^\s*(set_false_path|set_multicycle_path|set_clock_groups|set_disable_timing|reset_timing)', xdc, re.M)
checks['signature_IO_delays_retained'] = 'set_output_delay -clock clk -max 0.500' in xdc and 'set_output_delay -clock clk -min 0.100' in xdc
checks['routed_checkpoint_saved'] = (d / (stem + '.dcp')).is_file()
files = [p / 'source_binding.json', d / 'run.tcl', d / 'scope.json', d / 'route_status.rpt'] + sorted(d.glob(stem + '*'))
hashes = {}
for f in files:
    h = hashlib.sha256()
    with f.open('rb') as stream:
        for part in iter(lambda: stream.read(8 << 20), b''):
            h.update(part)
    hashes[str(f.relative_to(p))] = h.hexdigest()
result = {'all_mechanical_checks_pass': all(checks.values()), 'checks': checks,
          'version': version, 'top': binding['top'], 'tested_period_ns': period,
          'setup_ns': wns, 'hold_ns': whs, 'pulse_width_ns': wpws,
          'route_counts': counts, 'methodology_rules': methodology, 'DRC_rules': drc,
          'evidence_sha256': hashes, 'board_measured': False,
          'scope': 'saved routed physical context only; separate source/functional and scope review still required'}
out.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k != 'evidence_sha256'}, indent=2))
sys.exit(not result['all_mechanical_checks_pass'])

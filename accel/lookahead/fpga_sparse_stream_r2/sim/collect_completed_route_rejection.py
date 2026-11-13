"""Preserve completed, illegally routed impl_1 reports without assigning a clock.

Usage: SCRIPT MCP_TERMINAL_JSON TAG
The input contains status captured immediately after the failed STA source and a
separate read-only run-status query. This collector never invokes Vivado.
"""
from pathlib import Path
import datetime
import hashlib
import json
import re
import sys

root = Path(__file__).resolve().parents[4]
results = root / 'results/fpga_sparse_stream_r2_20261112'


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def write_new(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


input_path = Path(sys.argv[1]).resolve()
tag = sys.argv[2]
assert re.fullmatch(r'[A-Za-z0-9_]+', tag)
for item in json.loads(input_path.read_text()):
    variant, status = item['variant'], item['status']
    assert re.fullmatch(r'[A-Za-z0-9_]+', variant)
    assert not status['is_command_running'] and status['last_completed_code'] == 1
    assert status['last_completed'].startswith('source ')
    assert item['run_query']['exit_code'] == 0
    run_status = item['run_query']['output'].strip()
    assert run_status == 'route_design Complete, Failed Timing & Nets!'
    p = results / 'timing' / variant
    run = p / 'project' / (variant + '.runs') / 'impl_1'
    sta = p / 'routed_sta_v2'
    log = (run / 'runme.log').read_text()
    ended = re.findall(r'Exiting Vivado at (.*?)\.\.\.', log)
    assert ended and not (sta / 'tested_periods.csv').exists()
    route = (run / 'route_status.rpt').read_text()
    def count(label):
        return int(re.search(re.escape(label) + r'\.*\s*:\s*(\d+)', route)[1])
    routable = count('# of routable nets')
    routed = count('# of fully routed nets')
    errors = count('# of nets with routing errors')
    conflicts = count('# of nets with resource conflicts')
    assert errors > 0 and conflicts == errors and routed + errors == routable
    binding = json.loads((p / 'source_binding.json').read_text())
    sources = binding['source_sha256']
    assert all(sha(p / 'source' / name) == digest for name, digest in sources.items())
    util = (run / 'routed_utilization.rpt').read_text()
    row = next(line for line in util.splitlines() if line.split('|')[1:2] and
               line.split('|')[1].strip() == binding['top'])
    columns = [c.strip() for c in row.split('|')[1:-1]]
    assert len(columns) == 11 and columns[1] == '(top)'
    resources = dict(zip(['LUT', 'FF', 'RAMB36', 'RAMB18', 'URAM'],
                        [int(columns[n]) for n in [2, 6, 7, 8, 9]]))
    timing = (run / 'routed_timing.rpt').read_text()
    slacks = re.search(r'WNS\(ns\).*?\n\s*[- ]+\n([^\n]+)', timing, re.S)[1].split()
    assert len(slacks) == 12
    checks = dict(re.findall(r'checking ([a-z_]+) \((\d+)\)', (run / 'check_timing.rpt').read_text()))
    drc = (run / 'drc.rpt').read_text()
    drc_rules = re.findall(r'^\|\s*(RTSTAT-\d+)\s*\|\s*([^|]+?)\s*\|', drc, re.M)
    assert any(severity == 'Critical Warning' for _, severity in drc_rules)
    dcp = run / (binding['top'] + '_routed.dcp')
    parent = sta / ('parent_termination_' + tag + '.log')
    source_log = Path(status['log_file']).read_bytes()
    assert b'route did not complete: route_design Complete, Failed Timing & Nets!' in source_log
    with parent.open('xb') as stream:
        stream.write(source_log)
    evidence = [run / f for f in ['route_status.rpt', 'drc.rpt', 'routed_timing.rpt',
                'routed_utilization.rpt', 'check_timing.rpt', 'runme.log', 'methodology.rpt']]
    evidence += [p / 'source_binding.json', parent, sta / 'run.tcl', sta / 'scope.json']
    overlaps = re.findall(r'Design is not legally routed\. There are (\d+) node overlaps\.', log)
    final_counts = re.findall(r'Number of Node Overlaps\s*=\s*(\d+)', log)
    assert overlaps and final_counts and overlaps[-1] == final_counts[-1]
    review = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), variant=variant,
        scope='completed full32 OOC negative; illegal route, no assigned clock', clock_qualified=False,
        routable_nets=routable, fully_routed_nets=routed, nets_with_resource_conflicts=conflicts,
        route_node_overlaps=int(overlaps[-1]), DRC_rules=drc_rules, period_ns=binding['clock_ns'],
        setup_slack_ns=float(slacks[0]), hold_slack_ns=float(slacks[4]), pulse_width_slack_ns=float(slacks[8]),
        check_timing_12_categories_zero=len(checks) == 12 and all(int(v) == 0 for v in checks.values()),
        actual_physical_resources=resources, child_completed=True, child_exit_log_time=ended[-1],
        parent_session=item['session'], parent_source_exit_code=1,
        parent_source_elapsed_s=status['last_completed_elapsed'], run_status=run_status,
        frozen_source_files_rehashed=len(sources), source_sha256=sources,
        evidence_sha256={str(x.relative_to(p)): sha(x) for x in evidence},
        MCP_terminal_input=dict(path=str(input_path.relative_to(results)), sha256=sha(input_path)),
        collector_sha256=sha(Path(__file__)),
        routed_DCP=dict(path=str(dcp.relative_to(results)), bytes=dcp.stat().st_size, sha256=sha(dcp),
                        retained_on_shared_filesystem_not_git_blob=True),
        slower_periods_not_tested_ns=[x for x in json.loads((sta / 'scope.json').read_text())['periods_ns']
                                     if x != binding['clock_ns']],
        why_no_additional_clock_scan='illegal route; parent gate stopped before open_run/period loop',
        command_exit_caution='child command completion is not legal routing or clock qualification',
        decision='retain negative evidence; independent repaired candidates continue', board_measured=False)
    output = p / ('completed_route_rejection_' + tag + '.json')
    write_new(output, review)
    write_new(sta / ('termination_review_' + tag + '.json'), dict(parent_source_exit_code=1,
        reason='route did not complete: ' + run_status, tested_periods_file_exists=False,
        source_log_snapshot=str(parent.relative_to(p)), source_log_sha256=sha(parent),
        review=str(output.relative_to(results)), clock_qualified=False))
    print(json.dumps({key: review[key] for key in ['variant', 'nets_with_resource_conflicts',
        'route_node_overlaps', 'setup_slack_ns', 'hold_slack_ns', 'actual_physical_resources',
        'frozen_source_files_rehashed', 'clock_qualified']}), flush=True)

"""Prepare a resumable STA sweep of one actual routed synchronous context.

Run the emitted Tcl through the existing Vivado session. It waits for the
already launched implementation, preserves the original reports, and saves
separate reports/checkpoints at each explicitly tested period. It never emits
timing exceptions or removes IO constraints. Qualification requires subsequent
review of setup, hold, unconstrained paths, route status and methodology.
"""
from pathlib import Path
import json, sys

root = Path(__file__).resolve().parents[4]
p = root / 'results/fpga_sparse_stream_r2_20261112/timing' / sys.argv[1]
periods = [float(x) for x in sys.argv[2:] if not x.startswith('--tag=')] or [5.0, 8.0, 10.0]
tag = next((x.split('=', 1)[1] for x in sys.argv[2:] if x.startswith('--tag=')), 'routed_sta')
if not tag.startswith('routed_sta') or '/' in tag:
    raise ValueError('local routed_sta tag required')
binding = json.loads((p / 'source_binding.json').read_text())
if not binding.get('context_resource_overhead_included'):
    raise RuntimeError('requires the actual synchronous launch/capture context')
out = p / tag
out.mkdir(exist_ok=False)
commands = [
    'wait_on_run impl_1',
    'set r2_sta_run_status [get_property STATUS [get_runs impl_1]]',
    'if {$r2_sta_run_status ne "route_design Complete!" && $r2_sta_run_status ne "route_design Complete, Failed Timing!"} {error "route did not complete: $r2_sta_run_status"}',
    'open_run impl_1',
    'if {[get_property TOP [current_fileset]] ne {' + binding['top'] + '}} {error "wrong project/top"}',
    'report_route_status -file {' + str(out / 'route_status.rpt') + '}',
    'report_utilization -hierarchical -file {' + str(out / 'routed_utilization.rpt') + '}',
    'report_ram_utilization -file {' + str(out / 'routed_ram.rpt') + '}',
    'set r2_sta_fd [open {' + str(out / 'tested_periods.csv') + '} w]',
    'puts $r2_sta_fd "period_ns,setup_slack_ns,hold_slack_ns,qualification"',
]
for period in periods:
    if period <= 0:
        raise ValueError('positive period required')
    stem = out / ('p' + str(round(period * 1000)) + 'ps')
    commands += [
        f'create_clock -name clk -period {period:.6f} [get_ports clk]',
        'report_clocks -file {' + str(stem) + '_clocks.rpt}',
        'report_timing_summary -delay_type min_max -report_unconstrained -file {' + str(stem) + '_timing.rpt}',
        'report_timing -delay_type max -max_paths 20 -file {' + str(stem) + '_setup.rpt}',
        'report_timing -delay_type min -max_paths 20 -file {' + str(stem) + '_hold.rpt}',
        'check_timing -verbose -file {' + str(stem) + '_check_timing.rpt}',
        'report_methodology -file {' + str(stem) + '_methodology.rpt}',
        'report_drc -file {' + str(stem) + '_drc.rpt}',
        'set r2_sta_setup [get_property SLACK [lindex [get_timing_paths -delay_type max -max_paths 1] 0]]',
        'set r2_sta_hold [get_property SLACK [lindex [get_timing_paths -delay_type min -max_paths 1] 0]]',
        f'puts $r2_sta_fd "{period},$r2_sta_setup,$r2_sta_hold,pending_report_review"',
        'flush $r2_sta_fd',
        'write_checkpoint {' + str(stem) + '.dcp}',
        'write_xdc {' + str(stem) + '.xdc}',
    ]
commands += ['close $r2_sta_fd', 'puts R2_ROUTED_STA_COMPLETE_PENDING_REVIEW']
(out / 'run.tcl').write_text('\n'.join(commands) + '\n')
(out / 'scope.json').write_text(json.dumps({
    'periods_ns': periods, 'same_actual_routed_netlist': True,
    'source_binding': str(p / 'source_binding.json'),
    'board_measured': False, 'timing_exceptions_added': False,
    'IO_constraints_removed': False, 'qualification': 'pending_report_review',
}, indent=2))
print(out / 'run.tcl')

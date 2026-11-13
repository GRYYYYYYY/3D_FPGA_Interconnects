"""Freeze a completed placement DCP while its original route continues.

Usage: VARIANT NEW_TAG. Waits only for Vivado's exact checkpoint completion
marker, copies and hashes it, then emits read-only report Tcl for another idle
session. No placement, routing, timing exceptions or clock changes are issued.
"""
from pathlib import Path
import datetime, hashlib, json, re, shutil, sys, time

root = Path(__file__).resolve().parents[4]
r = root / 'results/fpga_sparse_stream_r2_20261112'
variant, tag = sys.argv[1:3]
assert all(re.fullmatch(r'[A-Za-z0-9_]+', x) for x in [variant, tag])
p = r / 'timing' / variant
binding = json.loads((p / 'source_binding.json').read_text())
run = next(p.glob('project/*.runs/impl_1'))
source = run / (binding['top'] + '_placed.dcp')
marker = "The checkpoint '" + str(source) + "' has been generated."
d = p / tag
d.mkdir(exist_ok=False)
state = dict(variant=variant, source=str(source), status='waiting_for_completed_placement',
             started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
             scope='placement diagnosis only; original implementation untouched; no routed clock')
receipt = d / 'receipt.json'

def save():
    receipt.write_text(json.dumps(state, indent=2) + '\n')

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()

save()
while True:
    text = (run / 'runme.log').read_text()
    if marker in text:
        break
    if 'Exiting Vivado' in text:
        state['status'] = 'source_run_ended_without_completed_placement'
        save()
        raise RuntimeError(state['status'])
    time.sleep(10)

h = digest(source)
copy = d / 'input_placed.dcp'
shutil.copyfile(source, copy)
assert h == digest(copy) == digest(source), 'source checkpoint changed while copying'
(d / 'source_log_at_capture.log').write_text(text)
shutil.copyfile(p / 'source_binding.json', d / 'source_binding.json')
commands = [f'open_checkpoint {{{copy}}}',
            'if {[llength [get_clocks clk]] != 1} {error "missing placed clock"}',
            f'report_clocks -file {{{d / "placed_clocks.rpt"}}}',
            f'report_design_analysis -congestion -file {{{d / "congestion.rpt"}}}',
            f'report_utilization -slr -file {{{d / "utilization_slr.rpt"}}}',
            f'report_utilization -hierarchical -file {{{d / "utilization_hier.rpt"}}}',
            f'report_timing_summary -delay_type min_max -report_unconstrained -file {{{d / "placed_timing.rpt"}}}',
            f'report_timing -delay_type max -max_paths 20 -file {{{d / "placed_setup.rpt"}}}',
            f'report_route_status -file {{{d / "route_status.rpt"}}}',
            f'check_timing -verbose -file {{{d / "check_timing.rpt"}}}',
            f'write_xdc {{{d / "constraints.xdc"}}}']
(d / 'run.tcl').write_text('\n'.join(commands) + '\n')
state.update(status='input_frozen_reports_not_run', input_sha256=h,
             input_bytes=copy.stat().st_size,
             source_binding_sha256=digest(d / 'source_binding.json'),
             captured_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
save()
print('PLACEMENT_INPUT_FROZEN', variant, tag, h, flush=True)

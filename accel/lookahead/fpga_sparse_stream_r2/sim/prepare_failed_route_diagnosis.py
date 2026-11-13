"""Copy a completed failed-route checkpoint for read-only physical diagnosis.

Usage: VARIANT NEW_TAG. The original implementation must have exited and its
error checkpoint must have a completion marker. No run reset, placement, route,
clock change or timing exception is issued. These reports cannot qualify a clock.
"""
from pathlib import Path
import datetime
import hashlib
import json
import re
import shutil
import sys

root = Path(__file__).resolve().parents[4]
r = root / 'results/fpga_sparse_stream_r2_20261112'
variant, tag = sys.argv[1:3]
assert all(re.fullmatch(r'[A-Za-z0-9_]+', x) for x in [variant, tag])
p = r / 'timing' / variant
binding = json.loads((p / 'source_binding.json').read_text())
run = next(p.glob('project/*.runs/impl_1'))
source = run / (binding['top'] + '_routed_error.dcp')
text = (run / 'runme.log').read_text()
assert 'Exiting Vivado' in text, 'original child run is still active'
assert 'route_design failed' in text, 'not a failed route'
assert "The checkpoint '" + str(source) + "' has been generated." in text, 'error DCP incomplete'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


d = p / tag
d.mkdir(exist_ok=False)
h = digest(source)
copy = d / 'input_failed_route.dcp'
shutil.copyfile(source, copy)
assert h == digest(copy) == digest(source), 'source changed during capture'
(d / 'source_log_at_capture.log').write_text(text)
shutil.copyfile(p / 'source_binding.json', d / 'source_binding.json')
commands = [f'open_checkpoint {{{copy}}}',
            f'report_route_status -file {{{d / "route_status.rpt"}}}',
            f'report_design_analysis -congestion -file {{{d / "congestion.rpt"}}}',
            f'report_utilization -slr -file {{{d / "utilization_slr.rpt"}}}',
            f'report_utilization -hierarchical -file {{{d / "utilization_hier.rpt"}}}',
            f'report_drc -file {{{d / "drc.rpt"}}}',
            f'report_clocks -file {{{d / "clocks.rpt"}}}',
            f'write_xdc {{{d / "constraints.xdc"}}}',
            'puts R2_FAILED_ROUTE_DIAGNOSIS_COMPLETE_NO_CLOCK_QUALIFICATION']
(d / 'run.tcl').write_text('\n'.join(commands) + '\n')
state = dict(variant=variant, source=str(source), input_sha256=h,
             input_bytes=copy.stat().st_size,
             source_binding_sha256=digest(d / 'source_binding.json'),
             captured_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
             status='input_frozen_reports_not_run', clock_qualified=False,
             original_error_lines=[line for line in text.splitlines() if line.startswith('ERROR:')],
             scope='failed physical route diagnosis only; source run untouched; no frequency qualification')
(d / 'receipt.json').write_text(json.dumps(state, indent=2) + '\n')
print('FAILED_ROUTE_INPUT_FROZEN', variant, tag, h)

#!/usr/bin/env python3
"""Freeze full-core source and reproducible project-mode OOC flow."""
import argparse,json,hashlib,datetime
from pathlib import Path
from sources import ROOT,closure
p=argparse.ArgumentParser();p.add_argument('out');p.add_argument('--period',type=float,default=5)
p.add_argument('--no-timing-driven',action='store_true',help='Resource diagnostic only: disable timing-driven synthesis; retain XDC and require actual route qualification separately')
a=p.parse_args()
out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True);src=out/'source';src.mkdir(exist_ok=False)
files=closure();binding={}
for f in files:
    b=(ROOT/f).read_bytes();(src/Path(f).name).write_bytes(b);binding[f]=hashlib.sha256(b).hexdigest()
(out/'binding.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':binding,'top':'cp_full_top','part':'xcu280-fsvh2892-2L-e','period_ns':a.period,'scope':'full_core_OOC_without_platform_shell','requires_gpu_win':False,'timing_driven_synthesis':not a.no_timing_driven},indent=2)+'\n')
(out/'clock.xdc').write_text(f'''create_clock -name core_clock -period {a.period:.6f} [get_ports clk]
set_clock_uncertainty 0.100 [get_clocks core_clock]
set_input_delay -clock core_clock -max 0.800 [get_ports -filter {{DIRECTION == IN && NAME != clk}}]
set_input_delay -clock core_clock -min 0.100 [get_ports -filter {{DIRECTION == IN && NAME != clk}}]
set_output_delay -clock core_clock -max 0.800 [get_ports -filter {{DIRECTION == OUT}}]
set_output_delay -clock core_clock -min 0.100 [get_ports -filter {{DIRECTION == OUT}}]
''')
lines=[f'create_project cp_full {{{out}/project}} -part xcu280-fsvh2892-2L-e','set_param general.maxThreads 8']
lines += [f'add_files {{{src/Path(f).name}}}' for f in files]
lines += [f'add_files -fileset constrs_1 {{{out}/clock.xdc}}','set_property top cp_full_top [current_fileset]','set_property verilog_define {} [current_fileset]','set_property -name {STEPS.SYNTH_DESIGN.ARGS.MORE OPTIONS} -value {-mode out_of_context} -objects [get_runs synth_1]','set_property STEPS.SYNTH_DESIGN.ARGS.FLATTEN_HIERARCHY rebuilt [get_runs synth_1]','update_compile_order -fileset sources_1']
(out/'setup.tcl').write_text('\n'.join(lines)+'\n')
if a.no_timing_driven:
    with (out/'setup.tcl').open('a') as f:
        f.write('set_property -name {STEPS.SYNTH_DESIGN.ARGS.MORE OPTIONS} -value {-mode out_of_context -no_timing_driven} -objects [get_runs synth_1]\n')
(out/'synth_reports.tcl').write_text(f'''open_run synth_1
report_utilization -file {{{out}/utilization.rpt}}
report_utilization -hierarchical -hierarchical_depth 4 -file {{{out}/hierarchy.rpt}}
report_timing_summary -delay_type min_max -report_unconstrained -file {{{out}/synth_timing.rpt}}
report_drc -file {{{out}/synth_drc.rpt}}
write_checkpoint -force {{{out}/full_synth.dcp}}
set fp [open {{{out}/blackboxes.txt}} w]
puts $fp [get_cells -hierarchical -filter {{IS_BLACKBOX == 1}}]
close $fp
''')
print(out)

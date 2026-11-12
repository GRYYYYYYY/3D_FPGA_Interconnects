"""Freeze an OOC project with an actual registered synchronous partner context."""
from pathlib import Path
import hashlib,json,shutil,sys
root=Path(__file__).resolve().parents[4];s=root/'accel/lookahead/fpga_sparse_stream_r2'
variant,top=sys.argv[1:3];period=float(sys.argv[3]) if len(sys.argv)>3 else 5.0
p=root/'results/fpga_sparse_stream_r2_20261112/timing'/variant;p.mkdir(exist_ok=False);f=p/'source';f.mkdir()
for x in [*s.glob('rtl/*.sv'),s/'physical_context'/(top+'.sv')]:shutil.copy2(x,f/x.name)
(f/'tile_ooc.xdc').write_text(f'create_clock -name clk -period {period:.6f} [get_ports clk]\nset_output_delay -clock clk -max 0.500 [get_ports signature*]\nset_output_delay -clock clk -min 0.100 [get_ports signature*]\n')
(f/'synth_pre.tcl').write_text('set_param general.maxThreads 8\n')
(f/'synth_post.tcl').write_text('if {[llength [get_clocks]]==0} {read_xdc {'+str(f/'tile_ooc.xdc')+'}}\nreport_clocks -file synth_clocks.rpt\nreport_utilization -hierarchical -file synth_utilization.rpt\nreport_ram_utilization -file ram_utilization.rpt\nreport_timing_summary -delay_type min_max -report_unconstrained -file synth_timing.rpt\n')
(f/'route_post.tcl').write_text('report_utilization -hierarchical -file routed_utilization.rpt\nreport_ram_utilization -file routed_ram.rpt\nreport_timing_summary -delay_type min_max -report_unconstrained -file routed_timing.rpt\nreport_timing -delay_type max -max_paths 20 -file setup_paths.rpt\nreport_timing -delay_type min -max_paths 20 -file hold_paths.rpt\nreport_route_status -file route_status.rpt\nreport_drc -file drc.rpt\ncheck_timing -verbose -file check_timing.rpt\nreport_methodology -file methodology.rpt\n')
lines=['create_project '+variant+' {'+str(p/'project')+'} -part xcu280-fsvh2892-2L-e',
       'add_files [glob {'+str(f/'*.sv')+'}]','set_property top '+top+' [current_fileset]',
       'add_files -fileset constrs_1 {'+str(f/'tile_ooc.xdc')+'}',
       'set_property -name {STEPS.SYNTH_DESIGN.ARGS.MORE OPTIONS} -value {-mode out_of_context} -objects [get_runs synth_1]']
for step,hook,filename,run in [('SYNTH_DESIGN','PRE','synth_pre.tcl','synth_1'),('SYNTH_DESIGN','POST','synth_post.tcl','synth_1'),('ROUTE_DESIGN','POST','route_post.tcl','impl_1')]:
 lines.append('set_property STEPS.'+step+'.TCL.'+hook+' {'+str(f/filename)+'} [get_runs '+run+']')
lines.append('update_compile_order -fileset sources_1');(p/'setup.tcl').write_text('\n'.join(lines)+'\n')
(p/'source_binding.json').write_text(json.dumps({'top':top,'scope':'physical synchronous registered partner context; actual BUFG inside; not shell, board or functional stimulus','input_contract':'all DUT inputs driven by real same-clock launch registers; context top has only clock input','clock_ns':period,'clock_buffer_site':'BUFGCE_X0Y144','context_resource_overhead_included':True,'source_sha256':{x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in f.iterdir()}},indent=2))
print(p)

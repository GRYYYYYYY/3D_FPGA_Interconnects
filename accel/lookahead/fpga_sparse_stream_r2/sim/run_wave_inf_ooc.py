"""Vivado 2022.2 nonproject fallback after MCP parent process abort; new output only."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys,os
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_r2_20261112';tag=sys.argv[1];d=r/'timing'/tag;d.mkdir(exist_ok=False);(d/'source').mkdir()
source=r/'accumulator/rtl_micro_ram_d/source/wave_inf_bank.sv';(d/'source/wave_inf_bank.sv').write_bytes(source.read_bytes())
script='''set d [file dirname [info script]]
set_param general.maxThreads 4
read_verilog -sv [file join $d source wave_inf_bank.sv]
synth_design -top wave_inf_owner -part xcu280-fsvh2892-2L-e -mode out_of_context
create_clock -name clk -period 5.000 [get_ports clk]
report_utilization -hierarchical -file [file join $d synthesis_utilization.rpt]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $d synthesis_timing.rpt]
write_checkpoint [file join $d synthesized.dcp]
opt_design
place_design
phys_opt_design
route_design
report_route_status -file [file join $d route_status.rpt]
report_utilization -hierarchical -file [file join $d routed_utilization.rpt]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $d routed_timing.rpt]
report_methodology -file [file join $d methodology.rpt]
report_drc -file [file join $d drc.rpt]
write_checkpoint [file join $d routed.dcp]
'''
(d/'run.tcl').write_text(script)
cmd=['/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin/vivado','-mode','batch','-source',str(d/'run.tcl'),'-log',str(d/'vivado.log'),'-journal',str(d/'vivado.jou')]
(d/'source_binding.json').write_text(json.dumps({'source_sha256':{'wave_inf_bank.sv':hashlib.sha256(source.read_bytes()).hexdigest()},'script_sha256':hashlib.sha256(script.encode()).hexdigest(),'command':cmd,'LD_PRELOAD':'/usr/lib/x86_64-linux-gnu/libudev.so.1','scope':'two subbanks only; OOC internal clock, not full kernel clock; no board'},indent=2)+'\n')
env=os.environ.copy();env['LD_PRELOAD']='/usr/lib/x86_64-linux-gnu/libudev.so.1'
with (d/'console.log').open('x') as log:rc=subprocess.run(cmd,cwd=d,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
(d/'terminal.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'returncode':rc,'board_measured':False},indent=2)+'\n');sys.exit(rc)

set root [file normalize [file join [file dirname [info script]] ../../../..]]
set out $root/results/fpga_descriptor_front_20261114/$df_out
if {[llength [get_projects -quiet]]} {close_project}
create_project df_leaf $out/project -part xcu280-fsvh2892-2L-e
add_files [glob $root/accel/lookahead/fpga_descriptor_front/front/df_*.sv]
add_files -fileset sim_1 $root/accel/lookahead/fpga_descriptor_front/front/${df_tb}.sv
add_files -fileset sim_1 [glob $out/*.hex]
set_property top $df_tb [get_filesets sim_1]
set_property generic L=$df_lanes [get_filesets sim_1]
set_property target_simulator XSim [current_project]
set_property xsim.simulate.runtime 300us [get_filesets sim_1]
update_compile_order -fileset sim_1
launch_simulation
close_sim

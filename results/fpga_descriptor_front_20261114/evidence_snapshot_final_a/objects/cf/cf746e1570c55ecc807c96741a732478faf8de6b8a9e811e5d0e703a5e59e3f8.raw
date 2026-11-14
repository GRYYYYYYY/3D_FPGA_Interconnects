set root [file normalize [file join [file dirname [info script]] ../../../..]]
set src $root/accel/lookahead/fpga_descriptor_front/output
set out [pwd]
create_project ack $out/project -part xcu280-fsvh2892-2L-e -force
set_property target_simulator XSim [current_project]
add_files $src/df_ack_collector.sv
add_files -fileset sim_1 $src/tb_ack.sv
set_property top df_ack_collector [get_filesets sources_1]
set_property top tb_ack [get_filesets sim_1]
set_property xsim.simulate.runtime 100us [get_filesets sim_1]
update_compile_order -fileset sim_1
file mkdir $out/project/ack.sim/sim_1/behav/xsim
file copy -force $out/ack.vec $out/project/ack.sim/sim_1/behav/xsim/ack.vec
launch_simulation -simset sim_1 -mode behavioral
close_sim

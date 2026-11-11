set root [file normalize [file join [file dirname [info script]] ../../../..]]
set src $root/accel/lookahead/fpga_sim_restart
set result $root/results/fpga_sim_restart_20261111T231000Z
create_project owner_sim $result/xsim_project -part xcu280-fsvh2892-2L-e -force
add_files $src/rtl/owner_service.sv
add_files -fileset sim_1 $src/tb/owner_tb.sv
set_property top owner_tb [get_filesets sim_1]
set_property xsim.simulate.runtime all [get_filesets sim_1]
set_property -name xsim.simulate.xsim.more_options -value "-testplusarg DIR=$result/directed" -objects [get_filesets sim_1]
update_compile_order -fileset sim_1
launch_simulation

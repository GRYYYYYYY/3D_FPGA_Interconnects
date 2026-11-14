set root [file normalize [file join [file dirname [info script]] ../../../..]]
set out $root/results/fpga_descriptor_front_20261114/front_sim_a
create_project df_front $out/project -part xcu280-fsvh2892-2L-e -force
add_files [glob $root/accel/lookahead/fpga_descriptor_front/front/df_*.sv]
add_files -fileset sim_1 $root/accel/lookahead/fpga_descriptor_front/front/tb_pair.sv
add_files -fileset sim_1 $out/arith.hex
set_property top tb_pair [get_filesets sim_1]
set_property target_simulator XSim [current_project]
set_property xsim.simulate.runtime 100us [get_filesets sim_1]
update_compile_order -fileset sim_1
launch_simulation
close_sim

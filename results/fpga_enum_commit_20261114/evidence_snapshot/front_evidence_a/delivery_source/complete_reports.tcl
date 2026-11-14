set root [file normalize [file join [file dirname [info script]] ../../../..]]
set out $root/results/fpga_enum_commit_20261114/front_ooc_e
open_checkpoint $out/route.dcp
puts CHECK_TIMING_BEGIN
puts [check_timing -verbose]
puts CHECK_TIMING_END
write_xdc -force -exclude_physical $out/constraints.xdc
puts FRONT_REPORT_RECOVERY_COMPLETE

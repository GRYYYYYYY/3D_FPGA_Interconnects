set root [file normalize [file join [file dirname [info script]] ../../../..]]
set out $root/results/fpga_enum_commit_20261114/front_ooc_d
redirect -file $out/check_timing.rpt {check_timing -verbose}
report_drc -file $out/drc.rpt
report_methodology -file $out/methodology_post.rpt
write_xdc -force -exclude_physical $out/constraints.xdc

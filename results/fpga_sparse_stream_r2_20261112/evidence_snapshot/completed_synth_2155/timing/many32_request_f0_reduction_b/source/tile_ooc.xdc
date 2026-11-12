create_clock -name clk -period 5.000000 [get_ports clk]
set_output_delay -clock clk -max 0.500 [get_ports signature*]
set_output_delay -clock clk -min 0.100 [get_ports signature*]

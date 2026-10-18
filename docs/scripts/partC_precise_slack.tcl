# Part C helper: worst setup slack at full precision (sta/sta.tcl prints it with 2 decimals).
# Same library, netlist and constraints as sta/sta.tcl. Run from the repo root:
#   sta -no_splash docs/scripts/partC_precise_slack.tcl                    # T = 10 ns
#   STA_PERIOD=2.79 sta -no_splash docs/scripts/partC_precise_slack.tcl    # T = T_min

set lib $::env(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
if {[info exists ::env(STA_PERIOD)]} { set T $::env(STA_PERIOD) } else { set T 10.0 }

read_liberty $lib
read_verilog synth/mult_array_netlist.v
link_design mult_array
create_clock -name clk -period $T [get_ports clk]
set_input_delay 1.0 -clock clk [delete_from_list [all_inputs] [get_ports clk]]
set_output_delay 1.0 -clock clk [all_outputs]
report_worst_slack -max -digits 6
exit

#!/usr/bin/env bash
# Part C extra: which critical-path cells come from which full adders?
# Run INSIDE the container from the repo root:   eda bash docs/scripts/partC_net_correspondence.sh
# Output: docs/logs/partC/net_correspondence.log   (scratch files in a temp dir; repo untouched)
set -eu
W=$(mktemp -d)
CELLS=$PDK_ROOT/sky130A/libs.ref/sky130_fd_sc_hd/verilog
S=docs/scripts/partC_net_correspondence.py
python3 -I $S gen synth/mult_array_netlist.v $W/tb_gate.v $W/tb_rtl.v $W/names.txt
iverilog -g2012 -DFUNCTIONAL -DUNIT_DELAY=#1 -o $W/g $W/tb_gate.v $CELLS/primitives.v $CELLS/sky130_fd_sc_hd.v synth/mult_array_netlist.v
iverilog -g2012 -o $W/r $W/tb_rtl.v rtl/full_adder.v rtl/mult_array.v
vvp -n $W/g > $W/gate.out
vvp -n $W/r > $W/rtl.out
python3 -I $S match $W/names.txt $W/gate.out $W/rtl.out | tee docs/logs/partC/net_correspondence.log
rm -rf "$W"

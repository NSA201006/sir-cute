#!/usr/bin/env bash
# TB-strength experiment (beyond the spec), run INSIDE the container from the repo root:
#     eda bash docs/scripts/tb_latency_mutants.sh
# Runs the repo tb/tb_mult.v (unmodified) against throwaway mutants of mult_array with
# latency 0, 1 and 3 (instead of 2). A testbench that truly checks the 2-cycle latency
# must print FAIL for all three. Mutants live in /tmp inside the container only;
# nothing is written to the repo. They use '*' on purpose: they are test fixtures, not deliverables.
set -u
W=$(mktemp -d)

cat > "$W/lat0.v" <<'EOF'
module mult_array(input clk, input rst_n, input [3:0] a, input [3:0] b, output [7:0] p);
  assign p = a * b;                       // latency 0 (combinational)
endmodule
EOF

cat > "$W/lat1.v" <<'EOF'
module mult_array(input clk, input rst_n, input [3:0] a, input [3:0] b, output reg [7:0] p);
  always @(posedge clk or negedge rst_n)  // latency 1 (output register only)
    if (!rst_n) p <= 8'd0; else p <= a * b;
endmodule
EOF

cat > "$W/lat3.v" <<'EOF'
module mult_array(input clk, input rst_n, input [3:0] a, input [3:0] b, output reg [7:0] p);
  reg [3:0] a_r, b_r; reg [7:0] m;        // latency 3 (one extra stage)
  always @(posedge clk or negedge rst_n)
    if (!rst_n) begin a_r <= 0; b_r <= 0; m <= 0; p <= 0; end
    else begin a_r <= a; b_r <= b; m <= a_r * b_r; p <= m; end
endmodule
EOF

cd "$W"
for m in lat0 lat1 lat3; do
  iverilog -g2012 -o "sim_$m" "$OLDPWD/tb/tb_mult.v" "$m.v" </dev/null 2>&1
  printf '%-5s -> %s\n' "$m" "$(vvp -n "sim_$m" </dev/null 2>&1 | grep -E '^(PASS|FAIL):')"
done
rm -rf "$W"

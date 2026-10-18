#!/usr/bin/env bash
# Part A verification suite. Run INSIDE the container from the repo root:
#     eda bash docs/scripts/partA_checks.sh
# Each check writes its own log to docs/logs/partA/. The repo sources are never modified
# (fault injection and mutants are built in /tmp inside the container).
set -u
L=docs/logs/partA
mkdir -p "$L"

echo "== 1. spec RTL simulation (verbatim spec section 6 task 4)"
{ set -x
  iverilog -g2012 -o sim tb/tb_mult.v rtl/full_adder.v rtl/mult_array.v
  vvp sim
  { set +x; } 2>/dev/null
} > "$L/rtl_sim.log" 2>&1 </dev/null
grep -E "^(PASS|FAIL):" "$L/rtl_sim.log"

echo "== 2. fault injection, sum = a ^ b (spec section 6 task 6), on a temp copy"
F=$(mktemp -d)
{ set -x
  sed "s/assign sum = a ^ b ^ cin;/assign sum = a ^ b;/" rtl/full_adder.v > "$F/full_adder.v"
  diff rtl/full_adder.v "$F/full_adder.v"
  iverilog -g2012 -o "$F/sim_fault" tb/tb_mult.v "$F/full_adder.v" rtl/mult_array.v
  (cd "$F" && vvp -n sim_fault)
  { set +x; } 2>/dev/null
} > "$L/fault_injection.log" 2>&1 </dev/null
echo "MISMATCH lines: $(grep -c MISMATCH "$L/fault_injection.log")" >> "$L/fault_injection.log"
grep -E "^(PASS|FAIL):" "$L/fault_injection.log"; rm -rf "$F"

echo "== 3. Verilator lint, all warnings enabled"
{ set -x
  verilator --lint-only -Wall --top-module mult_array rtl/full_adder.v rtl/mult_array.v
  echo "verilator exit=$?"
  { set +x; } 2>/dev/null
} > "$L/verilator_lint.log" 2>&1 </dev/null
grep -E "verilator exit=|%Warning|%Error" "$L/verilator_lint.log"

echo "== 4. Yosys structure (pre-flatten hierarchy, then generic synth)"
yosys -p "read_verilog rtl/full_adder.v rtl/mult_array.v; hierarchy -check -top mult_array; proc; opt_clean; \
          stat; synth -top mult_array -flatten; stat" \
      > "$L/yosys_structure.log" 2>&1 </dev/null
echo "yosys exit=$?" | tee -a "$L/yosys_structure.log"

echo "== 5. TB strength: repo TB vs latency-0/1/3 mutants"
bash docs/scripts/tb_latency_mutants.sh > "$L/tb_latency_mutants.log" 2>&1 </dev/null
cat "$L/tb_latency_mutants.log"

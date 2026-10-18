# Part B: logic synthesis with Yosys. Decisions and results

Inputs: fixed RTL (see partA doc §3A). Tool: Yosys 0.70 in IIC-OSIC-TOOLS 2026.10.
Library: `sky130_fd_sc_hd__tt_025C_1v80.lib`. Logs: `docs/logs/partB/`.

## 1. Decisions

| Decision | Choice | Why |
|---|---|---|
| Script content | Exactly the 7 spec steps, in order, each as `yosys <command>` | Graded script; spec §7 |
| `$lib` | `$::env(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib` | Spec §4.2 path; resolves to `/foss/pdks/...` in the container |
| Paths | Relative to the repo root; run as `yosys -c synth/synth.tcl` from the root | Matches the spec's run command and the paths in steps 1, 6, 7 |
| Cell exclusions (`dont_use`) | **None**, i.e. plain `abc -liberty $lib` as the spec says | Graded script. Consequence: 4 instances of LibreLane-excluded cells appear (see §4.3). Not changed; flagged |
| Extra analysis | In separate commands and logs only; `synth.tcl` is not extended | Keep the graded script exactly as specified |

## 2. Run
`yosys -c synth/synth.tcl` → `yosys exit=0` (`docs/logs/partB/yosys_synth.log`).
Generated: `synth/mult_array_netlist.v`, `synth/mult_array_stat.rpt`.

ABC messages (informational, from the log):
- `Detected 9 multi-output cells (for example, "sky130_fd_sc_hd__fa_1")`: **ABC cannot map to multi-output cells**, so SKY130's full-adder (`fa_*`) and half-adder (`ha_*`) cells are never used, even though the design is 12 full adders.
- `The network is combinational (run "fraig" or "fraig_sweep")`: normal for ABC's combinational mapping.

## 3. Part B results table (all values from `synth/mult_array_stat.rpt` unless noted)

| Metric | Value |
|---|---|
| Total number of cells | **61** |
| Number of flip-flops | **16** (`sky130_fd_sc_hd__dfrtp_1`) |
| Total cell area (µm²) | **756.976** |
| Flip-flop area (µm²) | **400.384** = 16 × 25.024 (liberty `area : 25.024` for `dfrtp_1`, `netlist_audit.log`) |
| Flip-flop area (% of total) | **52.89 %** (stat: "of which used for sequential elements: 400.384000 (52.89%)") |
| 3 most-used cell types | `dfrtp_1` × 16; `nand2_1` × 7; then a **tie** at 4: `and2_0` × 4 and `maj3_1` × 4 |
| Netlist simulation result | **`PASS: 256 vectors checked, 0 errors`** (`gls.log`; spec command verbatim, 0 warnings) |

Full cell list (stat): a21boi_0 ×1, a21oi_1 ×3, a22oi_1 ×2, and2_0 ×4, and3_1 ×1, and4_1 ×1, clkinv_1 ×2, dfrtp_1 ×16,
lpflow_isobufsrc_1 ×2, maj3_1 ×4, nand2_1 ×7, nand3_1 ×2, nand4_1 ×2, nor2_1 ×2, o2111ai_1 ×1, o21bai_1 ×1, o311ai_0 ×1,
xnor2_1 ×3, xnor3_1 ×1, xor2_1 ×2, xor3_1 ×3.

Derived (arithmetic on the values above, for report Q1): combinational cells = 61 − 16 = **45**, vs 16 AND + 12 FA = 28 RTL primitives.

## 4. Verification beyond the spec

### 4.1 Netlist audit (`netlist_audit.log`)
| Check | Result |
|---|---|
| Modules in netlist | 1 (`mult_array`); the full adders are flattened |
| SKY130 cell instances | 61 (= stat) |
| Generic or unmapped cells (`$_*`, `$scopeinfo`, `$lut`) | 0. The 12 `$scopeinfo` markers seen after generic synth (partA §3B) are gone |
| Latches | 0 |
| Flip-flops | 16 × `dfrtp_1` (D-FF, async active-low reset, Q output) |
| `assign` statements | 0 |
| Ports | `clk`, `rst_n`, `a[3:0]`, `b[3:0]`, `p[7:0]`, as spec §5 |

### 4.2 Gate-level simulation semantics
Cell models with `-DFUNCTIONAL -DUNIT_DELAY=#1` put a 1-unit delay on flip-flops only (env_setup §3.3). The GLS PASS therefore proves
**logical equivalence of the netlist with the RTL over all 256 inputs, including the exact 2-cycle latency** (the TB now checks it).
It does not prove timing; that is Part C.

### 4.3 Cells LibreLane would not use (`librelane_excluded_cells_check.log`)
Checked glob-aware against `$PDK_ROOT/sky130A/libs.tech/librelane/sky130_fd_sc_hd/{synth,pnr}_excluded.cells`:

| Cell (count) | Excluded by | Meaning |
|---|---|---|
| `clkinv_1` (2) | synth list (`sky130_fd_sc_hd__clkinv*`) | Clock inverters are reserved for clock-tree synthesis |
| `lpflow_isobufsrc_1` (2) | synth **and** P&R lists (`sky130_fd_sc_hd__lpflow_*`) | Low-power isolation cell; ABC uses it as an AND-NOT gate (liberty function `(A&!SLEEP)`) |

All other cells used are allowed, including the `_0` drive-strength cells (`a21boi_0`, `and2_0`, `o311ai_0`).
**Impact:** none on Part B/C correctness (valid liberty cells, GLS PASS). Part D re-synthesizes from the RTL with its own strategy
and these exclusions, which is one reason Part B and Part D cell counts differ (Part D comparison).

### 4.4 Hierarchical names
Observed in `synth/mult_array_netlist.v` (`wire` declarations): the only public names besides the ports are the register outputs
`a_r`, `b_r` and exactly the **8 nets feeding the `p` register D pins**: `pp[0]` (p[0]), `fa1.sum` (p[1]), `fa5.sum` (p[2]),
`fa9.sum` (p[3]), `fa10.sum` (p[4]), `fa11.sum` (p[5]), `fa12.sum` (p[6]), `fa12.cout` (p[7]). All other internal nets are renamed `_00_` … `_31_`.
Part C maps those back to RTL full adders by truth table.

# Part C: static timing analysis with OpenSTA. Decisions and results

Inputs: `synth/mult_array_netlist.v` (Part B). Tool: OpenSTA 3.1.0. Corner: tt_025C_1v80 only (spec).
Logs: `docs/logs/partC/`.

## 1. Decisions

| Decision | Choice | Why |
|---|---|---|
| Script content | Exactly the 7 spec steps, in order, plus `exit` | Graded script; `exit` makes `sta sta/sta.tcl` return instead of waiting at the prompt |
| Clock period | `-period $T`, `T` = env `STA_PERIOD` if set, else 10.0 | The spec needs two runs (T = 10, then T = T_min) without editing the graded file |
| WNS precision | T_min computed from the full-precision WNS (`docs/scripts/partC_precise_slack.tcl`, `report_worst_slack -digits 6`) | The spec's `report_worst_slack -max` prints 2 decimals (7.21). The 3-digit report value 7.215 gives T_min = 2.785, exactly halfway between 2.78 and 2.79, so more digits are needed to round correctly |
| T_min rounding | Nearest 0.01 ns, as the spec says. 2.785168 → **2.79** (happens to round up, so slack stays ≥ 0) | spec §8 |
| Final `sta/mult_array_timing.rpt` | From the **last** run in the spec's order (T = T_min = 2.79 ns). Both runs are archived | `docs/logs/partC/mult_array_timing_T10.rpt`, `..._Tmin_2.79.rpt` |
| Extra analysis | Separate script `docs/scripts/partC_extra.tcl`; graded script untouched | - |

## 2. Runs
| Run | Command | Printed by the tool | Log |
|---|---|---|---|
| T = 10 ns | `sta sta/sta.tcl` | `worst slack max 7.21` | `sta_T10.log` |
| WNS full precision | `sta -no_splash docs/scripts/partC_precise_slack.tcl` | `worst slack max 7.214832` | `sta_T10_precise_slack.log` |
| T = T_min | `STA_PERIOD=2.79 sta sta/sta.tcl` | `worst slack max 0.00` | `sta_Tmin.log` |
| Slack at T_min, full precision | `STA_PERIOD=2.79 sta -no_splash docs/scripts/partC_precise_slack.tcl` | `worst slack max 0.004832` | `sta_Tmin_precise_slack.log` |

## 3. Part C results table

| Metric | Value |
|---|---|
| Worst slack at T = 10 ns (ns) | **7.21** (full precision 7.214832) |
| T_min (ns) | **2.79** (= 10 − 7.214832 = 2.785168, rounded to 0.01) |
| F_max (MHz) | **358.42** (= 1000 / 2.79). Using the unrounded T_min: 359.05 |
| Slack at T = T_min (ns) | **0.00** as printed (+0.004832 at full precision; MET) |
| Critical path start point | **`a_r[1]`**: flip-flop `_91_` (`dfrtp_1`, D = `a[1]`, Q = `a_r[1]`), launched on the rising edge of `clk` |
| Critical path end point | **`p[6]`**: flip-flop `_88_` (`dfrtp_1`, D = `fa12.sum`, Q = `p[6]`), setup check on the rising edge of `clk` |
| Number of cells on the critical path | **10** = launch FF + **8 combinational cells** + capture FF |
| Latency (ns) = 2 × T_min | **5.58** (2 × 2.79) |
| Throughput (million results per second) | **358.42** (one result per cycle, = F_max) |

Arithmetic log: `docs/logs/partC/tmin_fmax_arithmetic.log`.

### 3.1 Critical path, cells in order (`sta/mult_array_timing.rpt`; identical at T = 10 and 2.79)
| # | Instance | Cell | Incr (ns) | Arrival (ns) | Output net | Same truth table as (RTL) |
|---|---|---|---|---|---|---|
| 1 | `_91_` | dfrtp_1 (CLK→Q) | 0.398 | 0.398 | `a_r[1]` | register a_r[1] |
| 2 | `_37_` | clkinv_1 | 0.073 | 0.471 | `_00_` | ¬a_r[1] |
| 3 | `_41_` | o311ai_0 | 0.354 | 0.826 | `_11_` | none (merged AND + row-1 logic) |
| 4 | `_45_` | a21oi_1 | 0.152 | 0.978 | `_15_` | **fa5.cout** |
| 5 | `_51_` | maj3_1 | 0.402 | 1.380 | `_20_` | **fa6.cout** |
| 6 | `_58_` | xnor3_1 | 0.370 | 1.750 | `_27_` | **¬fa7.sum** |
| 7 | `_61_` | maj3_1 | 0.368 | 2.117 | `_29_` | **¬fa10.cout** |
| 8 | `_63_` | maj3_1 | 0.354 | 2.471 | `_31_` | **¬fa11.cout** |
| 9 | `_64_` | xor3_1 | 0.178 | 2.650 | `fa12.sum` | **fa12.sum** |
| 10 | `_88_` | dfrtp_1 (D, setup 0.135) | - | 2.650 | `p[6]` | register p[6] |

The last column comes from `docs/scripts/partC_net_correspondence.sh` (log `net_correspondence.log`). It simulates the netlist and the RTL
over all 256 (a_r, b_r) inputs and compares the 256-entry truth table of every netlist net with every RTL full-adder port,
internal FA terms (a^b, a&b, a|b, (a^b)&cin), partial products and registers, including complements. "Same truth table" means identical for all 256 inputs.

### 3.2 How many cells come from full adders (spec task 3) vs the 2N = 8 estimate
- **6 of the 8 combinational cells compute an exact full-adder output**: fa5.cout, fa6.cout, fa7.sum, fa10.cout, fa11.cout, fa12.sum
  (3 of them in inverted polarity, which ABC uses freely). Cell types: 3 × maj3 (FA carry = majority), 1 × xnor3 + 1 × xor3 (FA sum = 3-input XOR), 1 × a21oi.
- The other 2 cells (`clkinv_1`, `o311ai_0`) invert `a_r[1]` and implement **merged logic**: partial-product ANDs folded together with the start of the
  adder chain. They match no single RTL signal.
- In RTL terms, the path follows the chain `a_r[1] → (fa1 →) fa2 → fa5 → fa6 → fa7 → fa10 → fa11 → fa12 → p[6]`. From the RTL connections:
  fa5.a = sums[0][1] = fa2.sum, and fa2.cin = carry[0] = fa1.cout. That is **up to 8 full-adder stages = 2N**, and ABC realised them as
  **8 combinational cells**. The estimate holds; ABC compressed the AND gates plus the first adder(s) (fa1 has cin = 0, i.e. a half adder) into 2 cells.
- Delay split (from the report): FA-output cells 4–9 = 1.824 ns of the 2.650 ns arrival; CLK→Q 0.398 ns; inverter + o311ai 0.427 ns.

## 4. Beyond the spec (`sta -no_splash docs/scripts/partC_extra.tcl` → `sta_extra.log`)

| Check | Result |
|---|---|
| `check_setup -verbose` | no output: no unconstrained endpoints, no missing clocks, no combinational loops |
| Worst hold slack | **0.5595 ns** (MET); path `_97_` → `a21oi_1` → `lpflow_isobufsrc_1` → `_85_`; removal check on `rst_n`: 0.704 ns |
| Worst setup slack, input → register | 8.895 ns (`a[0]` → `_90_/D`) |
| Worst setup slack, register → register | 7.215 ns (the critical path) |
| Worst setup slack, register → output | 8.688 ns (`_82_/Q` → `p[0]`) |
| Recovery check (async reset de-assertion) | 9.228 ns (`rst_n` → `_82_/RESET_B`); listed under path group `asynchronous` in the report |

### 4.1 What LibreLane's default constraints would cost on this same netlist (T = 10 ns, cumulative)
| Added constraint (LibreLane default) | Worst setup slack (ns) | Change (ns) |
|---|---|---|
| spec constraints only | 7.2148 | - |
| + 33.442 fF load on outputs | 7.2148 | 0 (outputs come straight from flops; the reg→out path is not critical) |
| + `inv_2` input driver | 7.2148 | 0 (inputs go straight to flop D pins) |
| + 0.25 ns clock uncertainty | 6.9648 | −0.2500 |
| + 0.15 ns clock transition | 6.9456 | −0.0192 |
| + ±5 % timing derate | 6.8104 | −0.1352 |
| **Total** | | **−0.4044** |

So about **0.40 ns of any Part C vs post-route F_max gap comes from constraint differences alone**, before wires, CTS or placement.
Under LibreLane-style constraints, the pre-layout T_min of this netlist would be 10 − 6.8104 = 3.19 ns.

### 4.2 Caveats to state in the report
- Ideal clock (no skew, no clock tree), no wire parasitics, no output load, ideal input slew: the spec's STA is **pre-layout and optimistic**.
- tt corner only; LibreLane signs off over 9 corners (env_setup §4).

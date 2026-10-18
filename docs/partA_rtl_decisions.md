# Part A: RTL design and verification. Decisions and review

Scope: `rtl/full_adder.v`, `rtl/mult_array.v`, `tb/tb_mult.v`. Baseline = commit `a3f0eaf`.
Rule for this document: claims about **code structure** come from reading the source; claims about
**behaviour or counts** come only from tool output, with the log named. Logs live in `docs/logs/partA/`
(kept locally, git-ignored).

---

## 1. Language choice: stay with Verilog-2001

Question: should the front end move to SystemVerilog with a more modular structure?

**Decision: no. Keep Verilog-2001.** SystemVerilog would add risk and no benefit here.

| Consideration | Finding | Source |
|---|---|---|
| File and module names are graded | Spec §5 fixes `rtl/full_adder.v` and `rtl/mult_array.v` (`.v`) and says checking is done against them | RTL_to_GDS.pdf §5 |
| `full_adder` style is prescribed | "written with `assign` statements" | §5 table |
| Synthesis script is prescribed | Step 1 is `read_verilog rtl/full_adder.v rtl/mult_array.v` **without `-sv`**. SV-only syntax (`logic`, `always_ff`) fails that step, so a graded script would have to change | §7 |
| Yosys SV frontend maturity | Upstream known-issues for this image list silent wrong-netlist bugs and rejected constructs in Yosys 0.70's built-in SV frontend (the one LibreLane uses unless `USE_SLANG: true`) | IIC-OSIC-TOOLS `KNOWN_ISSUES.md`, "Yosys Miscompiles or Rejects Some SystemVerilog" |
| Design size | 16 flip-flops, 16 AND gates, 12 full adders. SV abstractions (interfaces, packages, structs) have nothing to abstract | - |
| Modularity within the spec | The only modularity the spec allows is `generate` loops (§6 task 2). A row wrapper (mult_array → 3 rows → 4 FA) risks failing "must use 12 instances of `full_adder`" if the check counts instances in `mult_array.v` | §5, §6 |

The testbench is compiled with `-g2012` per the spec, so SV is already allowed there. It does not need any.

---

## 2. Static review of the baseline against the spec (code reading)

### 2.1 `rtl/full_adder.v`
| Requirement (§5) | Code | OK |
|---|---|---|
| Module `full_adder` | `module full_adder(` | ✔ |
| Inputs `a, b, cin`; outputs `sum, cout` | `input a, b, cin, output sum, cout` | ✔ |
| Written with `assign` | `assign sum = a ^ b ^ cin;` `assign cout = (a&b)\|(b&cin)\|(cin&a);` | ✔ |
| 1-bit (fixes the 4-bit version noted in commit `bd0614e`) | scalar ports | ✔ |

### 2.2 `rtl/mult_array.v`: ports, registers, operator
| Requirement (§5) | Code | OK |
|---|---|---|
| `clk` in 1, `rst_n` in 1, `a` in 4, `b` in 4, `p` out 8 | matches | ✔ |
| Async active-low reset clears all registers | `always @(posedge clk or negedge rst_n) if(!rst_n) a_r<=0; b_r<=0; p<=0;` | ✔ |
| Register a, b (4+4) and p (8): 16 flip-flops | `a_r[3:0]`, `b_r[3:0]`, `p[7:0]` | ✔ (16 confirmed by Yosys, §5) |
| Array built from registered values | AND gates use `a_r`, `b_r` | ✔ |
| 16 AND gates | baseline: 4 primitive instance arrays `and gK[3:0]` (**not synthesizable by Yosys**, §3); now 16 single `and` primitives | ✔ after fix |
| 12 `full_adder` instances | `fa1` … `fa12` | ✔ |
| No `*` operator | none in file | ✔ |

### 2.3 `rtl/mult_array.v`: connection table (Section 2), checked FA by FA
Spec: FA *j* of row *i* takes `pp_i[j]`, `r_{i-1}[j]`, `c_i[j]`, with `c_i[0]=0`.
Code port order is `(a, b, cin, sum, cout)`; the code puts `r` on `a` and `pp` on `b`. A full adder is symmetric in a/b, so the function is identical.

| Inst | a (= r_{i-1}[j]) | b (= pp_i[j]) | cin (= c_i[j]) | sum | cout | Spec | OK |
|---|---|---|---|---|---|---|---|
| fa1 | pp0[1] = r0[0] | pp1[0] | 0 | s1[0] → p[1] | c1[1] | row 1, j=0 | ✔ |
| fa2 | pp0[2] = r0[1] | pp1[1] | c1[1] | s1[1] | c1[2] | j=1 | ✔ |
| fa3 | pp0[3] = r0[2] | pp1[2] | c1[2] | s1[2] | c1[3] | j=2 | ✔ |
| fa4 | 0 = r0[3] | pp1[3] | c1[3] | s1[3] | c1[4] | j=3 | ✔ |
| fa5 | s1[1] = r1[0] | pp2[0] | 0 | s2[0] → p[2] | c2[1] | row 2, j=0 | ✔ |
| fa6 | s1[2] = r1[1] | pp2[1] | c2[1] | s2[1] | c2[2] | j=1 | ✔ |
| fa7 | s1[3] = r1[2] | pp2[2] | c2[2] | s2[2] | c2[3] | j=2 | ✔ |
| fa8 | c1[4] = r1[3] | pp2[3] | c2[3] | s2[3] | c2[4] | j=3 | ✔ |
| fa9 | s2[1] = r2[0] | pp3[0] | 0 | s3[0] → p[3] | c3[1] | row 3, j=0 | ✔ |
| fa10 | s2[2] = r2[1] | pp3[1] | c3[1] | s3[1] → p[4] | c3[2] | j=1 | ✔ |
| fa11 | s2[3] = r2[2] | pp3[2] | c3[2] | s3[2] → p[5] | c3[3] | j=2 | ✔ |
| fa12 | c2[4] = r2[3] | pp3[3] | c3[3] | s3[3] → p[6] | c3[4] → p[7] | j=3 | ✔ |

`p[0] = pp0[0]` ✔. `p[7:4] = {c3[4], s3[3], s3[2], s3[1]}` ✔.

Note for the report (Q1): fa1, fa5, fa9 have `cin = 0` and fa4 has `a = 0`, as the spec's structure requires.
Synthesis constant-folds these, one reason the cell count is not simply 16 + 12 (Part B: 45 combinational cells).

### 2.4 `tb/tb_mult.v` against the Part A testbench requirements
| Requirement | Code | OK |
|---|---|---|
| 10 ns clock | `always #5 clk = ~clk;` | ✔ |
| `rst_n` low for the first 2 cycles | low from t=0 through posedges at 5 and 15 ns, released at the negedge at 20 ns | ✔ |
| All 256 combinations | nested `i`, `k` loops 0..15 | ✔ |
| Wait for the 2-cycle latency, compare with `a*b` | 2 posedges, then compare at the negedge; `*` only in the TB | ✔ (but see §3.3) |
| One line per mismatch | `$display("MISMATCH: ...")` | ✔ |
| Exactly one summary line `PASS: 256 vectors checked, 0 errors` / `FAIL: ...` | `PASS: %0d vectors checked, %0d errors` / `FAIL: ...` | ✔ |
| Writes `mult.vcd` | `$dumpfile("mult.vcd")` | ✔ |

---

## 3. Issues found in the baseline (tool evidence, `docs/logs/partA/baseline_a3f0eaf/`)

| # | Check | Result (verbatim where quoted) | Log |
|---|---|---|---|
| B1 | Spec RTL sim | `PASS: 256 vectors checked, 0 errors`; `$finish` at 5,140,000 ps (= 20 ns reset + 256 × 2 cycles × 10 ns) | `rtl_sim.log` |
| B2 | Fault injection (spec task 6), on a temp copy | `FAIL: 256 vectors checked, 95 errors`; first mismatch `a=3 b=3 p=5 expected=9` | `fault_injection.log` |
| B3 | **Yosys 0.70 `read_verilog` (spec Part B step 1)** | **`rtl/mult_array.v:27: ERROR:Cell arrays of primitives are currently not supported.`** | `yosys_structure.log` |
| B4 | **LibreLane (Verilator lint → Yosys synthesis)** | Lint passes; Yosys fails with the same error; **librelane exit 2** | `librelane_baseline_synth.log` |
| B5 | Verilator 5.052 `--lint-only -Wall` | Only `EOFNEWLINE` (missing newline at end of file) in both RTL files | `verilator_lint.log` |
| B6 | TB strength: TB vs mutants | latency-0 design → **PASS**; latency-1 → **PASS**; latency-3 → FAIL (239 errors) | `tb_latency_mutants.log` |

### 3.1 B3/B4: the baseline RTL was not synthesizable by the prescribed tools (blocking)
The four lines `and gK[3:0](pp[K][3:0], a_r[3:0], {4{b_r[K]}});` are *arrays of gate-primitive instances*.
They are legal Verilog-2001, and iverilog and Verilator accept them, but Yosys does not. Part B step 1 and LibreLane synthesis (Part D) would both fail.
Passing in iverilog did not show that the RTL was synthesizable.

### 3.2 Fix candidates (tried on scratch copies; `fix_candidates.log`)
| Variant | Change | Yosys `read_verilog` (spec) | Yosys `-sv` (LibreLane) | Verilator `-Wall` | TB | Yosys structure (pre-flatten) | Flops after `synth -flatten` |
|---|---|---|---|---|---|---|---|
| **M2 (chosen)**: 16 single `and` primitives | 4 lines → 16 lines `and gK_J(pp[K][J], a_r[J], b_r[K]);` | exit 0 | exit 0 | clean | PASS 256/0 | 3 `$adff`, **16 `$and`**, **12 `full_adder`** | **16** `$_DFF_PN0_` |
| M1: continuous assign | 4 lines → `assign pp[K] = a_r & {4{b_r[K]}};` | exit 0 | exit 0 | clean | PASS 256/0 | 3 `$adff`, 4 × 4-bit `$and`, **12 `full_adder`** | **16** `$_DFF_PN0_` |

Why M2: it keeps the gate-level style, and Yosys then shows exactly **16 AND cells** and **12 full adders**, a one-to-one match with the spec's
"16 AND gates and 12 full adders". The instance names `gK_J` map to `pp_K[J]`. M1 is equally correct and closer to typical industry RTL.

### 3.3 B6: the baseline testbench did not prove latency = 2
Each vector was held for 2 cycles and checked once at the end, so any design with latency 0, 1 or 2 showed the correct value at that moment.
The TB met the letter of the spec ("wait for the 2-cycle latency and compare") but would have passed a design that breaks "latency of 2 clock cycles".

Fix (now in `tb/tb_mult.v`): after edge 1, check that `p` has *not changed* from its previously observed value; after edge 2, check the value as before.
A vector counts as one error if either check fails. Vector timing, the waveform and the summary-line format are unchanged.
Before applying it, the change was checked against every case (`tb_proposed_check.log`, diff `tb_mult_proposed.diff`):

| DUT | Baseline TB | New TB |
|---|---|---|
| Original RTL / M1 / M2 | PASS 256, 0 | PASS 256, 0 (`$finish` still 5,140,000 ps) |
| Fault `sum = a ^ b` | FAIL, 95 | FAIL, 95 (0 latency lines, so the checks don't overlap) |
| Latency-0 mutant | **PASS** | FAIL, 239 |
| Latency-1 mutant | **PASS** | FAIL, 239 |
| Latency-3 mutant | FAIL, 239 | FAIL, 239 |

The 17 vectors that cannot reveal latency are those whose product equals the previous product (the 16 with a = 0, plus a = 1, b = 0).

---

## 4. Changes applied (team decision, 2026-10-18)

| # | Change | File | Why |
|---|---|---|---|
| R1 | 4 primitive-instance arrays → 16 single `and` primitives `gI_J(pp[I][J], a_r[J], b_r[I])` (M2) | `rtl/mult_array.v` | Yosys rejects primitive arrays (§3.1) |
| R2 | Latency check after edge 1 | `tb/tb_mult.v` | TB now proves the 2-cycle latency (§3.3) |
| R3 | Trailing newline at end of file; trailing whitespace removed | `rtl/*.v`, `tb/tb_mult.v` | Verilator `EOFNEWLINE` (B5); hygiene |
| R4 | Commented-out 4-bit-adder lines removed | `rtl/mult_array.v` | Dead code from before commit `bd0614e` |
| R6 | Comment typo "ared" → "are" | `tb/tb_mult.v` | Cosmetic |
| R5 | **Not applied**: named port connections and renamed FA instances (optional) | - | Function already verified; Part B §4.4 shows the netlist keeps only the names of nets feeding the `p` register |

Not done on purpose: SystemVerilog conversion (§1); changing the reset style (the spec mandates an async active-low reset).

---

## 5. Results on the fixed sources
Suite: `eda bash docs/scripts/partA_checks.sh`. Logs in `docs/logs/partA/`.

| Check | Result (verbatim) | Log |
|---|---|---|
| Spec RTL sim (verbatim spec commands) | `PASS: 256 vectors checked, 0 errors` | `rtl_sim.log` |
| Fault injection `sum = a ^ b` (temp copy) | `FAIL: 256 vectors checked, 95 errors` | `fault_injection.log` |
| Verilator 5.052 `--lint-only -Wall` | no warnings, `verilator exit=0` | `verilator_lint.log` |
| Yosys 0.70, pre-flatten (`hierarchy; proc`) | `mult_array`: 3 `$adff`, **16 `$and`**, **12 `full_adder`** | `yosys_structure.log` |
| Yosys 0.70, `synth -top mult_array -flatten` | **16 `$_DFF_PN0_`** (async active-low reset flops), 95 cells including **12 `$scopeinfo`** (non-logic hierarchy markers; removed by the Part B flow) | `yosys_structure.log` |
| TB vs latency mutants | lat0 FAIL 239 · lat1 FAIL 239 · lat3 FAIL 239 | `tb_latency_mutants.log` |

---

## 6. Hand-worked example (spec §6 task 5)
Roll number used: **M P Samartha, 2023102038** → last digit 8 → **A = 8 + 5 = 13**, A ≠ 7 so **B = 7**.
(Alternative: Sai Abhinav Nagamalla, 2024102037 → A = 12, B = 7.)

```
          1 1 0 1     A = 13
        x 0 1 1 1     B = 7
   -----------------
          1 1 0 1     pp0 = A AND b0 (b0 = 1)
        1 1 0 1       pp1 = A AND b1 (b1 = 1), shifted 1
      1 1 0 1         pp2 = A AND b2 (b2 = 1), shifted 2
    0 0 0 0           pp3 = A AND b3 (b3 = 0), shifted 3
   -----------------
    1 0 1 1 0 1 1     P = 91  (8-bit: 0101 1011)
```

Row by row through the array (Section 2 table; hand-computed):

| Row | Inputs (r_{i-1} + pp_i) | Sum s_i | Carry-out c_i[4] | Product bit(s) | Passed down |
|---|---|---|---|---|---|
| 0 | pp0 = 1101 | - | - | p[0] = 1 | r0 = {0, 1, 1, 0} = 0110 |
| 1 | 0110 + 1101 = 10011 | 0011 | 1 | p[1] = 1 | r1 = {1, 0, 0, 1} = 1001 |
| 2 | 1001 + 1101 = 10110 | 0110 | 1 | p[2] = 0 | r2 = {1, 0, 1, 1} = 1011 |
| 3 | 1011 + 0000 = 01011 | 1011 | 0 | p[3] = 1 | p[7:4] = {0, 1, 0, 1} |

P = 0101 1011 = 91.

**Checked against the RTL waveform** (`python3 -I docs/scripts/vcd_probe.py mult.vcd 13 7` → `hand_example_vcd_probe.log`):

| Time | Event | a, b | a_r, b_r | prod (comb.) | p |
|---|---|---|---|---|---|
| 4320 ns | TB applies inputs (falling edge) | 13, 7 | 13, 6 | 78 | 78 (previous vector 13×6) |
| 4325 ns | **edge 1**: inputs captured | 13, 7 | 13, 7 | **91** | 78 |
| 4335 ns | **edge 2**: product captured | 13, 7 | 13, 7 | 91 | **91** |

Internal check: `dut.carry` = 156 = `0b000_1001_1100` → carry[2], carry[3], carry[4], carry[7] = 1.
The hand calculation predicts c1[3] = carry[2] = 1, c1[4] = carry[3] = 1, c2[1] = carry[4] = 1, c2[4] = carry[7] = 1, all others 0. **Match.**
(The unpacked arrays `pp[]` and `sums[]` are not dumped by iverilog, so they cannot be checked in the VCD; `prod` and `carry` cover them.)

**Waveform screenshot** (GTKWave 4.0.0-prealpha on Xvfb): `docs/images/partA_waveform_A13_B7_raw.png` (capture: clk, rst_n, a, b, p,
window 4290–4359 ns, named markers A = 4325 ns (edge 1) and B = 4335 ns (edge 2)) and `docs/images/partA_waveform_A13_B7_annotated.png`
(adds the latency bracket and caption). Save file: `docs/scripts/partA_wave.gtkw`. The Part B gate-level run overwrites `mult.vcd`, so the RTL sim
is re-run before the capture.

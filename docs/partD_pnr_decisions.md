# Part D: physical design with LibreLane. Decisions and results

Tool: LibreLane v3.1.0.dev3 (OpenROAD 26Q1-1024-gdcf36133a, Magic 8.3.685, KLayout 0.30.12, Netgen 1.5.324), sky130A / sky130_fd_sc_hd.
Run from `pnr/`: `librelane --run-tag attempt<N>_<P>ns config.json` (inside the container). Logs: `docs/logs/partD/`.
Run directories: `pnr/runs/` (git-ignored, 610 MB). Logs: `docs/logs/partD/` (git-ignored). Scripts: `docs/scripts/partD_*.{sh,py}`.

## 1. Decisions

| Decision | Choice | Why / evidence |
|---|---|---|
| `config.json` keys | **Exactly the 6 spec keys**; everything else LibreLane defaults | spec §9 table |
| Initial CLOCK_PERIOD | 1.2 × T_min = 1.2 × 2.79 = 3.348 → next 0.5 ns = **3.5 ns** (the exact T_min 2.785168 also gives 3.5) | spec §9 |
| Pass criterion | **LibreLane completes with exit 0**, i.e. its signoff checkers pass: 0 DRC, 0 LVS, no setup or hold violations **in all 9 STA corners** | spec §9 task 1 ("run the flow until it finishes with 0 DRC errors, 0 LVS errors and setup slack ≥ 0") and §14 ("LibreLane stops with setup violations → increase CLOCK_PERIOD by 0.5 ns") taken literally. **⚠ Team confirmation pending (§4)** |
| Iteration | +0.5 ns per attempt, each attempt in its own tagged run dir, every attempt logged | spec §9 task 1 |
| Run tags | `attempt<N>_<P>ns` (attempt 1 predates the tags: `RUN_2026-10-18_16-22-16`) | traceability |
| Final deliverables | `pnr/metrics.json`, `pnr/mult_array.gds` copied from `pnr/runs/attempt7_6.5ns/final/`; sha256 verified (`final_copy_checksums.log`) | spec §9 |
| Screenshots | Headless KLayout render with the PDK layer properties (`docs/scripts/partD_render.py`) plus LibreLane's own `final/render` PNG | issue #6 (headless option) |

## 2. Attempt log (record of every run; spec §9 task 1). Source: `all_attempts_metrics.log`

| # | CLOCK_PERIOD (ns) | LibreLane exit | Setup WS, all corners (ns) | Worst corner | Setup WS, nom_tt (ns) | Hold WS (ns) | DRC (Magic/KLayout/route) | LVS | Std-cell area (µm²) | Timing-repair buffers |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 3.5 | 2 (setup, ss corners) | −2.2565 | max_ss_100C_1v60 | +0.5188 | 0.1176 | 0/0/0 | 0 | 1452.64 | 31 |
| 2 | 4.0 | 2 (setup, ss corners) | −1.7565 | max_ss_100C_1v60 | +1.0188 | 0.1297 | 0/0/0 | 0 | 1452.64 | 31 |
| 3 | 4.5 | 2 (setup, ss corners) | −1.2532 | max_ss_100C_1v60 | +1.5198 | 0.1322 | 0/0/0 | 0 | 1450.14 | 31 |
| 4 | 5.0 | 2 (setup, ss corners) | −0.7532 | max_ss_100C_1v60 | +2.0198 | 0.1322 | 0/0/0 | 0 | 1450.14 | 31 |
| 5 | 5.5 | 2 (setup, ss corners) | −0.3747 | max_ss_100C_1v60 | +2.4931 | 0.1303 | 0/0/0 | 0 | 1377.57 | 25 |
| 6 | 6.0 | 2 (setup, ss corners) | −0.1794 | max_ss_100C_1v60 | +2.8806 | 0.1321 | 0/0/0 | 0 | 1292.49 | 23 |
| **7** | **6.5** | **0 (pass)** | **+0.1301** | max_ss_100C_1v60 | **+3.3217** | 0.1330 | **0/0/0** | **0** | 1283.73 | 23 |

Every failing attempt stopped with the same deferred error: `Setup violations found in the following corners: max_ss_100C_1v60, min_ss_100C_1v60, nom_ss_100C_1v60`.
DRC, LVS, antenna and hold were clean in **all** attempts. Observed: attempts 1 & 2 and attempts 3 & 4 produced identical layouts (same cell counts and wirelength).
As the period relaxed, the flow inserted fewer repair buffers (31 → 23) and less upsizing (std-cell area 1452.6 → 1283.7 µm²).

Why the 20 % margin is not enough: the ss corner (100 °C, 1.60 V) roughly **doubles** cell delays compared with tt. On the attempt-6 ss critical path
(`55-openroad-stapostpnr/max_ss_100C_1v60/max.rpt`): dfrtp_1 CLK→Q 0.752 ns (tt 0.398 in Part C), xor3_1 0.903 ns, maj3 0.745/0.893 ns. The path is reg→reg,
a_r[0] → … → fa12.sum → p[6] reg, data arrival 6.176 ns. 1.2 × T_min (tt) cannot cover that.

## 3. Part D results table (final run = attempt 7; all values from `pnr/metrics.json` → `final_table_values.log`)

| Metric | Value |
|---|---|
| CLOCK_PERIOD used (ns) | **6.5** |
| Number of runs needed | **7** (3.5 → 6.5 ns in 0.5 ns steps) |
| Core area (µm²) | **17,759.5** (`design__core__area`); die area 22,500 (`design__die__area`, 150 × 150) |
| Cells after synthesis (from Part B) | **61** |
| Cells after place and route | **1,879** (`design__instance__count`). Of these: 1,546 fill + decap, 245 tap, **88 functional cells** (16 FF + 42 logic + 4 inv + 26 buffers) |
| Kinds of cells added | **tap** (245 × `tapvpwrvgnd_1`), **decap** (1,288 × `decap_3/4/6/8/12`), **fill** (258 × `fill_1/2`), **clock buffers** (3 × `clkbuf_16`, CTS), **buffers** (17 × `buf_2` I/O port buffers, 3 × `buf_4` rebuffers, 3 × `clkdlybuf4s*` fanout/max-cap repair). No diode cells |
| Wirelength (µm) | **2,491** (`route__wirelength`) |
| Setup slack (ns) | **+0.130** (`timing__setup__ws`, worst of 9 corners = max_ss_100C_1v60); nom_tt: **+3.322** |
| Post-route F_max (MHz) | **156.99** = 1000 / (6.5 − 0.130) with the all-corner slack · **314.64** = 1000 / (6.5 − 3.322) with the nom_tt slack |
| F_max from Part C (MHz) | **358.42** (tt, pre-layout) |
| DRC errors | **0** (Magic 0, KLayout 0, routing 0) |
| LVS errors | **0** |

### 3.1 Cell counts: synthesis → layout (`final_cell_diff.log`, `final_added_buffers.log`)
| Kind | Part B netlist | LibreLane synthesis | Final layout (DEF) |
|---|---|---|---|
| flip-flops | 16 | 16 | 16 |
| logic | 43 | 42 | 42 (some upsized: maj3_1→maj3_2 ×2, a21oi_1→a21oi_2, o311ai_0→o311ai_1) |
| inverters | 2 (clkinv_1) | 4 | 4 |
| buffers / clock / delay buffers | 0 | 0 | 26 |
| tap / decap / fill | 0 | 0 | 245 / 1,288 / 258 |
| **total** | **61** | **62** | **1,879** |

Why Part B (61) and LibreLane synthesis (62) differ: LibreLane re-synthesizes the RTL with its own script (`SYNTH_STRATEGY` `AREA 0`) and excludes `clkinv*` and
`lpflow_*` cells (partB §4.3). Area is almost the same (758.227 vs 756.976 µm²).

Added buffers by OpenROAD instance-name prefix (final DEF):
| Prefix | Count | Cell | Purpose |
|---|---|---|---|
| `clkbuf_*` | 3 | clkbuf_16 | clock tree (1 root + 2 leaves), CTS |
| `inputN` | 9 | buf_2 | one per input port: a[3:0], b[3:0], rst_n (port buffering) |
| `outputN` | 8 | buf_2 | one per output port p[7:0] |
| `fanoutN` | 2 | clkdlybuf4s50_1 | fanout repair (`fanout20` drives the 10 RESET_B pins) |
| `max_capN` | 1 | clkdlybuf4s25_1 | max-capacitance repair |
| `rebufferN` | 3 | buf_4 | timing-driven rebuffering |

LibreLane's metric class `fill_cell` (1,546) **includes decap cells** (258 fill + 1,288 decap). The spec asks about `fill` and `decap` separately, so the DEF breakdown above is the one to report.

### 3.2 Screenshots (headless; `docs/images/`)
| File | Content |
|---|---|
| `partD_layout_whole_die.png` | whole 150 × 150 µm die, KLayout render with `sky130A.lyp` |
| `partD_layout_whole_die_librelane_render.png` | LibreLane's own `final/render/mult_array.png` |
| `partD_layout_zoom_47-77um_x_42-72um.png` | 30 × 30 µm window over the logic cluster: standard-cell rows (met1 rails), cells, met1/met2 routing, vias |
Command: `QT_QPA_PLATFORM=offscreen klayout -z -nc -rx -r docs/scripts/partD_render.py -rd gds=pnr/mult_array.gds -rd out=<png> [-rd box=x1,y1,x2,y2]`

## 4. ⚠ Open question: which "setup slack ≥ 0" does the spec mean? (team decision pending)

Facts (all tool output):
- At the spec's CLOCK_PERIOD (3.5 ns) the **tt corner passes** (+0.519 ns). The **ss corners fail** (−2.256 ns), and LibreLane exits with an error.
- Following the spec's procedure literally (+0.5 ns until LibreLane passes) takes **7 runs** and ends at **6.5 ns**.
- Part C is tt-only by spec. LibreLane signs off on 9 corners by default, and its `timing__setup__ws` is the all-corner worst.

| Option | Final CLOCK_PERIOD | Runs | Setup slack reported | Post-route F_max vs Part C 358.42 | Config | Comment |
|---|---|---|---|---|---|---|
| **A, literal (current deliverables)** | 6.5 ns | 7 | +0.130 (all corners); tt +3.322 | 156.99 (all-corner) or 314.64 (tt) | spec-minimal | Follows §9 and §14 exactly; signoff-correct. Report the tt-based value for the Part C comparison and explain the corner effect |
| B, tt-only signoff | 3.5 ns | 1 | +0.519 (tt) | 335.44 (tt) | needs an extra key restricting LibreLane's STA corners to tt (**not yet tested**) | Apples-to-apples with Part C, but changes the signoff and adds a non-spec key |
| C, spec config at 3.5 ns, accept exit 2 | 3.5 ns | 1 | +0.519 (tt); −2.256 (all) | 335.44 (tt) | spec-minimal | The flow did not "finish" successfully, which contradicts §9 task 1 |

**Recommendation: A** (already in `pnr/`). In the report, give both slacks, use the tt-based post-route F_max (314.64 MHz) for the comparison with Part C,
and use the ss result to explain why the spec's 20 % margin was not enough. If B or C is chosen instead: the attempt-1 run already exists for C; B needs one new run.

## 5. Other observations (all from the logs; none blocks the deliverables)

| Observation | Evidence | Assessment |
|---|---|---|
| 11 max-slew violations in every attempt, **only at max_ss_100C_1v60**: the async-reset net (`fanout20` → 10 × RESET_B), slew 0.760 ns vs 0.750 ns limit (10 ps over) | `attempt7_6.5ns/55-openroad-stapostpnr/max_ss_100C_1v60/checks.rpt` | Warning in LibreLane, not a spec criterion; reset is quasi-static. Fixable with extra repair keys; left as is (reportable) |
| `494 Lint warnings` | `01-verilator-lint/verilator-lint.log` | All `TIMESCALEMOD` in LibreLane-generated cell blackbox stubs (`runs/*/tmp/*.bb.v`), because our RTL has `` `timescale ``. **0 in `rtl/`** |
| `RSZ-0020 found 2 floating nets` | `32-openroad-repairdesignpostgpl` log | The nets are `VGND` and `VPWR` (power, connected by the PDN); LVS 0 confirms connectivity |
| `RSZ-0062 Unable to repair all setup violations` | failing attempts | Expected while the ss corners are over-constrained |
| PNR/SIGNOFF SDC not defined → generic fallback SDC | flow warnings | Defaults: 20 % I/O delay, 0.25 ns uncertainty, 5 % derate, 33.442 fF output load (env_setup §4); Part C §4.1 quantifies about 0.40 ns of their cost |

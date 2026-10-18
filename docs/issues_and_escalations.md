# Issues and escalations

Severity: **H** blocks a graded deliverable or risks correctness · **M** risks quality or reproducibility · **L** informational.
Every item cites the log or file that shows it. Logs under `docs/logs/` and run directories under `pnr/runs/` are kept locally (git-ignored).

## Open: team decision pending

| # | Sev | Area | Issue | Evidence | Recommendation |
|---|---|---|---|---|---|
| 13 | **H** | Part D | **Which "setup slack ≥ 0" decides the final CLOCK_PERIOD?** At the spec's 3.5 ns the tt corner passes (+0.519 ns) but LibreLane's ss corners fail (−2.256 ns) and the flow exits with an error. Following the spec procedure literally (+0.5 ns until LibreLane passes) took **7 runs → 6.5 ns** | `docs/logs/partD/all_attempts_metrics.log`; partD doc §2, §4 | **Option A (literal, all corners) is in `pnr/` now.** Use the tt-based post-route F_max (314.64 MHz) for the comparison with Part C. Alternatives B and C are in partD doc §4 |
| 6 | M | Deliverables | Screenshots were produced **headlessly** (GTKWave under Xvfb + `xwd`; KLayout offscreen). Interactive GUI captures (VNC / `ssh -X`) are the alternative if these are not accepted. | `docs/images/*.png` | Headless images are genuine tool renders; team to confirm they are sufficient |
| 16 | L | Part A deliverable | The waveform marking labels edge 1 → edge 2 as "latency = 2 clock cycles" (spec §2's own wording), although the bracket spans one period in time | `docs/images/partA_waveform_A13_B7_annotated.png` | Keep, or re-annotate (the raw capture is saved too) |
| 1 | M | Env / security | `/home/dvd-a2-env` is `drwxrwxrwx root root` without the sticky bit (shared host) | `ls -ld /home/dvd-a2-env` | Ask the admin for `chown samarthamp: /home/dvd-a2-env && chmod 755`, or `chmod +t` |

## Observations, no action needed (documented for the report)

| # | Sev | Area | Observation | Evidence |
|---|---|---|---|---|
| 17 | L | Part D | 11 max-slew violations, **only at max_ss_100C_1v60**, all on the async-reset net (`fanout20` → 10 × RESET_B): 0.760 ns vs 0.750 ns limit. A LibreLane warning, not a spec criterion | `pnr/runs/attempt7_6.5ns/55-openroad-stapostpnr/max_ss_100C_1v60/checks.rpt` |
| 18 | L | Part D | `494 Lint warnings` are all `TIMESCALEMOD` in LibreLane-generated cell stubs; 0 in `rtl/` | `01-verilator-lint/verilator-lint.log` |
| 19 | L | Part D | `RSZ-0020 found 2 floating nets` = `VGND`, `VPWR` (PDN-connected; LVS 0) | `32-openroad-repairdesignpostgpl` log |
| 14 | M | Part D metrics | `design__instance__count` (1879) includes 1546 fill + decap; the metric class `fill_cell` **includes decaps** | partD doc §3.1 |
| 15 | M | Part D vs C | LibreLane's default constraints alone cost about 0.40 ns of slack on the Part B netlist (0.25 ns uncertainty, 0.019 ns clock transition, 0.135 ns derate) | `docs/logs/partC/sta_extra.log` |
| 20 | L | Part B | The spec's plain `abc -liberty` uses `clkinv_1` ×2 and `lpflow_isobufsrc_1` ×2, which LibreLane excludes. Kept per the spec | `docs/logs/partB/librelane_excluded_cells_check.log` |
| 21 | L | Part B/A | The Part B GLS run overwrites `mult.vcd`; re-run the RTL sim before viewing the Part A waveform (done; the current `mult.vcd` is RTL) | spec commands |
| 22 | L | Env | GTKWave 4.0.0-prealpha in the image has **no Tcl** (`-S` rejected) and a different save-file zoom scale (measured: time/px = 0.005 ps × 2^−zoom) | env_setup §6 |
| 5 | L | Env | Synopsys tools exist in `/eda/bin`; not used (open-source only) | `ls /eda/bin` |

## Resolved

| # | Sev | Issue | Resolution |
|---|---|---|---|
| 8 | M | `docs/` is outside the spec §5 tree | Team decision: markdown notes, helper scripts and images are committed; logs and runtime files are git-ignored |
| 10 | H | Baseline RTL not synthesizable (Yosys: "Cell arrays of primitives are currently not supported") | Team approved fix M2 (16 single `and` primitives). Verified: Yosys/LibreLane synthesize; 12 FA, 16 AND, 16 FF; RTL + GLS PASS |
| 11 | M | TB passed latency-0/1 designs | Team approved the latency check. Verified: lat0/1/3 mutants FAIL, correct design PASS, fault test still 95 errors |
| 12 | L | Missing newline at end of file (Verilator) | Fixed; Verilator `-Wall` clean |
| 7 | H | Roll number for the worked example | M P Samartha 2023102038 → A = 13, B = 7, P = 91 (verified in the waveform) |
| 9 | H | Names and roll numbers for README | Added |
| 3 | M | Image defaults to `PDK=ihp-sg13g2` | `-e PDK=sky130A`; verified |
| 4 | M | SELinux blocks bind mounts | `--security-opt label=disable`; verified |
| 2 | L | Shared host, about 8 GB RAM free | LibreLane runs take about 65 s; no issue |

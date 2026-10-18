# Progress tracker: 4-bit array multiplier, RTL to GDSII (SKY130)

Source of requirements: `RTL_to_GDS.pdf`. Team: M P Samartha (2023102038), Sai Abhinav Nagamalla (2024102037).
Status: `[x]` done and verified with tool output · `[~]` in progress · `[ ]` not started · `[!]` team decision pending
Every number in these docs comes from a tool run with its log cited. Logs (`docs/logs/`) and LibreLane runs (`pnr/runs/`) are kept locally and git-ignored.

---

## Phase 0: Toolchain setup and verification ([env_setup.md](env_setup.md))
- [x] 0.1 Host survey: RHEL 9.8, 64 cores, about 8 GB RAM free, SELinux Enforcing, no sudo, rootless Podman 5.8.2
- [x] 0.2 Deployment: IIC-OSIC-TOOLS (spec toolchain) with rootless Podman
- [x] 0.3 Project-local image store under `/home/dvd-a2-env/containers`
- [x] 0.4 Image `hpretl/iic-osic-tools:2026.10`, pinned by digest `sha256:306585de…557be`
- [x] 0.5 `eda` wrapper + `env.sh`
- [x] 0.6 Tool versions verified (iverilog 14.0-devel, GTKWave 4.0.0-prealpha, Yosys 0.70, OpenSTA 3.1.0, LibreLane 3.1.0.dev3, OpenROAD 26Q1, KLayout 0.30.12, Magic 8.3.685, Netgen 1.5.324, Verilator 5.052)
- [x] 0.7 PDK `/foss/pdks sky130A`; liberty and cell models present
- [x] 0.8 End-to-end smoke test on a toy design (sim, synth, GLS, STA, LibreLane 0 DRC / 0 LVS)
- [x] 0.9 Headless screenshot pipeline (GTKWave + Xvfb + xwd → PNG; KLayout offscreen). [!] Acceptability: team (issue #6)

## Phase A: RTL design and verification (30) ([partA_rtl_decisions.md](partA_rtl_decisions.md))
- [x] A.1–A.3 Static review of full_adder, mult_array (all 12 FA connections match §2), tb_mult
- [x] A.4 Keep Verilog-2001 (no SystemVerilog)
- [x] A.4b **Fix applied (approved):** 16 single `and` primitives (Yosys rejects primitive arrays); dead code removed; EOF newlines
- [x] A.4c **TB latency check applied (approved)**
- [x] A.5 RTL sim: `PASS: 256 vectors checked, 0 errors`
- [x] A.6 Verilator `-Wall`: clean
- [x] A.7 Yosys structure: 16 `$and`, 12 `full_adder`, 16 FF
- [x] A.8 Fault injection: `FAIL: 256 vectors checked, 95 errors`
- [x] A.9 TB vs latency mutants: lat0/1/3 all FAIL
- [x] A.10 Worked example A = 13, B = 7 (roll 2023102038), checked against the VCD: p = 91 at edge 2 (4335 ns); internal carries match
- [x] A.11 Waveform screenshot with markers at edges 1 and 2 (`docs/images/partA_waveform_A13_B7_*.png`). [!] Annotation style: team (issue #16)
- [ ] A.12 Block diagram (team deliverable; hand-drawn allowed)

## Phase B: Logic synthesis (20) ([partB_synth_decisions.md](partB_synth_decisions.md))
- [x] B.1 `synth/synth.tcl`: exactly the 7 spec steps
- [x] B.2 `yosys -c synth/synth.tcl`: exit 0; netlist + stat written
- [x] B.3 Table: 61 cells, 16 FF (dfrtp_1), 756.976 µm², FF 400.384 µm² (52.89 %), top 3: dfrtp_1 16, nand2_1 7, and2_0/maj3_1 4 (tie)
- [x] B.4 GLS (spec command): `PASS: 256 vectors checked, 0 errors`
- [x] B.5 Netlist audit: 1 module, 61 cells, 0 generic, 0 latches; LibreLane-excluded cells noted

## Phase C: Static timing analysis (20) ([partC_sta_decisions.md](partC_sta_decisions.md))
- [x] C.1 `sta/sta.tcl`: exactly the 7 spec steps (+ env-overridable period, `exit`)
- [x] C.2 T = 10 ns: WNS 7.21 (7.214832)
- [x] C.3 T_min = 2.79 ns (2.785168), F_max = 358.42 MHz
- [x] C.4 T = 2.79 ns: slack 0.00 (+0.004832)
- [x] C.5 Critical path a_r[1] → p[6], 10 cells (8 combinational); 6 cells are exact FA outputs (fa5, fa6, fa7, fa10, fa11, fa12) by truth-table matching; RTL chain up to 8 FA = 2N
- [x] C.6 Extras: hold 0.5595 ns MET, check_setup clean, slack per path type, LibreLane-constraint sensitivity (−0.404 ns)

## Phase D: Physical design (30) ([partD_pnr_decisions.md](partD_pnr_decisions.md))
- [x] D.1 `pnr/config.json`: exactly the 6 spec keys
- [x] D.2 Initial CLOCK_PERIOD 3.5 ns (1.2 × 2.79 → next 0.5)
- [x] D.3 7 attempts (3.5 → 6.5 ns); attempt 7 passes LibreLane (all 9 corners). [!] **Criterion confirmation: team (issue #13)**
- [x] D.4 `pnr/metrics.json`, `pnr/mult_array.gds` copied from attempt 7 (sha256 verified)
- [x] D.5 Table: 6.5 ns, 7 runs, core 17,759.5 µm², 1,879 cells, wirelength 2,491 µm, setup +0.130 (all) / +3.322 (tt), post-route F_max 156.99 (all) / 314.64 (tt) MHz, DRC 0, LVS 0
- [x] D.6 Added cells: 245 tap, 1,288 decap, 258 fill, 3 clkbuf_16, 17 I/O buf_2, 3 buf_4 rebuffers, 3 clkdlybuf repair
- [x] D.7 Layout screenshots: whole die + 30 × 30 µm zoom (`docs/images/partD_layout_*.png`)
- [x] D.8 `pnr/runs/` in `.gitignore`

## Phase E: Repo and deliverable hygiene
- [x] E.1 README: names and roll numbers
- [x] E.2 README: commands in order + Part D attempt record
- [x] E.3 `.gitignore`: sim, gls, *.vcd, pnr/runs/
- [x] E.3b Reproducibility: re-running synth and STA gives byte-identical netlist, stat and timing report (`docs/logs/reproducibility_check.log`)
- [x] E.4 `docs/`: markdown, scripts and images committed; logs and runtime files git-ignored
- [x] E.5 Work committed as a series of per-part commits (spec expects at least 4–5 meaningful commits)

## Report: not started (deferred)
Material ready for it: all tables above, the critical-path FA mapping, the cell-count breakdowns, the corner analysis, and the images.

---
Open items: [issues_and_escalations.md](issues_and_escalations.md) · Commands: [run_commands.md](run_commands.md)

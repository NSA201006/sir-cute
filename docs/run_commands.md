# Run commands (in the order they were run)

Every command behind a recorded result, in order, with where its output went.
`README.md` holds the grader-facing subset (spec §5); this file also has the setup and the beyond-spec checks.

Conventions
- **Host** = RHEL host. `eda <cmd>` runs `<cmd>` inside the container from the repo root (`/foss/designs/DVD-Assignment`);
  `eda` alone opens an interactive container shell, where the spec commands can be typed verbatim.
- One-time per host shell: `source /home/dvd-a2-env/env.sh`.
- Logs named below (`docs/logs/...`) are kept locally and git-ignored; re-running a command regenerates its log.
- `docs/scripts/*.sh` are run with `eda bash docs/scripts/<x>.sh`, except `partD_sweep.sh`, which is a host script that calls `eda` itself.

---

## Phase 0: environment (host)
```bash
mkdir -p /home/dvd-a2-env/{containers/storage,bin,logs,scripts,src,work}
#   /home/dvd-a2-env/containers/storage.conf : graphroot=/home/dvd-a2-env/containers/storage
git clone --depth 1 https://github.com/iic-jku/IIC-OSIC-TOOLS.git /home/dvd-a2-env/src/IIC-OSIC-TOOLS     # reference only
CONTAINERS_STORAGE_CONF=/home/dvd-a2-env/containers/storage.conf podman pull docker.io/hpretl/iic-osic-tools:2026.10
#   -> digest sha256:306585de35d198e70ea58950f77147c86f56c698726a19afea9f1c83009557be (pinned in env.sh)
source /home/dvd-a2-env/env.sh
eda bash -s < /home/dvd-a2-env/scripts/verify_env.sh        # -> docs/logs/env/verify_env.log
eda bash -s < /home/dvd-a2-env/scripts/smoke_toolchain.sh   # -> docs/logs/env/smoke_toolchain.log
```

## Part A, on the baseline RTL (commit a3f0eaf, before the fix): diagnostics
Logs in `docs/logs/partA/baseline_a3f0eaf/`: `rtl_sim.log` (PASS), `fault_injection.log` (FAIL 95),
`verilator_lint.log` (EOFNEWLINE only), `yosys_structure.log` (**Yosys error**), `librelane_baseline_synth.log` (exit 2),
`fix_candidates.log` (M1/M2), `tb_latency_mutants.log`, `tb_proposed_check.log`, `tb_mult_proposed.diff`.

## Part A, after the approved fix (current tree)
```bash
eda bash docs/scripts/partA_checks.sh
#   1. iverilog -g2012 -o sim tb/tb_mult.v rtl/full_adder.v rtl/mult_array.v ; vvp sim   -> PASS: 256 vectors checked, 0 errors
#   2. fault injection on a mktemp copy (sum = a ^ b)                                    -> FAIL: 256 vectors checked, 95 errors
#   3. verilator --lint-only -Wall --top-module mult_array rtl/full_adder.v rtl/mult_array.v   -> exit 0, no warnings
#   4. yosys -p "read_verilog ...; hierarchy -check -top mult_array; proc; opt_clean; stat; synth -top mult_array -flatten; stat"
#   5. bash docs/scripts/tb_latency_mutants.sh                                          -> lat0/lat1/lat3 FAIL
# logs: docs/logs/partA/{rtl_sim,fault_injection,verilator_lint,yosys_structure,tb_latency_mutants}.log

python3 -I docs/scripts/vcd_probe.py mult.vcd 13 7          # -> docs/logs/partA/hand_example_vcd_probe.log
```

## Part B
```bash
eda yosys -c synth/synth.tcl                                # -> docs/logs/partB/yosys_synth.log, synth/mult_array_{netlist.v,stat.rpt}
eda bash -c 'CELLS=$PDK_ROOT/sky130A/libs.ref/sky130_fd_sc_hd/verilog
  iverilog -g2012 -DFUNCTIONAL -DUNIT_DELAY=#1 -o gls tb/tb_mult.v $CELLS/primitives.v $CELLS/sky130_fd_sc_hd.v synth/mult_array_netlist.v
  vvp gls'                                                  # -> docs/logs/partB/gls.log : PASS
# netlist audit and LibreLane exclusion check (inline scripts, recorded in):
#   docs/logs/partB/netlist_audit.log, docs/logs/partB/librelane_excluded_cells_check.log
```

## Part C
```bash
eda sta sta/sta.tcl                                         # T = 10   -> docs/logs/partC/sta_T10.log            (worst slack max 7.21)
#   copy of the report: docs/logs/partC/mult_array_timing_T10.rpt
eda sta -no_splash docs/scripts/partC_precise_slack.tcl     # full-precision WNS -> docs/logs/partC/sta_T10_precise_slack.log (7.214832)
eda bash -c 'STA_PERIOD=2.79 sta sta/sta.tcl'               # T = T_min -> docs/logs/partC/sta_Tmin.log         (worst slack max 0.00)
#   copy: docs/logs/partC/mult_array_timing_Tmin_2.79.rpt
eda bash -c 'STA_PERIOD=2.79 sta -no_splash docs/scripts/partC_precise_slack.tcl'   # -> sta_Tmin_precise_slack.log (0.004832)
#   arithmetic: docs/logs/partC/tmin_fmax_arithmetic.log
eda sta -no_splash docs/scripts/partC_extra.tcl             # -> docs/logs/partC/sta_extra.log
eda bash docs/scripts/partC_net_correspondence.sh           # -> docs/logs/partC/net_correspondence.log
#   critical-path net names: docs/logs/partC/critical_path_nets.log
```

## Part D
```bash
eda -c 'cd pnr && librelane config.json'                    # attempt 1, 3.5 ns -> docs/logs/partD/attempt1_3.5ns_librelane.log (exit 2)
bash docs/scripts/partD_sweep.sh 2 4.0 4.5 5.0 5.5 6.0 6.5 7.0   # host; stops at the first pass
#   -> attempt2_4.0ns ... attempt7_6.5ns (exit 0); logs docs/logs/partD/attempt<N>_<P>ns_librelane.log; summary sweep_summary.log
python3 -I docs/scripts/partD_metrics.py pnr/runs/RUN_2026-10-18_16-22-16 pnr/runs/attempt{2_4.0,3_4.5,4_5.0,5_5.5,6_6.0,7_6.5}ns
#   -> docs/logs/partD/all_attempts_metrics.log
cp pnr/runs/attempt7_6.5ns/final/metrics.json pnr/metrics.json
cp pnr/runs/attempt7_6.5ns/final/gds/mult_array.gds pnr/mult_array.gds   # sha256: docs/logs/partD/final_copy_checksums.log
python3 -I docs/scripts/partD_cell_diff.py pnr/runs/attempt7_6.5ns       # -> docs/logs/partD/final_cell_diff.log
#   buffer attribution by instance name -> docs/logs/partD/final_added_buffers.log ; values -> final_table_values.log
```

## Screenshots (headless)
```bash
# Part A waveform (RTL mult.vcd must be current: re-run the RTL sim after any GLS run)
eda bash -c 'Xvfb :99 -screen 0 1600x560x24 -nolisten tcp & sleep 1
  DISPLAY=:99 gtkwave mult.vcd docs/scripts/partA_wave.gtkw & sleep 6
  xwd -root -display :99 -out /work/render_test/wave.xwd'
eda python3 -I docs/scripts/xwd2png.py /work/render_test/wave.xwd /work/render_test/wave_raw.png 1600 200
eda python3 -I docs/scripts/annotate_wave.py /work/render_test/wave_raw.png /work/render_test/wave_annotated.png
#   -> docs/images/partA_waveform_A13_B7_{raw,annotated}.png
# Part D layout
eda bash -c 'export QT_QPA_PLATFORM=offscreen
  klayout -z -nc -rx -r docs/scripts/partD_render.py -rd gds=pnr/mult_array.gds -rd out=docs/images/partD_layout_whole_die.png -rd px=1600
  klayout -z -nc -rx -r docs/scripts/partD_render.py -rd gds=pnr/mult_array.gds -rd out=docs/images/partD_layout_zoom_47-77um_x_42-72um.png -rd box=47,42,77,72 -rd px=1600'
cp pnr/runs/attempt7_6.5ns/final/render/mult_array.png docs/images/partD_layout_whole_die_librelane_render.png
```

## Reproducibility check
```bash
# re-run synth + STA + GLS + RTL sim; compare checksums taken before
eda bash -c 'yosys -q -c synth/synth.tcl; STA_PERIOD=2.79 sta sta/sta.tcl; ...'   # -> docs/logs/reproducibility_check.log (all OK)
```

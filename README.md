# 4-bit Array Multiplier: RTL to GDSII on SkyWater SKY130

| Team member | Roll number |
|---|---|
| M P Samartha | 2023102038 |
| Sai Abhinav Nagamalla | 2024102037 |

Design: 4 × 4-bit unsigned array multiplier (16 AND gates, 12 full adders, 16 flip-flops, 2-cycle latency), `sky130_fd_sc_hd`.

## Environment

All tools come from the IIC-OSIC-TOOLS image, tag `2026.10`
(digest `sha256:306585de35d198e70ea58950f77147c86f56c698726a19afea9f1c83009557be`), run with rootless Podman
(no Docker on our Linux host). The repository is mounted at `/foss/designs/DVD-Assignment` and `PDK=sky130A`.

```bash
# host, one-time
podman pull docker.io/hpretl/iic-osic-tools:2026.10
# host, start a shell in the container (SELinux host, rootless Podman; same flags as upstream start_shell.sh)
podman run --rm -it --user 0:0 --security-opt seccomp=unconfined --security-opt label=disable \
  -e PDK=sky130A -v "$PWD":/foss/designs/DVD-Assignment:rw -w /foss/designs/DVD-Assignment \
  docker.io/hpretl/iic-osic-tools@sha256:306585de35d198e70ea58950f77147c86f56c698726a19afea9f1c83009557be --skip bash
```
(On our host this command is wrapped in a small script, `eda`, which also mounts a scratch directory and sets `IIC_OSIC_TOOLS_QUIET=1`.)

Tool versions reported inside the container: Icarus Verilog 14.0 (devel), Yosys 0.70, OpenSTA 3.1.0, LibreLane 3.1.0.dev3,
OpenROAD 26Q1-1024-gdcf36133a (LibreLane's), KLayout 0.30.12, Magic 8.3.685, Netgen 1.5.324, GTKWave 4.0.0-prealpha.

Checks from spec §4.2 (inside the container):
```bash
iverilog -V | head -1
yosys -V
sta -version
echo $PDK_ROOT $PDK          # -> /foss/pdks sky130A
```

All commands below are run inside the container from the repository root, in this order.

## Part A: RTL design and verification

```bash
iverilog -g2012 -o sim tb/tb_mult.v rtl/full_adder.v rtl/mult_array.v
vvp sim
#   -> PASS: 256 vectors checked, 0 errors
```

Waveform screenshot (the container has no display; GTKWave ran on a virtual X server and the screen was captured):
```bash
Xvfb :99 -screen 0 1600x560x24 -nolisten tcp &
DISPLAY=:99 gtkwave mult.vcd docs/scripts/partA_wave.gtkw &      # signals clk, rst_n, a, b, p; markers A, B
xwd -root -display :99 -out wave.xwd                               # then converted to PNG
```

Error-detection test (task 6). The `sum = a ^ b` change was made on a temporary copy of `full_adder.v`, so the original was never edited:
```bash
F=$(mktemp -d)
sed "s/assign sum = a ^ b ^ cin;/assign sum = a ^ b;/" rtl/full_adder.v > "$F/full_adder.v"
iverilog -g2012 -o "$F/sim_fault" tb/tb_mult.v "$F/full_adder.v" rtl/mult_array.v
(cd "$F" && vvp -n sim_fault)
#   -> FAIL: 256 vectors checked, 95 errors
```

Worked example: roll number 2023102038 → A = 8 + 5 = 13, B = 7 → P = 91. In the waveform the inputs are captured at the rising edge at 4325 ns
and `p = 91` appears at the next rising edge, 4335 ns (2-cycle latency).

## Part B: Logic synthesis

```bash
yosys -c synth/synth.tcl
#   -> synth/mult_array_netlist.v, synth/mult_array_stat.rpt  (61 cells, 16 x dfrtp_1, 756.976 um^2)

CELLS=$PDK_ROOT/sky130A/libs.ref/sky130_fd_sc_hd/verilog
iverilog -g2012 -DFUNCTIONAL -DUNIT_DELAY=#1 -o gls \
  tb/tb_mult.v $CELLS/primitives.v $CELLS/sky130_fd_sc_hd.v synth/mult_array_netlist.v
vvp gls
#   -> PASS: 256 vectors checked, 0 errors
```

## Part C: Static timing analysis

`sta/sta.tcl` takes the clock period from the environment variable `STA_PERIOD` (default 10 ns).
```bash
sta sta/sta.tcl
#   -> worst slack max 7.21          (T = 10 ns; 7.214832 at 6 digits)
#   T_min = 10 - 7.214832 = 2.785168 -> 2.79 ns, F_max = 1000 / 2.79 = 358.42 MHz
STA_PERIOD=2.79 sta sta/sta.tcl
#   -> worst slack max 0.00          (T = T_min; +0.004832 at 6 digits)
```
`sta/mult_array_timing.rpt` is from the last run (T = 2.79 ns).

## Part D: Physical design (LibreLane)

```bash
cd pnr && librelane config.json                                  # attempt 1, CLOCK_PERIOD = 3.5
# attempts 2..7: CLOCK_PERIOD in pnr/config.json increased by 0.5 ns each time, then
cd pnr && librelane --run-tag attempt<N>_<P>ns config.json       # attempt2_4.0ns ... attempt7_6.5ns
# from the repository root:
cp pnr/runs/attempt7_6.5ns/final/metrics.json pnr/metrics.json
cp pnr/runs/attempt7_6.5ns/final/gds/mult_array.gds pnr/mult_array.gds
```

Layout screenshots (headless KLayout with the PDK layer colours `sky130A.lyp`):
```bash
QT_QPA_PLATFORM=offscreen klayout -z -nc -rx -r docs/scripts/partD_render.py \
  -rd gds=pnr/mult_array.gds -rd out=docs/images/partD_layout_whole_die.png -rd px=1600
QT_QPA_PLATFORM=offscreen klayout -z -nc -rx -r docs/scripts/partD_render.py \
  -rd gds=pnr/mult_array.gds -rd out=docs/images/partD_layout_zoom_47-77um_x_42-72um.png -rd box=47,42,77,72 -rd px=1600
```

Initial CLOCK_PERIOD = 1.2 × T_min = 1.2 × 2.79 = 3.348 → rounded up to 3.5 ns. Record of every attempt:

| Attempt | CLOCK_PERIOD (ns) | Result | Worst setup slack, all 9 corners (ns) | Setup slack, nom_tt_025C_1v80 (ns) | DRC | LVS |
|---|---|---|---|---|---|---|
| 1 | 3.5 | failed: setup violations at ss corners | −2.256 | +0.519 | 0 | 0 |
| 2 | 4.0 | failed: setup violations at ss corners | −1.757 | +1.019 | 0 | 0 |
| 3 | 4.5 | failed: setup violations at ss corners | −1.253 | +1.520 | 0 | 0 |
| 4 | 5.0 | failed: setup violations at ss corners | −0.753 | +2.020 | 0 | 0 |
| 5 | 5.5 | failed: setup violations at ss corners | −0.375 | +2.493 | 0 | 0 |
| 6 | 6.0 | failed: setup violations at ss corners | −0.179 | +2.881 | 0 | 0 |
| **7** | **6.5** | **passed (flow completed, 0 DRC, 0 LVS, no setup/hold violations)** | **+0.130** | **+3.322** | **0** | **0** |

The `runs/` folder is not committed (`.gitignore`).

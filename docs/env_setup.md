# Environment setup and verification

All values below were printed by the tools themselves. Logs are in `/home/dvd-a2-env/logs/` on the host.

## 1. Host constraints (why the setup looks like this)

| Fact | Value | Consequence |
|---|---|---|
| OS | RHEL 9.8, x86_64, kernel 7.2.3 | IIC-OSIC-TOOLS image runs natively (amd64) |
| CPU / RAM | 64 cores; 30 GB RAM, about 8 GB available (shared host, swap in use) | Fine for a 4-bit design |
| Disk | `/home` XFS, about 172 GB free before setup | Image takes 12.7 GB |
| Privileges | no sudo | No Docker install possible |
| Container runtime | Podman 5.8.2, **rootless** (subuid/subgid mapped, cgroup v2, crun) | Use Podman instead of Docker Desktop (upstream supports Podman as a first-class runtime) |
| SELinux | **Enforcing** | Container needs `--security-opt label=disable`, otherwise the bind-mounted repo is denied (upstream issue #352) |

## 2. What was installed, and where

| Item | Location |
|---|---|
| Podman image store (project-local) | `/home/dvd-a2-env/containers/storage` via `/home/dvd-a2-env/containers/storage.conf` (selected with `CONTAINERS_STORAGE_CONF`; the global `~/.config/containers` is untouched) |
| Image | `docker.io/hpretl/iic-osic-tools:2026.10`, **pinned by digest** `sha256:306585de35d198e70ea58950f77147c86f56c698726a19afea9f1c83009557be` (image created 2026-10-15, 12.7 GB) |
| Environment file | `/home/dvd-a2-env/env.sh` |
| Run wrapper | `/home/dvd-a2-env/bin/eda` |
| Upstream repo (reference only) | `/home/dvd-a2-env/src/IIC-OSIC-TOOLS` (commit `d8a4d383`) |
| Verification and experiment scripts | `/home/dvd-a2-env/scripts/` |
| Scratch area, mounted at `/work` | `/home/dvd-a2-env/work/` |
| Logs | `/home/dvd-a2-env/logs/` |

### Why tag 2026.10
- Upstream `KNOWN_ISSUES.md`: Yosys `arith_tree` dropped operand widths in images **up to 2026.08**, fixed from 2026.09 (Yosys 0.69). Older tags are excluded.
- 2026.10 also fixes an `eqy` plugin-lookup bug (release notes), which matters if we add formal equivalence checking.
- Pinning by digest makes runs bit-reproducible even if the tag is re-pushed.

### What the `eda` wrapper does (and why)
| Flag | Reason |
|---|---|
| `--user 0:0` | Under rootless Podman, container root maps to the host user (uid 1006). Files written to the repo stay `samarthamp:samarthamp` (verified), and no ID-mapped image copy is needed. Same default as upstream `start_shell.sh` |
| `--security-opt seccomp=unconfined` | As in upstream `start_shell.sh` |
| `--security-opt label=disable` | SELinux Enforcing on this host (upstream workaround) |
| `-e PDK=sky130A` | **The image defaults to `ihp-sg13g2`** (`export PDK=${PDK:-ihp-sg13g2}` in `/etc/profile.d/iic-osic-tools-setup.sh`). Setting it up front also sets `STD_CELL_LIBRARY=sky130_fd_sc_hd` |
| `-v <repo>:/foss/designs/DVD-Assignment` | Spec §4.1 convention (`/foss/designs`) |
| `-v /home/dvd-a2-env/work:/work` | Scratch area for experiments that must not touch the repo |
| entrypoint `--skip <cmd>` | Upstream entrypoint: skips the VNC/X11 UI, sources the tool environment, then execs the command |

## 3. Verification results (Phase 0.6, 0.7)
Command: `eda bash -s < /home/dvd-a2-env/scripts/verify_env.sh` → `/home/dvd-a2-env/logs/verify_env.log`

### 3.1 Spec §4.2 checks
| Check | Spec expects | Tool output | OK |
|---|---|---|---|
| `echo $PDK_ROOT $PDK` | shows sky130A | `/foss/pdks sky130A` | ✔ |
| Liberty (tt corner) | `$PDK_ROOT/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib` | exists, 12,841,637 bytes, `library ("sky130_fd_sc_hd__tt_025C_1v80")` | ✔ |
| Cell models | `.../verilog/primitives.v`, `.../verilog/sky130_fd_sc_hd.v` | exist (50,512 and 3,995,427 bytes) | ✔ |
| PDK build | - | open_pdks `1689ac3f2dc763876eaf967227c7dfe831b031ae` | - |

### 3.2 Tool versions (as printed by each tool)
| Tool | Spec use | Path in container | Version string |
|---|---|---|---|
| Icarus Verilog | A, B | `/foss/tools/bin/iverilog` | `Icarus Verilog version 14.0 (devel) (s20260301-579-g15d870a5-dirty)` |
| GTKWave | A | `/foss/tools/bin/gtkwave` | `GTKWave Analyzer v4.0.0-prealpha (f6d60e0)` (needs a display; checked under `xvfb-run`) |
| Yosys | B | `/foss/tools/bin/yosys` | `Yosys 0.70 (git sha1 28ba3cb92, Release, GNU /usr/bin/c++ 13.3.0)` |
| OpenSTA | C | `/foss/tools/bin/sta` | `3.1.0` |
| OpenROAD (standalone) | - | `/foss/tools/bin/openroad` | `26Q4-407-geb14e40b7` |
| OpenROAD (used by LibreLane) | D | `/foss/tools/openroad-librelane/bin/openroad` | `26Q1-1024-gdcf36133a` |
| LibreLane | D | `/foss/tools/bin/librelane` (wrapper) | `LibreLane v3.1.0.dev3` (pip `librelane 3.1.0.dev3`) |
| KLayout | D | `/foss/tools/klayout/klayout` | `KLayout 0.30.12` |
| Magic | D | `/foss/tools/bin/magic` | `8.3.685` |
| Netgen | D | `/foss/tools/bin/netgen` | `Netgen 1.5.324` |
| Verilator | lint (and LibreLane's lint step) | `/foss/tools/bin/verilator` | `Verilator 5.052 2026-09-05 rev v5.052` |
| EQY | optional formal equivalence | `/foss/tools/bin/eqy` | `EQY v0.70-dirty` |

Notes:
- The `librelane` command in the image is a wrapper: it puts `openroad-librelane` first on `PATH` and runs
  `librelane --manual-pdk "$@"`. LibreLane therefore uses the image's PDK as is and does not try to download one.
- LibreLane is a **dev** release (`3.1.0.dev3`). Recorded for reproducibility; no issue seen so far.

### 3.3 Gate-level simulation semantics (matters for Part B)
`UNIT_DELAY` appears 116 times in `sky130_fd_sc_hd.v`, and **only in the 58 sequential cell models** (flip-flops and latches, e.g. `dfrtp_1`).
Combinational cell models have no delay. So `iverilog -DFUNCTIONAL -DUNIT_DELAY=#1` gives a **functional** gate-level simulation:
flops have a 1-unit clock-to-Q, logic settles in zero time. It proves the netlist's logic matches the RTL. It cannot detect timing problems (that is Part C's job), and it cannot fail spuriously at a 10 ns clock.

## 4. End-to-end smoke test (Phase 0.8)
Throwaway 4-bit counter, not the assignment design. Command: `eda bash -s < /home/dvd-a2-env/scripts/smoke_toolchain.sh`
→ `/home/dvd-a2-env/logs/smoke_toolchain.log`. Run outputs are in `/home/dvd-a2-env/work/smoke/`.

| Stage | Result (tool output) |
|---|---|
| iverilog RTL sim | `SMOKE-SIM PASS q=4` |
| Yosys + sky130 liberty | exit 0; 10 cells, 4 × `sky130_fd_sc_hd__dfrtp_1`, chip area 137.632 |
| iverilog GLS (spec Part B flags) | `SMOKE-SIM PASS q=4` |
| OpenSTA, 10 ns | `worst slack max 8.62` |
| LibreLane full flow (150 × 150 µm, 10 ns) | exit 0 in 56 s; Magic DRC 0, KLayout DRC 0, route DRC 0, LVS 0, antenna 0; GDS written |

### What the smoke run told us about LibreLane v3.1.0.dev3 defaults (read from `resolved.json`)
| Setting | Default | Compare with Part C |
|---|---|---|
| `STA_CORNERS` | 9 corners: {nom, min, max} RC × {tt_025C_1v80, ss_100C_1v60, ff_n40C_1v95} | Part C: tt only |
| `DEFAULT_CORNER` | `nom_tt_025C_1v80` | - |
| `IO_DELAY_CONSTRAINT` | 20 (% of clock period) | Part C: 1.0 ns |
| `OUTPUT_CAP_LOAD` | 33.442 fF | Part C: none |
| `SYNTH_DRIVING_CELL` | `sky130_fd_sc_hd__inv_2/Y` | Part C: ideal inputs |
| `CLOCK_UNCERTAINTY_CONSTRAINT` | 0.25 ns | Part C: none |
| `TIME_DERATING_CONSTRAINT` | 5 % | Part C: none |
| `SYNTH_STRATEGY` | `AREA 0` | Part B: `abc -liberty` default script |

Metric keys observed in `final/metrics.json` (relevant to Part D): `design__instance__count` (includes fill cells),
`design__instance__count__stdcell`, `design__instance__count__class:{fill_cell,tap_cell,clock_buffer,timing_repair_buffer,...}`,
`design__core__area`, `design__die__area`, `route__wirelength`, `timing__setup__ws` (**worst over all 9 corners**),
`timing__setup__ws__corner:nom_tt_025C_1v80`, `magic__drc_error__count`, `klayout__drc_error__count`, `route__drc_errors`,
`design__lvs_error__count`.

LibreLane has a `klayout-render` step that writes a PNG of the final layout into `final/render/` without a GUI.

## 5b. Headless rendering (screenshots without a display)
| Tool | Finding (tested) | What works |
|---|---|---|
| KLayout 0.30.12 | `klayout -z` with `pya.LayoutView` aborts without a Qt platform | `QT_QPA_PLATFORM=offscreen klayout -z -nc -rx -r docs/scripts/partD_render.py ...` |
| GTKWave 4.0.0-prealpha | `-S` (Tcl script) is rejected: `invalid option -- 'S'`, so no Tcl in this build | Save file (`.gtkw`) + `Xvfb :99` + `xwd -root`, converted with `docs/scripts/xwd2png.py` (PIL) |
| GTKWave 4 `.gtkw` zoom | Different scale from GTKWave 3 docs; measured at zoom −5.64, −10 and −16: **time per pixel = 0.005 ps × 2^(−zoom)** | zoom −13.3 → about 50 ps/px → about 69 ns window |
| GTKWave 4 markers | Primary and named markers from the `*` line are honoured; drawn in RGB (255, 255, 128) | used to place annotations |
| Image tools | no ImageMagick, ffmpeg, xdotool or scrot; `xwd` and Python PIL 12.3.0 are available | - |

## 5. Daily use
```bash
source /home/dvd-a2-env/env.sh      # once per host shell
eda                                  # interactive shell in the container, at the repo root
eda iverilog -V                      # one-off command
eda -c 'cd pnr && librelane config.json'
```

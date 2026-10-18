#!/usr/bin/env python3
"""Summarise LibreLane runs for the Part D table. Reads only tool outputs (metrics.json, resolved.json).

Usage (repo root):  python3 -I docs/scripts/partD_metrics.py pnr/runs/<run1> [pnr/runs/<run2> ...]
Post-route F_max uses the spec formula 1000 / (CLOCK_PERIOD - setup slack), for two slack definitions:
  all-corner = timing__setup__ws (worst of the 9 LibreLane corners)
  tt         = timing__setup__ws__corner:nom_tt_025C_1v80 (the corner Part C uses)
"""
import json
import os
import sys

TT = "nom_tt_025C_1v80"
ROWS = [
    ("CLOCK_PERIOD (ns)", lambda m, c: c["CLOCK_PERIOD"]),
    ("setup WS all corners (ns)  [timing__setup__ws]", lambda m, c: m["timing__setup__ws"]),
    ("  worst corner", lambda m, c: min((v, k.split(":")[1]) for k, v in m.items()
                                         if k.startswith("timing__setup__ws__corner:"))[1]),
    (f"setup WS {TT} (ns)", lambda m, c: m[f"timing__setup__ws__corner:{TT}"]),
    ("setup TNS all corners (ns)", lambda m, c: m["timing__setup__tns"]),
    ("hold WS all corners (ns)", lambda m, c: m["timing__hold__ws"]),
    ("post-route Fmax, all-corner slack (MHz)", lambda m, c: 1000 / (c["CLOCK_PERIOD"] - m["timing__setup__ws"])),
    ("post-route Fmax, tt slack (MHz)", lambda m, c: 1000 / (c["CLOCK_PERIOD"] - m[f"timing__setup__ws__corner:{TT}"])),
    ("Magic DRC errors", lambda m, c: m["magic__drc_error__count"]),
    ("KLayout DRC errors", lambda m, c: m["klayout__drc_error__count"]),
    ("route DRC errors", lambda m, c: m["route__drc_errors"]),
    ("LVS errors", lambda m, c: m["design__lvs_error__count"]),
    ("antenna violating nets", lambda m, c: m["antenna__violating__nets"]),
    ("max slew violations", lambda m, c: m["design__max_slew_violation__count"]),
    ("max cap violations", lambda m, c: m["design__max_cap_violation__count"]),
    ("setup violations (count)", lambda m, c: m["timing__setup_vio__count"]),
    ("hold violations (count)", lambda m, c: m["timing__hold_vio__count"]),
    ("die area (um^2)", lambda m, c: m["design__die__area"]),
    ("core area (um^2)", lambda m, c: m["design__core__area"]),
    ("std-cell area (um^2)", lambda m, c: m["design__instance__area__stdcell"]),
    ("instance count, total  [design__instance__count]", lambda m, c: m["design__instance__count"]),
    ("  std cells (excl. fill)", lambda m, c: m["design__instance__count__stdcell"]),
    ("  fill cells", lambda m, c: m["design__instance__count__class:fill_cell"]),
    ("  tap cells", lambda m, c: m["design__instance__count__class:tap_cell"]),
    ("  clock buffers", lambda m, c: m["design__instance__count__class:clock_buffer"]),
    ("  timing-repair buffers", lambda m, c: m["design__instance__count__class:timing_repair_buffer"]),
    ("  inverters", lambda m, c: m["design__instance__count__class:inverter"]),
    ("  sequential cells", lambda m, c: m["design__instance__count__class:sequential_cell"]),
    ("  multi-input comb. cells", lambda m, c: m["design__instance__count__class:multi_input_combinational_cell"]),
    ("routed wirelength (um)  [route__wirelength]", lambda m, c: m["route__wirelength"]),
]


def fmt(v):
    return f"{v:.4f}" if isinstance(v, float) else str(v)


def main(runs):
    cols = []
    for r in runs:
        m = json.load(open(os.path.join(r, "final", "metrics.json")))
        c = json.load(open(os.path.join(r, "resolved.json")))
        cols.append((os.path.basename(os.path.normpath(r)), m, c))
    w = max(len(n) for n, _ in ROWS)
    print(f"{'metric':{w}s} | " + " | ".join(f"{n:>22s}" for n, _, _ in cols))
    for name, f in ROWS:
        vals = []
        for _, m, c in cols:
            try:
                vals.append(fmt(f(m, c)))
            except KeyError as e:
                vals.append(f"<missing {e}>")
        print(f"{name:{w}s} | " + " | ".join(f"{v:>22s}" for v in vals))


if __name__ == "__main__":
    main(sys.argv[1:])

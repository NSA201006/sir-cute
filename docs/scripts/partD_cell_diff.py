#!/usr/bin/env python3
"""Part D task 4: which kinds of cells did place-and-route add? Counts cell types from tool outputs only.

Usage (repo root):  python3 -I docs/scripts/partD_cell_diff.py pnr/runs/<run>
Sources:
  Part B netlist         synth/mult_array_netlist.v
  LibreLane synthesis    <run>/06-yosys-synthesis/mult_array.nl.v
  Final layout           <run>/final/def/mult_array.def   (COMPONENTS: every placed instance)
"""
import collections
import glob
import os
import re
import sys

KINDS = [  # (kind, regex on the cell name after the library prefix), first match wins
    ("fill", r"^fill_"),
    ("decap", r"^decap_"),
    ("tap", r"^tap"),
    ("diode", r"^diode"),
    ("clock buffer", r"^clkbuf_"),
    ("clock inverter", r"^clkinv"),
    ("delay buffer (dly*)", r"^(dlygate|dlymetal|clkdlybuf)"),
    ("buffer", r"^buf_"),
    ("inverter", r"^inv_"),
    ("flip-flop", r"^df"),
    ("logic", r"."),
]


def kind(cell):
    base = re.sub(r"^sky130_(fd|ef)_sc_hd__", "", cell)
    return next(k for k, rx in KINDS if re.search(rx, base))


def count_verilog(path):
    src = open(path).read()
    return collections.Counter(re.findall(r"^\s*(sky130_\w+)\s+\S+\s*\(", src, re.M))


def count_def(path):
    src = open(path).read()
    comp = src[src.index("COMPONENTS"):src.index("END COMPONENTS")]
    return collections.Counter(re.findall(r"^\s*-\s+\S+\s+(sky130_\w+)", comp, re.M))


def by_kind(cnt):
    k = collections.Counter()
    for cell, n in cnt.items():
        k[kind(cell)] += n
    return k


def main(run):
    srcs = [("Part B (synth.tcl)", count_verilog("synth/mult_array_netlist.v")),
            ("LibreLane synthesis", count_verilog(glob.glob(os.path.join(run, "*-yosys-synthesis", "mult_array.nl.v"))[0])),
            ("final layout (DEF)", count_def(os.path.join(run, "final", "def", "mult_array.def")))]
    kinds = [k for k, _ in KINDS]
    print(f"Run: {run}\n")
    print(f"{'cell kind':22s} | " + " | ".join(f"{n:>20s}" for n, _ in srcs))
    tot = [0] * len(srcs)
    for k in kinds:
        vals = [by_kind(c)[k] for _, c in srcs]
        tot = [t + v for t, v in zip(tot, vals)]
        if any(vals):
            print(f"{k:22s} | " + " | ".join(f"{v:>20d}" for v in vals))
    print(f"{'TOTAL':22s} | " + " | ".join(f"{t:>20d}" for t in tot))
    final, lsyn = srcs[2][1], srcs[1][1]
    print("\nCell types in the final layout that are NOT in LibreLane's synthesized netlist (added by the P&R flow):")
    for cell in sorted(set(final) - set(lsyn), key=lambda c: (kind(c), c)):
        print(f"  {cell:40s} x{final[cell]:<5d} [{kind(cell)}]")
    print("\nCell types whose count changed between LibreLane synthesis and the final layout (resizing/repair):")
    for cell in sorted(set(final) & set(lsyn)):
        if final[cell] != lsyn[cell]:
            print(f"  {cell:40s} {lsyn[cell]:>4d} -> {final[cell]:<4d}")
    gone = sorted(set(lsyn) - set(final))
    if gone:
        print("\nCell types present after synthesis but absent in the final layout (resized away):")
        for cell in gone:
            print(f"  {cell:40s} x{lsyn[cell]}")


if __name__ == "__main__":
    main(sys.argv[1])

#!/usr/bin/env python3
"""Print signal values from mult.vcd around one input vector (dependency-free VCD reader).

Usage (from the repo root, host or container):
    python3 -I docs/scripts/vcd_probe.py mult.vcd 13 7

Finds the first time the testbench applies a=<A>, b=<B>, then prints the value of every
dumped signal of interest at that time and at the next 4 clock edges (rising and falling).
"""
import sys


def parse_vcd(path):
    """Return (signals, changes): signals maps id -> list of full names; changes maps id -> [(t, value)]."""
    signals, changes, scope = {}, {}, []
    t = 0
    with open(path) as f:
        in_defs = True
        for line in f:
            tok = line.split()
            if not tok:
                continue
            if in_defs:
                if tok[0] == "$scope":
                    scope.append(tok[2])
                elif tok[0] == "$upscope":
                    scope.pop()
                elif tok[0] == "$var":
                    # $var <type> <width> <id> <name> [<range>] $end
                    ident, name = tok[3], tok[4]
                    rng = tok[5] if len(tok) > 6 else ""
                    signals.setdefault(ident, []).append(".".join(scope + [name]) + rng)
                    changes.setdefault(ident, [])
                elif tok[0] == "$enddefinitions":
                    in_defs = False
                continue
            # Value-change section is line-oriented: "#<time>", "b<bits> <id>", "<0|1|x|z><id>".
            # (Identifier codes may themselves contain '#', so only an all-digit "#..." is a time.)
            head = tok[0]
            if head[0] == "#" and head[1:].isdigit():
                t = int(head[1:])
            elif head[0] in "bBrR" and len(tok) == 2:
                changes[tok[1]].append((t, head[1:]))
            elif head[0] in "01xXzZ" and len(head) > 1:
                changes[head[1:]].append((t, head[0]))
    return signals, changes


def value_at(chg, t):
    v = "x"
    for tc, val in chg:
        if tc > t:
            break
        v = val
    return v


def fmt(v):
    if any(c in v for c in "xXzZ"):
        return v
    n = int(v, 2)
    return f"{n:>3} (0b{v})"


def main():
    path, A, B = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    signals, changes = parse_vcd(path)
    by_name = {n: i for i, names in signals.items() for n in names}

    def sig(name):
        for n, i in by_name.items():
            if n == name or n.split("[")[0] == name:
                return i
        return None

    a_id, b_id, clk_id = sig("tb_mult.a"), sig("tb_mult.b"), sig("tb_mult.clk")
    times = sorted({t for c in (changes[a_id], changes[b_id]) for t, _ in c})
    t0 = next(t for t in times
              if value_at(changes[a_id], t) not in "x" and int(value_at(changes[a_id], t), 2) == A
              and int(value_at(changes[b_id], t), 2) == B)
    edges = [(t, v) for t, v in changes[clk_id] if t > t0][:4]

    wanted = ["tb_mult.clk", "tb_mult.rst_n", "tb_mult.a", "tb_mult.b", "tb_mult.p",
              "tb_mult.dut.a_r", "tb_mult.dut.b_r", "tb_mult.dut.prod", "tb_mult.dut.carry"]
    dumped_dut = sorted({n.split("[")[0] for n in by_name if n.startswith("tb_mult.dut.")
                         and n.count(".") == 2})
    print(f"VCD: {path}   timescale units as in file (ps for this TB)")
    print("DUT-level signals present in the VCD:", ", ".join(dumped_dut))
    print("NOTE: unpacked net arrays (pp[], sums[]) are only listed above if iverilog dumped them.\n")
    points = [(t0, f"t={t0} inputs applied")] + \
             [(t, f"t={t} clk {'rise' if v == '1' else 'fall'}") for t, v in edges]
    for t, label in points:
        print(f"--- {label}")
        for w in wanted:
            i = sig(w)
            if i is not None:
                print(f"    {w:20s} = {fmt(value_at(changes[i], t))}")


if __name__ == "__main__":
    main()

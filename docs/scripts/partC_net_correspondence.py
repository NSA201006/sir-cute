#!/usr/bin/env python3
"""Part C extra: map each critical-path net of the synthesized netlist back to the RTL full adders.

Method (exhaustive and tool-based, no hand modelling):
  * gen   : write two probe testbenches. Both apply all 256 (a, b) pairs and, one clock edge later
            (a_r, b_r = a, b; combinational logic settled), print a line of values.
              - GATE build: every wire of synth/mult_array_netlist.v
              - RTL  build: dut.a_r, dut.b_r, dut.pp[i], and dut.faK.{a,b,cin,sum,cout} for K = 1..12
  * match : build a 256-entry truth table per signal and report, for every netlist net, which RTL
            signals (or their complements) have the identical truth table.
Driver: docs/scripts/partC_net_correspondence.sh
"""
import re
import sys

CRIT = ["a_r[1]", "_00_", "_11_", "_15_", "_20_", "_27_", "_29_", "_31_", "fa12.sum"]
CRIT_CELLS = {"_00_": "_37_ clkinv_1", "_11_": "_41_ o311ai_0", "_15_": "_45_ a21oi_1",
              "_20_": "_51_ maj3_1", "_27_": "_58_ xnor3_1", "_29_": "_61_ maj3_1",
              "_31_": "_63_ maj3_1", "fa12.sum": "_64_ xor3_1", "a_r[1]": "_91_ dfrtp_1 (Q)"}


def netlist_wires(path):
    """Return [(display_name, hier_ref, width)] for every wire in the netlist."""
    out = []
    for m in re.finditer(r"^\s*wire\s+(\[(\d+):(\d+)\]\s*)?(\\\S+|\w+)\s*;", open(path).read(), re.M):
        name = m[4]
        width = int(m[2]) - int(m[3]) + 1 if m[1] else 1
        ref = f"dut.{name} " if name.startswith("\\") else f"dut.{name}"
        out.append((name.lstrip("\\"), ref, width))
    return out


TB = """`timescale 1ns/1ps
module tb_probe;
  reg clk = 0, rst_n = 0; reg [3:0] a = 0, b = 0; wire [7:0] p; integer i, k;
  mult_array dut(.clk(clk), .rst_n(rst_n), .a(a), .b(b), .p(p));
  always #5 clk = ~clk;
  initial begin
    repeat (2) @(posedge clk); @(negedge clk) rst_n = 1;
    for (i = 0; i < 16; i = i + 1) for (k = 0; k < 16; k = k + 1) begin
      a = i; b = k;
      @(posedge clk); @(negedge clk);   // a_r, b_r now hold (i, k); logic settled
      $display("V %0d %0d %s", i, k, {FMT});
    end
    $finish;
  end
endmodule
"""


def gen(netlist, out_gate, out_rtl, names_file):
    wires = netlist_wires(netlist)
    fmt_g = '{$sformatf("' + " ".join(["%b"] * len(wires)) + '", ' + ", ".join(w[1] for w in wires) + ")}"
    open(out_gate, "w").write(TB.replace("{FMT}", fmt_g))
    rtl_refs = ["dut.a_r", "dut.b_r"] + [f"dut.pp[{i}]" for i in range(4)]
    for k in range(1, 13):
        rtl_refs += [f"dut.fa{k}.{p}" for p in ("a", "b", "cin", "sum", "cout")]
    fmt_r = '{$sformatf("' + " ".join(["%b"] * len(rtl_refs)) + '", ' + ", ".join(rtl_refs) + ")}"
    open(out_rtl, "w").write(TB.replace("{FMT}", fmt_r))
    with open(names_file, "w") as f:
        f.write("GATE " + " ".join(f"{n}:{w}" for n, _, w in wires) + "\n")
        f.write("RTL " + " ".join(r.replace("dut.", "") for r in rtl_refs) + "\n")


def read_tables(path, names_widths):
    """names_widths: [(name, width)] -> {bit_name: tuple of 256 chars}"""
    rows = [l.split()[3:] for l in open(path) if l.startswith("V ")]
    assert len(rows) == 256, f"{path}: expected 256 vectors, got {len(rows)}"
    tables = {}
    for col, (name, width) in enumerate(names_widths):
        for bit in range(width):
            key = name if width == 1 else f"{name}[{width - 1 - bit}]"
            tables[key] = tuple(r[col][bit] for r in rows)
    return tables


def match(names_file, gate_out, rtl_out):
    lines = open(names_file).read().splitlines()
    gate_nw = [(t.rsplit(":", 1)[0], int(t.rsplit(":", 1)[1])) for t in lines[0].split()[1:]]
    rtl_names = lines[1].split()[1:]
    rtl_nw = [(n, 4 if n.startswith(("pp[", "a_r", "b_r")) else 1) for n in rtl_names]
    G, R = read_tables(gate_out, gate_nw), read_tables(rtl_out, rtl_nw)

    # Candidate RTL signals: every FA port, FA-internal terms, and partial products (+ complements).
    cand = {}
    inv = lambda t: tuple({"0": "1", "1": "0"}.get(c, c) for c in t)
    op = lambda f, *ts: tuple(str(f(*(int(c) for c in cs))) for cs in zip(*ts))
    for n, t in R.items():
        cand[n] = t
    for k in range(1, 13):
        a, b, c = R[f"fa{k}.a"], R[f"fa{k}.b"], R[f"fa{k}.cin"]
        cand[f"fa{k}.(a^b)"] = op(lambda x, y: x ^ y, a, b)
        cand[f"fa{k}.(a&b)"] = op(lambda x, y: x & y, a, b)
        cand[f"fa{k}.(a|b)"] = op(lambda x, y: x | y, a, b)
        cand[f"fa{k}.((a^b)&cin)"] = op(lambda x, y, z: (x ^ y) & z, a, b, c)
    for n, t in list(cand.items()):
        cand["~" + n] = inv(t)

    def hits(t):
        if len(set(t)) == 1:
            return ["<constant " + t[0] + ">"]
        return [n for n, ct in cand.items() if ct == t] or ["<no RTL match: merged logic>"]

    print("Critical-path nets of synth/mult_array_netlist.v vs RTL signals (identical 256-entry truth tables):")
    for net in CRIT:
        hs = hits(G[net])
        print(f"  {CRIT_CELLS[net]:22s} output {net:9s} == " + ", ".join(sorted(hs, key=len)))
    matched = sum(1 for n in G if not hits(G[n])[0].startswith("<"))
    print(f"\nAll netlist nets: {len(G)} bits; {matched} have at least one RTL match.")


if __name__ == "__main__":
    if sys.argv[1] == "gen":
        gen(*sys.argv[2:6])
    else:
        match(*sys.argv[2:5])

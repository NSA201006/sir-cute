#!/usr/bin/env python3
"""Add a caption to the GTKWave capture, marking the 2-cycle latency between named markers A and B.
Usage: python3 -I docs/scripts/annotate_wave.py raw.png out.png
Marker columns are found from the pixels themselves (GTKWave 4 draws markers in light yellow, RGB (255, 255, 128), measured).
"""
import sys

from PIL import Image, ImageDraw, ImageFont


def marker_columns(img, y0=90, y1=190):
    px = img.load()
    cols = []
    for x in range(img.width):
        n = sum(1 for y in range(y0, min(y1, img.height)) if px[x, y][0] > 200 and px[x, y][1] > 200 and px[x, y][2] < 170)
        if n >= 5:
            cols.append(x)
    groups = []
    for x in cols:  # merge adjacent columns
        if groups and x - groups[-1][-1] <= 2:
            groups[-1].append(x)
        else:
            groups.append([x])
    return [sum(g) // len(g) for g in groups]


def main(src, dst):
    raw = Image.open(src).convert("RGB")
    xs = marker_columns(raw)
    assert len(xs) == 2, f"expected 2 marker columns (A, B), found {xs}"
    xa, xb = xs
    pad = 120
    img = Image.new("RGB", (raw.width, raw.height + pad), "white")
    img.paste(raw, (0, 0))
    d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype("DejaVuSans.ttf", 15)
        fb = ImageFont.truetype("DejaVuSans-Bold.ttf", 15)
    except OSError:
        f = fb = ImageFont.load_default()
    y = raw.height + 18
    for x in (xa, xb):
        d.line([(x, raw.height), (x, y + 8)], fill="black", width=2)
    d.line([(xa, y + 8), (xb, y + 8)], fill="red", width=3)
    for x in (xa, xb):
        d.polygon([(x, y + 8), (x + (8 if x == xa else -8), y + 3), (x + (8 if x == xa else -8), y + 13)], fill="red")
    d.text((xa - 150, y - 4), "edge 1 (A, 4325 ns)", fill="black", font=f)
    d.text((xb + 10, y - 4), "edge 2 (B, 4335 ns)", fill="black", font=f)
    d.text((xa + 12, y + 14), "latency = 2 clock cycles", fill="red", font=fb)
    d.text((10, y + 42), "Example A = 13, B = 7 (roll no. 2023102038 -> 8 + 5 = 13).  a, b applied at 4320 ns (falling edge); "
           "captured into a_r, b_r at rising edge 1 (marker A, p still 78 = 13 x 6);", fill="black", font=f)
    d.text((10, y + 64), "product captured into p at rising edge 2 (marker B): p = 91 = 13 x 7.  "
           "RTL simulation (iverilog), viewed in GTKWave 4.0.0-prealpha; clock period 10 ns.", fill="black", font=f)
    img.save(dst)
    print(f"wrote {dst}: markers at x={xa}, x={xb}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

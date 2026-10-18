#!/usr/bin/env python3
"""Convert an X11 window dump (xwd, ZPixmap, 24/32 bpp TrueColor) to PNG with PIL.
Usage: python3 -I docs/scripts/xwd2png.py in.xwd out.png [crop_w crop_h]
"""
import struct
import sys

from PIL import Image


def main(src, dst, crop=None):
    data = open(src, "rb").read()
    # Header = 25 CARD32 fields; detect byte order from header_size (must be >= 100 and small).
    for e in (">", "<"):
        h = struct.unpack(e + "25I", data[:100])
        if 100 <= h[0] < 4096:
            break
    (header_size, _ver, fmt, depth, width, height, _xoff, byte_order, _bu, _bbo, _pad,
     bpp, bpl, _vc, rmask, gmask, bmask, _bprgb, _cmap_entries, ncolors) = h[:20]
    assert fmt == 2 and bpp in (24, 32), f"unsupported xwd: format={fmt} bpp={bpp}"
    off = header_size + 12 * ncolors
    raw = data[off:off + bpl * height]
    if bpp == 32:
        mode = "BGRX" if (byte_order == 0) == (rmask == 0xFF0000) else "XRGB"
    else:
        mode = "BGR" if byte_order == 0 else "RGB"
    img = Image.frombuffer("RGB", (width, height), raw, "raw", mode, bpl, 1)
    if crop:
        img = img.crop((0, 0, crop[0], crop[1]))
    img.save(dst)
    print(f"wrote {dst} {img.size[0]}x{img.size[1]} (xwd {width}x{height}, depth {depth}, bpp {bpp})")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], tuple(int(v) for v in sys.argv[3:5]) if len(sys.argv) >= 5 else None)

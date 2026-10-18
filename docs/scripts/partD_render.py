# Headless KLayout render of a GDS (whole die or a zoom box), using the PDK layer properties.
# Run INSIDE the container from the repo root, e.g.
#   klayout -z -nc -rx -r docs/scripts/partD_render.py -rd gds=pnr/mult_array.gds \
#           -rd out=docs/images/partD_zoom.png -rd box=55,60,85,90 -rd px=1600
# Variables (-rd): gds (required), out (required), box "x1,y1,x2,y2" in um (optional; default = whole die),
#                  px image width/height in pixels (optional, default 1600)
import os
import pya

lyp = os.path.join(os.environ["PDK_ROOT"], "sky130A", "libs.tech", "klayout", "tech", "sky130A.lyp")
size = int(globals().get("px", "1600"))

lv = pya.LayoutView()
lv.set_config("background-color", "#ffffff")
lv.set_config("grid-visible", "false")
lv.set_config("text-visible", "false")
lv.load_layout(gds, True)
lv.load_layer_props(lyp)
lv.max_hier()
box = globals().get("box", "")
if box:
    x1, y1, x2, y2 = (float(v) for v in box.split(","))
    lv.zoom_box(pya.DBox(x1, y1, x2, y2))
else:
    lv.zoom_fit()
lv.save_image(out, size, size)
print(f"wrote {out} ({size}x{size}), box={box or 'whole die'}")

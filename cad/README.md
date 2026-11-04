# cad/ — enclosure sources (OpenSCAD)

| File | What |
|---|---|
| `params.scad` | shared dimensions: walls, clearances, insert sizes, stack heights (several marked verify) |
| `lib/pi5.scad` | Pi 5 outline, hole pattern, standoff bosses, keep-out volume |
| `tray-v0.scad` | the first printable part: a bench tray for the Pi over an NVMe base |
| `lib/display2.scad`, `lib/gopro.scad`, `lib/cells.scad`, `slab.scad`, `mounts/` | not written yet; see docs/05-enclosure.md |

Render from the command line (OpenSCAD 2021.01 or newer; the nightly builds are much faster):

```
openscad -o out/tray-v0.stl tray-v0.scad
```

`out/` is gitignored; STLs are build outputs. Tag a release when a version is printed and fits.

Before trusting any part: print the fit-test coupons (standoff plate, GoPro mount pair, 21700
holder, button plunger) and measure them. Every number in `params.scad` marked *verify* was taken
from vendor pages, not from a part on the desk.

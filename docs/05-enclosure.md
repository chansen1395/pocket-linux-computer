# 05 — Enclosure

> Status: superseded in part by [decision 0010](decisions/0010-compact-layout.md), which moves to a 5-inch
> display and a smaller footprint. The sizes and layout below describe the original 7-inch slab plan.

## 1. Architecture: one core, many mounts

Instead of three devices (laptop, handheld, arm computer) we build **one slab** and swap what it
attaches to.

```
            ┌───────────────────────────────────┐
            │  7" Touch Display 2 (190 × 120 mm) │   lid / face
            ├───────────────────────────────────┤
            │ Pi 5 + NVMe base │ 4× 21700 UPS    │   core bay, side by side
            │ cooler, encoder  │ board + cells   │
            └──────────┬────────────────┬────────┘
                mount standard      mount standard
         ┌─────────────┴──┐   ┌─────────┴──────────┐  ┌──────────────┐
         │ forearm cradle │   │ belt / MOLLE clip  │  │ keyboard base │
         │ (TPU straps)   │   │                    │  │ (clamshell)   │
         └────────────────┘   └────────────────────┘  └──────────────┘
```

- **The slab** holds everything electronic. Target: 195 × 125 × 28 mm, ~650 g with cells.
- **The mount standard** is the **GoPro three-prong mount**: cheap, printable in PETG, tolerant of
  print variation, and the accessory ecosystem already includes wrist straps, chest harnesses,
  clips, suction cups and tripod adapters. Two female mounts on the back of the slab (top and bottom
  of the long axis) so a cradle can grab it in landscape.
- **The keyboard base** (clamshell) uses the same mounts as hinges; the slab folds flat onto the
  keyboard for the bag.
- **Forearm cradle:** a curved PETG shell with TPU-printed straps (or a sewn neoprene sleeve with
  Velcro) and a shade hood. The slab sits in landscape along the forearm.
- **Belt / bag:** a MOLLE-compatible clip and a padded sleeve with a lanyard point.

## 2. Slab internals

| Zone | Contents | Notes |
|---|---|---|
| Face | Display, with a 1.5 mm lip and a replaceable 1 mm PET/acrylic screen protector | Touch works through thin PET |
| Bay A | Pi 5 on 4 heat-set M2.5 standoffs, NVMe base beneath, Active Cooler on top | Vents under the fan and out the side; cooler needs ~12 mm above the board |
| Bay B | UPS board + 4× 21700 cells | Cells are the heaviest item; place them under the palm side for balance |
| Edge | USB-C power-in (passthrough to the UPS), 1× USB-A, micro-HDMI, the Pi's power button via a printed plunger | Everything else stays inside |
| Controls | Rotary encoder with push on the top-right corner, 4 tactile buttons along the right edge | Glove-sized caps |
| Back | 2× GoPro female mounts, 1/4-20 insert, passive vents, cell-door with captive screws | |
| Antennas | Wi-Fi is on the Pi; LoRa and GPS get internal patch/whip antennas routed to the top edge, away from the hand | |

Thermal: the Active Cooler's fan exhausts through side vents; the back panel carries a 2 mm aluminum
plate that bridges the SoC heatsink to the outside for the sealed-on-arm case. Measure before trusting.

## 3. CAD approach: OpenSCAD, parametric, in git

Everything is code so Claude Code can iterate on it with us and every version is a commit.

```
cad/
  lib/pi5.scad        Pi 5 outline, holes, keep-outs (dimensions from the official drawing)
  lib/display2.scad   Touch Display 2 outline and mounting (TODO: from the official drawing)
  lib/gopro.scad      GoPro male/female mount (TODO: print a test piece before trusting)
  lib/cells.scad      21700 cell holder cut-outs
  slab.scad           the core enclosure, assembled from the libs
  mounts/*.scad       cradle, clip, keyboard base
  out/                STLs (gitignored; regenerate with openscad -o)
```

- Shared `params.scad` for wall thickness (2.4 mm = 6 perimeters at 0.4 mm), clearance (0.3 mm),
  heat-set insert diameters, screw sizes.
- `openscad -o out/slab.stl slab.scad` in a `make` target; print profiles stored next to the STLs.
- FreeCAD or CadQuery if we need real fillets and STEP export later; the OpenSCAD files remain the spec.

## 4. Printing

| | Choice | Why |
|---|---|---|
| Structural parts | PETG, 0.2 mm layers, 6 walls, 25 % gyroid | Survives a hot Pi; PLA creeps at 60 °C |
| Outdoor / sun | ASA | UV-stable; needs an enclosed printer |
| Straps, bumpers, button caps | TPU 95A | |
| Fasteners | M2.5 (Pi), M3 (case), heat-set brass inserts | No printed threads for anything that gets opened |
| Finish | Light sanding; optional primer + paint | |

Print the **fit-test coupons** first: a Pi 5 standoff plate, a GoPro mount pair, a 21700 holder, a
button plunger. Thirty minutes of plastic saves a day of re-prints.

## 5. Iteration plan

1. **v0 — tray.** Flat plate with Pi standoffs, NVMe base, and the display on a hinge. Proves cables and thermals.
2. **v1 — slab.** Closed box, power bank in an external pocket, encoder and buttons live.
3. **v2 — integrated power.** UPS board and cells inside, cell door, USB-C passthrough.
4. **v3 — mounts.** Forearm cradle, clip, keyboard base; TPU straps; hood.
5. **v4 — weather.** Gaskets, port covers, conformal coating on exposed boards.

Each version is a tag in git with its STLs attached as release artifacts.

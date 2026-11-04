// Raspberry Pi 5 reference geometry for enclosure design.
// Board outline and mounting holes are the standard Pi B+ pattern (85 x 56, holes 58 x 49 on
// 3.5 mm offsets) and are reliable. Port cut-outs are NOT modeled yet: take them from the
// official drawing, https://datasheets.raspberrypi.com/rpi5/raspberry-pi-5-mechanical-drawing.pdf
// Origin: bottom-left corner of the PCB, PCB top surface at z = pcb_t, SD-card edge at x = 0.

include <../params.scad>

pi5_w = 85;
pi5_d = 56;
pi5_r = 3.0;                       // corner radius
pi5_holes = [[3.5, 3.5], [3.5, 52.5], [61.5, 3.5], [61.5, 52.5]];

module rounded_rect(w, d, r) {
    hull() for (x = [r, w - r], y = [r, d - r]) translate([x, y]) circle(r = r);
}

// The bare PCB with its holes, for visual checks and subtraction.
module pi5_board(t = pi_pcb_t) {
    difference() {
        linear_extrude(t) rounded_rect(pi5_w, pi5_d, pi5_r);
        for (h = pi5_holes) translate([h[0], h[1], -1]) cylinder(d = m25_hole, h = t + 2);
    }
}

// Rough keep-out volume above the board: the Active Cooler and connectors. Use for clearance checks.
module pi5_keepout(h = cooler_h) {
    translate([0, 0, pi_pcb_t]) linear_extrude(h) offset(delta = 1) rounded_rect(pi5_w, pi5_d, pi5_r);
}

// Four standoff bosses with heat-set insert holes, ready to be unioned into a tray floor.
module pi5_standoffs(height = 6, od = 6.5, insert_d = insert_m25, insert_depth = 4) {
    for (h = pi5_holes) translate([h[0], h[1], 0]) difference() {
        cylinder(d = od, h = height);
        translate([0, 0, height - insert_depth]) cylinder(d = insert_d, h = insert_depth + 1);
    }
}

// Through-holes matching the Pi pattern, for subtracting from a plate.
module pi5_hole_pattern(d = m25_hole, h = 20) {
    for (p = pi5_holes) translate([p[0], p[1], -h / 2]) cylinder(d = d, h = h);
}

// This file is meant to be included by parts (include <lib/pi5.scad>), so it draws nothing itself.
// To look at it alone: openscad -D 'pi5_board();' or open and uncomment the next line.
// color("green") pi5_board(); %pi5_keepout();

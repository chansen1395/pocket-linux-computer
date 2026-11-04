// Pocket v0 "tray": a flat bench plate that holds the Pi 5 over an NVMe base, with a lip and
// vent slots. Purpose: prove cables, thermals and the stack height before the slab (v1).
// Render: openscad -o out/tray-v0.stl tray-v0.scad

include <lib/pi5.scad>     // brings in params.scad, the Pi dimensions and the helper modules

margin   = 6;                       // plate margin around the board
plate_w  = pi5_w + 2 * margin;
plate_d  = pi5_d + 2 * margin;
lip_h    = 8;                       // low wall; keeps the stack from sliding, leaves ports open
post_h   = nvme_base_h + 3;         // standoffs tall enough to clear the NVMe base beneath the Pi

module vents(n = 7, len = 30, w = 2.2) {
    for (i = [0 : n - 1])
        translate([plate_w / 2 - len / 2, margin + 6 + i * 6, -1])
            cube([len, w, floor_t + 2]);
}

module tray() {
    difference() {
        union() {
            // floor with a lip around three sides (the SD-card edge stays open for the rescue card)
            linear_extrude(floor_t) rounded_rect(plate_w, plate_d, 4);
            difference() {
                linear_extrude(lip_h) rounded_rect(plate_w, plate_d, 4);
                translate([wall, wall, -1]) linear_extrude(lip_h + 2) rounded_rect(plate_w - 2 * wall, plate_d - 2 * wall, 2);
                translate([-1, wall + 4, -1]) cube([wall + 2, plate_d - 2 * wall - 8, lip_h + 2]);   // SD edge opening
            }
            translate([margin, margin, 0]) pi5_standoffs(height = post_h);
        }
        vents();
        // strap slots for a power bank or a hook-and-loop strap under the tray
        for (x = [plate_w * 0.25, plate_w * 0.75]) translate([x - 2, -1, -1]) cube([4, plate_d + 2, floor_t + 2]);
    }
}

tray();

if ($preview) translate([margin, margin, post_h]) %pi5_board();

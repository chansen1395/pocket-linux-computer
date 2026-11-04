// Pocket shared CAD parameters. Every part includes this file. Units: mm.

$fn = 48;

wall       = 2.4;   // 6 perimeters at 0.4 mm
floor_t    = 2.0;
clear      = 0.3;   // general print clearance per side
fit        = 0.15;  // tight fit for press parts

// fasteners
m25_hole   = 2.7;   // M2.5 clearance (Pi mounting holes)
m3_hole    = 3.4;
insert_m25 = 3.5;   // heat-set insert hole diameter, M2.5 (verify with your inserts)
insert_m3  = 4.0;   // heat-set insert hole diameter, M3

// stack heights (verify on the bench; see docs/research/open-questions.md)
pi_pcb_t        = 1.6;
nvme_base_h     = 10.0;  // Pimoroni NVMe Base below the Pi, standoff to standoff
cooler_h        = 12.0;  // Active Cooler above the PCB
display_t       = 10.0;  // Touch Display 2 module thickness, glass to back of the PCB (verify)
cell_d          = 21.5;  // 21700 cell diameter with wrap
cell_l          = 71.0;  // 21700 length, protected cells are longer (verify)

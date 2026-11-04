# 0002 — 2 TB NVMe on a bottom-mount 2280 base, boot from NVMe, rescue microSD

Status: proposed (2026-10-16)

**Context.** 2 TB target; the official M.2 HAT+ only takes 2230/2242, where 2 TB costs about double.

**Decision.** Pimoroni NVMe Base (or an equivalent 2280 bottom board) with a drive from its tested list; EEPROM BOOT_ORDER=0xf416; PCIe Gen 3 enabled only after a week of stable Gen 2 use; microSD rescue image always present.

**Alternatives.** Official M.2 HAT+ with a 2 TB 2230 drive (cleaner, pricier). USB SSD (slower, a cable, a port).

**Consequences.** Adds about 10 mm under the Pi; enclosure bay A must allow it. Gen 3 stability is an open question.

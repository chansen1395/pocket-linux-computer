# 0004 — Power: USB-C PD bank first, 4x 21700 UPS board second

Status: proposed (2026-10-16)

**Context.** Nothing is measured yet, and the Pi 5 wants 5 V / 5 A for full USB current.

**Decision.** Phase 1 runs from a 20 000 mAh USB-C PD bank in an external pocket. Phase 2 moves to a 4-cell 21700 UPS board (Waveshare UPS HAT (E) first candidate, Geekworm X1206 second) with cells under 100 Wh total.

**Alternatives.** 2-cell boards (lighter, half the runtime); a custom 2S2P pack with PD charger, buck and fuel gauge (phase 3 fallback).

**Consequences.** Real consumption numbers before committing money to cells; the slab v1 has a bank pocket, v2 has a cell bay.

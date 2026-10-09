#!/usr/bin/env python3
"""Tecan-ready PyLabRobot script for the toy SPPS demonstration job.

This version is written to match the real PyLabRobot/Tecan pattern:
- trough_1 (grid 3, site 1): compartments for piperidine, DCE, DMF (and DMSO, unused)
- trough_2 (grid 3, site 2): four amino acid compartments (AA1..AA4)
- plate (grid 17, site 2): 96-well flat-bottom destination plate
- 8 fixed (steel) LiHa tips, one dedicated to each liquid (see LIQUID_CHANNELS)

Deck positions are defined in ``ccas_deck.py`` (see ``ccas_deck.png``).

The script encodes the requested logic:
1. All ordered 4-AA combinations across the plate
2. Remaining wells use all ordered 2-AA combinations
3. For each amino acid in a well's sequence:
      Fmoc-AA -> DMF -> DCE -> piperidine
4. Repeat the sequence set as needed to fill all 96 wells

This script is intended for execution on a machine where PyLabRobot and the
Tecan EVO driver stack are installed. Confirm the grid/site constants in
``ccas_deck.py`` match the actual deck before running on hardware.
"""

from __future__ import annotations

import asyncio
from itertools import permutations
try:
    from pylabrobot.liquid_handling import LiquidHandler
    from pylabrobot.liquid_handling.backends import EVOBackend
    from pylabrobot.resources.tecan.tip_creators import standard_fixed_tip
    from ccas_deck import AA_SOURCE_WELLS, REAGENT_WELLS, build_deck
except ImportError:  # pragma: no cover - enables syntax checking in minimal environments
    LiquidHandler = None
    EVOBackend = None

AA_ORDER = ["AA1", "AA2", "AA3", "AA4"]
VOLUME_UL = 25.0

# Fixed tips are never changed, so each liquid gets its own channel (0 = rear-most tip) to avoid
# carrying one reagent into another. PLR 0.2.1 has no fixed-tip wash command, so this replaces
# washing between reagents within a run; wash the tips in EVOware before and after a run.
# trough_1 is at the rear site, so it uses the rear channels: when channel k is over a well,
# channel 0 sits k * 9 mm further back and must stay inside the LiHa's Y range.
# Channel 7 is spare.
LIQUID_CHANNELS = {
    "PIPERIDINE": 0,
    "DCE": 1,
    "DMF": 2,
    "AA1": 3,
    "AA2": 4,
    "AA3": 5,
    "AA4": 6,
}


def build_unique_sequence_set() -> list[list[str]]:
    """Return all ordered 4-AA permutations and all ordered 2-AA permutations."""
    four_aa = [list(seq) for seq in permutations(AA_ORDER, 4)]
    two_aa = [list(seq) for seq in permutations(AA_ORDER, 2)]
    return four_aa + two_aa


def build_plate_sequence_plan(total_wells: int = 96) -> list[list[str]]:
    """Expand the unique sequence set to cover the full 96-well plate."""
    unique = build_unique_sequence_set()
    plan: list[list[str]] = []
    while len(plan) < total_wells:
        for seq in unique:
            if len(plan) >= total_wells:
                break
            plan.append(seq)
    return plan


def build_plate_wells() -> list[str]:
    """Return standard 96-well coordinates in A1..H12 order."""
    rows = [chr(i) for i in range(ord("A"), ord("H") + 1)]
    cols = list(range(1, 13))
    return [f"{row}{col}" for row in rows for col in cols]


def mount_fixed_tips(lih: LiquidHandler) -> None:
    """Tell PLR every channel permanently carries a fixed tip (no pick-up or drop moves)."""
    lih.update_head_state(
        {ch: standard_fixed_tip(name=f"fixed_tip_{ch + 1}") for ch in range(lih.backend.num_channels)}
    )


async def transfer(lih: LiquidHandler, liquid: str, source, destination) -> None:
    """Aspirate from source and dispense to destination on the liquid's dedicated channel."""
    channel = LIQUID_CHANNELS[liquid]
    await lih.aspirate(source, vols=[VOLUME_UL], use_channels=[channel])
    await lih.dispense(destination, vols=[VOLUME_UL], use_channels=[channel])


async def run_well_sequence(lih: LiquidHandler, well_name: str, amino_acid_order: list[str]) -> None:
    """Execute the request for a single well: AA -> DMF -> DCE -> piperidine, repeated per AA."""
    plate = lih.deck.get_resource("plate")
    trough_1 = lih.deck.get_resource("trough_1")
    trough_2 = lih.deck.get_resource("trough_2")

    for aa in amino_acid_order:
        await transfer(lih, aa, trough_2[AA_SOURCE_WELLS[aa]], plate[well_name])
        for reagent in ("DMF", "DCE", "PIPERIDINE"):
            await transfer(lih, reagent, trough_1[REAGENT_WELLS[reagent]], plate[well_name])
        print(f"Well {well_name}: completed {aa}")


async def run_plate(lih: LiquidHandler) -> None:
    """Run the full 96-well combinatorial job."""
    plate_wells = build_plate_wells()
    sequence_plan = build_plate_sequence_plan(total_wells=96)

    for well_index, well_name in enumerate(plate_wells):
        aa_order = sequence_plan[well_index]
        print(f"Executing well {well_name} with amino acid order: {aa_order}")
        await run_well_sequence(lih, well_name, aa_order)


async def main() -> None:
    deck = build_deck()
    lih = LiquidHandler(backend=EVOBackend(diti_count=0), deck=deck)  # 0 DiTi channels: all fixed
    await lih.setup()
    mount_fixed_tips(lih)

    try:
        await run_plate(lih)
    finally:
        await lih.stop()


if __name__ == "__main__":
    if LiquidHandler is None or EVOBackend is None:
        raise RuntimeError(
            "PyLabRobot and the Tecan EVO backend are not installed in this Python environment. "
            "Install the Tecan driver stack and PyLabRobot before running on the robot."
        )
    asyncio.run(main())

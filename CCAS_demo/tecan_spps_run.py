#!/usr/bin/env python3
"""Tecan-ready PyLabRobot script for the toy SPPS demonstration job.

This version is written to match the real PyLabRobot/Tecan pattern:
- A1: trough with reagent wells for DMF, DCE, and piperidine
- A2: trough with four amino acid wells (AA1..AA4)
- B2: 96-well flat-bottom destination plate
- 8 reusable LiHa tips via shared-tip strategy

The script encodes the requested logic:
1. All ordered 4-AA combinations across the plate
2. Remaining wells use all ordered 2-AA combinations
3. For each amino acid in a well's sequence:
      Fmoc-AA -> DMF -> DCE -> piperidine
4. Repeat the sequence set as needed to fill all 96 wells

This script is intended for execution on a machine where PyLabRobot and the
Tecan EVO driver stack are installed. Update the deck JSON file to match your
actual deck coordinates before running on hardware.
"""

from __future__ import annotations

import asyncio
from itertools import permutations
from pathlib import Path

try:
    from pylabrobot.liquid_handling import LiquidHandler
    from pylabrobot.liquid_handling.backends import EVOBackend
except ImportError:  # pragma: no cover - enables syntax checking in minimal environments
    LiquidHandler = None
    EVOBackend = None

AA_ORDER = ["AA1", "AA2", "AA3", "AA4"]
AA_SOURCE_WELLS = {"AA1": "A1", "AA2": "A2", "AA3": "A3", "AA4": "A4"}
REAGENT_WELLS = {"DMF": "A1", "DCE": "A2", "PIPERIDINE": "A3"}


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


async def pick_shared_tip(lih: LiquidHandler, tip_index: int) -> str:
    """Pick a reusable tip from the 8-position shared-tip rack."""
    tip_rack = lih.deck.get_resource("tip_rack")
    tip_positions = [f"A{i}" for i in range(1, 9)]
    tip_pos = tip_positions[tip_index % len(tip_positions)]
    await lih.pick_up_tips(tip_rack[tip_pos])
    return tip_pos


async def run_well_sequence(lih: LiquidHandler, well_name: str, amino_acid_order: list[str]) -> None:
    """Execute the request for a single well: AA -> DMF -> DCE -> piperidine, repeated per AA."""
    plate = lih.deck.get_resource("plate")
    trough_1 = lih.deck.get_resource("trough_1")
    trough_2 = lih.deck.get_resource("trough_2")
    aspirate_dispense_volume = 25.0

    for aa_index, aa in enumerate(amino_acid_order):
        tip_name = await pick_shared_tip(lih, aa_index)
        try:
            await lih.aspirate(trough_2[AA_SOURCE_WELLS[aa]], vols=aspirate_dispense_volume)
            await lih.dispense(plate[well_name], vols=aspirate_dispense_volume)

            await lih.aspirate(trough_1[REAGENT_WELLS["DMF"]], vols=aspirate_dispense_volume)
            await lih.dispense(plate[well_name], vols=aspirate_dispense_volume)

            await lih.aspirate(trough_1[REAGENT_WELLS["DCE"]], vols=aspirate_dispense_volume)
            await lih.dispense(plate[well_name], vols=aspirate_dispense_volume)

            await lih.aspirate(trough_1[REAGENT_WELLS["PIPERIDINE"]], vols=aspirate_dispense_volume)
            await lih.dispense(plate[well_name], vols=aspirate_dispense_volume)
        finally:
            await lih.return_tips()
            print(f"Well {well_name}: completed {aa} using reusable tip {tip_name}")


async def run_plate(lih: LiquidHandler) -> None:
    """Run the full 96-well combinatorial job."""
    plate_wells = build_plate_wells()
    sequence_plan = build_plate_sequence_plan(total_wells=96)

    for well_index, well_name in enumerate(plate_wells):
        aa_order = sequence_plan[well_index]
        print(f"Executing well {well_name} with amino acid order: {aa_order}")
        await run_well_sequence(lih, well_name, aa_order)


async def main() -> None:
    deck_path = Path(__file__).with_name("tecan_deck_layout.json")
    if not deck_path.exists():
        raise FileNotFoundError(
            "Deck layout file not found: "
            f"{deck_path}. Update the file to match the real Tecan deck before running."
        )

    deck = Deck.load_from_json_file(str(deck_path))
    lih = LiquidHandler(backend=EVOBackend(), deck=deck)
    await lih.setup()

    try:
        await run_plate(lih)
    finally:
        await lih.teardown()


if __name__ == "__main__":
    if LiquidHandler is None or EVOBackend is None:
        raise RuntimeError(
            "PyLabRobot and the Tecan EVO backend are not installed in this Python environment. "
            "Install the Tecan driver stack and PyLabRobot before running on the robot."
        )
    asyncio.run(main())

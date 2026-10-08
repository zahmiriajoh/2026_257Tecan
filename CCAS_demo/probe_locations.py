#!/usr/bin/env python3
"""Probe A1/A2 trough positions for a toy SPPS-style LiHa workflow.

This script is intentionally limited to deck-position checking:
- it tests the physical reach to the two troughs
- it uses the Tecan LiHa shared-tip strategy (8 reusable tips)
- it does not include heating, shaking, downtime, or chemistry steps

Use this to confirm where the troughs are located before building the full
transfer logic for the SPPS-style job.

Deck expectation for this toy workflow:
- Trough 1: deck position A1, source for DMF / DCE / deprotection agent
- Trough 2: deck position A2, source for four Fmoc-protected amino acid solutions
- Destination 96-well plate: deck position B2

This script intentionally avoids moving to B2 during the probe, since the goal is to
confirm the source trough locations before running the actual plate transfers.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Iterable, List, Sequence


@dataclass
class DeckResource:
    name: str
    position: str
    description: str
    liquid_level_mm: float = 10.0


# These are the resource names needed for the toy SPPS job.
# Replace the "position" strings with your actual deck coordinates if needed.
DECK_LAYOUT: dict[str, DeckResource] = {
    "Trough_1": DeckResource(
        name="Trough_1",
        position="A1",
        description="DMF / DCE / deprotection agent",
        liquid_level_mm=12.0,
    ),
    "Trough_2": DeckResource(
        name="Trough_2",
        position="A2",
        description="4 Fmoc-protected amino acid solutions",
        liquid_level_mm=12.0,
    ),
    "Destination_96": DeckResource(
        name="Destination_96",
        position="B2",
        description="Standard 1 mL flat-bottom 96-well plate",
        liquid_level_mm=8.0,
    ),
}


def print_deck_summary() -> None:
    print("Toy SPPS deck probe configuration")
    print("=" * 40)
    for resource in DECK_LAYOUT.values():
        print(f"- {resource.name}: position {resource.position} | {resource.description}")
    print()
    print("Assumptions:")
    print("- Only deck-position probing is being performed")
    print("- No heating, shaking, or downtime is included")
    print("- Shared-tip strategy uses 8 reusable tips")
    print("- Troughs are assumed to be at least quarter full")
    print()


def get_shared_tip_sequence(num_tips: int = 8) -> List[str]:
    """Return a simple reusable tip registry for the LiHa."""
    return [f"TIP_{i:02d}" for i in range(1, num_tips + 1)]


def coordinate_probe_plan() -> List[str]:
    """Return the source troughs to probe in order."""
    return ["Trough_1", "Trough_2"]


def _safe_move_to(liha, resource_name: str) -> None:
    """Move to a deck resource using a generic set of common PyLabRobot patterns.

    This helper is intentionally tolerant of API differences between PyLabRobot releases.
    """
    resource = DECK_LAYOUT[resource_name]
    print(f"Moving LiHa to {resource.name} at position {resource.position}")

    # Common patterns across versions:
    move_calls = [
        ("move_to", [resource_name]),
        ("move_to_resource", [resource_name]),
        ("move_to_position", [resource.position]),
        ("move_to_coords", [resource.position]),
        ("deck_move_to", [resource_name]),
    ]

    for method_name, args in move_calls:
        method = getattr(liha, method_name, None)
        if callable(method):
            try:
                method(*args)
                return
            except TypeError:
                pass

    if hasattr(liha, "deck"):
        deck = getattr(liha, "deck")
        if resource_name in deck:
            try:
                deck[resource_name].move_to()
                return
            except Exception:
                pass

    print(
        "No matching LiHa move method found for this environment. "
        "This is expected in a dry-run mode or a version mismatch."
    )


def _safe_pick_up_tip(liha, tip_name: str) -> None:
    for method_name in ["pick_up_tip", "pickup_tip", "pick_tip"]:
        method = getattr(liha, method_name, None)
        if callable(method):
            try:
                method(tip_name)
                return
            except TypeError:
                try:
                    method()
                    return
                except TypeError:
                    pass

    print(f"Tip {tip_name} would be picked up here using the shared-tip strategy.")


def _safe_aspirate(liha, volume_uL: float, resource_name: str) -> None:
    resource = DECK_LAYOUT[resource_name]
    for method_name in ["aspirate", "aspirate_liquid"]:
        method = getattr(liha, method_name, None)
        if callable(method):
            try:
                method(volume=volume_uL, source=resource_name)
                return
            except TypeError:
                try:
                    method(volume_uL, resource_name)
                    return
                except TypeError:
                    pass

    print(
        f"Would aspirate {volume_uL} uL from {resource.name} at position {resource.position} "
        f"(liquid level assumed at {resource.liquid_level_mm} mm)."
    )


def _safe_dispense(liha, volume_uL: float, destination_name: str) -> None:
    destination = DECK_LAYOUT[destination_name]
    for method_name in ["dispense", "dispense_liquid"]:
        method = getattr(liha, method_name, None)
        if callable(method):
            try:
                method(volume=volume_uL, destination=destination_name)
                return
            except TypeError:
                try:
                    method(volume_uL, destination_name)
                    return
                except TypeError:
                    pass

    print(
        f"Would dispense {volume_uL} uL into {destination.name} at position {destination.position}."
    )


def _safe_drop_tip(liha, tip_name: str) -> None:
    for method_name in ["drop_tip", "drop_tips", "return_tip"]:
        method = getattr(liha, method_name, None)
        if callable(method):
            try:
                method(tip_name)
                return
            except TypeError:
                try:
                    method()
                    return
                except TypeError:
                    pass

    print(f"Tip {tip_name} would be returned to the shared-tip rack.")


def run_probe(liha, aspirate_volume_uL: float = 10.0, use_execute_mode: bool = False) -> None:
    """Probe the trough positions using a shared-tip strategy.

    In execute mode, the routine tries to move the LiHa to the source troughs and perform
    a tiny aspirate / dispense cycle with reusable tips. In dry-run mode, it prints exactly
    what would happen without physically moving the robot.
    """
    source_order = coordinate_probe_plan()
    tip_sequence = get_shared_tip_sequence(num_tips=8)

    print("Starting source-probe routine")
    print(f"Shared tip pool: {len(tip_sequence)} reusable tips")
    print(f"Aspiration volume for probe: {aspirate_volume_uL} uL")
    print()

    for idx, resource_name in enumerate(source_order, start=1):
        tip_name = tip_sequence[(idx - 1) % len(tip_sequence)]
        print(f"Step {idx}: probing {resource_name} using shared tip {tip_name}")

        if use_execute_mode:
            _safe_pick_up_tip(liha, tip_name)
            _safe_move_to(liha, resource_name)
            _safe_aspirate(liha, aspirate_volume_uL, resource_name)
            _safe_move_to(liha, "Destination_96")
            _safe_dispense(liha, aspirate_volume_uL, "Destination_96")
            _safe_drop_tip(liha, tip_name)
        else:
            print(f"DRY RUN: would pick tip {tip_name}")
            print(f"DRY RUN: would move to {resource_name} at position {DECK_LAYOUT[resource_name].position}")
            print(f"DRY RUN: would aspirate {aspirate_volume_uL} uL")
            print(f"DRY RUN: would return to the deck area or safe position")
            print(f"DRY RUN: would dispense to {DECK_LAYOUT['Destination_96'].name} at position {DECK_LAYOUT['Destination_96'].position}")
            print(f"DRY RUN: would return tip {tip_name} to the shared-tip rack")

        print("-" * 30)

    print("Probe routine complete.")
    print("Use this to confirm the actual deck locations for A1 and A2 before building the full SPPS transfer logic.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deck position probe for the toy SPPS LiHa workflow")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Attempt to perform the move/aspirate/dispense sequence. Default is dry-run printout.",
    )
    parser.add_argument(
        "--volume",
        type=float,
        default=10.0,
        help="Probe aspiration volume in uL (default: 10.0)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    print_deck_summary()

    try:
        from pylabrobot import LiquidHandler  # type: ignore
    except ImportError:
        LiquidHandler = None  # type: ignore

    if args.execute:
        if LiquidHandler is None:
            raise RuntimeError(
                "PyLabRobot is not installed in this environment; cannot execute the deck probe. "
                "Install PyLabRobot first or run without --execute to see the dry-run plan."
            )

        # In many setups, the robot object is created elsewhere and passed here.
        # The demo is intentionally structured so the user can insert their real LiHa object.
        print("Execute mode is selected.")
        print("Insert your actual LiHa instance and replace the next line before running on hardware.")
        print("For example: run_probe(liha, aspirate_volume_uL=args.volume, use_execute_mode=True)")
        print("\nNo hardware move was executed automatically in this template example.")
    else:
        run_probe(liha=None, aspirate_volume_uL=args.volume, use_execute_mode=False)

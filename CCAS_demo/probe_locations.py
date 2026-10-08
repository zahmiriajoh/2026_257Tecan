#!/usr/bin/env python3
"""Live movement probe for the Tecan LiHa.

This is the actual movement version, matching the PyLabRobot documented pattern:

    from pylabrobot.liquid_handling import LiquidHandler
    from pylabrobot.liquid_handling.backends import EVOBackend
    from pylabrobot.resources import Deck

    deck = Deck.load_from_json_file("CCAS_demo/tecan_deck_layout.json")
    lih = LiquidHandler(backend=EVOBackend(), deck=deck)
    await lih.setup()
    await lih.move_to(lih.deck.get_resource("trough_1"))
    await lih.move_to(lih.deck.get_resource("trough_2"))
    await lih.move_to(lih.deck.get_resource("plate"))
    await lih.teardown()

This script does not aspirate liquid. It is a simple location-validation move to the
source troughs and the destination plate.
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

try:
    from pylabrobot.liquid_handling import LiquidHandler
    from pylabrobot.liquid_handling.backends import EVOBackend
    from pylabrobot.resources import Deck
except ImportError:  # pragma: no cover - import guard for static syntax checks
    LiquidHandler = None
    EVOBackend = None
    Deck = None


RESOURCE_SEQUENCE = ["trough_1", "trough_2", "plate"]


def print_deck_summary() -> None:
    print("Tecan location probe")
    print("=" * 40)
    print("A1 -> trough_1")
    print("A2 -> trough_2")
    print("B2 -> plate")
    print()
    print("This probe only tests movement. It does not aspirate or dispense liquid.")
    print()


async def move_to_resource(lih: LiquidHandler, resource_name: str) -> None:
    """Move the LiHa to a given deck resource."""
    resource = lih.deck.get_resource(resource_name)
    print(f"Moving to {resource_name} at deck location {resource.name}")
    if hasattr(lih, "move_to"):
        await lih.move_to(resource)
    else:
        # Fallback for some API variants.
        resource.move_to()
    print(f"Reached {resource_name}")


async def run_live_probe() -> None:
    """Connect to the Tecan backend and move the LiHa to each named resource."""
    deck_path = Path(__file__).with_name("tecan_deck_layout.json")
    if not deck_path.exists():
        raise FileNotFoundError(
            f"Deck file not found: {deck_path}. Update the deck map before running on hardware."
        )

    deck = Deck.load_from_json_file(str(deck_path))
    lih = LiquidHandler(backend=EVOBackend(), deck=deck)
    await lih.setup()
    try:
        for resource_name in RESOURCE_SEQUENCE:
            await move_to_resource(lih, resource_name)
    finally:
        await lih.teardown()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Move the Tecan LiHa to the A1/A2 troughs and the B2 destination plate for deck validation."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the intended movement plan without attempting hardware motion.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    print_deck_summary()

    if args.dry_run:
        for name in RESOURCE_SEQUENCE:
            print(f"DRY RUN: would move to {name}")
        raise SystemExit(0)

    if LiquidHandler is None or EVOBackend is None or Deck is None:
        raise RuntimeError(
            "PyLabRobot and the Tecan EVO backend are not installed in this environment. "
            "Install the robot software stack first, then run this script on the controlling computer."
        )

    asyncio.run(run_live_probe())

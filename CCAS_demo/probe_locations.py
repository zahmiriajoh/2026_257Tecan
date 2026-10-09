#!/usr/bin/env python3
"""Live movement probe for the Tecan LiHa.

PyLabRobot 0.2.1 has no ``LiquidHandler.move_to`` and the EVO backend does not implement
``move_channel_x/y``, so this probe calls the LiHa firmware move the backend itself uses before
every aspirate/dispense:

    from pylabrobot.liquid_handling import LiquidHandler
    from pylabrobot.liquid_handling.backends import EVOBackend
    from ccas_deck import build_deck

    deck = build_deck()
    lih = LiquidHandler(backend=EVOBackend(), deck=deck)
    await lih.setup()
    x, y = liha_xy(deck.get_resource("trough_1")["A1"][0], deck)
    await lih.backend.liha.position_absolute_all_axis(x, y, 90, [lih.backend._z_range] * 8)
    await lih.stop()

Channel 1 (the rear-most fixed tip) is moved over well/compartment A1 of each resource with
every Z axis fully raised, then only tip 1 is lowered slowly to a viewing height so you can see
where it is, and raised again before the next move. The viewing height is the higher of:

- halfway between fully raised and the labware's z_start (where EVOware starts searching for
  liquid, which is above the labware), and
- half of the Z axis travel,

so tip 1 never reaches the labware even if the placeholder z values in ccas_deck.py are off.
Use --lower-fraction to change "halfway" (0 = stay fully raised). This script does not aspirate
or dispense liquid.
"""

from __future__ import annotations

import argparse
import asyncio

try:
    from pylabrobot.liquid_handling import LiquidHandler
    from pylabrobot.liquid_handling.backends import EVOBackend
    from pylabrobot.resources.tecan.tip_creators import standard_fixed_tip
    from ccas_deck import build_deck, describe
except ImportError:  # pragma: no cover - import guard for static syntax checks
    LiquidHandler = None
    EVOBackend = None
    build_deck = None


RESOURCE_SEQUENCE = ["trough_1", "trough_2", "plate"]
CHANNEL_SPACING = 90  # 1/10 mm (9 mm pitch); firmware allows 90-380


def liha_xy(well, deck) -> tuple[int, int]:
    """Deck coordinate of a well's centre -> LiHa firmware x/y in 1/10 mm.

    Same conversion as EVOBackend._liha_positions in PLR 0.2.1.
    """
    location = well.get_location_wrt(deck) + well.center()
    return int((location.x - 100) * 10), int((346.5 - location.y) * 10)


def viewing_z(well, deck, z_range: int, fraction: float) -> int:
    """Firmware Z (1/10 mm, larger = higher) for tip 1 to hover at over ``well``.

    z_start uses the same conversion as EVOBackend._liha_positions in PLR 0.2.1.
    """
    plate = well.parent
    tip_length = int(standard_fixed_tip().total_tip_length * 10)
    z_start = int(z_range - plate.z_start + plate.get_location_wrt(deck).z * 10 + tip_length)
    target = round(z_range - fraction * (z_range - z_start))
    return min(z_range, max(target, z_range // 2))


def print_deck_summary() -> None:
    print("Tecan location probe")
    print("=" * 40)
    if build_deck is not None:
        print(describe(build_deck()))
    else:
        print("trough_1 -> grid 3, site 1")
        print("trough_2 -> grid 3, site 2")
        print("plate    -> grid 17, site 2")
    print()
    print("This probe only tests movement. It does not aspirate or dispense liquid.")
    print()


async def move_to_resource(
    lih: LiquidHandler, resource_name: str, pause: bool, fraction: float
) -> None:
    """Move LiHa channel 1 over well A1 of a deck resource, lower it to viewing height, raise it."""
    well = lih.deck.get_resource(resource_name)["A1"][0]
    x, y = liha_xy(well, lih.deck)
    backend = lih.backend
    print(f"Moving channel 1 over {well.name} (x={x}, y={y} in 1/10 mm)")
    await backend.liha.set_z_travel_height([backend._z_range] * backend.num_channels)
    await backend.liha.position_absolute_all_axis(
        x, y, CHANNEL_SPACING, [backend._z_range] * backend.num_channels
    )
    print(f"Reached {resource_name}")

    z_up = backend._z_range
    z_view = viewing_z(well, lih.deck, z_up, fraction)
    others = [None] * (backend.num_channels - 1)  # None = leave that tip where it is
    print(f"Lowering tip 1 from z={z_up} to z={z_view} ({(z_up - z_view) / 10:.1f} mm down)")
    await backend.liha.move_absolute_z([z_view] + others)
    if pause:
        await asyncio.to_thread(input, "Check alignment, then press Enter to continue...")
    await backend.liha.move_absolute_z([z_up] + others)


async def run_live_probe(pause: bool, fraction: float) -> None:
    """Connect to the Tecan backend and move the LiHa to each named resource."""
    deck = build_deck()
    lih = LiquidHandler(backend=EVOBackend(), deck=deck)
    await lih.setup()
    try:
        for resource_name in RESOURCE_SEQUENCE:
            await move_to_resource(lih, resource_name, pause, fraction)
    finally:
        await lih.backend._park_liha()
        await lih.stop()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Move the Tecan LiHa to trough_1/trough_2 (grid 3) and the destination plate (grid 17) for deck validation."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the intended movement plan without attempting hardware motion.",
    )
    parser.add_argument(
        "--no-pause",
        action="store_true",
        help="Do not wait for Enter at each position.",
    )
    parser.add_argument(
        "--lower-fraction",
        type=float,
        default=0.5,
        help="How far to lower tip 1 from fully raised toward the labware's z_start (0-1, default 0.5).",
    )
    args = parser.parse_args()
    if not 0 <= args.lower_fraction <= 1:
        parser.error("--lower-fraction must be between 0 and 1")
    return args


if __name__ == "__main__":
    args = parse_args()
    print_deck_summary()

    if args.dry_run:
        deck = build_deck() if build_deck is not None else None
        for name in RESOURCE_SEQUENCE:
            if deck is None:
                print(f"DRY RUN: would move to {name}")
            else:
                x, y = liha_xy(deck.get_resource(name)["A1"][0], deck)
                print(f"DRY RUN: would move channel 1 over {name} A1 (x={x}, y={y} in 1/10 mm), "
                      f"then lower tip 1 {args.lower_fraction:.0%} of the way to z_start")
        raise SystemExit(0)

    if LiquidHandler is None or EVOBackend is None or build_deck is None:
        raise RuntimeError(
            "PyLabRobot and the Tecan EVO backend are not installed in this environment. "
            "Install the robot software stack first, then run this script on the controlling computer."
        )

    asyncio.run(run_live_probe(pause=not args.no_pause, fraction=args.lower_fraction))

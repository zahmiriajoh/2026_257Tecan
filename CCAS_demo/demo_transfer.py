#!/usr/bin/env python3
"""CCAS_demo: a simple PyLabRobot transfer from a 4-trough source to a 96-well plate.

This script provides a starting template for a routine that:
- aspirates liquid from a 4-trough source reservoir
- dispenses to a standard 96-well destination plate
- cycles through the source troughs in a simple, repeatable pattern

The exact PyLabRobot class names can vary slightly by released version. The import
block below is intentionally written as a template and can be adjusted to match the
installed package on the Tecan controller.
"""

from __future__ import annotations

from typing import Iterable, List, Sequence

# NOTE: Update these imports to match the installed PyLabRobot version.
try:
    from pylabrobot import LiquidHandler
    from pylabrobot.resources import Plate, Trough
except ImportError as exc:  # pragma: no cover - for template use only
    raise RuntimeError(
        "PyLabRobot is not installed or the import names differ in your version. "
        "Install PyLabRobot and update the imports in this file to match your setup."
    ) from exc


ROWS = ["A", "B", "C", "D", "E", "F", "G", "H"]
COLUMNS = list(range(1, 13))


def build_well_list() -> List[str]:
    """Return the standard 96-well layout as A1, A2, ..., H12."""
    wells: List[str] = []
    for row in ROWS:
        for col in COLUMNS:
            wells.append(f"{row}{col}")
    return wells


def build_transfer_plan(source_troughs: Sequence[str], volume_uL: float = 25.0) -> List[dict]:
    """Create a simple repeating transfer plan.

    Example:
    - Column 1 uses source_troughs[0]
    - Column 2 uses source_troughs[1]
    - ...
    - Column 4 uses source_troughs[3]
    - Column 5 loops back to source_troughs[0]
    """
    plan: List[dict] = []
    for col in COLUMNS:
        source_name = source_troughs[(col - 1) % len(source_troughs)]
        for row in ROWS:
            destination_well = f"{row}{col}"
            plan.append(
                {
                    "source": source_name,
                    "destination": destination_well,
                    "volume_uL": volume_uL,
                }
            )
    return plan


def run_demo_transfer(
    liquid_handler: LiquidHandler,
    source_troughs: Sequence[str],
    destination_plate: Plate,
    volume_uL: float = 25.0,
    mix_before: bool = False,
    mix_after: bool = True,
) -> None:
    """Execute the transfer pattern for a 4-trough reservoir into a 96-well plate.

    This is a template routine that aligns with the common PyLabRobot resource pattern:
    - source_troughs is a list of named source reservoirs or positions
    - destination_plate is the 96-well plate resource
    - each well gets a volume from the current trough in the repeating pattern
    """
    transfer_plan = build_transfer_plan(source_troughs, volume_uL=volume_uL)

    for step in transfer_plan:
        source_name = step["source"]
        destination_well = step["destination"]
        target_volume = step["volume_uL"]

        source = _resolve_resource(liquid_handler, source_name)
        destination = _resolve_destination_well(destination_plate, destination_well)

        # Typical PyLabRobot method pattern. Adjust argument names to match the version
        # used on your system.
        liquid_handler.transfer(
            source=source,
            destination=destination,
            volume=target_volume,
            mix_before=mix_before,
            mix_after=mix_after,
        )


def _resolve_resource(liquid_handler: LiquidHandler, resource_name: str):
    """Look up a resource by name on the deck.

    This helper is intentionally generic and keeps the example readable. Real projects
    often use deck resources that are already accessible as named objects.
    """
    try:
        return liquid_handler.deck[resource_name]
    except (KeyError, AttributeError):
        # Fall back to a direct lookup that may be adapted to the installed library.
        return liquid_handler.resources[resource_name]


def _resolve_destination_well(destination_plate: Plate, well_name: str):
    """Return the destination well object for a standard 96-well plate."""
    # PyLabRobot often exposes wells by direct indexing such as destination_plate["A1"].
    # This method keeps the code compatible with that style.
    if hasattr(destination_plate, "__getitem__"):
        return destination_plate[well_name]
    return destination_plate.wells[well_name]


if __name__ == "__main__":
    print("CCAS demo transfer template")
    print("This script is a starting point for a 4-trough to 96-well transfer workflow.")
    print("Update the resource names and deck configuration for your actual Tecan setup before use.")
    print()
    print("Example transfer plan for 4 source troughs:")
    example_tough = ["Trough_1", "Trough_2", "Trough_3", "Trough_4"]
    for step in build_transfer_plan(example_tough, volume_uL=25.0)[:6]:
        print(step)

    print("\nTotal planned steps:", len(build_transfer_plan(example_tough, volume_uL=25.0)))

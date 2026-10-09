#!/usr/bin/env python3
"""PyLabRobot deck representation for the CCAS demo on the 257 Tecan EVO.

Positions use EVOware grid/site numbering:

    trough_1  (piperidine, DCE, DMF, DMSO)  -> grid 3,  site 1
    trough_2  (Fmoc-AA1..AA4)               -> grid 3,  site 2
    plate     (96-well destination)         -> grid 17, site 2

The LiHa has 8 fixed (steel) tips, so there is no tip rack on the deck; scripts mount the tips
in software with ``LiquidHandler.update_head_state`` (see tecan_spps_run.py).

In PLR, a Tecan carrier is placed with ``deck.assign_child_resource(carrier, rails=<grid>)``
and labware goes into ``carrier[<site index>]``. PLR site indices are 0-based and count from
the FRONT of the carrier, while EVOware sites are 1-based and count from the BACK, so
``evo_site()`` converts between the two (EVOware site 1 on a 3-position carrier is PLR index 2).

Usage from another script:

    from ccas_deck import build_deck
    deck = build_deck()
    trough_1 = deck.get_resource("trough_1")

Run this file directly to print the deck summary and write ``ccas_deck.png``:

    python CCAS_demo/ccas_deck.py
"""

from __future__ import annotations

from pathlib import Path

from pylabrobot.resources import Coordinate
from pylabrobot.resources.carrier import Carrier
from pylabrobot.resources.tecan import (
    EVO150Deck,
    MP_3Pos,
    DeepWell_96_Well,
    TecanDeck,
    TecanPlate,
)
from pylabrobot.resources.utils import create_ordered_items_2d
from pylabrobot.resources.well import CrossSectionType, Well

# EVOware grid/site for each resource. Edit here if the physical deck changes.
TROUGH_CARRIER_GRID = 3
TROUGH_1_SITE = 1
TROUGH_2_SITE = 2

PLATE_CARRIER_GRID = 17
PLATE_SITE = 2

# Compartment (well) names inside each trough, A1 = left-most compartment.
# trough_1 labels on the deck, left to right: piperidine (relabelled from H2O), DCE, DMF, DMSO.
REAGENT_WELLS = {"PIPERIDINE": "A1", "DCE": "A2", "DMF": "A3", "DMSO": "A4"}
AA_SOURCE_WELLS = {"AA1": "A1", "AA2": "A2", "AA3": "A3", "AA4": "A4"}


def evo_site(carrier: Carrier, site: int) -> int:
    """Convert a 1-based EVOware site number (1 = back) to a PLR carrier index (0 = front)."""
    num_sites = len(carrier.sites)
    if not 1 <= site <= num_sites:
        raise ValueError(f"Site {site} out of range for {carrier.name} ({num_sites} sites).")
    return num_sites - site


def CCAS_Trough(name: str, num_compartments: int) -> TecanPlate:
    """SBS-footprint reservoir with ``num_compartments`` side-by-side compartments (A1, A2, ...).

    The EVO backend only aspirates from wells of a ``TecanPlate``, so each compartment is a Well.
    Each Well is a 9 x 9 mm pipetting target at the centre of its compartment rather than the full
    compartment: the backend sets the LiHa tip spacing from the well's Y size, and the firmware
    only accepts 9-38 mm.
    TODO: replace the z_* / area values (Tecan 1/10 mm units) with the ones from the EVOware
    labware definition of the actual trough; these are copied from DeepWell_96_Well.
    """
    pitch_x = 127.8 / num_compartments
    return TecanPlate(
        name=name,
        size_x=127.8,
        size_y=85.4,
        size_z=39.0,
        model=f"CCAS_Trough_{num_compartments}",
        z_start=1670.0,
        z_dispense=1690.0,
        z_max=2060.0,
        area=33.2,
        ordered_items=create_ordered_items_2d(
            Well,
            num_items_x=num_compartments,
            num_items_y=1,
            dx=pitch_x / 2 - 4.5,
            dy=85.4 / 2 - 4.5,
            dz=0.0,
            item_dx=pitch_x,
            item_dy=9.0,
            size_x=9.0,
            size_y=9.0,
            size_z=39.0,
            cross_section_type=CrossSectionType.RECTANGLE,
        ),
    )


def build_deck() -> TecanDeck:
    """Build the CCAS demo deck. Returns a deck ready to pass to ``LiquidHandler``."""
    deck = EVO150Deck()

    trough_carrier = MP_3Pos("trough_carrier")
    trough_carrier[evo_site(trough_carrier, TROUGH_1_SITE)] = CCAS_Trough("trough_1", 4)
    trough_carrier[evo_site(trough_carrier, TROUGH_2_SITE)] = CCAS_Trough("trough_2", 4)
    deck.assign_child_resource(trough_carrier, rails=TROUGH_CARRIER_GRID)

    plate_carrier = MP_3Pos("plate_carrier")
    plate_carrier[evo_site(plate_carrier, PLATE_SITE)] = DeepWell_96_Well("plate")
    deck.assign_child_resource(plate_carrier, rails=PLATE_CARRIER_GRID)

    return deck


def describe(deck: TecanDeck) -> str:
    """One line per labware: name, EVOware grid/site."""
    lines = []
    for carrier in deck.children:
        if not isinstance(carrier, Carrier) or carrier.name == "wash_station":
            continue
        grid = deck._rails_for_x_coordinate(carrier.location.x)
        for idx, holder in sorted(carrier.sites.items(), reverse=True):
            if holder.resource is not None:
                site = len(carrier.sites) - idx
                lines.append(f"{holder.resource.name:10} -> grid {grid}, site {site} ({carrier.name})")
    return "\n".join(lines)


def draw_deck(deck: TecanDeck, out_path: Path) -> None:
    """Top-down PNG of the deck, front of the robot at the bottom."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    colors = {"trough_1": "#4c8bf5", "trough_2": "#9b59b6", "plate": "#27ae60"}

    fig, ax = plt.subplots(figsize=(14, 5))

    # Grid lines (rails) with labels every 5 grids plus the ones in use.
    used = {TROUGH_CARRIER_GRID, PLATE_CARRIER_GRID}
    for grid in range(1, deck.num_rails + 1):
        x = (grid - 1) * 25 + 100
        ax.axvline(x, color="#dddddd", lw=0.6, zorder=0)
        if grid in used or grid % 5 == 0 or grid == 1:
            ax.text(x, -18, str(grid), ha="center", va="top", fontsize=8,
                            fontweight="bold" if grid in used else "normal")
    ax.text(deck.get_absolute_size_x() / 2, -45, "EVOware grid", ha="center", va="top", fontsize=9)

    for resource in deck.get_all_resources():
        loc = resource.get_location_wrt(deck)
        w, h = resource.get_absolute_size_x(), resource.get_absolute_size_y()
        if isinstance(resource, Carrier):
            ax.add_patch(Rectangle((loc.x, loc.y), w, h, fc="#f2f2f2", ec="#555555", lw=1, zorder=1))
            ax.text(loc.x + w / 2, loc.y + h + 6, resource.name, ha="center", va="bottom", fontsize=8)
            if resource.name == "wash_station":
                continue
            for idx, holder in resource.sites.items():
                hl = holder.get_location_wrt(deck)
                site = len(resource.sites) - idx
                ax.text(hl.x + 2, hl.y + holder.get_absolute_size_y() - 2, f"site {site}",
                                ha="left", va="top", fontsize=6, color="#777777", zorder=4)
        elif resource.name in colors:
            ax.add_patch(Rectangle((loc.x, loc.y), w, h, fc=colors[resource.name], ec="black",
                                                          alpha=0.35, lw=1, zorder=2))
            ax.text(loc.x + w / 2, loc.y + h - 8, resource.name, ha="center", va="top",
                            fontsize=9, fontweight="bold", zorder=4)
        elif isinstance(resource, Well) and resource.parent.name.startswith("trough"):
            ax.add_patch(Rectangle((loc.x, loc.y), w, h, fill=False, ec="#333333", lw=0.5, zorder=3))
            contents = REAGENT_WELLS if resource.parent.name == "trough_1" else AA_SOURCE_WELLS
            well_id = resource.name.rsplit("_", 1)[-1]
            liquid = next((k for k, v in contents.items() if v == well_id), "")
            ax.text(loc.x + w / 2, loc.y - 2, liquid.lower() if liquid.isupper() and len(liquid) > 4 else liquid,
                    ha="center", va="top", fontsize=5.5, zorder=4)

    ax.set_xlim(-20, deck.get_absolute_size_x() + 20)
    ax.set_ylim(-70, 420)  # deck extends further back than any carrier; crop to the used area
    ax.set_aspect("equal")
    ax.set_title("CCAS demo deck (EVO150) — top view, front at bottom")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    deck = build_deck()
    print(deck.summary())
    print()
    print(describe(deck))
    out = Path(__file__).with_name("ccas_deck.png")
    draw_deck(deck, out)
    print(f"\nWrote {out}")

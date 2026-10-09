#!/usr/bin/env python3
"""Toy SPPS test job for the Tecan LiHa.

This script encodes the actual job described by the user:
- 4 Fmoc-protected amino acids are stored in trough_2 (grid 3, site 2; see ccas_deck.py)
- trough_1 (grid 3, site 1) contains DMF, DCE, and the deprotection agent (piperidine)
- For each well, generate all ordered permutations of the 4 amino acids
- Then, fill the remaining wells with all ordered pairs of the 4 amino acids
- For each amino acid in the sequence:
    1. add the Fmoc-AA
    2. add DMF
    3. add DCE
    4. add piperidine
    5. proceed to the next amino acid in the order

This script is a logical test representation for a later SPPS automation workflow.
It does not include heating, shaking, downtime, or any chemistry beyond the
aspirate/dispense/mix pattern requested.
"""

from __future__ import annotations

from itertools import permutations
from typing import Iterable, List, Sequence


AA_NAMES = ["AA1", "AA2", "AA3", "AA4"]
# Names match the resources in ccas_deck.build_deck(), so plans can be resolved with
# deck.get_resource(step["source"]).
TROUGH_1 = "trough_1"  # grid 3, site 1: DMF, DCE, deprotection agent
TROUGH_2 = "trough_2"  # grid 3, site 2: 4 Fmoc-protected amino acid solutions
DESTINATION_PLATE = "plate"  # grid 17, site 2: 96-well destination


def generate_amino_acid_sequences() -> List[List[str]]:
    """Return all ordered 4-AA permutations and all ordered 2-AA permutations."""
    four_aa_orders = [list(order) for order in permutations(AA_NAMES, 4)]
    two_aa_orders = [list(order) for order in permutations(AA_NAMES, 2)]
    return four_aa_orders + two_aa_orders


def repeat_sequences_to_plate(sequence_list: Sequence[Sequence[str]], total_wells: int = 96) -> List[List[str]]:
    """Repeat the valid sequence set across all wells in the plate.

    There are only 24 four-AA permutations and 12 two-AA permutations, so the unique set is
    smaller than a full 96-well plate. Repeating the list makes the deck planning easy to test
    in a real 96-well context without changing the underlying logic.
    """
    plan: List[List[str]] = []
    if not sequence_list:
        return plan

    idx = 0
    while len(plan) < total_wells:
        plan.append(list(sequence_list[idx % len(sequence_list)]))
        idx += 1
    return plan


def build_well_sequence(order: Sequence[str]) -> List[dict]:
    """Build a transfer sequence for one well.

    For each AA in the order, do:
      - Fmoc-AA addition
      - DMF
      - DCE
      - piperidine
    The next amino acid is then processed in the same pattern.
    """
    steps: List[dict] = []
    for aa in order:
        steps.append(
            {
                "source": TROUGH_2,
                "destination": DESTINATION_PLATE,
                "action": "add_fmoc_aa",
                "aa": aa,
                "volume_uL": 25.0,
            }
        )
        steps.append({"source": TROUGH_1, "destination": DESTINATION_PLATE, "action": "add_dmf", "reagent": "DMF", "volume_uL": 25.0})
        steps.append({"source": TROUGH_1, "destination": DESTINATION_PLATE, "action": "add_dce", "reagent": "DCE", "volume_uL": 25.0})
        steps.append({"source": TROUGH_1, "destination": DESTINATION_PLATE, "action": "add_piperidine", "reagent": "Piperidine", "volume_uL": 25.0})
    return steps


def build_plate_plan(total_wells: int = 96) -> List[dict]:
    """Create a plate-level plan using all 4-AA permutations and then all 2-AA permutations."""
    unique_orders = generate_amino_acid_sequences()
    repeated_orders = repeat_sequences_to_plate(unique_orders, total_wells=total_wells)

    plan: List[dict] = []
    for well_index, order in enumerate(repeated_orders):
        plate_well = f"{chr(65 + (well_index // 12))}{(well_index % 12) + 1}"
        plan.append({"well": plate_well, "sequence": order, "steps": build_well_sequence(order)})
    return plan


def print_plate_summary() -> None:
    print("Toy SPPS plate plan")
    print("=" * 40)
    print("Sequence rule:")
    print("1. Add Fmoc-AA")
    print("2. Add DMF")
    print("3. Add DCE")
    print("4. Add piperidine")
    print("5. Proceed to the next Fmoc-AA in the order")
    print()
    print("Source resources:")
    print(f"- {TROUGH_1}: DMF, DCE, deprotection agent (piperidine)")
    print(f"- {TROUGH_2}: four Fmoc-protected amino acid solutions")
    print(f"- {DESTINATION_PLATE}: 96-well flat-bottom destination plate")
    print()
    print("Permutation set:")
    print(f"- 4-AA permutations: {len(list(permutations(AA_NAMES, 4)))}")
    print(f"- 2-AA permutations: {len(list(permutations(AA_NAMES, 2)))}")
    print(f"- total unique sequences: {len(generate_amino_acid_sequences())}")
    print(f"- plate wells represented: 96")


if __name__ == "__main__":
    print_plate_summary()
    plate_plan = build_plate_plan(total_wells=96)

    for idx, item in enumerate(plate_plan[:6]):
        print(f"\nWell {item['well']} -> order {item['sequence']}")
        for step_no, step in enumerate(item["steps"][:8], start=1):
            print(f"  {step_no}: {step['action']} | source={step['source']} | reagent={step.get('reagent', step.get('aa'))}")

    print("\nTotal wells in plate plan:", len(plate_plan))
    print("Remaining wells beyond the unique sequence set are filled by repeating the generated sequence set.")

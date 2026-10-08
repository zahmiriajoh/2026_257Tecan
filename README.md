# 2026_257Tecan
Largely focused on the files and environments needed to run PyLabRobot on the Tecan in 66-257.

## Purpose
This repository contains starter files for a simple Tecan/PyLabRobot test workflow representing a toy SPPS-style process. The goal is to validate deck positioning, aspiration, dispensing, and shared-tip handling before moving to a fuller chemistry sequence.

## Included demo files
- `CCAS_demo/README.md` - overview of the demo workflow
- `CCAS_demo/deck_layout.md` - placement assumptions for source and destination decks
- `CCAS_demo/demo_transfer.py` - generalized transfer template
- `CCAS_demo/probe_locations.py` - deck probe script for testing A1/A2 locations and shared-tip movement
- `CCAS_demo/requirements_demo.txt` - PyLabRobot install hint

## Current toy workflow assumptions
- Source 1: Trough at deck position A1
  - Contains DMF, DCE, and deprotection agent
- Source 2: Trough at deck position A2
  - Contains four different Fmoc-protected amino acid solutions
- Destination: 96-well flat-bottom plate at deck position B2
  - Standard 1 mL capacity plate
- Only aspiration, dispensing, and mixing are included in this stage
- No heating, shaking, or downtime are modeled in the toy workflow
- Shared-tip strategy is required with 8 reusable tips
- Source liquid level is assumed to be at least quarter full

## Actual job instructions for the toy SPPS-like run
For each well, the workflow should be structured as follows:

1. Combine the four Fmoc-protected amino acids in every possible order.
2. Use the remaining wells to perform the same pattern with all possible ordered combinations of only 2 of the 4 Fmoc-protected amino acids.
3. For every amino acid in the order assigned to a well:
   - add the Fmoc-AA
   - then add DMF
   - then add DCE
   - then add piperidine (deprotection agent)
   - then continue to the next Fmoc-AA in that sequence
4. Use the same reagent sequence for every well, while varying the order of amino acids from well to well.

This means the per-step reagent ordering is:

```text
Fmoc-AA -> DMF -> DCE -> piperidine -> next Fmoc-AA -> DMF -> DCE -> piperidine -> ...
```

The order of the amino acids is the key variable across the plate.

## Basic test flow
1. Confirm the deck coordinates for A1, A2, and B2 match the actual Tecan configuration.
2. Run the probe script to verify robot movement to the troughs and the shared-tip strategy.
3. Confirm that the LiHa can move to the correct source wells without collision.
4. Confirm that the aspirate/dispense cycle responds correctly at the expected liquid height.
5. Only after the movement and tip logic are validated should the chemistry transfer workflow be expanded.

## Run the position probe
From the repository root:

```bash
python CCAS_demo/probe_locations.py
```

This will execute a dry-run deck-probe that shows the intended movement and aspiration/dispense plan for the A1 and A2 troughs.

## Run the general transfer demo
From the repository root:

```bash
python CCAS_demo/demo_transfer.py
```

This prints a generic transfer plan for a 4-trough-to-96-well workflow and is intended as a template for adapting the later SPPS-style task.

## Run the SPPS toy job planner
From the repository root:

```bash
python CCAS_demo/spps_toy_job.py
```

This script generates the plate-level sequence plan for all 4-AA permutations and then the 2-AA permutations, and prints the representative steps for each well.

## Environment setup
Install PyLabRobot in the environment used by the robot controller:

```bash
pip install -r CCAS_demo/requirements_demo.txt
```

If the exact PyLabRobot import names differ in your installed version, update the imports in `CCAS_demo/demo_transfer.py` and `CCAS_demo/probe_locations.py` to match your environment.

## Important notes
- These scripts are intentionally simple and should be treated as demonstration/test starting points.
- The actual deck resource names and coordinates will need to be confirmed against the real Tecan setup before running on hardware.
- This repo is meant to support a toy representation of later SPPS actions, not a production synthesis workflow.

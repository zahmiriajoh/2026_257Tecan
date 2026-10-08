# CCAS_demo

This folder contains the current toy job and demonstration scripts for the 2026 restart of the 257 Tecan. The content here is more detailed than the repo-level summary and documents the active test workflow.

## Goal

This is a toy SPPS-style test job designed to validate the following actions:
- source handling in A1 and A2
- LiHa movement and deck location checks
- shared-tip usage with 8 reusable tips
- aspiration, dispensing, and mixing steps only
- combinatorial amino acid ordering patterns across a 96-well destination plate

## Current workflow assumptions
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

## Files in this folder
- `probe_locations.py` - dry-run deck probe for A1/A2 motion and shared-tip behavior
- `demo_transfer.py` - generalized template for a simple transfer pattern
- `spps_toy_job.py` - combinatorial sequence planner for the toy SPPS job
- `tecan_spps_run.py` - Tecan-ready PyLabRobot script using the EVO backend
- `tecan_deck_layout.json` - sample deck map for the actual robot
- `deck_layout.md` - schematic summary of the source and destination layout
- `requirements_demo.txt` - PyLabRobot install hint

## Run the position probe
From the repository root:

```bash
python CCAS_demo/probe_locations.py
```

## Run the toy job planner
From the repository root:

```bash
python CCAS_demo/spps_toy_job.py
```

## Run the actual Tecan-ready job
From the repository root, after confirming the deck JSON matches the real instrument:

```bash
python CCAS_demo/tecan_spps_run.py
```

This is the version intended to be run on the Tecan with the installed PyLabRobot/EVO stack. It uses the shared-tip strategy across 8 reusable tips and follows the reagent ordering:

```text
Fmoc-AA -> DMF -> DCE -> piperidine
```

for each amino acid in the sequence assigned to a well.

## Environment setup
Install PyLabRobot in the environment used by the robot controller:

```bash
pip install -r CCAS_demo/requirements_demo.txt
```

## Notes
- These scripts are intentionally simple and should be treated as demonstration/test starting points.
- The actual deck resource names and coordinates will need to be confirmed against the real Tecan setup before running on hardware.
- This repo is meant to support a toy representation of later SPPS actions, not a production synthesis workflow.

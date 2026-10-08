# CCAS_demo

This folder contains a simple demonstration script for a standard liquid transfer from a 4-trough source plate to a 96-well destination plate using PyLabRobot.

## Goal

This is intended to be a good Tecan test job or demonstration for:
- loading 4 source reagents into a 4-trough reservoir
- transferring fixed volumes into a 96-well plate
- verifying deck positioning, pipetting, and aspiration/dispense behavior
- using a repeatable pattern that is easy to expand for more advanced workflows

## Deck layout

Source reservoir (4 troughs):
- Trough 1: reagent A
- Trough 2: reagent B
- Trough 3: reagent C
- Trough 4: reagent D

Destination plate:
- 96-well plate in standard ANSI layout (A1:H12)
- One or more predetermined wells receive liquid from each source trough

A simple pattern is to cycle through the 4 source troughs by column:
- Column 1 -> trough 1
- Column 2 -> trough 2
- Column 3 -> trough 3
- Column 4 -> trough 4
- Column 5 -> trough 1
- ... and continue until all columns are filled

## Files in this folder

- `demo_transfer.py` - executable template workflow for the transfer
- `deck_layout.md` - schematic of the source/destination arrangement

## Typical setup

1. Install PyLabRobot in the environment used by the robot control software.
2. Confirm the deck positions match the real Tecan layout.
3. Verify source trough positions, plate positions, tip geometry, and liquid classes.
4. Run the demo script in simulation mode first, then on the instrument.

## Example usage

```bash
python CCAS_demo/demo_transfer.py
```

## Notes

- The exact PyLabRobot resource class names may vary slightly by version. If the import names differ on your machine, update the imports at the top of `demo_transfer.py` to match the installed package.
- This is a demonstration workflow. For production use, add dead volume checks, tip tracking, and error handling.
- The pattern can be modified to deliver different volumes or mix steps per well.

# Deck layout for the CCAS demo

This document describes a standard 4-trough-to-96-well transfer pattern suitable as a Tecan demonstration job.

## Source layout

Four source troughs are arranged in a simple row or column on the deck.

```text
    ┌──────────────┐
    │ Trough 1     │
    │ Reagent A    │
    └──────────────┘

    ┌──────────────┐
    │ Trough 2     │
    │ Reagent B    │
    └──────────────┘

    ┌──────────────┐
    │ Trough 3     │
    │ Reagent C    │
    └──────────────┘

    ┌──────────────┐
    │ Trough 4     │
    │ Reagent D    │
    └──────────────┘
```

## Destination layout

The destination is a standard 96-well plate with rows A-H and columns 1-12.

```text
    Column 1   Column 2   Column 3   ...   Column 12
A   A1         A2         A3                   A12
B   B1         B2         B3                   B12
C   C1         C2         C3                   C12
D   D1         D2         D3                   D12
E   E1         E2         E3                   E12
F   F1         F2         F3                   F12
G   G1         G2         G3                   G12
H   H1         H2         H3                   H12
```

## Example execution pattern

- Fill all wells in column 1 from Trough 1
- Fill all wells in column 2 from Trough 2
- Fill all wells in column 3 from Trough 3
- Fill all wells in column 4 from Trough 4
- Repeat for remaining columns

This is a good test pattern because it clearly shows that the deck positioning and transfer routine are correct.

## Suggested start values

- Transfer volume: 10-50 µL per well
- Aspiration height: just above liquid surface
- Dispense height: near bottom or mid-level depending on plate geometry
- Mix: optional, 2-3 repeats for better accuracy
- Tip usage: either one tip per transfer or once per source if compatible with the method

Adjust these values based on the actual liquid properties, plate type, and robot configuration.

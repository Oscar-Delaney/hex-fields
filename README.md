# Hex Fields

Three-colour logic puzzles on hexes: a one-off map of Great Britain, plus a week of puzzles from Monday to Sunday. Inspired by [Fields](https://inkwellgames.com) from Inkwell Games; not affiliated with them.

## Rules

- Colour every cell green, blue or yellow.
- A field is a connected group of cells of one colour. Fields of the same colour can't touch, because they would be one field.
- Every field contains exactly one number, in its own colour. The number is the field's size. A **?** field can be any size.

Every puzzle has exactly one solution.

## The puzzles

The page opens on **Great Britain**: mainland Britain traced onto 89 hexes, about as hard as a weekend puzzle. The week's puzzles sit in the tabs below it.

| Day | Board | Fields | What it takes |
|---|---|---|---|
| Monday | 37 cells | 12 | Basic techniques only |
| Tuesday | 61 | 14 | A few intermediate steps |
| Wednesday | 61 | 16, one ? | Steady intermediate logic |
| Thursday | 91 | 21, one ? | Intermediate logic on a big board |
| Friday | 91 | 19, one ? | Long chains of intermediate logic |
| Saturday | 91 | 22, two ? | A couple of short trials |
| Sunday | 91 | 22, three ? | Several short trials |

## How the puzzles are made

`src/gen.py` holds a solver that only makes sound deductions, in three tiers:

1. **Basic:** finished fields, separation, overgrowth, forced expansion.
2. **Intermediate:** out-of-range cells, bottlenecks, orphan pathing.
3. **Trials:** assume one cell's colour, follow tiers 1–2 for at most 40 steps, and rule the colour out if a rule breaks.

A puzzle's difficulty is the lowest tier that finishes it, plus how many rounds it needs at that tier. A full solve proves the solution is unique. `src/verify.py` double-checks this with a brute-force search that uses only the bare rules.

With three colours, random clue placement almost never gives a unique puzzle. The generator therefore hill-climbs on the map and the clue positions together, then tunes toward each day's difficulty target (`DAYS` in `src/week.py`).

## Commands

Generate a new puzzle for a day. The arguments are the day, a seed and a time limit in minutes; the result is written to `<day>_<seed>.json`.

```bash
python3 src/week.py sat 63 10
```

Check that a puzzle has exactly one solution:

```bash
python3 src/verify.py puzzles/sat.json
```

`gb` works the same way as a day name. Its board comes from `shapes/gb.json`, which `src/shape_gb.py` traced from Natural Earth's 1:50m country outlines, keeping cells whose centres fall on mainland Great Britain at a 31 km cell size with the grid shifted half a row:

```bash
python3 -I src/shape_gb.py ne_50m_admin_0_countries.geojson 31 shapes/gb.json 0 0.5
```

Rebuild the page after changing `src/template.html` or a puzzle. `index.html` is generated, so don't edit it by hand.

```bash
python3 src/build.py --standalone index.html gb=puzzles/gb.json mon=puzzles/mon.json tue=puzzles/tue.json wed=puzzles/wed.json thu=puzzles/thu.json fri=puzzles/fri.json sat=puzzles/sat.json sun=puzzles/sun.json
```

## Notes

- The page is one self-contained HTML file. The only network request is for its Google fonts.
- Progress is saved in each player's browser.
- The solutions are embedded in the page so Check can work, so a curious player can find them in the source.

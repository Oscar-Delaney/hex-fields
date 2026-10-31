# Hex Fields

Three-colour logic puzzles on hexes: specially shaped boards plus a week of puzzles from Monday to Sunday. Inspired by [Fields](https://inkwellgames.com) from Inkwell Games; not affiliated with them.

## Rules

- Colour every cell green, blue or yellow.
- A field is a connected group of cells of one colour. Fields of the same colour can't touch, because they would be one field.
- Every field contains exactly one number, in its own colour. The number is the field's size. A **?** field can be any size.

Every puzzle has exactly one solution.

## Sets

The main page shows the latest set. Earlier sets stay playable in the archive (`archive/`), and saved progress carries over because it's stored per puzzle.

- **Set 2 (31 Oct 2026):**
  - **Australia:** the mainland traced onto 88 hexes, weekend difficulty.
  - **Star:** a six-pointed star of 73 cells, Thursday difficulty. The tips give sharp corners.
  - **Ring:** a hexagon with a hexagonal hole, 72 cells, Friday difficulty. Fields can wrap around the hole.
  - **A new week**, from Monday to Sunday.
- **Set 1 (29 Oct 2026):** Great Britain (89 hexes, weekend difficulty) and the first week.

Each week's difficulty, the same in every set:

| Day | Board | What it takes |
|---|---|---|
| Monday | 37 cells | Basic techniques only |
| Tuesday | 61 | A few intermediate steps |
| Wednesday | 61 | Steady intermediate logic |
| Thursday | 91 | Intermediate logic on a big board |
| Friday | 91 | Long chains of intermediate logic |
| Saturday | 91 | A couple of short trials |
| Sunday | 91 | Several short trials |

## How the puzzles are made

`src/gen.py` holds a solver that only makes sound deductions, in three tiers:

1. **Basic:** finished fields, separation, overgrowth, forced expansion.
2. **Intermediate:** out-of-range cells, bottlenecks, orphan pathing.
3. **Trials:** assume one cell's colour, follow tiers 1–2 for at most 40 steps, and rule the colour out if a rule breaks.

A puzzle's difficulty is the lowest tier that finishes it, plus how many rounds it needs at that tier. A full solve proves the solution is unique. `src/verify.py` double-checks this with a brute-force search that uses only the bare rules.

With three colours, random clue placement almost never gives a unique puzzle. The generator therefore hill-climbs on the map and the clue positions together, then tunes toward each puzzle's difficulty target (`DAYS` in `src/week.py`).

## Commands

Generate a puzzle. The arguments are a key from `DAYS` (`mon`…`sun`, `gb`, `aus`, `star`, `ring`), a seed and a time limit in minutes. The result is written to `<key>_<seed>.json`. Use seeds you haven't used before, because saved progress is keyed by puzzle and seed.

```bash
python3 src/week.py sat 63 10
```

Check that a puzzle has exactly one solution:

```bash
python3 src/verify.py puzzles/set2/sat.json
```

Make a new board shape. `src/shape_map.py` traces a country's largest landmass from Natural Earth's 1:50m country outlines (`ne_50m_admin_0_countries.geojson`), keeping cells whose centres fall on land. `src/shape_geo.py` draws geometric boards. The existing boards were made with:

```bash
python3 -I src/shape_map.py ne_50m_admin_0_countries.geojson "United Kingdom" 31 shapes/gb.json 0 0.5 54.5
python3 -I src/shape_map.py ne_50m_admin_0_countries.geojson Australia 185 shapes/aus.json 0.5 0
python3 src/shape_geo.py star 3 shapes/star.json
python3 src/shape_geo.py ring 6 3 shapes/ring.json
```

A new shape also needs an entry in `DAYS`, and a display name in `NAMES` in `src/template.html`.

To publish a new set:
1. Generate its puzzles into `puzzles/set<N>/`.
2. Add the set to the **top** of `sets.json`.
3. Rebuild the site:

```bash
python3 src/build.py
```

This writes `index.html` (the latest set), `archive/<id>/index.html` for each earlier set, and `archive/index.html`. These files are generated, so don't edit them by hand.

## Notes

- Each page is one self-contained HTML file. The only network request is for its Google fonts.
- Progress is saved in each player's browser.
- The solutions are embedded in the page so Check can work, so a curious player can find them in the source.

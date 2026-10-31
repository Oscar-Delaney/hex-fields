"""Geometric hex boards.  Usage: python3 shape_geo.py star A out.json | ring OUTER INNER out.json
star A: a six-pointed star, two overlapping triangles whose middle is a hexagon of side A+1
        (A=3 gives 73 cells).
ring OUTER INNER: a hexagon of side OUTER with a hexagonal hole of side INNER in the middle."""
import json, sys


def star(a):
    # cube coordinates x, y, z with x + y + z = 0; each triangle bounds all three from one side
    return sorted(((x, y) for x in range(-2 * a, 2 * a + 1) for y in range(-2 * a, 2 * a + 1)
                   if min(x, y, -x - y) >= -a or max(x, y, -x - y) <= a), key=lambda c: (c[1], c[0]))


def ring(outer, inner):
    R = outer - 1
    return sorted(((q, r) for r in range(-R, R + 1) for q in range(-R, R + 1)
                   if abs(q + r) <= R and max(abs(q), abs(r), abs(q + r)) >= inner), key=lambda c: (c[1], c[0]))


if __name__ == '__main__':
    kind = sys.argv[1]
    cells = star(int(sys.argv[2])) if kind == 'star' else ring(int(sys.argv[2]), int(sys.argv[3]))
    from shape_map import show
    show(cells)
    print(len(cells), 'cells')
    out = sys.argv[-1]
    if out.endswith('.json'):
        json.dump([list(c) for c in cells], open(out, 'w'))

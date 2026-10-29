"""Trace mainland Great Britain onto a pointy-top hex grid.
Usage: python3 -I shape_gb.py ne_50m_admin_0_countries.geojson cell_km [out.json [x_shift y_shift]]
Shifts move the grid by fractions of a cell width / row. A cell is in if its centre is on land;
only the largest connected piece is kept. The site uses: 31 gb.json 0 0.5 (89 cells)."""
import json, math, sys

DIRS = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
KM_PER_DEG = 111.32
LAT0 = 54.5

geo = json.load(open(sys.argv[1]))
uk = next(f for f in geo['features'] if f['properties'].get('ADMIN') == 'United Kingdom')
polys = uk['geometry']['coordinates']


def to_km(lon, lat):
    return lon * KM_PER_DEG * math.cos(math.radians(LAT0)), -lat * KM_PER_DEG


def area(ring):
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]))) / 2


rings = [[to_km(*p) for p in poly[0]] for poly in polys]
gb = max(rings, key=area)  # the island of Great Britain


def inside(x, y, ring):
    hit = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            hit = not hit
    return hit


def trace(s, ox=0.0, oy=0.0):
    xs, ys = [p[0] for p in gb], [p[1] for p in gb]
    cells = set()
    rmin, rmax = int(min(ys) / (1.5 * s)) - 2, int(max(ys) / (1.5 * s)) + 2
    for r in range(rmin, rmax + 1):
        qmin = int(min(xs) / (math.sqrt(3) * s) - r / 2) - 2
        qmax = int(max(xs) / (math.sqrt(3) * s) - r / 2) + 2
        for q in range(qmin, qmax + 1):
            x, y = math.sqrt(3) * s * (q + r / 2) + ox, 1.5 * s * r + oy
            if inside(x, y, gb):
                cells.add((q, r))
    # keep the largest connected piece
    best, seen = set(), set()
    for c in cells:
        if c in seen:
            continue
        comp, stack = {c}, [c]
        seen.add(c)
        while stack:
            q, r = stack.pop()
            for a, b in DIRS:
                d = (q + a, r + b)
                if d in cells and d not in seen:
                    seen.add(d)
                    comp.add(d)
                    stack.append(d)
        best = max(best, comp, key=len)
    # re-centre so axial coordinates start near zero
    rs = sorted({r for _, r in best})
    r0 = rs[len(rs) // 2]
    q0 = round(sum(q + r / 2 for q, r in best) / len(best) - r0 / 2)
    return sorted(((q - q0, r - r0) for q, r in best), key=lambda c: (c[1], c[0]))


def show(cells):
    rows = {}
    for q, r in cells:
        rows.setdefault(r, []).append(q)
    xmin = min(2 * q + r for q, r in cells)
    for r in sorted(rows):
        line = [' '] * (max(2 * q + r for q, r in cells) - xmin + 2)
        for q in rows[r]:
            line[2 * q + r - xmin] = 'o'
        print(''.join(line).rstrip())


if __name__ == '__main__':
    s = float(sys.argv[2])
    fx, fy = (float(sys.argv[4]), float(sys.argv[5])) if len(sys.argv) > 5 else (0, 0)
    cells = trace(s, fx * math.sqrt(3) * s, fy * 1.5 * s)
    show(cells)
    print(len(cells), 'cells at', s, 'km')
    if len(sys.argv) > 3:
        json.dump([list(c) for c in cells], open(sys.argv[3], 'w'))

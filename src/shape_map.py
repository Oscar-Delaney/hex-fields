"""Trace a country's largest landmass onto a pointy-top hex grid.
Usage: python3 -I shape_map.py ne_50m_admin_0_countries.geojson COUNTRY cell_km out.json [x_shift y_shift [lat0]]
Shifts move the grid by fractions of a cell width / row; lat0 is the latitude whose scale the
projection keeps (default: the landmass's middle). A cell is in if its centre is on land; only the
largest connected piece is kept. Pass '-' as out.json to just preview."""
import json, math, sys

DIRS = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
KM_PER_DEG = 111.32


def area(ring):
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]))) / 2


def inside(x, y, ring):
    hit = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            hit = not hit
    return hit


def landmass(geojson, country, lat0=None):
    """Largest polygon of the country, projected to km (x east, y south)."""
    feat = next(f for f in json.load(open(geojson))['features'] if f['properties'].get('ADMIN') == country)
    geom = feat['geometry']
    polys = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
    ring = max((p[0] for p in polys), key=lambda r: area([(x * math.cos(math.radians(y)), y) for x, y in r]))
    if lat0 is None:
        lats = [y for _, y in ring]
        lat0 = (min(lats) + max(lats)) / 2
    k = math.cos(math.radians(lat0))
    return [(lon * KM_PER_DEG * k, -lat * KM_PER_DEG) for lon, lat in ring]


def trace(land, s, ox=0.0, oy=0.0):
    xs, ys = [p[0] for p in land], [p[1] for p in land]
    cells = set()
    for r in range(int(min(ys) / (1.5 * s)) - 2, int(max(ys) / (1.5 * s)) + 3):
        for q in range(int(min(xs) / (math.sqrt(3) * s) - r / 2) - 2, int(max(xs) / (math.sqrt(3) * s) - r / 2) + 3):
            if inside(math.sqrt(3) * s * (q + r / 2) + ox, 1.5 * s * r + oy, land):
                cells.add((q, r))
    best, seen = set(), set()  # keep the largest connected piece
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
    rs = sorted({r for _, r in best})  # re-centre so axial coordinates start near zero
    r0 = rs[len(rs) // 2]
    q0 = round(sum(q + r / 2 for q, r in best) / len(best) - r0 / 2)
    return sorted(((q - q0, r - r0) for q, r in best), key=lambda c: (c[1], c[0]))


def show(cells):
    xmin = min(2 * q + r for q, r in cells)
    rows = {}
    for q, r in cells:
        rows.setdefault(r, []).append(2 * q + r - xmin)
    for r in sorted(rows):
        line = [' '] * (max(rows[r]) + 1)
        for x in rows[r]:
            line[x] = 'o'
        print(''.join(line))


if __name__ == '__main__':
    geojson, country, s, out = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
    fx, fy = (float(sys.argv[5]), float(sys.argv[6])) if len(sys.argv) > 6 else (0, 0)
    lat0 = float(sys.argv[7]) if len(sys.argv) > 7 else None
    cells = trace(landmass(geojson, country, lat0), s, fx * math.sqrt(3) * s, fy * 1.5 * s)
    show(cells)
    print(len(cells), 'cells at', s, 'km')
    if out != '-':
        json.dump([list(c) for c in cells], open(out, 'w'))

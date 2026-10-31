"""Generate one day of a Hex Fields week.  Usage: python3 week.py <day> <seed> <minutes>

Difficulty = the lowest solver tier that finishes the puzzle, then how many rounds it
needs at that tier. Weekdays never need trials; weekends need a few short ones."""
import json, math, os, random, sys, time
from gen import Board, Layout, Solver, gen_solution, SIZE_W

SMALL_W = {1: 1, 2: 3, 3: 5, 4: 6, 5: 5, 6: 3, 7: 2, 8: 1}
DAYS = {
    'mon': dict(N=4, tier=1, rounds=(0, 0), q=0, ok=dict(max_size=8, max_ones=2, min_col=2), w=SMALL_W),
    'tue': dict(N=5, tier=2, rounds=(1, 4), q=0, ok=dict(), w=SIZE_W),
    'wed': dict(N=5, tier=2, rounds=(5, 14), q=1, ok=dict(), w=SIZE_W),
    'thu': dict(N=6, tier=2, rounds=(5, 12), q=1, ok=dict(max_size=13, max_ones=3), w=SIZE_W),
    'fri': dict(N=6, tier=2, rounds=(14, 99), q=1, ok=dict(max_size=13, max_ones=3), w=SIZE_W),
    'sat': dict(N=6, tier=3, rounds=(1, 2), q=2, ok=dict(max_size=13, max_ones=3), w=SIZE_W),
    'sun': dict(N=6, tier=3, rounds=(3, 8), q=3, ok=dict(max_size=13, max_ones=3), w=SIZE_W),
    # specials on custom boards (shapes/*.json from shape_map.py / shape_geo.py)
    'gb': dict(cells='shapes/gb.json', tier=3, rounds=(1, 3), q=2, ok=dict(max_size=13, max_ones=3), w=SIZE_W,
               budget=25),
    'star': dict(cells='shapes/star.json', tier=2, rounds=(5, 12), q=1, ok=dict(max_size=12, max_ones=3), w=SIZE_W),
    'ring': dict(cells='shapes/ring.json', tier=2, rounds=(12, 99), q=1, ok=dict(max_size=12, max_ones=3), w=SIZE_W),
    'aus': dict(cells='shapes/aus.json', tier=3, rounds=(1, 3), q=2, ok=dict(max_size=13, max_ones=3), w=SIZE_W,
                budget=25),
}
HERE = os.path.dirname(os.path.abspath(__file__))


def score(B, clues, tier):
    st, cand, log = Solver(B, clues).solve(tier)
    if st == 'contradiction':
        raise RuntimeError('solver contradiction on a valid layout')
    return sum(3 - bin(m).count('1') for m in cand), st


def grade(B, clues, max_tier, budget=10):
    """(tier, rounds at that tier) for the lowest tier that solves it, or None."""
    S = Solver(B, clues, deadline=time.time() + budget)
    for tier in range(1, max_tier + 1):
        try:
            st, _, log = S.solve(tier)
        except TimeoutError:
            return None
        if st == 'contradiction':
            raise RuntimeError('solver contradiction on a valid layout')
        if st == 'solved':
            return tier, log['t%d_rounds' % tier] if tier > 1 else 0
    return None


def distance(g, cfg, nq):
    """How far a grade is from the day's target; 0 means on target."""
    if g is None:
        return math.inf
    tier, rounds = g
    lo, hi = cfg['rounds']
    if tier != cfg['tier']:
        d = 100 * abs(tier - cfg['tier']) + (lo if tier < cfg['tier'] else 0)
    else:
        d = lo - rounds if rounds < lo else max(0, rounds - hi)
    return d + (cfg['q'] - nq)


def run(day, seed, minutes):
    cfg = DAYS[day]
    shape = cfg.get('cells') and json.load(open(os.path.join(HERE, '..', cfg['cells'])))
    B = Board(cfg.get('N'), shape)
    budget = cfg.get('budget', 10)
    rng = random.Random(seed)
    stop = time.time() + 60 * minutes
    climb_tier = min(cfg['tier'], 2)
    while time.time() < stop:
        # 1. random map, then climb until the solver can finish it at the climb tier
        while True:
            sol = gen_solution(B, rng, cfg['w'])
            if not sol:
                continue
            col, regions = sol
            reg = [0] * B.n
            for i, r in enumerate(regions):
                for x in r:
                    reg[x] = i
            L = Layout(B, reg, [col[r[0]] for r in regions], [rng.choice(r) for r in regions])
            if L.ok(**cfg['ok']):
                break
        best, st = score(B, L.clues(), climb_tier)
        for _ in range(4000 if B.n < 80 else 15000):
            if st == 'solved' or time.time() > stop:
                break
            M = L.copy()
            if not M.mutate(rng) or not M.ok(**cfg['ok']):
                continue
            s, st2 = score(B, M.clues(), climb_tier)
            if s >= best:
                L, best, st = M, s, st2
        if st != 'solved':
            continue
        # 2. tune toward the day's difficulty: map/clue moves and '?' clues, keeping uniqueness
        qs = ()
        cur = distance(grade(B, L.clues(qs), cfg['tier'], budget), cfg, len(qs))
        for _ in range(600):
            if cur == 0 or time.time() > stop:
                break
            M, q2 = L.copy(), qs
            u = rng.random()
            if u < 0.2 and len(qs) < cfg['q']:
                sizes = M.sizes()
                opts = [r for r in range(len(M.rcol)) if r not in qs and 3 <= sizes[r] <= 9]
                if not opts:
                    continue
                q2 = qs + (rng.choice(opts),)
            elif not M.mutate(rng) or not M.ok(**cfg['ok']):
                continue
            d = distance(grade(B, M.clues(q2), cfg['tier'], budget), cfg, len(q2))
            if d <= cur:
                L, qs, cur = M, q2, d
        if cur == 0:
            clues = L.clues(qs)
            tier, rounds = grade(B, clues, cfg['tier'], budget=600)
            return dict(day=day, N=cfg.get('N'), seed=seed, cells=B.cells, solution=L.col(),
                        clues=[[x, c, n] for x, (c, n) in sorted(clues.items())],
                        grade=dict(tier=tier, rounds=rounds), fields=len(L.rcol))
        print(day, 'missed target, distance', cur, flush=True)
    return None


if __name__ == '__main__':
    day, seed, minutes = sys.argv[1], int(sys.argv[2]), float(sys.argv[3])
    t = time.time()
    res = run(day, seed, minutes)
    if not res:
        sys.exit(f'{day}: nothing found in {minutes} min')
    json.dump(res, open(f'{day}_{seed}.json', 'w'))
    print(day, 'done in', round(time.time() - t), 's', res['grade'], 'fields', res['fields'],
          '?', sum(n is None for _, _, n in res['clues']), flush=True)

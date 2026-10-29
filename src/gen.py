"""Hex Fields: 3-colour Fields on a hexagonal board.

Rules: colour every cell. Each field (maximal connected one-colour group) holds
exactly one clue, of its colour; the number is the field's size ('?' = any).

The solver only makes sound deductions, so a full solve proves uniqueness.
Tiers: 1 = completed area, separation, overgrowth, forced expansion;
2 = out of range, bottleneck, orphan pathing; 3 = single-cell trials.
"""
import heapq, json, random, sys, time
from collections import Counter

DIRS = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
SINGLE = {1: 0, 2: 1, 4: 2}
FULL = 7


class Board:
    """A hexagon of side N, or any set of axial (q, r) cells."""

    def __init__(self, N=None, cells=None):
        if cells is None:
            R = N - 1
            cells = [(q, r) for r in range(-R, R + 1) for q in range(-R, R + 1) if abs(q + r) <= R]
        self.N = N
        self.cells = [tuple(c) for c in cells]
        self.idx = {c: i for i, c in enumerate(self.cells)}
        self.n = len(self.cells)
        self.nbr = [[self.idx[(q + a, r + b)] for a, b in DIRS if (q + a, r + b) in self.idx]
                    for q, r in self.cells]


class Contradiction(Exception):
    pass


# ---------- solution generation ----------

SIZE_W = {1: 1, 2: 3, 3: 5, 4: 6, 5: 6, 6: 5, 7: 4, 8: 3, 9: 2, 10: 2, 11: 1}


def gen_solution(B, rng, weights=SIZE_W):
    col, reg, regions = [-1] * B.n, [-1] * B.n, []
    while True:
        best, best_allowed = None, None
        order = list(range(B.n))
        rng.shuffle(order)
        for i in order:
            if col[i] >= 0:
                continue
            allowed = [c for c in range(3) if all(col[j] != c for j in B.nbr[i])]
            if not allowed:
                return None
            if best is None or len(allowed) < len(best_allowed):
                best, best_allowed = i, allowed
        if best is None:
            return col, regions
        c = rng.choice(best_allowed)
        target = rng.choices(list(weights), weights=list(weights.values()))[0]
        rid = len(regions)
        R = [best]
        col[best], reg[best] = c, rid
        while len(R) < target:
            opts = sorted({j for i in R for j in B.nbr[i] if col[j] < 0
                           and all(col[k] != c or reg[k] == rid for k in B.nbr[j])})
            if not opts:
                break
            j = rng.choice(opts)
            col[j], reg[j] = c, rid
            R.append(j)
        regions.append(R)


# ---------- solver ----------

class Solver:
    def __init__(self, B, clues, deadline=None, trial_steps=40):
        self.B, self.clues = B, clues  # clues: cell -> (colour, size or None)
        self.deadline, self.trial_steps = deadline, trial_steps

    def start(self):
        cand = [FULL] * self.B.n
        for x, (c, _) in self.clues.items():
            cand[x] = 1 << c
        return cand

    def comps(self, cand):
        B, clues = self.B, self.clues
        comp_of, comps = [-1] * B.n, []
        for i in range(B.n):
            m = cand[i]
            if m == 0:
                raise Contradiction
            if m in SINGLE and comp_of[i] < 0:
                cid, cells, stack = len(comps), [i], [i]
                comp_of[i] = cid
                while stack:
                    x = stack.pop()
                    for y in B.nbr[x]:
                        if comp_of[y] < 0 and cand[y] == m:
                            comp_of[y] = cid
                            cells.append(y)
                            stack.append(y)
                cl = [x for x in cells if x in clues]
                if len(cl) > 1:
                    raise Contradiction
                target = (clues[cl[0]][1] or B.n) if cl else None
                if cl and len(cells) > target:
                    raise Contradiction
                comps.append(dict(id=cid, c=SINGLE[m], cells=cells, clued=bool(cl),
                                  q=bool(cl) and clues[cl[0]][1] is None, target=target))
        return comps, comp_of

    @staticmethod
    def remove(cand, x, c):
        cand[x] &= ~(1 << c)
        if cand[x] == 0:
            raise Contradiction

    # ----- tier 1 -----
    def tier1(self, cand, log):
        B = self.B
        comps, comp_of = self.comps(cand)
        hit = 0
        for K in comps:  # completed area
            if K['clued'] and not K['q'] and len(K['cells']) == K['target']:
                for x in K['cells']:
                    for y in B.nbr[x]:
                        if cand[y] not in SINGLE and cand[y] >> K['c'] & 1:
                            self.remove(cand, y, K['c'])
                            hit += 1
        if hit:
            log['completed'] += hit
            return True
        for x in range(B.n):  # separation / overgrowth
            if cand[x] in SINGLE:
                continue
            for c in range(3):
                if not cand[x] >> c & 1:
                    continue
                adj = {comp_of[y] for y in B.nbr[x] if comp_of[y] >= 0 and comps[comp_of[y]]['c'] == c}
                clued = [comps[a] for a in adj if comps[a]['clued']]
                if len(clued) >= 2:
                    self.remove(cand, x, c)
                    log['separation'] += 1
                    hit += 1
                elif len(clued) == 1 and not clued[0]['q'] and \
                        1 + sum(len(comps[a]['cells']) for a in adj) > clued[0]['target']:
                    self.remove(cand, x, c)
                    log['overgrowth'] += 1
                    hit += 1
        if hit:
            return True
        for K in comps:  # forced expansion
            need = not K['clued'] or (not K['q'] and len(K['cells']) < K['target'])
            if not need:
                continue
            fr = {y for x in K['cells'] for y in B.nbr[x] if cand[y] not in SINGLE and cand[y] >> K['c'] & 1}
            if not fr:
                raise Contradiction
            if len(fr) == 1:
                cand[fr.pop()] = 1 << K['c']
                log['expansion'] += 1
                return True
        return False

    # ----- tier 2 -----
    def reach(self, cand, comps, comp_of, K, budget, banned=-1):
        """Dijkstra from K over cells that could join K. Orphan comps cost their size.
        Returns (dist over undetermined cells, set of reached orphan ids, capacity)."""
        B, c, kid = self.B, K['c'], K['id']
        dist, orph = {}, {}
        heap = [(0, x) for x in K['cells']]
        seen = set(K['cells'])
        while heap:
            d, x = heapq.heappop(heap)
            for y in B.nbr[x]:
                if y in seen or y == banned:
                    continue
                cy = comp_of[y]
                if cy >= 0:
                    O = comps[cy]
                    if O['c'] != c or O['clued'] or d + len(O['cells']) > budget:
                        continue
                    orph[cy] = d + len(O['cells'])
                    for z in O['cells']:
                        seen.add(z)
                        heapq.heappush(heap, (orph[cy], z))
                elif cand[y] >> c & 1 and d + 1 <= budget:
                    # a cell next to another clued field of colour c would join that field
                    if any(comp_of[z] >= 0 and comp_of[z] != kid and comps[comp_of[z]]['c'] == c
                           and comps[comp_of[z]]['clued'] for z in B.nbr[y]):
                        continue
                    seen.add(y)
                    dist[y] = d + 1
                    heapq.heappush(heap, (d + 1, y))
        cap = len(K['cells']) + len(dist) + sum(len(comps[o]['cells']) for o in orph)
        return dist, orph, cap

    def tier2(self, cand, log, light=False):
        B = self.B
        comps, comp_of = self.comps(cand)
        clued = [K for K in comps if K['clued']]
        R = {}
        for K in clued:
            budget = K['target'] - len(K['cells'])
            dist, orph, cap = self.reach(cand, comps, comp_of, K, budget)
            if cap < K['target'] and not K['q']:
                raise Contradiction
            R[K['id']] = (budget, dist, orph)
        # out of range
        hit = 0
        for x in range(B.n):
            if cand[x] in SINGLE:
                continue
            for c in range(3):
                if cand[x] >> c & 1 and not any(K['c'] == c and x in R[K['id']][1] for K in clued):
                    self.remove(cand, x, c)
                    hit += 1
        for O in comps:
            if not O['clued'] and not any(O['id'] in R[K['id']][2] for K in clued if K['c'] == O['c']):
                raise Contradiction
        if hit:
            log['out_of_range'] += hit
            return True
        if light:
            return False
        # bottleneck: cells every completion of K must use
        for K in clued:
            if K['q'] or len(K['cells']) == K['target']:
                continue
            budget, dist, _ = R[K['id']]
            for v in dist:
                if cand[v] in SINGLE:
                    continue
                if self.reach(cand, comps, comp_of, K, budget, banned=v)[2] < K['target']:
                    cand[v] = 1 << K['c']
                    log['bottleneck'] += 1
                    return True
        # orphan pathing: cells every connection of an orphan must use
        for O in comps:
            if O['clued']:
                continue
            Ks = [K for K in clued if O['id'] in R[K['id']][2]]
            pool = set().union(*(R[K['id']][1] for K in Ks))
            for v in pool:
                if cand[v] in SINGLE:
                    continue
                if not any(O['id'] in self.reach(cand, comps, comp_of, K, R[K['id']][0], banned=v)[1]
                           for K in Ks):
                    cand[v] = 1 << O['c']
                    log['pathing'] += 1
                    return True
        return False

    # ----- driver -----
    def propagate(self, cand, max_tier, log, trace=None, max_steps=None, light=False):
        """Apply rules to a fixpoint, always preferring the lowest tier."""
        steps = 0
        while True:
            steps += 1
            if max_steps and steps > max_steps:
                return False
            if all(m in SINGLE for m in cand):
                self.verify(cand)
                return True
            if self.tier1(cand, log):
                continue
            if max_tier >= 2:
                before = cand[:]
                if self.tier2(cand, log, light):
                    log['t2_rounds'] += 1
                    if trace is not None:
                        trace.append(sum(a != b for a, b in zip(before, cand)))
                    continue
            if max_tier >= 3 and self.trial(cand, log):
                log['t3_rounds'] += 1
                continue
            return False

    def trial(self, cand, log):
        """Assume one colour for one cell; if short-range logic breaks, rule it out.
        Tries the most constrained cells first, and follows each trial for at most `trial_steps` steps."""
        B = self.B
        order = sorted((x for x in range(B.n) if cand[x] not in SINGLE),
                       key=lambda x: (bin(cand[x]).count('1'), -sum(cand[y] in SINGLE for y in B.nbr[x])))
        for x in order:
            for c in range(3):
                if not cand[x] >> c & 1:
                    continue
                if self.deadline and time.time() > self.deadline:
                    raise TimeoutError
                t = cand[:]
                t[x] = 1 << c
                try:
                    self.propagate(t, 2, Counter(), max_steps=self.trial_steps, light=True)
                except Contradiction:
                    self.remove(cand, x, c)
                    log['trial'] += 1
                    return True
        return False

    def verify(self, cand):
        comps, _ = self.comps(cand)
        for K in comps:
            if not K['clued'] or (not K['q'] and len(K['cells']) != K['target']):
                raise Contradiction

    def solve(self, max_tier):
        cand, log = self.start(), Counter()
        try:
            ok = self.propagate(cand, max_tier, log)
        except Contradiction:
            return 'contradiction', cand, log
        return ('solved' if ok else 'stuck'), cand, log


# ---------- puzzle search ----------

def triple_points(B, col):
    n = 0
    for i in range(B.n):
        for j in B.nbr[i]:
            for k in B.nbr[j]:
                if i < j < k and k in B.nbr[i] and len({col[i], col[j], col[k]}) == 3:
                    n += 1
    return n


def connected(B, cells):
    cells = set(cells)
    if not cells:
        return False
    first = next(iter(cells))
    seen, stack = {first}, [first]
    while stack:
        x = stack.pop()
        for y in B.nbr[x]:
            if y in cells and y not in seen:
                seen.add(y)
                stack.append(y)
    return len(seen) == len(cells)


class Layout:
    """A solution (region per cell, colour per region) plus a clue cell per region."""

    def __init__(self, B, reg, rcol, clue):
        self.B, self.reg, self.rcol, self.clue = B, reg, rcol, clue

    def copy(self):
        return Layout(self.B, self.reg[:], self.rcol[:], self.clue[:])

    def sizes(self):
        return Counter(self.reg)

    def col(self):
        return [self.rcol[r] for r in self.reg]

    def clues(self, qs=()):
        s = self.sizes()
        return {self.clue[r]: (self.rcol[r], None if r in qs else s[r]) for r in range(len(self.rcol))}

    def mutate(self, rng):
        B, reg, rcol = self.B, self.reg, self.rcol
        kind = rng.random()
        if kind < 0.3:  # move a clue within its field
            r = rng.randrange(len(rcol))
            self.clue[r] = rng.choice([x for x in range(B.n) if reg[x] == r])
            return True
        if kind < 0.4:  # recolour a field to a colour none of its neighbours has
            r = rng.randrange(len(rcol))
            cells = [x for x in range(B.n) if reg[x] == r]
            near = {rcol[reg[y]] for x in cells for y in B.nbr[x] if reg[y] != r}
            opts = [c for c in range(3) if c != rcol[r] and c not in near]
            if not opts:
                return False
            rcol[r] = rng.choice(opts)
            return True
        # move a border cell into a neighbouring field
        x = rng.randrange(B.n)
        a = reg[x]
        if self.clue[a] == x:
            return False
        bs = sorted({reg[y] for y in B.nbr[x] if reg[y] != a})
        if not bs:
            return False
        b = rng.choice(bs)
        if any(rcol[reg[y]] == rcol[b] and reg[y] != b for y in B.nbr[x]):
            return False
        if not connected(B, [y for y in range(B.n) if reg[y] == a and y != x]):
            return False
        reg[x] = b
        return True

    def ok(self, max_size=11, max_ones=2, min_col=3):
        s = self.sizes()
        per = Counter(self.rcol)
        return (max(s.values()) <= max_size and list(s.values()).count(1) <= max_ones
                and len(per) == 3 and min(per.values()) >= min_col)


def evaluate(B, clues):
    st, cand, log = Solver(B, clues).solve(2)
    if st == 'contradiction':
        raise RuntimeError('solver contradiction on a valid layout')
    return sum(3 - bin(m).count('1') for m in cand), st, log


def make(N, seed, iters=3000, want_t2=(5, 14), n_q=1):
    B = Board(N)
    rng = random.Random(seed)
    while True:
        sol = gen_solution(B, rng)
        if not sol:
            continue
        col, regions = sol
        reg = [0] * B.n
        for i, r in enumerate(regions):
            for x in r:
                reg[x] = i
        L = Layout(B, reg, [col[r[0]] for r in regions], [rng.choice(r) for r in regions])
        if L.ok():
            break
    best, st, log = evaluate(B, L.clues())
    for it in range(iters):
        M = L.copy()
        if not M.mutate(rng) or not M.ok():
            continue
        s, st2, log2 = evaluate(B, M.clues())
        if s >= best:
            L, best, st, log = M, s, st2, log2
        if st == 'solved':
            break
    if st != 'solved':
        return None
    # Wednesday: tier 1 must stall, tier 2 must finish; try '?' clues for extra bite
    qs = ()
    sizes = L.sizes()
    for r in rng.sample(range(len(L.rcol)), len(L.rcol)):
        if len(qs) >= n_q or not 3 <= sizes[r] <= 8:
            continue
        s2, st2, log2 = evaluate(B, L.clues(qs + (r,)))
        if st2 == 'solved':
            qs, log = qs + (r,), log2
    clues = L.clues(qs)
    if Solver(B, clues).solve(1)[0] == 'solved':
        return None
    if not want_t2[0] <= log['t2_rounds'] <= want_t2[1]:
        return None
    return B, L, clues, log, it


if __name__ == '__main__':
    N, seed, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    for s in range(seed, seed + 200):
        res = make(N, s)
        if res:
            break
        print('seed', s, 'rejected', flush=True)
    else:
        sys.exit('no puzzle found')
    B, L, clues, log, it = res
    print('seed', s, 'iters', it, 'fields', len(L.rcol), 'sizes', sorted(L.sizes().values()))
    print(dict(log))
    json.dump(dict(N=N, seed=s, cells=B.cells, solution=L.col(),
                   clues=[[x, c, n] for x, (c, n) in sorted(clues.items())], log=dict(log)), open(out, 'w'))

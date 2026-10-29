"""Independent uniqueness check: brute force over cell colours using only the bare rules
(no field holds two clues, none outgrows its number, every closed field is complete).
Branches on the cell with the fewest legal colours. Usage: python3 verify.py puzzle.json"""
import json, sys, time
from gen import Board

P = json.load(open(sys.argv[1]))
B = Board(cells=P['cells'])
clue = {x: (c, n) for x, c, n in P['clues']}
col = [-1] * B.n
for x, (c, _) in clue.items():
    col[x] = c
sols, nodes = [], 0


def comp(x):
    c, seen, stack = col[x], {x}, [x]
    while stack:
        y = stack.pop()
        for z in B.nbr[y]:
            if z not in seen and col[z] == c:
                seen.add(z)
                stack.append(z)
    return seen


def ok_around(x):
    for y in [x] + B.nbr[x]:
        if col[y] < 0:
            continue
        K = comp(y)
        cl = [z for z in K if z in clue]
        if len(cl) > 1:
            return False
        open_ = any(col[w] < 0 for z in K for w in B.nbr[z])
        if cl:
            n = clue[cl[0]][1]
            if n is not None and (len(K) > n or (not open_ and len(K) != n)):
                return False
        elif not open_:
            return False
    return True


def legal(x):
    out = []
    for c in range(3):
        col[x] = c
        if ok_around(x):
            out.append(c)
    col[x] = -1
    return out


def dfs():
    global nodes
    nodes += 1
    free = [i for i in range(B.n) if col[i] < 0]
    if not free:
        sols.append(col[:])
        return
    best, best_opts = None, None
    for i in free:
        if not any(col[j] >= 0 for j in B.nbr[i]):
            continue
        opts = legal(i)
        if not opts:
            return
        if best is None or len(opts) < len(best_opts):
            best, best_opts = i, opts
            if len(opts) == 1:
                break
    if best is None:
        best, best_opts = free[0], legal(free[0])
    for c in best_opts:
        col[best] = c
        if ok_around(best):
            dfs()
        col[best] = -1
        if len(sols) > 1:
            return


t = time.time()
dfs()
print('solutions found:', len(sols), '(stopped at 2)' if len(sols) > 1 else '', 'nodes', nodes, round(time.time() - t, 1), 's')
if sols:
    print('matches generated solution:', sols[0] == P['solution'])

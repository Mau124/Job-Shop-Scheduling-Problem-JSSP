"""
Tabu search for the Job Shop Scheduling Problem (JSSP), following
"A Fast Taboo Search Algorithm for the Job Shop Scheduling Problem"
(Christensen, Pedersen, Vejlin, 2008), based on Nowicki & Smutnicki (1996).

Neighbourhoods:
  n1_adjacent_swaps   adjacent swaps on the same machine        (note's definition 2, H''(pi))
  n2_block_boundary   block-boundary swaps on a critical path   (note's definition 4, H(pi))
"""

import random
from collections import deque
from ..core.models import SolverResult

def machine_of(jsp, op):
    """mu_i: machine of operation op = (job, step)."""
    j, s = op
    return jsp.ops[j][s]

def duration_of(jsp, op):
    """tau_i: processing time of operation op = (job, step). dur is indexed by machine."""
    j, s = op
    return jsp.dur[j][jsp.ops[j][s]]


def job_next(jsp, op):
    """Next operation of the same job, or None if op is the job's last step."""
    j, s = op
    return (j, s + 1) if s + 1 < jsp.max_ops[j] else None

class Evaluator:
    """Computes makespans on the JSSP and counts evaluations."""

    def __init__(self, jsp_instance):
        self.jsp = jsp_instance
        self.count = 0

    def evaluate(self, pi):
        self.count += 1
        jsp = self.jsp
        mach_next = {}
        indeg = [[0 if s == 0 else 1 for s in range(jsp.max_ops[j])]
                 for j in range(jsp.num_jobs)]
        for seq in pi:
            for a, b in zip(seq, seq[1:]):
                mach_next[a] = b
                indeg[b[0]][b[1]] += 1

        start = [[0] * jsp.max_ops[j] for j in range(jsp.num_jobs)]
        crit = [[None] * jsp.max_ops[j] for j in range(jsp.num_jobs)]
        stack = [(j, s) for j in range(jsp.num_jobs)
                 for s in range(jsp.max_ops[j]) if indeg[j][s] == 0]
        processed = 0
        while stack:
            op = stack.pop()
            processed += 1
            end = start[op[0]][op[1]] + duration_of(jsp, op)
            for nxt in (job_next(jsp, op), mach_next.get(op)):
                if nxt is None:
                    continue
                j, s = nxt
                if end > start[j][s]:
                    start[j][s] = end
                    crit[j][s] = op
                indeg[j][s] -= 1
                if indeg[j][s] == 0:
                    stack.append(nxt)
        if processed < jsp.total_operations:
            return float('inf'), None, None
        cmax = max(start[j][s] + duration_of(jsp, (j, s))
                   for j in range(jsp.num_jobs) for s in range(jsp.max_ops[j]))
        return cmax, start, crit

    def cmax(self, pi):
        return self.evaluate(pi)[0]


def critical_path(ev, pi):
    """One critical path u = (u_1, ..., u_w) of G(pi), as (job, step) pairs."""
    jsp = ev.jsp
    _, start, crit = ev.evaluate(pi)
    last = max(((j, s) for j in range(jsp.num_jobs) for s in range(jsp.max_ops[j])),
               key=lambda op: start[op[0]][op[1]] + duration_of(jsp, op))
    path = [last]
    while crit[path[-1][0]][path[-1][1]] is not None:
        path.append(crit[path[-1][0]][path[-1][1]])
    path.reverse()
    return path


def blocks(jsp, u):
    """Splits a critical path into maximal same-machine blocks B_1, ..., B_r."""
    result = [[u[0]]]
    for op in u[1:]:
        if machine_of(jsp, op) == machine_of(jsp, result[-1][-1]):
            result[-1].append(op)
        else:
            result.append([op])
    return result


def apply_move(jsp, pi, v):
    """Q(pi, v): swaps operations x and y on their machine; returns a new order."""
    x, y = v
    k = machine_of(jsp, x)
    new = list(pi)
    seq = pi[k][:]
    ix, iy = seq.index(x), seq.index(y)
    seq[ix], seq[iy] = seq[iy], seq[ix]
    new[k] = seq
    return new


def n1_adjacent_swaps(ev, pi):
    """
    N1 / H''(pi): every swap of two adjacent operations on the same machine.
    Size Theta(sum m_k). Connected, may contain infeasible orders (filtered out).
    """
    cands = []
    for seq in pi:
        for i in range(len(seq) - 1):
            v = (seq[i], seq[i + 1])
            new = apply_move(ev.jsp, pi, v)
            c = ev.cmax(new)
            if c < float('inf'):
                cands.append((v, new, c))
    return cands


def n2_block_boundary(ev, pi):
    """
    N2 / H(pi): on one critical path, swap only the first and last pair of each block;
    first block -> only its last pair, last block -> only its first pair.
    Size O(r), always feasible, not connected. Empty means pi is optimal.
    """
    bl = blocks(ev.jsp, critical_path(ev, pi))
    r = len(bl)
    moves = []
    if r > 1:
        for j, b in enumerate(bl):
            if len(b) < 2:
                continue
            first_pair = (b[0], b[1])
            last_pair = (b[-2], b[-1])
            if j == 0:
                moves.append(last_pair)
            elif j == r - 1:
                moves.append(first_pair)
            else:
                moves.append(first_pair)
                if last_pair != first_pair:
                    moves.append(last_pair)
    cands = []
    for v in moves:
        new = apply_move(ev.jsp, pi, v)
        cands.append((v, new, ev.cmax(new)))
    return cands


def neighbourhood_search(cands, T, c_best):
    """
    cands  : list of (v, pi', Cmax(pi')) for v in V(pi)
    T      : tabu list (deque, maxlen = maxt); updated in place with the inverse move
    c_best : C*, best makespan so far
    """
    allowed = [c for c in cands if c[0] not in T or c[2] < c_best]
    if allowed:
        chosen = min(allowed, key=lambda c: c[2])
    elif len(cands) == 1:
        chosen = cands[0]
    else:
        moves = [c[0] for c in cands]
        while all(mv in T for mv in moves):
            T.append(T[-1])
        chosen = next(c for c in cands if c[0] not in T)
    x, y = chosen[0]
    T.append((y, x))
    return chosen


def random_initial_solution(jsp_instance, seed=None):
    rng = random.Random(seed)
    nxt = [0] * jsp_instance.num_jobs
    pi = [[] for _ in range(jsp_instance.num_machines)]
    ready = [j for j in range(jsp_instance.num_jobs) if jsp_instance.max_ops[j] > 0]
    while ready:
        j = rng.choice(ready)
        op = (j, nxt[j])
        pi[machine_of(jsp_instance, op)].append(op)
        nxt[j] += 1
        if nxt[j] == jsp_instance.max_ops[j]:
            ready.remove(j)
    return pi

def tabu_search(jsp_instance, neighbourhood, maxiter=1000, maxt=8, seed=None):
    """
    jsp           : jsp_instance
    neighbourhood : n1_adjacent_swaps or n2_block_boundary
    maxiter       : stop after this many iterations without improving C*
    maxt          : tabu tenure (length of T)
    seed          : seed for the random initial solution

    Returns a SolverResult:
      schedule         : start times, schedule[job][step]
      makespan         : best makespan found, C*
      runtime          : total time in seconds
      time_to_best     : seconds until the best makespan was found
      success          : True if the known solution was reached
      expanded_nodes   : neighbours evaluated (makespan evaluations)
      max_frontier     : largest neighbourhood size |V(pi)| seen
      diff_to_solution : makespan - known_solution
    """
    ev = Evaluator(jsp_instance)

    pi = random_initial_solution(jsp_instance, seed)
    best_pi = pi
    c_best = ev.cmax(pi)
    T = deque([None] * maxt, maxlen=maxt)
    t = 0
    max_frontier = 0

    while t < maxiter:
        t += 1

        cands = neighbourhood(ev, pi)
        if not cands:
            # with N2 this means pi is optimal
            break

        max_frontier = max(max_frontier, len(cands))
        _, pi, c = neighbourhood_search(cands, T, c_best)   # always move to the chosen neighbour

        if c < c_best:
            best_pi, c_best = pi, c
            t = 0

    _, start, _ = Evaluator(jsp_instance).evaluate(best_pi)
    schedule = [[(j, start[j][s], start[j][s] + duration_of(jsp_instance, (j, s))) 
                    for (j, s) in seq]  for seq in best_pi ]

    return SolverResult(
        schedule=schedule,
        makespan=c_best,
        runtime=None,
        time_to_best=None,
        success=True,
        expanded_nodes=ev.count,
        max_frontier=max_frontier,
        diff_to_solution=0,
    )
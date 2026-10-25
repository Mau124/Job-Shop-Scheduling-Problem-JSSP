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
from ..core.models import SolverResult, Solver, JSP

class TabuSolver(Solver):

    def __init__(self, jsp_instance: JSP, seed: int, hyperparameters: dict):
        super().__init__(jsp_instance, hyperparameters)

        self.jsp_instance = jsp_instance
        self.seed = seed
        self.hyperparameters = hyperparameters

        self.neighbourhood_type = self.hyperparameters.get('neighbourhood', 'n1')
        self.maxiter = self.hyperparameters.get('maxiter', 1000)
        self.maxt = self.hyperparameters.get('maxt', 8)

        if self.neighbourhood_type == 'n1':
            self.neighbourhood = self.n1_adjacent_swaps
        elif self.neighbourhood_type == 'n2':
            self.neighbourhood = self.n2_block_boundary
        else:
            raise ValueError('Parameter neighbourhood must be either n1 or n2')

        self.schedule_response = None
        self.min_time = None

        self.result = None

    def solve(self):
        self.schedule_response = None
        self.min_time = None
        self.result = None
        self.expanded_nodes = 0
        self.max_frontier = 0

        ev = self.Evaluator(self, self.jsp_instance)

        pi = self._random_initial_solution(self.jsp_instance, self.seed)
        best_pi = pi
        c_best = ev.cmax(pi)
        T = deque([None] * self.maxt, maxlen=self.maxt)
        t = 0
        max_frontier = 0

        while t < self.maxiter:
            t += 1

            cands = self.neighbourhood(ev, pi)
            if not cands:
                # with N2 this means pi is optimal
                break

            max_frontier = max(max_frontier, len(cands))
            _, pi, c = self._neighbourhood_search(cands, T, c_best)   # always move to the chosen neighbour

            if c < c_best:
                best_pi, c_best = pi, c
                t = 0

        _, start, _ = self.Evaluator(self, self.jsp_instance).evaluate(best_pi)
        schedule = [[(j, start[j][s], start[j][s] + self._duration_of(self.jsp_instance, (j, s))) 
                        for (j, s) in seq]  for seq in best_pi ]


        self.schedule_response = schedule
        self.min_time = c_best
        self.expanded_nodes = ev.count
        self.max_frontier = max_frontier

        self.result = SolverResult(
            schedule = self.schedule_response,
            makespan = self.min_time
        )

        # return SolverResult(
        #     schedule=schedule,
        #     makespan=c_best,
        #     runtime=None,
        #     time_to_best=None,
        #     success=True,
        #     expanded_nodes=ev.count,
        #     max_frontier=max_frontier,
        #     diff_to_solution=0,
        # )

    def _machine_of(self, jsp, op):
        """mu_i: machine of operation op = (job, step)."""
        j, s = op
        return jsp.ops[j][s]

    def _duration_of(self, jsp, op):
        """tau_i: processing time of operation op = (job, step). dur is indexed by machine."""
        j, s = op
        return jsp.dur[j][jsp.ops[j][s]]

    def _job_next(self, jsp, op):
        """Next operation of the same job, or None if op is the job's last step."""
        j, s = op
        return (j, s + 1) if s + 1 < jsp.max_ops[j] else None

    def _critical_path(self, ev, pi):
        """One critical path u = (u_1, ..., u_w) of G(pi), as (job, step) pairs."""
        jsp = ev.jsp
        _, start, crit = ev.evaluate(pi)
        last = max(((j, s) for j in range(jsp.num_jobs) for s in range(jsp.max_ops[j])),
                key=lambda op: start[op[0]][op[1]] + self._duration_of(jsp, op))
        path = [last]
        while crit[path[-1][0]][path[-1][1]] is not None:
            path.append(crit[path[-1][0]][path[-1][1]])
        path.reverse()
        return path

    def _blocks(self, jsp, u):
        """Splits a critical path into maximal same-machine blocks B_1, ..., B_r."""
        result = [[u[0]]]
        for op in u[1:]:
            if self._machine_of(jsp, op) == self._machine_of(jsp, result[-1][-1]):
                result[-1].append(op)
            else:
                result.append([op])
        return result

    def _apply_move(self, jsp, pi, v):
        """Q(pi, v): swaps operations x and y on their machine; returns a new order."""
        x, y = v
        k = self._machine_of(jsp, x)
        new = list(pi)
        seq = pi[k][:]
        ix, iy = seq.index(x), seq.index(y)
        seq[ix], seq[iy] = seq[iy], seq[ix]
        new[k] = seq
        return new

    class Evaluator:
        """Computes makespans on the JSSP and counts evaluations."""

        def __init__(self, outer_instance, jsp_instance):
            self.jsp = jsp_instance
            self.count = 0
            self.outer_instance = outer_instance

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
                end = start[op[0]][op[1]] + self.outer_instance._duration_of(jsp, op)
                for nxt in (self.outer_instance._job_next(jsp, op), mach_next.get(op)):
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
            cmax = max(start[j][s] + self.outer_instance._duration_of(jsp, (j, s))
                    for j in range(jsp.num_jobs) for s in range(jsp.max_ops[j]))
            return cmax, start, crit

        def cmax(self, pi):
            return self.evaluate(pi)[0]

    def n1_adjacent_swaps(self, ev, pi):
        """
        N1 / H''(pi): every swap of two adjacent operations on the same machine.
        Size Theta(sum m_k). Connected, may contain infeasible orders (filtered out).
        """
        cands = []
        for seq in pi:
            for i in range(len(seq) - 1):
                v = (seq[i], seq[i + 1])
                new = self._apply_move(ev.jsp, pi, v)
                c = ev.cmax(new)
                if c < float('inf'):
                    cands.append((v, new, c))
        return cands

    def n2_block_boundary(self, ev, pi):
        """
        N2 / H(pi): on one critical path, swap only the first and last pair of each block;
        first block -> only its last pair, last block -> only its first pair.
        Size O(r), always feasible, not connected. Empty means pi is optimal.
        """
        bl = self._blocks(ev.jsp, self._critical_path(ev, pi))
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
            new = self._apply_move(ev.jsp, pi, v)
            cands.append((v, new, ev.cmax(new)))
        return cands

    def _neighbourhood_search(self, cands, T, c_best):
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

    def _random_initial_solution(self, jsp_instance, seed=None):
        rng = random.Random(seed)
        nxt = [0] * jsp_instance.num_jobs
        pi = [[] for _ in range(jsp_instance.num_machines)]
        ready = [j for j in range(jsp_instance.num_jobs) if jsp_instance.max_ops[j] > 0]
        while ready:
            j = rng.choice(ready)
            op = (j, nxt[j])
            pi[self._machine_of(jsp_instance, op)].append(op)
            nxt[j] += 1
            if nxt[j] == jsp_instance.max_ops[j]:
                ready.remove(j)
        return pi

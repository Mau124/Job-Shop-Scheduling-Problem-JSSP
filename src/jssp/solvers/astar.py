from heapq import heappop, heappush
from itertools import count

from ..core.models import JSP, Solver, SolverResult

"""
Minimize makespan with A* and an admissible remaining-cost bound
"""
class AStarSolver(Solver):
    def __init__(self, jsp_instance: JSP, hyperparameters: dict):
        super().__init__(jsp_instance, hyperparameters)

        self.hyperparameters = hyperparameters
        heuristic = self.hyperparameters.get('heuristic', 'h2')

        if heuristic not in ("h1", "h2"):
            raise ValueError("heuristic must be 'h1' or 'h2'")

        self.num_jobs = jsp_instance.num_jobs
        self.num_machines = jsp_instance.num_machines
        # ops lists each job's machines in operation order; dur uses machine IDs
        # as column indexes, not operation positions
        self.ops = jsp_instance.ops
        self.dur = jsp_instance.dur
        self.total_operations = jsp_instance.total_operations
        self.max_ops = jsp_instance.max_ops
        self.heuristic = heuristic
        self.result = None

    def _heuristic(self, indexes, time, job_time):
        makespan = max(time, default=0)
        # h1 lets each job finish its remaining work without waiting for machines
        # Its operations still run in sequence, so the slowest job sets a lower bound
        job_bound = max(
            (
                job_time[job]
                + sum(
                    self.dur[job][machine]
                    for machine in self.ops[job][indexes[job]:self.max_ops[job]]
                )
                for job in range(self.num_jobs)
            ),
            default=0,
        )
        bound = max(makespan, job_bound)

        if self.heuristic == "h2":
            # h2 also counts each machine's remaining work after its current tail
            # Assume no further idle time, this branch cannot fill earlier gaps
            machine_bound = time.copy()
            for job in range(self.num_jobs):
                for machine in self.ops[job][indexes[job]:self.max_ops[job]]:
                    machine_bound[machine] += self.dur[job][machine]
            # Job and machine bounds overlap, so take the maximum rather than add them
            bound = max(bound, max(machine_bound, default=0))

        # Subtract the current makespan so g + h equals the final-makespan bound
        return bound - makespan

    def solve(self):
        self.schedule_response = None
        self.min_time = float("inf")
        self.result = None
        self.expanded_nodes = 0
        self.max_frontier = 0

        indexes = [0] * self.num_jobs  # Next operation index for each job
        time = [0] * self.num_machines  # Finish time of each machine's last operation
        job_time = [0] * self.num_jobs  # Finish time of each job's last operation
        # Each machine has its own list of (job, start, end) records
        schedule = [[] for _ in range(self.num_machines)]
        # Heap entries compare f = g + h first, then insertion order to break ties
        order = count()
        # The empty schedule has g = 0, so its priority is just h
        frontier = [
            (self._heuristic(indexes, time, job_time), next(order),
             indexes, time, job_time, schedule)
        ]
        self.max_frontier = len(frontier)
        seen = {(tuple(indexes), tuple(time), tuple(job_time))}

        while frontier:
            _, _, indexes, time, job_time, schedule = heappop(frontier)
            self.expanded_nodes += 1
            # Check goals when popped: the first complete schedule has minimum
            # makespan because no queued state has a smaller completion bound
            if sum(indexes) == self.total_operations:
                self.schedule_response = schedule
                self.min_time = max(time, default=0)
                self.result = SolverResult(
                    schedule=self.schedule_response,
                    makespan=self.min_time,
                )
                return

            # Choosing only the next operation of each job preserves job order
            for job in range(self.num_jobs):
                if indexes[job] >= self.max_ops[job]:
                    continue

                machine = self.ops[job][indexes[job]]
                # Append as soon as both the machine and the job are available
                start = max(time[machine], job_time[job])
                end = start + self.dur[job][machine]

                # Keep this branch's updates separate from the parent and siblings
                next_indexes = indexes.copy()
                next_time = time.copy()
                next_job_time = job_time.copy()
                next_indexes[job] += 1
                next_time[machine] = end
                next_job_time[job] = end

                key = (tuple(next_indexes), tuple(next_time), tuple(next_job_time))
                # Matching progress and availability mean identical futures and g
                # Keep the first such state, even if it has not been expanded yet
                if key in seen:
                    continue
                seen.add(key)

                # Copy each machine's list so appending here cannot change another
                # branch's schedule. Existing operation tuples are safe to share
                next_schedule = [operations.copy() for operations in schedule]
                next_schedule[machine].append((job, start, end))
                # g is makespan; an edge costs only its increase, which can be zero
                # when the new operation finishes within the current makespan
                g = max(next_time, default=0)
                h = self._heuristic(next_indexes, next_time, next_job_time)
                heappush(
                    frontier,
                    (g + h, next(order), next_indexes, next_time,
                     next_job_time, next_schedule),
                )

            self.max_frontier = max(self.max_frontier, len(frontier))

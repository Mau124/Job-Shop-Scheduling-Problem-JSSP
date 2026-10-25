from ..core.models import JSP, Solver, SolverResult

"""
Minimize makespan using start-time CSPs with MRV, LCV and forward checking
"""
class CSPSolver(Solver):
    def __init__(self, jsp_instance: JSP, hyperparameters: dict):
        super().__init__(jsp_instance, hyperparameters)

        self.hyperparameters = hyperparameters

        self.num_jobs = jsp_instance.num_jobs
        self.num_machines = jsp_instance.num_machines

        self.use_mrv = hyperparameters.get('use_mrv', True)
        self.use_lcv = hyperparameters.get('use_lcv', True)

        # Variables follow job/step order; durations are indexed by machine.
        self.operations = [
            (job, step, machine, jsp_instance.dur[job][machine])
            for job in range(self.num_jobs)
            for step, machine in enumerate(
                jsp_instance.ops[job][:jsp_instance.max_ops[job]]
            )
        ]

        self.result = None

    def solve(self):
        self.schedule_response = None
        self.min_time = float("inf")
        self.result = None
        self.expanded_nodes = 0
        self.max_frontier = 0

        job_loads = [0] * self.num_jobs
        machine_loads = [0] * self.num_machines
        earliest = {}
        for operation in self.operations:
            job, _, machine, duration = operation
            earliest[operation] = job_loads[job]
            job_loads[job] += duration
            machine_loads[machine] += duration

        # Workloads bound the optimum below; running everything serially bounds
        # it above. The first feasible integer bound is therefore optimal.
        lower_bound = max([0] + job_loads + machine_loads)
        for bound in range(lower_bound, sum(job_loads) + 1):
            domains = {}
            for operation in self.operations:
                first_start = earliest[operation]
                remaining = job_loads[operation[0]] - first_start
                # Leave enough time for this operation and its job's successors.
                domains[operation] = list(range(first_start, bound - remaining + 1))

            self._frontier_size = 1
            self.max_frontier = max(self.max_frontier, self._frontier_size)
            assignment = self._backtrack({}, domains)
            if assignment is not None:
                schedule = [[] for _ in range(self.num_machines)]
                for (job, _, machine, duration), start in assignment.items():
                    schedule[machine].append((job, start, start + duration))
                for machine_schedule in schedule:
                    machine_schedule.sort(key=lambda operation: operation[1])
                self.schedule_response = schedule
                self.min_time = bound

                self.result = SolverResult(
                    schedule = self.schedule_response,
                    makespan = self.min_time
                )

                return

    def _compatible(self, operation, start, other, other_start):
        job, step, machine, duration = operation
        other_job, other_step, other_machine, other_duration = other
        if job == other_job:
            if step + 1 == other_step and start + duration > other_start:
                return False
            if other_step + 1 == step and other_start + other_duration > start:
                return False
        if machine == other_machine:
            return start + duration <= other_start or other_start + other_duration <= start
        return True

    def _backtrack(self, assignment, domains):
        self._frontier_size -= 1
        self.expanded_nodes += 1

        if not domains:
            return assignment

        # MRV ties use job/step order. Without MRV, dict order gives that baseline.
        operation = (
            min(domains, key=lambda op: (len(domains[op]), op))
            if self.use_mrv else next(iter(domains))
        )
        values = domains[operation]
        if self.use_lcv:
            # LCV tries starts that remove the fewest values from other domains.
            values = sorted(
                values,
                key=lambda start: (
                    sum(
                        not self._compatible(operation, start, other, value)
                        for other, domain in domains.items() if other != operation
                        for value in domain
                    ),
                    start,
                ),
            )

        self._frontier_size += len(values)
        self.max_frontier = max(self.max_frontier, self._frontier_size)

        for start in values:
            # Domains already satisfy earlier assignments. Copy and filter for
            # this assignment so failed branches cannot affect their siblings.
            next_domains = {
                other: [
                    value for value in domain
                    if self._compatible(operation, start, other, value)
                ]
                for other, domain in domains.items() if other != operation
            }
            if any(not domain for domain in next_domains.values()):
                self._frontier_size -= 1
                continue
            result = self._backtrack({**assignment, operation: start}, next_domains)
            if result is not None:
                return result
        return None

from ..core.models import JSP, Solver, SolverResult
import copy
from abc import abstractmethod

class RecursiveSolver(Solver):

    def __init__(self, jsp_instance: JSP, hyperparameters: dict):
        super().__init__(jsp_instance, hyperparameters)

        self.num_jobs = jsp_instance.num_jobs
        self.num_machines = jsp_instance.num_machines
        self.ops = jsp_instance.ops
        self.dur = jsp_instance.dur
        self.total_operations = jsp_instance.total_operations
        self.max_ops = jsp_instance.max_ops

        self.result = None

    def solve(self):
        self.result = None
        self.expanded_nodes = 0
        self.max_frontier = 1
        self._frontier_size = 1

        self.indexes = [0 for _ in range(self.num_jobs)]
        self.operations_covered = 0
        self.schedule = [[] for _ in range(self.num_machines)]
        self.time = [0 for _ in range(self.num_machines)]
        self.job_time = [0 for _ in range(self.num_jobs)]

        self.schedule_response = None
        self.min_time = float('inf')

        initial_actions = list(range(self.num_jobs))
        self._search_schedule(initial_actions)

        self.result = SolverResult(
            schedule = self.schedule_response,
            makespan = self.min_time
        )

    def _search_schedule(self, possible_actions: list[int]):
        self._frontier_size -= 1
        self.expanded_nodes += 1

        if self.operations_covered >= self.total_operations:
            total_time = max(self.time, default=0)
            if total_time < self.min_time:
                self.min_time = total_time
                self.schedule_response = copy.deepcopy(self.schedule)
            return

        next_jobs = [
            job_idx
            for job_idx in list(self.get_next_actions(possible_actions))
            if self.indexes[job_idx] < self.max_ops[job_idx]
        ]
        self._frontier_size += len(next_jobs)
        self.max_frontier = max(self.max_frontier, self._frontier_size)

        for job_idx in next_jobs:
            machine = self.ops[job_idx][self.indexes[job_idx]]

            before_time_machine = self.time[machine]
            before_job_time = self.job_time[job_idx]
            start_time = max(before_time_machine, before_job_time)
            end_time = start_time + self.dur[job_idx][machine]

            self.time[machine] = end_time
            self.job_time[job_idx] = self.time[machine]
            self.indexes[job_idx] += 1
            self.operations_covered += 1

            self.schedule[machine].append((job_idx, start_time, end_time))

            if self.indexes[job_idx] >= self.max_ops[job_idx]:
                possible_actions.remove(job_idx)

            self._search_schedule(possible_actions)

            if self.indexes[job_idx] >= self.max_ops[job_idx]:
                possible_actions.append(job_idx)

            self.time[machine] = before_time_machine
            self.job_time[job_idx] = before_job_time

            self.indexes[job_idx] -= 1
            self.operations_covered -= 1
            self.schedule[machine].pop(-1)
            
    @abstractmethod
    def get_next_actions(self, possible_actions: list[int]) -> list[int]:
        # This function should return the next actions to visit
        # Actions will be visited in the exact order return by this function
        pass

class DFSSolver(RecursiveSolver):

    def get_next_actions(self, possible_actions: list[int]) -> list[int]:
        # Since dfs is deterministic, we return the same possible actions always
        return possible_actions

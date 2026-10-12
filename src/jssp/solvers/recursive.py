from ..core.models import JSP
from abc import ABC, abstractmethod
import copy

class RecursiveSolver(ABC):

    def __init__(self, jsp_instance: JSP):
        self.num_jobs = jsp_instance.num_jobs
        self.num_machines = jsp_instance.num_machines
        self.ops = jsp_instance.ops
        self.dur = jsp_instance.dur
        self.total_operations = jsp_instance.total_operations
        self.max_ops = jsp_instance.max_ops

    def solve(self):
        self.indexes = [0 for _ in range(self.num_jobs)]
        self.operations_covered = 0
        self.schedule = [[] for _ in range(self.num_machines)]
        self.time = [0 for _ in range(self.num_machines)]
        self.job_time = [0 for _ in range(self.num_jobs)]

        self.schedule_response = None
        self.min_time = float('inf')

        initial_actions = list(range(self.num_jobs))
        self._search_schedule(initial_actions)

    def _search_schedule(self, possible_actions: list[int]):
                
        if self.operations_covered >= self.total_operations:
            total_time = max(self.time)
            if total_time < self.min_time:
                self.min_time = total_time
                self.schedule_response = copy.deepcopy(self.schedule)
            return

        next_jobs = self.get_next_actions(possible_actions)

        for job_idx in next_jobs:
            if self.indexes[job_idx] < self.max_ops[job_idx]:
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
                self.operations_covered -=1
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

class HeuristicSolver(RecursiveSolver):

    def get_next_actions(self, possible_actions: list[int]) -> list[int]:
        # We need to compare possible_actions in order to return the best valued
        # first
        pass

# THIS CLASS SHOULD BE DEPRECATED. THE USAGE SHOULD BE USING RECURSIVESOLVER
class UninformedSolver:

    def __init__(self, jsp_instance: JSP):
        self.num_jobs = jsp_instance.num_jobs
        self.num_machines = jsp_instance.num_machines
        self.ops = jsp_instance.ops
        self.dur = jsp_instance.dur
        self.total_operations = jsp_instance.total_operations
        self.max_ops = jsp_instance.max_ops

    def solve(self):
        self.indexes = [0 for _ in range(self.num_jobs)]
        self.operations_covered = 0
        self.schedule = [[] for _ in range(self.num_machines)]
        self.time = [0 for _ in range(self.num_machines)]
        self.job_time = [0 for _ in range(self.num_jobs)]
        self.schedule_response = None
        self.min_time = float('inf')

        self._search_schedule()

    def _search_schedule(self):
            
        if self.operations_covered >= self.total_operations:
            total_time = max(self.time)
            if total_time < self.min_time:
                self.min_time = total_time
                self.schedule_response = copy.deepcopy(self.schedule)
            return

        # For it to use an heuristic, it most change the way it selects the next
        # job id. As for now, it adds the jobs deterministically

        for job_idx in range(self.num_jobs):
            if self.indexes[job_idx] < self.max_ops[job_idx]:
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

                self._search_schedule()

                self.time[machine] = before_time_machine
                self.job_time[job_idx] = before_job_time

                self.indexes[job_idx] -= 1
                self.operations_covered -=1
                self.schedule[machine].pop(-1)

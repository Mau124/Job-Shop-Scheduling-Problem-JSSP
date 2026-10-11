from ..core.models import JSP
import copy

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

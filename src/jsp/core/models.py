from dataclasses import dataclass

# Problem representation

@dataclass(frozen=True)
class Operation:
    job_id: int
    operation_id: int
    machine_id: int
    duration: int

@dataclass
class Job:
    job_id: int
    operations: list[Operation]

@dataclass
class JSPInstance:
    jobs: list[Job]
    num_machines: int

''' Instance example
instance = JSPInstance(
    jobs=[
        Job(
            job_id=0,
            operations=[
                Operation(0, 0, machine_id=0, duration=3),
                Operation(0, 1, machine_id=1, duration=2),
            ],
        ),
        Job(
            job_id=1,
            operations=[
                Operation(1, 0, machine_id=1, duration=2),
                Operation(1, 1, machine_id=0, duration=4),
            ],
        ),
    ],
    num_machines=2,
)
'''

# Solution representation

@dataclass(frozen=True)
class ScheduledOperation:
    operation: Operation
    start_time: int

    @property
    def end_time(self):
        return self.start_time + self.operation.duration

@dataclass
class Schedule:
    operations: list[ScheduledOperation]

    @property
    def makespan(self):
        if not self.operations:
            return 0

        return max(op.end_time for op in self.operations)

''' Solution example
Schedule(
    operations=[
        ScheduledOperation(operation=..., start_time=0),
        ScheduledOperation(operation=..., start_time=3),
        ScheduledOperation(operation=..., start_time=0),
        ScheduledOperation(operation=..., start_time=5),
    ]
)
'''

# Result model

@dataclass
class SolverResult:
    schedule: Schedule | None

    makespan: int | None

    runtime: float
    time_to_best: float | None

    success: bool

    expanded_nodes: int | None = None
    max_frontier: int | None = None

# Validation model

@dataclass
class ValidationResult:
    valid: bool
    errors: list[str]

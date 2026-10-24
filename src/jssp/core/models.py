from dataclasses import dataclass
from abc import ABC, abstractmethod
import inspect

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

@dataclass
class JSP:
    name: str
    known_solution: int
    num_jobs: int
    num_machines: int
    total_operations: int
    max_ops: list[int]
    ops: list[list]
    dur: list[list]

class Solver(ABC):

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        
        sig = inspect.signature(cls.__init__)
        parameters = list(sig.parameters.keys())

        if 'jsp_instance' not in parameters:
            raise TypeError(
                f"Error: Class '{cls.__name__}' must include 'jsp_instance' "
                f"in its __init__ signature to match the Solver contract."
            )

        if 'seed' not in parameters:
            raise TypeError(
                f"Error: Class '{cls.__name__}' must include 'seed' "
                f"in its __init__ signature to match the Solver contract."
            )

        if 'hyperparameters' not in parameters:
            raise TypeError(
                f"Error: Class '{cls.__name__}' must include 'hyperparameters' "
                f"in its __init__ signature to match the Solver contract."
            )

    def __init__(self, jsp_instance: JSP, seed: int, hyperparameters: dict):
        self.expanded_nodes = None
        self.max_frontier = None

    @abstractmethod
    def solve():
        pass

@dataclass
class SolverConfig:
    name: str
    solver: Solver
    hyperparameters: dict

@dataclass
class ExperimentConfig:
    n_repeats: int
    max_time: int
    instances: list[JSP]
    seeds: list[int]
    solver: SolverConfig

@dataclass
class BenchmarkConfig:
    name: str
    solvers: list[SolverConfig]
    seeds: list[int]
    n_repeats: int
    max_time: int
    instances: list[JSP]
    output_path: str

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
    schedule: list | None
    makespan: int | None

@dataclass
class ExperimentResult:
    solver_result: SolverResult | None
    runtime: float
    time_to_best: float | None
    success: bool
    expanded_nodes: int | None = None
    max_frontier: int | None = None
    diff_to_solution: int | None = None

# Validation model

@dataclass
class ValidationResult:
    valid: bool
    errors: list[str]
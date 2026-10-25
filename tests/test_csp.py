from pathlib import Path

import pytest

from jssp.core.utils import read_problem_instance
from jssp.solvers.csp import CSPSolver


@pytest.mark.parametrize("use_heuristics", [True, False])
def test_example1(use_heuristics):
    path = Path(__file__).resolve().parents[1] / "instances/generated/simple/example1.json"
    instance = read_problem_instance(path)
    solver = CSPSolver(
        instance,
        hyperparameters={
            "use_mrv": use_heuristics,
            "use_lcv": use_heuristics,
        },
    )
    assert solver.solve() is None
    assert solver.min_time == 9
    assert solver.schedule_response is not None
    assert len(solver.schedule_response) == instance.num_machines

    scheduled = {}
    for machine, operations in enumerate(solver.schedule_response):
        for job, start, end in operations:
            assert (job, machine) not in scheduled
            scheduled[job, machine] = (start, end)
            assert start >= 0
            assert end - start == instance.dur[job][machine]
        for current, following in zip(operations, operations[1:]):
            assert current[2] <= following[1]

    assert scheduled.keys() == {
        (job, machine)
        for job in range(instance.num_jobs)
        for machine in instance.ops[job][:instance.max_ops[job]]
    }
    assert solver.min_time == max(end for _, end in scheduled.values())
    for job in range(instance.num_jobs):
        machines = instance.ops[job][:instance.max_ops[job]]
        for current, following in zip(machines, machines[1:]):
            assert scheduled[job, current][1] <= scheduled[job, following][0]

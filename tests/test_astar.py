from pathlib import Path

import pytest

from jssp.core.utils import read_problem_instance
from jssp.solvers.astar import AStarSolver


@pytest.mark.parametrize("heuristic", ["h1", "h2"])
def test_example1(heuristic):
    path = Path(__file__).resolve().parents[1] / "instances/generated/easy/example1.json"
    solver = AStarSolver(read_problem_instance(path), heuristic)
    solver.solve()
    assert solver.min_time == 9
    assert solver.schedule_response is not None

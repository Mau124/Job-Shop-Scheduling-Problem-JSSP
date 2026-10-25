from pathlib import Path

import pytest
import yaml

from jssp.core.models import ExperimentConfig, SolverConfig
from jssp.core.utils import read_problem_instance
from jssp.experiments.experiments import Experiment
from jssp.solvers.astar import AStarSolver
from jssp.solvers.csp import CSPSolver
from jssp.solvers.recursive import DFSSolver
from jssp.solvers.tabu import TabuSolver


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INSTANCE_PATH = PROJECT_ROOT / "instances/generated/simple/example1.json"
BENCHMARK_CONFIGS = [
    PROJECT_ROOT / "experiments/configs/examples/basic_benchmark.yaml",
    *sorted((PROJECT_ROOT / "experiments/configs/final").glob("*.yaml")),
]
SOLVER_CASES = [
    (AStarSolver, {"heuristic": "h2"}, False),
    (DFSSolver, {}, False),
    (CSPSolver, {"use_mrv": True, "use_lcv": True}, False),
    (
        TabuSolver,
        {"neighbourhood": "n1", "maxiter": 3, "maxt": 2},
        True,
    ),
]


@pytest.fixture(scope="module")
def instance():
    return read_problem_instance(INSTANCE_PATH)


def make_solver(solver_class, instance, hyperparameters, requires_seed):
    arguments = {
        "jsp_instance": instance,
        "hyperparameters": hyperparameters,
    }
    if requires_seed:
        arguments["seed"] = 42
    return solver_class(**arguments)


@pytest.mark.parametrize(
    "solver_class,hyperparameters,requires_seed",
    SOLVER_CASES,
    ids=["astar", "dfs", "csp", "tabu"],
)
def test_solver_metrics_are_initialized_and_reset(
    solver_class,
    hyperparameters,
    requires_seed,
    instance,
):
    solver = make_solver(
        solver_class,
        instance,
        hyperparameters,
        requires_seed,
    )

    assert solver.expanded_nodes is None
    assert solver.max_frontier is None

    solver.solve()
    first_metrics = (solver.expanded_nodes, solver.max_frontier)

    assert all(type(metric) is int for metric in first_metrics)
    assert solver.expanded_nodes > 0
    assert solver.max_frontier >= 0

    solver.solve()

    assert (solver.expanded_nodes, solver.max_frontier) == first_metrics


@pytest.mark.parametrize(
    "solver_class,hyperparameters,_requires_seed",
    SOLVER_CASES,
    ids=["astar", "dfs", "csp", "tabu"],
)
def test_experiment_worker_records_solver_metrics(
    solver_class,
    hyperparameters,
    _requires_seed,
    instance,
):
    experiment = Experiment(
        ExperimentConfig(
            n_repeats=1,
            max_time=1,
            instances=[instance],
            seeds=[42],
            solver=SolverConfig(
                name=solver_class.__name__,
                solver=solver_class.__name__,
                hyperparameters=hyperparameters,
            ),
        )
    )
    worker_result = {}

    experiment._worker_target(
        solver_class,
        instance,
        42,
        hyperparameters,
        worker_result,
    )

    assert worker_result.get("error") is None
    assert worker_result["success"] is True
    assert worker_result["schedule_response"] is not None
    assert worker_result["min_time"] is not None
    assert type(worker_result["expanded_nodes"]) is int
    assert type(worker_result["max_frontier"]) is int


@pytest.mark.parametrize("config_path", BENCHMARK_CONFIGS, ids=lambda path: path.stem)
def test_benchmark_tabu_neighbourhoods_match_their_labels(config_path, instance):
    with config_path.open(encoding="utf-8") as config_file:
        benchmark = yaml.safe_load(config_file)["benchmark"]

    tabu_configs = {
        solver["name"]: solver["hyperparameters"]
        for solver in benchmark["solvers"]
        if solver["type"] == "TabuSolver"
    }

    assert set(tabu_configs) == {"Tabu - n1", "Tabu - n2"}
    for name, expected_neighbourhood in (
        ("Tabu - n1", "n1"),
        ("Tabu - n2", "n2"),
    ):
        hyperparameters = tabu_configs[name]
        assert hyperparameters["neighbourhood"] == expected_neighbourhood

        solver = TabuSolver(instance, seed=42, hyperparameters=hyperparameters)
        assert solver.neighbourhood_type == expected_neighbourhood

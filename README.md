# Job Shop Scheduling Problem (JSSP)

This repository is a Python research implementation of the Job Shop
Scheduling Problem (JSSP). Given jobs with ordered operations and shared
machines, the solvers build feasible schedules that minimize the makespan.

The project includes exact search methods, a tabu-search heuristic, JSON
problem instances, a YAML-driven experiment runner, schedule plotting, and a
notebook with worked examples.

## Implemented solvers

| Solver | Entry point | Approach |
| --- | --- | --- |
| Depth-first search | `DFSSolver` | Exhaustive recursive search |
| A* | `AStarSolver` | Search with the `h1` or `h2` admissible bound |
| Constraint satisfaction | `CSPSolver` | MRV/LCV backtracking |
| Tabu search | `tabu_search` | `N1`/`N2` neighborhood search |

The class-based solvers expose their results after `solve()` through
`schedule_response` and `min_time`. `tabu_search` returns a `SolverResult`.
Schedules are grouped by machine and use
`(job_id, start_time, end_time)` tuples.

## Requirements

- Python 3.12 or newer
- `uv` for environment and dependency management

## Setup

Clone the repository and synchronize its locked dependencies:

```bash
git clone https://github.com/Mau124/Job-Shop-Scheduling-Problem-JSSP.git
cd Job-Shop-Scheduling-Problem-JSSP
uv sync
```

`uv` creates the `.venv` environment and installs the local `jssp` package.
The commands below use `uv run`, so activating the environment is optional.

## Quick start

Run A* with the stronger `h2` heuristic on the included three-job example:

```bash
uv run python - <<'PY'
from jssp.core.utils import read_problem_instance
from jssp.solvers.astar import AStarSolver

instance = read_problem_instance("instances/generated/easy/example1.json")
solver = AStarSolver(instance, heuristic="h2")
solver.solve()

print(f"Makespan: {solver.min_time}")
print(f"Schedule: {solver.schedule_response}")
PY
```

Expected makespan:

```text
9
```

The other class-based solvers follow the same pattern:

```python
from jssp.solvers.csp import CSPSolver
from jssp.solvers.recursive import DFSSolver

dfs_solver = DFSSolver(instance)
csp_solver = CSPSolver(instance, use_mrv=True, use_lcv=True)
```

Tabu search uses a function-based API:

```python
from jssp.solvers.tabu import n2_block_boundary, tabu_search

result = tabu_search(
    instance,
    neighbourhood=n2_block_boundary,
    maxiter=1000,
    maxt=8,
    seed=42,
)
print(result.makespan)
```

The tabu implementation also provides `n1_adjacent_swaps` as an alternative
neighborhood.

## Problem instances

Instances are JSON documents under `instances/`. The loader expects:

- `jobs` and `machines` counts;
- a known `solution` makespan;
- an `operations` array with zero-based `job`, `step`, and `machine` values,
    plus a positive `duration`.

Operation order is determined by `step`. The current internal representation
stores one duration per job and machine, matching the standard JSSP instances
included in this repository.

Included data sets are:

- three small generated examples in `instances/generated/easy/`;
- the Fisher-Thompson `ft06` benchmark in `instances/benchmarks/ft/`.

## Experiments

`Experiment` runs a solver factory repeatedly for every instance in a YAML
configuration. The included configuration sets repetition count, timeout, and
input paths:

```python
from functools import partial

from jssp.experiments.experiments import Experiment
from jssp.solvers.astar import AStarSolver

solver_factory = partial(AStarSolver, heuristic="h2")
experiment = Experiment(
    "experiments/configs/basic_experiment.yaml",
    solver_factory,
)
experiment.run_experiment()

print(experiment.results)
```

The experiment runner currently targets solvers that provide
`schedule_response` and `min_time` attributes. See
`notebooks/example_experiment.ipynb` for DFS, A*, CSP, tabu-search, experiment,
and plotting examples.

## Tests

Run the automated tests with:

```bash
uv run pytest
```

The current test suite covers the A* and CSP solvers against the known optimum
for `example1.json`.

## Repository layout

```text
.
├── experiments/
│   └── configs/                 # YAML experiment definitions
├── instances/
│   ├── benchmarks/ft/          # Fisher-Thompson benchmark data
│   └── generated/easy/         # Small generated examples
├── notebooks/
│   └── example_experiment.ipynb
├── pre-analysis/                # Requirements and research notes
├── src/jssp/
│   ├── core/                    # Models, loaders, plots, validation
│   ├── experiments/             # Experiment orchestration
│   └── solvers/                 # DFS, A*, CSP, and tabu search
├── tests/                       # Automated solver tests
├── pyproject.toml               # Package metadata and dependencies
└── uv.lock                      # Locked dependency versions
```

`main.py` is currently a minimal project scaffold. Use the package APIs or the
example notebook for solver execution.

## License

This project is licensed under the GNU General Public License v3.0. See
`LICENSE` for the full terms.

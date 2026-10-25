# Job Shop Scheduling Problem (JSSP)

This repository is a Python research project for the Job Shop Scheduling
Problem (JSSP). Given jobs with ordered operations and shared machines, the
solvers build feasible schedules that minimize the makespan.

The project includes four solver implementations, JSON problem instances,
YAML-driven experiments and benchmarks, multiprocessing timeouts, metrics,
plots, and example notebooks.

## Solvers

The solver constructors are:

```python
AStarSolver(jsp_instance, hyperparameters)
DFSSolver(jsp_instance, hyperparameters)
CSPSolver(jsp_instance, hyperparameters)
TabuSolver(jsp_instance, seed, hyperparameters)
```

Tabu search uses the seed when generating its
initial solution. The experiment runner inspects each constructor and only
passes a seed when the solver accepts one.

The implemented solvers are:

- `DFSSolver`: exhaustive recursive depth-first search;
- `AStarSolver`: A* search with the `h1` or `h2` heuristic;
- `CSPSolver`: constraint search with optional MRV and LCV;
- `TabuSolver`: tabu search with the `n1` or `n2` neighbourhood.

`solve()` returns `None`. After it finishes, each solver exposes
`schedule_response` and `min_time`. Schedules are grouped by machine and
contain `(job_id, start_time, end_time)` tuples. Each solver also populates a
`SolverResult` in `result`.

The solver-level instrumentation attributes are `expanded_nodes` and
`max_frontier`. Both are `None` after construction, reset on every `solve()`
call, and populated with integers after a successful run. Their meanings are
specific to each search strategy:

| Solver | `expanded_nodes` | `max_frontier` |
| --- | --- | --- |
| A* | States removed from the priority queue | Largest priority queue |
| DFS | Recursive schedule states visited | Largest pending DFS frontier |
| CSP | Backtracking states across makespan bounds | Largest pending value frontier |
| Tabu | Schedule evaluations | Largest generated neighbourhood |

Supported hyperparameters and their defaults are:

- A*: `heuristic` set to `h1` or `h2` (default: `h2`);
- CSP: `use_mrv` and `use_lcv` booleans (both default to `True`);
- tabu search: `neighbourhood` (default: `n1`), `maxiter` (default: `1000`),
    and `maxt` (default: `8`).

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

`uv` creates `.venv` and installs the local `jssp` package. The commands below
use `uv run`, so activating the environment is optional.

## Quick start

Run A* with the `h2` heuristic on the included three-job instance:

```bash
uv run python - <<'PY'
from jssp.core.utils import read_problem_instance
from jssp.solvers.astar import AStarSolver

instance = read_problem_instance(
    "instances/generated/simple/example1.json"
)
solver = AStarSolver(
    instance,
    hyperparameters={"heuristic": "h2"},
)
solver.solve()

print(f"Makespan: {solver.min_time}")
print(f"Schedule: {solver.schedule_response}")
PY
```

The expected makespan is `9`.

Construct the other solvers as follows:

```python
from jssp.solvers.csp import CSPSolver
from jssp.solvers.recursive import DFSSolver
from jssp.solvers.tabu import TabuSolver

dfs = DFSSolver(instance, hyperparameters={})
csp = CSPSolver(
    instance,
    hyperparameters={"use_mrv": True, "use_lcv": True},
)
tabu = TabuSolver(
    instance,
    seed=42,
    hyperparameters={
        "neighbourhood": "n2",
        "maxiter": 1000,
        "maxt": 8,
    },
)
```

## Problem instances

Instances are JSON documents under `instances/`. The loader accesses these
required fields:

- `jobs` and `machines` counts;
- a known `solution` makespan;
- an `operations` array containing `job`, `step`, `machine`, and `duration`
    values.

The loader does not perform explicit schema or range validation. The included
instances use zero-based job, step, and machine values and positive durations.
Operation order is determined by `step`. The internal representation stores
one duration per job and machine, so it assumes that a job visits each machine
at most once. This matches the instances in the repository.

The included data is organized as follows:

- `instances/generated/simple/`: three small generated instances;
- `instances/benchmarks/toy/`: FT and LA benchmark instances;
- `instances/benchmarks/easy/`: ABZ, LA, SWV, and Taillard instances;
- `instances/benchmarks/medium/`: larger ABZ, SWV, and Taillard instances;
- `instances/benchmarks/hard/`: the largest included Taillard instances.

## Experiments and benchmarks

`Experiment` runs one solver configuration. `Benchmark` creates one
experiment per configured solver, enforces per-run timeouts in child
processes, aggregates results, and writes reports.

Instance paths are resolved relative to the YAML file. The benchmark `output`
path is resolved relative to the directory where the command is run.

For example, save the following as
`experiments/configs/local_benchmark.yaml`:

```yaml
benchmark:
  n_repeats: 1
  max_time: 60
  instances:
    - "../../instances/generated/simple/example1.json"
  output: "outputs"
  solvers:
    - name: "AStar - H2"
      type: AStarSolver
      hyperparameters:
        heuristic: "h2"
  seeds: [42]
```

The `seeds` list must contain at least `n_repeats` entries because repeat `i`
uses `seeds[i]`.

Run it from the repository root:

```bash
uv run python -m jssp.experiments.run_benchmark \
  --config experiments/configs/local_benchmark.yaml
```

The benchmark writer creates a subdirectory named after the configuration
file and produces:

- `metrics_summary.json`;
- `metrics_summary.csv`;
- `success_rate_comparison.png`;
- `execution_time_comparison.png`.

Committed reports are available under `outputs/` for the toy, easy, medium,
and hard instance sets. The example
and final YAML files are under `experiments/configs/`.

`run.sh` installs the project in editable mode and starts the final toy
benchmark. It changes to the repository root before resolving the relative
paths in the final configuration:

```bash
./run.sh
```

By default, the benchmark uses the `max_time` value from its YAML
configuration. Override it for each solver run, or disable the timeout:

```bash
./run.sh --max-time 120
./run.sh --max-time none
```

Run solver experiments concurrently to reduce total wall-clock time.
Parallelism is opt-in so timing remains comparable by default:

```bash
./run.sh --workers 4
./run.sh --workers max
```

A positive integer limits concurrent solver experiments. `max` uses the
available logical CPUs, capped by the number of configured solvers. Concurrent
runs compete for CPU and memory, so individual runtime measurements may be
higher even when the overall benchmark finishes sooner.

Select one or more instance sets, or run all sets:

```bash
./run.sh --instances easy
./run.sh --instances toy medium
./run.sh --instances all
```

## Tests

Run the test suite with:

```bash
uv run pytest
```

The checked-in tests cover A* and CSP solutions, metric initialization and
reset behavior for all four solvers, experiment-worker metric collection, and
the tabu neighbourhood labels in every benchmark configuration.

## Repository layout

```text
.
├── experiments/
│   └── configs/
│       ├── examples/            # Example experiment and benchmark YAML
│       └── final/               # Final benchmark YAML files
├── instances/
│   ├── benchmarks/
│   │   ├── toy/
│   │   ├── easy/
│   │   ├── medium/
│   │   └── hard/
│   └── generated/simple/        # Small generated examples
├── notebooks/
│   ├── example_benchmark.ipynb
│   ├── example_experiment.ipynb
│   └── test_solvers.ipynb
├── outputs/                      # Committed benchmark reports and plots
├── pre-analysis/                 # Requirements and research notes
├── src/jssp/
│   ├── core/                     # Models, loaders, plots, validation
│   ├── experiments/              # Experiment and benchmark runners
│   └── solvers/                  # DFS, A*, CSP, and tabu search
├── tests/                        # Solver regression tests
├── run.sh                        # Toy benchmark entry point
├── pyproject.toml                # Package metadata and dependencies
└── uv.lock                       # Locked dependency versions
```

`main.py` remains a minimal project scaffold. Use the package APIs, benchmark
entry point, or notebooks for solver execution.

## License

This project is licensed under the GNU General Public License v3.0. See
`LICENSE` for the full terms.

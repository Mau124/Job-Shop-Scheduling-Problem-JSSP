# Job-Shop-Scheduling-Problem-JSP-
Repository to solve the Job Shop Scheduling Problem

### How to run
Using [UV](https://docs.astral.sh/uv/pip/environments/)
- source .venv/bin/activate
- uv install
- python _module_

### Repository structure
```text
jssp/
│
├── README.md
├── main.py
├── .venv
├── .python-version
├── pyproject.toml
├── LICENSE
│
├── pre-analysis/...
|
├── src/
│   └── jsp/
│       ├── __init__.py
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── models.py
│       │   ├── validator.py
│       │   └── utils.py
│       │
│       ├── instances/
│       │   ├── __init__.py
│       │   ├── generator.py
│       │   └── parser.py
│       │
│       ├── solvers/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── dfs.py
│       │   ├── astar.py
│       │   ├── local_search.py
│       │   └── csp.py
│       │
│       └── experiments/
│           ├── __init__.py
│           ├── runner.py
│           ├── metrics.py
│           └── report.py
│
├── instances/
│   ├── generated/
│   │   ├── easy/
│   │   ├── medium/
│   │   └── hard/
│   │
│   ├── benchmarks/
│   │   ├── ft/
│   │   ├── la/
│   │   └── ta/
│   │
│   └── tiny/
│
├── tests/
│   ├── test_models.py
│   ├── test_validator.py
│   ├── test_generator.py
│   ├── test_parser.py
│   ├── test_dfs.py
│   ├── test_astar.py
│   ├── test_local_search.py
│   └── test_csp.py
│
├── experiments/
│   ├── configs/
│   ├── raw_results/
│   └── processed_results/
│
├── notebooks/
│   └── analysis.ipynb
│
└── report/
    ├── figures/
    ├── tables/
    └── final_report.md
```

### Folders intention
```text
core/
    What is a JSP?

instances/
    Where do JSP problems come from?

solvers/
    How do we solve them?

experiments/
    How do we measure the solvers?

tests/
    How do we know everything works?
```

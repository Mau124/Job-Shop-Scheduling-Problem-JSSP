
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from jssp.core.utils import read_exp_config_file, read_benchmark_config_file
from jssp.core.models import JSP, BenchmarkConfig, ExperimentConfig, SolverResult, Solver, ExperimentResult
from jssp.solvers.recursive import DFSSolver
from jssp.solvers.astar import AStarSolver
from jssp.solvers.tabu import TabuSolver
from jssp.solvers.csp import CSPSolver
from collections import defaultdict 
from tqdm import tqdm
import time

class Experiment:

    def __init__(self, exp_config: ExperimentConfig):
        self.exp_config = exp_config

        self.algo_name = self.exp_config.solver.name
        self.algo_type = self.exp_config.solver.solver

        if self.algo_type == 'DFSSolver':
            self.algo = DFSSolver
        elif self.algo_type == 'AStarSolver':
            self.algo = AStarSolver
        elif self.algo_type == 'TabuSolver':
            self.algo = TabuSolver
        elif self.algo_type == 'CSPSolver':
            self.algo = CSPSolver
        else:
            raise ValueError(f'Solver not found')

        self.algo_hyperparameters = self.exp_config.solver.hyperparameters

        self.seeds = self.exp_config.seeds
        self.results = defaultdict(list)

    def get_metrics(self):
        # To implement
        pass

    def run_experiment(self):
        if self.algo is None:
            raise ValueError("Parameter 'algo' must not be None")

        total_tasks = len(self.exp_config.instances) * self.exp_config.n_repeats

        with tqdm(total=total_tasks, desc="Running Task", leave=False) as pbar:
            for instance in self.exp_config.instances:
                for i in range(self.exp_config.n_repeats):
                    processor = self.algo(instance, self.seeds[i], self.algo_hyperparameters)

                    start_time = time.perf_counter()

                    with ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(processor.solve)

                        try:
                            future.result(timeout=self.exp_config.max_time)
                            elapsed_time = time.perf_counter() - start_time
                        except TimeoutError:
                            tqdm.write('Task took too much time')
                            elapsed_time = time.perf_counter() - start_time

                        self.results[instance.name].append(
                            ExperimentResult(
                                SolverResult(
                                    processor.schedule_response,
                                    processor.min_time
                                ),
                                elapsed_time,
                                None,
                                processor.schedule_response is not None,
                                None,
                                None,
                                abs(processor.min_time - instance.known_solution)
                            )
                        )
                    pbar.update(1)

    @classmethod
    def from_yaml(cls, yaml_path: str):
        experiment_config = read_exp_config_file(yaml_path)
        return cls(experiment_config)

class Benchmark:
    # This class should be used to compare different experiments using different solvers

    def __init__(self, bench_config: BenchmarkConfig):
        self.solvers = bench_config.solvers
        self.seeds = bench_config.seeds
        self.n_repeats = bench_config.n_repeats
        self.max_time = bench_config.max_time
        self.instances = bench_config.instances

        self.experiments = []

        for solver_conf in self.solvers:
            exp_config = ExperimentConfig(
                n_repeats = self.n_repeats,
                max_time = self.max_time,
                instances = self.instances,
                seeds = self.seeds,
                solver = solver_conf
            )
            self.experiments.append(Experiment(exp_config))

    def run_benchmarks(self):
        for experiment in tqdm(self.experiments, desc="Total Benchmarks", leave=True):
            tqdm.write(f'=== Running Experiment with algo: {experiment.algo_name} ===')
            experiment.run_experiment()

    def get_comparissons(self):
        # ToDO: This method should call the get metrics of each experiment to
        # compare
        for experiment in self.experiments:
            metrics = experiment.get_metrics()\

    @classmethod
    def from_yaml(cls, yaml_path: str):
        benchmark_config = read_benchmark_config_file(yaml_path)
        return cls(benchmark_config)

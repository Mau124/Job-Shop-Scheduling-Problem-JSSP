
from concurrent.futures import ThreadPoolExecutor, as_completed
from jssp.core.utils import read_exp_config_file, read_benchmark_config_file
from jssp.core.models import JSP, BenchmarkConfig, ExperimentConfig, SolverResult, Solver, ExperimentResult
from jssp.solvers.recursive import DFSSolver
from jssp.solvers.astar import AStarSolver
from jssp.solvers.tabu import TabuSolver
from jssp.solvers.csp import CSPSolver
from collections import defaultdict 
from tqdm import tqdm
import time
import multiprocessing
import statistics
import json
import csv
import inspect
from pathlib import Path
import matplotlib.pyplot as plt

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
        metrics_summary = {}

        for instance_name, results in self.results.items():
            if not results:
                continue

            total_runs = len(results)
            successful_runs = [r for r in results if r.success]
            num_successes = len(successful_runs)
            success_rate = num_successes / total_runs

            def get_stats(values):
                if not values:
                    return {'mean': None, 'variance': None, 'std': None}
                
                mean_val = statistics.mean(values)
                variance_val = statistics.variance(values) if len(values) > 1 else 0.0
                std_val = statistics.stdev(values) if len(values) > 1 else 0.0
                
                return {
                    'mean': mean_val, 
                    'variance': variance_val, 
                    'std': std_val
                }

            elapsed_times = [r.runtime for r in results if r.runtime is not None]

            min_times = [
                r.solver_result.makespan
                for r in successful_runs
                if r.solver_result and r.solver_result.makespan is not None
            ]
            
            expanded_nodes = [r.expanded_nodes for r in successful_runs if r.expanded_nodes is not None]
            max_frontiers = [r.max_frontier for r in successful_runs if r.max_frontier is not None]
            
            errors = [r.error for r in successful_runs if hasattr(r, 'error') and r.error is not None]

            metrics_summary[instance_name] = {
                'total_runs': total_runs,
                'successful_runs': num_successes,
                'success_rate': success_rate,
                'elapsed_time': get_stats(elapsed_times),
                'min_time': get_stats(min_times),
                'expanded_nodes': get_stats(expanded_nodes),
                'max_frontier': get_stats(max_frontiers),
                'error': get_stats(errors)
            }

        return metrics_summary

    def _worker_target(self, algo_class, instance, seed, hyperparameters, return_dict):
        """Target function executed in a separate process."""
        try:
            parameters = inspect.signature(algo_class).parameters
            solver_arguments = {
                'jsp_instance': instance,
                'hyperparameters': hyperparameters,
            }
            if 'seed' in parameters:
                solver_arguments['seed'] = seed

            processor = algo_class(**solver_arguments)
            processor.solve()
            return_dict['schedule_response'] = processor.schedule_response
            return_dict['min_time'] = processor.min_time
            return_dict['success'] = True
            return_dict['expanded_nodes'] = processor.expanded_nodes
            return_dict['max_frontier'] = processor.max_frontier
        except Exception as e:
            return_dict['error'] = str(e)
            return_dict['success'] = False

    def run_experiment(self):
        if self.algo is None:
            raise ValueError("Parameter 'algo' must not be None")

        total_tasks = len(self.exp_config.instances) * self.exp_config.n_repeats

        with tqdm(total=total_tasks, desc='Running Task', leave=False) as pbar:
            for instance in self.exp_config.instances:
                for i in range(self.exp_config.n_repeats):
                    
                    start_time = time.perf_counter()
                    success = False
                    schedule_response = None
                    min_time = None
                    expanded_nodes = None
                    max_frontier = None

                    manager = multiprocessing.Manager()
                    return_dict = manager.dict()

                    p = multiprocessing.Process(
                        target=self._worker_target,
                        args=(self.algo, instance, self.seeds[i], self.algo_hyperparameters, return_dict)
                    )
                    
                    p.start()
                    
                    p.join(timeout=self.exp_config.max_time)
                    
                    elapsed_time = time.perf_counter() - start_time

                    if p.is_alive():
                        tqdm.write(f'Task took too much time (Timeout: {self.exp_config.max_time}s)')
                        p.terminate()
                        p.join()
                    else:
                        if return_dict.get('success', False):
                            success = True
                            schedule_response = return_dict.get('schedule_response')
                            min_time = return_dict.get('min_time')
                            expanded_nodes = return_dict.get('expanded_nodes')
                            max_frontier = return_dict.get('max_frontier')

                    self.results[instance.name].append(
                        ExperimentResult(
                            SolverResult(
                                schedule=schedule_response,
                                makespan=min_time,
                            ),
                            elapsed_time,
                            None,
                            success,
                            expanded_nodes,
                            max_frontier,
                            abs(min_time - instance.known_solution) if min_time is not None else None
                        )
                    )
                    pbar.update(1)
                
                tqdm.write(f'Task {instance.name} processed')

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
        self.output_path = bench_config.output_path
        self.benchmark_name = bench_config.name

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

    @staticmethod
    def _run_experiment(experiment):
        tqdm.write(f'=== Running Experiment with algo: {experiment.algo_name} ===')
        experiment.run_experiment()

    def run_benchmarks(self, max_workers: int = 1):
        if max_workers <= 0:
            raise ValueError('max_workers must be greater than zero')

        start_time = time.perf_counter()

        worker_count = min(max_workers, max(len(self.experiments), 1))
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = [
                executor.submit(self._run_experiment, experiment)
                for experiment in self.experiments
            ]
            for future in tqdm(
                as_completed(futures),
                total=len(futures),
                desc="Total Benchmarks",
                leave=True,
            ):
                future.result()

        total_elapsed_time = time.perf_counter() - start_time

        tqdm.write(f'\n All benchmarks completed in {total_elapsed_time:.2f} seconds.')

        self.write_results()

    def write_results(self):
        target_dir = Path(self.output_path) / Path(self.benchmark_name)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        comparisons = self.get_comparisons()

        json_file = target_dir / 'metrics_summary.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(comparisons, f, indent=4)
        tqdm.write(f'Saved JSON report to: {json_file}')

        csv_file = target_dir / 'metrics_summary.csv'
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'instance', 'algorithm', 'total_runs', 'successful_runs', 
                'success_rate', 'mean_time', 'std_time', 'mean_error', 'std_error'
            ])
            
            for instance_name, algos in comparisons.items():
                for algo_name, metrics in algos.items():
                    writer.writerow([
                        instance_name,
                        algo_name,
                        metrics.get('total_runs'),
                        metrics.get('successful_runs'),
                        metrics.get('success_rate'),
                        metrics.get('elapsed_time', {}).get('mean'),
                        metrics.get('elapsed_time', {}).get('std'),
                        metrics.get('error', {}).get('mean'),
                        metrics.get('error', {}).get('std')
                    ])
        tqdm.write(f'Saved CSV report to: {csv_file}')

        self._generate_plots(comparisons, target_dir)

    def _generate_plots(self, comparisons, target_dir: Path):
        instances = list(comparisons.keys())
        if not instances:
            return

        algos = sorted(list({algo for inst in comparisons.values() for algo in inst.keys()}))
        
        success_rates = {algo: [] for algo in algos}
        mean_times = {algo: [] for algo in algos}

        for inst in instances:
            for algo in algos:
                algo_metrics = comparisons[inst].get(algo, {})
                success_rates[algo].append(algo_metrics.get('success_rate', 0.0) * 100)
                
                t_mean = algo_metrics.get('elapsed_time', {}).get('mean')
                mean_times[algo].append(t_mean if t_mean is not None else 0.0)

        plt.figure(figsize=(10, 5))
        x = range(len(instances))
        width = 0.8 / max(len(algos), 1)

        for i, algo in enumerate(algos):
            offset = (i - len(algos) / 2 + 0.5) * width
            plt.bar([pos + offset for pos in x], success_rates[algo], width, label=algo)

        # Plot 1
        plt.xlabel('Problem Instances')
        plt.ylabel('Success Rate (%)')
        plt.title(f'Algorithm Success Rate Comparison - {self.benchmark_name}')
        plt.xticks(list(x), instances, rotation=30, ha='right')
        plt.ylim(0, 105)
        plt.legend()
        plt.tight_layout()
        
        success_plot_path = target_dir / 'success_rate_comparison.png'
        plt.savefig(success_plot_path, dpi=300)
        plt.close()
        tqdm.write(f'Saved success rate plot to: {success_plot_path}')

        # Plot 2
        plt.figure(figsize=(10, 5))
        for i, algo in enumerate(algos):
            offset = (i - len(algos) / 2 + 0.5) * width
            plt.bar([pos + offset for pos in x], mean_times[algo], width, label=algo)

        plt.xlabel('Problem Instances')
        plt.ylabel('Mean Execution Time (s)')
        plt.title(f'Algorithm Execution Time Comparison - {self.benchmark_name}')
        plt.xticks(list(x), instances, rotation=30, ha='right')
        plt.legend()
        plt.tight_layout()
        
        time_plot_path = target_dir / 'execution_time_comparison.png'
        plt.savefig(time_plot_path, dpi=300)
        plt.close()
        tqdm.write(f'Saved execution time plot to: {time_plot_path}')

    def get_comparisons(self):
        comparisons = {}

        for experiment in self.experiments:
            algo_name = experiment.algo_name
            experiment_metrics = experiment.get_metrics()

            for instance_name, metrics in experiment_metrics.items():
                if instance_name not in comparisons:
                    comparisons[instance_name] = {}
                
                comparisons[instance_name][algo_name] = metrics

        return comparisons

    def print_comparison_summary(self):
        comparisons = self.get_comparisons()
        
        print('\n' + '='*60)
        print('BENCHMARK COMPARISON SUMMARY')
        print('='*60)

        for instance_name, algos in comparisons.items():
            print(f'\nInstance: {instance_name}')
            print('-' * 40)
            
            for algo_name, metrics in algos.items():
                success_rate = metrics.get('success_rate', 0.0) * 100
                mean_time = metrics.get('elapsed_time', {}).get("mean")
                mean_time_str = f'{mean_time:.4f}s' if mean_time is not None else 'N/A'
                
                mean_error = metrics.get('error', {}).get('mean')
                mean_error_str = f"{mean_error:.4f}" if mean_error is not None else 'N/A'

                print(f'  [{algo_name}]')
                print(f'    - Success Rate: {success_rate:.1f}% ({metrics.get('successful_runs')}/{metrics.get('total_runs')} runs)')
                print(f'    - Avg Time:     {mean_time_str}')
                print(f'    - Avg Error:    {mean_error_str}')
                
        print('='*60)

    @classmethod
    def from_yaml(cls, yaml_path: str):
        benchmark_config = read_benchmark_config_file(yaml_path)
        return cls(benchmark_config)

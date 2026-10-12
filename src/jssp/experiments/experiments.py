
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from jssp.core.utils import read_config_file
from jssp.core.models import ExperimentConfig, SolverResult
from jssp.solvers.recursive import RecursiveSolver
from collections import defaultdict 
from tqdm import tqdm
import time

class Experiment:

    def __init__(self, config_path, algo):
        self.algo = algo
        self.config = read_config_file(config_path)
        self.results = defaultdict(list)

    def get_metrics(self):
        # To implement
        pass

    def run_experiment(self):
        if self.algo is None:
            raise ValueError("Parameter 'algo' must not be None")

        total_tasks = len(self.config.instances) * self.config.n_repeats

        with tqdm(total=total_tasks, desc="Running Experiments") as pbar:
            for instance in self.config.instances:

                for i in range(self.config.n_repeats):
                    processor = self.algo(instance)

                    start_time = time.perf_counter()

                    with ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(processor.solve)

                        try:
                            future.result(timeout=self.config.max_time)
                            elapsed_time = time.perf_counter() - start_time
                        except TimeoutError:
                            print('Task took too much time')
                            elapsed_time = time.perf_counter() - start_time

                        self.results[instance.name].append(
                            SolverResult(
                                processor.schedule_response,
                                processor.min_time,
                                elapsed_time,
                                None,
                                processor.schedule_response is not None,
                                None,
                                None,
                                abs(processor.min_time - instance.known_solution)
                            )
                        )
                    pbar.update(1)

class Benchmark:
    # This class should be used to compare different experiments using different solvers

    def __init__(self, config_path: str, solvers: list[RecursiveSolver]):
        self.experiments = [Experiment(config_path, solver) for solver in solvers]

    def run_benchmarks(self):
        for experiment in self.experiments:
            experiment.run_experiment()

    def get_comparissons(self):
        # ToDO: This method should call the get metrics of each experiment to
        # compare
        for experiment in self.experiments:
            metrics = experiment.get_metrics()
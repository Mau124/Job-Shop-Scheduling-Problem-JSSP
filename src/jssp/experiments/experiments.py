
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from jssp.core.utils import read_config_file
from jssp.core.models import ExperimentConfig
from collections import defaultdict 
from tqdm import tqdm

class Experiment:

    def __init__(self, config_path, algo):
        self.algo = algo
        self.config = read_config_file(config_path)
        self.results = defaultdict(list)

    def run_experiment(self):
        if self.algo is None:
            raise ValueError("Parameter 'algo' must not be None")

        total_tasks = len(self.config.instances) * self.config.n_repeats

        with tqdm(total=total_tasks, desc="Running Experiments") as pbar:
            for instance in self.config.instances:

                for i in range(self.config.n_repeats):
                    processor = self.algo(instance)

                    with ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(processor.solve)

                        try:
                            future.result(timeout=self.config.max_time)
                        except TimeoutError:
                            print('Task took too much time')

                        self.results[str(instance)].append(processor.min_time)
                    pbar.update(1)
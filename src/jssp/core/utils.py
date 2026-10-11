import json
import yaml
from pathlib import Path

from jssp.core.models import ExperimentConfig, JSP

def read_config_file(file_path):
    path = Path(file_path)

    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    exp_data = data.get('experiment', {})

    return ExperimentConfig(
        int(exp_data.get('n_repeats', 1)),
        int(exp_data.get('max_time', 0)),
        [read_problem_instance(str(instance)) for instance in exp_data.get('instances', [])]
    )


def read_problem_instance(filename):

    with open(filename, 'r') as f:
        data = json.load(f)

    num_jobs = data['jobs']
    num_machines = data['machines']

    ops = [[0] * num_machines for _ in range(num_jobs)]
    dur = [[0] * num_machines for _ in range(num_jobs)]
    max_ops = [0 for _ in range(num_jobs)]

    total_operations = 0

    for op in data['operations']:
        job = op['job']
        step = op['step']
        machine = op['machine']
        duration = op['duration']

        ops[job][step] = machine
        dur[job][machine] = duration

        max_ops[job] += 1
        total_operations += 1

    return JSP(num_jobs, num_machines, total_operations, max_ops, ops, dur)
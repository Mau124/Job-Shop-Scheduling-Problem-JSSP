import json
import yaml
from pathlib import Path
import matplotlib.pyplot as plt

from jssp.core.models import ExperimentConfig, JSP

def read_config_file(file_path):
    path = Path(file_path)

    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    exp_data = data.get('experiment', {})

    return ExperimentConfig(
        int(exp_data.get('n_repeats', 1)),
        int(exp_data.get('max_time', 0)),
        [read_problem_instance(path.parent / Path(instance))
         for instance in exp_data.get('instances', [])]
    )


def read_problem_instance(filename):

    name = Path(filename).stem

    with open(filename, 'r') as f:
        data = json.load(f)

    known_solution = data['solution']
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

    return JSP(name, known_solution, num_jobs, num_machines, total_operations, max_ops, ops, dur)

def plot_jssp_schedule(schedule):
    """
    Plots a Gantt chart for a JSSP schedule.
    schedule format: [[(job_id, start, end), ...], [(job_id, start, end), ...]]
    where each outer list represents a machine.
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    
    colors = plt.cm.tab10.colors

    plotted_jobs = set()

    for machine_idx, machine_ops in enumerate(schedule):
        machine_name = f"Machine {machine_idx}"
        
        for job_id, start_time, end_time in machine_ops:
            duration = end_time - start_time
            color = colors[job_id % len(colors)]
            
            label = f"Job {job_id}" if job_id not in plotted_jobs else ""
            plotted_jobs.add(job_id)

            ax.barh(
                y=machine_name,
                width=duration,
                left=start_time,
                color=color,
                edgecolor='black',
                height=0.5,
                alpha=0.85,
                label=label
            )
            
            ax.text(
                start_time + (duration / 2),
                machine_name,
                f"J{job_id}\n({start_time}-{end_time})",
                ha='center',
                va='center',
                color='white',
                fontsize=9,
                fontweight='bold'
            )

    ax.set_xlabel("Time", fontsize=12, fontweight='bold')
    ax.set_ylabel("Machines", fontsize=12, fontweight='bold')
    ax.set_title("Job Shop Schedule (Gantt Chart)", fontsize=14, fontweight='bold')
    
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    
    ax.legend(title="Jobs", bbox_to_anchor=(1.02, 1), loc='upper left')
    
    plt.tight_layout()
    plt.show()

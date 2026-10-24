import argparse

from jssp.core.utils import read_benchmark_config_file
from jssp.experiments.experiments import Benchmark


def parse_max_time(value: str) -> int | None:
    if value.lower() == 'none':
        return None

    try:
        max_time = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            'max time must be a positive integer or "none"'
        ) from error

    if max_time <= 0:
        raise argparse.ArgumentTypeError(
            'max time must be greater than zero or "none"'
        )

    return max_time


def parse_arguments(arguments=None):
    parser = argparse.ArgumentParser(description='Run experiment benchmarks from a YAML config file.')

    parser.add_argument(
        '--config',
        type=str,
        required=True,
        help='Path to the YAML configuration file (e.g., config.yaml)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging.'
    )

    parser.add_argument(
        '--max-time',
        type=parse_max_time,
        default=argparse.SUPPRESS,
        metavar='SECONDS',
        help='Override the configured timeout with a positive number of seconds; use "none" for no timeout.'
    )

    return parser.parse_args(arguments)


def create_benchmark(args):
    benchmark_config = read_benchmark_config_file(args.config)

    if hasattr(args, 'max_time'):
        benchmark_config.max_time = args.max_time

    return Benchmark(benchmark_config)


def main():
    args = parse_arguments()

    print(f'Loading configuration from: {args.config}')
    benchmark = create_benchmark(args)

    if args.verbose:
        print('Verbose mode enabled.')

    benchmark.run_benchmarks()
    benchmark.print_comparison_summary()


if __name__ == '__main__':
    main()

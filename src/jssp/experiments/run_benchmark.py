import argparse
import yaml

from pathlib import Path
from jssp.experiments.experiments import Benchmark

def main():
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

    args = parser.parse_args()

    print(f'Loading configuration from: {args.config}')
    benchmark = Benchmark.from_yaml(args.config)
    
    if args.verbose:
        print('Verbose mode enabled.')
        
    benchmark.run_benchmarks()
    benchmark.print_comparison_summary()

if __name__ == "__main__":
    main()
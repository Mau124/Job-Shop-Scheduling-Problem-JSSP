# TODO

* Store specific metrics in Experiment and Benchmark class. Metrics such as:
    * mean of time, result between runs
    * variance of time, result between runs
    * Values that allow us to make curves for comparisons
* Complete experiments/core/run_benchmark.py file with the following:
    * This file has the intention to run as a script in the terminal
    * You can pass any configuraiton in yaml and the script will run the benchmark
    * It will store all the results, metrics, plots, etc in the folder outputs
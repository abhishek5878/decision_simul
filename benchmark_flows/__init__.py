"""
Benchmark Flows

Canonical onboarding flow representations for Indian B2C fintech products.
"""

from benchmark_flows.benchmark_loader import (
    load_benchmark_flow,
    list_available_benchmarks,
    get_benchmark_metadata
)

from benchmark_flows.benchmark_runner import run_benchmark_simulation

from benchmark_flows.comparative_analyzer import ComparativeAnalyzer

__all__ = [
    'load_benchmark_flow',
    'list_available_benchmarks',
    'get_benchmark_metadata',
    'run_benchmark_simulation',
    'ComparativeAnalyzer'
]


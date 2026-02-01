"""
Benchmark Runner

Runs fixed personas through target product and all benchmark flows.
"""

import json
import os
from typing import Dict, List, Optional
from pathlib import Path

from sensitivity_engine.fixed_personas import generate_fixed_personas, load_fixed_personas
from sensitivity_engine.sensitivity_simulator import SensitivitySimulator, SimulationConfig
from sensitivity_engine.decision_trace_extended import SensitivityDecisionTrace
from benchmark_flows.benchmark_loader import load_benchmark_flow, list_available_benchmarks, get_benchmark_metadata


def run_benchmark_simulation(
    target_product_steps: Dict,
    target_product_name: str,
    target_intent_frame,
    benchmark_products: Optional[List[str]] = None,
    personas: Optional[List] = None,
    n_personas: int = 100,
    output_dir: str = ".",
    seed: int = 42
) -> Dict:
    """
    Run fixed personas through target product and benchmark flows.
    
    Returns:
        Dictionary with all decision traces organized by product
    """
    print("=" * 80)
    print("BENCHMARK SIMULATION")
    print("=" * 80)
    print()
    
    # 1. Generate or load fixed personas
    if personas is None:
        personas_file = os.path.join(output_dir, "fixed_personas.json")
        if os.path.exists(personas_file):
            print(f"Loading fixed personas from {personas_file}...")
            personas = load_fixed_personas(personas_file)
        else:
            print(f"Generating {n_personas} fixed personas...")
            personas = generate_fixed_personas(n_personas, seed=seed)
        
        print(f"  Loaded {len(personas)} personas")
        print()
    
    # 2. Initialize simulator
    simulator = SensitivitySimulator(None)
    
    # 3. Get benchmark products
    if benchmark_products is None:
        benchmark_products = list_available_benchmarks()
        print(f"Found {len(benchmark_products)} benchmark products: {', '.join(benchmark_products)}")
        print()
    
    # 4. Run target product
    print(f"Running target product: {target_product_name}...")
    target_config = SimulationConfig(
        experiment_id=f"target_{target_product_name}",
        product_name=target_product_name,
        seed=seed
    )
    
    # Create a dummy intent frame if not provided (for benchmark compatibility)
    if target_intent_frame is None:
        # Use a generic intent frame
        class DummyIntentFrame:
            pass
        target_intent_frame = DummyIntentFrame()
    
    target_traces = simulator.simulate_personas(
        personas, target_product_steps, target_intent_frame, target_config
    )
    print(f"  Generated {len(target_traces)} decision traces")
    print()
    
    # 5. Run benchmark products
    all_traces = {
        target_product_name: target_traces
    }
    
    benchmark_traces = {}
    
    for benchmark_product in benchmark_products:
        print(f"Running benchmark: {benchmark_product}...")
        try:
            benchmark_steps = load_benchmark_flow(benchmark_product)
            benchmark_metadata = get_benchmark_metadata(benchmark_product)
            
            benchmark_config = SimulationConfig(
                experiment_id=f"benchmark_{benchmark_product}",
                product_name=benchmark_product,
                seed=seed  # Same seed for reproducibility
            )
            
            # Use dummy intent frame for benchmarks (simplified)
            benchmark_traces_list = simulator.simulate_personas(
                personas, benchmark_steps, target_intent_frame, benchmark_config
            )
            
            benchmark_traces[benchmark_product] = {
                'traces': benchmark_traces_list,
                'metadata': benchmark_metadata
            }
            
            print(f"  Generated {len(benchmark_traces_list)} decision traces")
        except Exception as e:
            print(f"  Error: {e}")
            continue
        
        print()
    
    # 6. Create unified ledger
    unified_ledger = {
        'target_product': target_product_name,
        'benchmark_products': list(benchmark_traces.keys()),
        'n_personas': len(personas),
        'seed': seed,
        'target_traces': [t.to_dict() for t in target_traces],
        'benchmark_traces': {
            product: {
                'metadata': data['metadata'],
                'traces': [t.to_dict() for t in data['traces']]
            }
            for product, data in benchmark_traces.items()
        }
    }
    
    # Save unified ledger
    ledger_file = os.path.join(output_dir, "benchmark_decision_ledger.json")
    with open(ledger_file, 'w') as f:
        json.dump(unified_ledger, f, indent=2)
    
    print(f"✓ Saved unified ledger to {ledger_file}")
    print()
    
    print("=" * 80)
    print("BENCHMARK SIMULATION COMPLETE")
    print("=" * 80)
    
    return unified_ledger


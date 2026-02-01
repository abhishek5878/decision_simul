#!/usr/bin/env python3
"""
Run Credigo Benchmark Analysis

Runs Credigo through the benchmark pipeline and generates comparative analysis.
"""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmark_flows.benchmark_loader import load_benchmark_flow, list_available_benchmarks, get_benchmark_metadata
from benchmark_flows.benchmark_runner import run_benchmark_simulation
from benchmark_flows.comparative_analyzer import ComparativeAnalyzer
from sensitivity_engine.perturbation_engine import Perturbation, PerturbationType, PerturbationEngine
from sensitivity_engine.sensitivity_simulator import SensitivitySimulator, SimulationConfig
from sensitivity_engine.sensitivity_analyzer import SensitivityAnalyzer
from sensitivity_engine.fixed_personas import generate_fixed_personas, load_fixed_personas

# Import intent frame
from dropsim_intent_model import CREDIGO_GLOBAL_INTENT


def run_credigo_benchmark_analysis(output_dir: str = ".", n_personas: int = 100, seed: int = 42):
    """
    Run complete Credigo benchmark analysis.
    """
    print("=" * 80)
    print("CREDIGO BENCHMARK ANALYSIS")
    print("=" * 80)
    print()
    
    # Step 1: Load Credigo flow
    print("Step 1: Loading Credigo onboarding flow...")
    credigo_steps = load_benchmark_flow("credigo")
    print(f"  Loaded {len(credigo_steps)} steps")
    print()
    
    # Step 2: Run baseline benchmark simulation
    print("Step 2: Running baseline benchmark simulation...")
    print("  Products: Credigo, Zerodha, Groww, CRED")
    print()
    
    # Get benchmark products
    benchmark_products = ["zerodha", "groww", "cred"]
    
    # Generate/load fixed personas
    personas_file = os.path.join(output_dir, "fixed_personas.json")
    if os.path.exists(personas_file):
        personas = load_fixed_personas(personas_file)
    else:
        personas = generate_fixed_personas(n_personas, seed=seed)
    
    # Initialize simulator
    simulator = SensitivitySimulator(None)
    
    # Run Credigo
    print("  Running Credigo...")
    credigo_config = SimulationConfig(
        experiment_id="credigo_baseline",
        product_name="credigo",
        seed=seed
    )
    credigo_traces = simulator.simulate_personas(
        personas, credigo_steps, CREDIGO_GLOBAL_INTENT, credigo_config
    )
    print(f"    Generated {len(credigo_traces)} decision traces")
    
    # Run benchmarks
    benchmark_traces_dict = {}
    
    for benchmark_product in benchmark_products:
        print(f"  Running {benchmark_product}...")
        benchmark_steps = load_benchmark_flow(benchmark_product)
        benchmark_metadata = get_benchmark_metadata(benchmark_product)
        
        benchmark_config = SimulationConfig(
            experiment_id=f"{benchmark_product}_baseline",
            product_name=benchmark_product,
            seed=seed
        )
        
        # Use generic intent for benchmarks (simplified)
        benchmark_traces = simulator.simulate_personas(
            personas, benchmark_steps, CREDIGO_GLOBAL_INTENT, benchmark_config
        )
        
        benchmark_traces_dict[benchmark_product] = {
            'traces': benchmark_traces,
            'metadata': benchmark_metadata
        }
        
        print(f"    Generated {len(benchmark_traces)} decision traces")
    
    print()
    
    # Create unified ledger
    unified_ledger = {
        'target_product': 'credigo',
        'benchmark_products': benchmark_products,
        'n_personas': len(personas),
        'seed': seed,
        'target_traces': [t.to_dict() for t in credigo_traces],
        'benchmark_traces': {
            product: {
                'metadata': data['metadata'],
                'traces': [t.to_dict() for t in data['traces']]
            }
            for product, data in benchmark_traces_dict.items()
        }
    }
    
    # Save ledger
    ledger_file = os.path.join(output_dir, "credigo_benchmark_decision_ledger.json")
    with open(ledger_file, 'w') as f:
        json.dump(unified_ledger, f, indent=2)
    
    print(f"✓ Saved unified ledger to {ledger_file}")
    print()
    
    # Step 3: Comparative Analysis
    print("Step 3: Running comparative analysis...")
    analyzer = ComparativeAnalyzer()
    comparative_results = analyzer.analyze_benchmarks(unified_ledger)
    
    # Save comparative results
    comparison_file = os.path.join(output_dir, "credigo_comparative_analysis.json")
    with open(comparison_file, 'w') as f:
        json.dump({
            'comparisons': {
                k: {
                    'step_comparisons': {
                        sk: {
                            'step_id': v['step_id'],
                            'drop_rate_ratio': v.get('drop_rate_ratio'),
                            'force_ratios': v.get('force_ratios', {})
                        }
                        for sk, v in comp.get('step_comparisons', {}).items()
                    },
                    'overall': comp.get('overall', {}),
                    'force_dominance': comp.get('force_dominance', {}),
                    'persona_survival': comp.get('persona_survival', {})
                    if isinstance(comp.get('persona_survival'), dict) else {}
                }
                for k, comp in comparative_results.get('comparisons', {}).items()
            }
        }, f, indent=2)
    
    print(f"✓ Saved comparative analysis to {comparison_file}")
    print()
    
    # Step 4: Sensitivity Simulation (Credigo only)
    print("Step 4: Running sensitivity simulation on Credigo...")
    
    perturbations = [
        Perturbation(
            perturbation_type=PerturbationType.REDUCE_EFFORT,
            step_index=0,
            magnitude=0.1,
            experiment_id="credigo_reduce_effort_step0_10pct"
        ),
        Perturbation(
            perturbation_type=PerturbationType.REDUCE_EFFORT,
            step_index=0,
            magnitude=0.2,
            experiment_id="credigo_reduce_effort_step0_20pct"
        ),
        Perturbation(
            perturbation_type=PerturbationType.REDUCE_EFFORT,
            step_index=0,
            magnitude=0.3,
            experiment_id="credigo_reduce_effort_step0_30pct"
        ),
        Perturbation(
            perturbation_type=PerturbationType.INCREASE_VALUE_SIGNAL,
            step_index=0,
            magnitude=0.1,
            experiment_id="credigo_increase_value_step0_10pct"
        ),
        Perturbation(
            perturbation_type=PerturbationType.INCREASE_VALUE_SIGNAL,
            step_index=0,
            magnitude=0.2,
            experiment_id="credigo_increase_value_step0_20pct"
        ),
    ]
    
    perturbation_engine = PerturbationEngine()
    sensitivity_analyzer = SensitivityAnalyzer()
    
    sensitivity_results = []
    
    for pert in perturbations:
        print(f"  Perturbation: {pert.perturbation_type.value} @ step {pert.step_index} ({pert.magnitude:.0%})")
        
        # Apply perturbation
        perturbed_steps = perturbation_engine.apply_perturbation(credigo_steps, pert)
        
        # Run simulation
        pert_config = SimulationConfig(
            experiment_id=pert.experiment_id,
            product_name="credigo",
            seed=seed
        )
        perturbed_traces = simulator.simulate_personas(
            personas, perturbed_steps, CREDIGO_GLOBAL_INTENT, pert_config
        )
        
        # Compare with baseline
        pert_sensitivity = sensitivity_analyzer.compare_traces(
            credigo_traces,
            perturbed_traces,
            pert.experiment_id,
            pert.perturbation_type.value
        )
        
        sensitivity_results.append({
            'perturbation': pert.to_dict(),
            'sensitivity': pert_sensitivity.to_dict()
        })
        
        print(f"    Change rate: {pert_sensitivity.overall_decision_change_rate:.1%}")
    
    # Save sensitivity results
    sensitivity_file = os.path.join(output_dir, "credigo_sensitivity_results.json")
    with open(sensitivity_file, 'w') as f:
        json.dump(sensitivity_results, f, indent=2)
    
    print(f"✓ Saved sensitivity results to {sensitivity_file}")
    print()
    
    # Step 5: Generate founder-ready report
    print("Step 5: Generating founder-ready report...")
    from benchmark_flows.credigo_report_generator import generate_credigo_report
    
    report = generate_credigo_report(
        unified_ledger,
        comparative_results,
        sensitivity_results,
        output_dir
    )
    
    report_file = os.path.join(output_dir, "credigo_vs_benchmarks_report.md")
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"✓ Generated report: {report_file}")
    print()
    
    print("=" * 80)
    print("CREDIGO BENCHMARK ANALYSIS COMPLETE")
    print("=" * 80)
    
    return {
        'ledger': unified_ledger,
        'comparative_analysis': comparative_results,
        'sensitivity_results': sensitivity_results,
        'report_file': report_file
    }


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Credigo Benchmark Analysis')
    parser.add_argument('--output-dir', type=str, default='output',
                       help='Output directory (default: output)')
    parser.add_argument('--personas', type=int, default=100,
                       help='Number of fixed personas (default: 100)')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed (default: 42)')
    
    args = parser.parse_args()
    
    run_credigo_benchmark_analysis(
        output_dir=args.output_dir,
        n_personas=args.personas,
        seed=args.seed
    )


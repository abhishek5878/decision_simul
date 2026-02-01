#!/usr/bin/env python3
"""
Run Decision Sensitivity Analysis

Main execution script for sensitivity simulation and analysis.
"""

import json
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sensitivity_engine.fixed_personas import generate_fixed_personas, save_fixed_personas, load_fixed_personas
from sensitivity_engine.perturbation_engine import Perturbation, PerturbationType, PerturbationEngine
from sensitivity_engine.sensitivity_simulator import SensitivitySimulator, SimulationConfig
from sensitivity_engine.sensitivity_analyzer import SensitivityAnalyzer
from sensitivity_engine.sensitivity_report import SensitivityReportGenerator


def load_product_steps(product_config: str) -> dict:
    """Load product steps configuration."""
    if product_config == "trial1":
        from trial1_steps import TRIAL1_STEPS
        return TRIAL1_STEPS
    elif product_config == "credigo" or product_config == "credigo_ss":
        from credigo_ss_steps_improved import CREDIGO_SS_11_STEPS
        return CREDIGO_SS_11_STEPS
    else:
        raise ValueError(f"Unknown product config: {product_config}")


def load_intent_frame(product_config: str):
    """Load intent frame for product."""
    from dropsim_intent_model import TRIAL1_GLOBAL_INTENT, CREDIGO_GLOBAL_INTENT
    
    if product_config == "trial1":
        return TRIAL1_GLOBAL_INTENT
    elif product_config == "credigo" or product_config == "credigo_ss":
        return CREDIGO_GLOBAL_INTENT
    else:
        raise ValueError(f"Unknown product config: {product_config}")


def run_sensitivity_analysis(
    product_config: str,
    n_personas: int = 100,
    perturbations: Optional[list] = None,
    output_dir: str = "."
) -> dict:
    """
    Run complete sensitivity analysis.
    
    Returns:
        Dictionary with baseline traces, perturbed traces, and report
    """
    print("=" * 80)
    print("DECISION SENSITIVITY ANALYSIS")
    print("=" * 80)
    print(f"Product: {product_config}")
    print(f"Personas: {n_personas}")
    print()
    
    # 1. Generate or load fixed personas
    personas_file = os.path.join(output_dir, "fixed_personas.json")
    if os.path.exists(personas_file):
        print(f"Loading fixed personas from {personas_file}...")
        personas = load_fixed_personas(personas_file)
    else:
        print(f"Generating {n_personas} fixed personas...")
        personas = generate_fixed_personas(n_personas, seed=42)
        save_fixed_personas(personas, personas_file)
        print(f"✓ Saved fixed personas to {personas_file}")
    print(f"  Loaded {len(personas)} personas")
    print()
    
    # 2. Load product configuration
    print(f"Loading product configuration: {product_config}...")
    product_steps = load_product_steps(product_config)
    intent_frame = load_intent_frame(product_config)
    print(f"  Loaded {len(product_steps)} steps")
    print()
    
    # 3. Initialize simulator
    print("Initializing sensitivity simulator...")
    # Create a simple simulator module
    simulator = SensitivitySimulator(None)  # Will use internal logic
    print()
    
    # 4. Run baseline simulation
    print("Running baseline simulation...")
    baseline_config = SimulationConfig(
        experiment_id="baseline",
        product_name=product_config,
        seed=42
    )
    baseline_traces = simulator.simulate_personas(
        personas, product_steps, intent_frame, baseline_config
    )
    print(f"  Generated {len(baseline_traces)} decision traces")
    print()
    
    # Save baseline traces
    baseline_file = os.path.join(output_dir, f"{product_config}_baseline_traces.json")
    with open(baseline_file, 'w') as f:
        json.dump([t.to_dict() for t in baseline_traces], f, indent=2)
    print(f"✓ Saved baseline traces to {baseline_file}")
    print()
    
    # 5. Define perturbations (if not provided)
    if perturbations is None:
        perturbations = [
            Perturbation(
                perturbation_type=PerturbationType.REDUCE_EFFORT,
                step_index=1,
                magnitude=0.3,
                experiment_id="perturb_reduce_effort_step1"
            ),
            Perturbation(
                perturbation_type=PerturbationType.INCREASE_VALUE_SIGNAL,
                step_index=0,
                magnitude=0.3,
                experiment_id="perturb_increase_value_step0"
            ),
        ]
    
    # 6. Run perturbed simulations
    print(f"Running {len(perturbations)} perturbation experiments...")
    perturbation_engine = PerturbationEngine()
    analyzer = SensitivityAnalyzer()
    
    perturbation_results = []
    
    for i, perturbation in enumerate(perturbations):
        print(f"  [{i+1}/{len(perturbations)}] {perturbation.perturbation_type.value} @ step {perturbation.step_index}")
        
        # Apply perturbation
        perturbed_steps = perturbation_engine.apply_perturbation(
            product_steps, perturbation
        )
        
        # Run simulation
        perturbed_config = SimulationConfig(
            experiment_id=perturbation.experiment_id,
            product_name=product_config,
            seed=42  # Same seed for reproducibility
        )
        perturbed_traces = simulator.simulate_personas(
            personas, perturbed_steps, intent_frame, perturbed_config
        )
        
        # Compare with baseline
        pert_sensitivity = analyzer.compare_traces(
            baseline_traces,
            perturbed_traces,
            perturbation.experiment_id,
            perturbation.perturbation_type.value
        )
        
        perturbation_results.append(pert_sensitivity)
        
        print(f"    Change rate: {pert_sensitivity.overall_decision_change_rate:.1%}")
    
    print()
    
    # 7. Generate report
    print("Generating sensitivity report...")
    report_generator = SensitivityReportGenerator()
    report = report_generator.generate_report(
        product_name=product_config,
        baseline_experiment_id="baseline",
        perturbation_results=perturbation_results
    )
    
    # Save reports
    report_json = os.path.join(output_dir, f"{product_config}_sensitivity_report.json")
    report_md = os.path.join(output_dir, f"{product_config}_sensitivity_report.md")
    
    report_generator.save_report(report, report_json)
    report_generator.save_markdown_report(report, report_md)
    
    print(f"✓ Saved report to {report_json}")
    print(f"✓ Saved markdown report to {report_md}")
    print()
    
    print("=" * 80)
    print("SENSITIVITY ANALYSIS COMPLETE")
    print("=" * 80)
    
    return {
        'baseline_traces': [t.to_dict() for t in baseline_traces],
        'perturbation_results': [p.to_dict() for p in perturbation_results],
        'report': report.to_dict()
    }


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Decision Sensitivity Analysis')
    parser.add_argument('product', choices=['trial1', 'credigo', 'credigo_ss'],
                       help='Product configuration')
    parser.add_argument('--personas', type=int, default=100,
                       help='Number of fixed personas (default: 100)')
    parser.add_argument('--output-dir', type=str, default='.',
                       help='Output directory (default: current directory)')
    
    args = parser.parse_args()
    
    run_sensitivity_analysis(
        product_config=args.product,
        n_personas=args.personas,
        output_dir=args.output_dir
    )


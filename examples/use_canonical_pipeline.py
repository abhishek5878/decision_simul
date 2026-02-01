#!/usr/bin/env python3
"""
Example: Using the Canonical Simulation Pipeline

This demonstrates the ONLY supported way to run simulations.
"""

from simulation_pipeline import run_simulation


def main():
    print("=" * 80)
    print("CANONICAL PIPELINE EXAMPLE")
    print("=" * 80)
    
    # Example 1: Research mode (quick, no evaluation)
    print("\n1. Research Mode (quick experiment):")
    result_research = run_simulation(
        product_config="credigo",
        mode="research",
        n_personas=100,  # Smaller for speed
        seed=42,
        verbose=True
    )
    
    print(f"\nResearch Results:")
    print(f"  Entry rate: {result_research.final_metrics['entry_rate']:.2%}")
    print(f"  Completion rate: {result_research.final_metrics['completion_rate']:.2%}")
    print(f"  Total conversion: {result_research.final_metrics['total_conversion']:.2%}")
    
    # Example 2: Production mode (full pipeline)
    print("\n" + "=" * 80)
    print("2. Production Mode (full pipeline with evaluation & drift):")
    
    result_production = run_simulation(
        product_config="credigo",
        mode="production",
        n_personas=500,  # Medium for production
        seed=42,
        calibration_file="output/credigo_ss_calibration_summary.json",  # Optional
        baseline_file="output/credigo_ss_baseline.json",  # Optional
        verbose=True
    )
    
    print(f"\nProduction Results:")
    print(f"  Entry rate: {result_production.final_metrics['entry_rate']:.2%}")
    print(f"  Completion rate: {result_production.final_metrics['completion_rate']:.2%}")
    print(f"  Total conversion: {result_production.final_metrics['total_conversion']:.2%}")
    
    if result_production.drift:
        print(f"  Drift status: {result_production.drift.get('overall_status', 'unknown')}")
    
    if result_production.evaluation:
        print(f"  Evaluation: ✓ Complete")
    
    # Export results
    print("\n" + "=" * 80)
    print("3. Exporting Results:")
    result_production.export('example_simulation_result.json')
    print("   ✓ Exported to example_simulation_result.json")
    
    # Access unified output
    print("\n" + "=" * 80)
    print("4. Unified Output Structure:")
    print(f"   - Entry: {len(result_production.entry)} fields")
    print(f"   - Behavioral: {len(result_production.behavioral)} fields")
    print(f"   - Intent: {len(result_production.intent)} fields")
    print(f"   - Calibration: {'Present' if result_production.calibration else 'None'}")
    print(f"   - Evaluation: {'Present' if result_production.evaluation else 'None'}")
    print(f"   - Drift: {'Present' if result_production.drift else 'None'}")
    print(f"   - Final Metrics: {len(result_production.final_metrics)} metrics")
    print(f"   - Model Version: {result_production.model_version}")
    print("=" * 80)


if __name__ == '__main__':
    main()


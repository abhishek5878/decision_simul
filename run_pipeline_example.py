#!/usr/bin/env python3
"""
Example: Running the Canonical Simulation Pipeline

This demonstrates the correct way to use the pipeline.
"""

from simulation_pipeline import run_simulation


def main():
    print("=" * 80)
    print("CANONICAL PIPELINE EXAMPLE")
    print("=" * 80)
    
    # Run simulation in production mode
    result = run_simulation(
        product_config="credigo",
        mode="production",
        n_personas=500,  # Smaller for faster execution
        seed=42,
        calibration_file="credigo_ss_calibration_summary.json",  # Optional
        baseline_file="credigo_ss_baseline.json",  # Optional
        verbose=True
    )
    
    # Access unified results
    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print(f"Entry rate: {result.final_metrics['entry_rate']:.2%}")
    print(f"Completion rate: {result.final_metrics['completion_rate']:.2%}")
    print(f"Total conversion: {result.final_metrics['total_conversion']:.2%}")
    
    if result.drift:
        print(f"Drift status: {result.drift.get('overall_status', 'unknown')}")
    
    if result.evaluation:
        print(f"Evaluation: Complete")
    
    # Export results
    print("\n" + "=" * 80)
    print("EXPORTING RESULTS")
    print("=" * 80)
    result.export('pipeline_simulation_result.json')
    print("✓ Exported to pipeline_simulation_result.json")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()


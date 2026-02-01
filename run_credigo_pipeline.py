#!/usr/bin/env python3
"""
Run canonical pipeline for Credigo.

This runs the complete simulation pipeline with:
- Policy versioning
- Decision traces
- Context graph
- All evaluation layers
"""

import sys
from simulation_pipeline import run_simulation

def main():
    print("=" * 80)
    print("Running Credigo Simulation Pipeline")
    print("=" * 80)
    print()
    
    # Run pipeline in production mode
    result = run_simulation(
        product_config="credigo",
        mode="production",
        n_personas=1000,
        seed=42,
        verbose=True
    )
    
    # Export results
    output_file = "credigo_pipeline_result.json"
    result.export(output_file)
    print(f"\n✅ Results exported to: {output_file}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("SIMULATION SUMMARY")
    print("=" * 80)
    print(f"Entry rate: {result.final_metrics['entry_rate']:.2%}")
    print(f"Completion rate: {result.final_metrics['completion_rate']:.2%}")
    print(f"Total conversion: {result.final_metrics['total_conversion']:.2%}")
    
    if result.context_graph_summary:
        print(f"\nContext Graph:")
        print(f"  Total nodes: {result.context_graph_summary.get('total_nodes', 0)}")
        print(f"  Total edges: {result.context_graph_summary.get('total_edges', 0)}")
        print(f"  Dominant failure paths: {len(result.context_graph_summary.get('dominant_failure_paths', []))}")
    
    if result.decision_traces:
        print(f"\nDecision Traces:")
        print(f"  Total traces: {len(result.decision_traces)}")
    
    if result.drift:
        print(f"\nDrift Status: {result.drift.get('overall_status', 'unknown')}")
    
    print("=" * 80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())


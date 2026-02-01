#!/usr/bin/env python3
"""
Run original base behavioral simulation for Credigo.
Uses the original deterministic behavioral_engine.py without any improvements.
"""

import json
import numpy as np
from datetime import datetime
from collections import Counter
from behavioral_engine import run_behavioral_simulation
from credigo_ss_steps_improved import CREDIGO_SS_11_STEPS
from load_dataset import load_and_sample
from derive_features import derive_all_features

def main():
    print("\n" + "=" * 80)
    print("🧠 ORIGINAL BEHAVIORAL SIMULATION: Credigo.club")
    print("=" * 80)
    print(f"   Personas: 1000")
    print(f"   Product Steps: {len(CREDIGO_SS_11_STEPS)}")
    print(f"   Model: Base Behavioral Engine (Deterministic)")
    print("=" * 80)
    
    # Load personas
    print("\n📂 Loading dataset...")
    df, _ = load_and_sample(n=1000, seed=42, verbose=False)
    print(f"   Loaded {len(df)} personas")
    
    print("\n🔧 Deriving features...")
    df = derive_all_features(df, verbose=False)
    print(f"   Derived features")
    
    # Run original behavioral simulation
    print("\n🧠 Running original behavioral simulation...")
    result_df = run_behavioral_simulation(
        df,
        product_steps=CREDIGO_SS_11_STEPS,
        verbose=True
    )
    
    # Save results
    output_file = "output/credigo_original_results.json"
    print(f"\n💾 Saving results to {output_file}...")
    
    # Prepare summary for JSON
    total_trajectories = len(result_df) * 7  # 7 state variants per persona
    total_completed = sum(1 for _, row in result_df.iterrows() 
                         for t in row['trajectories'] if t.get('exit_step') == 'Completed')
    overall_completion = total_completed / total_trajectories if total_trajectories > 0 else 0
    
    # Convert numpy types to native Python types for JSON
    def convert_to_native(obj):
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: convert_to_native(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_native(item) for item in obj]
        return obj
    
    summary = {
        'simulation_type': 'original_behavioral_engine',
        'product': 'Credigo.club',
        'timestamp': datetime.now().isoformat(),
        'total_personas': int(len(result_df)),
        'total_trajectories': int(total_trajectories),
        'overall_completion_rate': float(overall_completion),
        'failure_reasons': convert_to_native(dict(Counter([t['failure_reason'] for _, row in result_df.iterrows() 
                                                           for t in row['trajectories'] if t.get('failure_reason')]))),
        'exit_steps': convert_to_native(dict(Counter([t['exit_step'] for _, row in result_df.iterrows() 
                                                      for t in row['trajectories']])))
    }
    
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"   ✓ Results saved to {output_file}")
    
    print("\n" + "=" * 80)
    print("✅ ORIGINAL BEHAVIORAL SIMULATION COMPLETE")
    print("=" * 80)
    print(f"\n📊 KEY METRICS:")
    print(f"   Completion Rate: {overall_completion:.1%}")
    print(f"   Results saved to: {output_file}")
    print("=" * 80 + "\n")
    
    return result_df, summary

if __name__ == "__main__":
    result_df, summary = main()


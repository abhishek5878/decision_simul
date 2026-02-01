#!/usr/bin/env python3
"""
Run intent-aware behavioral simulation for Keeper SS.
Matches ARCHITECTURE_COMPLETE.md exactly:
- Base Behavioral Engine (behavioral_engine.py)
- Improved Behavioral Engine (behavioral_engine_improved.py)
- Intent-Aware Layer (behavioral_engine_intent_aware.py)
"""

import json
import numpy as np
from datetime import datetime
from collections import Counter
from load_dataset import load_and_sample
from derive_features import derive_all_features
from behavioral_engine_intent_aware import (
    run_intent_aware_simulation,
    generate_intent_analysis,
    export_intent_artifacts
)
from dropsim_intent_model import KEEPER_SS_GLOBAL_INTENT
from keeper_ss_steps import KEEPER_SS_STEPS
import numpy as np

def convert_to_native(obj):
    """Convert numpy types to native Python types for JSON."""
    if isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_to_native(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_native(item) for item in obj]
    return obj

def main():
    print("\n" + "=" * 80)
    print("🧠 INTENT-AWARE BEHAVIORAL SIMULATION: Keeper SS")
    print("=" * 80)
    print(f"   Personas: 1000")
    print(f"   Product Steps: {len(KEEPER_SS_STEPS)}")
    print(f"   Architecture: Base → Improved → Intent-Aware")
    print("=" * 80)
    
    # Load personas
    print("\n📂 Loading dataset...")
    df, _ = load_and_sample(n=1000, seed=42, verbose=False)
    print(f"   Loaded {len(df)} personas")
    
    print("\n🔧 Deriving features...")
    df = derive_all_features(df, verbose=False)
    print(f"   Derived features")
    
    # Use fixed global intent for Keeper SS
    # All users are founders, business owners, or CEOs wanting to calculate leave liability
    print("\n🎯 Using fixed global intent for Keeper SS...")
    print(f"   Intent: {KEEPER_SS_GLOBAL_INTENT.intent_id}")
    print(f"   Description: {KEEPER_SS_GLOBAL_INTENT.description}")
    print(f"   Primary Goal: {KEEPER_SS_GLOBAL_INTENT.primary_goal}")
    print(f"   User Type: Founders, Business Owners, CEOs")
    print(f"   Note: All users share this intent (ground truth, not inferred)")
    
    # Run intent-aware simulation with fixed intent
    print("\n🧠 Running intent-aware simulation with fixed intent...")
    result_df = run_intent_aware_simulation(
        df,
        product_steps=KEEPER_SS_STEPS,
        fixed_intent=KEEPER_SS_GLOBAL_INTENT,  # Fixed intent for all users
        verbose=True,
        seed=42
    )
    
    # Generate intent analysis
    print("\n📊 Generating intent-aware analysis...")
    analysis = generate_intent_analysis(result_df, KEEPER_SS_STEPS)
    
    # Export artifacts
    print("\n💾 Exporting intent artifacts...")
    artifacts = export_intent_artifacts(result_df, KEEPER_SS_STEPS, output_dir=".")
    print(f"   ✓ Exported {len(artifacts)} artifacts")
    for name, path in artifacts.items():
        print(f"     {name}: {path}")
    
    # Calculate confidence intervals
    print("\n📊 Calculating confidence intervals...")
    completion_outcomes = [t['completed'] for _, row in result_df.iterrows() for t in row['trajectories']]
    
    # Bootstrap confidence intervals
    n_bootstrap = 1000
    bootstrap_means = []
    for _ in range(n_bootstrap):
        sample = np.random.choice(completion_outcomes, len(completion_outcomes), replace=True)
        bootstrap_means.append(np.mean(sample))
    
    mean_completion = np.mean(completion_outcomes)
    ci_lower = np.percentile(bootstrap_means, 2.5)
    ci_upper = np.percentile(bootstrap_means, 97.5)
    std_error = np.std(bootstrap_means)
    
    ci_results = {
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'std_error': std_error,
        'completion_range': f"{ci_lower:.1%} - {ci_upper:.1%}"
    }
    
    # Save comprehensive results
    output_file = "keeper_ss_intent_aware_results.json"
    print(f"\n💾 Saving comprehensive results to {output_file}...")
    
    total_trajectories = len(result_df) * 7
    total_completed = result_df['variants_completed'].sum()
    overall_completion = total_completed / total_trajectories
    total_mismatches = result_df['intent_mismatch_count'].sum()
    
    summary = {
        'simulation_type': 'intent_aware_behavioral_engine',
        'product': 'Keeper SS',
        'timestamp': datetime.now().isoformat(),
        'total_personas': int(len(result_df)),
        'total_trajectories': int(total_trajectories),
        'overall_completion_rate': float(overall_completion),
        'completion_rate_ci_lower': float(ci_results['ci_lower']),
        'completion_rate_ci_upper': float(ci_results['ci_upper']),
        'completion_rate_std_error': float(ci_results['std_error']),
        'completion_rate_range': ci_results['completion_range'],
        'confidence_level': 0.95,
        'total_intent_mismatches': int(total_mismatches),
        'fixed_intent': KEEPER_SS_GLOBAL_INTENT.to_dict(),
        'intent_profile': convert_to_native(analysis.get('intent_profile', {})),
        'failure_reasons': convert_to_native(dict(Counter([t['failure_reason'] for _, row in result_df.iterrows() 
                                                           for t in row['trajectories'] if t.get('failure_reason')]))),
        'exit_steps': convert_to_native(dict(Counter([t['exit_step'] for _, row in result_df.iterrows() 
                                                      for t in row['trajectories']])))
    }
    
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"   ✓ Results saved to {output_file}")
    
    print("\n" + "=" * 80)
    print("✅ INTENT-AWARE SIMULATION COMPLETE")
    print("=" * 80)
    print(f"\n📊 KEY METRICS:")
    print(f"   Completion Rate: {overall_completion:.1%}")
    print(f"   95% Confidence Interval: {ci_results['ci_lower']:.1%} - {ci_results['ci_upper']:.1%}")
    print(f"   Standard Error: {ci_results['std_error']:.1%}")
    print(f"   Total Intent Mismatches: {total_mismatches:,}")
    print(f"   Mismatch Rate: {total_mismatches / total_trajectories * 100:.1f}%")
    
    print(f"\n🎯 INTENT PROFILE:")
    for intent_id, prob in sorted(analysis['intent_profile'].items(), key=lambda x: x[1], reverse=True):
        print(f"   {intent_id}: {prob:.1%}")
    
    print(f"\n📁 ARTIFACTS:")
    for name, path in artifacts.items():
        print(f"   {name}: {path}")
    
    print("=" * 80 + "\n")
    
    return result_df, analysis, artifacts, summary

if __name__ == "__main__":
    result_df, analysis, artifacts, summary = main()


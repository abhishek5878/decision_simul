#!/usr/bin/env python3
import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

"""
Run persona-driven intent-aware simulation for Credigo SS.

All users share the same high-level intent: "I want good credit card recommendations"
But they differ in HOW they want to achieve it based on their persona traits:
- compare_options: Want to see options side-by-side
- quick_decision: Want fast eligibility check
- validate_choice: Want to validate a choice they have in mind
- learn_basics: Want to learn about credit cards first
- eligibility_check: Just want to check if they qualify

This demonstrates persona-driven intent inference working even with same high-level goal.
"""

import json
import numpy as np
from datetime import datetime
from collections import Counter
from behavioral_engine_intent_aware import run_intent_aware_simulation
from credigo_ss_steps_improved import CREDIGO_SS_11_STEPS
from load_dataset import load_and_sample
from derive_features import derive_all_features

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
    print("🧠 PERSONA-DRIVEN INTENT-AWARE SIMULATION: Credigo SS")
    print("=" * 80)
    print(f"   Personas: 1000")
    print(f"   Product Steps: {len(CREDIGO_SS_11_STEPS)}")
    print(f"   High-Level Intent: 'I want good credit card recommendations'")
    print(f"   Granular Intents: Differentiated by persona traits")
    print(f"   Model: Persona-Driven Intent-Aware Behavioral Engine")
    print("=" * 80)
    
    # Load personas
    print("\n📂 Loading dataset...")
    df, _ = load_and_sample(n=1000, seed=42, verbose=False)
    print(f"   Loaded {len(df)} personas")
    
    print("\n🔧 Deriving features...")
    df = derive_all_features(df, verbose=False)
    print(f"   Derived features")
    
    # Run persona-driven intent-aware simulation
    print("\n🧠 Running persona-driven intent-aware simulation...")
    print("   Note: All users want credit card recommendations, but HOW they want")
    print("   to get them differs based on their persona traits (cognitive capacity,")
    print("   risk tolerance, urgency, financial literacy, etc.)")
    
    result_df = run_intent_aware_simulation(
        df,
        product_steps=CREDIGO_SS_11_STEPS,
        intent_distribution=None,  # Will be inferred per-persona
        verbose=True,
        seed=42
    )
    
    # Analyze intent distribution across personas
    print("\n📊 Analyzing persona-specific intent distributions...")
    intent_distributions = []
    for _, row in result_df.iterrows():
        for traj in row['trajectories']:
            intent_id = traj.get('intent_id', 'unknown')
            intent_distributions.append(intent_id)
    
    intent_counts = Counter(intent_distributions)
    total = len(intent_distributions)
    
    print(f"\n   Granular Intent Distribution (from persona traits):")
    for intent_id, count in sorted(intent_counts.items(), key=lambda x: x[1], reverse=True):
        pct = count / total * 100
        print(f"     {intent_id}: {pct:.1f}% ({count:,} users)")
    
    # Save results
    output_file = "output/credigo_ss_persona_intent_results.json"
    print(f"\n💾 Saving results to {output_file}...")
    
    # Prepare summary
    total_trajectories = len(result_df) * 7
    total_completed = result_df['variants_completed'].sum()
    overall_completion = total_completed / total_trajectories
    
    # Extract intent mismatches
    total_intent_mismatches = 0
    intent_mismatch_by_type = Counter()
    
    for _, row in result_df.iterrows():
        for traj in row['trajectories']:
            intent_mismatches = traj.get('intent_mismatches', [])
            total_intent_mismatches += len(intent_mismatches)
            for mismatch in intent_mismatches:
                mismatch_type = mismatch.get('mismatch_type', 'unknown')
                intent_mismatch_by_type[mismatch_type] += 1
    
    # Aggregate by step
    step_drop_rates = {}
    step_intent_mismatches = {}
    
    for _, row in result_df.iterrows():
        for traj in row['trajectories']:
            journey = traj.get('journey', [])
            for step_data in journey:
                step_name = step_data.get('step', 'Unknown')
                if step_name not in step_drop_rates:
                    step_drop_rates[step_name] = {'drops': 0, 'continues': 0}
                    step_intent_mismatches[step_name] = []
                
                if step_data.get('continue', 'True') == 'False':
                    step_drop_rates[step_name]['drops'] += 1
                else:
                    step_drop_rates[step_name]['continues'] += 1
                
                # Check for intent mismatch at this step
                alignment = step_data.get('intent_alignment', {})
                if isinstance(alignment, dict) and alignment.get('is_intent_mismatch', False):
                    step_intent_mismatches[step_name].append({
                        'intent_id': traj.get('intent_id', 'unknown'),
                        'mismatch_type': alignment.get('mismatch_type', 'unknown')
                    })
    
    summary = {
        'simulation_type': 'persona_driven_intent_aware_behavioral_engine',
        'product': 'Credigo.club SS',
        'high_level_intent': 'I want good credit card recommendations',
        'granular_intent_differentiation': 'Based on persona behavioral traits',
        'timestamp': datetime.now().isoformat(),
        'total_personas': int(len(result_df)),
        'total_trajectories': int(total_trajectories),
        'overall_completion_rate': float(overall_completion),
        'granular_intent_distribution': convert_to_native(dict(intent_counts)),
        'total_intent_mismatches': int(total_intent_mismatches),
        'intent_mismatch_by_type': convert_to_native(dict(intent_mismatch_by_type)),
        'step_drop_rates': convert_to_native({
            step_name: {
                'drops': int(data['drops']),
                'continues': int(data['continues']),
                'drop_rate': float(data['drops'] / (data['drops'] + data['continues']) if (data['drops'] + data['continues']) > 0 else 0)
            }
            for step_name, data in step_drop_rates.items()
        }),
        'step_intent_mismatches': convert_to_native({
            step_name: {
                'total_mismatches': len(mismatches),
                'by_intent': dict(Counter(m.get('intent_id', 'unknown') for m in mismatches)),
                'by_type': dict(Counter(m.get('mismatch_type', 'unknown') for m in mismatches))
            }
            for step_name, mismatches in step_intent_mismatches.items()
        }),
        'failure_reasons': convert_to_native(dict(Counter([t['failure_reason'] for _, row in result_df.iterrows() for t in row['trajectories'] if t.get('failure_reason')]))),
        'exit_steps': convert_to_native(dict(Counter([t['exit_step'] for _, row in result_df.iterrows() for t in row['trajectories']])))
    }
    
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"   ✓ Results saved to {output_file}")
    
    print("\n" + "=" * 80)
    print("✅ PERSONA-DRIVEN INTENT-AWARE SIMULATION COMPLETE")
    print("=" * 80)
    print(f"\n📊 KEY METRICS:")
    print(f"   Completion Rate: {overall_completion:.1%}")
    print(f"   Total Intent Mismatches: {total_intent_mismatches:,}")
    print(f"   Granular Intent Distribution:")
    for intent_id, count in sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
        pct = count / total * 100
        print(f"     - {intent_id}: {pct:.1f}%")
    print(f"\n   Results saved to: {output_file}")
    print("=" * 80 + "\n")
    
    return result_df, summary

if __name__ == "__main__":
    result_df, summary = main()


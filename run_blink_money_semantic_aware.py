#!/usr/bin/env python3
"""
Run semantic-aware behavioral simulation for Blink Money.
"""

import json
import numpy as np
from datetime import datetime
from collections import Counter
from behavioral_engine_semantic_aware import run_semantic_aware_simulation
from blink_money_steps_improved import BLINK_MONEY_STEPS_IMPROVED
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
    print("🧠 SEMANTIC-AWARE BEHAVIORAL SIMULATION: Blink Money")
    print("=" * 80)
    print(f"   Personas: 1000")
    print(f"   Product Steps: {len(BLINK_MONEY_STEPS_IMPROVED)}")
    print(f"   Model: Semantic-Aware Behavioral Engine")
    print("=" * 80)
    
    # Load personas
    print("\n📂 Loading dataset...")
    df, _ = load_and_sample(n=1000, seed=42, verbose=False)
    print(f"   Loaded {len(df)} personas")
    
    print("\n🔧 Deriving features...")
    df = derive_all_features(df, verbose=False)
    print(f"   Derived features")
    
    # Run semantic-aware simulation
    print("\n🧠 Running semantic-aware simulation...")
    
    # Infer intent distribution first to include in results
    from dropsim_intent_model import infer_intent_distribution
    first_step = list(BLINK_MONEY_STEPS_IMPROVED.values())[0]
    entry_text = first_step.get('description', '')
    cta_phrasing = first_step.get('cta_phrasing', '')
    
    intent_result = infer_intent_distribution(
        entry_page_text=entry_text,
        cta_phrasing=cta_phrasing,
        product_type='fintech',
        persona_attributes={'intent': 'medium', 'urgency': 'medium'},
        product_steps=BLINK_MONEY_STEPS_IMPROVED
    )
    intent_distribution = intent_result['intent_distribution']
    
    result_df = run_semantic_aware_simulation(
        df,
        product_steps=BLINK_MONEY_STEPS_IMPROVED,
        intent_distribution=intent_distribution,
        use_llm=False,  # Use rule-based for now
        verbose=True,
        seed=42
    )
    
    # Save results
    output_file = "output/blink_money_semantic_aware_results.json"
    print(f"\n💾 Saving results to {output_file}...")
    
    # Prepare summary for JSON
    total_trajectories = len(result_df) * 7
    total_completed = result_df['variants_completed'].sum()
    overall_completion = total_completed / total_trajectories
    total_semantic_mismatches = result_df['semantic_mismatch_count'].sum()
    
    # Extract semantic profiles and alignment results from trajectories
    step_semantic_data = {}
    
    for _, row in result_df.iterrows():
        for traj in row['trajectories']:
            journey = traj.get('journey', [])
            for step_data in journey:
                step_name = step_data.get('step', 'Unknown')
                if step_name not in step_semantic_data:
                    step_semantic_data[step_name] = {
                        'semantic_profiles': [],
                        'alignment_results': [],
                        'drops': 0,
                        'continues': 0
                    }
                
                if 'semantic_profile' in step_data:
                    step_semantic_data[step_name]['semantic_profiles'].append(step_data['semantic_profile'])
                
                if 'intent_alignment' in step_data:
                    step_semantic_data[step_name]['alignment_results'].append(step_data['intent_alignment'])
                
                if step_data.get('continue', 'True') == 'False':
                    step_semantic_data[step_name]['drops'] += 1
                else:
                    step_semantic_data[step_name]['continues'] += 1
    
    # Aggregate semantic insights
    semantic_insights = {}
    for step_name, data in step_semantic_data.items():
        if data['alignment_results']:
            avg_alignment = sum(a.get('intent_alignment_score', 0.5) for a in data['alignment_results']) / len(data['alignment_results'])
            conflict_axes = []
            for a in data['alignment_results']:
                conflict_axes.extend(a.get('conflict_axes', []))
            conflict_counts = {}
            for axis in conflict_axes:
                conflict_counts[axis] = conflict_counts.get(axis, 0) + 1
            
            semantic_insights[step_name] = {
                'avg_alignment_score': avg_alignment,
                'drop_rate': data['drops'] / (data['drops'] + data['continues']) if (data['drops'] + data['continues']) > 0 else 0,
                'conflict_axes': conflict_counts,
                'total_analyzed': len(data['alignment_results'])
            }
    
    summary = {
        'simulation_type': 'semantic_aware_behavioral_engine',
        'product': 'Blink Money (Credit against Mutual Funds)',
        'timestamp': datetime.now().isoformat(),
        'total_personas': int(len(result_df)),
        'total_trajectories': int(total_trajectories),
        'overall_completion_rate': float(overall_completion),
        'total_semantic_mismatches': int(total_semantic_mismatches),
        'intent_distribution': convert_to_native(intent_distribution),
        'semantic_insights': convert_to_native(semantic_insights),
        'step_semantic_data': convert_to_native({
            step_name: {
                'drops': int(data['drops']),
                'continues': int(data['continues']),
                'drop_rate': float(data['drops'] / (data['drops'] + data['continues']) if (data['drops'] + data['continues']) > 0 else 0),
                'sample_semantic_profile': data['semantic_profiles'][0] if data['semantic_profiles'] else None,
                'sample_alignment_result': data['alignment_results'][0] if data['alignment_results'] else None
            }
            for step_name, data in step_semantic_data.items()
        }),
        'failure_reasons': convert_to_native(dict(Counter([t['failure_reason'] for _, row in result_df.iterrows() for t in row['trajectories'] if t.get('failure_reason')]))),
        'exit_steps': convert_to_native(dict(Counter([t['exit_step'] for _, row in result_df.iterrows() for t in row['trajectories']])))
    }
    
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"   ✓ Results saved to {output_file}")
    
    print("\n" + "=" * 80)
    print("✅ SEMANTIC-AWARE SIMULATION COMPLETE")
    print("=" * 80)
    print(f"\n📊 KEY METRICS:")
    print(f"   Completion Rate: {overall_completion:.1%}")
    print(f"   Total Semantic Mismatches: {total_semantic_mismatches:,}")
    print(f"   Results saved to: {output_file}")
    print("=" * 80 + "\n")
    
    return result_df, summary

if __name__ == "__main__":
    result_df, summary = main()

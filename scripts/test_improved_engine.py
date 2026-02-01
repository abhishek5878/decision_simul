#!/usr/bin/env python3
import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

"""
Test script to compare original vs improved behavioral engine.
"""

import numpy as np
import pandas as pd
from collections import Counter

def test_improved_engine():
    """Test the improved behavioral engine and show results."""
    print("\n" + "=" * 80)
    print("🧪 TESTING IMPROVED BEHAVIORAL ENGINE")
    print("=" * 80)
    
    try:
        from load_dataset import load_and_sample
        from derive_features import derive_all_features
        from behavioral_engine_improved import run_behavioral_simulation_improved
        
        # Load small sample for testing
        print("\n📂 Loading dataset...")
        n_personas = 20
        df, _ = load_and_sample(n=n_personas, seed=42, verbose=False)
        print(f"   Loaded {len(df)} personas")
        
        print("\n🔧 Deriving features...")
        df = derive_all_features(df, verbose=False)
        print(f"   Derived features")
        
        # Run improved simulation
        print("\n🧠 Running IMPROVED behavioral simulation...")
        print("   (This may take a moment...)")
        result_df = run_behavioral_simulation_improved(df, verbose=True, seed=42)
        
        # Analyze results
        print("\n" + "=" * 80)
        print("📊 RESULTS ANALYSIS")
        print("=" * 80)
        
        # 1. Completion Rate
        total_trajectories = len(result_df) * 7  # 7 variants per persona
        total_completed = result_df['variants_completed'].sum()
        overall_completion = total_completed / total_trajectories
        
        print(f"\n✅ COMPLETION RATE:")
        print(f"   Overall: {overall_completion:.1%} ({total_completed}/{total_trajectories} trajectories)")
        print(f"   Per Persona Average: {result_df['completion_rate'].mean():.1%}")
        print(f"   Range: {result_df['completion_rate'].min():.1%} - {result_df['completion_rate'].max():.1%}")
        
        # Validation
        if 0.05 <= overall_completion <= 0.50:
            print(f"   ✓ Realistic completion rate (5-50%)")
        else:
            print(f"   ⚠️  Completion rate outside expected range (5-50%)")
        
        # 2. Failure Reason Diversity
        print(f"\n📋 FAILURE REASON DISTRIBUTION:")
        all_failure_reasons = []
        for _, row in result_df.iterrows():
            for traj in row['trajectories']:
                if traj.get('failure_reason'):
                    all_failure_reasons.append(traj['failure_reason'])
        
        if all_failure_reasons:
            reason_counts = Counter(all_failure_reasons)
            total_failures = len(all_failure_reasons)
            
            for reason, count in reason_counts.most_common():
                pct = count / total_failures * 100
                print(f"   {reason}: {count} ({pct:.1f}%)")
            
            # Validation
            max_reason_pct = reason_counts.most_common(1)[0][1] / total_failures * 100
            if max_reason_pct < 60:
                print(f"   ✓ Failure reasons are distributed (no single reason > 60%)")
            else:
                print(f"   ⚠️  One reason dominates ({max_reason_pct:.1f}%)")
        else:
            print("   (All trajectories completed - no failures)")
        
        # 3. Exit Step Diversity
        print(f"\n🚪 EXIT STEP DISTRIBUTION:")
        all_exit_steps = []
        for _, row in result_df.iterrows():
            for traj in row['trajectories']:
                all_exit_steps.append(traj['exit_step'])
        
        exit_counts = Counter(all_exit_steps)
        for step, count in exit_counts.most_common(10):
            pct = count / len(all_exit_steps) * 100
            print(f"   {step}: {count} ({pct:.1f}%)")
        
        # 4. Energy Recovery Analysis
        print(f"\n⚡ ENERGY RECOVERY ANALYSIS:")
        recovery_count = 0
        total_steps = 0
        
        for _, row in result_df.iterrows():
            for traj in row['trajectories']:
                journey = traj.get('journey', [])
                for i in range(1, len(journey)):
                    prev_energy = journey[i-1].get('cognitive_energy', 0)
                    curr_energy = journey[i].get('cognitive_energy', 0)
                    if curr_energy > prev_energy:
                        recovery_count += 1
                    total_steps += 1
        
        if total_steps > 0:
            recovery_rate = recovery_count / total_steps * 100
            print(f"   Energy recovery events: {recovery_count}/{total_steps} ({recovery_rate:.1f}%)")
            if recovery_rate > 0:
                print(f"   ✓ Energy recovery is working")
            else:
                print(f"   ⚠️  No energy recovery detected")
        
        # 5. Persona Variance
        print(f"\n👥 PERSONA VARIANCE:")
        completion_rates = result_df['completion_rate'].values
        variance = np.var(completion_rates)
        std_dev = np.std(completion_rates)
        
        print(f"   Completion rate variance: {variance:.4f}")
        print(f"   Standard deviation: {std_dev:.1%}")
        
        if std_dev > 0.05:  # 5% std dev
            print(f"   ✓ Good variance between personas")
        else:
            print(f"   ⚠️  Low variance (personas too similar)")
        
        # 6. Value Override Analysis
        print(f"\n💎 VALUE OVERRIDE ANALYSIS:")
        high_value_continuations = 0
        high_value_total = 0
        
        for _, row in result_df.iterrows():
            for traj in row['trajectories']:
                journey = traj.get('journey', [])
                for step_data in journey:
                    value = step_data.get('perceived_value', 0)
                    continued = step_data.get('continue', 'True') == 'True'
                    
                    if value > 0.7:  # High value threshold
                        high_value_total += 1
                        if continued:
                            high_value_continuations += 1
        
        if high_value_total > 0:
            high_value_continuation_rate = high_value_continuations / high_value_total * 100
            print(f"   High value steps (>0.7): {high_value_total}")
            print(f"   Continuation rate at high value: {high_value_continuation_rate:.1f}%")
            if high_value_continuation_rate > 60:
                print(f"   ✓ Value override is working (high value → high continuation)")
            else:
                print(f"   ⚠️  Value override may need tuning")
        
        # 7. Commitment Effect
        print(f"\n📈 COMMITMENT EFFECT ANALYSIS:")
        # Group by step position
        step_positions = {}
        for _, row in result_df.iterrows():
            for traj in row['trajectories']:
                journey = traj.get('journey', [])
                for i, step_data in enumerate(journey):
                    if i not in step_positions:
                        step_positions[i] = {'total': 0, 'continued': 0}
                    
                    step_positions[i]['total'] += 1
                    if step_data.get('continue', 'True') == 'True':
                        step_positions[i]['continued'] += 1
        
        if len(step_positions) > 0:
            print("   Continuation rate by step position:")
            for pos in sorted(step_positions.keys())[:5]:  # First 5 steps
                data = step_positions[pos]
                rate = data['continued'] / data['total'] * 100 if data['total'] > 0 else 0
                print(f"   Step {pos+1}: {rate:.1f}% ({data['continued']}/{data['total']})")
            
            # Check if later steps have higher continuation
            early_rate = step_positions[0]['continued'] / step_positions[0]['total'] * 100 if step_positions[0]['total'] > 0 else 0
            if len(step_positions) > 3:
                late_pos = max(step_positions.keys())
                late_rate = step_positions[late_pos]['continued'] / step_positions[late_pos]['total'] * 100 if step_positions[late_pos]['total'] > 0 else 0
                if late_rate > early_rate:
                    print(f"   ✓ Commitment effect detected (later steps have higher continuation)")
                else:
                    print(f"   ⚠️  Commitment effect not clear (may need tuning)")
        
        # Summary
        print("\n" + "=" * 80)
        print("✅ VALIDATION SUMMARY")
        print("=" * 80)
        
        checks = []
        if 0.05 <= overall_completion <= 0.50:
            checks.append("✓ Completion rate realistic (5-50%)")
        else:
            checks.append("✗ Completion rate outside expected range")
        
        if all_failure_reasons:
            max_reason_pct = Counter(all_failure_reasons).most_common(1)[0][1] / len(all_failure_reasons) * 100
            if max_reason_pct < 60:
                checks.append("✓ Failure reasons distributed")
            else:
                checks.append("✗ One failure reason dominates")
        else:
            checks.append("✓ All trajectories completed")
        
        if std_dev > 0.05:
            checks.append("✓ Good persona variance")
        else:
            checks.append("⚠️  Low persona variance")
        
        if recovery_count > 0:
            checks.append("✓ Energy recovery working")
        else:
            checks.append("⚠️  No energy recovery detected")
        
        for check in checks:
            print(f"   {check}")
        
        print("\n" + "=" * 80)
        print("✅ TEST COMPLETE")
        print("=" * 80)
        
        return result_df
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result_df = test_improved_engine()


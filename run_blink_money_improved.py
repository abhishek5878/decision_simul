#!/usr/bin/env python3
"""
Run improved behavioral simulation for Blink Money with 1000 personas.
"""

import numpy as np
import pandas as pd
from collections import Counter
import json
from datetime import datetime

def run_blink_money_simulation_improved():
    """Run improved behavioral simulation for Blink Money."""
    print("\n" + "=" * 80)
    print("🚀 BLINK MONEY IMPROVED BEHAVIORAL SIMULATION")
    print("=" * 80)
    print(f"   Personas: 1000")
    print(f"   Product: Blink Money (Credit against Mutual Funds)")
    print(f"   Model: Improved Behavioral Engine")
    print("=" * 80)
    
    try:
        from load_dataset import load_and_sample
        from derive_features import derive_all_features
        from behavioral_engine_improved import run_behavioral_simulation_improved
        from blink_money_steps import BLINK_MONEY_STEPS
        
        # Load 1000 personas
        print("\n📂 Loading dataset...")
        start_time = datetime.now()
        df, _ = load_and_sample(n=1000, seed=42, verbose=False)
        print(f"   Loaded {len(df)} personas")
        
        print("\n🔧 Deriving features...")
        df = derive_all_features(df, verbose=False)
        print(f"   Derived features")
        
        # Run improved simulation
        print("\n🧠 Running IMPROVED behavioral simulation...")
        print("   (This will take a few minutes...)")
        result_df = run_behavioral_simulation_improved(
            df, 
            verbose=True, 
            product_steps=BLINK_MONEY_STEPS,
            seed=42
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n⏱️  Total time: {elapsed:.1f}s ({elapsed/1000:.2f}s per persona)")
        
        # Comprehensive Analysis
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE RESULTS ANALYSIS")
        print("=" * 80)
        
        # 1. Overall Metrics
        total_trajectories = len(result_df) * 7  # 7 variants per persona
        total_completed = result_df['variants_completed'].sum()
        overall_completion = total_completed / total_trajectories
        
        print(f"\n✅ OVERALL METRICS:")
        print(f"   Total Personas: {len(result_df):,}")
        print(f"   Total Trajectories: {total_trajectories:,}")
        print(f"   Completed Trajectories: {total_completed:,}")
        print(f"   Overall Completion Rate: {overall_completion:.1%}")
        print(f"   Per-Persona Average: {result_df['completion_rate'].mean():.1%}")
        print(f"   Completion Rate Range: {result_df['completion_rate'].min():.1%} - {result_df['completion_rate'].max():.1%}")
        
        # 2. Step-by-Step Funnel Analysis
        print(f"\n📈 FUNNEL ANALYSIS:")
        step_entries = Counter()
        step_exits = Counter()
        step_completions = Counter()
        
        for _, row in result_df.iterrows():
            for traj in row['trajectories']:
                journey = traj.get('journey', [])
                for i, step_data in enumerate(journey):
                    step_name = step_data.get('step', 'Unknown')
                    step_entries[step_name] += 1
                    
                    # Check if they continued or exited
                    if step_data.get('continue', 'True') == 'False':
                        step_exits[step_name] += 1
                
                # Track completions
                if traj.get('completed', False):
                    step_completions['Completed'] += 1
        
        # Build funnel table
        print(f"\n   Step-by-Step Funnel:")
        print(f"   {'Step':<40} {'Entered':<12} {'Exited':<12} {'Drop Rate':<12} {'Cumulative Loss':<15}")
        print(f"   {'-'*40} {'-'*12} {'-'*12} {'-'*12} {'-'*15}")
        
        cumulative_entered = total_trajectories
        cumulative_loss = 0
        
        for step_name in BLINK_MONEY_STEPS.keys():
            entered = step_entries.get(step_name, 0)
            exited = step_exits.get(step_name, 0)
            drop_rate = (exited / entered * 100) if entered > 0 else 0
            cumulative_loss += exited
            cumulative_loss_pct = (cumulative_loss / total_trajectories * 100) if total_trajectories > 0 else 0
            
            display_name = step_name[:38] + '..' if len(step_name) > 40 else step_name
            print(f"   {display_name:<40} {entered:<12,} {exited:<12,} {drop_rate:<11.1f}% {cumulative_loss_pct:<14.1f}%")
        
        # Completed
        completed_count = step_completions.get('Completed', 0)
        print(f"   {'Completed':<40} {total_trajectories:<12,} {completed_count:<12,} {'N/A':<12} {'N/A':<15}")
        
        # 3. Failure Reason Distribution
        print(f"\n📋 FAILURE REASON DISTRIBUTION:")
        all_failure_reasons = []
        for _, row in result_df.iterrows():
            for traj in row['trajectories']:
                if traj.get('failure_reason'):
                    all_failure_reasons.append(traj['failure_reason'])
        
        if all_failure_reasons:
            reason_counts = Counter(all_failure_reasons)
            total_failures = len(all_failure_reasons)
            
            print(f"   Total Failures: {total_failures:,}")
            print(f"\n   {'Reason':<30} {'Count':<12} {'Percentage':<12}")
            print(f"   {'-'*30} {'-'*12} {'-'*12}")
            
            for reason, count in reason_counts.most_common():
                pct = count / total_failures * 100
                print(f"   {reason:<30} {count:<12,} {pct:<11.1f}%")
        else:
            print("   (All trajectories completed - no failures)")
        
        # 4. Exit Step Distribution
        print(f"\n🚪 EXIT STEP DISTRIBUTION:")
        all_exit_steps = []
        for _, row in result_df.iterrows():
            for traj in row['trajectories']:
                all_exit_steps.append(traj['exit_step'])
        
        exit_counts = Counter(all_exit_steps)
        print(f"\n   {'Exit Step':<40} {'Count':<12} {'Percentage':<12}")
        print(f"   {'-'*40} {'-'*12} {'-'*12}")
        
        for step, count in exit_counts.most_common(10):
            display_name = step[:38] + '..' if len(step) > 40 else step
            pct = count / len(all_exit_steps) * 100
            print(f"   {display_name:<40} {count:<12,} {pct:<11.1f}%")
        
        # 5. Energy Recovery Analysis
        print(f"\n⚡ ENERGY RECOVERY ANALYSIS:")
        recovery_count = 0
        total_steps = 0
        recovery_by_step = Counter()
        
        for _, row in result_df.iterrows():
            for traj in row['trajectories']:
                journey = traj.get('journey', [])
                for i in range(1, len(journey)):
                    prev_energy = journey[i-1].get('cognitive_energy', 0)
                    curr_energy = journey[i].get('cognitive_energy', 0)
                    if curr_energy > prev_energy:
                        recovery_count += 1
                        recovery_by_step[journey[i].get('step', 'Unknown')] += 1
                    total_steps += 1
        
        if total_steps > 0:
            recovery_rate = recovery_count / total_steps * 100
            print(f"   Total Steps Analyzed: {total_steps:,}")
            print(f"   Energy Recovery Events: {recovery_count:,} ({recovery_rate:.1f}%)")
            
            if recovery_count > 0:
                print(f"\n   Recovery by Step:")
                for step, count in recovery_by_step.most_common(5):
                    print(f"     {step}: {count} recoveries")
        
        # 6. Persona Variance Analysis
        print(f"\n👥 PERSONA VARIANCE ANALYSIS:")
        completion_rates = result_df['completion_rate'].values
        variance = np.var(completion_rates)
        std_dev = np.std(completion_rates)
        median = np.median(completion_rates)
        
        print(f"   Mean Completion Rate: {np.mean(completion_rates):.1%}")
        print(f"   Median Completion Rate: {median:.1%}")
        print(f"   Standard Deviation: {std_dev:.1%}")
        print(f"   Variance: {variance:.4f}")
        print(f"   Min: {np.min(completion_rates):.1%}")
        print(f"   Max: {np.max(completion_rates):.1%}")
        
        # 7. Value Override Analysis
        print(f"\n💎 VALUE OVERRIDE ANALYSIS:")
        high_value_continuations = 0
        high_value_total = 0
        low_value_continuations = 0
        low_value_total = 0
        
        for _, row in result_df.iterrows():
            for traj in row['trajectories']:
                journey = traj.get('journey', [])
                for step_data in journey:
                    value = step_data.get('perceived_value', 0)
                    continued = step_data.get('continue', 'True') == 'True'
                    
                    if value > 0.7:  # High value
                        high_value_total += 1
                        if continued:
                            high_value_continuations += 1
                    elif value < 0.3:  # Low value
                        low_value_total += 1
                        if continued:
                            low_value_continuations += 1
        
        if high_value_total > 0:
            high_value_rate = high_value_continuations / high_value_total * 100
            print(f"   High Value Steps (>0.7): {high_value_total:,}")
            print(f"   Continuation Rate: {high_value_rate:.1f}%")
        
        if low_value_total > 0:
            low_value_rate = low_value_continuations / low_value_total * 100
            print(f"   Low Value Steps (<0.3): {low_value_total:,}")
            print(f"   Continuation Rate: {low_value_rate:.1f}%")
        
        # 8. Commitment Effect Analysis
        print(f"\n📈 COMMITMENT EFFECT ANALYSIS:")
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
            print(f"   Continuation Rate by Step Position:")
            for pos in sorted(step_positions.keys()):
                data = step_positions[pos]
                rate = data['continued'] / data['total'] * 100 if data['total'] > 0 else 0
                print(f"     Step {pos+1}: {rate:.1f}% ({data['continued']:,}/{data['total']:,})")
        
        # 9. Save Results
        output_file = "output/blink_money_improved_results.json"
        print(f"\n💾 SAVING RESULTS:")
        print(f"   Saving to: {output_file}")
        
        # Prepare summary for JSON
        summary = {
            'simulation_type': 'improved_behavioral_engine',
            'product': 'Blink Money (Credit against Mutual Funds)',
            'timestamp': datetime.now().isoformat(),
            'total_personas': len(result_df),
            'total_trajectories': total_trajectories,
            'overall_completion_rate': overall_completion,
            'funnel_analysis': {
                step_name: {
                    'entered': step_entries.get(step_name, 0),
                    'exited': step_exits.get(step_name, 0),
                    'drop_rate': (step_exits.get(step_name, 0) / step_entries.get(step_name, 1) * 100) if step_entries.get(step_name, 0) > 0 else 0
                }
                for step_name in BLINK_MONEY_STEPS.keys()
            },
            'failure_reasons': dict(reason_counts) if all_failure_reasons else {},
            'exit_steps': dict(exit_counts),
            'energy_recovery': {
                'total_events': recovery_count,
                'recovery_rate': recovery_rate if total_steps > 0 else 0,
                'by_step': dict(recovery_by_step)
            },
            'persona_variance': {
                'mean': float(np.mean(completion_rates)),
                'median': float(median),
                'std_dev': float(std_dev),
                'min': float(np.min(completion_rates)),
                'max': float(np.max(completion_rates))
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"   ✓ Results saved")
        
        # Final Summary
        print("\n" + "=" * 80)
        print("✅ SIMULATION COMPLETE")
        print("=" * 80)
        print(f"\n📊 KEY INSIGHTS:")
        print(f"   • Completion Rate: {overall_completion:.1%} (realistic range: 5-50%)")
        print(f"   • Energy Recovery: {recovery_count:,} events ({recovery_rate:.1f}% of steps)")
        print(f"   • Persona Variance: {std_dev:.1%} std dev (good diversity)")
        if high_value_total > 0:
            print(f"   • Value Override: {high_value_rate:.1f}% continuation at high value")
        print(f"   • Results saved to: {output_file}")
        print("=" * 80 + "\n")
        
        return result_df, summary
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None, None


if __name__ == "__main__":
    result_df, summary = run_blink_money_simulation_improved()


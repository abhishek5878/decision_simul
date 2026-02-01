#!/usr/bin/env python3
"""
run_behavioral_simulation.py - Behavioral State-Based Simulation Runner

Runs the cognitive state-based behavioral simulation engine.

This answers "WHY they dropped at step t" before "WHO".
"""

import argparse
from load_dataset import load_and_sample
from derive_features import derive_all_features
from behavioral_engine import run_behavioral_simulation, PRODUCT_STEPS
from behavioral_aggregator import (
    format_failure_mode_report,
    generate_full_report,
    print_persona_state_trace,
    export_persona_traces_json
)
from fintech_presets import get_default_fintech_scenario, FINTECH_ONBOARDING_STEPS
from fintech_demo import (
    run_fintech_demo_simulation,
    print_fintech_trace,
    export_fintech_json
)


def main():
    parser = argparse.ArgumentParser(
        description="Behavioral State-Based Simulation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard simulation
  python run_behavioral_simulation.py --n 100 --seed 42
  
  # Fintech onboarding demo
  python run_behavioral_simulation.py --fintech-demo
  
  # View specific persona × variant trace
  python run_behavioral_simulation.py --fintech-demo \\
    --persona-name "Salaried_Tier2_Cautious" \\
    --variant tired_commuter
  
  # Export fintech demo to JSON
  python run_behavioral_simulation.py --fintech-demo --export fintech_demo.json
        """
    )
    parser.add_argument("--n", type=int, default=100, help="Number of personas (ignored if --fintech-demo)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (ignored if --fintech-demo)")
    parser.add_argument("--fintech-demo", action="store_true", help="Run fintech onboarding demo")
    parser.add_argument("--trace", type=int, default=None, help="Show trace for persona index (standard mode)")
    parser.add_argument("--persona-name", type=str, default=None, help="Persona name for trace (fintech-demo mode)")
    parser.add_argument("--variant", type=str, default=None, help="State variant name for trace")
    parser.add_argument("--export", type=str, default=None, help="Export traces to JSON file")
    parser.add_argument("--export-all-variants", action="store_true", help="Export all variants per persona")
    
    args = parser.parse_args()
    
    # ============================================================================
    # FINTECH DEMO MODE
    # ============================================================================
    if args.fintech_demo:
        print("\n" + "=" * 80)
        print("🏦 FINTECH ONBOARDING DEMO")
        print("=" * 80)
        print("   Using default fintech personas and onboarding flow")
        print("=" * 80)
        
        # Load fintech scenario
        personas, state_variants, product_steps = get_default_fintech_scenario()
        
        # Run simulation
        result_df = run_fintech_demo_simulation(
            personas, state_variants, product_steps, verbose=True
        )
        
        # Generate report
        print("\n" + "=" * 80)
        print("[Fintech Onboarding Demo]")
        print("=" * 80)
        
        # Format failure mode report
        report = generate_full_report(result_df, product_steps=product_steps)
        print(report['report_text'])
        
        # Persona-level summary
        print("\n" + "=" * 80)
        print("👥 PERSONA SUMMARY")
        print("=" * 80)
        
        for _, row in result_df.iterrows():
            persona_name = str(row['persona_name']).split('\n')[0] if '\n' in str(row['persona_name']) else str(row['persona_name'])
            persona_desc = str(row['persona_description']).split('\n')[0] if '\n' in str(row['persona_description']) else str(row['persona_description'])
            print(f"\n{persona_name}: {persona_desc}")
            print(f"   Exit: {row['dominant_exit_step']} | Reason: {row['dominant_failure_reason']}")
            print(f"   Completed: {row['variants_completed']}/{row['variants_total']} variants")
            print(f"   Consistency: {row['consistency_score']:.2f}")
        
        # Drill-down: Show specific persona × variant trace
        if args.persona_name:
            print_fintech_trace(result_df, args.persona_name, args.variant or 'fresh_motivated', product_steps)
        
        # Export JSON
        if args.export:
            export_fintech_json(personas, result_df, state_variants, product_steps, args.export)
        
        print("\n" + "=" * 80)
        print("✅ FINTECH DEMO COMPLETE")
        print("=" * 80)
        print("\n💡 TIP: Use --persona-name <name> --variant <name> to see specific trace")
        print(f"   Available personas: {', '.join([p['name'] for p in personas])}")
        print("=" * 80)
        
        return result_df
    
    # ============================================================================
    # STANDARD MODE (Existing behavior)
    # ============================================================================
    print("\n" + "=" * 80)
    print("🧠 CREDIGO.CLUB BEHAVIORAL STATE-BASED SIMULATION")
    print("=" * 80)
    print(f"   Personas: {args.n}")
    print(f"   State variants per persona: 7")
    print(f"   Total trajectories: {args.n * 7}")
    print(f"   Seed: {args.seed}")
    print("=" * 80)
    
    # Load and process
    print("\n📂 Loading dataset...")
    df, _ = load_and_sample(n=args.n, seed=args.seed, verbose=False)
    print(f"   Loaded {len(df)} personas")
    
    print("\n🔧 Deriving features...")
    df = derive_all_features(df, verbose=False)
    print(f"   Derived features")
    
    # Run behavioral simulation
    print("\n🧠 Running behavioral simulation...")
    result_df = run_behavioral_simulation(df, verbose=True)
    
    # Generate full report (spec-compliant format)
    print("\n" + "=" * 80)
    report = generate_full_report(result_df)
    print(report['report_text'])
    
    # Persona-level insights
    print("\n" + "=" * 80)
    print("👥 PERSONA-LEVEL INSIGHTS")
    print("=" * 80)
    
    print(f"\nExit Step Distribution:")
    exit_dist = result_df['dominant_exit_step'].value_counts()
    for step, count in exit_dist.items():
        pct = count / len(result_df) * 100
        print(f"   {step}: {count} ({pct:.1f}%)")
    
    print(f"\nFailure Reason Distribution:")
    reason_dist = result_df['dominant_failure_reason'].value_counts()
    for reason, count in reason_dist.items():
        pct = count / len(result_df) * 100
        print(f"   {reason}: {count} ({pct:.1f}%)")
    
    print(f"\nConsistency Analysis:")
    print(f"   Avg consistency: {result_df['consistency_score'].mean():.2f}")
    print(f"   High consistency (>0.7): {(result_df['consistency_score'] > 0.7).sum()}")
    print(f"   Low consistency (<0.4): {(result_df['consistency_score'] < 0.4).sum()}")
    
    # Drill-down: Show specific persona × state trace
    if args.trace is not None:
        if 0 <= args.trace < len(result_df):
            print_persona_state_trace(result_df, args.trace, args.variant)
        else:
            print(f"❌ Invalid persona index. Must be 0-{len(result_df)-1}")
    
    # Export JSON traces
    if args.export:
        export_persona_traces_json(
            result_df,
            args.export,
            all_variants=args.export_all_variants
        )
    
    print("\n" + "=" * 80)
    print("✅ SIMULATION COMPLETE")
    print("=" * 80)
    print("\n💡 TIP: Use --trace <index> to see full journey for a persona")
    print("   Use --export <file.json> to export traces for data science teams")
    print("=" * 80)
    
    return result_df


if __name__ == "__main__":
    result_df = main()


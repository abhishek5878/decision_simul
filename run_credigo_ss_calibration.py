#!/usr/bin/env python3
"""
Run real-world calibration for Credigo SS.

Calibrates model parameters to match observed funnel data.
"""

import sys
from calibration.real_world_calibration import (
    ObservedFunnelData,
    calibrate_to_real_data,
    export_calibration_summary,
    export_calibration_diagnostics,
    log_parameter_changes
)


def main():
    print("\n" + "=" * 80)
    print("REAL-WORLD CALIBRATION: Credigo SS")
    print("=" * 80)
    
    try:
        # Import dependencies
        from load_dataset import load_and_sample
        from derive_features import derive_all_features
        from behavioral_engine_improved import run_behavioral_simulation_improved
        from credigo_ss_steps_improved import CREDIGO_SS_11_STEPS
        
        # Load personas
        print("\n📂 Loading dataset...")
        n_personas = 500  # Smaller sample for faster calibration
        df, _ = load_and_sample(n=n_personas, seed=42, verbose=False)
        print(f"   Loaded {len(df)} personas")
        
        print("\n🔧 Deriving features...")
        df = derive_all_features(df, verbose=False)
        print(f"   Derived features")
        
        # ====================================================================
        # OBSERVED FUNNEL DATA (Example - replace with real data)
        # ====================================================================
        print("\n📊 Setting up observed funnel data...")
        print("   NOTE: Replace with your actual observed data from analytics!")
        
        # Example observed data structure for Credigo SS
        # In production, this would come from analytics (Google Analytics, Mixpanel, etc.)
        # These are example numbers - replace with real data
        observed_funnel = ObservedFunnelData(
            entry_count=10000,  # Total visitors
            step_completions={
                "Find the Best Credit Card In 60 seconds": 3500,  # 35% entered
                "What kind of perks excite you the most?": 2800,  # 80% of entries
                "Any preference on annual fee?": 2200,
                "straightforward + options are clearly defined": 1800,
                "Your top 2 spend categories?": 1500,
                "Do you track your monthly spending?": 1200,
                "How much do you spend monthly?": 1000,
                "Help us personalise your card matches": 800,
                "Best Deals for You – Apply Now": 600,
                "Completed": 500  # 5% total conversion
            },
            total_completions=500
        )
        
        print(f"   Entry count: {observed_funnel.entry_count:,}")
        print(f"   Total completions: {observed_funnel.total_completions:,}")
        print(f"   Observed completion rate: {observed_funnel.total_completions / observed_funnel.entry_count:.2%}")
        
        # Compute observed rates
        observed_rates = observed_funnel.compute_rates()
        print(f"\n   Observed rates (first 5 steps):")
        for step_name, rate in list(observed_rates.items())[:5]:
            print(f"     {step_name}: {rate:.2%}")
        
        # Setup simulation
        simulation_args = {
            'df': df,
            'verbose': False,
            'product_steps': CREDIGO_SS_11_STEPS,
            'seed': 42
        }
        
        # Optional: Entry signals for full funnel calibration
        entry_signals = {
            'referrer': 'direct',
            'intent_frame': {'commitment_threshold': 0.7, 'tolerance_for_effort': 0.6},
            'landing_page_text': 'Find the Best Credit Card In 60 seconds - No PAN required'
        }
        
        # Run calibration
        print("\n🔧 Running calibration...")
        print("   This will take a few minutes (multiple simulations required)...")
        calibrated_params, summary, diagnostics = calibrate_to_real_data(
            observed_funnel=observed_funnel,
            simulation_function=run_behavioral_simulation_improved,
            simulation_args=simulation_args,
            product_steps=CREDIGO_SS_11_STEPS,
            entry_signals=entry_signals,
            regularization_weight=0.1,
            max_iterations=20,  # Reduced for faster execution
            verbose=True
        )
        
        # Export results
        print("\n💾 Exporting calibration results...")
        export_calibration_summary(summary, 'credigo_ss_calibration_summary.json')
        print(f"   ✓ Calibration summary: credigo_ss_calibration_summary.json")
        
        export_calibration_diagnostics(diagnostics, 'credigo_ss_calibration_diagnostics.json')
        print(f"   ✓ Calibration diagnostics: credigo_ss_calibration_diagnostics.json")
        
        log_parameter_changes(summary, 'credigo_ss_parameter_changes.log')
        print(f"   ✓ Parameter changes log: credigo_ss_parameter_changes.log")
        
        # Final validation output
        print("\n" + "=" * 80)
        print("FINAL VALIDATION")
        print("=" * 80)
        print(f"\nBefore calibration:")
        print(f"  Mean absolute error = {summary.before_error:.6f}")
        print(f"\nAfter calibration:")
        print(f"  Mean absolute error = {summary.after_error:.6f}")
        print(f"\nImprovement: {summary.improvement_pct:.1f}%")
        print(f"Fit score: {summary.fit_score:.4f}")
        print("\n" + "=" * 80)
        print("✅ CALIBRATION COMPLETE")
        print("=" * 80)
        print("\n📁 Output files:")
        print("   - credigo_ss_calibration_summary.json")
        print("   - credigo_ss_calibration_diagnostics.json")
        print("   - credigo_ss_parameter_changes.log")
        print("\n💡 Next steps:")
        print("   1. Review calibrated parameters")
        print("   2. Replace example data with real observed data")
        print("   3. Validate against additional data")
        print("   4. Use calibrated parameters in production")
        print("=" * 80 + "\n")
        
        return calibrated_params, summary, diagnostics
        
    except Exception as e:
        print(f"\n❌ Error during calibration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()


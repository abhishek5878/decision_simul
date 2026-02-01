#!/usr/bin/env python3
import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

"""
Run comprehensive model evaluation for Credigo.

Evaluates model reliability, confidence, and stability.
"""

import sys
from datetime import datetime

def main():
    print("\n" + "=" * 80)
    print("🔍 MODEL EVALUATION: Credigo.club")
    print("=" * 80)
    print("   Evaluating: Reliability, Confidence, Stability")
    print("=" * 80)
    
    try:
        # Import dependencies
        from load_dataset import load_and_sample
        from derive_features import derive_all_features
        from behavioral_engine_improved import run_behavioral_simulation_improved
        from credigo_11_steps import CREDIGO_11_STEPS
        from calibration import (
            evaluate_model,
            export_evaluation_report,
            export_calibration_report,
            export_sensitivity_report,
            export_confidence_intervals,
            get_default_parameters
        )
        
        # Load personas
        print("\n📂 Loading dataset...")
        n_personas = 500  # Use smaller sample for faster evaluation
        df, _ = load_and_sample(n=n_personas, seed=42, verbose=False)
        print(f"   Loaded {len(df)} personas")
        
        print("\n🔧 Deriving features...")
        df = derive_all_features(df, verbose=False)
        print(f"   Derived features")
        
        # Use default parameters as baseline
        baseline_parameters = get_default_parameters()
        print(f"\n📊 Using default parameters as baseline")
        print(f"   Parameters: {len(baseline_parameters)}")
        
        # Setup simulation arguments
        simulation_args = {
            'df': df,
            'verbose': False,  # Reduce verbosity during evaluation
            'product_steps': CREDIGO_11_STEPS,
            'seed': 42  # Base seed (will be varied in stochastic runs)
        }
        
        # Run comprehensive evaluation
        print(f"\n🔍 Running comprehensive evaluation...")
        print(f"   This will take some time (multiple simulations required)...")
        start_time = datetime.now()
        
        report = evaluate_model(
            simulation_function=run_behavioral_simulation_improved,
            simulation_args=simulation_args,
            product_steps=CREDIGO_11_STEPS,
            baseline_parameters=baseline_parameters,
            n_stochastic_runs=30,  # Reduced for faster execution
            sensitivity_variation_pct=0.20,
            confidence_level=0.90,
            engine_module='behavioral_engine_improved',
            parameter_subset=None,  # Analyze all parameters
            verbose=True
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n⏱️  Total evaluation time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
        
        # Export reports
        print(f"\n💾 Exporting reports...")
        export_evaluation_report(report, 'credigo_evaluation_report.json')
        print(f"   ✓ Full evaluation report: credigo_evaluation_report.json")
        
        export_calibration_report(report, 'output/credigo_calibration_report.json')
        print(f"   ✓ Calibration report: output/credigo_calibration_report.json")
        
        export_sensitivity_report(report, 'credigo_sensitivity_report.json')
        print(f"   ✓ Sensitivity report: credigo_sensitivity_report.json")
        
        export_confidence_intervals(report, 'credigo_confidence_intervals.json')
        print(f"   ✓ Confidence intervals: credigo_confidence_intervals.json")
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 EVALUATION SUMMARY")
        print("=" * 80)
        print(f"\n🎯 Overall Metrics:")
        print(f"   Mean Completion Rate: {report.overall_confidence.mean_completion:.2%}")
        print(f"   90% Prediction Interval: [{report.overall_prediction_interval.lower_bound:.2%}, {report.overall_prediction_interval.upper_bound:.2%}]")
        print(f"   Median: {report.overall_prediction_interval.median:.2%}")
        print(f"   Standard Deviation: {report.overall_confidence.std_dev:.4f}")
        
        print(f"\n📈 Stability Assessment:")
        print(f"   Stability Score: {report.overall_stability.stability_score:.4f}")
        print(f"   Interpretation: {report.overall_stability.interpretation}")
        print(f"   Coefficient of Variation: {report.overall_stability.coefficient_of_variation:.4f}")
        
        print(f"\n🔍 Top 5 Most Sensitive Parameters:")
        sorted_sensitivity = sorted(
            report.sensitivity_summary.items(),
            key=lambda x: x[1],
            reverse=True
        )
        for i, (param_name, sens) in enumerate(sorted_sensitivity[:5], 1):
            result = report.parameter_sensitivity[param_name]
            print(f"   {i}. {param_name}: {sens:.4f} (rank: {result.impact_rank})")
            print(f"      Baseline: {result.baseline_completion:.2%} | "
                  f"Low: {result.low_completion:.2%} | High: {result.high_completion:.2%}")
        
        print("\n" + "=" * 80)
        print("✅ EVALUATION COMPLETE")
        print("=" * 80)
        print(f"\n📁 Reports saved:")
        print(f"   - credigo_evaluation_report.json (complete report)")
        print(f"   - output/credigo_calibration_report.json (confidence & stability)")
        print(f"   - credigo_sensitivity_report.json (parameter sensitivity)")
        print(f"   - credigo_confidence_intervals.json (prediction intervals)")
        print("=" * 80 + "\n")
        
        return report
        
    except Exception as e:
        print(f"\n❌ Error during evaluation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()


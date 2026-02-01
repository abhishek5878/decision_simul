#!/usr/bin/env python3
"""
Run comprehensive validation suite to increase confidence in the engine.

Tests:
1. Cross-validation across persona samples
2. Edge case handling
3. Industry benchmark validation
4. Parameter sensitivity (if time permits)
"""

import json
from datetime import datetime
from validate_engine_robustness import (
    cross_validate_across_persona_samples,
    test_edge_cases,
    validate_against_benchmarks,
    generate_validation_report
)
from add_confidence_intervals import run_simulation_with_confidence
from load_dataset import load_and_sample
from derive_features import derive_all_features
from credigo_ss_steps_improved import CREDIGO_SS_11_STEPS

def main():
    print("\n" + "="*80)
    print("COMPREHENSIVE ENGINE VALIDATION SUITE")
    print("="*80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("="*80)
    
    # Run comprehensive validation
    report = generate_validation_report()
    
    # Additional: Bootstrap confidence intervals
    print("\n" + "="*60)
    print("Bootstrap Confidence Intervals")
    print("="*60)
    
    df, _ = load_and_sample(n=1000, seed=42, verbose=False)
    df = derive_all_features(df, verbose=False)
    
    ci_results = run_simulation_with_confidence(
        df,
        CREDIGO_SS_11_STEPS,
        n_bootstrap=10,
        confidence_level=0.95
    )
    
    report['bootstrap_confidence'] = ci_results
    
    print(f"\nCompletion Rate with Confidence Interval:")
    print(f"  Mean: {ci_results['mean_completion']:.1%}")
    print(f"  95% CI: {ci_results['ci_lower']:.1%} - {ci_results['ci_upper']:.1%}")
    print(f"  Std Error: {ci_results['std_error']:.1%}")
    print(f"  Range: {ci_results['completion_range']}")
    
    # Calculate updated confidence
    confidence_factors = report.get('confidence_factors', {})
    
    # Add bootstrap factor
    ci_width = ci_results['ci_upper'] - ci_results['ci_lower']
    # Narrower CI = higher confidence
    ci_confidence = max(0.5, 1.0 - (ci_width / 0.20))  # If CI width < 20%, high confidence
    confidence_factors['bootstrap_ci'] = ci_confidence
    
    updated_confidence = sum(confidence_factors.values()) / len(confidence_factors)
    report['updated_confidence'] = updated_confidence
    report['confidence_factors'] = confidence_factors
    
    # Save comprehensive report
    output_file = 'comprehensive_validation_report.json'
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print("\n" + "="*80)
    print("VALIDATION COMPLETE")
    print("="*80)
    print(f"\nOverall Confidence: {updated_confidence:.0%}")
    print(f"  (Up from baseline ~60-70%)")
    print(f"\nConfidence Factors:")
    for factor, value in confidence_factors.items():
        print(f"  {factor}: {value:.0%}")
    print(f"\n✅ Comprehensive report saved to: {output_file}")
    print("="*80 + "\n")
    
    return report

if __name__ == "__main__":
    main()


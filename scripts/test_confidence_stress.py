"""
Test script for confidence stress test suite.
"""
import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import json
import os
from dropsim_confidence_stress_test import run_stress_test_suite

def main():
    print("=" * 80)
    print("CONFIDENCE STRESS TEST SUITE")
    print("=" * 80)
    print()
    
    # Load baseline result
    result_file = "output/credigo_ss_full_pipeline_results.json"
    if not os.path.exists(result_file):
        print(f"❌ Baseline result file not found: {result_file}")
        print("   Please run a full pipeline test first.")
        return
    
    print(f"📊 Loading baseline result from: {result_file}")
    with open(result_file, 'r') as f:
        baseline_result = json.load(f)
    
    print("✅ Baseline result loaded")
    print()
    
    # Run stress test suite
    print("🔬 Running confidence stress test suite...")
    print("   Testing: High-confidence wrong, Low-signal, Overfitting traps, True positives")
    print()
    
    report_card = run_stress_test_suite(baseline_result, random_seed=42)
    
    # Print results
    print("=" * 80)
    print("CONFIDENCE REPORT CARD")
    print("=" * 80)
    print()
    
    print(f"Epistemic Health: {report_card.epistemic_health}")
    print(f"Overconfidence Rate: {report_card.overconfidence_rate:.1%}")
    print(f"Underconfidence Rate: {report_card.underconfidence_rate:.1%}")
    print()
    
    print("Sanity Metrics:")
    print(f"   False Confidence Rate: {report_card.sanity_metrics.false_confidence_rate:.1%}")
    print(f"   Missed Uncertainty Rate: {report_card.sanity_metrics.missed_uncertainty_rate:.1%}")
    print(f"   Confidence Volatility: {report_card.sanity_metrics.confidence_volatility:.3f}")
    print(f"   Overconfidence Count: {report_card.sanity_metrics.overconfidence_count}")
    print(f"   Underconfidence Count: {report_card.sanity_metrics.underconfidence_count}")
    print(f"   Correct Confidence Count: {report_card.sanity_metrics.correct_confidence_count}")
    print()
    
    print("Robust Zones (reliable confidence):")
    for zone in report_card.robust_zones:
        print(f"   ✅ {zone}")
    print()
    
    print("Fragile Zones (unreliable confidence):")
    for zone in report_card.fragile_zones:
        print(f"   ⚠️  {zone}")
    print()
    
    print("Recommendation:")
    print(f"   {report_card.recommendation}")
    print()
    
    print("=" * 80)
    print("RELIABILITY BOUNDARY")
    print("=" * 80)
    print()
    
    print("✅ System is RELIABLE for:")
    for item in report_card.reliability_boundary['reliable_for']:
        print(f"   • {item}")
    print()
    
    print("❌ System is UNRELIABLE for:")
    for item in report_card.reliability_boundary['unreliable_for']:
        print(f"   • {item}")
    print()
    
    print("⚠️  System REQUIRES VALIDATION for:")
    for item in report_card.reliability_boundary['requires_validation']:
        print(f"   • {item}")
    print()
    
    print("=" * 80)
    print("STRESS TEST RESULTS")
    print("=" * 80)
    print()
    
    for i, test_result in enumerate(report_card.test_results, 1):
        status = "✅ PASS" if test_result.passed else "❌ FAIL"
        print(f"{i}. {test_result.test_type} - {status}")
        print(f"   Expected: {test_result.expected_confidence_band}")
        print(f"   Actual: {test_result.actual_confidence_band} ({test_result.actual_confidence:.1%})")
        if test_result.issue:
            print(f"   Issue: {test_result.issue}")
        print()
    
    # Save report
    output_file = "output/confidence_report_card.json"
    with open(output_file, 'w') as f:
        json.dump(report_card.to_dict(), f, indent=2, default=str)
    
    print(f"💾 Confidence report card saved to: {output_file}")
    print()

if __name__ == "__main__":
    main()


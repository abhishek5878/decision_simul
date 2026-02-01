"""
Test script for falsification harness.
Runs falsification tests on Credigo results.
"""

import json
import os
from dropsim_falsification import run_falsification_suite

def main():
    print("=" * 80)
    print("FALSIFICATION HARNESS TEST")
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
    
    # Run falsification suite
    print("🔬 Running falsification test suite...")
    print("   This will inject contradictory evidence and measure system response")
    print()
    
    report = run_falsification_suite(baseline_result, random_seed=42)
    
    # Print results
    print("=" * 80)
    print("FALSIFICATION REPORT")
    print("=" * 80)
    print()
    
    print(f"Total Tests: {report.total_tests}")
    print(f"Contradictions Detected: {report.contradictions_detected}")
    print(f"Contradictions Missed: {report.contradictions_missed}")
    print(f"Confidence Decreased: {report.confidence_decreased_count}")
    print(f"Conclusions Changed: {report.conclusions_changed_count}")
    print()
    
    print("Test Results:")
    for i, result in enumerate(report.test_results, 1):
        print(f"\n{i}. {result.test.test_id} - {result.test.test_type}")
        print(f"   Description: {result.test.description}")
        print(f"   Expected Detection: {result.test.expected_detection}")
        print(f"   Contradiction Detected: {'✅' if result.contradiction_detected else '❌'}")
        print(f"   Confidence Decreased: {'✅' if result.confidence_decreased else '❌'}")
        print(f"   Conclusions Changed: {'✅' if result.conclusions_changed else '❌'}")
        print(f"   Confidence Shift: {result.confidence_shift:+.1%}")
        if result.detection_method:
            print(f"   Detection Method: {result.detection_method}")
    
    print()
    print("=" * 80)
    print(f"VERDICT: {report.verdict}")
    print("=" * 80)
    print()
    print(f"Reasoning: {report.reasoning}")
    print()
    
    # Save report
    output_file = "output/falsification_report.json"
    with open(output_file, 'w') as f:
        json.dump(report.to_dict(), f, indent=2, default=str)
    
    print(f"💾 Falsification report saved to: {output_file}")
    
    # Generate summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    
    detection_rate = report.contradictions_detected / report.total_tests if report.total_tests > 0 else 0.0
    confidence_rate = report.confidence_decreased_count / report.total_tests if report.total_tests > 0 else 0.0
    
    print(f"Detection Rate: {detection_rate:.1%}")
    print(f"Confidence Decrease Rate: {confidence_rate:.1%}")
    print()
    
    if report.verdict == "ROBUST":
        print("✅ System is ROBUST - correctly detects contradictions and adjusts confidence")
    elif report.verdict == "FRAGILE":
        print("⚠️  System is FRAGILE - maintains confidence despite contradictions")
    else:
        print("❓ System is INCONCLUSIVE - mixed behavior detected")
    
    print()

if __name__ == "__main__":
    main()


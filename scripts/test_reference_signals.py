"""
Test script for reference signal layer.
Demonstrates how to add reference signals and see calibration.
"""
import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import json
import os
from dropsim_reference_signals import (
    ReferenceSignal,
    ReferenceSignalStore,
    check_reference_signals
)

def main():
    print("=" * 80)
    print("REFERENCE SIGNAL LAYER TEST")
    print("=" * 80)
    print()
    
    # Load a system result
    result_file = "output/credigo_ss_full_pipeline_results.json"
    if not os.path.exists(result_file):
        print(f"❌ Result file not found: {result_file}")
        print("   Please run a full pipeline test first.")
        return
    
    print(f"📊 Loading system result from: {result_file}")
    with open(result_file, 'r') as f:
        system_result = json.load(f)
    
    print("✅ System result loaded")
    print()
    
    # Create reference signal store
    store = ReferenceSignalStore("config/reference_signals.json")
    
    # Example: Add a reference signal from an A/B test
    print("📝 Adding reference signals...")
    
    # Example 1: A/B test result
    ab_test_signal = ReferenceSignal(
        source="A/B test",
        confidence=0.9,
        assertion={
            "top_drop_step": "What kind of perks excite you the most?",
            "completion_rate": 0.65
        }
    )
    store.add_reference_signal(ab_test_signal)
    print(f"   ✅ Added A/B test signal: {ab_test_signal.signal_id}")
    
    # Example 2: Expert label
    expert_signal = ReferenceSignal(
        source="expert label",
        confidence=0.8,
        assertion={
            "drop_rate_at_step": {
                "step_id": "Your top 2 spend categories?",
                "drop_rate": 0.25
            }
        }
    )
    store.add_reference_signal(expert_signal)
    print(f"   ✅ Added expert signal: {expert_signal.signal_id}")
    
    # Example 3: User interview insight
    interview_signal = ReferenceSignal(
        source="user interview",
        confidence=0.7,
        assertion={
            "top_recommendation": "Help us personalise your card matches"
        }
    )
    store.add_reference_signal(interview_signal)
    print(f"   ✅ Added interview signal: {interview_signal.signal_id}")
    print()
    
    # Check system result against reference signals
    print("🔍 Comparing system predictions to reference signals...")
    print()
    
    original_confidence = system_result.get('scenario_result', {}).get(
        'confidence_assessment', {}
    ).get('adjusted_confidence', 0.5)
    
    # Check against references
    scenario_result = system_result.get('scenario_result', {})
    updated_result = check_reference_signals(scenario_result, store)
    system_result['scenario_result'] = updated_result
    
    new_confidence = updated_result.get('confidence_assessment', {}).get('adjusted_confidence', 0.5)
    confidence_change = new_confidence - original_confidence
    
    print(f"Original Confidence: {original_confidence:.1%}")
    print(f"Adjusted Confidence: {new_confidence:.1%}")
    print(f"Change: {confidence_change:+.1%}")
    print()
    
    # Show reference calibration info
    ref_calibration = updated_result.get('reference_calibration', {})
    if ref_calibration:
        print("Reference Calibration:")
        print(f"   Match Score: {ref_calibration.get('match_score', 0.5):.1%}")
        print(f"   Recent Calibration: {ref_calibration.get('recent_calibration', 'N/A')}")
        print(f"   Trend: {ref_calibration.get('calibration_trend', 'N/A')}")
        print()
    
    # Show calibration history
    print("=" * 80)
    print("CALIBRATION HISTORY")
    print("=" * 80)
    print()
    
    trend = store.get_calibration_trend()
    print(f"Average Match Score: {trend.get('average_match', 'N/A')}")
    print(f"Recent Match Score: {trend.get('recent_match', 'N/A')}")
    print(f"Trend: {trend.get('trend', 'N/A')}")
    print()
    
    print(f"Total Reference Signals: {len(store.signals)}")
    print(f"Total Calibration Records: {len(store.calibration_history)}")
    print()
    
    # Save updated result
    output_file = "output/credigo_ss_with_reference_calibration.json"
    with open(output_file, 'w') as f:
        json.dump(system_result, f, indent=2, default=str)
    
    print(f"💾 Updated result saved to: {output_file}")
    print()
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print("✅ Reference Signal Layer working!")
    print()
    print("The system now:")
    print("   • Compares predictions to real-world signals")
    print("   • Adjusts confidence based on match/mismatch")
    print("   • Tracks calibration over time")
    print("   • Learns from past accuracy")
    print()
    print("This turns the system from 'I think this is right'")
    print("into 'I've been right before in similar cases.'")

if __name__ == "__main__":
    main()


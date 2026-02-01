"""
Test script for interpreter module.
"""

from dropsim_interpreter import (
    interpret_results,
    infer_failure_modes,
    detect_structural_patterns,
    synthesize_behavioral_narrative
)

def test_interpreter_basic():
    """Test basic interpreter functionality."""
    print("🧪 Testing interpreter...")
    
    # Create mock context graph
    context_graph = {
        'nodes': [
            {
                'step_id': 'Step 1',
                'total_entries': 1000,
                'drop_rate': 0.05,
                'avg_cognitive_energy': 0.8,
                'avg_perceived_risk': 0.2,
                'avg_perceived_effort': 0.3,
                'avg_perceived_value': 0.5,
                'avg_perceived_control': 0.6,
                'dominant_failure_factor': 'System 2 fatigue'
            },
            {
                'step_id': 'Step 2',
                'total_entries': 950,
                'drop_rate': 0.15,
                'avg_cognitive_energy': 0.6,
                'avg_perceived_risk': 0.4,
                'avg_perceived_effort': 0.5,
                'avg_perceived_value': 0.5,
                'avg_perceived_control': 0.6,
                'dominant_failure_factor': 'System 2 fatigue'
            },
            {
                'step_id': 'Step 3',
                'total_entries': 800,
                'drop_rate': 0.25,
                'avg_cognitive_energy': 0.4,
                'avg_perceived_risk': 0.5,
                'avg_perceived_effort': 0.6,
                'avg_perceived_value': 0.5,
                'avg_perceived_control': 0.6,
                'dominant_failure_factor': 'Loss aversion'
            }
        ],
        'edges': [
            {
                'from_step': 'Step 1',
                'to_step': 'Step 2',
                'avg_energy_delta': -0.2,
                'avg_risk_delta': 0.2,
                'avg_effort_delta': 0.2,
                'avg_value_delta': 0.0,
                'avg_control_delta': 0.0
            }
        ],
        'fragile_transitions': [
            {
                'step_id': 'Step 3',
                'drop_rate': 0.25
            },
            {
                'step_id': 'Step 2',
                'drop_rate': 0.15
            }
        ]
    }
    
    try:
        report = interpret_results(
            context_graph,
            calibration=None,
            counterfactuals=None,
            decision_results=None
        )
        
        print(f"✅ Interpreter successful!")
        print(f"   Root causes: {len(report.root_causes)}")
        print(f"   Structural patterns: {len(report.dominant_patterns)}")
        print(f"   Design shifts: {len(report.recommended_design_shifts)}")
        print()
        
        if report.root_causes:
            print(f"   Top root cause:")
            top = report.root_causes[0]
            print(f"     Step: {top.step_id}")
            print(f"     Failure mode: {top.dominant_failure_mode}")
            print(f"     Confidence: {top.confidence:.1%}")
            print(f"     Cause: {top.behavioral_cause}")
            print()
        
        if report.dominant_patterns:
            print(f"   Top pattern:")
            top_pattern = report.dominant_patterns[0]
            print(f"     Pattern: {top_pattern.pattern_name}")
            print(f"     Evidence: {', '.join(top_pattern.evidence)}")
            print(f"     Recommendation: {top_pattern.recommended_direction}")
            print()
        
        print(f"   Behavioral summary:")
        print(f"     {report.behavioral_summary}")
        print()
        
        if report.recommended_design_shifts:
            print(f"   Design shifts:")
            for shift in report.recommended_design_shifts[:3]:
                print(f"     • {shift}")
        
        return True
    except Exception as e:
        print(f"❌ Interpreter failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("INTERPRETER MODULE TEST")
    print("=" * 80)
    print()
    
    success = test_interpreter_basic()
    
    print()
    print("=" * 80)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Tests failed")
    print("=" * 80)


"""
Test script for decision engine.
"""

from dropsim_decision_engine import (
    generate_decision_report,
    DecisionCandidate,
    DecisionReport
)

def test_decision_engine_basic():
    """Test basic decision engine functionality."""
    print("🧪 Testing decision engine...")
    
    # Create mock calibration report
    calibration_report = {
        'calibration_score': 0.85,
        'stability_score': 0.90,
        'bias_summary': {
            'fatigue_bias': -0.12,  # Overestimated fatigue
            'effort_bias': 0.05,    # Slightly underestimated effort
            'risk_bias': 0.02,
            'trust_bias': -0.05
        },
        'step_metrics': [
            {
                'step_id': 'step_1',
                'predicted_drop_rate': 0.05,
                'observed_drop_rate': 0.08,
                'absolute_error': 0.03,
                'error_direction': 'overestimate'
            },
            {
                'step_id': 'step_2',
                'predicted_drop_rate': 0.15,
                'observed_drop_rate': 0.12,
                'absolute_error': 0.03,
                'error_direction': 'underestimate'
            },
            {
                'step_id': 'step_3',
                'predicted_drop_rate': 0.25,
                'observed_drop_rate': 0.25,
                'absolute_error': 0.00,
                'error_direction': 'accurate'
            }
        ]
    }
    
    # Create mock counterfactuals
    counterfactuals = {
        'top_interventions': [
            {
                'intervention': {
                    'type': 'step_modification',
                    'step_id': 'step_2',
                    'delta': {'effort': -0.2}
                },
                'outcome_change_rate': 0.35,
                'avg_effect_size': 2.1,
                'avg_sensitivity': 2.5
            },
            {
                'intervention': {
                    'type': 'step_modification',
                    'step_id': 'step_1',
                    'delta': {'risk': -0.15}
                },
                'outcome_change_rate': 0.20,
                'avg_effect_size': 1.8,
                'avg_sensitivity': 2.0
            }
        ],
        'sensitivity_map': {
            'effort_sensitivity': 0.42,
            'risk_sensitivity': 0.38,
            'cognitive_sensitivity': 0.31,
            'most_sensitive': 'effort'
        },
        'robustness_score': 0.82
    }
    
    # Create mock context graph
    context_graph = {
        'nodes': [
            {
                'step_id': 'step_1',
                'total_entries': 1000,
                'drop_rate': 0.05
            },
            {
                'step_id': 'step_2',
                'total_entries': 950,
                'drop_rate': 0.15
            },
            {
                'step_id': 'step_3',
                'total_entries': 800,
                'drop_rate': 0.25
            }
        ]
    }
    
    try:
        report = generate_decision_report(
            calibration_report,
            counterfactuals,
            context_graph,
            top_n=5
        )
        
        print(f"✅ Decision engine successful!")
        print(f"   Overall confidence: {report.overall_confidence:.3f}")
        print(f"   Total actions: {report.total_actions_evaluated}")
        print(f"   Top opportunity: {report.top_impact_opportunity}")
        print()
        print(f"   Recommended actions:")
        for i, action in enumerate(report.recommended_actions, 1):
            print(f"     {i}. {action.target_step} ({action.change_type})")
            print(f"        Impact: {action.estimated_impact:.1%}")
            print(f"        Confidence: {action.confidence:.1%}")
            print(f"        Priority: {action.priority_score:.3f}")
            print(f"        Rationale: {action.rationale[0] if action.rationale else 'N/A'}")
        
        return True
    except Exception as e:
        print(f"❌ Decision engine failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("DECISION ENGINE TEST")
    print("=" * 80)
    print()
    
    success = test_decision_engine_basic()
    
    print()
    print("=" * 80)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Tests failed")
    print("=" * 80)


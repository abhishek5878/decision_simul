"""
Test script for deployment guard.
"""
import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from dropsim_deployment_guard import (
    evaluate_deployment_candidate,
    DeploymentCandidate,
    DeploymentEvaluation,
    validate_all_recommendations
)

def test_deployment_guard_basic():
    """Test basic deployment guard functionality."""
    print("🧪 Testing deployment guard...")
    
    # Create mock decision candidate
    decision_candidate = {
        'action_id': 'step_2_reduce_effort',
        'target_step': 'step_2',
        'change_type': 'reduce_effort',
        'estimated_impact': 0.18,
        'confidence': 0.82,
        'affected_users': 950,
        'implementation_complexity': 1.0
    }
    
    # Create mock calibration data
    calibration_data = {
        'stability_score': 0.90,
        'calibration_score': 0.85
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
            }
        ],
        'robustness_score': 0.82
    }
    
    # Create mock context graph
    context_graph = {
        'nodes': [
            {
                'step_id': 'step_2',
                'total_entries': 950,
                'drop_rate': 0.15
            }
        ]
    }
    
    try:
        report = evaluate_deployment_candidate(
            decision_candidate,
            calibration_data,
            counterfactuals,
            context_graph,
            run_shadow=True
        )
        
        print(f"✅ Deployment guard successful!")
        print(f"   Recommendation: {report.evaluation.rollout_recommendation}")
        print(f"   Expected gain: {report.evaluation.expected_gain:.1%}")
        print(f"   Estimated risk: {report.evaluation.estimated_risk:.1%}")
        print(f"   Safety score: {report.evaluation.safety_score:.1%}")
        print(f"   Confidence interval: [{report.evaluation.confidence_interval[0]:.1%}, {report.evaluation.confidence_interval[1]:.1%}]")
        print()
        if report.evaluation.risk_factors:
            print(f"   Risk factors:")
            for factor in report.evaluation.risk_factors:
                print(f"     - {factor}")
        print()
        print(f"   Monitoring plan:")
        print(f"     Metrics: {report.monitoring_plan.metrics}")
        print(f"     Check interval: {report.monitoring_plan.check_interval_hours} hours")
        print(f"     Rollback conditions: {len(report.monitoring_plan.rollback_conditions)}")
        
        if report.shadow_evaluation_result:
            print()
            print(f"   Shadow evaluation:")
            print(f"     Counterfactual match: {report.shadow_evaluation_result.get('counterfactual_match', False)}")
            if 'outcome_change_rate' in report.shadow_evaluation_result:
                print(f"     Outcome change rate: {report.shadow_evaluation_result['outcome_change_rate']:.1%}")
        
        return True
    except Exception as e:
        print(f"❌ Deployment guard failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_validate_all_recommendations():
    """Test validation of all recommendations."""
    print("\n🧪 Testing validate_all_recommendations...")
    
    # Create mock decision report
    decision_report = {
        'recommended_actions': [
            {
                'action_id': 'step_1_reduce_risk',
                'target_step': 'step_1',
                'change_type': 'reduce_risk',
                'estimated_impact': 0.10,
                'confidence': 0.75,
                'affected_users': 1000,
                'implementation_complexity': 1.5
            },
            {
                'action_id': 'step_2_reduce_effort',
                'target_step': 'step_2',
                'change_type': 'reduce_effort',
                'estimated_impact': 0.18,
                'confidence': 0.82,
                'affected_users': 950,
                'implementation_complexity': 1.0
            }
        ]
    }
    
    calibration_data = {
        'stability_score': 0.90,
        'calibration_score': 0.85
    }
    
    counterfactuals = {
        'robustness_score': 0.82
    }
    
    try:
        reports = validate_all_recommendations(
            decision_report,
            calibration_data,
            counterfactuals,
            None
        )
        
        print(f"✅ Validation successful!")
        print(f"   Validated {len(reports)} recommendations")
        for i, report in enumerate(reports, 1):
            print(f"   {i}. {report.candidate.target_step}: {report.evaluation.rollout_recommendation}")
        
        return True
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("DEPLOYMENT GUARD TEST")
    print("=" * 80)
    print()
    
    success1 = test_deployment_guard_basic()
    success2 = test_validate_all_recommendations()
    
    print()
    print("=" * 80)
    if success1 and success2:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
    print("=" * 80)


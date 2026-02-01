"""
Test script for calibration module.
"""
import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from dropsim_calibration import (
    run_calibration,
    ObservedOutcomes,
    CalibrationReport,
    CalibrationHistory,
    update_calibration_history
)
from dropsim_context_graph import ContextGraph, StepNode, EdgeStats

def test_calibration_basic():
    """Test basic calibration functionality."""
    print("🧪 Testing basic calibration...")
    
    # Create mock simulation results
    simulation_results = {
        'aggregated_results': {
            'step_results': [
                {
                    'step_id': 'step_1',
                    'failure_rate': 0.05,  # 5% predicted drop
                    'failure_count': 50
                },
                {
                    'step_id': 'step_2',
                    'failure_rate': 0.15,  # 15% predicted drop
                    'failure_count': 150
                },
                {
                    'step_id': 'step_3',
                    'failure_rate': 0.25,  # 25% predicted drop
                    'failure_count': 250
                }
            ]
        }
    }
    
    # Create mock observed outcomes
    observed_metrics = ObservedOutcomes(
        step_drop_rates={
            'step_1': 0.08,  # 8% observed (overestimated by 3%)
            'step_2': 0.12,  # 12% observed (underestimated by 3%)
            'step_3': 0.25   # 25% observed (accurate)
        },
        overall_completion_rate=0.55,
        sample_size=1000
    )
    
    try:
        report = run_calibration(
            simulation_results,
            observed_metrics,
            context_graph=None,
            product_steps=None
        )
        
        print(f"✅ Calibration successful!")
        print(f"   Calibration score: {report.calibration_score:.3f}")
        print(f"   Stability score: {report.stability_score:.3f}")
        print(f"   Dominant biases: {report.dominant_biases}")
        print(f"   Stable factors: {report.stable_factors}")
        print()
        print(f"   Step metrics:")
        for metric in report.step_metrics:
            print(f"     {metric.step_id}:")
            print(f"       Predicted: {metric.predicted_drop_rate:.3f}")
            print(f"       Observed: {metric.observed_drop_rate:.3f}")
            print(f"       Error: {metric.absolute_error:.3f} ({metric.error_direction})")
        
        return True
    except Exception as e:
        print(f"❌ Calibration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_calibration_history():
    """Test calibration history tracking."""
    print("\n🧪 Testing calibration history...")
    
    # Create a mock report
    from dropsim_calibration import BiasSummary, StepCalibrationMetrics
    
    bias_summary = BiasSummary(
        fatigue_bias=-0.05,
        effort_bias=0.02,
        risk_bias=0.01,
        trust_bias=-0.03,
        early_step_bias=-0.04,
        late_step_bias=0.02
    )
    
    step_metrics = [
        StepCalibrationMetrics(
            step_id='step_1',
            predicted_drop_rate=0.05,
            observed_drop_rate=0.08,
            absolute_error=0.03,
            relative_error=0.375,
            error_direction='overestimate',
            bias_magnitude=0.06
        )
    ]
    
    report = CalibrationReport(
        calibration_score=0.85,
        step_metrics=step_metrics,
        bias_summary=bias_summary,
        confidence_adjusted_predictions={'step_1': 0.08},
        stability_score=0.90,
        timestamp='2024-01-01T00:00:00',
        dominant_biases=['overestimated_fatigue'],
        stable_factors=['effort', 'risk']
    )
    
    try:
        # Test history update
        history = update_calibration_history(
            'test_calibration_history.json',
            report
        )
        
        print(f"✅ History update successful!")
        print(f"   History entries: {len(history.history)}")
        
        # Test trend analysis
        if len(history.history) >= 2:
            trend = history.get_trend()
            print(f"   Trend: {trend.get('trend', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"❌ History test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("CALIBRATION MODULE TEST")
    print("=" * 80)
    print()
    
    success1 = test_calibration_basic()
    success2 = test_calibration_history()
    
    print()
    print("=" * 80)
    if success1 and success2:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
    print("=" * 80)


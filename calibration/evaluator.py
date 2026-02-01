"""
evaluator.py - Main Evaluation Module

Ties together confidence estimation, sensitivity analysis, prediction intervals,
and stability metrics to provide comprehensive evaluation of model reliability.
"""

import json
from typing import Dict, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime

from calibration.confidence_estimation import (
    estimate_confidence_intervals,
    estimate_step_level_confidence,
    ConfidenceEstimate
)
from calibration.sensitivity_analysis import (
    analyze_all_parameter_sensitivities,
    compute_sensitivity_summary,
    SensitivityResult
)
from calibration.prediction_intervals import (
    get_prediction_interval,
    get_prediction_intervals_for_steps,
    PredictionInterval
)
from calibration.stability_metrics import (
    assess_stability,
    compute_aggregate_stability,
    StabilityAssessment
)
from calibration.parameter_space import get_default_parameters


@dataclass
class EvaluationReport:
    """Complete evaluation report."""
    timestamp: str
    overall_confidence: ConfidenceEstimate
    overall_stability: StabilityAssessment
    overall_prediction_interval: PredictionInterval
    step_confidence: Dict[str, ConfidenceEstimate]
    step_prediction_intervals: Dict[str, PredictionInterval]
    parameter_sensitivity: Dict[str, SensitivityResult]
    sensitivity_summary: Dict[str, float]  # parameter_name -> relative_sensitivity
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'timestamp': self.timestamp,
            'overall_confidence': self.overall_confidence.to_dict(),
            'overall_stability': self.overall_stability.to_dict(),
            'overall_prediction_interval': self.overall_prediction_interval.to_dict(),
            'step_confidence': {
                step_name: est.to_dict()
                for step_name, est in self.step_confidence.items()
            },
            'step_prediction_intervals': {
                step_name: interval.to_dict()
                for step_name, interval in self.step_prediction_intervals.items()
            },
            'parameter_sensitivity': {
                param_name: result.to_dict()
                for param_name, result in self.parameter_sensitivity.items()
            },
            'sensitivity_summary': {
                param_name: float(sens)
                for param_name, sens in self.sensitivity_summary.items()
            }
        }


def evaluate_model(
    simulation_function: Callable,
    simulation_args: Dict,
    product_steps: Dict,
    baseline_parameters: Optional[Dict[str, float]] = None,
    n_stochastic_runs: int = 50,
    sensitivity_variation_pct: float = 0.20,
    confidence_level: float = 0.90,
    engine_module: str = 'behavioral_engine_improved',
    parameter_subset: Optional[list] = None,
    verbose: bool = True
) -> EvaluationReport:
    """
    Run comprehensive model evaluation.
    
    Args:
        simulation_function: Function to run simulation
        simulation_args: Arguments for simulation function
        product_steps: Dict of step definitions
        baseline_parameters: Baseline parameters (if None, use defaults)
        n_stochastic_runs: Number of stochastic simulations for confidence estimation
        sensitivity_variation_pct: Percentage variation for sensitivity analysis (0.20 = ±20%)
        confidence_level: Confidence level for prediction intervals (0.90 = 90%)
        engine_module: Engine module to use
        parameter_subset: Optional list of parameters to analyze (if None, analyze all)
        verbose: Print progress
    
    Returns:
        EvaluationReport with all evaluation metrics
    """
    if baseline_parameters is None:
        baseline_parameters = get_default_parameters()
    
    if verbose:
        print("=" * 80)
        print("MODEL EVALUATION: Starting Comprehensive Analysis")
        print("=" * 80)
    
    # 1. Confidence Interval Estimation
    if verbose:
        print("\n1. Estimating confidence intervals...")
    
    overall_confidence = estimate_confidence_intervals(
        simulation_function,
        simulation_args,
        n_simulations=n_stochastic_runs,
        product_steps=product_steps,
        verbose=verbose
    )
    
    step_confidence = estimate_step_level_confidence(
        simulation_function,
        simulation_args,
        product_steps,
        n_simulations=n_stochastic_runs,
        verbose=verbose
    )
    
    # 2. Stability Assessment
    if verbose:
        print("\n2. Assessing stability...")
    
    overall_stability = assess_stability(overall_confidence)
    aggregate_step_stability = compute_aggregate_stability(step_confidence)
    
    if verbose:
        print(f"   Overall stability: {overall_stability.stability_score:.4f} ({overall_stability.interpretation})")
        print(f"   Step-level stability: {aggregate_step_stability.stability_score:.4f} ({aggregate_step_stability.interpretation})")
    
    # 3. Prediction Intervals
    if verbose:
        print("\n3. Computing prediction intervals...")
    
    overall_prediction_interval = get_prediction_interval(
        overall_confidence,
        confidence=confidence_level
    )
    
    step_prediction_intervals = get_prediction_intervals_for_steps(
        step_confidence,
        confidence=confidence_level
    )
    
    if verbose:
        print(f"   Overall {confidence_level*100:.0f}% prediction interval: "
              f"[{overall_prediction_interval.lower_bound:.4f}, {overall_prediction_interval.upper_bound:.4f}]")
        print(f"   Median: {overall_prediction_interval.median:.4f}")
    
    # 4. Sensitivity Analysis
    if verbose:
        print("\n4. Running sensitivity analysis...")
    
    parameter_sensitivity = analyze_all_parameter_sensitivities(
        baseline_parameters,
        simulation_function,
        simulation_args,
        product_steps,
        variation_pct=sensitivity_variation_pct,
        engine_module=engine_module,
        parameter_subset=parameter_subset,
        verbose=verbose
    )
    
    sensitivity_summary = compute_sensitivity_summary(parameter_sensitivity)
    
    if verbose:
        print("\n" + "=" * 80)
        print("EVALUATION: Complete")
        print("=" * 80)
        print(f"\nKey Findings:")
        print(f"  Stability Score: {overall_stability.stability_score:.4f} ({overall_stability.interpretation})")
        print(f"  Mean Completion: {overall_confidence.mean_completion:.2%}")
        print(f"  {confidence_level*100:.0f}% Prediction Interval: "
              f"[{overall_prediction_interval.lower_bound:.2%}, {overall_prediction_interval.upper_bound:.2%}]")
        print(f"\nMost Sensitive Parameters:")
        sorted_sensitivity = sorted(sensitivity_summary.items(), key=lambda x: x[1], reverse=True)
        for param_name, sens in sorted_sensitivity[:3]:
            print(f"  {param_name}: {sens:.4f}")
        print("=" * 80)
    
    return EvaluationReport(
        timestamp=datetime.now().isoformat(),
        overall_confidence=overall_confidence,
        overall_stability=overall_stability,
        overall_prediction_interval=overall_prediction_interval,
        step_confidence=step_confidence,
        step_prediction_intervals=step_prediction_intervals,
        parameter_sensitivity=parameter_sensitivity,
        sensitivity_summary=sensitivity_summary
    )


def export_evaluation_report(
    report: EvaluationReport,
    output_file: str = 'evaluation_report.json'
):
    """Export evaluation report to JSON file."""
    report_dict = report.to_dict()
    
    with open(output_file, 'w') as f:
        json.dump(report_dict, f, indent=2)
    
    return report_dict


def export_calibration_report(
    report: EvaluationReport,
    output_file: str = 'calibration_report.json'
):
    """
    Export calibration-focused report (subset of full evaluation).
    
    Includes: confidence intervals, stability, prediction intervals.
    """
    calibration_dict = {
        'timestamp': report.timestamp,
        'overall_confidence': report.overall_confidence.to_dict(),
        'overall_stability': report.overall_stability.to_dict(),
        'overall_prediction_interval': report.overall_prediction_interval.to_dict(),
        'step_confidence': {
            step_name: est.to_dict()
            for step_name, est in report.step_confidence.items()
        },
        'step_prediction_intervals': {
            step_name: interval.to_dict()
            for step_name, interval in report.step_prediction_intervals.items()
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(calibration_dict, f, indent=2)
    
    return calibration_dict


def export_sensitivity_report(
    report: EvaluationReport,
    output_file: str = 'sensitivity_report.json'
):
    """
    Export sensitivity-focused report.
    
    Includes: parameter sensitivity rankings and impact analysis.
    """
    sensitivity_dict = {
        'timestamp': report.timestamp,
        'parameter_sensitivity': {
            param_name: result.to_dict()
            for param_name, result in report.parameter_sensitivity.items()
        },
        'sensitivity_summary': report.sensitivity_summary,
        'ranked_by_sensitivity': [
            {
                'parameter_name': param_name,
                'relative_sensitivity': float(sens),
                'rank': report.parameter_sensitivity[param_name].impact_rank
            }
            for param_name, sens in sorted(
                report.sensitivity_summary.items(),
                key=lambda x: x[1],
                reverse=True
            )
        ]
    }
    
    with open(output_file, 'w') as f:
        json.dump(sensitivity_dict, f, indent=2)
    
    return sensitivity_dict


def export_confidence_intervals(
    report: EvaluationReport,
    output_file: str = 'confidence_intervals.json'
):
    """
    Export confidence intervals report.
    
    Includes: prediction intervals for overall and step-level metrics.
    """
    intervals_dict = {
        'timestamp': report.timestamp,
        'overall_prediction_interval': report.overall_prediction_interval.to_dict(),
        'overall_confidence': report.overall_confidence.to_dict(),
        'step_prediction_intervals': {
            step_name: interval.to_dict()
            for step_name, interval in report.step_prediction_intervals.items()
        },
        'step_confidence': {
            step_name: est.to_dict()
            for step_name, est in report.step_confidence.items()
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(intervals_dict, f, indent=2)
    
    return intervals_dict


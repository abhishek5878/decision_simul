"""
calibration - Long-term Calibration Layer for Behavioral Simulation

Converts hand-tuned simulator into data-grounded, self-correcting model.
Calibrates parameters only - does not modify behavioral logic.
"""

from calibration.parameter_space import (
    PARAMETER_SPACE,
    get_default_parameters,
    validate_parameters,
    sample_random_parameters,
    get_parameter_bounds,
    describe_parameters
)

from calibration.loss_functions import (
    compute_composite_loss,
    extract_simulated_metrics_from_results,
    compute_completion_rate_error,
    compute_step_dropoff_mse,
    compute_avg_steps_completed_error
)

from calibration.optimizer import (
    random_search_optimize,
    grid_search_optimize,
    bayesian_optimize,
    OptimizationResult
)

from calibration.validation import (
    validate_all,
    validate_probability_bounds,
    validate_monotonicity,
    validate_overfitting_penalty,
    validate_parameter_dominance,
    compute_confidence_intervals,
    ValidationError
)

from calibration.calibrator import (
    CalibrationConfig,
    CalibrationResult,
    calibrate_parameters,
    run_simulation_with_parameters,
    inject_parameters_into_engine,
    export_calibration_result
)

from calibration.confidence_estimation import (
    ConfidenceEstimate,
    estimate_confidence_intervals,
    estimate_step_level_confidence,
    run_stochastic_simulations
)

from calibration.sensitivity_analysis import (
    SensitivityResult,
    analyze_parameter_sensitivity,
    analyze_all_parameter_sensitivities,
    compute_sensitivity_summary
)

from calibration.prediction_intervals import (
    PredictionInterval,
    get_prediction_interval,
    get_prediction_interval_simple,
    get_prediction_intervals_for_steps
)

from calibration.stability_metrics import (
    StabilityAssessment,
    compute_stability_score,
    interpret_stability_score,
    assess_stability,
    compute_aggregate_stability
)

from calibration.evaluator import (
    EvaluationReport,
    evaluate_model,
    export_evaluation_report,
    export_calibration_report,
    export_sensitivity_report,
    export_confidence_intervals
)

from calibration.real_world_calibration import (
    ObservedFunnelData,
    CalibrationSummary,
    CalibrationDiagnostics,
    calibrate_to_real_data,
    compute_funnel_error,
    export_calibration_summary,
    export_calibration_diagnostics,
    log_parameter_changes,
    CALIBRATABLE_PARAMETERS
)

from calibration.drift_metrics import (
    DriftSeverity,
    DriftMetric,
    DriftSummary,
    detect_entry_rate_drift,
    detect_completion_rate_drift,
    detect_total_conversion_drift,
    detect_step_level_drift,
    detect_parameter_drift,
    detect_distribution_drift,
    summarize_drift
)

from calibration.model_health_monitor import (
    ModelBaseline,
    CurrentModelState,
    DriftReport,
    ModelHealthMonitor
)

__all__ = [
    # Parameter space
    'PARAMETER_SPACE',
    'get_default_parameters',
    'validate_parameters',
    'sample_random_parameters',
    'get_parameter_bounds',
    'describe_parameters',
    
    # Loss functions
    'compute_composite_loss',
    'extract_simulated_metrics_from_results',
    'compute_completion_rate_error',
    'compute_step_dropoff_mse',
    'compute_avg_steps_completed_error',
    
    # Optimizer
    'random_search_optimize',
    'grid_search_optimize',
    'bayesian_optimize',
    'OptimizationResult',
    
    # Validation
    'validate_all',
    'validate_probability_bounds',
    'validate_monotonicity',
    'validate_overfitting_penalty',
    'validate_parameter_dominance',
    'compute_confidence_intervals',
    'ValidationError',
    
    # Main calibrator
    'CalibrationConfig',
    'CalibrationResult',
    'calibrate_parameters',
    'run_simulation_with_parameters',
    'inject_parameters_into_engine',
    'export_calibration_result',
    
    # Confidence estimation
    'ConfidenceEstimate',
    'estimate_confidence_intervals',
    'estimate_step_level_confidence',
    'run_stochastic_simulations',
    
    # Sensitivity analysis
    'SensitivityResult',
    'analyze_parameter_sensitivity',
    'analyze_all_parameter_sensitivities',
    'compute_sensitivity_summary',
    
    # Prediction intervals
    'PredictionInterval',
    'get_prediction_interval',
    'get_prediction_interval_simple',
    'get_prediction_intervals_for_steps',
    
    # Stability metrics
    'StabilityAssessment',
    'compute_stability_score',
    'interpret_stability_score',
    'assess_stability',
    'compute_aggregate_stability',
    
    # Main evaluator
    'EvaluationReport',
    'evaluate_model',
    'export_evaluation_report',
    'export_calibration_report',
    'export_sensitivity_report',
    'export_confidence_intervals',
    
    # Real-world calibration
    'ObservedFunnelData',
    'CalibrationSummary',
    'CalibrationDiagnostics',
    'calibrate_to_real_data',
    'compute_funnel_error',
    'export_calibration_summary',
    'export_calibration_diagnostics',
    'log_parameter_changes',
    'CALIBRATABLE_PARAMETERS',
    
    # Drift monitoring
    'DriftSeverity',
    'DriftMetric',
    'DriftSummary',
    'detect_entry_rate_drift',
    'detect_completion_rate_drift',
    'detect_total_conversion_drift',
    'detect_step_level_drift',
    'detect_parameter_drift',
    'detect_distribution_drift',
    'summarize_drift',
    'ModelBaseline',
    'CurrentModelState',
    'DriftReport',
    'ModelHealthMonitor'
]


"""
validation.py - Validation and Guardrails for Calibrated Parameters

Ensures calibrated parameters maintain model integrity and interpretability.
"""

from typing import Dict, List, Tuple, Optional
import numpy as np
from calibration.parameter_space import PARAMETER_SPACE, validate_parameters


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


def validate_probability_bounds(
    parameters: Dict[str, float],
    simulated_metrics: Optional[Dict] = None
) -> Tuple[bool, List[str]]:
    """
    Validate that probabilities remain within [0.05, 0.95] bounds.
    
    Args:
        parameters: Calibrated parameters
        simulated_metrics: Optional simulated metrics to check actual probabilities
    
    Returns:
        (is_valid, list of error messages)
    """
    errors = []
    
    # Check parameter bounds
    base_completion = parameters.get('BASE_COMPLETION_RATE', 0.60)
    if base_completion < 0.05 or base_completion > 0.95:
        errors.append(f"BASE_COMPLETION_RATE {base_completion:.4f} outside [0.05, 0.95]")
    
    # Check if simulated probabilities are within bounds
    if simulated_metrics:
        completion_rate = simulated_metrics.get('completion_rate', 0.0)
        if completion_rate < 0.05 or completion_rate > 0.95:
            errors.append(f"Simulated completion rate {completion_rate:.4f} outside [0.05, 0.95]")
        
        # Check step dropoff rates (should be 0-1, but completion should be reasonable)
        dropoff_by_step = simulated_metrics.get('dropoff_by_step', {})
        for step_name, drop_rate in dropoff_by_step.items():
            if drop_rate < 0.0 or drop_rate > 1.0:
                errors.append(f"Step '{step_name}' drop rate {drop_rate:.4f} outside [0, 1]")
    
    return len(errors) == 0, errors


def validate_monotonicity(
    parameters: Dict[str, float],
    simulated_metrics: Optional[Dict] = None
) -> Tuple[bool, List[str]]:
    """
    Validate monotonicity constraints:
    - More friction → lower completion
    - Higher persistence bonus → higher completion
    
    Args:
        parameters: Calibrated parameters
        simulated_metrics: Optional simulated metrics
    
    Returns:
        (is_valid, list of warnings)
    """
    warnings = []
    
    # Check friction penalty weight
    friction_weight = parameters.get('FRICTION_PENALTY_WEIGHT', 1.0)
    if friction_weight < 0:
        warnings.append("FRICTION_PENALTY_WEIGHT is negative (would increase completion with friction)")
    
    # Check persistence bonuses
    persistence_start = parameters.get('PERSISTENCE_BONUS_START', 0.18)
    persistence_rate = parameters.get('PERSISTENCE_BONUS_RATE', 0.22)
    
    if persistence_start < 0 or persistence_rate < 0:
        warnings.append("Persistence bonuses are negative (would reduce completion)")
    
    # If we have simulated metrics, check basic sanity
    if simulated_metrics:
        completion_rate = simulated_metrics.get('completion_rate', 0.0)
        
        # Very high friction weight should correlate with lower completion (if we had friction data)
        # This is a heuristic check - in practice, we'd need step-level friction data
        
        pass  # Placeholder for more sophisticated checks
    
    return len(warnings) == 0, warnings


def validate_overfitting_penalty(
    simulated_metrics: Dict,
    observed_metrics: Dict,
    threshold: float = 0.001
) -> Tuple[bool, float, str]:
    """
    Check if model is overfitting (too sharp/perfect match).
    
    Perfect matches are suspicious - may indicate overfitting.
    
    Args:
        simulated_metrics: Simulated metrics
        observed_metrics: Observed metrics
        threshold: Minimum expected error (below this is suspicious)
    
    Returns:
        (is_valid, error_magnitude, message)
    """
    completion_error = abs(
        simulated_metrics.get('completion_rate', 0.0) -
        observed_metrics.get('completion_rate', 0.0)
    )
    
    # Compute average step error
    sim_dropoff = simulated_metrics.get('dropoff_by_step', {})
    obs_dropoff = observed_metrics.get('dropoff_by_step', {})
    all_steps = set(sim_dropoff.keys()) | set(obs_dropoff.keys())
    
    step_errors = []
    for step_name in all_steps:
        sim_rate = sim_dropoff.get(step_name, 0.0)
        obs_rate = obs_dropoff.get(step_name, 0.0)
        step_errors.append(abs(sim_rate - obs_rate))
    
    avg_step_error = np.mean(step_errors) if step_errors else 0.0
    total_error = (completion_error + avg_step_error) / 2.0
    
    if total_error < threshold:
        return False, total_error, f"Suspiciously low error {total_error:.6f} < {threshold} (possible overfitting)"
    
    return True, total_error, f"Error {total_error:.6f} is reasonable"


def validate_parameter_dominance(
    parameters: Dict[str, float],
    default_parameters: Dict[str, float],
    max_change_factor: float = 3.0
) -> Tuple[bool, List[str]]:
    """
    Ensure no single parameter dominates (changed too much from default).
    
    Args:
        parameters: Calibrated parameters
        default_parameters: Default parameter values
        max_change_factor: Maximum allowed change (e.g., 3.0 = 3x default)
    
    Returns:
        (is_valid, list of warnings)
    """
    warnings = []
    
    for param_name, calibrated_value in parameters.items():
        if param_name not in default_parameters:
            continue
        
        default_value = default_parameters[param_name]
        if default_value == 0:
            # Skip zero defaults (can't compute ratio)
            continue
        
        change_factor = abs(calibrated_value / default_value)
        if change_factor > max_change_factor:
            warnings.append(
                f"{param_name} changed by {change_factor:.2f}x from default "
                f"({default_value:.4f} -> {calibrated_value:.4f})"
            )
    
    return len(warnings) == 0, warnings


def validate_all(
    parameters: Dict[str, float],
    simulated_metrics: Optional[Dict] = None,
    observed_metrics: Optional[Dict] = None,
    default_parameters: Optional[Dict[str, float]] = None,
    strict: bool = False
) -> Dict:
    """
    Run all validation checks.
    
    Args:
        parameters: Calibrated parameters to validate
        simulated_metrics: Optional simulated metrics
        observed_metrics: Optional observed metrics (for overfitting check)
        default_parameters: Optional default parameters (for dominance check)
        strict: If True, raise ValidationError on failures
    
    Returns:
        Dict with validation results:
            - is_valid: bool
            - errors: List[str]
            - warnings: List[str]
            - checks: Dict with individual check results
    """
    from calibration.parameter_space import get_default_parameters
    
    if default_parameters is None:
        default_parameters = get_default_parameters()
    
    # Validate bounds
    prob_valid, prob_errors = validate_probability_bounds(parameters, simulated_metrics)
    
    # Validate monotonicity
    mono_valid, mono_warnings = validate_monotonicity(parameters, simulated_metrics)
    
    # Validate overfitting
    overfitting_valid = True
    overfitting_error = 0.0
    overfitting_message = "N/A (no observed metrics)"
    if simulated_metrics and observed_metrics:
        overfitting_valid, overfitting_error, overfitting_message = validate_overfitting_penalty(
            simulated_metrics, observed_metrics
        )
    
    # Validate parameter dominance
    dominance_valid, dominance_warnings = validate_parameter_dominance(
        parameters, default_parameters
    )
    
    # Collect all errors and warnings
    all_errors = prob_errors
    if not overfitting_valid:
        all_errors.append(overfitting_message)
    
    all_warnings = mono_warnings + dominance_warnings
    
    is_valid = prob_valid and overfitting_valid and (not strict or len(all_warnings) == 0)
    
    result = {
        'is_valid': is_valid,
        'errors': all_errors,
        'warnings': all_warnings,
        'checks': {
            'probability_bounds': {
                'valid': prob_valid,
                'errors': prob_errors
            },
            'monotonicity': {
                'valid': mono_valid,
                'warnings': mono_warnings
            },
            'overfitting': {
                'valid': overfitting_valid,
                'error': overfitting_error,
                'message': overfitting_message
            },
            'parameter_dominance': {
                'valid': dominance_valid,
                'warnings': dominance_warnings
            }
        }
    }
    
    if strict and not is_valid:
        error_msg = "Validation failed:\n" + "\n".join(all_errors)
        if all_warnings:
            error_msg += "\nWarnings:\n" + "\n".join(all_warnings)
        raise ValidationError(error_msg)
    
    return result


def compute_confidence_intervals(
    optimization_history: List[Dict],
    percentile: float = 0.95
) -> Dict[str, Tuple[float, float]]:
    """
    Compute confidence intervals for parameters from optimization history.
    
    Uses distribution of top-performing parameter sets.
    
    Args:
        optimization_history: List of {parameters, loss, ...} dicts
        percentile: Percentile for confidence interval (0.95 = 95% CI)
    
    Returns:
        Dict mapping parameter_name -> (lower_bound, upper_bound)
    """
    if not optimization_history:
        return {}
    
    # Sort by loss (lower is better)
    sorted_history = sorted(optimization_history, key=lambda x: x.get('loss', float('inf')))
    
    # Take top 10% of results
    top_n = max(1, int(len(sorted_history) * 0.1))
    top_results = sorted_history[:top_n]
    
    # Extract parameter values
    param_values = {}
    for result in top_results:
        params = result.get('parameters', {})
        for param_name, param_value in params.items():
            if param_name not in param_values:
                param_values[param_name] = []
            param_values[param_name].append(param_value)
    
    # Compute percentiles
    alpha = (1.0 - percentile) / 2.0
    lower_percentile = alpha * 100
    upper_percentile = (1.0 - alpha) * 100
    
    confidence_intervals = {}
    for param_name, values in param_values.items():
        lower = np.percentile(values, lower_percentile)
        upper = np.percentile(values, upper_percentile)
        confidence_intervals[param_name] = (float(lower), float(upper))
    
    return confidence_intervals


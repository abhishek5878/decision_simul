"""
real_world_calibration.py - Real-World Data Calibration

Calibrates model parameters to match observed funnel data from real users.
This converts the system from theoretically calibrated to empirically grounded.
"""

import numpy as np
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict

from calibration.parameter_space import (
    PARAMETER_SPACE,
    get_default_parameters,
    validate_parameters
)
from calibration.loss_functions import extract_simulated_metrics_from_results
from calibration.calibrator import run_simulation_with_parameters
from entry_model.funnel_integration import compute_full_funnel_prediction


@dataclass
class ObservedFunnelData:
    """Observed funnel data from real users."""
    entry_count: int  # Total visitors/impressions
    step_completions: Dict[str, int]  # step_name -> number who completed this step
    total_completions: int  # Number who completed entire funnel
    entry_probability: Optional[float] = None  # Observed P(entry) if known
    step_completion_rates: Optional[Dict[str, float]] = None  # step_name -> completion rate
    
    def compute_rates(self) -> Dict:
        """Compute rates from counts."""
        rates = {}
        
        if self.entry_count > 0:
            rates['entry_rate'] = self.total_completions / self.entry_count if self.entry_count > 0 else 0.0
            
            # Step completion rates (conditional on entry)
            # Need to compute cumulative: how many reached each step
            step_names = list(self.step_completions.keys())
            step_counts = [self.step_completions[step] for step in step_names]
            
            # Entry count (those who entered)
            # If we don't have entry count, estimate from first step
            if len(step_counts) > 0:
                entries = step_counts[0]  # First step count = entries
                rates['entry_rate'] = entries / self.entry_count if self.entry_count > 0 else 0.0
                
                # Step completion rates (conditional on reaching that step)
                for i, step_name in enumerate(step_names):
                    if i == 0:
                        # First step: completion rate = entries / total visitors
                        rates[step_name] = entries / self.entry_count if self.entry_count > 0 else 0.0
                    else:
                        # Later steps: completion rate = completions / previous step completions
                        prev_count = step_counts[i-1] if i > 0 else entries
                        curr_count = step_counts[i]
                        rates[step_name] = curr_count / prev_count if prev_count > 0 else 0.0
        
        return rates
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        rates = self.compute_rates()
        return {
            'entry_count': self.entry_count,
            'step_completions': self.step_completions,
            'total_completions': self.total_completions,
            'computed_rates': rates
        }


@dataclass
class CalibrationSummary:
    """Summary of calibration results."""
    before_error: float  # Mean absolute error before calibration
    after_error: float  # Mean absolute error after calibration
    improvement_pct: float  # Percentage improvement
    calibrated_parameters: Dict[str, float]  # Optimized parameters
    default_parameters: Dict[str, float]  # Original parameters
    parameter_changes: Dict[str, float]  # Change from default
    confidence_ranges: Dict[str, Tuple[float, float]]  # Confidence intervals
    fit_score: float  # Overall fit quality [0, 1]
    timestamp: str
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'before_error': float(self.before_error),
            'after_error': float(self.after_error),
            'improvement_pct': float(self.improvement_pct),
            'calibrated_parameters': {k: float(v) for k, v in self.calibrated_parameters.items()},
            'default_parameters': {k: float(v) for k, v in self.default_parameters.items()},
            'parameter_changes': {k: float(v) for k, v in self.parameter_changes.items()},
            'confidence_ranges': {
                k: [float(bounds[0]), float(bounds[1])]
                for k, bounds in self.confidence_ranges.items()
            },
            'fit_score': float(self.fit_score),
            'timestamp': self.timestamp
        }


@dataclass
class CalibrationDiagnostics:
    """Detailed calibration diagnostics."""
    per_step_errors_before: Dict[str, float]  # step_name -> error before
    per_step_errors_after: Dict[str, float]  # step_name -> error after
    parameter_sensitivity: Dict[str, float]  # parameter -> sensitivity score
    regularization_penalty: float  # Regularization term value
    optimization_history: List[Dict]  # Optimization iterations
    convergence_reason: str
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'per_step_errors_before': {k: float(v) for k, v in self.per_step_errors_before.items()},
            'per_step_errors_after': {k: float(v) for k, v in self.per_step_errors_after.items()},
            'parameter_sensitivity': {k: float(v) for k, v in self.parameter_sensitivity.items()},
            'regularization_penalty': float(self.regularization_penalty),
            'optimization_history': self.optimization_history,
            'convergence_reason': self.convergence_reason
        }


# ============================================================================
# CALIBRATABLE PARAMETERS (Limited Set)
# ============================================================================

CALIBRATABLE_PARAMETERS = {
    'BASE_COMPLETION_RATE': {
        'default': 0.60,
        'bounds': (0.05, 0.90),
        'description': 'Base completion probability floor'
    },
    'PERSISTENCE_BONUS_START': {
        'default': 0.18,
        'bounds': (0.0, 0.40),
        'description': 'Persistence bonus at start'
    },
    'PERSISTENCE_BONUS_RATE': {
        'default': 0.22,
        'bounds': (0.0, 0.50),
        'description': 'Persistence bonus rate increase'
    },
    'INTENT_PENALTY_WEIGHT': {
        'default': 0.025,
        'bounds': (0.0, 0.15),
        'description': 'Intent penalty weight'
    },
    'ENTRY_PROBABILITY_SCALE': {
        'default': 1.0,
        'bounds': (0.5, 2.0),
        'description': 'Entry probability scaling factor'
    }
}


# ============================================================================
# ERROR COMPUTATION
# ============================================================================

def compute_funnel_error(
    observed: ObservedFunnelData,
    simulated_metrics: Dict,
    entry_probability: Optional[float] = None
) -> Dict[str, float]:
    """
    Compute error between observed and simulated funnel data.
    
    Args:
        observed: Observed funnel data
        simulated_metrics: Simulated metrics from behavioral engine
        entry_probability: Optional entry probability from entry model
    
    Returns:
        Dict with error metrics
    """
    errors = {}
    
    # Overall completion rate error
    observed_rates = observed.compute_rates()
    observed_completion = observed_rates.get('entry_rate', 0.0)
    
    if entry_probability is not None:
        # Full funnel: entry × completion
        simulated_completion = simulated_metrics.get('completion_rate', 0.0)
        simulated_total = entry_probability * simulated_completion
        errors['total_conversion_error'] = abs(simulated_total - observed_completion)
    else:
        # Just behavioral completion
        simulated_completion = simulated_metrics.get('completion_rate', 0.0)
        errors['completion_rate_error'] = abs(simulated_completion - observed_completion)
    
    # Step-level errors
    step_errors = {}
    dropoff_by_step = simulated_metrics.get('dropoff_by_step', {})
    
    for step_name, observed_count in observed.step_completions.items():
        # Compute observed completion rate for this step
        if step_name in observed_rates:
            obs_rate = observed_rates[step_name]
        else:
            # Estimate from counts
            prev_step_count = observed.step_completions.get(list(observed.step_completions.keys())[0], observed.entry_count)
            obs_rate = observed_count / prev_step_count if prev_step_count > 0 else 0.0
        
        # Simulated dropoff rate
        sim_dropoff = dropoff_by_step.get(step_name, 0.0)
        sim_completion = 1.0 - sim_dropoff
        
        # Error
        step_errors[step_name] = abs(sim_completion - obs_rate)
    
    errors['step_errors'] = step_errors
    errors['mean_step_error'] = np.mean(list(step_errors.values())) if step_errors else 0.0
    
    # Overall mean absolute error
    all_errors = [errors.get('completion_rate_error', errors.get('total_conversion_error', 0.0))]
    all_errors.extend(step_errors.values())
    errors['mean_absolute_error'] = np.mean(all_errors)
    
    return errors


# ============================================================================
# CALIBRATION OBJECTIVE FUNCTION
# ============================================================================

def calibration_objective(
    parameters: Dict[str, float],
    observed: ObservedFunnelData,
    simulation_function,
    simulation_args: Dict,
    product_steps: Dict,
    entry_signals: Optional[Dict] = None,
    regularization_weight: float = 0.1,
    default_parameters: Optional[Dict[str, float]] = None
) -> float:
    """
    Objective function for calibration (to minimize).
    
    Args:
        parameters: Parameters to test
        observed: Observed funnel data
        simulation_function: Function to run simulation
        simulation_args: Arguments for simulation
        product_steps: Product step definitions
        entry_signals: Optional entry signals for entry model
        regularization_weight: Weight for regularization term
        default_parameters: Default parameter values for regularization
    
    Returns:
        Total error (data fit + regularization)
    """
    if default_parameters is None:
        default_parameters = get_default_parameters()
    
    # Validate parameters
    validated_params = validate_parameters(parameters)
    
    # Run simulation with these parameters
    result_df = run_simulation_with_parameters(
        validated_params,
        simulation_function,
        simulation_args,
        engine_module='behavioral_engine_improved'
    )
    
    # Extract simulated metrics
    simulated_metrics = extract_simulated_metrics_from_results(result_df, product_steps)
    
    # Compute entry probability if entry signals provided
    entry_prob = None
    if entry_signals:
        from entry_model.funnel_integration import compute_full_funnel_prediction
        entry_scale = validated_params.get('ENTRY_PROBABILITY_SCALE', 1.0)
        
        # Get base entry probability
        from entry_model import estimate_entry_probability
        entry_result = estimate_entry_probability(**entry_signals)
        base_entry_prob = entry_result.entry_probability
        
        # Apply scaling
        entry_prob = np.clip(base_entry_prob * entry_scale, 0.01, 0.95)
    
    # Compute error
    errors = compute_funnel_error(observed, simulated_metrics, entry_prob)
    data_error = errors['mean_absolute_error']
    
    # Regularization: penalize large deviations from defaults
    regularization = 0.0
    for param_name in CALIBRATABLE_PARAMETERS:
        if param_name in validated_params and param_name in default_parameters:
            default_val = default_parameters[param_name]
            calibrated_val = validated_params[param_name]
            
            if default_val > 0:
                # Relative change
                relative_change = abs(calibrated_val - default_val) / default_val
                regularization += relative_change ** 2
    
    regularization *= regularization_weight
    
    total_error = data_error + regularization
    
    return total_error


# ============================================================================
# CALIBRATION OPTIMIZATION
# ============================================================================

def calibrate_to_real_data(
    observed_funnel: ObservedFunnelData,
    simulation_function,
    simulation_args: Dict,
    product_steps: Dict,
    entry_signals: Optional[Dict] = None,
    initial_parameters: Optional[Dict[str, float]] = None,
    regularization_weight: float = 0.1,
    max_iterations: int = 50,
    verbose: bool = True
) -> Tuple[Dict[str, float], CalibrationSummary, CalibrationDiagnostics]:
    """
    Calibrate model parameters to match observed funnel data.
    
    Args:
        observed_funnel: Observed funnel data
        simulation_function: Function to run simulation
        simulation_args: Arguments for simulation
        product_steps: Product step definitions
        entry_signals: Optional entry signals for entry model
        initial_parameters: Optional initial parameter values
        regularization_weight: Weight for regularization (prevents overfitting)
        max_iterations: Maximum optimization iterations
        verbose: Print progress
    
    Returns:
        Tuple of (calibrated_parameters, summary, diagnostics)
    """
    if initial_parameters is None:
        initial_parameters = get_default_parameters()
    
    default_parameters = initial_parameters.copy()
    
    # Compute error before calibration
    if verbose:
        print("=" * 80)
        print("REAL-WORLD CALIBRATION")
        print("=" * 80)
        print("\nComputing baseline error...")
    
    baseline_result_df = run_simulation_with_parameters(
        default_parameters,
        simulation_function,
        simulation_args,
        engine_module='behavioral_engine_improved'
    )
    baseline_metrics = extract_simulated_metrics_from_results(baseline_result_df, product_steps)
    
    entry_prob_before = None
    if entry_signals:
        from entry_model import estimate_entry_probability
        entry_result = estimate_entry_probability(**entry_signals)
        entry_prob_before = entry_result.entry_probability
    
    baseline_errors = compute_funnel_error(observed_funnel, baseline_metrics, entry_prob_before)
    before_error = baseline_errors['mean_absolute_error']
    
    if verbose:
        print(f"  Baseline mean absolute error: {before_error:.6f}")
        print(f"  Baseline completion rate error: {baseline_errors.get('completion_rate_error', baseline_errors.get('total_conversion_error', 0.0)):.6f}")
        print(f"  Baseline mean step error: {baseline_errors['mean_step_error']:.6f}")
    
    # Optimization: coordinate descent (simpler than full grid search)
    if verbose:
        print(f"\nOptimizing {len(CALIBRATABLE_PARAMETERS)} parameters...")
        print(f"  Regularization weight: {regularization_weight}")
        print(f"  Max iterations: {max_iterations}\n")
    
    best_parameters = default_parameters.copy()
    
    # Initialize any missing calibratable parameters with their defaults
    for param_name, param_def in CALIBRATABLE_PARAMETERS.items():
        if param_name not in best_parameters:
            best_parameters[param_name] = param_def['default']
    
    best_error = float('inf')
    optimization_history = []
    
    param_names = list(CALIBRATABLE_PARAMETERS.keys())
    
    # Coordinate descent: optimize one parameter at a time
    iteration = 0
    converged = False
    
    while iteration < max_iterations and not converged:
        iteration += 1
        prev_best_error = best_error
        
        # Optimize each parameter in turn
        for param_name in param_names:
            param_def = CALIBRATABLE_PARAMETERS[param_name]
            
            # Test 5 values for this parameter
            test_values = np.linspace(
                param_def['bounds'][0],
                param_def['bounds'][1],
                5
            )
            
            # Initialize with default if not present
            if param_name not in best_parameters:
                best_parameters[param_name] = param_def['default']
            
            best_param_value = best_parameters[param_name]
            best_param_error = best_error
            
            for test_value in test_values:
                candidate_params = best_parameters.copy()
                candidate_params[param_name] = test_value
                
                # Evaluate objective
                error = calibration_objective(
                    candidate_params,
                    observed_funnel,
                    simulation_function,
                    simulation_args,
                    product_steps,
                    entry_signals=entry_signals,
                    regularization_weight=regularization_weight,
                    default_parameters=default_parameters
                )
                
                if error < best_param_error:
                    best_param_error = error
                    best_param_value = test_value
            
            # Update parameter
            best_parameters[param_name] = best_param_value
            best_error = best_param_error
            
            optimization_history.append({
                'iteration': iteration,
                'parameter': param_name,
                'error': best_error,
                'parameters': best_parameters.copy()
            })
        
        # Check convergence
        error_change = abs(prev_best_error - best_error)
        if error_change < 1e-6:
            converged = True
        
        if verbose and iteration % 2 == 0:
            print(f"  Iteration {iteration}: Best error = {best_error:.6f}")
    
    # Compute error after calibration
    if verbose:
        print(f"\nComputing calibrated error...")
    
    calibrated_result_df = run_simulation_with_parameters(
        best_parameters,
        simulation_function,
        simulation_args,
        engine_module='behavioral_engine_improved'
    )
    calibrated_metrics = extract_simulated_metrics_from_results(calibrated_result_df, product_steps)
    
    entry_prob_after = None
    if entry_signals:
        from entry_model import estimate_entry_probability
        entry_scale = best_parameters.get('ENTRY_PROBABILITY_SCALE', 1.0)
        entry_result = estimate_entry_probability(**entry_signals)
        entry_prob_after = np.clip(entry_result.entry_probability * entry_scale, 0.01, 0.95)
    
    after_errors = compute_funnel_error(observed_funnel, calibrated_metrics, entry_prob_after)
    after_error = after_errors['mean_absolute_error']
    
    # Compute improvement
    improvement_pct = ((before_error - after_error) / before_error * 100) if before_error > 0 else 0.0
    
    # Compute parameter changes
    parameter_changes = {}
    for param_name in CALIBRATABLE_PARAMETERS:
        if param_name in best_parameters:
            # Get default value (from default_parameters or CALIBRATABLE_PARAMETERS)
            if param_name in default_parameters:
                default_val = default_parameters[param_name]
            else:
                default_val = CALIBRATABLE_PARAMETERS[param_name]['default']
            
            calibrated_val = best_parameters[param_name]
            change = calibrated_val - default_val
            change_pct = (change / default_val * 100) if default_val > 0 else 0.0
            parameter_changes[param_name] = change_pct
    
    # Compute parameter sensitivity (from optimization history)
    parameter_sensitivity = {}
    for param_name in param_names:
        # Find range of values tested and their errors
        param_errors = []
        for hist_entry in optimization_history:
            param_val = hist_entry['parameters'].get(param_name, 0.0)
            error = hist_entry['error']
            param_errors.append((param_val, error))
        
        if param_errors:
            # Compute sensitivity as variance in error across parameter range
            errors_only = [e for _, e in param_errors]
            if len(errors_only) > 1:
                sensitivity = np.std(errors_only)
                parameter_sensitivity[param_name] = sensitivity
    
    # Compute confidence ranges (from optimization history)
    # Use top 10% of results to estimate confidence
    sorted_history = sorted(optimization_history, key=lambda x: x['error'])
    top_n = max(1, int(len(sorted_history) * 0.1))
    top_results = sorted_history[:top_n]
    
    confidence_ranges = {}
    for param_name in param_names:
        param_values = [entry['parameters'][param_name] for entry in top_results]
        if param_values:
            confidence_ranges[param_name] = (
                float(np.percentile(param_values, 5)),
                float(np.percentile(param_values, 95))
            )
    
    # Compute fit score
    max_possible_error = 1.0
    normalized_after_error = min(1.0, after_error / max_possible_error)
    fit_score = 1.0 - normalized_after_error
    
    # Build summary
    summary = CalibrationSummary(
        before_error=before_error,
        after_error=after_error,
        improvement_pct=improvement_pct,
        calibrated_parameters=best_parameters,
        default_parameters=default_parameters,
        parameter_changes=parameter_changes,
        confidence_ranges=confidence_ranges,
        fit_score=fit_score,
        timestamp=datetime.now().isoformat()
    )
    
    # Build diagnostics
    diagnostics = CalibrationDiagnostics(
        per_step_errors_before=baseline_errors['step_errors'],
        per_step_errors_after=after_errors['step_errors'],
        parameter_sensitivity=parameter_sensitivity,
        regularization_penalty=best_error - after_error,  # Approximate
        optimization_history=optimization_history[:20],  # Keep last 20
        convergence_reason=f"Grid search completed ({iteration} iterations)"
    )
    
    if verbose:
        print("\n" + "=" * 80)
        print("CALIBRATION COMPLETE")
        print("=" * 80)
        print(f"\nBefore calibration:")
        print(f"  Mean absolute error = {before_error:.6f}")
        print(f"\nAfter calibration:")
        print(f"  Mean absolute error = {after_error:.6f}")
        print(f"\nImprovement: {improvement_pct:.1f}%")
        print(f"Fit score: {fit_score:.4f}")
        print(f"\nCalibrated parameters:")
        for param_name in param_names:
            # Get default value (from default_parameters or CALIBRATABLE_PARAMETERS)
            if param_name in default_parameters:
                default_val = default_parameters[param_name]
            else:
                default_val = CALIBRATABLE_PARAMETERS[param_name]['default']
            
            calibrated_val = best_parameters[param_name]
            change_pct = parameter_changes[param_name]
            print(f"  {param_name}: {calibrated_val:.4f} (default: {default_val:.4f}, change: {change_pct:+.1f}%)")
        print("=" * 80)
    
    return best_parameters, summary, diagnostics


# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

def export_calibration_summary(
    summary: CalibrationSummary,
    filepath: str = 'calibration_summary.json'
):
    """Export calibration summary to JSON."""
    export_dict = summary.to_dict()
    
    with open(filepath, 'w') as f:
        json.dump(export_dict, f, indent=2)
    
    return export_dict


def export_calibration_diagnostics(
    diagnostics: CalibrationDiagnostics,
    filepath: str = 'calibration_diagnostics.json'
):
    """Export calibration diagnostics to JSON."""
    export_dict = diagnostics.to_dict()
    
    with open(filepath, 'w') as f:
        json.dump(export_dict, f, indent=2)
    
    return export_dict


def log_parameter_changes(
    summary: CalibrationSummary,
    filepath: str = 'parameter_changes.log'
):
    """Log all parameter changes for audit trail."""
    with open(filepath, 'w') as f:
        f.write(f"Parameter Calibration Log\n")
        f.write(f"Timestamp: {summary.timestamp}\n")
        f.write(f"=" * 80 + "\n\n")
        f.write(f"Before calibration error: {summary.before_error:.6f}\n")
        f.write(f"After calibration error: {summary.after_error:.6f}\n")
        f.write(f"Improvement: {summary.improvement_pct:.1f}%\n\n")
        f.write(f"Parameter Changes:\n")
        f.write(f"-" * 80 + "\n")
        for param_name, change_pct in summary.parameter_changes.items():
            # Get default value (from default_parameters or CALIBRATABLE_PARAMETERS)
            if param_name in summary.default_parameters:
                default = summary.default_parameters[param_name]
            else:
                default = CALIBRATABLE_PARAMETERS[param_name]['default']
            
            calibrated = summary.calibrated_parameters[param_name]
            f.write(f"{param_name}:\n")
            f.write(f"  Default: {default:.6f}\n")
            f.write(f"  Calibrated: {calibrated:.6f}\n")
            f.write(f"  Change: {change_pct:+.2f}%\n")
            if param_name in summary.confidence_ranges:
                f.write(f"  Confidence range: {summary.confidence_ranges[param_name]}\n\n")
            else:
                f.write(f"  Confidence range: N/A\n\n")
        f.write(f"=" * 80 + "\n")
        f.write(f"Note: All changes are reversible. Default parameters preserved.\n")
    
    return filepath


"""
sensitivity_analysis.py - Parameter Sensitivity Analysis

Varies parameters ±20% and measures impact on outputs to identify which assumptions matter most.
"""

import numpy as np
from typing import Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass

from calibration.parameter_space import (
    PARAMETER_SPACE,
    get_default_parameters,
    validate_parameters
)
from calibration.loss_functions import extract_simulated_metrics_from_results
from calibration.calibrator import run_simulation_with_parameters


@dataclass
class SensitivityResult:
    """Sensitivity analysis result for a single parameter."""
    parameter_name: str
    baseline_value: float
    low_value: float  # -20%
    high_value: float  # +20%
    baseline_completion: float
    low_completion: float
    high_completion: float
    sensitivity: float  # Absolute change per unit parameter change
    relative_sensitivity: float  # Percentage change per percentage parameter change
    impact_rank: Optional[int] = None  # Rank by sensitivity (1 = most sensitive)
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'parameter_name': self.parameter_name,
            'baseline_value': float(self.baseline_value),
            'low_value': float(self.low_value),
            'high_value': float(self.high_value),
            'baseline_completion': float(self.baseline_completion),
            'low_completion': float(self.low_completion),
            'high_completion': float(self.high_completion),
            'sensitivity': float(self.sensitivity),
            'relative_sensitivity': float(self.relative_sensitivity),
            'impact_rank': self.impact_rank
        }


def analyze_parameter_sensitivity(
    parameter_name: str,
    baseline_parameters: Dict[str, float],
    simulation_function: Callable,
    simulation_args: Dict,
    product_steps: Dict,
    variation_pct: float = 0.20,  # ±20%
    engine_module: str = 'behavioral_engine_improved'
) -> SensitivityResult:
    """
    Analyze sensitivity of a single parameter.
    
    Args:
        parameter_name: Name of parameter to analyze
        baseline_parameters: Baseline parameter values
        simulation_function: Function to run simulation
        simulation_args: Arguments for simulation function
        product_steps: Dict of step definitions
        variation_pct: Percentage variation (0.20 = ±20%)
        engine_module: Engine module to use
    
    Returns:
        SensitivityResult with sensitivity metrics
    """
    if parameter_name not in baseline_parameters:
        raise ValueError(f"Parameter {parameter_name} not found in baseline_parameters")
    
    if parameter_name not in PARAMETER_SPACE:
        raise ValueError(f"Parameter {parameter_name} not in parameter space")
    
    baseline_value = baseline_parameters[parameter_name]
    param_def = PARAMETER_SPACE[parameter_name]
    
    # Compute low and high values (clipped to bounds)
    low_value = max(param_def.min_value, baseline_value * (1.0 - variation_pct))
    high_value = min(param_def.max_value, baseline_value * (1.0 + variation_pct))
    
    # Run baseline simulation
    baseline_params = baseline_parameters.copy()
    baseline_result_df = run_simulation_with_parameters(
        baseline_params,
        simulation_function,
        simulation_args,
        engine_module
    )
    baseline_metrics = extract_simulated_metrics_from_results(baseline_result_df, product_steps)
    baseline_completion = baseline_metrics.get('completion_rate', 0.0)
    
    # Run low value simulation
    low_params = baseline_parameters.copy()
    low_params[parameter_name] = low_value
    low_result_df = run_simulation_with_parameters(
        low_params,
        simulation_function,
        simulation_args,
        engine_module
    )
    low_metrics = extract_simulated_metrics_from_results(low_result_df, product_steps)
    low_completion = low_metrics.get('completion_rate', 0.0)
    
    # Run high value simulation
    high_params = baseline_parameters.copy()
    high_params[parameter_name] = high_value
    high_result_df = run_simulation_with_parameters(
        high_params,
        simulation_function,
        simulation_args,
        engine_module
    )
    high_metrics = extract_simulated_metrics_from_results(high_result_df, product_steps)
    high_completion = high_metrics.get('completion_rate', 0.0)
    
    # Compute sensitivity (absolute change per unit parameter change)
    param_range = high_value - low_value
    completion_range = max(abs(high_completion - baseline_completion),
                          abs(baseline_completion - low_completion))
    
    if param_range > 0:
        sensitivity = completion_range / param_range
    else:
        sensitivity = 0.0
    
    # Compute relative sensitivity (percentage change per percentage parameter change)
    if baseline_value > 0 and baseline_completion > 0:
        param_change_pct = variation_pct  # 20%
        completion_change_low = abs(baseline_completion - low_completion) / baseline_completion
        completion_change_high = abs(high_completion - baseline_completion) / baseline_completion
        max_completion_change_pct = max(completion_change_low, completion_change_high)
        relative_sensitivity = max_completion_change_pct / param_change_pct if param_change_pct > 0 else 0.0
    else:
        relative_sensitivity = 0.0
    
    return SensitivityResult(
        parameter_name=parameter_name,
        baseline_value=baseline_value,
        low_value=low_value,
        high_value=high_value,
        baseline_completion=baseline_completion,
        low_completion=low_completion,
        high_completion=high_completion,
        sensitivity=sensitivity,
        relative_sensitivity=relative_sensitivity
    )


def analyze_all_parameter_sensitivities(
    baseline_parameters: Dict[str, float],
    simulation_function: Callable,
    simulation_args: Dict,
    product_steps: Dict,
    variation_pct: float = 0.20,
    engine_module: str = 'behavioral_engine_improved',
    parameter_subset: Optional[List[str]] = None,
    verbose: bool = True
) -> Dict[str, SensitivityResult]:
    """
    Analyze sensitivity of all (or subset of) parameters.
    
    Args:
        baseline_parameters: Baseline parameter values
        simulation_function: Function to run simulation
        simulation_args: Arguments for simulation function
        product_steps: Dict of step definitions
        variation_pct: Percentage variation (0.20 = ±20%)
        engine_module: Engine module to use
        parameter_subset: Optional list of parameter names to analyze (if None, analyze all)
        verbose: Print progress
    
    Returns:
        Dict mapping parameter_name -> SensitivityResult
    """
    # Determine which parameters to analyze
    if parameter_subset is None:
        parameters_to_analyze = list(baseline_parameters.keys())
    else:
        parameters_to_analyze = [p for p in parameter_subset if p in baseline_parameters]
    
    if verbose:
        print(f"Analyzing sensitivity of {len(parameters_to_analyze)} parameters...")
    
    sensitivity_results = {}
    
    for i, param_name in enumerate(parameters_to_analyze):
        if verbose:
            print(f"  Analyzing {param_name} ({i+1}/{len(parameters_to_analyze)})...")
        
        try:
            result = analyze_parameter_sensitivity(
                param_name,
                baseline_parameters,
                simulation_function,
                simulation_args,
                product_steps,
                variation_pct=variation_pct,
                engine_module=engine_module
            )
            sensitivity_results[param_name] = result
        except Exception as e:
            if verbose:
                print(f"    Warning: Failed to analyze {param_name}: {e}")
            continue
    
    # Rank by sensitivity (relative sensitivity)
    ranked_results = sorted(
        sensitivity_results.items(),
        key=lambda x: x[1].relative_sensitivity,
        reverse=True
    )
    
    # Assign ranks
    for rank, (param_name, result) in enumerate(ranked_results, start=1):
        result.impact_rank = rank
    
    if verbose:
        print(f"\nParameter Sensitivity Ranking:")
        for param_name, result in ranked_results[:5]:  # Top 5
            print(f"  {rank}. {param_name}: sensitivity = {result.relative_sensitivity:.4f}")
    
    return sensitivity_results


def compute_sensitivity_summary(
    sensitivity_results: Dict[str, SensitivityResult]
) -> Dict[str, float]:
    """
    Compute summary dict mapping parameter_name -> relative_sensitivity.
    
    Args:
        sensitivity_results: Dict from analyze_all_parameter_sensitivities
    
    Returns:
        Dict mapping parameter_name -> relative_sensitivity (for easy access)
    """
    return {
        param_name: result.relative_sensitivity
        for param_name, result in sensitivity_results.items()
    }


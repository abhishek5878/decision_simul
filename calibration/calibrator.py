"""
calibrator.py - Main Calibration Module

Ties together parameter space, loss functions, optimizer, and validation
to calibrate behavioral simulation parameters against observed data.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
import copy

from calibration.parameter_space import (
    get_default_parameters,
    validate_parameters,
    PARAMETER_SPACE
)
from calibration.loss_functions import (
    extract_simulated_metrics_from_results,
    compute_composite_loss
)
from calibration.optimizer import random_search_optimize, OptimizationResult
from calibration.validation import validate_all, compute_confidence_intervals


@dataclass
class CalibrationConfig:
    """Configuration for calibration run."""
    max_iterations: int = 100
    early_stopping_patience: int = 20
    tolerance: float = 0.01
    loss_weights: Optional[Dict[str, float]] = None
    validation_strict: bool = False
    random_seed: int = 42
    verbose: bool = True


@dataclass
class CalibrationResult:
    """Result from calibration run."""
    calibrated_parameters: Dict[str, float]
    fit_score: float  # 1 - normalized_loss (higher is better, 0-1)
    loss: float  # Raw loss value
    confidence_intervals: Dict[str, Tuple[float, float]]
    validation_results: Dict
    optimization_history: List[Dict]
    recommended_defaults: Dict[str, float]  # Same as calibrated_parameters
    timestamp: str
    metadata: Dict


# ============================================================================
# PARAMETER INJECTION
# ============================================================================

def inject_parameters_into_engine(
    parameters: Dict[str, float],
    engine_module: str = 'behavioral_engine_improved'
):
    """
    Inject calibrated parameters into the behavioral engine.
    
    This patches the engine functions to use calibrated parameters.
    We do this by monkey-patching the functions that use hardcoded values.
    
    Args:
        parameters: Dict of calibrated parameters
        engine_module: Module name to patch ('behavioral_engine_improved' or 'behavioral_engine_intent_aware')
    
    Returns:
        Context manager that restores original functions on exit
    """
    import contextlib
    import sys
    
    if engine_module == 'behavioral_engine_improved':
        import behavioral_engine_improved as engine
    elif engine_module == 'behavioral_engine_intent_aware':
        import behavioral_engine_intent_aware as engine
        # Intent-aware uses improved engine, so we need to patch both
        import behavioral_engine_improved as base_engine
    else:
        raise ValueError(f"Unknown engine module: {engine_module}")
    
    # Store original functions
    original_functions = {}
    
    @contextlib.contextmanager
    def parameter_patch():
        # Always patch behavioral_engine_improved since it's the base
        import behavioral_engine_improved as base_engine
        
        # Patch should_continue_probabilistic in base engine
        if hasattr(base_engine, 'should_continue_probabilistic'):
            original = base_engine.should_continue_probabilistic
            original_functions['should_continue_probabilistic'] = original
            
            def patched_should_continue_probabilistic(state, priors, step_index, total_steps, modifiers=None):
                """Patched version with calibrated parameters."""
                # We need to replicate the original logic but with calibrated parameters
                # The original function computes base_prob, then applies BASE_COMPLETION_PROB and persistence_bonus
                
                if modifiers is None:
                    modifiers = {'base_persistence': 1.0, 'value_sensitivity': 1.0, 
                                 'fatigue_resilience': 1.0, 'risk_tolerance_mult': 1.0}
                
                # Get calibrated parameters
                BASE_COMPLETION_RATE = parameters.get('BASE_COMPLETION_RATE', 0.60)
                PERSISTENCE_BONUS_START = parameters.get('PERSISTENCE_BONUS_START', 0.18)
                PERSISTENCE_BONUS_RATE = parameters.get('PERSISTENCE_BONUS_RATE', 0.22)
                VALUE_SENSITIVITY = parameters.get('VALUE_SENSITIVITY', 1.0)
                
                # Replicate original logic up to the point where parameters are applied
                left = (state.perceived_value * priors['MS']) + state.perceived_control
                right = state.perceived_risk + state.perceived_effort
                base_advantage = left - right
                
                # Value override
                value_override = 0.0
                if state.perceived_value > 0.7:
                    value_override = state.perceived_value * 0.3
                
                # Commitment effect
                progress = step_index / total_steps if total_steps > 0 else 0
                commitment_boost = progress * 0.8
                
                if progress > 0.2:
                    early_progress_bonus = (progress - 0.2) * 0.5
                    commitment_boost += early_progress_bonus
                
                # Cognitive recovery
                energy_factor = state.cognitive_energy
                if state.cognitive_energy < 0.2 and state.perceived_value > 0.6:
                    energy_factor = 0.3
                
                adjusted_advantage = base_advantage + value_override + commitment_boost
                steepness = 1.2
                base_prob = 1 / (1 + np.exp(-steepness * adjusted_advantage))
                progress_prob_boost = progress * 0.20
                base_prob += progress_prob_boost
                
                # Apply archetype modifiers
                adjusted_prob = base_prob * modifiers['base_persistence']
                
                # Value sensitivity (calibrated)
                if state.perceived_value > 0.6:
                    value_bonus = (state.perceived_value - 0.6) * 0.2 * modifiers.get('value_sensitivity', 1.0) * VALUE_SENSITIVITY
                    adjusted_prob += value_bonus
                
                # Fatigue resilience
                if state.cognitive_energy < 0.3:
                    fatigue_penalty = (0.3 - state.cognitive_energy) * 0.15
                    fatigue_penalty *= (2.0 - modifiers.get('fatigue_resilience', 1.0))
                    adjusted_prob -= fatigue_penalty
                
                # Apply calibrated BASE_COMPLETION_RATE (replaces hardcoded 0.60)
                adjusted_prob = max(BASE_COMPLETION_RATE, adjusted_prob)
                
                # Apply calibrated persistence bonus (replaces hardcoded 0.18 + 0.22 * progress)
                persistence_bonus = PERSISTENCE_BONUS_START + PERSISTENCE_BONUS_RATE * progress
                adjusted_prob += persistence_bonus
                
                # Clamp to [0.05, 0.95]
                adjusted_prob = np.clip(adjusted_prob, 0.05, 0.95)
                
                return adjusted_prob
            
            # Patch in the module
            base_engine.should_continue_probabilistic = patched_should_continue_probabilistic
        
        # Patch intent model if using intent-aware
        if engine_module == 'behavioral_engine_intent_aware':
            from dropsim_intent_model import compute_intent_conditioned_continuation_prob
            original_intent = compute_intent_conditioned_continuation_prob
            original_functions['compute_intent_conditioned_continuation_prob'] = original_intent
            
            def patched_intent_conditioned(base_prob, intent_frame, step, step_index, total_steps, state):
                """Patched version with calibrated intent penalty."""
                # Call original
                prob, diagnostic = original_intent(base_prob, intent_frame, step, step_index, total_steps, state)
                
                # Apply calibrated intent penalty weight (scale the penalty)
                INTENT_PENALTY_WEIGHT = parameters.get('INTENT_PENALTY_WEIGHT', 0.025)
                default_intent_weight = 0.025
                if default_intent_weight > 0:
                    scale_factor = INTENT_PENALTY_WEIGHT / default_intent_weight
                    # Adjust penalty in diagnostic
                    if 'penalties' in diagnostic and 'intent' in diagnostic['penalties']:
                        original_penalty = diagnostic['penalties']['intent']
                        diagnostic['penalties']['intent'] = original_penalty * scale_factor
                        prob = base_prob + diagnostic['penalties']['intent']  # Recompute
                
                return prob, diagnostic
            
            # Monkey patch
            import dropsim_intent_model
            dropsim_intent_model.compute_intent_conditioned_continuation_prob = patched_intent_conditioned
        
        try:
            yield
        finally:
            # Restore original functions
            import behavioral_engine_improved as base_engine
            for func_name, original_func in original_functions.items():
                if func_name == 'should_continue_probabilistic':
                    base_engine.should_continue_probabilistic = original_func
                elif func_name == 'compute_intent_conditioned_continuation_prob':
                    import dropsim_intent_model
                    dropsim_intent_model.compute_intent_conditioned_continuation_prob = original_func
    
    return parameter_patch()


# ============================================================================
# SIMULATION RUNNER WRAPPER
# ============================================================================

def run_simulation_with_parameters(
    parameters: Dict[str, float],
    simulation_function: Callable,
    simulation_args: Dict,
    engine_module: str = 'behavioral_engine_improved'
) -> pd.DataFrame:
    """
    Run simulation with calibrated parameters injected.
    
    Args:
        parameters: Calibrated parameters to inject
        simulation_function: Function to run simulation (e.g., run_behavioral_simulation_improved)
        simulation_args: Arguments to pass to simulation function
        engine_module: Engine module to patch
    
    Returns:
        Simulation results DataFrame
    """
    # Validate parameters
    validated_params = validate_parameters(parameters)
    
    # Inject parameters and run simulation
    with inject_parameters_into_engine(validated_params, engine_module):
        result_df = simulation_function(**simulation_args)
    
    return result_df


# ============================================================================
# CALIBRATION RUNNER
# ============================================================================

def calibrate_parameters(
    simulation_function: Callable,
    simulation_args: Dict,
    observed_metrics: Dict,
    product_steps: Dict,
    config: Optional[CalibrationConfig] = None,
    engine_module: str = 'behavioral_engine_improved'
) -> CalibrationResult:
    """
    Main calibration function.
    
    Args:
        simulation_function: Function to run simulation
        simulation_args: Arguments for simulation function
        observed_metrics: Dict with 'completion_rate', 'dropoff_by_step', 'avg_steps_completed'
        product_steps: Dict of step definitions
        config: Calibration configuration
        engine_module: Engine module to patch
    
    Returns:
        CalibrationResult with calibrated parameters and metrics
    """
    if config is None:
        config = CalibrationConfig()
    
    rng = np.random.default_rng(config.random_seed)
    
    # Define loss function
    def loss_function(parameters: Dict[str, float]) -> float:
        """Compute loss for given parameters."""
        # Run simulation with these parameters
        result_df = run_simulation_with_parameters(
            parameters,
            simulation_function,
            simulation_args,
            engine_module
        )
        
        # Extract simulated metrics
        simulated_metrics = extract_simulated_metrics_from_results(result_df, product_steps)
        
        # Compute loss
        loss_result = compute_composite_loss(
            simulated_metrics,
            observed_metrics,
            config.loss_weights
        )
        
        return loss_result['total_loss']
    
    # Run optimization
    if config.verbose:
        print("=" * 80)
        print("CALIBRATION: Starting Parameter Optimization")
        print("=" * 80)
        print(f"Observed metrics:")
        print(f"  Completion rate: {observed_metrics.get('completion_rate', 0.0):.2%}")
        print(f"  Avg steps completed: {observed_metrics.get('avg_steps_completed', 0.0):.2f}")
        print(f"  Steps: {len(observed_metrics.get('dropoff_by_step', {}))}")
        print()
    
    opt_result = random_search_optimize(
        loss_function,
        max_iterations=config.max_iterations,
        early_stopping_patience=config.early_stopping_patience,
        tolerance=config.tolerance,
        rng=rng,
        verbose=config.verbose
    )
    
    # Run final simulation with best parameters to get metrics for validation
    best_result_df = run_simulation_with_parameters(
        opt_result.best_parameters,
        simulation_function,
        simulation_args,
        engine_module
    )
    final_simulated_metrics = extract_simulated_metrics_from_results(best_result_df, product_steps)
    
    # Validate calibrated parameters
    validation_results = validate_all(
        opt_result.best_parameters,
        simulated_metrics=final_simulated_metrics,
        observed_metrics=observed_metrics,
        strict=config.validation_strict
    )
    
    # Compute confidence intervals
    confidence_intervals = compute_confidence_intervals(opt_result.history)
    
    # Compute fit score (1 - normalized loss, where 0 = worst, 1 = perfect)
    # Normalize loss to [0, 1] range (assume max loss is ~1.0 for completion rate error)
    normalized_loss = min(1.0, opt_result.best_loss)
    fit_score = 1.0 - normalized_loss
    
    # Build result
    result = CalibrationResult(
        calibrated_parameters=opt_result.best_parameters,
        fit_score=fit_score,
        loss=opt_result.best_loss,
        confidence_intervals=confidence_intervals,
        validation_results=validation_results,
        optimization_history=opt_result.history,
        recommended_defaults=opt_result.best_parameters.copy(),  # Same as calibrated
        timestamp=datetime.now().isoformat(),
        metadata={
            'optimization_iterations': opt_result.iteration,
            'converged': opt_result.converged,
            'convergence_reason': opt_result.convergence_reason,
            'observed_metrics': observed_metrics,
            'final_simulated_metrics': final_simulated_metrics
        }
    )
    
    if config.verbose:
        print("\n" + "=" * 80)
        print("CALIBRATION: Complete")
        print("=" * 80)
        print(f"Fit score: {fit_score:.4f} (higher is better, 1.0 = perfect)")
        print(f"Final loss: {opt_result.best_loss:.6f}")
        print(f"\nCalibrated parameters:")
        for name, value in opt_result.best_parameters.items():
            default = PARAMETER_SPACE[name].default
            change_pct = ((value - default) / default * 100) if default > 0 else 0
            print(f"  {name}: {value:.4f} (default: {default:.4f}, change: {change_pct:+.1f}%)")
        print(f"\nValidation: {'PASSED' if validation_results['is_valid'] else 'FAILED'}")
        if validation_results['warnings']:
            print(f"Warnings: {len(validation_results['warnings'])}")
        if validation_results['errors']:
            print(f"Errors: {len(validation_results['errors'])}")
        print("=" * 80)
    
    return result


def export_calibration_result(
    result: CalibrationResult,
    filepath: str
):
    """Export calibration result to JSON file."""
    export_dict = {
        'calibrated_parameters': result.calibrated_parameters,
        'fit_score': result.fit_score,
        'loss': result.loss,
        'confidence_intervals': {
            name: list(bounds) for name, bounds in result.confidence_intervals.items()
        },
        'validation_results': result.validation_results,
        'recommended_defaults': result.recommended_defaults,
        'timestamp': result.timestamp,
        'metadata': result.metadata
    }
    
    with open(filepath, 'w') as f:
        json.dump(export_dict, f, indent=2)
    
    return export_dict


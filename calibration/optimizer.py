"""
optimizer.py - Optimization Algorithms for Parameter Calibration

Implements random search and optional Bayesian optimization.
"""

from typing import Dict, List, Tuple, Optional, Callable
import numpy as np
from dataclasses import dataclass
from calibration.parameter_space import (
    PARAMETER_SPACE,
    get_default_parameters,
    validate_parameters,
    sample_random_parameters,
    get_parameter_bounds
)


@dataclass
class OptimizationResult:
    """Result from optimization run."""
    best_parameters: Dict[str, float]
    best_loss: float
    iteration: int
    history: List[Dict]  # List of {iteration, loss, parameters}
    converged: bool
    convergence_reason: str


def random_search_optimize(
    loss_function: Callable[[Dict[str, float]], float],
    max_iterations: int = 100,
    early_stopping_patience: int = 20,
    tolerance: float = 0.01,
    rng: Optional[np.random.Generator] = None,
    verbose: bool = True
) -> OptimizationResult:
    """
    Random search optimization.
    
    Args:
        loss_function: Function that takes parameters dict and returns loss (lower is better)
        max_iterations: Maximum number of iterations
        early_stopping_patience: Stop if no improvement for this many iterations
        tolerance: Minimum improvement to count as progress
        rng: Random number generator
        verbose: Print progress
    
    Returns:
        OptimizationResult with best parameters found
    """
    if rng is None:
        rng = np.random.default_rng(42)
    
    # Initialize with default parameters
    best_params = get_default_parameters()
    best_loss = loss_function(best_params)
    
    history = [{
        'iteration': 0,
        'loss': best_loss,
        'parameters': best_params.copy()
    }]
    
    no_improvement_count = 0
    converged = False
    convergence_reason = "max_iterations"
    
    if verbose:
        print(f"Starting random search optimization...")
        print(f"  Initial loss: {best_loss:.6f}")
        print(f"  Max iterations: {max_iterations}")
        print(f"  Early stopping patience: {early_stopping_patience}\n")
    
    for iteration in range(1, max_iterations + 1):
        # Sample random parameters
        candidate_params = sample_random_parameters(rng)
        
        # Evaluate loss
        candidate_loss = loss_function(candidate_params)
        
        # Check if better
        improvement = best_loss - candidate_loss
        if improvement > tolerance:
            best_params = candidate_params
            best_loss = candidate_loss
            no_improvement_count = 0
            
            if verbose and iteration % 10 == 0:
                print(f"  Iteration {iteration}: New best loss = {best_loss:.6f} "
                      f"(improvement: {improvement:.6f})")
        else:
            no_improvement_count += 1
        
        # Record history
        history.append({
            'iteration': iteration,
            'loss': candidate_loss,
            'parameters': candidate_params.copy(),
            'best_loss': best_loss,
            'improvement': improvement
        })
        
        # Check early stopping
        if no_improvement_count >= early_stopping_patience:
            converged = True
            convergence_reason = f"early_stopping (no improvement for {early_stopping_patience} iterations)"
            if verbose:
                print(f"\nEarly stopping at iteration {iteration}")
                print(f"  No improvement for {early_stopping_patience} iterations")
            break
    
    if verbose:
        print(f"\nOptimization complete!")
        print(f"  Best loss: {best_loss:.6f}")
        print(f"  Converged: {converged} ({convergence_reason})")
        print(f"  Total iterations: {len(history) - 1}")
    
    return OptimizationResult(
        best_parameters=best_params,
        best_loss=best_loss,
        iteration=len(history) - 1,
        history=history,
        converged=converged,
        convergence_reason=convergence_reason
    )


def grid_search_optimize(
    loss_function: Callable[[Dict[str, float]], float],
    grid_size: int = 3,
    verbose: bool = True
) -> OptimizationResult:
    """
    Grid search optimization (coarse, for validation).
    
    Only searches over a subset of parameters due to curse of dimensionality.
    Uses grid_size points per parameter.
    
    Args:
        loss_function: Function that takes parameters dict and returns loss
        grid_size: Number of points per parameter (3 = low, mid, high)
        verbose: Print progress
    
    Returns:
        OptimizationResult with best parameters found
    """
    # Grid search is only practical for a small subset of key parameters
    key_params = ['BASE_COMPLETION_RATE', 'PERSISTENCE_BONUS_START', 
                  'PERSISTENCE_BONUS_RATE', 'INTENT_PENALTY_WEIGHT']
    
    # Generate grid points for each parameter
    grids = {}
    for param_name in key_params:
        if param_name in PARAMETER_SPACE:
            param_def = PARAMETER_SPACE[param_name]
            grids[param_name] = np.linspace(
                param_def.min_value,
                param_def.max_value,
                grid_size
            )
    
    # Use defaults for other parameters
    defaults = get_default_parameters()
    
    best_params = defaults.copy()
    best_loss = loss_function(best_params)
    
    history = [{
        'iteration': 0,
        'loss': best_loss,
        'parameters': best_params.copy()
    }]
    
    if verbose:
        print(f"Starting grid search optimization...")
        print(f"  Grid size: {grid_size} points per parameter")
        print(f"  Parameters: {', '.join(key_params)}")
        print(f"  Total combinations: {grid_size ** len(key_params)}\n")
    
    # Iterate over grid
    total_combinations = grid_size ** len(key_params)
    iteration = 0
    
    # Create all combinations (nested loops)
    import itertools
    param_names = list(grids.keys())
    param_values = [grids[name] for name in param_names]
    
    for combination in itertools.product(*param_values):
        iteration += 1
        candidate_params = defaults.copy()
        for name, value in zip(param_names, combination):
            candidate_params[name] = value
        
        candidate_loss = loss_function(candidate_params)
        
        if candidate_loss < best_loss:
            best_params = candidate_params
            best_loss = candidate_loss
        
        history.append({
            'iteration': iteration,
            'loss': candidate_loss,
            'parameters': candidate_params.copy(),
            'best_loss': best_loss
        })
        
        if verbose and iteration % 10 == 0:
            print(f"  Iteration {iteration}/{total_combinations}: "
                  f"Best loss = {best_loss:.6f}")
    
    if verbose:
        print(f"\nGrid search complete!")
        print(f"  Best loss: {best_loss:.6f}")
        print(f"  Total iterations: {iteration}")
    
    return OptimizationResult(
        best_parameters=best_params,
        best_loss=best_loss,
        iteration=iteration,
        history=history,
        converged=True,
        convergence_reason="grid_search_complete"
    )


def bayesian_optimize(
    loss_function: Callable[[Dict[str, float]], float],
    max_iterations: int = 50,
    initial_points: int = 10,
    rng: Optional[np.random.Generator] = None,
    verbose: bool = True
) -> OptimizationResult:
    """
    Bayesian optimization using Gaussian Process.
    
    Requires scikit-optimize. Falls back to random search if not available.
    
    Args:
        loss_function: Function that takes parameters dict and returns loss
        max_iterations: Maximum number of iterations
        initial_points: Number of random points before GP fitting
        rng: Random number generator
        verbose: Print progress
    
    Returns:
        OptimizationResult with best parameters found
    """
    try:
        from skopt import gp_minimize
        from skopt.space import Real
        from skopt.utils import use_named_args
    except ImportError:
        if verbose:
            print("scikit-optimize not available, falling back to random search")
        return random_search_optimize(
            loss_function, max_iterations=max_iterations, 
            rng=rng, verbose=verbose
        )
    
    if rng is None:
        rng = np.random.default_rng(42)
    
    # Define search space
    bounds = get_parameter_bounds()
    dimensions = []
    param_names = list(bounds.keys())
    
    for param_name in param_names:
        min_val, max_val = bounds[param_name]
        dimensions.append(Real(min_val, max_val, name=param_name))
    
    # Wrap loss function
    @use_named_args(dimensions=dimensions)
    def wrapped_loss(**kwargs):
        return loss_function(kwargs)
    
    if verbose:
        print(f"Starting Bayesian optimization...")
        print(f"  Max iterations: {max_iterations}")
        print(f"  Initial random points: {initial_points}\n")
    
    # Run optimization
    result = gp_minimize(
        wrapped_loss,
        dimensions=dimensions,
        n_calls=max_iterations,
        n_initial_points=initial_points,
        random_state=rng.integers(0, 2**31),
        verbose=verbose
    )
    
    # Extract best parameters
    best_params = dict(zip(param_names, result.x))
    best_loss = result.fun
    
    # Build history (simplified)
    history = [{
        'iteration': i,
        'loss': result.func_vals[i],
        'parameters': dict(zip(param_names, result.x_iters[i]))
    } for i in range(len(result.func_vals))]
    
    if verbose:
        print(f"\nBayesian optimization complete!")
        print(f"  Best loss: {best_loss:.6f}")
        print(f"  Total iterations: {len(result.func_vals)}")
    
    return OptimizationResult(
        best_parameters=best_params,
        best_loss=best_loss,
        iteration=len(result.func_vals),
        history=history,
        converged=True,
        convergence_reason="bayesian_optimization_complete"
    )


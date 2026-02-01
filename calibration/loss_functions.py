"""
loss_functions.py - Loss Functions for Calibration

Compares simulated outcomes with observed real-world data.
"""

from typing import Dict, List, Optional
import numpy as np
from collections import Counter


def compute_completion_rate_error(
    simulated_completion_rate: float,
    observed_completion_rate: float
) -> float:
    """
    Compute absolute error in completion rate.
    
    Args:
        simulated_completion_rate: Completion rate from simulation (0-1)
        observed_completion_rate: Observed completion rate from real data (0-1)
    
    Returns:
        Absolute error (0-1, where 0 = perfect match)
    """
    return abs(simulated_completion_rate - observed_completion_rate)


def compute_step_dropoff_mse(
    simulated_dropoff_by_step: Dict[str, float],
    observed_dropoff_by_step: Dict[str, float]
) -> float:
    """
    Compute mean squared error for step drop-off distribution.
    
    Args:
        simulated_dropoff_by_step: Dict mapping step_name -> drop_rate (0-1)
        observed_dropoff_by_step: Dict mapping step_name -> drop_rate (0-1)
    
    Returns:
        Mean squared error (0-1, where 0 = perfect match)
    """
    # Get union of all steps
    all_steps = set(simulated_dropoff_by_step.keys()) | set(observed_dropoff_by_step.keys())
    
    if not all_steps:
        return 0.0
    
    errors = []
    for step_name in all_steps:
        sim_rate = simulated_dropoff_by_step.get(step_name, 0.0)
        obs_rate = observed_dropoff_by_step.get(step_name, 0.0)
        errors.append((sim_rate - obs_rate) ** 2)
    
    return np.mean(errors) if errors else 0.0


def compute_avg_steps_completed_error(
    simulated_avg_steps: float,
    observed_avg_steps: float
) -> float:
    """
    Compute absolute error in average steps completed.
    
    Args:
        simulated_avg_steps: Average steps completed in simulation
        observed_avg_steps: Average steps completed in real data
    
    Returns:
        Absolute error (0+, where 0 = perfect match)
    """
    return abs(simulated_avg_steps - observed_avg_steps)


def compute_composite_loss(
    simulated_metrics: Dict,
    observed_metrics: Dict,
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, float]:
    """
    Compute composite loss function comparing simulation to observed data.
    
    Args:
        simulated_metrics: Dict with keys:
            - completion_rate: float (0-1)
            - dropoff_by_step: Dict[str, float] (step_name -> drop_rate)
            - avg_steps_completed: float
        observed_metrics: Dict with same structure as simulated_metrics
        weights: Optional dict with keys 'completion', 'dropoff', 'steps' for loss weights
    
    Returns:
        Dict with:
            - total_loss: float (weighted sum)
            - completion_error: float
            - dropoff_mse: float
            - steps_error: float
            - component_losses: Dict with individual losses
    """
    if weights is None:
        weights = {
            'completion': 1.0,
            'dropoff': 1.0,
            'steps': 0.5  # Less weight on steps (derived from dropoff)
        }
    
    # Extract metrics
    sim_completion = simulated_metrics.get('completion_rate', 0.0)
    obs_completion = observed_metrics.get('completion_rate', 0.0)
    
    sim_dropoff = simulated_metrics.get('dropoff_by_step', {})
    obs_dropoff = observed_metrics.get('dropoff_by_step', {})
    
    sim_steps = simulated_metrics.get('avg_steps_completed', 0.0)
    obs_steps = observed_metrics.get('avg_steps_completed', 0.0)
    
    # Compute component losses
    completion_error = compute_completion_rate_error(sim_completion, obs_completion)
    dropoff_mse = compute_step_dropoff_mse(sim_dropoff, obs_dropoff)
    steps_error = compute_avg_steps_completed_error(sim_steps, obs_steps)
    
    # Normalize steps error (divide by max steps to get 0-1 range)
    # Assume max steps is 10 for normalization
    max_steps = 10.0
    normalized_steps_error = steps_error / max_steps if max_steps > 0 else steps_error
    
    # Weighted combination
    total_loss = (
        weights['completion'] * completion_error +
        weights['dropoff'] * dropoff_mse +
        weights['steps'] * normalized_steps_error
    )
    
    return {
        'total_loss': total_loss,
        'completion_error': completion_error,
        'dropoff_mse': dropoff_mse,
        'steps_error': steps_error,
        'normalized_steps_error': normalized_steps_error,
        'component_losses': {
            'completion': completion_error,
            'dropoff': dropoff_mse,
            'steps': normalized_steps_error
        }
    }


def extract_simulated_metrics_from_results(
    result_df,
    product_steps: Dict
) -> Dict:
    """
    Extract observable metrics from simulation results DataFrame.
    
    Args:
        result_df: DataFrame with simulation results (must have 'trajectories' column)
        product_steps: Dict of step definitions (for step names)
    
    Returns:
        Dict with completion_rate, dropoff_by_step, avg_steps_completed
    """
    step_names = list(product_steps.keys())
    total_trajectories = 0
    completed_trajectories = 0
    step_dropoff_counts = {step: 0 for step in step_names}
    step_entry_counts = {step: 0 for step in step_names}
    total_steps_completed = 0
    
    # Aggregate across all personas and trajectories
    for _, row in result_df.iterrows():
        trajectories = row.get('trajectories', [])
        for traj in trajectories:
            total_trajectories += 1
            journey = traj.get('journey', [])
            exit_step = traj.get('exit_step', 'Completed')
            
            # Count completion
            if exit_step == 'Completed':
                completed_trajectories += 1
            
            # Track step dropoffs
            for step_idx, step_data in enumerate(journey):
                step_name = step_data.get('step', '')
                if step_name in step_entry_counts:
                    step_entry_counts[step_name] += 1
                    
                    # If this is the last step before exit, count as dropout
                    if step_idx == len(journey) - 1 and exit_step != 'Completed':
                        if step_name in step_dropoff_counts:
                            step_dropoff_counts[step_name] += 1
            
            # Count steps completed
            total_steps_completed += len(journey)
    
    # Compute completion rate
    completion_rate = completed_trajectories / total_trajectories if total_trajectories > 0 else 0.0
    
    # Compute dropoff rates per step
    dropoff_by_step = {}
    for step_name in step_names:
        entered = step_entry_counts.get(step_name, 0)
        dropped = step_dropoff_counts.get(step_name, 0)
        dropoff_rate = dropped / entered if entered > 0 else 0.0
        dropoff_by_step[step_name] = dropoff_rate
    
    # Compute average steps completed
    avg_steps_completed = total_steps_completed / total_trajectories if total_trajectories > 0 else 0.0
    
    return {
        'completion_rate': completion_rate,
        'dropoff_by_step': dropoff_by_step,
        'avg_steps_completed': avg_steps_completed,
        'total_trajectories': total_trajectories,
        'completed_trajectories': completed_trajectories
    }


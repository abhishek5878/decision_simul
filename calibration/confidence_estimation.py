"""
confidence_estimation.py - Confidence Interval Estimation

Runs stochastic simulations to estimate prediction variance and confidence intervals.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass
from collections import defaultdict

from calibration.loss_functions import extract_simulated_metrics_from_results


@dataclass
class ConfidenceEstimate:
    """Confidence interval estimate from stochastic simulations."""
    mean_completion: float
    p10: float  # 10th percentile
    p25: float  # 25th percentile
    p50: float  # 50th percentile (median)
    p75: float  # 75th percentile
    p90: float  # 90th percentile
    variance: float
    std_dev: float
    stability_score: float  # 1 - normalized variance
    n_simulations: int
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'mean_completion': float(self.mean_completion),
            'p10': float(self.p10),
            'p25': float(self.p25),
            'p50': float(self.p50),
            'p75': float(self.p75),
            'p90': float(self.p90),
            'variance': float(self.variance),
            'std_dev': float(self.std_dev),
            'stability_score': float(self.stability_score),
            'n_simulations': int(self.n_simulations)
        }


def run_stochastic_simulations(
    simulation_function: Callable,
    simulation_args: Dict,
    n_simulations: int = 50,
    random_seed_base: int = 42,
    verbose: bool = True
) -> List[float]:
    """
    Run multiple stochastic simulations with different random seeds.
    
    Args:
        simulation_function: Function to run simulation
        simulation_args: Arguments for simulation function (seed will be overridden)
        n_simulations: Number of stochastic runs
        random_seed_base: Base seed (each run gets seed_base + i)
        verbose: Print progress
    
    Returns:
        List of completion rates from each simulation
    """
    completion_rates = []
    
    if verbose:
        print(f"Running {n_simulations} stochastic simulations...")
    
    for i in range(n_simulations):
        # Use different seed for each simulation
        seed = random_seed_base + i
        args_with_seed = simulation_args.copy()
        
        # Override seed in arguments
        if 'seed' in args_with_seed:
            args_with_seed['seed'] = seed
        else:
            # Try to add seed if not present (may not work for all functions)
            args_with_seed['seed'] = seed
        
        # Run simulation
        try:
            result_df = simulation_function(**args_with_seed)
            
            # Extract completion rate
            # Check if result_df has completion_rate column
            if 'completion_rate' in result_df.columns:
                completion_rate = result_df['completion_rate'].mean()
            else:
                # Extract from trajectories
                total_completed = 0
                total_trajectories = 0
                for _, row in result_df.iterrows():
                    trajectories = row.get('trajectories', [])
                    for traj in trajectories:
                        total_trajectories += 1
                        if traj.get('exit_step') == 'Completed':
                            total_completed += 1
                completion_rate = total_completed / total_trajectories if total_trajectories > 0 else 0.0
            
            completion_rates.append(completion_rate)
            
            if verbose and (i + 1) % 10 == 0:
                print(f"  Completed {i + 1}/{n_simulations} simulations...")
        
        except Exception as e:
            if verbose:
                print(f"  Warning: Simulation {i+1} failed: {e}")
            # Skip failed simulations
            continue
    
    if verbose:
        print(f"  Completed {len(completion_rates)}/{n_simulations} successful simulations")
    
    return completion_rates


def estimate_confidence_intervals(
    simulation_function: Callable,
    simulation_args: Dict,
    n_simulations: int = 50,
    random_seed_base: int = 42,
    product_steps: Optional[Dict] = None,
    verbose: bool = True
) -> ConfidenceEstimate:
    """
    Estimate confidence intervals by running stochastic simulations.
    
    Args:
        simulation_function: Function to run simulation
        simulation_args: Arguments for simulation function
        n_simulations: Number of stochastic runs
        random_seed_base: Base random seed
        product_steps: Optional product steps for extracting metrics
        verbose: Print progress
    
    Returns:
        ConfidenceEstimate with percentiles and stability score
    """
    # Run stochastic simulations
    completion_rates = run_stochastic_simulations(
        simulation_function,
        simulation_args,
        n_simulations=n_simulations,
        random_seed_base=random_seed_base,
        verbose=verbose
    )
    
    if not completion_rates:
        raise ValueError("No successful simulations completed")
    
    # Compute statistics
    completion_array = np.array(completion_rates)
    mean_completion = np.mean(completion_array)
    variance = np.var(completion_array)
    std_dev = np.std(completion_array)
    
    # Compute percentiles
    p10 = np.percentile(completion_array, 10)
    p25 = np.percentile(completion_array, 25)
    p50 = np.percentile(completion_array, 50)  # median
    p75 = np.percentile(completion_array, 75)
    p90 = np.percentile(completion_array, 90)
    
    # Compute stability score: 1 - normalized variance
    # Normalize variance by max possible variance for completion rate (0-1 range)
    # Max variance occurs when outcomes are perfectly split (0.25)
    max_variance = 0.25  # For a 0-1 bounded variable
    normalized_variance = min(1.0, variance / max_variance)
    stability_score = 1.0 - normalized_variance
    
    return ConfidenceEstimate(
        mean_completion=mean_completion,
        p10=p10,
        p25=p25,
        p50=p50,
        p75=p75,
        p90=p90,
        variance=variance,
        std_dev=std_dev,
        stability_score=stability_score,
        n_simulations=len(completion_rates)
    )


def estimate_step_level_confidence(
    simulation_function: Callable,
    simulation_args: Dict,
    product_steps: Dict,
    n_simulations: int = 50,
    random_seed_base: int = 42,
    verbose: bool = True
) -> Dict[str, ConfidenceEstimate]:
    """
    Estimate confidence intervals for each step's drop-off rate.
    
    Args:
        simulation_function: Function to run simulation
        simulation_args: Arguments for simulation function
        product_steps: Dict of step definitions
        n_simulations: Number of stochastic runs
        random_seed_base: Base random seed
        verbose: Print progress
    
    Returns:
        Dict mapping step_name -> ConfidenceEstimate for drop-off rate
    """
    step_dropoff_rates = defaultdict(list)
    
    if verbose:
        print(f"Running {n_simulations} stochastic simulations for step-level confidence...")
    
    step_names = list(product_steps.keys())
    
    for i in range(n_simulations):
        seed = random_seed_base + i
        args_with_seed = simulation_args.copy()
        args_with_seed['seed'] = seed
        
        try:
            result_df = simulation_function(**args_with_seed)
            
            # Extract step-level metrics
            simulated_metrics = extract_simulated_metrics_from_results(result_df, product_steps)
            dropoff_by_step = simulated_metrics.get('dropoff_by_step', {})
            
            for step_name in step_names:
                dropoff_rate = dropoff_by_step.get(step_name, 0.0)
                step_dropoff_rates[step_name].append(dropoff_rate)
            
            if verbose and (i + 1) % 10 == 0:
                print(f"  Completed {i + 1}/{n_simulations} simulations...")
        
        except Exception as e:
            if verbose:
                print(f"  Warning: Simulation {i+1} failed: {e}")
            continue
    
    # Compute confidence estimates for each step
    step_confidence = {}
    
    for step_name, dropoff_rates in step_dropoff_rates.items():
        if not dropoff_rates:
            continue
        
        dropoff_array = np.array(dropoff_rates)
        mean_dropoff = np.mean(dropoff_array)
        variance = np.var(dropoff_array)
        std_dev = np.std(dropoff_array)
        
        p10 = np.percentile(dropoff_array, 10)
        p25 = np.percentile(dropoff_array, 25)
        p50 = np.percentile(dropoff_array, 50)
        p75 = np.percentile(dropoff_array, 75)
        p90 = np.percentile(dropoff_array, 90)
        
        # Stability score for drop-off rate
        max_variance = 0.25  # Max variance for 0-1 bounded variable
        normalized_variance = min(1.0, variance / max_variance)
        stability_score = 1.0 - normalized_variance
        
        step_confidence[step_name] = ConfidenceEstimate(
            mean_completion=mean_dropoff,  # Using mean_completion field for dropoff rate
            p10=p10,
            p25=p25,
            p50=p50,
            p75=p75,
            p90=p90,
            variance=variance,
            std_dev=std_dev,
            stability_score=stability_score,
            n_simulations=len(dropoff_rates)
        )
    
    return step_confidence


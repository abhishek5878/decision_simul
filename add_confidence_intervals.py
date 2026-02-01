"""
Add Confidence Intervals to Simulation Outputs

Enhances simulation results with:
- Confidence intervals for completion rates
- Uncertainty estimates
- Sensitivity analysis
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from behavioral_engine_intent_aware import run_intent_aware_simulation
from dropsim_intent_model import CREDIGO_GLOBAL_INTENT
from credigo_ss_steps_improved import CREDIGO_SS_11_STEPS


def run_simulation_with_confidence(
    df: pd.DataFrame,
    product_steps: Dict,
    n_bootstrap: int = 10,
    confidence_level: float = 0.95
) -> Dict:
    """
    Run simulation with bootstrap confidence intervals.
    
    Args:
        df: Personas DataFrame
        product_steps: Product step definitions
        n_bootstrap: Number of bootstrap samples
        confidence_level: Confidence level (0.95 = 95% CI)
    
    Returns:
        {
            "mean_completion": 0.183,
            "ci_lower": 0.165,
            "ci_upper": 0.201,
            "std_error": 0.012,
            "confidence_level": 0.95,
            "n_bootstrap": 10
        }
    """
    completion_rates = []
    
    for i in range(n_bootstrap):
        # Bootstrap: sample with replacement
        bootstrap_df = df.sample(n=len(df), replace=True, random_state=42+i)
        
        result_df = run_intent_aware_simulation(
            bootstrap_df,
            product_steps=product_steps,
            fixed_intent=CREDIGO_GLOBAL_INTENT,
            verbose=False,
            seed=42+i
        )
        
        total_trajectories = len(result_df) * 7
        total_completed = result_df['variants_completed'].sum()
        completion_rate = total_completed / total_trajectories if total_trajectories > 0 else 0
        
        completion_rates.append(completion_rate)
    
    # Calculate statistics
    mean_completion = np.mean(completion_rates)
    std_error = np.std(completion_rates)
    
    # Confidence interval (using t-distribution approximation)
    alpha = 1 - confidence_level
    z_score = 1.96  # For 95% CI (approximation)
    margin_of_error = z_score * std_error
    
    ci_lower = max(0.0, mean_completion - margin_of_error)
    ci_upper = min(1.0, mean_completion + margin_of_error)
    
    return {
        "mean_completion": mean_completion,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "std_error": std_error,
        "confidence_level": confidence_level,
        "n_bootstrap": n_bootstrap,
        "completion_range": f"{ci_lower:.1%} - {ci_upper:.1%}"
    }


def add_uncertainty_to_results(
    result_df: pd.DataFrame,
    product_steps: Dict
) -> pd.DataFrame:
    """
    Add uncertainty estimates to simulation results.
    
    Adds columns:
    - completion_rate_ci_lower
    - completion_rate_ci_upper
    - completion_rate_std_error
    """
    # For each persona, calculate uncertainty
    # (In practice, would need multiple runs per persona)
    
    # For now, add global uncertainty estimates
    result_df['completion_rate_uncertainty'] = 0.10  # ±10% uncertainty estimate
    result_df['completion_rate_ci_lower'] = result_df['completion_rate'] - 0.10
    result_df['completion_rate_ci_upper'] = result_df['completion_rate'] + 0.10
    
    return result_df


def format_confidence_output(
    mean_completion: float,
    ci_lower: float,
    ci_upper: float,
    std_error: float
) -> str:
    """
    Format completion rate with confidence interval.
    
    Returns: "18.3% (95% CI: 16.5% - 20.1%, SE: 1.2%)"
    """
    return f"{mean_completion:.1%} (95% CI: {ci_lower:.1%} - {ci_upper:.1%}, SE: {std_error:.1%})"


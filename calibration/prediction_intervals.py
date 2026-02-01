"""
prediction_intervals.py - Prediction Intervals and Confidence Bands

Provides methods to get prediction intervals at specified confidence levels.
"""

import numpy as np
from typing import Dict, Tuple, Optional
from dataclasses import dataclass

from calibration.confidence_estimation import ConfidenceEstimate


@dataclass
class PredictionInterval:
    """Prediction interval for a metric."""
    lower_bound: float
    median: float
    upper_bound: float
    confidence_level: float  # e.g., 0.90 for 90% confidence
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'lower_bound': float(self.lower_bound),
            'median': float(self.median),
            'upper_bound': float(self.upper_bound),
            'confidence_level': float(self.confidence_level)
        }


def get_prediction_interval(
    confidence_estimate: ConfidenceEstimate,
    confidence: float = 0.90
) -> PredictionInterval:
    """
    Get prediction interval from confidence estimate.
    
    Args:
        confidence_estimate: ConfidenceEstimate from stochastic simulations
        confidence: Confidence level (0.90 = 90% confidence interval)
    
    Returns:
        PredictionInterval with lower bound, median, upper bound
    """
    # Map confidence level to percentiles
    # 90% confidence = 5th to 95th percentile (2.5% tail on each side)
    # 95% confidence = 2.5th to 97.5th percentile
    # 80% confidence = 10th to 90th percentile
    
    if confidence == 0.90:
        lower_percentile = 5
        upper_percentile = 95
    elif confidence == 0.95:
        lower_percentile = 2.5
        upper_percentile = 97.5
    elif confidence == 0.80:
        lower_percentile = 10
        upper_percentile = 90
    else:
        # Generic: compute percentiles
        alpha = (1.0 - confidence) / 2.0
        lower_percentile = alpha * 100
        upper_percentile = (1.0 - alpha) * 100
    
    # Use existing percentiles if available, otherwise estimate
    # We have p10, p25, p50, p75, p90
    if lower_percentile <= 10:
        lower_bound = confidence_estimate.p10
    elif lower_percentile <= 25:
        # Interpolate between p10 and p25
        frac = (lower_percentile - 10) / (25 - 10)
        lower_bound = confidence_estimate.p10 + frac * (confidence_estimate.p25 - confidence_estimate.p10)
    else:
        # Use p25 as approximation
        lower_bound = confidence_estimate.p25
    
    if upper_percentile >= 90:
        upper_bound = confidence_estimate.p90
    elif upper_percentile >= 75:
        # Interpolate between p75 and p90
        frac = (upper_percentile - 75) / (90 - 75)
        upper_bound = confidence_estimate.p75 + frac * (confidence_estimate.p90 - confidence_estimate.p75)
    else:
        # Use p75 as approximation
        upper_bound = confidence_estimate.p75
    
    median = confidence_estimate.p50
    
    return PredictionInterval(
        lower_bound=lower_bound,
        median=median,
        upper_bound=upper_bound,
        confidence_level=confidence
    )


def get_prediction_interval_simple(
    mean: float,
    std_dev: float,
    confidence: float = 0.90
) -> PredictionInterval:
    """
    Get prediction interval from mean and standard deviation (Gaussian assumption).
    
    Args:
        mean: Mean value
        std_dev: Standard deviation
        confidence: Confidence level
    
    Returns:
        PredictionInterval
    """
    from scipy import stats
    
    try:
        # Use z-score for confidence interval
        alpha = 1.0 - confidence
        z_score = stats.norm.ppf(1.0 - alpha / 2.0)
        
        margin = z_score * std_dev
        lower_bound = max(0.0, mean - margin)
        upper_bound = min(1.0, mean + margin)
        median = mean
    except ImportError:
        # Fallback: use 2-sigma rule (rough approximation)
        if confidence == 0.90:
            z_score = 1.645
        elif confidence == 0.95:
            z_score = 1.96
        elif confidence == 0.80:
            z_score = 1.28
        else:
            z_score = 2.0  # Rough default
        
        margin = z_score * std_dev
        lower_bound = max(0.0, mean - margin)
        upper_bound = min(1.0, mean + margin)
        median = mean
    
    return PredictionInterval(
        lower_bound=lower_bound,
        median=median,
        upper_bound=upper_bound,
        confidence_level=confidence
    )


def get_prediction_intervals_for_steps(
    step_confidence_estimates: Dict[str, ConfidenceEstimate],
    confidence: float = 0.90
) -> Dict[str, PredictionInterval]:
    """
    Get prediction intervals for each step.
    
    Args:
        step_confidence_estimates: Dict mapping step_name -> ConfidenceEstimate
        confidence: Confidence level
    
    Returns:
        Dict mapping step_name -> PredictionInterval
    """
    intervals = {}
    
    for step_name, confidence_estimate in step_confidence_estimates.items():
        intervals[step_name] = get_prediction_interval(confidence_estimate, confidence)
    
    return intervals


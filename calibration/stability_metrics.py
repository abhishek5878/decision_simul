"""
stability_metrics.py - Stability Score Computation

Computes stability scores and interprets model reliability.
"""

import numpy as np
from typing import Dict, Optional
from dataclasses import dataclass

from calibration.confidence_estimation import ConfidenceEstimate


@dataclass
class StabilityAssessment:
    """Stability assessment with interpretation."""
    stability_score: float  # 0-1, higher is more stable
    interpretation: str  # "very stable", "moderately sensitive", "unstable"
    variance: float
    std_dev: float
    coefficient_of_variation: float  # std_dev / mean
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'stability_score': float(self.stability_score),
            'interpretation': self.interpretation,
            'variance': float(self.variance),
            'std_dev': float(self.std_dev),
            'coefficient_of_variation': float(self.coefficient_of_variation)
        }


def compute_stability_score(variance: float, max_variance: float = 0.25) -> float:
    """
    Compute stability score from variance.
    
    stability_score = 1 - normalized_variance
    
    Args:
        variance: Variance of predictions
        max_variance: Maximum possible variance (for normalization)
    
    Returns:
        Stability score [0, 1], where 1 = perfectly stable
    """
    normalized_variance = min(1.0, variance / max_variance)
    stability_score = 1.0 - normalized_variance
    return max(0.0, min(1.0, stability_score))  # Clamp to [0, 1]


def interpret_stability_score(stability_score: float) -> str:
    """
    Interpret stability score.
    
    Args:
        stability_score: Stability score [0, 1]
    
    Returns:
        Interpretation string
    """
    if stability_score >= 0.8:
        return "very_stable"
    elif stability_score >= 0.5:
        return "moderately_sensitive"
    else:
        return "unstable_or_overfitted"


def assess_stability(confidence_estimate: ConfidenceEstimate) -> StabilityAssessment:
    """
    Assess stability from confidence estimate.
    
    Args:
        confidence_estimate: ConfidenceEstimate from stochastic simulations
    
    Returns:
        StabilityAssessment with score and interpretation
    """
    stability_score = confidence_estimate.stability_score
    variance = confidence_estimate.variance
    std_dev = confidence_estimate.std_dev
    mean = confidence_estimate.mean_completion
    
    # Coefficient of variation
    cv = std_dev / mean if mean > 0 else float('inf')
    
    interpretation = interpret_stability_score(stability_score)
    
    return StabilityAssessment(
        stability_score=stability_score,
        interpretation=interpretation,
        variance=variance,
        std_dev=std_dev,
        coefficient_of_variation=cv
    )


def compute_aggregate_stability(
    step_confidence_estimates: Dict[str, ConfidenceEstimate]
) -> StabilityAssessment:
    """
    Compute aggregate stability across all steps.
    
    Args:
        step_confidence_estimates: Dict mapping step_name -> ConfidenceEstimate
    
    Returns:
        StabilityAssessment for aggregate
    """
    if not step_confidence_estimates:
        return StabilityAssessment(
            stability_score=0.0,
            interpretation="no_data",
            variance=0.0,
            std_dev=0.0,
            coefficient_of_variation=0.0
        )
    
    # Compute weighted average of stability scores
    stability_scores = [est.stability_score for est in step_confidence_estimates.values()]
    variances = [est.variance for est in step_confidence_estimates.values()]
    
    avg_stability_score = np.mean(stability_scores)
    avg_variance = np.mean(variances)
    avg_std_dev = np.sqrt(avg_variance)
    
    # Average mean for CV computation
    avg_mean = np.mean([est.mean_completion for est in step_confidence_estimates.values()])
    cv = avg_std_dev / avg_mean if avg_mean > 0 else float('inf')
    
    interpretation = interpret_stability_score(avg_stability_score)
    
    return StabilityAssessment(
        stability_score=avg_stability_score,
        interpretation=interpretation,
        variance=avg_variance,
        std_dev=avg_std_dev,
        coefficient_of_variation=cv
    )


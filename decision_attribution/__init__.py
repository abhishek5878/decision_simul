"""
Decision Attribution Module

Game-theoretic attribution of decision forces using Shapley values.
Answers: "Which internal forces caused this specific decision?"
"""

from decision_attribution.attribution_types import DecisionAttribution
from decision_attribution.attribution_model import LocalDecisionFunction
from decision_attribution.shap_attributor import compute_decision_attribution
from decision_attribution.attribution_utils import (
    aggregate_step_attribution,
    aggregate_decision_attribution,
    get_dominant_forces_by_step
)

__all__ = [
    'DecisionAttribution',
    'LocalDecisionFunction',
    'compute_decision_attribution',
    'aggregate_step_attribution',
    'aggregate_decision_attribution',
    'get_dominant_forces_by_step'
]


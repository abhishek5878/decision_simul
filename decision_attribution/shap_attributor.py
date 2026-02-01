"""
SHAP-based attribution using Shapley values (game-theoretic).

Computes local attribution for each decision without training.
Uses exact Shapley value computation for small feature sets.
"""

import numpy as np
from typing import Dict, List, Tuple
from itertools import combinations

from decision_attribution.attribution_types import DecisionAttribution
from decision_attribution.attribution_model import LocalDecisionFunction


def compute_shapley_values(
    decision_func: LocalDecisionFunction,
    features: Dict[str, float],
    baseline: Dict[str, float],
    step_index: int,
    total_steps: int,
    intent_alignment: float = 0.5
) -> Dict[str, float]:
    """
    Compute exact Shapley values for all features.
    
    Shapley value = average marginal contribution across all coalitions.
    
    Args:
        decision_func: Local decision function
        features: Current feature values
        baseline: Baseline (neutral) feature values
        step_index: Current step index
        total_steps: Total number of steps
        intent_alignment: Intent alignment score
    
    Returns:
        Dict mapping feature names to Shapley values
    """
    feature_names = decision_func.get_feature_names()
    n_features = len(feature_names)
    
    # Compute baseline probability
    baseline_prob = decision_func.compute_probability(
        baseline, step_index, total_steps, intent_alignment
    )
    
    # Compute final probability
    final_prob = decision_func.compute_probability(
        features, step_index, total_steps, intent_alignment
    )
    
    # Shapley values
    shap_values = {}
    
    # For each feature, compute Shapley value
    for feature_name in feature_names:
        shap_value = 0.0
        
        # Get all subsets that don't include this feature
        other_features = [f for f in feature_names if f != feature_name]
        
        # Compute marginal contribution for each subset size
        for subset_size in range(len(other_features) + 1):
            # Get all subsets of this size
            for subset in combinations(other_features, subset_size):
                # Create coalition without feature
                coalition_without = baseline.copy()
                for f in subset:
                    coalition_without[f] = features[f]
                
                # Create coalition with feature
                coalition_with = coalition_without.copy()
                coalition_with[feature_name] = features[feature_name]
                
                # Compute marginal contribution
                prob_without = decision_func.compute_probability(
                    coalition_without, step_index, total_steps, intent_alignment
                )
                prob_with = decision_func.compute_probability(
                    coalition_with, step_index, total_steps, intent_alignment
                )
                
                marginal_contrib = prob_with - prob_without
                
                # Weight by coalition size (Shapley formula)
                # Weight = 1 / (n * C(n-1, |S|))
                n = n_features
                s = len(subset)
                weight = 1.0 / (n * _binomial_coefficient(n - 1, s))
                
                shap_value += weight * marginal_contrib
        
        shap_values[feature_name] = shap_value
    
    return shap_values


def _binomial_coefficient(n: int, k: int) -> int:
    """Compute binomial coefficient C(n, k)."""
    if k < 0 or k > n:
        return 0
    if k == 0 or k == n:
        return 1
    
    # Use iterative computation
    result = 1
    for i in range(min(k, n - k)):
        result = result * (n - i) // (i + 1)
    return result


def get_baseline_features(step_index: int = 0, total_steps: int = 11) -> Dict[str, float]:
    """
    Get baseline (neutral) feature values.
    
    Baseline represents a neutral state where all forces are at midpoint.
    Can be adapted based on step context (early steps have different expectations).
    
    Args:
        step_index: Current step index (for adaptive baselines)
        total_steps: Total number of steps
    """
    baseline = {
        'cognitive_energy': 0.5,
        'intent_strength': 0.5,
        'effort_tolerance': 0.5,
        'risk_tolerance': 0.5,
        'trust_baseline': 0.5,
        'value_expectation': 0.5,
        'step_effort': 0.0,
        'step_risk': 0.0,
        'step_value': 0.0,
        'step_trust': 0.0,
        'intent_mismatch': 0.0
    }
    
    # Adaptive baseline: Early steps have higher expected trust
    if step_index < 3:
        baseline['trust_baseline'] = 0.6  # Higher trust expected at entry
    else:
        # Later steps: lower expected intent mismatch (users are committed)
        baseline['intent_mismatch'] = 0.1
    
    return baseline


def compute_decision_attribution(
    cognitive_state: Dict[str, float],
    step_forces: Dict[str, float],
    intent_info: Dict[str, float],
    step_id: str,
    step_index: int,
    total_steps: int,
    decision: str,  # "CONTINUE" or "DROP"
    final_probability: float,
    modifiers: Dict = None,
    intent_alignment: float = 0.5
) -> DecisionAttribution:
    """
    Compute game-theoretic attribution for a decision.
    
    Args:
        cognitive_state: Dict with cognitive_energy, perceived_risk, perceived_effort, etc.
        step_forces: Dict with step_effort, step_risk, step_value, step_trust
        intent_info: Dict with intent_strength, intent_mismatch
        step_id: Step identifier
        step_index: Current step index
        total_steps: Total number of steps
        decision: "CONTINUE" or "DROP"
        final_probability: Actual P(CONTINUE) that was used
        modifiers: Optional archetype modifiers
        intent_alignment: Intent alignment score
    
    Returns:
        DecisionAttribution object
    """
    # Build feature dict
    features = {
        'cognitive_energy': cognitive_state.get('cognitive_energy', 0.5),
        'intent_strength': intent_info.get('intent_strength', 0.5),
        'effort_tolerance': cognitive_state.get('effort_tolerance', 0.5),
        'risk_tolerance': cognitive_state.get('risk_tolerance', 0.5),
        'trust_baseline': cognitive_state.get('trust_baseline', 0.5),
        'value_expectation': cognitive_state.get('value_expectation', 0.5),
        'step_effort': step_forces.get('step_effort', 0.0),
        'step_risk': step_forces.get('step_risk', 0.0),
        'step_value': step_forces.get('step_value', 0.0),
        'step_trust': step_forces.get('step_trust', 0.0),
        'intent_mismatch': intent_info.get('intent_mismatch', 0.0)
    }
    
    # Get adaptive baseline (context-aware)
    baseline = get_baseline_features(step_index, total_steps)
    
    # Create decision function
    decision_func = LocalDecisionFunction(modifiers=modifiers)
    
    # Compute baseline probability
    baseline_prob = decision_func.compute_probability(
        baseline, step_index, total_steps, intent_alignment
    )
    
    # Compute Shapley values
    shap_values = compute_shapley_values(
        decision_func, features, baseline, step_index, total_steps, intent_alignment
    )
    
    # Map to force names (for readability)
    force_names = {
        'cognitive_energy': 'cognitive_energy',
        'intent_strength': 'intent',
        'effort_tolerance': 'effort_tolerance',
        'risk_tolerance': 'risk_tolerance',
        'trust_baseline': 'trust',
        'value_expectation': 'value',
        'step_effort': 'effort',
        'step_risk': 'risk',
        'step_value': 'value',
        'step_trust': 'trust',
        'intent_mismatch': 'intent_mismatch'
    }
    
    # Aggregate step forces with state tolerances (RAW VALUES)
    aggregated_shap_raw = {}
    for feature_name, shap_value in shap_values.items():
        force_name = force_names.get(feature_name, feature_name)
        if force_name in aggregated_shap_raw:
            # Combine state tolerance and step force
            aggregated_shap_raw[force_name] += shap_value
        else:
            aggregated_shap_raw[force_name] = shap_value
    
    # Store raw values for transparency
    total_contribution_magnitude = sum(abs(v) for v in aggregated_shap_raw.values())
    
    # Normalize to relative contributions (for DROP decisions, use absolute values)
    aggregated_shap_normalized = {}
    if decision == "DROP":
        # For drops, negative contributions matter
        total_abs = sum(abs(v) for v in aggregated_shap_raw.values())
        if total_abs > 0:
            aggregated_shap_normalized = {k: v / total_abs for k, v in aggregated_shap_raw.items()}
        else:
            aggregated_shap_normalized = aggregated_shap_raw.copy()
    else:
        # For continues, positive contributions matter
        total_pos = sum(max(0, v) for v in aggregated_shap_raw.values())
        if total_pos > 0:
            aggregated_shap_normalized = {k: max(0, v) / total_pos for k, v in aggregated_shap_raw.items()}
        else:
            aggregated_shap_normalized = aggregated_shap_raw.copy()
    
    # Rank dominant forces (using normalized values for readability)
    dominant_forces = sorted(
        aggregated_shap_normalized.items(),
        key=lambda x: abs(x[1]),
        reverse=True
    )
    
    return DecisionAttribution(
        step_id=step_id,
        decision=decision,
        baseline_probability=baseline_prob,
        final_probability=final_probability,
        shap_values=aggregated_shap_normalized,  # Normalized (percentages)
        shap_values_raw=aggregated_shap_raw,  # Raw SHAP values
        total_contribution=total_contribution_magnitude,  # Total magnitude
        dominant_forces=dominant_forces
    )


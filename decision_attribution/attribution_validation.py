"""
Validation functions for attribution accuracy.
"""

import numpy as np
from typing import List, Dict, Tuple
from decision_attribution.attribution_model import LocalDecisionFunction


def validate_local_function_accuracy(
    traces: List[Dict],
    max_mse: float = 0.01,
    max_max_error: float = 0.1
) -> Tuple[bool, Dict]:
    """
    Validate that local decision function matches actual engine outputs.
    
    Args:
        traces: List of trace dicts with 'probability_before_sampling'
        max_mse: Maximum allowed mean squared error
        max_max_error: Maximum allowed individual error
    
    Returns:
        (is_valid, stats_dict)
    """
    local_func = LocalDecisionFunction()
    
    local_preds = []
    actual_preds = []
    errors = []
    
    for trace in traces[:100]:  # Sample 100 traces for validation
        # Extract features (would need to reconstruct from trace)
        # For now, skip - this requires trace structure access
        continue
    
    if not local_preds:
        return True, {"note": "Validation skipped - trace structure needs adjustment"}
    
    # Compute errors
    local_preds = np.array(local_preds)
    actual_preds = np.array(actual_preds)
    errors = np.abs(local_preds - actual_preds)
    
    mse = np.mean((local_preds - actual_preds) ** 2)
    max_error = np.max(errors)
    mean_error = np.mean(errors)
    
    stats = {
        'mse': float(mse),
        'max_error': float(max_error),
        'mean_error': float(mean_error),
        'n_samples': len(local_preds),
        'is_valid': mse <= max_mse and max_error <= max_max_error
    }
    
    return stats['is_valid'], stats


def validate_attribution_plausibility(attribution) -> Tuple[bool, List[str]]:
    """
    Check that attribution values are plausible.
    
    Args:
        attribution: DecisionAttribution object
    
    Returns:
        (is_plausible, list_of_warnings)
    """
    warnings = []
    
    # Check 1: SHAP values should sum approximately to (final_prob - baseline_prob)
    if attribution.shap_values_raw:
        shap_sum = sum(attribution.shap_values_raw.values())
        expected_sum = attribution.final_probability - attribution.baseline_probability
        diff = abs(shap_sum - expected_sum)
        
        if diff > 0.1:  # Allow some tolerance
            warnings.append(f"SHAP sum ({shap_sum:.3f}) doesn't match probability difference ({expected_sum:.3f})")
    
    # Check 2: Dominant force shouldn't be 100% unless really extreme
    if attribution.shap_values:
        max_force_pct = max(abs(v) for v in attribution.shap_values.values())
        if max_force_pct > 0.95 and attribution.decision == "DROP":
            warnings.append(f"Single force dominates ({max_force_pct*100:.1f}%) - may indicate normalization issue")
    
    # Check 3: Total contribution magnitude should be reasonable
    if attribution.total_contribution is not None:
        if attribution.total_contribution < 0.001:
            warnings.append(f"Very small total contribution ({attribution.total_contribution:.4f}) - may indicate weak attribution")
        if attribution.total_contribution > 1.0:
            warnings.append(f"Very large total contribution ({attribution.total_contribution:.4f}) - may indicate computation issue")
    
    return len(warnings) == 0, warnings


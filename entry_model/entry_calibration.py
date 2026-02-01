"""
entry_calibration.py - Entry Model Calibration

Calibrates entry probability model parameters against observed entry rates.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

from entry_model.entry_model import compute_entry_probability
from entry_model.entry_signals import EntrySignals, TrafficSource, IntentStrength


@dataclass
class ObservedEntryData:
    """Observed entry data for calibration."""
    traffic_source: TrafficSource
    intent_strength: IntentStrength
    landing_page_promise_strength: float
    observed_entry_rate: float  # Observed P(entry)
    sample_size: int  # Number of visitors
    brand_trust_proxy: Optional[float] = None


@dataclass
class CalibrationResult:
    """Result from entry model calibration."""
    calibrated_weights: Dict[str, float]
    fit_score: float  # 1 - normalized_error
    errors_by_source: Dict[str, float]  # Error by traffic source
    errors_by_intent: Dict[str, float]  # Error by intent strength
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'calibrated_weights': {k: float(v) for k, v in self.calibrated_weights.items()},
            'fit_score': float(self.fit_score),
            'errors_by_source': {k: float(v) for k, v in self.errors_by_source.items()},
            'errors_by_intent': {k: float(v) for k, v in self.errors_by_intent.items()}
        }


def calibrate_entry_model(
    observed_data: List[ObservedEntryData],
    initial_weights: Optional[Dict[str, float]] = None
) -> CalibrationResult:
    """
    Calibrate entry model weights to match observed entry rates.
    
    Uses simple least squares optimization to find weights that minimize
    error between predicted and observed entry rates.
    
    Args:
        observed_data: List of observed entry data points
        initial_weights: Optional initial weights
    
    Returns:
        CalibrationResult with calibrated weights
    """
    if initial_weights is None:
        initial_weights = {
            'intent_match': 1.0,
            'source_quality': 1.0,
            'message_alignment': 1.0,
            'brand_trust': 1.0
        }
    
    # Simple grid search over weight space
    best_weights = initial_weights.copy()
    best_error = float('inf')
    
    # Search space: each weight in [0.5, 1.5]
    weight_range = np.linspace(0.5, 1.5, 5)
    
    for intent_w in weight_range:
        for source_w in weight_range:
            for message_w in weight_range:
                for trust_w in weight_range:
                    weights = {
                        'intent_match': intent_w,
                        'source_quality': source_w,
                        'message_alignment': message_w,
                        'brand_trust': trust_w
                    }
                    
                    # Compute total error
                    total_error = 0.0
                    total_weight = 0.0
                    
                    for data_point in observed_data:
                        signals = EntrySignals(
                            traffic_source=data_point.traffic_source,
                            intent_strength=data_point.intent_strength,
                            landing_page_promise_strength=data_point.landing_page_promise_strength,
                            brand_trust_proxy=data_point.brand_trust_proxy
                        )
                        
                        result = compute_entry_probability(signals, weights)
                        predicted = result.entry_probability
                        observed = data_point.observed_entry_rate
                        
                        # Weighted error (by sample size)
                        weight = data_point.sample_size
                        error = abs(predicted - observed) * weight
                        total_error += error
                        total_weight += weight
                    
                    avg_error = total_error / total_weight if total_weight > 0 else float('inf')
                    
                    if avg_error < best_error:
                        best_error = avg_error
                        best_weights = weights
    
    # Compute errors by source and intent
    errors_by_source = defaultdict(list)
    errors_by_intent = defaultdict(list)
    
    for data_point in observed_data:
        signals = EntrySignals(
            traffic_source=data_point.traffic_source,
            intent_strength=data_point.intent_strength,
            landing_page_promise_strength=data_point.landing_page_promise_strength,
            brand_trust_proxy=data_point.brand_trust_proxy
        )
        
        result = compute_entry_probability(signals, best_weights)
        predicted = result.entry_probability
        observed = data_point.observed_entry_rate
        error = abs(predicted - observed)
        
        errors_by_source[data_point.traffic_source.value].append(error)
        errors_by_intent[data_point.intent_strength.value].append(error)
    
    # Average errors
    errors_by_source_avg = {
        source: np.mean(errors) for source, errors in errors_by_source.items()
    }
    errors_by_intent_avg = {
        intent: np.mean(errors) for intent, errors in errors_by_intent.items()
    }
    
    # Compute fit score (1 - normalized error)
    max_possible_error = 1.0  # Max error is 1.0 (0% vs 100%)
    normalized_error = min(1.0, best_error / max_possible_error)
    fit_score = 1.0 - normalized_error
    
    return CalibrationResult(
        calibrated_weights=best_weights,
        fit_score=fit_score,
        errors_by_source=errors_by_source_avg,
        errors_by_intent=errors_by_intent_avg
    )


def load_calibrated_weights(filepath: str) -> Dict[str, float]:
    """Load calibrated weights from JSON file."""
    import json
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            return data.get('calibrated_weights', {
                'intent_match': 1.0,
                'source_quality': 1.0,
                'message_alignment': 1.0,
                'brand_trust': 1.0
            })
    except FileNotFoundError:
        return {
            'intent_match': 1.0,
            'source_quality': 1.0,
            'message_alignment': 1.0,
            'brand_trust': 1.0
        }


def save_calibrated_weights(weights: Dict[str, float], filepath: str):
    """Save calibrated weights to JSON file."""
    import json
    with open(filepath, 'w') as f:
        json.dump({'calibrated_weights': weights}, f, indent=2)


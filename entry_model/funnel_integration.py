"""
funnel_integration.py - Integration of Entry Model with Behavioral Engine

Combines entry probability with behavioral completion probability:
Total Conversion = P(entry) × P(completion | entry)
"""

import json
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime

from entry_model.entry_model import EntryProbabilityResult, estimate_entry_probability
from entry_model.entry_signals import extract_entry_signals


@dataclass
class FullFunnelPrediction:
    """Full funnel prediction combining entry and completion."""
    entry_probability: float  # P(entry)
    completion_probability: float  # P(completion | entry)
    total_conversion: float  # P(entry) × P(completion | entry)
    entry_result: EntryProbabilityResult
    completion_metrics: Dict  # Metrics from behavioral engine
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'entry_probability': float(self.entry_probability),
            'completion_probability': float(self.completion_probability),
            'total_conversion': float(self.total_conversion),
            'entry_result': self.entry_result.to_dict(),
            'completion_metrics': self.completion_metrics
        }


def compute_full_funnel_prediction(
    entry_signals: Dict,
    behavioral_completion_rate: float,
    calibrated_entry_weights: Optional[Dict[str, float]] = None
) -> FullFunnelPrediction:
    """
    Compute full funnel prediction.
    
    Args:
        entry_signals: Dict with entry signal inputs (referrer, utm_source, etc.)
        behavioral_completion_rate: Completion rate from behavioral engine (P(completion | entry))
        calibrated_entry_weights: Optional calibrated weights for entry model
    
    Returns:
        FullFunnelPrediction
    """
    # Estimate entry probability
    entry_result = estimate_entry_probability(
        referrer=entry_signals.get('referrer'),
        utm_source=entry_signals.get('utm_source'),
        utm_medium=entry_signals.get('utm_medium'),
        intent_frame=entry_signals.get('intent_frame'),
        search_query=entry_signals.get('search_query'),
        landing_page_text=entry_signals.get('landing_page_text'),
        cta_text=entry_signals.get('cta_text'),
        value_propositions=entry_signals.get('value_propositions'),
        brand_awareness=entry_signals.get('brand_awareness'),
        domain_age=entry_signals.get('domain_age'),
        has_trust_signals=entry_signals.get('has_trust_signals'),
        calibrated_weights=calibrated_entry_weights
    )
    
    # Compute total conversion
    entry_prob = entry_result.entry_probability
    completion_prob = behavioral_completion_rate
    total_conversion = entry_prob * completion_prob
    
    return FullFunnelPrediction(
        entry_probability=entry_prob,
        completion_probability=completion_prob,
        total_conversion=total_conversion,
        entry_result=entry_result,
        completion_metrics={
            'completion_rate': completion_prob,
            'source': 'behavioral_engine'
        }
    )


def export_entry_probability(
    entry_result: EntryProbabilityResult,
    filepath: str = 'entry_probability.json'
):
    """Export entry probability result to JSON."""
    export_dict = {
        'timestamp': datetime.now().isoformat(),
        'entry_probability': entry_result.to_dict()
    }
    
    with open(filepath, 'w') as f:
        json.dump(export_dict, f, indent=2)
    
    return export_dict


def export_entry_diagnostics(
    entry_result: EntryProbabilityResult,
    filepath: str = 'entry_diagnostics.json'
):
    """Export entry diagnostics to JSON."""
    diagnostics = {
        'timestamp': datetime.now().isoformat(),
        'entry_probability': entry_result.entry_probability,
        'confidence': entry_result.confidence,
        'drivers': entry_result.drivers,
        'signals': entry_result.signals.to_dict(),
        'interpretation': {
            'traffic_source': entry_result.signals.traffic_source.value,
            'intent_strength': entry_result.signals.intent_strength.value,
            'promise_strength': entry_result.signals.landing_page_promise_strength,
            'primary_driver': max(entry_result.drivers.items(), key=lambda x: x[1])[0] if entry_result.drivers else 'unknown'
        }
    }
    
    with open(filepath, 'w') as f:
        json.dump(diagnostics, f, indent=2)
    
    return diagnostics


def export_full_funnel_prediction(
    prediction: FullFunnelPrediction,
    filepath: str = 'full_funnel_prediction.json'
):
    """Export full funnel prediction to JSON."""
    export_dict = {
        'timestamp': datetime.now().isoformat(),
        'full_funnel_prediction': prediction.to_dict(),
        'breakdown': {
            'entry_probability': prediction.entry_probability,
            'completion_probability': prediction.completion_probability,
            'total_conversion': prediction.total_conversion,
            'funnel_stage': {
                'visitors': 1000,  # Example: 1000 visitors
                'entries': int(1000 * prediction.entry_probability),
                'completions': int(1000 * prediction.total_conversion)
            }
        }
    }
    
    with open(filepath, 'w') as f:
        json.dump(export_dict, f, indent=2)
    
    return export_dict


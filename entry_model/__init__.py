"""
entry_model - Pre-Behavioral Entry Layer

Models P(entry | traffic_source, context, intent).
Separates entry probability from in-funnel behavioral completion.
"""

from entry_model.entry_signals import (
    EntrySignals,
    TrafficSource,
    IntentStrength,
    extract_entry_signals,
    extract_traffic_source,
    extract_intent_strength,
    extract_landing_page_promise_strength,
    extract_brand_trust_proxy
)

from entry_model.entry_model import (
    EntryProbabilityResult,
    compute_entry_probability,
    estimate_entry_probability,
    compute_confidence
)

from entry_model.entry_calibration import (
    ObservedEntryData,
    CalibrationResult,
    calibrate_entry_model,
    load_calibrated_weights,
    save_calibrated_weights
)

__all__ = [
    # Signals
    'EntrySignals',
    'TrafficSource',
    'IntentStrength',
    'extract_entry_signals',
    'extract_traffic_source',
    'extract_intent_strength',
    'extract_landing_page_promise_strength',
    'extract_brand_trust_proxy',
    
    # Entry model
    'EntryProbabilityResult',
    'compute_entry_probability',
    'estimate_entry_probability',
    'compute_confidence',
    
    # Calibration
    'ObservedEntryData',
    'CalibrationResult',
    'calibrate_entry_model',
    'load_calibrated_weights',
    'save_calibrated_weights'
]


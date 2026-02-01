"""
entry_model.py - Entry Probability Model

Models P(entry | traffic_source, context, intent).
This is separate from behavioral completion probability.
"""

import numpy as np
from typing import Dict, Optional, List
from dataclasses import dataclass

from entry_model.entry_signals import (
    EntrySignals,
    TrafficSource,
    IntentStrength
)


@dataclass
class EntryProbabilityResult:
    """Result from entry probability estimation."""
    entry_probability: float  # P(entry)
    confidence: float  # Confidence in estimate [0, 1]
    drivers: Dict[str, float]  # Contribution of each driver
    signals: EntrySignals  # Input signals
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'entry_probability': float(self.entry_probability),
            'confidence': float(self.confidence),
            'drivers': {k: float(v) for k, v in self.drivers.items()},
            'signals': self.signals.to_dict()
        }


# ============================================================================
# BASE ENTRY PROBABILITIES BY TRAFFIC SOURCE
# ============================================================================

BASE_ENTRY_PROBABILITIES = {
    TrafficSource.ADS: 0.15,  # Paid ads: lower intent, higher bounce
    TrafficSource.SEO: 0.35,  # Organic search: higher intent
    TrafficSource.REFERRAL: 0.40,  # Referrals: high trust
    TrafficSource.DIRECT: 0.50,  # Direct: highest intent
    TrafficSource.SOCIAL: 0.12,  # Social: low intent, exploratory
    TrafficSource.EMAIL: 0.30,  # Email: medium intent
    TrafficSource.UNKNOWN: 0.25  # Unknown: default
}


# ============================================================================
# INTENT STRENGTH MULTIPLIERS
# ============================================================================

INTENT_MULTIPLIERS = {
    IntentStrength.HIGH: 1.4,  # High intent → 40% boost
    IntentStrength.MEDIUM: 1.0,  # Medium intent → no change
    IntentStrength.LOW: 0.7,  # Low intent → 30% reduction
    IntentStrength.UNKNOWN: 0.9  # Unknown → slight reduction
}


# ============================================================================
# PROMISE STRENGTH MULTIPLIERS
# ============================================================================

def get_promise_multiplier(promise_strength: float) -> float:
    """
    Get multiplier based on promise strength.
    
    Args:
        promise_strength: Promise strength [0, 1]
    
    Returns:
        Multiplier [0.7, 1.3]
    """
    # Linear mapping: 0.0 → 0.7x, 1.0 → 1.3x
    return 0.7 + (promise_strength * 0.6)


# ============================================================================
# BRAND TRUST MULTIPLIERS
# ============================================================================

def get_brand_trust_multiplier(brand_trust: Optional[float]) -> float:
    """
    Get multiplier based on brand trust.
    
    Args:
        brand_trust: Brand trust proxy [0, 1] or None
    
    Returns:
        Multiplier [0.9, 1.2]
    """
    if brand_trust is None:
        return 1.0  # No effect if unknown
    
    # Linear mapping: 0.0 → 0.9x, 1.0 → 1.2x
    return 0.9 + (brand_trust * 0.3)


# ============================================================================
# MAIN ENTRY PROBABILITY MODEL
# ============================================================================

def compute_entry_probability(
    signals: EntrySignals,
    calibrated_weights: Optional[Dict[str, float]] = None
) -> EntryProbabilityResult:
    """
    Compute entry probability from entry signals.
    
    Formula:
    P(entry) = base_prob × intent_mult × promise_mult × trust_mult
    
    Then clamped to [0.01, 0.95]
    
    Args:
        signals: EntrySignals object
        calibrated_weights: Optional calibrated weights for drivers
    
    Returns:
        EntryProbabilityResult with probability and drivers
    """
    if calibrated_weights is None:
        calibrated_weights = {
            'intent_match': 1.0,
            'source_quality': 1.0,
            'message_alignment': 1.0,
            'brand_trust': 1.0
        }
    
    # 1. Base probability from traffic source
    base_prob = BASE_ENTRY_PROBABILITIES[signals.traffic_source]
    source_contribution = base_prob
    
    # 2. Intent strength multiplier
    intent_mult = INTENT_MULTIPLIERS[signals.intent_strength]
    intent_contribution = (intent_mult - 1.0) * base_prob  # Contribution amount
    
    # 3. Promise strength multiplier
    promise_mult = get_promise_multiplier(signals.landing_page_promise_strength)
    promise_contribution = (promise_mult - 1.0) * base_prob
    
    # 4. Brand trust multiplier
    trust_mult = get_brand_trust_multiplier(signals.brand_trust_proxy)
    trust_contribution = (trust_mult - 1.0) * base_prob
    
    # Apply calibrated weights
    intent_contribution *= calibrated_weights.get('intent_match', 1.0)
    promise_contribution *= calibrated_weights.get('message_alignment', 1.0)
    trust_contribution *= calibrated_weights.get('brand_trust', 1.0)
    source_contribution *= calibrated_weights.get('source_quality', 1.0)
    
    # Compute final probability
    entry_prob = base_prob + intent_contribution + promise_contribution + trust_contribution
    
    # Clamp to valid range
    entry_prob = np.clip(entry_prob, 0.01, 0.95)
    
    # Compute drivers (normalized contributions)
    total_contribution = abs(intent_contribution) + abs(promise_contribution) + abs(trust_contribution) + abs(source_contribution)
    
    if total_contribution > 0:
        drivers = {
            'intent_match': abs(intent_contribution) / total_contribution,
            'source_quality': abs(source_contribution) / total_contribution,
            'message_alignment': abs(promise_contribution) / total_contribution,
            'brand_trust': abs(trust_contribution) / total_contribution
        }
    else:
        drivers = {
            'intent_match': 0.25,
            'source_quality': 0.25,
            'message_alignment': 0.25,
            'brand_trust': 0.25
        }
    
    # Compute confidence (based on signal completeness)
    confidence = compute_confidence(signals)
    
    return EntryProbabilityResult(
        entry_probability=entry_prob,
        confidence=confidence,
        drivers=drivers,
        signals=signals
    )


def compute_confidence(signals: EntrySignals) -> float:
    """
    Compute confidence in entry probability estimate.
    
    Higher confidence when:
    - Traffic source is known (not UNKNOWN)
    - Intent strength is known (not UNKNOWN)
    - Brand trust is provided
    - Multiple signals are available
    
    Args:
        signals: EntrySignals object
    
    Returns:
        Confidence [0, 1]
    """
    confidence = 0.5  # Base confidence
    
    # Traffic source known
    if signals.traffic_source != TrafficSource.UNKNOWN:
        confidence += 0.2
    
    # Intent strength known
    if signals.intent_strength != IntentStrength.UNKNOWN:
        confidence += 0.15
    
    # Brand trust provided
    if signals.brand_trust_proxy is not None:
        confidence += 0.1
    
    # Additional signals
    if signals.device_type is not None:
        confidence += 0.025
    if signals.platform is not None:
        confidence += 0.025
    
    return min(1.0, confidence)


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def estimate_entry_probability(
    referrer: Optional[str] = None,
    utm_source: Optional[str] = None,
    utm_medium: Optional[str] = None,
    intent_frame: Optional[Dict] = None,
    search_query: Optional[str] = None,
    landing_page_text: Optional[str] = None,
    cta_text: Optional[str] = None,
    value_propositions: Optional[List[str]] = None,
    brand_awareness: Optional[float] = None,
    domain_age: Optional[int] = None,
    has_trust_signals: Optional[bool] = None,
    calibrated_weights: Optional[Dict[str, float]] = None
) -> EntryProbabilityResult:
    """
    Convenience function to estimate entry probability from raw inputs.
    
    Args:
        referrer: HTTP referrer
        utm_source: UTM source
        utm_medium: UTM medium
        intent_frame: Intent frame
        search_query: Search query
        landing_page_text: Landing page text
        cta_text: CTA text
        value_propositions: Value propositions
        brand_awareness: Brand awareness
        domain_age: Domain age
        has_trust_signals: Has trust signals
        calibrated_weights: Optional calibrated weights
    
    Returns:
        EntryProbabilityResult
    """
    from entry_model.entry_signals import extract_entry_signals
    
    signals = extract_entry_signals(
        referrer=referrer,
        utm_source=utm_source,
        utm_medium=utm_medium,
        intent_frame=intent_frame,
        search_query=search_query,
        landing_page_text=landing_page_text,
        cta_text=cta_text,
        value_propositions=value_propositions,
        brand_awareness=brand_awareness,
        domain_age=domain_age,
        has_trust_signals=has_trust_signals
    )
    
    return compute_entry_probability(signals, calibrated_weights)


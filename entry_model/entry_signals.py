"""
entry_signals.py - Entry-Level Signal Extraction

Extracts coarse, high-level signals for entry probability estimation.
These signals are independent of downstream behavioral factors.
"""

from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum


class TrafficSource(Enum):
    """Traffic source types."""
    ADS = "ads"  # Paid advertising
    SEO = "seo"  # Organic search
    REFERRAL = "referral"  # Referral/link
    DIRECT = "direct"  # Direct navigation
    SOCIAL = "social"  # Social media
    EMAIL = "email"  # Email campaign
    UNKNOWN = "unknown"


class IntentStrength(Enum):
    """User intent strength levels."""
    HIGH = "high"  # Strong, specific intent
    MEDIUM = "medium"  # Moderate intent
    LOW = "low"  # Weak, exploratory intent
    UNKNOWN = "unknown"


@dataclass
class EntrySignals:
    """Entry-level signals for probability estimation."""
    traffic_source: TrafficSource
    intent_strength: IntentStrength
    landing_page_promise_strength: float  # 0-1, how strong is the value promise
    brand_trust_proxy: Optional[float] = None  # 0-1, brand awareness/trust
    device_type: Optional[str] = None  # "mobile", "desktop", "tablet"
    platform: Optional[str] = None  # "web", "app"
    market_maturity: Optional[str] = None  # "early", "mature", "saturated"
    referral_quality: Optional[float] = None  # 0-1, quality of referral source
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'traffic_source': self.traffic_source.value,
            'intent_strength': self.intent_strength.value,
            'landing_page_promise_strength': self.landing_page_promise_strength,
            'brand_trust_proxy': self.brand_trust_proxy,
            'device_type': self.device_type,
            'platform': self.platform,
            'market_maturity': self.market_maturity,
            'referral_quality': self.referral_quality
        }


def extract_traffic_source(
    referrer: Optional[str] = None,
    utm_source: Optional[str] = None,
    utm_medium: Optional[str] = None
) -> TrafficSource:
    """
    Extract traffic source from referrer/UTM parameters.
    
    Args:
        referrer: HTTP referrer
        utm_source: UTM source parameter
        utm_medium: UTM medium parameter
    
    Returns:
        TrafficSource enum
    """
    # Check UTM parameters first (more reliable)
    if utm_source:
        source_lower = utm_source.lower()
        medium_lower = utm_medium.lower() if utm_medium else ""
        
        if 'google' in source_lower or 'bing' in source_lower:
            if 'cpc' in medium_lower or 'paid' in medium_lower or 'ad' in medium_lower:
                return TrafficSource.ADS
            else:
                return TrafficSource.SEO
        
        if 'facebook' in source_lower or 'instagram' in source_lower or 'twitter' in source_lower:
            return TrafficSource.SOCIAL
        
        if 'email' in medium_lower or 'mail' in medium_lower:
            return TrafficSource.EMAIL
        
        if 'referral' in medium_lower or 'partner' in source_lower:
            return TrafficSource.REFERRAL
    
    # Check referrer
    if referrer:
        referrer_lower = referrer.lower()
        
        if 'google' in referrer_lower or 'bing' in referrer_lower:
            return TrafficSource.SEO
        
        if 'facebook' in referrer_lower or 'twitter' in referrer_lower:
            return TrafficSource.SOCIAL
        
        if referrer_lower and referrer_lower != 'direct':
            return TrafficSource.REFERRAL
    
    # Default
    if not referrer or referrer.lower() == 'direct':
        return TrafficSource.DIRECT
    
    return TrafficSource.UNKNOWN


def extract_intent_strength(
    intent_frame: Optional[Dict] = None,
    search_query: Optional[str] = None,
    landing_page_text: Optional[str] = None
) -> IntentStrength:
    """
    Extract intent strength from available signals.
    
    Args:
        intent_frame: Intent frame from intent model
        search_query: Search query (if from search)
        landing_page_text: Landing page text
    
    Returns:
        IntentStrength enum
    """
    # If we have intent frame, use commitment threshold as proxy
    if intent_frame:
        if isinstance(intent_frame, dict):
            commitment = intent_frame.get('commitment_threshold', 0.5)
            tolerance = intent_frame.get('tolerance_for_effort', 0.5)
            
            # High commitment + high tolerance = high intent
            if commitment > 0.7 and tolerance > 0.6:
                return IntentStrength.HIGH
            elif commitment > 0.4 or tolerance > 0.4:
                return IntentStrength.MEDIUM
            else:
                return IntentStrength.LOW
        else:
            # IntentFrame object
            commitment = getattr(intent_frame, 'commitment_threshold', 0.5)
            tolerance = getattr(intent_frame, 'tolerance_for_effort', 0.5)
            
            if commitment > 0.7 and tolerance > 0.6:
                return IntentStrength.HIGH
            elif commitment > 0.4 or tolerance > 0.4:
                return IntentStrength.MEDIUM
            else:
                return IntentStrength.LOW
    
    # Check search query specificity
    if search_query:
        query_lower = search_query.lower()
        # Specific queries indicate higher intent
        specific_indicators = ['best', 'compare', 'review', 'apply', 'get', 'find']
        if any(indicator in query_lower for indicator in specific_indicators):
            return IntentStrength.HIGH
        elif len(query_lower.split()) >= 3:  # Longer queries = more specific
            return IntentStrength.MEDIUM
        else:
            return IntentStrength.LOW
    
    # Default to medium if we have landing page but no other signals
    if landing_page_text:
        return IntentStrength.MEDIUM
    
    return IntentStrength.UNKNOWN


def extract_landing_page_promise_strength(
    landing_page_text: Optional[str] = None,
    cta_text: Optional[str] = None,
    value_propositions: Optional[List[str]] = None
) -> float:
    """
    Extract landing page promise strength (0-1).
    
    Strong promises: "60 seconds", "No PAN required", "Best match", "Free"
    Weak promises: Generic, vague, no time/value commitment
    
    Args:
        landing_page_text: Landing page text
        cta_text: Call-to-action text
        value_propositions: List of value propositions
    
    Returns:
        Promise strength [0, 1]
    """
    strength = 0.5  # Default medium
    
    text_to_check = ""
    if landing_page_text:
        text_to_check += landing_page_text.lower() + " "
    if cta_text:
        text_to_check += cta_text.lower() + " "
    if value_propositions:
        text_to_check += " ".join(vp.lower() for vp in value_propositions) + " "
    
    if not text_to_check:
        return 0.3  # Low if no text
    
    # Strong promise indicators
    strong_indicators = [
        '60 second', 'instant', 'immediate', 'no pan', 'no data',
        'best match', 'personalized', 'free', 'no fee', 'guaranteed',
        'top rated', 'exclusive', 'limited time'
    ]
    
    # Weak promise indicators
    weak_indicators = [
        'maybe', 'might', 'could', 'possibly', 'explore', 'browse',
        'learn more', 'see more', 'discover'
    ]
    
    strong_count = sum(1 for indicator in strong_indicators if indicator in text_to_check)
    weak_count = sum(1 for indicator in weak_indicators if indicator in text_to_check)
    
    # Adjust strength
    if strong_count > 0:
        strength += min(0.4, strong_count * 0.1)
    if weak_count > 0:
        strength -= min(0.3, weak_count * 0.1)
    
    # Clamp to [0, 1]
    return max(0.0, min(1.0, strength))


def extract_brand_trust_proxy(
    brand_awareness: Optional[float] = None,
    domain_age: Optional[int] = None,
    has_trust_signals: Optional[bool] = None
) -> float:
    """
    Extract brand trust proxy (0-1).
    
    Args:
        brand_awareness: Brand awareness score [0, 1]
        domain_age: Domain age in years
        has_trust_signals: Has trust badges, certifications, etc.
    
    Returns:
        Brand trust proxy [0, 1]
    """
    trust = 0.5  # Default medium
    
    if brand_awareness is not None:
        trust = brand_awareness
    elif domain_age is not None:
        # Older domains = more trust (up to 5 years)
        trust = min(0.8, 0.3 + (domain_age / 5.0) * 0.5)
    elif has_trust_signals is not None:
        trust = 0.7 if has_trust_signals else 0.4
    
    return max(0.0, min(1.0, trust))


def extract_entry_signals(
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
    device_type: Optional[str] = None,
    platform: Optional[str] = None,
    market_maturity: Optional[str] = None
) -> EntrySignals:
    """
    Extract all entry-level signals.
    
    Args:
        referrer: HTTP referrer
        utm_source: UTM source parameter
        utm_medium: UTM medium parameter
        intent_frame: Intent frame from intent model
        search_query: Search query
        landing_page_text: Landing page text
        cta_text: Call-to-action text
        value_propositions: List of value propositions
        brand_awareness: Brand awareness score
        domain_age: Domain age in years
        has_trust_signals: Has trust signals
        device_type: Device type
        platform: Platform
        market_maturity: Market maturity
    
    Returns:
        EntrySignals object
    """
    traffic_source = extract_traffic_source(referrer, utm_source, utm_medium)
    intent_strength = extract_intent_strength(intent_frame, search_query, landing_page_text)
    promise_strength = extract_landing_page_promise_strength(
        landing_page_text, cta_text, value_propositions
    )
    brand_trust = extract_brand_trust_proxy(brand_awareness, domain_age, has_trust_signals)
    
    return EntrySignals(
        traffic_source=traffic_source,
        intent_strength=intent_strength,
        landing_page_promise_strength=promise_strength,
        brand_trust_proxy=brand_trust,
        device_type=device_type,
        platform=platform,
        market_maturity=market_maturity
    )


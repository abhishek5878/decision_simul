"""
fintech_presets.py - Fintech Onboarding Demo Presets

This module provides a complete, opinionated fintech onboarding scenario with:
- Default personas (3-5) in raw field-space
- 7 deterministic state variants per persona
- Realistic fintech onboarding flow (5-7 steps)
- Vertical-specific calibration

This is the canonical fintech example for the behavioral engine.
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from behavioral_engine import STATE_VARIANTS
import pandas as pd


# ============================================================================
# DEFAULT PERSONAS (Raw Field-Space)
# ============================================================================

DEFAULT_FINTECH_PERSONAS = [
    {
        "name": "GenZ_UPI_Native_Metro",
        "description": "Gen Z UPI-native, metro, low risk aversion",
        "raw_fields": {
            "SEC": 0.6,  # Middle class, educated
            "UrbanRuralTier": 1.0,  # Metro
            "DigitalLiteracy": 0.9,  # Power user
            "FamilyInfluence": 0.2,  # Individualistic
            "AspirationalLevel": 0.8,  # High aspiration
            "PriceSensitivity": 0.3,  # Not very price sensitive
            "RegionalCulture": 0.4,  # Less collectivist (metro)
            "InfluencerTrust": 0.7,  # Trusts influencers
            "ProfessionalSector": 0.8,  # Tech/formal
            "EnglishProficiency": 0.9,  # Fluent
            "HobbyDiversity": 0.7,  # Broad interests
            "CareerAmbition": 0.8,  # Aggressive growth
            "AgeBucket": 1.0,  # Gen Z
            "GenderMarital": 0.7  # Single male proxy
        }
    },
    {
        "name": "Salaried_Tier2_Cautious",
        "description": "Salaried worker, Tier-2, high family influence, cautious",
        "raw_fields": {
            "SEC": 0.5,  # Middle class
            "UrbanRuralTier": 0.4,  # Tier-2/Semi-urban
            "DigitalLiteracy": 0.5,  # Moderate
            "FamilyInfluence": 0.8,  # High family influence
            "AspirationalLevel": 0.4,  # Moderate aspiration
            "PriceSensitivity": 0.7,  # Price sensitive
            "RegionalCulture": 0.7,  # More collectivist
            "InfluencerTrust": 0.4,  # Moderate trust
            "ProfessionalSector": 0.5,  # Mixed
            "EnglishProficiency": 0.5,  # Moderate
            "HobbyDiversity": 0.4,  # Narrow interests
            "CareerAmbition": 0.4,  # Status quo
            "AgeBucket": 0.6,  # Core Millennial
            "GenderMarital": 0.2  # Married female proxy
        }
    },
    {
        "name": "Self_Employed_Trader_HighRisk",
        "description": "Self-employed trader, high risk tolerance, impatient",
        "raw_fields": {
            "SEC": 0.4,  # Lower-middle class
            "UrbanRuralTier": 0.7,  # Urban
            "DigitalLiteracy": 0.6,  # Moderate-high
            "FamilyInfluence": 0.5,  # Moderate
            "AspirationalLevel": 0.7,  # High aspiration
            "PriceSensitivity": 0.6,  # Price conscious
            "RegionalCulture": 0.6,  # Moderate
            "InfluencerTrust": 0.5,  # Moderate
            "ProfessionalSector": 0.3,  # Informal/trading
            "EnglishProficiency": 0.4,  # Basic
            "HobbyDiversity": 0.5,  # Moderate
            "CareerAmbition": 0.7,  # Growth-oriented
            "AgeBucket": 0.6,  # Core Millennial
            "GenderMarital": 0.8  # Single male proxy
        }
    },
    {
        "name": "Rural_First_Time_User",
        "description": "Rural user, first-time fintech, high trust concerns",
        "raw_fields": {
            "SEC": 0.2,  # Lower income
            "UrbanRuralTier": 0.0,  # Rural
            "DigitalLiteracy": 0.3,  # Low
            "FamilyInfluence": 0.9,  # Very high
            "AspirationalLevel": 0.2,  # Low aspiration
            "PriceSensitivity": 0.9,  # Very price sensitive
            "RegionalCulture": 0.9,  # High collectivism
            "InfluencerTrust": 0.2,  # Low trust
            "ProfessionalSector": 0.2,  # Informal/agricultural
            "EnglishProficiency": 0.1,  # Minimal
            "HobbyDiversity": 0.2,  # Narrow
            "CareerAmbition": 0.2,  # Status quo
            "AgeBucket": 0.4,  # Gen X
            "GenderMarital": 0.3  # Married proxy
        }
    },
    {
        "name": "Urban_Professional_Optimizer",
        "description": "Urban professional, high digital literacy, value optimizer",
        "raw_fields": {
            "SEC": 0.8,  # Upper-middle class
            "UrbanRuralTier": 0.9,  # Metro/Urban
            "DigitalLiteracy": 0.95,  # Very high
            "FamilyInfluence": 0.3,  # Individualistic
            "AspirationalLevel": 0.9,  # Very high
            "PriceSensitivity": 0.2,  # Not price sensitive
            "RegionalCulture": 0.3,  # Low collectivism
            "InfluencerTrust": 0.6,  # Moderate-high
            "ProfessionalSector": 0.95,  # Tech/formal
            "EnglishProficiency": 1.0,  # Native
            "HobbyDiversity": 0.9,  # Very broad
            "CareerAmbition": 0.9,  # Very aggressive
            "AgeBucket": 0.8,  # Young Millennial
            "GenderMarital": 0.6  # Single proxy
        }
    }
]


# ============================================================================
# FINTECH ONBOARDING FLOW (5-7 Steps)
# ============================================================================

FINTECH_ONBOARDING_STEPS = {
    "Landing Page": {
        "cognitive_demand": 0.2,
        "effort_demand": 0.0,
        "risk_signal": 0.1,
        "irreversibility": 0,
        "delay_to_value": 5,
        "explicit_value": 0.4,  # "Get instant payments, rewards"
        "reassurance_signal": 0.5,  # "RBI regulated", "Secure"
        "authority_signal": 0.3,
        "description": "Product explanation, value proposition"
    },
    "Mobile + OTP": {
        "cognitive_demand": 0.3,
        "effort_demand": 0.4,  # Enter number, wait for OTP, enter OTP
        "risk_signal": 0.2,  # Sharing phone number
        "irreversibility": 0,
        "delay_to_value": 4,
        "explicit_value": 0.3,
        "reassurance_signal": 0.4,  # "OTP is secure"
        "authority_signal": 0.2,
        "description": "Phone verification step"
    },
    "KYC Document Upload": {
        "cognitive_demand": 0.5,  # Need to find, scan, upload documents
        "effort_demand": 0.7,  # High effort - find Aadhaar/PAN, take photo
        "risk_signal": 0.4,  # Sharing identity documents
        "irreversibility": 0,
        "delay_to_value": 3,
        "explicit_value": 0.2,  # "Required for verification"
        "reassurance_signal": 0.6,  # "Encrypted", "RBI compliant"
        "authority_signal": 0.5,  # Government-backed KYC
        "description": "Identity verification via documents"
    },
    "PAN + Bank Linking": {
        "cognitive_demand": 0.4,
        "effort_demand": 0.6,  # Enter PAN, link bank account
        "risk_signal": 0.7,  # HIGH RISK - financial data
        "irreversibility": 1,  # Once linked, hard to undo
        "delay_to_value": 2,
        "explicit_value": 0.5,  # "Enable payments"
        "reassurance_signal": 0.7,  # "Bank-grade security"
        "authority_signal": 0.6,  # Bank partnership
        "description": "Financial data linking (irreversible)"
    },
    "Consent + Terms": {
        "cognitive_demand": 0.6,  # Read terms, understand consent
        "effort_demand": 0.2,
        "risk_signal": 0.3,  # Legal commitment
        "irreversibility": 0,
        "delay_to_value": 1,
        "explicit_value": 0.3,
        "reassurance_signal": 0.3,
        "authority_signal": 0.4,
        "description": "Legal consent and terms acceptance"
    },
    "First Transaction": {
        "cognitive_demand": 0.3,
        "effort_demand": 0.3,  # Make a test payment
        "risk_signal": 0.2,  # Using real money
        "irreversibility": 0,
        "delay_to_value": 0,  # IMMEDIATE VALUE
        "explicit_value": 1.0,  # Full value realized!
        "reassurance_signal": 0.5,
        "authority_signal": 0.3,
        "description": "First transaction / test transfer (value delivery)"
    }
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_persona_meta_from_raw(raw_fields: Dict, persona_def: Optional[Dict] = None) -> Dict:
    """
    Extract categorical meta tags from raw fields for filtering.
    
    Args:
        raw_fields: Raw persona fields dict
        persona_def: Optional original persona definition (for lite input labels)
    
    Returns:
        Dict with categorical tags
    """
    # Map numeric values to labels
    sec = raw_fields.get('SEC', 0.5)
    if sec < 0.4:
        sec_band = "low"
    elif sec < 0.7:
        sec_band = "mid"
    else:
        sec_band = "high"
    
    urban_rural_tier = raw_fields.get('UrbanRuralTier', 0.5)
    if urban_rural_tier < 0.3:
        urban_rural = "rural"
    elif urban_rural_tier < 0.7:
        urban_rural = "tier2"
    else:
        urban_rural = "metro"
    
    age_bucket = raw_fields.get('AgeBucket', 0.5)
    if age_bucket < 0.3:
        age_bucket_label = "senior"
    elif age_bucket < 0.7:
        age_bucket_label = "middle"
    else:
        age_bucket_label = "young"
    
    digital_literacy = raw_fields.get('DigitalLiteracy', 0.5)
    if digital_literacy < 0.4:
        digital_skill_band = "low"
    elif digital_literacy < 0.7:
        digital_skill_band = "medium"
    else:
        digital_skill_band = "high"
    
    # Risk attitude - try to infer from RT or use default
    rt = raw_fields.get('RT', None)
    if rt is None:
        # Infer from compiled priors if available
        priors = compile_persona_from_raw(raw_fields)
        rt = priors.get('RT', 0.5)
    
    if rt < 0.3:
        risk_attitude_label = "risk_averse"
    elif rt < 0.6:
        risk_attitude_label = "balanced"
    else:
        risk_attitude_label = "risk_tolerant"
    
    # Intent - infer from MS
    ms = raw_fields.get('MS', None)
    if ms is None:
        priors = compile_persona_from_raw(raw_fields)
        ms = priors.get('MS', 0.6)
    
    if ms < 0.5:
        intent_label = "low"
    elif ms < 0.75:
        intent_label = "medium"
    else:
        intent_label = "high"
    
    return {
        'sec_band': sec_band,
        'urban_rural': urban_rural,
        'age_bucket_label': age_bucket_label,
        'digital_skill_band': digital_skill_band,
        'risk_attitude_label': risk_attitude_label,
        'intent_label': intent_label
    }


def compile_persona_from_raw(raw_fields: Dict) -> Dict:
    """
    Compile a persona from raw field-space to latent priors.
    
    Args:
        raw_fields: Dict with normalized [0,1] inputs
    
    Returns:
        Dict with compiled priors (CC, FR, RT, LAM, ET, TB, DR, CN, MS)
    """
    # Clamp all inputs
    clamped = {k: max(0.0, min(1.0, v)) for k, v in raw_fields.items()}
    
    # Compile priors (same logic as behavioral_engine)
    priors = {}
    
    priors['CC'] = max(0.2, min(0.9,
        0.35 * clamped['DigitalLiteracy'] +
        0.25 * clamped['EnglishProficiency'] +
        0.20 * clamped['HobbyDiversity'] +
        0.20 * clamped['AgeBucket']
    ))
    
    priors['FR'] = max(0.1, min(0.8,
        1 - (
            0.5 * clamped['DigitalLiteracy'] +
            0.3 * clamped['AgeBucket'] +
            0.2 * clamped['EnglishProficiency']
        )
    ))
    
    priors['RT'] = max(0.1, min(0.9,
        0.4 * clamped['SEC'] +
        0.3 * (1 - clamped['FamilyInfluence']) +
        0.2 * clamped['AspirationalLevel'] +
        0.1 * (1 - clamped['PriceSensitivity'])
    ))
    
    priors['LAM'] = max(1.0, min(2.5,
        1 + (
            0.6 * clamped['FamilyInfluence'] +
            0.4 * clamped['PriceSensitivity']
        )
    ))
    
    priors['ET'] = max(0.2, min(0.9,
        0.5 * clamped['DigitalLiteracy'] +
        0.3 * clamped['HobbyDiversity'] +
        0.2 * clamped['CareerAmbition']
    ))
    
    priors['TB'] = max(0.2, min(0.9,
        0.4 * clamped['UrbanRuralTier'] +
        0.3 * clamped['ProfessionalSector'] +
        0.3 * clamped['InfluencerTrust']
    ))
    
    priors['DR'] = max(0.05, min(0.9,
        0.5 * clamped['PriceSensitivity'] +
        0.3 * (1 - clamped['AgeBucket']) +
        0.2 * clamped['AspirationalLevel']
    ))
    
    priors['CN'] = max(0.2, min(0.9,
        0.5 * clamped['FamilyInfluence'] +
        0.3 * clamped['RegionalCulture'] +
        0.2 * (1 - clamped['UrbanRuralTier'])
    ))
    
    priors['MS'] = max(0.3, min(1.0,
        clamped['AspirationalLevel'] * 0.6 +
        clamped['DigitalLiteracy'] * 0.4
    ))
    
    return priors


def get_default_fintech_scenario() -> Tuple[List[Dict], Dict, Dict]:
    """
    Get the default fintech onboarding scenario.
    
    Returns:
        Tuple of (personas, state_variants, product_steps)
        
        personas: List of dicts with 'name', 'description', 'raw_fields', 'priors'
        state_variants: Dict of state variant definitions (reuses existing)
        product_steps: Dict of fintech onboarding steps
    """
    # Compile all personas
    personas = []
    for persona_def in DEFAULT_FINTECH_PERSONAS:
        priors = compile_persona_from_raw(persona_def['raw_fields'])
        meta = extract_persona_meta_from_raw(persona_def['raw_fields'], persona_def)
        personas.append({
            'name': persona_def['name'],
            'description': persona_def['description'],
            'raw_fields': persona_def['raw_fields'],
            'priors': priors,
            'meta': meta
        })
    
    return personas, STATE_VARIANTS, FINTECH_ONBOARDING_STEPS


def get_persona_by_name(personas: List[Dict], name: str) -> Optional[Dict]:
    """Get a persona by name."""
    return next((p for p in personas if p['name'] == name), None)


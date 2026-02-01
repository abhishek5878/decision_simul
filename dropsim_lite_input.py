#!/usr/bin/env python3
"""
dropsim_lite_input.py - Lite Input Format for Non-Technical Users

Allows PMs to describe personas and steps using simple labels (low/medium/high)
instead of raw numeric values. Maps to full ScenarioConfig automatically.
"""

from typing import Dict, List, Optional, Literal
from dataclasses import dataclass
import json


# ============================================================================
# Lite Input Schemas
# ============================================================================

@dataclass
class LitePersona:
    """Human-friendly persona description."""
    name: str
    sec: Literal["low", "mid", "high"]
    urban_rural: Literal["rural", "tier2", "metro"]
    digital_skill: Literal["low", "medium", "high"]
    family_influence: Literal["low", "medium", "high"]
    aspiration: Literal["low", "medium", "high"]
    price_sensitivity: Literal["low", "medium", "high"]
    risk_attitude: Optional[Literal["risk_averse", "balanced", "risk_tolerant"]] = None
    age_bucket: Literal["senior", "middle", "young"] = "middle"
    intent: Literal["low", "medium", "high"] = "medium"
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'LitePersona':
        """Load from JSON dict."""
        # Handle missing optional fields
        kwargs = dict(data)
        if 'risk_attitude' not in kwargs:
            kwargs['risk_attitude'] = None
        if 'age_bucket' not in kwargs:
            kwargs['age_bucket'] = "middle"
        if 'intent' not in kwargs:
            kwargs['intent'] = "medium"
        return cls(**kwargs)


@dataclass
class LiteStep:
    """Human-friendly step description."""
    name: str
    type: Literal["landing", "signup", "kyc", "payment", "consent", "other"]
    mental_complexity: Literal["low", "medium", "high"]
    effort: Literal["low", "medium", "high"]
    risk: Literal["low", "medium", "high"]
    irreversible: bool
    value_visibility: Literal["low", "medium", "high"]
    delay_to_value: Literal["instant", "soon", "later"]
    reassurance: Literal["low", "medium", "high"] = "medium"
    authority: Literal["low", "medium", "high"] = "medium"
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'LiteStep':
        """Load from JSON dict."""
        # Handle missing optional fields
        kwargs = dict(data)
        if 'reassurance' not in kwargs:
            kwargs['reassurance'] = "medium"
        if 'authority' not in kwargs:
            kwargs['authority'] = "medium"
        return cls(**kwargs)


@dataclass
class LiteScenario:
    """Complete lite scenario configuration."""
    product_type: str  # e.g., "fintech", "edtech", "commerce"
    personas: List[LitePersona]
    steps: List[LiteStep]
    fintech_archetype: Optional[str] = None  # For fintech products: payments_wallet, neo_bank, lending_bnpl, etc.
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'LiteScenario':
        """Load from JSON dict."""
        return cls(
            product_type=data.get('product_type', 'custom'),
            personas=[LitePersona.from_dict(p) for p in data.get('personas', [])],
            steps=[LiteStep.from_dict(s) for s in data.get('steps', [])]
        )


# ============================================================================
# Mapping Functions: Lite → Full
# ============================================================================

def map_label_to_value(label: str, low: float = 0.2, medium: float = 0.5, high: float = 0.8) -> float:
    """Map low/medium/high labels to numeric values."""
    label_lower = label.lower()
    if label_lower == "low":
        return low
    elif label_lower == "medium":
        return medium
    elif label_lower == "high":
        return high
    else:
        # Default to medium if unknown
        return medium


def map_sec_label(sec: str) -> float:
    """Map SEC label to numeric."""
    mapping = {
        "low": 0.2,
        "mid": 0.5,
        "high": 0.8
    }
    return mapping.get(sec.lower(), 0.5)


def map_urban_rural_label(urban_rural: str) -> float:
    """Map urban/rural label to numeric."""
    mapping = {
        "rural": 0.0,
        "tier2": 0.4,
        "metro": 1.0
    }
    return mapping.get(urban_rural.lower(), 0.5)


def map_age_bucket_label(age_bucket: str) -> float:
    """Map age bucket label to numeric."""
    mapping = {
        "senior": 0.1,
        "middle": 0.5,
        "young": 0.9
    }
    return mapping.get(age_bucket.lower(), 0.5)


def map_intent_label(intent: str) -> float:
    """Map intent label to Motivation Strength (MS)."""
    mapping = {
        "low": 0.4,
        "medium": 0.6,
        "high": 0.85
    }
    return mapping.get(intent.lower(), 0.6)


def map_risk_attitude_label(risk_attitude: Optional[str]) -> Optional[float]:
    """Map risk attitude to Risk Tolerance (RT) override."""
    if not risk_attitude:
        return None
    mapping = {
        "risk_averse": 0.2,
        "balanced": 0.5,
        "risk_tolerant": 0.8
    }
    return mapping.get(risk_attitude.lower())


def map_delay_label(delay: str) -> int:
    """Map delay label to delay_to_value steps."""
    mapping = {
        "instant": 0,
        "soon": 2,
        "later": 4
    }
    return mapping.get(delay.lower(), 2)


def lite_persona_to_raw(lite_persona: LitePersona) -> Dict:
    """
    Convert LitePersona to PersonaRaw (full numeric fields).
    
    Uses deterministic mappings to construct all required raw fields.
    """
    # Map labels to numeric values
    sec = map_sec_label(lite_persona.sec)
    urban_rural_tier = map_urban_rural_label(lite_persona.urban_rural)
    digital_literacy = map_label_to_value(lite_persona.digital_skill, 0.3, 0.6, 0.9)
    family_influence = map_label_to_value(lite_persona.family_influence)
    aspirational_level = map_label_to_value(lite_persona.aspiration)
    price_sensitivity = map_label_to_value(lite_persona.price_sensitivity)
    age_bucket = map_age_bucket_label(lite_persona.age_bucket)
    
    # Derive additional fields from labels
    # Regional culture: higher for rural, lower for metro
    regional_culture = 0.9 if urban_rural_tier < 0.3 else (0.5 if urban_rural_tier < 0.7 else 0.3)
    
    # Influencer trust: higher for young, digital-savvy
    influencer_trust = 0.7 if digital_literacy > 0.7 and age_bucket > 0.7 else 0.4
    
    # Professional sector: higher for metro, digital-savvy
    professional_sector = 0.9 if urban_rural_tier > 0.8 and digital_literacy > 0.7 else 0.5
    
    # English proficiency: higher for metro, digital-savvy
    english_proficiency = 0.9 if urban_rural_tier > 0.8 and digital_literacy > 0.7 else 0.5
    
    # Hobby diversity: higher for young, aspirational
    hobby_diversity = 0.8 if age_bucket > 0.7 and aspirational_level > 0.6 else 0.4
    
    # Career ambition: maps to aspiration
    career_ambition = aspirational_level
    
    # Gender/marital: proxy based on age and family influence
    # Older + high family influence → more likely married
    gender_marital = 0.2 if age_bucket < 0.4 and family_influence > 0.7 else 0.7
    
    raw_fields = {
        "SEC": sec,
        "UrbanRuralTier": urban_rural_tier,
        "DigitalLiteracy": digital_literacy,
        "FamilyInfluence": family_influence,
        "AspirationalLevel": aspirational_level,
        "PriceSensitivity": price_sensitivity,
        "RegionalCulture": regional_culture,
        "InfluencerTrust": influencer_trust,
        "ProfessionalSector": professional_sector,
        "EnglishProficiency": english_proficiency,
        "HobbyDiversity": hobby_diversity,
        "CareerAmbition": career_ambition,
        "AgeBucket": age_bucket,
        "GenderMarital": gender_marital
    }
    
    return raw_fields


def lite_step_to_full(lite_step: LiteStep) -> Dict:
    """
    Convert LiteStep to full ProductStep definition.
    
    Maps intuitive labels to numeric step attributes.
    """
    # Map labels to numeric values
    cognitive_demand = map_label_to_value(lite_step.mental_complexity, 0.2, 0.5, 0.8)
    effort_demand = map_label_to_value(lite_step.effort, 0.2, 0.5, 0.8)
    risk_signal = map_label_to_value(lite_step.risk, 0.1, 0.4, 0.8)
    irreversibility = 1 if lite_step.irreversible else 0
    explicit_value = map_label_to_value(lite_step.value_visibility, 0.2, 0.5, 0.8)
    delay_to_value = map_delay_label(lite_step.delay_to_value)
    reassurance_signal = map_label_to_value(lite_step.reassurance, 0.3, 0.5, 0.7)
    authority_signal = map_label_to_value(lite_step.authority, 0.2, 0.5, 0.7)
    
    # Type-specific adjustments
    if lite_step.type == "payment":
        # Payments are inherently higher risk
        risk_signal = max(risk_signal, 0.6)
        if not lite_step.irreversible:
            irreversibility = 1  # Payments are typically irreversible
    elif lite_step.type == "kyc":
        # KYC has high effort and moderate risk
        effort_demand = max(effort_demand, 0.6)
        risk_signal = max(risk_signal, 0.4)
        authority_signal = max(authority_signal, 0.5)  # Government-backed
    elif lite_step.type == "landing":
        # Landing pages: Check if it's a commitment gate (CTA requires action)
        # If effort is already set to "high" (commitment gate), don't override
        if lite_step.effort == "high":
            # Commitment gate: CTA click requires commitment
            # Keep high effort, but allow risk to be medium
            risk_signal = max(risk_signal, 0.3)  # Commitment feels risky
        else:
            # Passive landing page (no CTA or low commitment)
            risk_signal = min(risk_signal, 0.2)
            effort_demand = min(effort_demand, 0.2)
    elif lite_step.type == "signup":
        # Signup is typically low risk, moderate effort
        risk_signal = min(risk_signal, 0.3)
        effort_demand = max(effort_demand, 0.3)
    
    return {
        "name": lite_step.name,
        "description": f"{lite_step.type} step: {lite_step.name}",
        "cognitive_demand": cognitive_demand,
        "effort_demand": effort_demand,
        "risk_signal": risk_signal,
        "irreversibility": irreversibility,
        "delay_to_value": delay_to_value,
        "explicit_value": explicit_value,
        "reassurance_signal": reassurance_signal,
        "authority_signal": authority_signal
    }


def lite_to_scenario(lite_scenario: LiteScenario) -> Dict:
    """
    Convert LiteScenario to full ScenarioConfig.
    
    This is the main entry point for lite input mode.
    """
    # Convert personas
    personas = []
    for lite_persona in lite_scenario.personas:
        raw_fields = lite_persona_to_raw(lite_persona)
        
        # Compile priors using existing compiler
        from fintech_presets import compile_persona_from_raw
        priors = compile_persona_from_raw(raw_fields)
        
        # Override RT if risk_attitude provided
        if lite_persona.risk_attitude:
            rt_override = map_risk_attitude_label(lite_persona.risk_attitude)
            if rt_override is not None:
                priors['RT'] = rt_override
        
        # Override MS from intent
        ms_override = map_intent_label(lite_persona.intent)
        priors['MS'] = ms_override
        
        # Extract meta tags for filtering
        from fintech_presets import extract_persona_meta_from_raw
        meta = {
            'sec_band': lite_persona.sec,
            'urban_rural': lite_persona.urban_rural,
            'age_bucket_label': lite_persona.age_bucket,
            'digital_skill_band': lite_persona.digital_skill,
            'intent_label': lite_persona.intent
        }
        
        # Add risk attitude if provided
        if lite_persona.risk_attitude:
            meta['risk_attitude_label'] = lite_persona.risk_attitude
        else:
            # Infer from RT
            if priors['RT'] < 0.3:
                meta['risk_attitude_label'] = "risk_averse"
            elif priors['RT'] < 0.6:
                meta['risk_attitude_label'] = "balanced"
            else:
                meta['risk_attitude_label'] = "risk_tolerant"
        
        personas.append({
            "name": lite_persona.name,
            "description": f"{lite_persona.sec} SEC, {lite_persona.urban_rural}, {lite_persona.digital_skill} digital skill",
            "raw_fields": raw_fields,
            "compiled_priors": priors,
            "meta": meta
        })
    
    # Convert steps
    steps = [lite_step_to_full(lite_step) for lite_step in lite_scenario.steps]
    
    return {
        "scenario_name": f"{lite_scenario.product_type}_lite",
        "personas": personas,
        "steps": steps
    }


def load_lite_scenario(filepath: str) -> LiteScenario:
    """Load lite scenario from JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return LiteScenario.from_dict(data)


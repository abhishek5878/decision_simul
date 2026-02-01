#!/usr/bin/env python3
"""
dropsim_target_filter.py - Target Group Filtering

Filters personas by target group criteria to focus simulation on relevant segments.
"""

from typing import Dict, List, Optional, Literal
from dataclasses import dataclass
import json


# ============================================================================
# Target Group Schema
# ============================================================================

@dataclass
class TargetGroup:
    """Target group filter criteria."""
    sec: Optional[List[Literal["low", "mid", "high"]]] = None
    urban_rural: Optional[List[Literal["rural", "tier2", "metro"]]] = None
    age_bucket: Optional[List[Literal["young", "middle", "senior"]]] = None
    digital_skill: Optional[List[Literal["low", "medium", "high"]]] = None
    risk_attitude: Optional[List[Literal["risk_averse", "balanced", "risk_tolerant"]]] = None
    intent: Optional[List[Literal["low", "medium", "high"]]] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TargetGroup':
        """Load from JSON dict."""
        return cls(
            sec=data.get('sec'),
            urban_rural=data.get('urban_rural'),
            age_bucket=data.get('age_bucket'),
            digital_skill=data.get('digital_skill'),
            risk_attitude=data.get('risk_attitude'),
            intent=data.get('intent')
        )
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        result = {}
        if self.sec:
            result['sec'] = self.sec
        if self.urban_rural:
            result['urban_rural'] = self.urban_rural
        if self.age_bucket:
            result['age_bucket'] = self.age_bucket
        if self.digital_skill:
            result['digital_skill'] = self.digital_skill
        if self.risk_attitude:
            result['risk_attitude'] = self.risk_attitude
        if self.intent:
            result['intent'] = self.intent
        return result


# ============================================================================
# Filtering Logic
# ============================================================================

def persona_matches_target(
    persona_meta: Dict,
    target: Optional[TargetGroup]
) -> bool:
    """
    Returns True if the persona falls inside the target group filters.
    
    Args:
        persona_meta: Dict with categorical tags:
            - sec_band: "low" | "mid" | "high"
            - urban_rural: "rural" | "tier2" | "metro"
            - age_bucket_label: "young" | "middle" | "senior"
            - digital_skill_band: "low" | "medium" | "high"
            - risk_attitude_label: "risk_averse" | "balanced" | "risk_tolerant" (optional)
            - intent_label: "low" | "medium" | "high"
        target: TargetGroup filter (None = no filter, match all)
    
    Returns:
        True if persona matches all specified filters, False otherwise
    """
    # No filter = match all
    if target is None:
        return True
    
    # Check each filter field
    if target.sec is not None:
        sec_band = persona_meta.get('sec_band')
        if sec_band not in target.sec:
            return False
    
    if target.urban_rural is not None:
        urban_rural = persona_meta.get('urban_rural')
        if urban_rural not in target.urban_rural:
            return False
    
    if target.age_bucket is not None:
        age_bucket_label = persona_meta.get('age_bucket_label')
        if age_bucket_label not in target.age_bucket:
            return False
    
    if target.digital_skill is not None:
        digital_skill_band = persona_meta.get('digital_skill_band')
        if digital_skill_band not in target.digital_skill:
            return False
    
    if target.risk_attitude is not None:
        risk_attitude_label = persona_meta.get('risk_attitude_label')
        if risk_attitude_label not in target.risk_attitude:
            return False
    
    if target.intent is not None:
        intent_label = persona_meta.get('intent_label')
        if intent_label not in target.intent:
            return False
    
    # All filters passed
    return True


def load_target_group(filepath: str) -> TargetGroup:
    """Load target group from JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return TargetGroup.from_dict(data)


def filter_personas_by_target(
    personas: List[Dict],
    target_group: Optional[TargetGroup]
) -> List[Dict]:
    """
    Filter personas by target group criteria.
    
    Args:
        personas: List of persona dicts with 'meta' field
        target_group: Optional TargetGroup filter
    
    Returns:
        Filtered list of personas
    """
    if target_group is None:
        return personas
    
    filtered = []
    for persona in personas:
        meta = persona.get('meta', {})
        if persona_matches_target(meta, target_group):
            filtered.append(persona)
    
    return filtered


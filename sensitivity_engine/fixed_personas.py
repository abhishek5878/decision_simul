"""
Fixed Persona Generation for Decision Sensitivity Simulation

Generates 100 fixed personas with 7 state variants each.
These personas remain identical across all experiments for reproducibility.
"""

from dataclasses import dataclass
from typing import List, Dict
import numpy as np
from numpy.random import Generator


@dataclass
class FixedPersona:
    """
    A fixed persona with immutable state variants.
    
    Used for reproducible sensitivity experiments.
    """
    persona_id: str
    
    # Fixed state variants (0-1 scale)
    cognitive_energy: float
    risk_tolerance: float
    effort_tolerance: float
    intent_strength: float
    trust_baseline: float
    urgency: float
    value_expectation: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'persona_id': self.persona_id,
            'cognitive_energy': float(self.cognitive_energy),
            'risk_tolerance': float(self.risk_tolerance),
            'effort_tolerance': float(self.effort_tolerance),
            'intent_strength': float(self.intent_strength),
            'trust_baseline': float(self.trust_baseline),
            'urgency': float(self.urgency),
            'value_expectation': float(self.value_expectation)
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FixedPersona':
        """Create from dictionary."""
        return cls(
            persona_id=data['persona_id'],
            cognitive_energy=data['cognitive_energy'],
            risk_tolerance=data['risk_tolerance'],
            effort_tolerance=data['effort_tolerance'],
            intent_strength=data['intent_strength'],
            trust_baseline=data['trust_baseline'],
            urgency=data['urgency'],
            value_expectation=data['value_expectation']
        )


def generate_fixed_personas(n: int = 100, seed: int = 42) -> List[FixedPersona]:
    """
    Generate n fixed personas with diverse state combinations.
    
    Uses stratified sampling to ensure coverage across state space.
    """
    rng = np.random.default_rng(seed)
    
    personas = []
    
    # Use stratified sampling for better coverage
    # Split each dimension into roughly equal bins
    n_bins = 5  # 5 bins per dimension
    
    for i in range(n):
        persona_id = f"fixed_persona_{i:03d}"
        
        # Stratified sampling: select bin, then sample within bin
        cognitive_energy = (i % n_bins + rng.uniform(0, 0.2)) / n_bins
        risk_tolerance = ((i // n_bins) % n_bins + rng.uniform(0, 0.2)) / n_bins
        effort_tolerance = ((i // (n_bins * n_bins)) % n_bins + rng.uniform(0, 0.2)) / n_bins
        intent_strength = ((i // (n_bins * n_bins * n_bins)) % n_bins + rng.uniform(0, 0.2)) / n_bins
        trust_baseline = rng.uniform(0, 1)
        urgency = rng.uniform(0, 1)
        value_expectation = rng.uniform(0, 1)
        
        # Clamp to [0, 1]
        cognitive_energy = max(0.0, min(1.0, cognitive_energy))
        risk_tolerance = max(0.0, min(1.0, risk_tolerance))
        effort_tolerance = max(0.0, min(1.0, effort_tolerance))
        intent_strength = max(0.0, min(1.0, intent_strength))
        trust_baseline = max(0.0, min(1.0, trust_baseline))
        urgency = max(0.0, min(1.0, urgency))
        value_expectation = max(0.0, min(1.0, value_expectation))
        
        persona = FixedPersona(
            persona_id=persona_id,
            cognitive_energy=cognitive_energy,
            risk_tolerance=risk_tolerance,
            effort_tolerance=effort_tolerance,
            intent_strength=intent_strength,
            trust_baseline=trust_baseline,
            urgency=urgency,
            value_expectation=value_expectation
        )
        
        personas.append(persona)
    
    return personas


def save_fixed_personas(personas: List[FixedPersona], filepath: str):
    """Save fixed personas to JSON file."""
    import json
    data = [p.to_dict() for p in personas]
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def load_fixed_personas(filepath: str) -> List[FixedPersona]:
    """Load fixed personas from JSON file."""
    import json
    with open(filepath, 'r') as f:
        data = json.load(f)
    return [FixedPersona.from_dict(p) for p in data]


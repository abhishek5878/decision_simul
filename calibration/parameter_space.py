"""
parameter_space.py - Define Learnable Parameters for Calibration

This module defines all parameters that can be calibrated to match observed behavior.
Parameters only adjust scaling/weights, not behavioral logic.
"""

from dataclasses import dataclass
from typing import Dict, Tuple
import numpy as np


@dataclass
class ParameterDefinition:
    """Definition of a single learnable parameter."""
    name: str
    default: float
    min_value: float
    max_value: float
    description: str
    
    def sample_random(self, rng: np.random.Generator) -> float:
        """Sample a random value within bounds."""
        return rng.uniform(self.min_value, self.max_value)
    
    def clip(self, value: float) -> float:
        """Clip value to valid bounds."""
        return np.clip(value, self.min_value, self.max_value)


# ============================================================================
# PARAMETER DEFINITIONS
# ============================================================================

PARAMETER_SPACE = {
    "BASE_COMPLETION_RATE": ParameterDefinition(
        name="BASE_COMPLETION_RATE",
        default=0.60,  # Current hardcoded value
        min_value=0.05,
        max_value=0.90,
        description="Base completion probability floor - reflects real-world stickiness"
    ),
    
    "PERSISTENCE_BONUS_START": ParameterDefinition(
        name="PERSISTENCE_BONUS_START",
        default=0.18,  # Current: 0.18 + 0.22 * progress
        min_value=0.0,
        max_value=0.40,
        description="Persistence bonus at start of journey (people continue even when unsure)"
    ),
    
    "PERSISTENCE_BONUS_RATE": ParameterDefinition(
        name="PERSISTENCE_BONUS_RATE",
        default=0.22,  # Current: 0.18 + 0.22 * progress
        min_value=0.0,
        max_value=0.50,
        description="Rate at which persistence bonus increases with progress"
    ),
    
    "INTENT_PENALTY_WEIGHT": ParameterDefinition(
        name="INTENT_PENALTY_WEIGHT",
        default=0.025,  # Current: 0.10 * 0.25 = 0.025 max reduction
        min_value=0.0,
        max_value=0.15,
        description="Weight for intent mismatch penalties (max reduction per step)"
    ),
    
    "FRICTION_PENALTY_WEIGHT": ParameterDefinition(
        name="FRICTION_PENALTY_WEIGHT",
        default=1.0,  # Current: implicit 1.0 multiplier on friction costs
        min_value=0.3,
        max_value=2.0,
        description="Global multiplier for cognitive/effort/risk friction penalties"
    ),
    
    "VALUE_SENSITIVITY": ParameterDefinition(
        name="VALUE_SENSITIVITY",
        default=1.0,  # Current: base value sensitivity
        min_value=0.5,
        max_value=2.0,
        description="Global multiplier for how much value signals affect continuation probability"
    ),
    
    "COGNITIVE_PENALTY_WEIGHT": ParameterDefinition(
        name="COGNITIVE_PENALTY_WEIGHT",
        default=1.0,  # Current: implicit 1.0 multiplier
        min_value=0.5,
        max_value=2.0,
        description="Weight for cognitive/fatigue penalties"
    ),
    
    "EFFORT_PENALTY_WEIGHT": ParameterDefinition(
        name="EFFORT_PENALTY_WEIGHT",
        default=1.0,  # Current: implicit 1.0 multiplier
        min_value=0.5,
        max_value=2.0,
        description="Weight for effort-related penalties"
    ),
    
    "RISK_PENALTY_WEIGHT": ParameterDefinition(
        name="RISK_PENALTY_WEIGHT",
        default=1.0,  # Current: implicit 1.0 multiplier
        min_value=0.5,
        max_value=2.0,
        description="Weight for risk/loss-aversion penalties"
    ),
}


def get_default_parameters() -> Dict[str, float]:
    """Get default parameter values (current hardcoded values)."""
    return {name: param.default for name, param in PARAMETER_SPACE.items()}


def validate_parameters(params: Dict[str, float]) -> Dict[str, float]:
    """Validate and clip parameters to valid bounds."""
    validated = {}
    for name, value in params.items():
        if name in PARAMETER_SPACE:
            validated[name] = PARAMETER_SPACE[name].clip(value)
        else:
            # Unknown parameter - keep as is (may be used by other parts)
            validated[name] = value
    return validated


def sample_random_parameters(rng: np.random.Generator = None) -> Dict[str, float]:
    """Sample random parameters within bounds."""
    if rng is None:
        rng = np.random.default_rng()
    
    return {
        name: param.sample_random(rng)
        for name, param in PARAMETER_SPACE.items()
    }


def get_parameter_bounds() -> Dict[str, Tuple[float, float]]:
    """Get parameter bounds for optimization."""
    return {
        name: (param.min_value, param.max_value)
        for name, param in PARAMETER_SPACE.items()
    }


def describe_parameters(params: Dict[str, float]) -> str:
    """Generate human-readable description of parameters."""
    lines = ["Calibration Parameters:"]
    for name, value in params.items():
        if name in PARAMETER_SPACE:
            param_def = PARAMETER_SPACE[name]
            lines.append(f"  {name}: {value:.4f} (default: {param_def.default:.4f}, "
                        f"range: [{param_def.min_value:.4f}, {param_def.max_value:.4f}])")
            lines.append(f"    {param_def.description}")
    return "\n".join(lines)


"""
Stabilized Probability Model - Prevents collapse through bounded additive aggregation.

Key improvements:
1. Additive aggregation instead of multiplicative (prevents exponential collapse)
2. Explicit probability floors/ceilings (0.05-0.95)
3. Penalty caps (prevents penalties from dominating)
4. Full trace logging (diagnosable at every step)
5. Rebalanced base values
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from behavioral_engine_improved import InternalState

# ============================================================================
# CONSTANTS - Rebalanced Values
# ============================================================================

BASE_EXPLICIT_VALUE = 0.45  # Was too low (0.2-0.3)
BASE_IMPLICIT_VALUE = 0.35
MIN_PROGRESS_VALUE = 0.20
MIN_PROB = 0.05  # Floor - prevents zero-out
MAX_PROB = 0.95  # Ceiling - prevents unrealistic completion

# Penalty caps - prevent penalties from dominating
MAX_TOTAL_PENALTY = 0.8  # Maximum total penalty score (increased from 0.6)
MAX_SEMANTIC_PENALTY = 0.25  # Maximum semantic penalty
MAX_FATIGUE_PENALTY = 0.15  # Maximum fatigue penalty (reduced from 0.2)
MAX_COGNITIVE_PENALTY = 0.15  # Maximum cognitive load penalty


# ============================================================================
# PROBABILITY TRACE DATA STRUCTURE
# ============================================================================

@dataclass
class ProbabilityTrace:
    """Full trace of probability calculation for debugging."""
    step_id: str
    step_index: int
    total_steps: int
    
    # Base values
    base_value: float
    base_advantage: float
    
    # Amplifiers (additive boosts)
    amplifiers: Dict[str, float] = field(default_factory=dict)
    
    # Penalties (subtractive costs)
    penalties: Dict[str, float] = field(default_factory=dict)
    
    # Intermediate calculations
    post_adjustment_score: float = 0.0
    sigmoid_input: float = 0.0
    final_probability: float = 0.0
    
    # State snapshot
    cognitive_energy: float = 0.0
    perceived_value: float = 0.0
    perceived_risk: float = 0.0
    perceived_effort: float = 0.0
    perceived_control: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "step_id": self.step_id,
            "step_index": self.step_index,
            "total_steps": self.total_steps,
            "base_value": round(self.base_value, 3),
            "base_advantage": round(self.base_advantage, 3),
            "amplifiers": {k: round(v, 3) for k, v in self.amplifiers.items()},
            "penalties": {k: round(v, 3) for k, v in self.penalties.items()},
            "post_adjustment_score": round(self.post_adjustment_score, 3),
            "sigmoid_input": round(self.sigmoid_input, 3),
            "final_probability": round(self.final_probability, 3),
            "state": {
                "cognitive_energy": round(self.cognitive_energy, 3),
                "perceived_value": round(self.perceived_value, 3),
                "perceived_risk": round(self.perceived_risk, 3),
                "perceived_effort": round(self.perceived_effort, 3),
                "perceived_control": round(self.perceived_control, 3)
            }
        }


# ============================================================================
# STABILIZED PROBABILITY CALCULATION
# ============================================================================

def compute_stabilized_continuation_probability(
    state: InternalState,
    priors: Dict,
    step_index: int,
    total_steps: int,
    step_id: str,
    modifiers: Optional[Dict] = None,
    semantic_adjustments: Optional[Dict] = None
) -> Tuple[float, ProbabilityTrace]:
    """
    Compute continuation probability using bounded additive aggregation.
    
    This prevents exponential collapse by:
    1. Using additive aggregation (score += amplifiers, score -= penalties)
    2. Capping penalties to prevent domination
    3. Applying explicit floors/ceilings
    4. Full trace logging for diagnosis
    
    Args:
        state: Current internal state
        priors: Behavioral priors
        step_index: Current step index (0-based)
        total_steps: Total number of steps
        step_id: Step identifier for logging
        modifiers: Archetype modifiers
        semantic_adjustments: Optional semantic layer adjustments
    
    Returns:
        (probability, trace) tuple
    """
    if modifiers is None:
        modifiers = {'base_persistence': 1.0, 'value_sensitivity': 1.0, 
                     'fatigue_resilience': 1.0, 'risk_tolerance_mult': 1.0}
    
    if semantic_adjustments is None:
        semantic_adjustments = {}
    
    # ========================================================================
    # STEP 1: BASE ADVANTAGE (value + control vs risk + effort)
    # ========================================================================
    left = (state.perceived_value * priors['MS']) + state.perceived_control
    right = state.perceived_risk + state.perceived_effort
    base_advantage = left - right
    
    trace = ProbabilityTrace(
        step_id=step_id,
        step_index=step_index,
        total_steps=total_steps,
        base_value=state.perceived_value,
        base_advantage=base_advantage,
        cognitive_energy=state.cognitive_energy,
        perceived_value=state.perceived_value,
        perceived_risk=state.perceived_risk,
        perceived_effort=state.perceived_effort,
        perceived_control=state.perceived_control
    )
    
    # Start with base advantage as score
    score = base_advantage
    
    # First-step boost: Users are optimistic at the start
    # This prevents immediate collapse on first step
    if step_index == 0:
        first_step_boost = 0.15  # Moderate boost to prevent early collapse
        trace.amplifiers["first_step_optimism"] = first_step_boost
        score += first_step_boost
    
    # ========================================================================
    # STEP 2: ADD AMPLIFIERS (additive boosts)
    # ========================================================================
    progress = step_index / total_steps if total_steps > 0 else 0
    
    # Amplifier 1: Goal Proximity
    goal_proximity = progress * 0.8  # Up to 0.8 boost at completion
    trace.amplifiers["goal_proximity"] = goal_proximity
    score += goal_proximity
    
    # Amplifier 2: Sunk Cost Effect
    sunk_cost = progress * 0.4  # Up to 0.4 boost
    trace.amplifiers["sunk_cost"] = sunk_cost
    score += sunk_cost
    
    # Amplifier 3: Progress Momentum (after 20%)
    if progress > 0.2:
        momentum = (progress - 0.2) * 0.3  # Up to 0.24 boost
        trace.amplifiers["momentum"] = momentum
        score += momentum
    
    # Amplifier 4: Value Override (high value reduces effective costs)
    if state.perceived_value > 0.6:
        value_override = (state.perceived_value - 0.6) * 0.5  # Up to 0.2 boost
        trace.amplifiers["value_override"] = value_override
        score += value_override
    
    # Amplifier 5: Commitment Effect (stronger as you progress)
    commitment = progress * 0.6  # Up to 0.6 boost
    trace.amplifiers["commitment"] = commitment
    score += commitment
    
    # Amplifier 6: Trust/Control Boost
    if state.perceived_control > 0.5:
        control_boost = (state.perceived_control - 0.5) * 0.3  # Up to 0.45 boost
        trace.amplifiers["control_boost"] = control_boost
        score += control_boost
    
    # ========================================================================
    # STEP 3: SUBTRACT PENALTIES (capped to prevent domination)
    # ========================================================================
    
    # Penalty 1: Cognitive Load (fatigue)
    cognitive_penalty = 0.0
    # Only apply penalty if energy is very low (threshold increased from 0.5 to 0.3)
    if state.cognitive_energy < 0.3:
        # Fatigue penalty increases as energy decreases
        # Made less harsh: reduced multiplier and higher threshold
        fatigue_level = (0.3 - state.cognitive_energy) * 0.2  # Up to 0.06 (was 0.125)
        cognitive_penalty = min(fatigue_level, MAX_FATIGUE_PENALTY)
        trace.penalties["cognitive_load"] = -cognitive_penalty
        score -= cognitive_penalty
    
    # Penalty 2: High Effort
    effort_penalty = 0.0
    if state.perceived_effort > 1.0:
        effort_level = (state.perceived_effort - 1.0) * 0.15  # Up to 0.3
        effort_penalty = min(effort_level, 0.3)
        trace.penalties["high_effort"] = -effort_penalty
        score -= effort_penalty
    
    # Penalty 3: High Risk
    risk_penalty = 0.0
    if state.perceived_risk > 1.0:
        risk_level = (state.perceived_risk - 1.0) * 0.15  # Up to 0.3
        risk_penalty = min(risk_level, 0.3)
        trace.penalties["high_risk"] = -risk_penalty
        score -= risk_penalty
    
    # Penalty 4: Semantic Mismatch (from semantic layer)
    semantic_penalty = 0.0
    if 'friction_delta' in semantic_adjustments:
        friction = semantic_adjustments['friction_delta']
        semantic_penalty = min(friction * 0.2, MAX_SEMANTIC_PENALTY)  # Cap at 0.25
        trace.penalties["semantic_mismatch"] = -semantic_penalty
        score -= semantic_penalty
    
    # Penalty 5: Knowledge Gap
    if semantic_adjustments.get('knowledge_gap', False):
        knowledge_penalty = min(0.1, MAX_SEMANTIC_PENALTY * 0.4)  # 0.1 max
        trace.penalties["knowledge_gap"] = -knowledge_penalty
        score -= knowledge_penalty
    
    # Penalty 6: Anxiety/Emotional
    if 'anxiety_delta' in semantic_adjustments:
        anxiety = semantic_adjustments['anxiety_delta']
        if anxiety > 0.3:
            anxiety_penalty = min((anxiety - 0.3) * 0.15, 0.15)  # Up to 0.15
            trace.penalties["anxiety"] = -anxiety_penalty
            score -= anxiety_penalty
    
    # ========================================================================
    # STEP 4: CAP TOTAL PENALTIES (prevent domination)
    # ========================================================================
    total_penalty = sum(trace.penalties.values())
    if abs(total_penalty) > MAX_TOTAL_PENALTY:
        # Normalize penalties if they exceed cap
        penalty_scale = MAX_TOTAL_PENALTY / abs(total_penalty)
        for key in trace.penalties:
            trace.penalties[key] *= penalty_scale
        # Recalculate score with normalized penalties
        score = base_advantage + sum(trace.amplifiers.values()) + sum(trace.penalties.values())
    
    trace.post_adjustment_score = score
    
    # ========================================================================
    # STEP 5: APPLY ARCHETYPE MODIFIERS (additive adjustment)
    # ========================================================================
    archetype_adjustment = (modifiers['base_persistence'] - 1.0) * 0.3  # Up to ±0.3
    score += archetype_adjustment
    if abs(archetype_adjustment) > 0.01:
        trace.amplifiers["archetype"] = archetype_adjustment
    
    # Value sensitivity modifier
    if state.perceived_value > 0.6:
        value_sensitivity = (state.perceived_value - 0.6) * 0.2 * modifiers['value_sensitivity']
        score += value_sensitivity
        if value_sensitivity > 0.01:
            trace.amplifiers["value_sensitivity"] = value_sensitivity
    
    # ========================================================================
    # STEP 6: SIGMOID MAPPING (score → probability)
    # ========================================================================
    trace.sigmoid_input = score
    steepness = 1.2  # Less steep = more probabilistic
    probability = 1 / (1 + np.exp(-steepness * score))
    
    # ========================================================================
    # STEP 7: APPLY FLOORS/CEILINGS
    # ========================================================================
    probability = np.clip(probability, MIN_PROB, MAX_PROB)
    trace.final_probability = probability
    
    return probability, trace


def compute_stabilized_continuation_probability_with_semantic(
    state: InternalState,
    priors: Dict,
    step_index: int,
    total_steps: int,
    step_id: str,
    modifiers: Optional[Dict] = None,
    semantic_profile: Optional[Dict] = None,
    intent_alignment: Optional[Dict] = None
) -> Tuple[float, ProbabilityTrace]:
    """
    Wrapper that extracts semantic adjustments and calls stabilized function.
    """
    semantic_adjustments = {}
    
    if intent_alignment:
        # Extract friction delta
        if 'friction_delta' in intent_alignment:
            semantic_adjustments['friction_delta'] = intent_alignment['friction_delta']
        
        # Check for knowledge gap
        if 'conflict_axes' in intent_alignment:
            conflicts = intent_alignment['conflict_axes']
            if isinstance(conflicts, list) and 'knowledge_gap' in conflicts:
                semantic_adjustments['knowledge_gap'] = True
            elif isinstance(conflicts, dict) and conflicts.get('knowledge_gap', 0) > 0:
                semantic_adjustments['knowledge_gap'] = True
    
    if semantic_profile and 'emotional_deltas' in semantic_profile:
        emotional = semantic_profile['emotional_deltas']
        if isinstance(emotional, dict) and 'anxiety' in emotional:
            semantic_adjustments['anxiety_delta'] = emotional['anxiety']
    
    return compute_stabilized_continuation_probability(
        state, priors, step_index, total_steps, step_id, modifiers, semantic_adjustments
    )


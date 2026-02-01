"""
Local decision function that mirrors behavioral engine logic.

This function computes P(CONTINUE) deterministically from features.
It must match the actual decision logic used by behavioral_engine_intent_aware.
"""

import numpy as np
from typing import Dict, Optional, List


class LocalDecisionFunction:
    """
    Local surrogate decision function.
    
    Mirrors the decision logic from:
    - behavioral_engine_improved.should_continue_probabilistic
    - dropsim_intent_model.compute_intent_conditioned_continuation_prob
    
    This is NOT a trained model - it's a deterministic function.
    """
    
    def __init__(self, modifiers: Optional[Dict] = None):
        """
        Initialize with optional modifiers.
        
        Args:
            modifiers: Archetype modifiers (base_persistence, value_sensitivity, etc.)
        """
        if modifiers is None:
            modifiers = {
                'base_persistence': 1.0,
                'value_sensitivity': 1.0,
                'fatigue_resilience': 1.0,
                'risk_tolerance_mult': 1.0
            }
        self.modifiers = modifiers
    
    def compute_probability(
        self,
        features: Dict[str, float],
        step_index: int,
        total_steps: int,
        intent_alignment: float = 0.5
    ) -> float:
        """
        Compute P(CONTINUE) from features.
        
        Args:
            features: Dict with keys:
                - cognitive_energy
                - intent_strength
                - effort_tolerance
                - risk_tolerance
                - trust_baseline
                - value_expectation
                - step_effort
                - step_risk
                - step_value
                - step_trust
                - intent_mismatch
            step_index: Current step index (0-based)
            total_steps: Total number of steps
            intent_alignment: Intent alignment score (0-1)
        
        Returns:
            P(CONTINUE) in [0, 1]
        """
        # Extract features with defaults
        cognitive_energy = features.get('cognitive_energy', 0.5)
        intent_strength = features.get('intent_strength', 0.5)
        effort_tolerance = features.get('effort_tolerance', 0.5)
        risk_tolerance = features.get('risk_tolerance', 0.5)
        trust_baseline = features.get('trust_baseline', 0.5)
        value_expectation = features.get('value_expectation', 0.5)
        
        step_effort = features.get('step_effort', 0.0)
        step_risk = features.get('step_risk', 0.0)
        step_value = features.get('step_value', 0.0)
        step_trust = features.get('step_trust', 0.0)
        intent_mismatch = features.get('intent_mismatch', 0.0)
        
        # Compute perceived values (state after step)
        # These mirror update_state_improved logic
        perceived_value = min(1.0, value_expectation + step_value)
        perceived_control = min(1.0, trust_baseline + step_trust)
        perceived_effort = min(1.0, step_effort * (1 - effort_tolerance))
        perceived_risk = min(1.0, step_risk * (1 - risk_tolerance))
        
        # Base decision strength (mirrors should_continue_probabilistic)
        # MS (motivation strength) approximated from value_expectation
        MS = value_expectation  # Simplified
        left = (perceived_value * MS) + perceived_control
        right = perceived_risk + perceived_effort
        base_advantage = left - right
        
        # 1. VALUE OVERRIDE: High value can overcome fatigue
        value_override = 0.0
        if perceived_value > 0.7:
            value_override = perceived_value * 0.3
        
        # 2. COMMITMENT EFFECT: Progress creates momentum
        progress = step_index / total_steps if total_steps > 0 else 0
        commitment_boost = progress * 0.8
        if progress > 0.2:
            early_progress_bonus = (progress - 0.2) * 0.5
            commitment_boost += early_progress_bonus
        
        # 3. COGNITIVE RECOVERY: Low energy doesn't mean instant death
        energy_factor = cognitive_energy
        if cognitive_energy < 0.2 and perceived_value > 0.6:
            energy_factor = 0.3  # Minimum floor
        
        # Adjusted advantage
        adjusted_advantage = base_advantage + value_override + commitment_boost
        
        # 4. PROBABILISTIC MAPPING: Sigmoid
        steepness = 1.2
        base_prob = 1 / (1 + np.exp(-steepness * adjusted_advantage))
        
        # Progress-based probability boost
        progress_prob_boost = progress * 0.20
        base_prob += progress_prob_boost
        
        # 5. APPLY ARCHETYPE MODIFIERS
        adjusted_prob = base_prob * self.modifiers['base_persistence']
        
        # Value sensitivity
        if perceived_value > 0.6:
            value_bonus = (perceived_value - 0.6) * 0.2 * self.modifiers['value_sensitivity']
            adjusted_prob += value_bonus
        
        # Fatigue resilience
        if cognitive_energy < 0.3:
            fatigue_penalty = (0.3 - cognitive_energy) * 0.15
            fatigue_penalty *= (2.0 - self.modifiers['fatigue_resilience'])
            adjusted_prob -= fatigue_penalty
        
        # 6. BASE COMPLETION BIAS
        BASE_COMPLETION_PROB = 0.60
        adjusted_prob = max(BASE_COMPLETION_PROB, adjusted_prob)
        
        # 7. PERSISTENCE BIAS
        persistence_bonus = 0.18 + 0.22 * progress
        adjusted_prob += persistence_bonus
        
        # Cap at 95%
        adjusted_prob = min(adjusted_prob, 0.95)
        
        # 8. INTENT ALIGNMENT ADJUSTMENT (mirrors compute_intent_conditioned_continuation_prob)
        # Delay intent penalties until after step 2
        if step_index < 2:
            intent_penalty_factor = 1.0
        else:
            alignment_deficit = 1.0 - intent_alignment
            intent_penalty_raw = alignment_deficit * 0.10
            intent_penalty_factor = 1.0 - (intent_penalty_raw * 0.25)
            
            # Adaptive penalty dampening with progress
            progress_factor = step_index / total_steps if total_steps > 0 else 0
            penalty_dampening = 1.0 - (0.4 * progress_factor)
            intent_penalty_factor = 1.0 - ((1.0 - intent_penalty_factor) * penalty_dampening)
            
            adjusted_prob *= intent_penalty_factor
            
            # Intent boost for high alignment
            if intent_alignment >= 0.8:
                intent_boost = (intent_alignment - 0.8) * 0.15
                adjusted_prob += intent_boost
        
        # Intent mismatch penalty (if applicable)
        if intent_mismatch > 0.5:
            mismatch_penalty = intent_mismatch * 0.05  # Small penalty
            adjusted_prob -= mismatch_penalty
        
        # Final bounds
        adjusted_prob = np.clip(adjusted_prob, 0.35, 0.95)  # MIN_FINAL_PROB = 0.35
        
        return float(adjusted_prob)
    
    def get_feature_names(self) -> List[str]:
        """Get list of feature names in order."""
        return [
            'cognitive_energy',
            'intent_strength',
            'effort_tolerance',
            'risk_tolerance',
            'trust_baseline',
            'value_expectation',
            'step_effort',
            'step_risk',
            'step_value',
            'step_trust',
            'intent_mismatch'
        ]


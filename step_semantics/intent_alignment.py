"""
step_semantics/intent_alignment.py - Intent Alignment Analysis

Computes how well a step's semantic profile aligns with user intent,
and predicts the effect on drop probability.
"""

from typing import Dict, List, Optional
from .schema import StepSemanticProfile, IntentAlignmentResult, KnowledgeLevel


class IntentAlignmentAnalyzer:
    """
    Analyzes alignment between step semantics and user intent.
    
    Philosophy: We are not predicting clicks — we are modeling cognition.
    """
    
    def __init__(self):
        """Initialize intent alignment analyzer."""
        pass
    
    def analyze(self,
                semantic_profile: StepSemanticProfile,
                user_intent: Dict[str, float],
                persona_knowledge: str = "medium") -> IntentAlignmentResult:
        """
        Analyze intent alignment between step and user.
        
        Args:
            semantic_profile: Step's semantic profile
            user_intent: User's intent distribution (e.g., {"compare_options": 0.4, "quick_decision": 0.3})
            persona_knowledge: Persona's knowledge level ("low", "medium", "high")
        
        Returns:
            IntentAlignmentResult with alignment score and predicted effects
        """
        alignment_score = 1.0
        conflict_axes = []
        friction_delta = 0.0
        reasons = []
        
        # 1. Check knowledge gap
        knowledge_gap = self._check_knowledge_gap(
            semantic_profile.implied_user_knowledge,
            persona_knowledge
        )
        if knowledge_gap > 0:
            alignment_score -= knowledge_gap * 0.3
            conflict_axes.append('knowledge_gap')
            friction_delta += knowledge_gap * 0.2
            reasons.append(f"Step assumes {semantic_profile.implied_user_knowledge} knowledge, user has {persona_knowledge}")
        
        # 2. Check intent shift alignment
        intent_conflicts = self._check_intent_shifts(
            semantic_profile.intent_shift,
            user_intent
        )
        if intent_conflicts:
            alignment_score -= len(intent_conflicts) * 0.15
            conflict_axes.extend(intent_conflicts)
            friction_delta += len(intent_conflicts) * 0.1
            reasons.append(f"Step shifts intent away from user's primary intent")
        
        # 3. Check commitment mismatch (for compare/explore intents)
        if user_intent.get('compare_options', 0) > 0.3 or user_intent.get('learn_basics', 0) > 0.3:
            if semantic_profile.reversibility < 0.5:
                alignment_score -= 0.2
                conflict_axes.append('commitment')
                friction_delta += 0.15
                reasons.append("User wants to explore/compare but step requires commitment")
        
        # 4. Check speed mismatch (for quick_decision intent)
        if user_intent.get('quick_decision', 0) > 0.3:
            if semantic_profile.perceived_effort > 0.6:
                alignment_score -= 0.15
                conflict_axes.append('speed')
                friction_delta += 0.1
                reasons.append("User wants quick decision but step requires high effort")
            if semantic_profile.urgency < 0.5:
                alignment_score -= 0.1
                reasons.append("User expects urgency but step doesn't signal it")
        
        # 5. Check choice overload (for compare intent)
        if user_intent.get('compare_options', 0) > 0.3:
            if semantic_profile.choice_overload < 0.3:  # Too few options
                alignment_score -= 0.1
                conflict_axes.append('choice_availability')
                reasons.append("User wants to compare but step doesn't show options")
        
        # 6. Check trust signals (for risk-averse users)
        if semantic_profile.trust_signal < 0.5:
            friction_delta += 0.05
            reasons.append("Low trust signals may increase perceived risk")
        
        # 7. Check emotional impact
        if 'anxiety' in semantic_profile.emotional_deltas:
            anxiety_delta = semantic_profile.emotional_deltas['anxiety']
            if anxiety_delta > 0.2:
                alignment_score -= 0.1
                friction_delta += anxiety_delta * 0.1
                reasons.append("Step increases anxiety")
        
        # Normalize alignment score
        alignment_score = max(0.0, min(1.0, alignment_score))
        
        # Determine predicted effect
        if alignment_score < 0.5:
            predicted_effect = "increase_drop_probability"
        elif alignment_score > 0.7:
            predicted_effect = "decrease_drop_probability"
        else:
            predicted_effect = "neutral"
        
        # Combine reasons
        semantic_reason = "; ".join(reasons) if reasons else "Step aligns well with user intent"
        
        return IntentAlignmentResult(
            intent_alignment_score=alignment_score,
            conflict_axes=conflict_axes,
            predicted_effect=predicted_effect,
            semantic_reason=semantic_reason,
            friction_delta=friction_delta
        )
    
    def _check_knowledge_gap(self, step_knowledge: str, user_knowledge: str) -> float:
        """Check knowledge gap between step assumption and user level."""
        knowledge_levels = {'low': 0, 'medium': 1, 'high': 2}
        step_level = knowledge_levels.get(step_knowledge, 1)
        user_level = knowledge_levels.get(user_knowledge, 1)
        
        gap = step_level - user_level
        if gap > 0:  # Step assumes more knowledge than user has
            return min(1.0, gap * 0.5)
        return 0.0
    
    def _check_intent_shifts(self, step_intent_shift: Dict[str, float], user_intent: Dict[str, float]) -> List[str]:
        """Check if step shifts intent away from user's primary intent."""
        conflicts = []
        
        # Find user's primary intent
        primary_intent = max(user_intent.items(), key=lambda x: x[1])[0] if user_intent else None
        
        if not primary_intent:
            return conflicts
        
        # Check if step decreases user's primary intent
        if primary_intent in step_intent_shift:
            if step_intent_shift[primary_intent] < -0.2:
                conflicts.append('intent_shift')
        
        # Check if step increases conflicting intent
        conflicting_intents = {
            'compare_options': ['commit'],
            'explore': ['commit'],
            'quick_decision': ['explore', 'learn_basics'],
            'learn_basics': ['commit']
        }
        
        if primary_intent in conflicting_intents:
            for conflicting in conflicting_intents[primary_intent]:
                if conflicting in step_intent_shift and step_intent_shift[conflicting] > 0.2:
                    conflicts.append('intent_conflict')
        
        return conflicts


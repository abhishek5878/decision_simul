"""
dropsim_intent_model.py - Intent-Aware Causal Reasoning Layer

Introduces explicit Intent modeling to explain WHY users act, not just WHAT they do.
Transforms the system from behavior-level simulation to intent-aware causal reasoning.

This layer augments (does not replace) the existing behavioral engine.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import numpy as np


# ============================================================================
# INTENT FRAME ABSTRACTION
# ============================================================================

@dataclass
class IntentFrame:
    """
    Represents a user's underlying intent/goal when engaging with a product.
    
    This explains WHY users act, not just what they do.
    """
    intent_id: str
    description: str
    primary_goal: str
    tolerance_for_effort: float  # 0-1, higher = more tolerant
    tolerance_for_risk: float    # 0-1, higher = more tolerant
    expected_value_type: str     # "clarity", "comparison", "speed", "certainty", "exploration"
    commitment_threshold: float   # 0-1, how much commitment they'll accept before seeing value
    expected_reward: str         # What they expect to get
    acceptable_friction: float   # 0-1, how much friction they'll tolerate
    typical_exit_triggers: List[str]  # What causes them to leave
    expected_completion_behavior: str  # How they typically complete
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'intent_id': self.intent_id,
            'description': self.description,
            'primary_goal': self.primary_goal,
            'tolerance_for_effort': self.tolerance_for_effort,
            'tolerance_for_risk': self.tolerance_for_risk,
            'expected_value_type': self.expected_value_type,
            'commitment_threshold': self.commitment_threshold,
            'expected_reward': self.expected_reward,
            'acceptable_friction': self.acceptable_friction,
            'typical_exit_triggers': self.typical_exit_triggers,
            'expected_completion_behavior': self.expected_completion_behavior
        }


# ============================================================================
# GLOBAL INTENT FOR CREDIGO
# ============================================================================

# All users entering Credigo share the same primary intent:
# "Give me a new or better credit card recommendation"
# This is ground truth, not inferred.
# Note: This is NOT about comparing options - it's about getting a personalized recommendation
CREDIGO_GLOBAL_INTENT = IntentFrame(
    intent_id="credit_card_recommendation",
    description="User wants a new or better credit card recommendation (personalized, not comparison)",
    primary_goal="Get a personalized credit card recommendation that matches their needs",
    tolerance_for_effort=0.6,  # Moderate - will put in effort to get good recommendation
    tolerance_for_risk=0.5,    # Moderate - needs to understand risks
    expected_value_type="certainty",  # They want a clear recommendation, not comparison
    commitment_threshold=0.5,  # Moderate-high - will commit if recommendation is good
    expected_reward="Clear personalized credit card recommendation that fits their needs",
    acceptable_friction=0.5,   # Moderate tolerance for friction (questions to personalize)
    typical_exit_triggers=[
        "Asked for too much personal info before showing recommendation",
        "Forced to commit before seeing recommendation",
        "Recommendation seems generic or not personalized",
        "Too many irrelevant questions",
        "High friction data collection steps"
    ],
    expected_completion_behavior="Answers questions, sees personalized recommendation, then decides"
)


# ============================================================================
# GLOBAL INTENT FOR KEEPER SS
# ============================================================================

# All users entering Keeper SS are founders, business owners, or CEOs
# Their primary intent: "Calculate the financial impact of unused leave on my balance sheet"
# This is ground truth, not inferred.
KEEPER_SS_GLOBAL_INTENT = IntentFrame(
    intent_id="calculate_leave_liability",
    description="Founder/business owner/CEO wants to calculate leave liability financial impact",
    primary_goal="Understand financial impact of unused leave on balance sheet",
    tolerance_for_effort=0.7,  # High - business owners will put in effort for financial insights
    tolerance_for_risk=0.3,    # Low - sharing company financial data is sensitive
    expected_value_type="certainty",  # They want clear financial calculations
    commitment_threshold=0.6,  # High - will commit if they see value (financial insights)
    expected_reward="Clear financial calculation showing leave liability impact (e.g., ₹1.97 Cr)",
    acceptable_friction=0.6,   # Moderate-high - will tolerate data entry for valuable insights
    typical_exit_triggers=[
        "Too many questions before showing calculations",
        "Unclear how data will be used",
        "No clear value proposition",
        "Asking for sensitive financial data too early"
    ],
    expected_completion_behavior="Enters company data, sees financial calculations, then decides"
)


# ============================================================================
# GLOBAL INTENT FOR TRIAL1 (User Feedback Collection Tool)
# ============================================================================

# All users entering Trial1 are indie founders and small SaaS teams
# Their primary intent: "Use this tool to collect user feedback for my product"
# This is ground truth, not inferred.
TRIAL1_GLOBAL_INTENT = IntentFrame(
    intent_id="collect_user_feedback",
    description="Indie founder/small SaaS team wants to collect user feedback for their product",
    primary_goal="Set up and use the tool to collect feedback from their users",
    tolerance_for_effort=0.7,  # High - will put in effort to get valuable feedback
    tolerance_for_risk=0.5,    # Moderate - sharing product info is acceptable for feedback value
    expected_value_type="certainty",  # They want clear, actionable feedback
    commitment_threshold=0.5,  # Moderate - will commit if they see how it helps collect feedback
    expected_reward="Working feedback collection tool that helps them understand their users",
    acceptable_friction=0.6,   # Moderate-high - will tolerate setup for valuable feedback insights
    typical_exit_triggers=[
        "Too much setup before seeing how feedback collection works",
        "Unclear how to collect feedback or what value it provides",
        "Asking for payment before demonstrating feedback collection",
        "Tool seems too complex or doesn't match their feedback needs"
    ],
    expected_completion_behavior="Sets up feedback collection, sees how it works, then decides to use it or not"
)


# ============================================================================
# CANONICAL INTENT SET (v1)
# ============================================================================

CANONICAL_INTENTS = {
    "compare_options": IntentFrame(
        intent_id="compare_options",
        description="User wants to compare multiple options before deciding",
        primary_goal="See alternatives side-by-side, understand differences",
        tolerance_for_effort=0.6,  # Moderate - will put in effort to compare
        tolerance_for_risk=0.5,    # Moderate - needs to understand risks
        expected_value_type="comparison",
        commitment_threshold=0.3,  # Low - doesn't want to commit early
        expected_reward="Clear comparison of options with pros/cons",
        acceptable_friction=0.4,
        typical_exit_triggers=[
            "Asked for personal info before showing options",
            "Forced to commit before seeing alternatives",
            "No comparison view available"
        ],
        expected_completion_behavior="Compares options, then decides"
    ),
    
    "validate_choice": IntentFrame(
        intent_id="validate_choice",
        description="User has a choice in mind, wants to validate it's right",
        primary_goal="Confirm their choice is correct/optimal",
        tolerance_for_effort=0.5,
        tolerance_for_risk=0.4,  # Lower - wants certainty
        expected_value_type="certainty",
        commitment_threshold=0.5,  # Moderate - will commit if validated
        expected_reward="Confirmation that their choice is good",
        acceptable_friction=0.3,
        typical_exit_triggers=[
            "Validation requires too much personal info",
            "Can't verify without committing",
            "Unclear if choice is validated"
        ],
        expected_completion_behavior="Validates choice, then proceeds"
    ),
    
    "learn_basics": IntentFrame(
        intent_id="learn_basics",
        description="User wants to learn about the product/service",
        primary_goal="Understand what the product does, how it works",
        tolerance_for_effort=0.7,  # High - willing to learn
        tolerance_for_risk=0.6,    # Moderate - exploring
        expected_value_type="clarity",
        commitment_threshold=0.2,  # Very low - just learning
        expected_reward="Clear explanation, educational content",
        acceptable_friction=0.5,
        typical_exit_triggers=[
            "Forced to sign up to learn",
            "Information is unclear or missing",
            "Too much commitment required"
        ],
        expected_completion_behavior="Learns, then may or may not proceed"
    ),
    
    "quick_decision": IntentFrame(
        intent_id="quick_decision",
        description="User wants to make a fast decision",
        primary_goal="Get to decision/action quickly",
        tolerance_for_effort=0.3,  # Low - wants speed
        tolerance_for_risk=0.5,    # Moderate
        expected_value_type="speed",
        commitment_threshold=0.6,  # Higher - will commit if fast
        expected_reward="Quick path to decision/action",
        acceptable_friction=0.2,  # Very low friction tolerance
        typical_exit_triggers=[
            "Too many steps",
            "Slow loading",
            "Complex forms",
            "Long wait times"
        ],
        expected_completion_behavior="Completes quickly or exits"
    ),
    
    "price_check": IntentFrame(
        intent_id="price_check",
        description="User wants to check pricing/costs",
        primary_goal="Understand pricing, fees, costs",
        tolerance_for_effort=0.4,
        tolerance_for_risk=0.5,
        expected_value_type="clarity",
        commitment_threshold=0.2,  # Low - just checking prices
        expected_reward="Clear pricing information",
        acceptable_friction=0.3,
        typical_exit_triggers=[
            "Pricing hidden behind signup",
            "Unclear pricing structure",
            "Forced to commit to see prices"
        ],
        expected_completion_behavior="Checks prices, then decides"
    ),
    
    "eligibility_check": IntentFrame(
        intent_id="eligibility_check",
        description="User wants to check if they're eligible",
        primary_goal="Determine if they qualify",
        tolerance_for_effort=0.5,
        tolerance_for_risk=0.4,  # Lower - checking eligibility feels risky
        expected_value_type="certainty",
        commitment_threshold=0.4,  # Moderate
        expected_reward="Clear eligibility status",
        acceptable_friction=0.4,
        typical_exit_triggers=[
            "Eligibility check requires too much info",
            "Unclear eligibility criteria",
            "Forced to commit before checking"
        ],
        expected_completion_behavior="Checks eligibility, then proceeds if eligible"
    )
}


# ============================================================================
# INTENT INFERENCE LAYER
# ============================================================================

def infer_intent_distribution(
    entry_page_text: Optional[str] = None,
    copy_semantics: Optional[Dict] = None,
    cta_phrasing: Optional[str] = None,
    early_step_friction: Optional[Dict] = None,
    persona_attributes: Optional[Dict] = None,
    product_type: Optional[str] = None,
    product_steps: Optional[Dict] = None
) -> Dict[str, float]:
    """
    Infer probabilistic intent distribution from entry signals.
    
    Input:
        entry_page_text: Text from landing/entry page
        copy_semantics: Semantic analysis of copy (e.g., {"comparison": 0.3, "speed": 0.5})
        cta_phrasing: CTA button text
        early_step_friction: Friction in first 2-3 steps
        persona_attributes: Persona traits (intent, urgency, etc.)
        product_type: Type of product (fintech, e-commerce, etc.)
    
    Output:
        {
            "intent_distribution": {
            "compare_options": 0.42,
            "learn_basics": 0.31,
            "quick_decision": 0.18,
                ...
            }
        }
    
    This is deterministic given same inputs (no randomness).
    """
    # Initialize base distribution (uniform prior)
    intent_weights = {intent_id: 1.0 / len(CANONICAL_INTENTS) for intent_id in CANONICAL_INTENTS.keys()}
    
    # 0. Product Steps Analysis (if provided - use intent signals from steps)
    if product_steps:
        first_step = list(product_steps.values())[0]
        if 'intent_signals' in first_step:
            # Use intent signals from step definition
            for intent_id, signal_strength in first_step['intent_signals'].items():
                if intent_id in intent_weights:
                    intent_weights[intent_id] *= (1.0 + signal_strength)  # Boost based on signal
    
    # 1. CTA Phrasing Analysis
    if cta_phrasing:
        cta_lower = cta_phrasing.lower()
        
        # Quick decision signals
        if any(word in cta_lower for word in ['now', 'instant', 'quick', 'fast', 'immediate', '10s', '60s']):
            intent_weights['quick_decision'] *= 2.0
            intent_weights['learn_basics'] *= 0.5
        
        # Comparison signals
        if any(word in cta_lower for word in ['compare', 'find best', 'match', 'recommend']):
            intent_weights['compare_options'] *= 2.0
            intent_weights['validate_choice'] *= 1.5
        
        # Eligibility/validation signals
        if any(word in cta_lower for word in ['check', 'eligibility', 'verify', 'validate', 'see if']):
            intent_weights['eligibility_check'] *= 2.5
            intent_weights['validate_choice'] *= 1.5
        
        # Learning signals
        if any(word in cta_lower for word in ['learn', 'discover', 'explore', 'understand']):
            intent_weights['learn_basics'] *= 2.0
    
    # 1b. CTA from Product Steps (if available)
    if product_steps:
        first_step = list(product_steps.values())[0]
        step_cta = first_step.get('cta_phrasing', '')
        if step_cta:
            cta_lower = step_cta.lower()
            
            # Quick decision signals
            if any(word in cta_lower for word in ['now', 'instant', 'quick', 'fast', 'immediate', '10s', '60s', 'seconds']):
                intent_weights['quick_decision'] *= 2.0
                intent_weights['learn_basics'] *= 0.5
            
            # Comparison signals
            if any(word in cta_lower for word in ['compare', 'find best', 'match', 'recommend', 'best']):
                intent_weights['compare_options'] *= 2.0
                intent_weights['validate_choice'] *= 1.5
            
            # Eligibility/validation signals
            if any(word in cta_lower for word in ['check', 'eligibility', 'verify', 'validate', 'see if']):
                intent_weights['eligibility_check'] *= 2.5
                intent_weights['validate_choice'] *= 1.5
    
    # 2. Entry Page Text Analysis
    if entry_page_text:
        text_lower = entry_page_text.lower()
        
        # Price-focused
        if any(word in text_lower for word in ['price', 'cost', 'fee', '₹', 'rupee', 'affordable']):
            intent_weights['price_check'] *= 1.8
        
        # Comparison-focused
        if any(word in text_lower for word in ['compare', 'best', 'top', 'vs', 'versus', 'options']):
            intent_weights['compare_options'] *= 1.8
        
        # Speed-focused
        if any(word in text_lower for word in ['quick', 'fast', 'instant', 'seconds', 'minutes']):
            intent_weights['quick_decision'] *= 1.5
    
    # 3. Copy Semantics Analysis
    if copy_semantics:
        if copy_semantics.get('comparison', 0) > 0.3:
            intent_weights['compare_options'] *= 1.5
        if copy_semantics.get('speed', 0) > 0.3:
            intent_weights['quick_decision'] *= 1.5
        if copy_semantics.get('clarity', 0) > 0.3:
            intent_weights['learn_basics'] *= 1.3
    
    # 4. Early Step Friction Analysis
    if early_step_friction:
        # High early friction suggests learning/exploration intent
        avg_friction = early_step_friction.get('avg_effort', 0) + early_step_friction.get('avg_risk', 0)
        if avg_friction > 0.6:
            intent_weights['learn_basics'] *= 1.2
            intent_weights['quick_decision'] *= 0.7  # High friction hurts quick decision
    
    # 5. Persona Attributes
    if persona_attributes:
        intent_level = persona_attributes.get('intent', 'medium')
        urgency = persona_attributes.get('urgency', 'medium')
        
        if intent_level == 'high':
            intent_weights['quick_decision'] *= 1.3
            intent_weights['eligibility_check'] *= 1.2
        elif intent_level == 'low':
            intent_weights['learn_basics'] *= 1.3
            intent_weights['compare_options'] *= 1.2
        
        if urgency == 'high':
            intent_weights['quick_decision'] *= 1.5
            intent_weights['learn_basics'] *= 0.7
        
        # Risk attitude affects validation intent
        risk_attitude = persona_attributes.get('risk_attitude', 'balanced')
        if risk_attitude == 'risk_averse':
            intent_weights['validate_choice'] *= 1.3
            intent_weights['eligibility_check'] *= 1.2
    
    # 6. Product Type Adjustments
    if product_type:
        if product_type in ['fintech', 'lending', 'credit']:
            # Financial products often involve eligibility/validation
            intent_weights['eligibility_check'] *= 1.3
            intent_weights['validate_choice'] *= 1.2
        elif product_type in ['e-commerce', 'marketplace']:
            # Shopping involves comparison
            intent_weights['compare_options'] *= 1.4
            intent_weights['price_check'] *= 1.3
    
    # Normalize to probabilities
    total_weight = sum(intent_weights.values())
    intent_distribution = {intent_id: weight / total_weight for intent_id, weight in intent_weights.items()}
    
    return {
        'intent_distribution': intent_distribution,
        'primary_intent': max(intent_distribution.items(), key=lambda x: x[1])[0],
        'primary_intent_confidence': max(intent_distribution.values())
    }


# ============================================================================
# INTENT-STEP ALIGNMENT
# ============================================================================

def compute_intent_alignment_score(
    step: Dict,
    intent_frame: IntentFrame,
    step_index: int,
    total_steps: int
) -> float:
    """
    Compute how well a step aligns with user's intent.
    Now uses intent_signals from step definition if available.
    """
    """
    Compute how well a step aligns with user's intent.
    
    Returns: 0-1 score where 1 = perfect alignment, 0 = complete misalignment
    """
    alignment = 1.0
    
    # 0. Intent Signals from Step Definition (if available)
    if 'intent_signals' in step:
        intent_signal = step['intent_signals'].get(intent_frame.intent_id, 0.5)
        # Use intent signal as base alignment (0-1 scale)
        alignment = intent_signal
    else:
        # Fallback to computed alignment
        alignment = 1.0
    
    # 1. Commitment Threshold Check
    # If step requires commitment but intent has low commitment threshold → misalignment
    step_commitment = step.get('irreversibility', 0) + (step.get('effort_demand', 0) * 0.5)
    
    # Check if step is a commitment gate
    if step.get('commitment_gate', False):
        step_commitment += 0.3  # Commitment gates add extra commitment
    
    if step_commitment > intent_frame.commitment_threshold:
        # Penalty for exceeding commitment threshold
        excess = step_commitment - intent_frame.commitment_threshold
        alignment -= excess * 0.5  # Up to 50% penalty
    
    # 2. Comparison Availability Check (for compare_credit_cards or compare_options intent)
    if intent_frame.intent_id in ['compare_credit_cards', 'compare_options']:
        comparison_available = step.get('comparison_available', False)
        if not comparison_available and step_index > 2:  # After step 2, should have comparison
            alignment -= 0.3  # Major penalty for no comparison
    
    # 3. Value Type Alignment
    step_value_type = infer_step_value_type(step)
    if step_value_type != intent_frame.expected_value_type:
        # Misalignment penalty
        alignment -= 0.2
    
    # 4. Effort Tolerance Check
    step_effort = step.get('effort_demand', 0)
    if step_effort > intent_frame.acceptable_friction:
        excess = step_effort - intent_frame.acceptable_friction
        alignment -= excess * 0.3  # Up to 30% penalty
    
    # 5. Risk Tolerance Check
    step_risk = step.get('risk_signal', 0)
    if step_risk > intent_frame.tolerance_for_risk:
        excess = step_risk - intent_frame.tolerance_for_risk
        alignment -= excess * 0.2  # Up to 20% penalty
    
    # 6. Expected Reward Check
    # If step doesn't deliver expected reward type → misalignment
    step_explicit_value = step.get('explicit_value', 0)
    if step_explicit_value < 0.3 and intent_frame.expected_value_type in ['clarity', 'comparison']:
        # Low value when expecting clarity/comparison → misalignment
        alignment -= 0.15
    
    # 7. Progress Toward Goal
    # Later steps should align better if user has committed
    progress = step_index / total_steps if total_steps > 0 else 0
    if progress > intent_frame.commitment_threshold:
        # User has committed, alignment improves
        alignment += 0.1 * (progress - intent_frame.commitment_threshold)
    
    return np.clip(alignment, 0.0, 1.0)


def infer_step_value_type(step: Dict) -> str:
    """
    Infer what type of value a step provides based on its characteristics.
    """
    explicit_value = step.get('explicit_value', 0)
    delay_to_value = step.get('delay_to_value', 5)
    effort_demand = step.get('effort_demand', 0)
    
    # High explicit value, low delay → speed/certainty
    if explicit_value > 0.6 and delay_to_value < 2:
        return "speed"
    
    # Low explicit value, high delay → exploration/learning
    if explicit_value < 0.3 and delay_to_value > 3:
        return "clarity"
    
    # Medium value, medium delay → comparison/validation
    if 0.3 <= explicit_value <= 0.6:
        return "comparison"
    
    # Default
    return "clarity"


# ============================================================================
# INTENT-AWARE FAILURE ANALYSIS
# ============================================================================

def identify_intent_mismatch(
    step: Dict,
    intent_frame: IntentFrame,
    step_index: int,
    total_steps: int,
    failure_reason: str
) -> Dict:
    """
    Identify if failure was due to intent mismatch.
    
    Returns:
        {
            'is_intent_mismatch': bool,
            'mismatch_score': float,
            'violated_intent': str,
            'mismatch_type': str,
            'explanation': str
        }
    """
    alignment = compute_intent_alignment_score(step, intent_frame, step_index, total_steps)
    
    # More sensitive mismatch detection
    # Consider it a mismatch if alignment is below threshold OR if user actually dropped
    is_mismatch = alignment < 0.6  # Lower threshold for more sensitivity
    mismatch_score = 1.0 - alignment
    
    # If alignment is moderate (0.5-0.7) but step has high commitment/effort, still consider mismatch
    step_commitment = step.get('irreversibility', 0) + (step.get('effort_demand', 0) * 0.5)
    if 0.5 <= alignment < 0.7 and step_commitment > intent_frame.commitment_threshold:
        is_mismatch = True
        mismatch_score = max(mismatch_score, 0.3)  # Minimum mismatch score
    
    # Identify what was violated
    violations = []
    
    step_commitment = step.get('irreversibility', 0) + (step.get('effort_demand', 0) * 0.5)
    if step_commitment > intent_frame.commitment_threshold:
        violations.append("commitment_threshold")
    
    step_effort = step.get('effort_demand', 0)
    if step_effort > intent_frame.acceptable_friction:
        violations.append("effort_tolerance")
    
    step_risk = step.get('risk_signal', 0)
    if step_risk > intent_frame.tolerance_for_risk:
        violations.append("risk_tolerance")
    
    step_value_type = infer_step_value_type(step)
    if step_value_type != intent_frame.expected_value_type:
        violations.append("value_type_mismatch")
    
    # Generate explanation
    if is_mismatch:
        primary_violation = violations[0] if violations else "general_mismatch"
        
        if primary_violation == "commitment_threshold":
            explanation = (
                f"Users entered with {intent_frame.description} intent, but the step required "
                f"commitment ({step_commitment:.2f}) exceeding their threshold "
                f"({intent_frame.commitment_threshold:.2f}). This caused intent misalignment."
            )
        elif primary_violation == "effort_tolerance":
            explanation = (
                f"Users entered with {intent_frame.description} intent, but the step required "
                f"effort ({step_effort:.2f}) exceeding their tolerance "
                f"({intent_frame.acceptable_friction:.2f})."
            )
        elif primary_violation == "value_type_mismatch":
            explanation = (
                f"Users entered expecting {intent_frame.expected_value_type} value, but the step "
                f"provided {step_value_type} value. This mismatch caused abandonment."
            )
        else:
            explanation = (
                f"Step characteristics don't align with user's {intent_frame.description} intent. "
                f"Alignment score: {alignment:.2f}"
            )
    else:
        explanation = f"Step aligns well with {intent_frame.description} intent (alignment: {alignment:.2f})"
    
    return {
        'is_intent_mismatch': is_mismatch,
        'mismatch_score': mismatch_score,
        'violated_intent': intent_frame.intent_id,
        'mismatch_type': violations[0] if violations else None,
        'violations': violations,
        'alignment_score': alignment,
        'explanation': explanation
    }


# ============================================================================
# INTENT-CONDITIONED CONTINUATION PROBABILITY
# ============================================================================

def compute_intent_conditioned_continuation_prob(
    base_prob: float,
    intent_frame: IntentFrame,
    step: Dict,
    step_index: int,
    total_steps: int,
    state: Optional[Dict] = None
) -> Tuple[float, Dict]:
    """
    Adjust continuation probability based on intent alignment.
    
    FIXED: Uses bounded additive scoring instead of multiplicative collapse.
    
    Returns:
        (adjusted_probability, diagnostic_dict)
    """
    # Constants
    MIN_PROB = 0.05
    MAX_PROB = 0.95
    MAX_TOTAL_PENALTY = 0.45  # Cap maximum total penalty contribution
    
    alignment = compute_intent_alignment_score(step, intent_frame, step_index, total_steps)
    
    # Initialize diagnostic
    diagnostic = {
        "base_prob": base_prob,
        "intent_alignment": alignment,
        "penalties": {},
        "amplifiers": {},
        "final_prob": base_prob,
        "dominant_factor": "base"
    }
    
    # Start with base probability
    adjusted_prob = base_prob
    
    # Track total penalty for capping
    total_penalty = 0.0
    
    # RULE 6: Delay intent penalties until after step 2
    # Intent mismatch should not punish early exploration
    if step_index < 2:
        intent_penalty_factor = 1.0  # No penalty for first 2 steps
        diagnostic["penalties"]["intent"] = 0.0
        diagnostic["amplifiers"]["exploration_grace"] = 0.0
    else:
        # RULE 2: Soften penalty strength with bounded attenuation
        # Replace harsh penalty multiplication with bounded attenuation
        alignment_deficit = 1.0 - alignment
        
        # Intent penalty as attenuation factor (not direct reduction)
        # Extremely reduced penalties to prevent collapse
        intent_penalty_raw = alignment_deficit * 0.10  # Reduced to 0.10 (up to 10% penalty raw)
        intent_penalty_factor = 1.0 - (intent_penalty_raw * 0.25)  # Bounded attenuation: max 2.5% reduction
        
        # Adaptive penalty dampening with progress
        progress_factor = step_index / total_steps if total_steps > 0 else 0
        penalty_dampening = 1.0 - (0.4 * progress_factor)  # Up to 40% dampening at end
        intent_penalty_factor = 1.0 - ((1.0 - intent_penalty_factor) * penalty_dampening)
        
        # Apply as multiplicative factor (bounded attenuation)
        adjusted_prob *= intent_penalty_factor
        intent_penalty_amount = base_prob * (1.0 - intent_penalty_factor)
        total_penalty += intent_penalty_amount
        diagnostic["penalties"]["intent"] = -intent_penalty_amount
        
        # Intent boost for high alignment (additive)
        if alignment >= 0.8:
            intent_boost = (alignment - 0.8) * 0.15  # Up to 3% boost
            adjusted_prob += intent_boost
            diagnostic["amplifiers"]["intent_alignment"] = intent_boost
    
    # Intent-specific adjustments (bounded attenuation)
    intent_specific_factor = 1.0
    
    if intent_frame.intent_id == "quick_decision":
        # Quick decision users are more sensitive to delays
        if step.get('delay_to_value', 5) > 3:
            delay_penalty_raw = 0.15  # 15% raw penalty
            delay_penalty_factor = 1.0 - (delay_penalty_raw * 0.5)  # Bounded: max 7.5% reduction
            intent_specific_factor *= delay_penalty_factor
            delay_penalty_amount = adjusted_prob * (1.0 - delay_penalty_factor)
            total_penalty += delay_penalty_amount
            diagnostic["penalties"]["delay"] = -delay_penalty_amount
    
    elif intent_frame.intent_id in ["compare_credit_cards", "compare_options"]:
        # Comparison users need to see options
        # For Credigo: users want credit card recommendation, so comparison is critical
        # Reduced penalty to prevent collapse
        if not step.get('comparison_available', False) and step_index > 2:
            comparison_penalty_raw = 0.08  # Reduced from 0.12 to 0.08 (8% raw penalty)
            comparison_penalty_factor = 1.0 - (comparison_penalty_raw * 0.4)  # Bounded: max 3.2% reduction (reduced)
            intent_specific_factor *= comparison_penalty_factor
            comparison_penalty_amount = adjusted_prob * (1.0 - comparison_penalty_factor)
            total_penalty += comparison_penalty_amount
            diagnostic["penalties"]["no_comparison"] = -comparison_penalty_amount
    
    elif intent_frame.intent_id == "learn_basics":
        # Learning users are more tolerant of effort if it's educational
        if step.get('cognitive_demand', 0) > 0.5 and step.get('explicit_value', 0) > 0.3:
            educational_boost = 0.05  # 5% boost (additive)
            adjusted_prob += educational_boost
            diagnostic["amplifiers"]["educational_content"] = educational_boost
    
    adjusted_prob *= intent_specific_factor
    
    # RULE 3: Cap maximum total penalty contribution
    if total_penalty > MAX_TOTAL_PENALTY:
        penalty_scale = MAX_TOTAL_PENALTY / total_penalty
        # Scale down all penalties proportionally
        for key in diagnostic["penalties"]:
            diagnostic["penalties"][key] *= penalty_scale
        # Recalculate adjusted_prob with capped penalties
        adjusted_prob = base_prob + sum(diagnostic["penalties"].values())
        diagnostic["amplifiers"]["penalty_cap_applied"] = total_penalty - MAX_TOTAL_PENALTY
    
    # RULE 5: Enforce hard probability bounds
    adjusted_prob = np.clip(adjusted_prob, MIN_PROB, MAX_PROB)
    
    # CRITICAL: Ensure minimum completion probability even after all penalties
    # Maximum aggressive increase to prevent collapse
    MIN_COMPLETION_PROB = 0.40  # Increased to 0.40 (40% minimum)
    if adjusted_prob < MIN_COMPLETION_PROB:
        floor_boost = MIN_COMPLETION_PROB - adjusted_prob
        adjusted_prob = MIN_COMPLETION_PROB
        diagnostic["amplifiers"]["min_completion_floor"] = floor_boost
    
    # Determine dominant factor
    if abs(diagnostic["penalties"].get("intent", 0)) > 0.1:
        diagnostic["dominant_factor"] = "intent_mismatch"
    elif abs(diagnostic["penalties"].get("delay", 0)) > 0.05:
        diagnostic["dominant_factor"] = "delay"
    elif abs(diagnostic["penalties"].get("no_comparison", 0)) > 0.05:
        diagnostic["dominant_factor"] = "no_comparison"
    else:
        diagnostic["dominant_factor"] = "base"
    
    diagnostic["final_prob"] = adjusted_prob
    
    return adjusted_prob, diagnostic
    
    return np.clip(adjusted_prob, 0.05, 0.95)

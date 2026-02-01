"""
behavioral_engine.py - Cognitive State-Based Behavioral Simulation Engine

Implements the behavioral framework:
- Raw persona inputs → Compiled latent priors
- Internal state tracking (cognitive energy, perceived risk/effort/value/control)
- Deterministic state variants (one persona, multiple trajectories)
- Step-by-step cognitive/effort/risk cost computation
- Drop-off decision with failure reason identification

This answers "WHY they dropped at step t" before "WHO".
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import Counter


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class FailureReason(Enum):
    """Dominant failure reasons."""
    SYSTEM2_FATIGUE = "System 2 fatigue"
    LOW_ABILITY = "Low ability"
    LOSS_AVERSION = "Loss aversion"
    TEMPORAL_DISCOUNTING = "Temporal discounting"
    MULTI_FACTOR = "Multi-factor failure"


# ============================================================================
# STATE VARIANT DEFINITIONS (Structured, Deterministic)
# ============================================================================

STATE_VARIANTS = {
    "fresh_motivated": {
        "cognitive_energy_mult": 0.9,
        "perceived_value": 0.8,
        "perceived_risk": 0.1,
        "perceived_effort": 0.1,
        "perceived_control": 0.75,
        "description": "Fresh arrival, high motivation"
    },
    "tired_commuter": {
        "cognitive_energy_mult": 0.45,  # INCREASED PENALTY: 0.5 -> 0.45
        "perceived_value": 0.55,  # INCREASED PENALTY: 0.6 -> 0.55
        "perceived_risk": 0.25,  # INCREASED PENALTY: 0.2 -> 0.25
        "perceived_effort": 0.35,  # INCREASED PENALTY: 0.3 -> 0.35
        "perceived_control": 0.45,  # INCREASED PENALTY: 0.5 -> 0.45
        "description": "Tired, lower energy - STRONGER PENALTIES"
    },
    "distrustful_arrival": {
        "cognitive_energy_mult": 0.8,
        "perceived_value": 0.55,  # INCREASED PENALTY: 0.6 -> 0.55
        "perceived_risk": 0.5,  # INCREASED PENALTY: 0.4 -> 0.5
        "perceived_effort": 0.25,  # INCREASED PENALTY: 0.2 -> 0.25
        "perceived_control": 0.2,  # MUCH STRONGER PENALTY: 0.3 -> 0.2 (trust)
        "description": "Arrives with trust concerns - STRONGER PENALTIES"
    },
    "browsing_casually": {
        "cognitive_energy_mult": 0.9,
        "perceived_value": 0.25,  # INCREASED PENALTY: 0.3 -> 0.25
        "perceived_risk": 0.1,
        "perceived_effort": 0.2,
        "perceived_control": 0.6,
        "description": "Low urgency, exploring"
    },
    "urgent_need": {
        "cognitive_energy_mult": 0.7,
        "perceived_value": 0.95,  # INCREASED BONUS: 0.9 -> 0.95
        "perceived_risk": 0.15,  # INCREASED BONUS: 0.2 -> 0.15
        "perceived_effort": 0.08,  # INCREASED BONUS: 0.1 -> 0.08
        "perceived_control": 0.85,  # INCREASED BONUS: 0.8 -> 0.85
        "description": "High urgency, strong motivation - STRONGER BONUSES"
    },
    "price_sensitive": {
        "cognitive_energy_mult": 0.8,
        "perceived_value": 0.3,  # MUCH STRONGER PENALTY: 0.4 -> 0.3
        "perceived_risk": 0.35,  # INCREASED PENALTY: 0.3 -> 0.35
        "perceived_effort": 0.25,  # INCREASED PENALTY: 0.2 -> 0.25
        "perceived_control": 0.45,  # INCREASED PENALTY: 0.5 -> 0.45
        "description": "Highly price-conscious - STRONGER PENALTIES"
    },
    "tech_savvy_optimistic": {
        "cognitive_energy_mult": 0.98,  # INCREASED BONUS: 0.95 -> 0.98
        "perceived_value": 0.75,  # INCREASED BONUS: 0.7 -> 0.75
        "perceived_risk": 0.02,  # MUCH STRONGER BONUS: 0.05 -> 0.02
        "perceived_effort": 0.03,  # MUCH STRONGER BONUS: 0.05 -> 0.03
        "perceived_control": 0.9,  # STRONGER BONUS: 0.8 -> 0.9 (trust)
        "description": "High digital literacy, optimistic - STRONGER BONUSES"
    }
}


# ============================================================================
# PRODUCT STEP DEFINITIONS (Credigo.club)
# ============================================================================

PRODUCT_STEPS = {
    "Landing Page": {
        "cognitive_demand": 0.2,
        "effort_demand": 0.0,
        "risk_signal": 0.1,
        "irreversibility": 0,
        "delay_to_value": 5,
        "explicit_value": 0.3,
        "reassurance_signal": 0.6,  # "No PAN, no data" is strong
        "authority_signal": 0.2,
        "description": "Initial landing, privacy claims"
    },
    "Quiz Start": {
        "cognitive_demand": 0.3,
        "effort_demand": 0.2,
        "risk_signal": 0.15,
        "irreversibility": 0,
        "delay_to_value": 4,
        "explicit_value": 0.2,
        "reassurance_signal": 0.4,
        "authority_signal": 0.1,
        "description": "First questions appear"
    },
    "Quiz Progression": {
        "cognitive_demand": 0.4,
        "effort_demand": 0.3,
        "risk_signal": 0.2,
        "irreversibility": 0,
        "delay_to_value": 3,
        "explicit_value": 0.25,
        "reassurance_signal": 0.3,
        "authority_signal": 0.1,
        "description": "Mid-quiz, questions continue"
    },
    "Quiz Completion": {
        "cognitive_demand": 0.2,
        "effort_demand": 0.1,
        "risk_signal": 0.1,
        "irreversibility": 0,
        "delay_to_value": 1,
        "explicit_value": 0.5,  # Completion feels good
        "reassurance_signal": 0.5,
        "authority_signal": 0.2,
        "description": "Quiz finished, anticipation"
    },
    "Results Page": {
        "cognitive_demand": 0.3,
        "effort_demand": 0.1,
        "risk_signal": 0.15,
        "irreversibility": 0,
        "delay_to_value": 0.5,
        "explicit_value": 0.7,  # Value delivered!
        "reassurance_signal": 0.4,
        "authority_signal": 0.3,
        "description": "Personalized recommendations shown"
    },
    "Post-Results": {
        "cognitive_demand": 0.4,
        "effort_demand": 0.8,  # HIGH - must go to bank site
        "risk_signal": 0.2,
        "irreversibility": 0,
        "delay_to_value": 2,
        "explicit_value": 0.3,
        "reassurance_signal": 0.2,
        "authority_signal": 0.1,
        "description": "No apply button, manual redirect"
    }
}


# ============================================================================
# PERSONA INPUT NORMALIZATION
# ============================================================================

def normalize_persona_inputs(row: pd.Series, derived: Dict) -> Dict:
    """
    Map raw persona data to normalized [0,1] inputs.
    
    Returns dict with all required fields normalized.
    """
    # Extract and normalize
    inputs = {}
    
    # SEC (Socio-Economic Class) - proxy from occupation + education
    occupation = str(row.get('occupation', '')).lower()
    education = str(row.get('education_level', '')).lower()
    
    if any(x in occupation for x in ['manager', 'director', 'executive', 'engineer', 'doctor', 'lawyer']):
        inputs['SEC'] = 0.8
    elif any(x in occupation for x in ['professional', 'graduate', 'bachelor']):
        inputs['SEC'] = 0.6
    elif any(x in education for x in ['graduate', 'professional']):
        inputs['SEC'] = 0.5
    elif any(x in education for x in ['higher secondary', '12th']):
        inputs['SEC'] = 0.3
    else:
        inputs['SEC'] = 0.2
    
    # UrbanRuralTier
    urban = derived.get('urban_rural', 'Rural')
    if urban == 'Metro':
        inputs['UrbanRuralTier'] = 1.0
    elif urban == 'Urban':
        inputs['UrbanRuralTier'] = 0.7
    elif urban == 'Semi-Urban':
        inputs['UrbanRuralTier'] = 0.4
    else:
        inputs['UrbanRuralTier'] = 0.0
    
    # DigitalLiteracy (0-10 → 0-1)
    inputs['DigitalLiteracy'] = derived.get('digital_literacy_score', 3) / 10.0
    
    # FamilyInfluence (proxy from marital + cultural)
    marital = str(row.get('marital_status', '')).lower()
    if 'married' in marital:
        inputs['FamilyInfluence'] = 0.7
    else:
        inputs['FamilyInfluence'] = 0.3
    
    # AspirationalLevel (0-10 → 0-1)
    inputs['AspirationalLevel'] = derived.get('aspirational_score', 3) / 10.0
    
    # PriceSensitivity (inverse of SEC + aspiration)
    inputs['PriceSensitivity'] = 1.0 - (inputs['SEC'] * 0.6 + inputs['AspirationalLevel'] * 0.4)
    
    # RegionalCulture (proxy from regional cluster)
    region = derived.get('regional_cluster', 'Central')
    # Higher collectivism in East/North, lower in West/South metros
    if region in ['East', 'Northeast']:
        inputs['RegionalCulture'] = 0.8
    elif region in ['North', 'Central']:
        inputs['RegionalCulture'] = 0.6
    elif region == 'West':
        inputs['RegionalCulture'] = 0.4
    else:
        inputs['RegionalCulture'] = 0.5
    
    # InfluencerTrust (proxy from generation + digital)
    gen = derived.get('generation_bucket', 'Gen X')
    if gen == 'Gen Z':
        inputs['InfluencerTrust'] = 0.7
    elif gen == 'Young Millennial':
        inputs['InfluencerTrust'] = 0.6
    else:
        inputs['InfluencerTrust'] = 0.3
    
    # ProfessionalSector
    if any(x in occupation for x in ['tech', 'software', 'engineer', 'it', 'professional']):
        inputs['ProfessionalSector'] = 0.9
    elif any(x in occupation for x in ['teacher', 'government', 'clerk']):
        inputs['ProfessionalSector'] = 0.5
    elif 'farmer' in occupation or 'agricultural' in occupation:
        inputs['ProfessionalSector'] = 0.1
    else:
        inputs['ProfessionalSector'] = 0.4
    
    # EnglishProficiency (0-10 → 0-1)
    inputs['EnglishProficiency'] = derived.get('english_score', 0) / 10.0
    
    # HobbyDiversity (0-10 → 0-1)
    inputs['HobbyDiversity'] = derived.get('openness_score', 3) / 10.0
    
    # CareerAmbition (0-10 → 0-1)
    inputs['CareerAmbition'] = derived.get('aspirational_score', 3) / 10.0
    
    # AgeBucket (0 = 60+, 1 = Gen Z)
    age = row.get('age', 40)
    if age <= 24:
        inputs['AgeBucket'] = 1.0
    elif age <= 32:
        inputs['AgeBucket'] = 0.8
    elif age <= 40:
        inputs['AgeBucket'] = 0.6
    elif age <= 50:
        inputs['AgeBucket'] = 0.4
    elif age <= 60:
        inputs['AgeBucket'] = 0.2
    else:
        inputs['AgeBucket'] = 0.0
    
    # GenderMarital (proxy: 0 = married female, 1 = single male)
    sex = str(row.get('sex', '')).lower()
    if sex == 'male' and 'married' not in marital:
        inputs['GenderMarital'] = 1.0
    elif sex == 'female' and 'married' in marital:
        inputs['GenderMarital'] = 0.0
    else:
        inputs['GenderMarital'] = 0.5
    
    # Clamp all to [0,1]
    for key in inputs:
        inputs[key] = max(0.0, min(1.0, inputs[key]))
    
    return inputs


# ============================================================================
# COMPILED LATENT PRIORS
# ============================================================================

def compile_latent_priors(inputs: Dict) -> Dict:
    """
    Compile normalized inputs into behavioral latent priors.
    
    Returns dict with CC, FR, RT, LAM, ET, TB, DR, CN
    """
    priors = {}
    
    # 1. Cognitive Capacity (CC)
    priors['CC'] = np.clip(
        0.35 * inputs['DigitalLiteracy'] +
        0.25 * inputs['EnglishProficiency'] +
        0.20 * inputs['HobbyDiversity'] +
        0.20 * inputs['AgeBucket'],
        0.2, 0.9
    )
    
    # 2. Cognitive Fatigue Rate (FR)
    priors['FR'] = np.clip(
        1 - (
            0.5 * inputs['DigitalLiteracy'] +
            0.3 * inputs['AgeBucket'] +
            0.2 * inputs['EnglishProficiency']
        ),
        0.1, 0.8
    )
    
    # 3. Risk Tolerance (RT)
    priors['RT'] = np.clip(
        0.4 * inputs['SEC'] +
        0.3 * (1 - inputs['FamilyInfluence']) +
        0.2 * inputs['AspirationalLevel'] +
        0.1 * (1 - inputs['PriceSensitivity']),
        0.1, 0.9
    )
    
    # 4. Loss Aversion Multiplier (LAM)
    priors['LAM'] = np.clip(
        1 + (
            0.6 * inputs['FamilyInfluence'] +
            0.4 * inputs['PriceSensitivity']
        ),
        1.0, 2.5
    )
    
    # 5. Effort Tolerance (ET)
    priors['ET'] = np.clip(
        0.5 * inputs['DigitalLiteracy'] +
        0.3 * inputs['HobbyDiversity'] +
        0.2 * inputs['CareerAmbition'],
        0.2, 0.9
    )
    
    # 6. Trust Baseline (TB)
    priors['TB'] = np.clip(
        0.4 * inputs['UrbanRuralTier'] +
        0.3 * inputs['ProfessionalSector'] +
        0.3 * inputs['InfluencerTrust'],
        0.2, 0.9
    )
    
    # 7. Temporal Discount Rate (DR)
    priors['DR'] = np.clip(
        0.5 * inputs['PriceSensitivity'] +
        0.3 * (1 - inputs['AgeBucket']) +
        0.2 * inputs['AspirationalLevel'],
        0.05, 0.9
    )
    
    # 8. Control Need (CN)
    priors['CN'] = np.clip(
        0.5 * inputs['FamilyInfluence'] +
        0.3 * inputs['RegionalCulture'] +
        0.2 * (1 - inputs['UrbanRuralTier']),
        0.2, 0.9
    )
    
    # 9. Motivation Strength (MS) - from initial intent
    # This is computed separately based on product fit
    priors['MS'] = np.clip(
        inputs['AspirationalLevel'] * 0.6 + 
        inputs['DigitalLiteracy'] * 0.4,
        0.3, 1.0
    )
    
    return priors


# ============================================================================
# INTERNAL STATE MANAGEMENT
# ============================================================================

@dataclass
class InternalState:
    """Internal state variables for one simulation trajectory."""
    cognitive_energy: float
    perceived_risk: float
    perceived_effort: float
    perceived_value: float
    perceived_control: float
    
    def clamp(self, priors: Dict):
        """Clamp all values to valid ranges."""
        self.cognitive_energy = max(0.0, min(priors['CC'], self.cognitive_energy))
        self.perceived_risk = max(0.0, min(3.0, self.perceived_risk))
        self.perceived_effort = max(0.0, min(3.0, self.perceived_effort))
        self.perceived_value = max(0.0, min(3.0, self.perceived_value))
        self.perceived_control = max(0.0, min(2.0, self.perceived_control))


def initialize_state(variant_name: str, priors: Dict) -> InternalState:
    """Initialize state from variant definition."""
    variant = STATE_VARIANTS[variant_name]
    
    state = InternalState(
        cognitive_energy=priors['CC'] * variant['cognitive_energy_mult'],
        perceived_risk=variant['perceived_risk'],
        perceived_effort=variant['perceived_effort'],
        perceived_value=variant['perceived_value'] * priors['MS'],
        perceived_control=variant['perceived_control'] * priors['TB']
    )
    
    state.clamp(priors)
    return state


# ============================================================================
# PERCEPTION TRANSFORMATION (Behavioral Models)
# ============================================================================

def compute_cognitive_cost(
    cognitive_demand: float,
    fatigue_rate: float,
    cognitive_energy: float
) -> float:
    """System 2 fatigue amplification."""
    return cognitive_demand * (1 + fatigue_rate) * (1 - cognitive_energy)


def compute_effort_cost(
    effort_demand: float,
    effort_tolerance: float
) -> float:
    """Fogg Ability model."""
    return effort_demand * (1 - effort_tolerance)


def compute_risk_cost(
    risk_signal: float,
    loss_aversion_mult: float,
    irreversibility: int
) -> float:
    """Prospect Theory loss aversion."""
    return risk_signal * loss_aversion_mult * (1 + irreversibility)


def compute_value_yield(
    explicit_value: float,
    discount_rate: float,
    delay_to_value: float
) -> float:
    """Temporal discounting."""
    return explicit_value * np.exp(-discount_rate * delay_to_value)


def compute_reassurance_yield(
    reassurance_signal: float,
    authority_signal: float,
    control_need: float
) -> float:
    """Control/trust building."""
    return (reassurance_signal + authority_signal) * (1 - control_need)


def compute_transition_cost(
    current_step: Dict,
    previous_step: Optional[Dict],
    priors: Dict,
    state: InternalState
) -> Dict[str, float]:
    """
    Compute transition costs when moving between steps.
    
    Key insight: Moving from a passive step (landing page) to an active step 
    (quiz start) requires commitment, which adds cognitive/effort/risk costs.
    
    Returns dict with transition_cost_breakdown.
    """
    if previous_step is None:
        # First step, no transition cost
        return {
            'transition_cognitive_cost': 0.0,
            'transition_effort_cost': 0.0,
            'transition_risk_cost': 0.0,
            'transition_total_cost': 0.0
        }
    
    # Detect commitment gate: moving from passive (landing) to active (quiz/input)
    # Also check if previous step is a landing page with CTA (commitment gate)
    prev_is_passive = (
        previous_step.get('type') == 'landing' or
        previous_step.get('effort_demand', 0) < 0.3 or
        previous_step.get('cognitive_demand', 0) < 0.3
    )
    
    # Check if previous step is a commitment gate (landing with high effort = CTA)
    prev_is_commitment_gate = (
        previous_step.get('type') == 'landing' and
        previous_step.get('effort_demand', 0) >= 0.7  # High effort = CTA click required
    )
    
    current_is_active = (
        current_step.get('effort_demand', 0) >= 0.3 or
        current_step.get('cognitive_demand', 0) >= 0.3 or
        'quiz' in str(current_step.get('name', '')).lower() or
        'question' in str(current_step.get('name', '')).lower()
    )
    
    is_commitment_gate = (prev_is_passive and current_is_active) or prev_is_commitment_gate
    
    if not is_commitment_gate:
        # No significant transition cost
        return {
            'transition_cognitive_cost': 0.0,
            'transition_effort_cost': 0.0,
            'transition_risk_cost': 0.0,
            'transition_total_cost': 0.0
        }
    
    # Commitment gate detected - compute transition costs
    # The cost of moving from "browsing" to "committing"
    # This is a significant behavioral shift that many users don't make
    
    # 1. Cognitive cost: Decision-making fatigue
    # Higher when user is already low on energy
    # Commitment decisions are cognitively demanding
    transition_cognitive = 0.25 * (1 - state.cognitive_energy) * (1 + priors['FR'])
    
    # 2. Effort cost: The "activation energy" to start
    # Higher for users with lower effort tolerance
    # Clicking a CTA requires overcoming inertia
    transition_effort = 0.30 * (1 - priors['ET'])
    
    # 3. Risk cost: Commitment feels risky (loss of optionality)
    # Higher for loss-averse users
    # Starting a quiz feels like losing the option to leave
    transition_risk = 0.35 * priors['LAM'] * (1 - state.perceived_control)
    
    return {
        'transition_cognitive_cost': transition_cognitive,
        'transition_effort_cost': transition_effort,
        'transition_risk_cost': transition_risk,
        'transition_total_cost': transition_cognitive + transition_effort + transition_risk
    }


# ============================================================================
# STATE UPDATE
# ============================================================================

def update_state(
    state: InternalState,
    step: Dict,
    priors: Dict,
    previous_step: Optional[Dict] = None
) -> Tuple[InternalState, Dict]:
    """
    Update internal state based on product step.
    
    Args:
        state: Current internal state
        step: Current step definition
        priors: Compiled behavioral priors
        previous_step: Previous step definition (for transition cost calculation)
    
    Returns: (updated_state, cost_breakdown)
    """
    # Compute transition costs (commitment gate cost)
    transition_costs = compute_transition_cost(step, previous_step, priors, state)
    
    # Compute step-level costs and yields
    cognitive_cost = compute_cognitive_cost(
        step['cognitive_demand'],
        priors['FR'],
        state.cognitive_energy
    )
    
    effort_cost = compute_effort_cost(
        step['effort_demand'],
        priors['ET']
    )
    
    risk_cost = compute_risk_cost(
        step['risk_signal'],
        priors['LAM'],
        step['irreversibility']
    )
    
    value_yield = compute_value_yield(
        step['explicit_value'],
        priors['DR'],
        step['delay_to_value']
    )
    
    reassurance_yield = compute_reassurance_yield(
        step['reassurance_signal'],
        step['authority_signal'],
        priors['CN']
    )
    
    # Combine step costs with transition costs
    total_cognitive_cost = cognitive_cost + transition_costs['transition_cognitive_cost']
    total_effort_cost = effort_cost + transition_costs['transition_effort_cost']
    total_risk_cost = risk_cost + transition_costs['transition_risk_cost']
    
    # Update state (transition costs apply BEFORE step costs)
    new_state = InternalState(
        cognitive_energy=max(0.0, state.cognitive_energy - total_cognitive_cost),
        perceived_risk=min(3.0, state.perceived_risk + total_risk_cost),
        perceived_effort=min(3.0, state.perceived_effort + total_effort_cost),
        perceived_value=min(3.0, state.perceived_value + value_yield),
        perceived_control=min(2.0, state.perceived_control + reassurance_yield)
    )
    
    new_state.clamp(priors)
    
    # Cost breakdown for failure analysis (include transition costs)
    costs = {
        'cognitive_cost': total_cognitive_cost,
        'effort_cost': total_effort_cost,
        'risk_cost': total_risk_cost,
        'value_yield': value_yield,
        'reassurance_yield': reassurance_yield,
        'value_decay': -value_yield if value_yield < 0 else 0,
        'total_cost': total_cognitive_cost + total_effort_cost + total_risk_cost,
        # Transition cost breakdown (for debugging/analysis)
        'transition_cognitive_cost': transition_costs['transition_cognitive_cost'],
        'transition_effort_cost': transition_costs['transition_effort_cost'],
        'transition_risk_cost': transition_costs['transition_risk_cost'],
        'transition_total_cost': transition_costs['transition_total_cost'],
        'is_commitment_gate': transition_costs['transition_total_cost'] > 0
    }
    
    return new_state, costs


# ============================================================================
# DROP-OFF DECISION
# ============================================================================

def should_continue(state: InternalState, priors: Dict) -> bool:
    """
    Decision rule: CONTINUE if value + control > risk + effort.
    """
    left = (state.perceived_value * priors['MS']) + state.perceived_control
    right = state.perceived_risk + state.perceived_effort
    
    return left > right


def identify_failure_reason(costs: Dict) -> FailureReason:
    """
    Identify dominant failure reason.
    Must exceed 40% of total cost to be primary.
    """
    total = costs['total_cost']
    if total == 0:
        return FailureReason.MULTI_FACTOR
    
    # Check each cost
    cognitive_pct = costs['cognitive_cost'] / total if total > 0 else 0
    effort_pct = costs['effort_cost'] / total if total > 0 else 0
    risk_pct = costs['risk_cost'] / total if total > 0 else 0
    value_pct = abs(costs['value_decay']) / total if total > 0 else 0
    
    # Find dominant
    max_pct = max(cognitive_pct, effort_pct, risk_pct, value_pct)
    
    if max_pct >= 0.4:
        if cognitive_pct == max_pct:
            return FailureReason.SYSTEM2_FATIGUE
        elif effort_pct == max_pct:
            return FailureReason.LOW_ABILITY
        elif risk_pct == max_pct:
            return FailureReason.LOSS_AVERSION
        elif value_pct == max_pct:
            return FailureReason.TEMPORAL_DISCOUNTING
    
    return FailureReason.MULTI_FACTOR


# ============================================================================
# SINGLE PERSONA SIMULATION (Multiple State Variants)
# ============================================================================

def simulate_persona_trajectories(
    row: pd.Series,
    derived: Dict,
    variant_names: Optional[List[str]] = None,
    product_steps: Optional[Dict] = None
) -> List[Dict]:
    """
    Simulate one persona across multiple state variants.
    
    Returns list of trajectory results.
    """
    if variant_names is None:
        variant_names = list(STATE_VARIANTS.keys())
    
    # Normalize inputs
    inputs = normalize_persona_inputs(row, derived)
    
    # Compile priors
    priors = compile_latent_priors(inputs)
    
    # Use custom product steps if provided, else default
    steps_to_use = product_steps if product_steps else PRODUCT_STEPS
    
    # Simulate each variant
    trajectories = []
    
    for variant_name in variant_names:
        # Initialize state
        state = initialize_state(variant_name, priors)
        
        # Track journey
        journey = []
        exit_step = None
        failure_reason = None
        
        # Step through product flow
        previous_step = None
        for step_name, step_def in steps_to_use.items():
            # Update state (with transition cost from previous step)
            state, costs = update_state(state, step_def, priors, previous_step=previous_step)
            
            # Record step
            journey.append({
                'step': step_name,
                'cognitive_energy': state.cognitive_energy,
                'perceived_risk': state.perceived_risk,
                'perceived_effort': state.perceived_effort,
                'perceived_value': state.perceived_value,
                'perceived_control': state.perceived_control,
                'costs': costs
            })
            
            # Check continuation
            if not should_continue(state, priors):
                exit_step = step_name
                failure_reason = identify_failure_reason(costs)
                break
            
            # Update previous step for next iteration
            previous_step = step_def
        
        # If completed all steps
        if exit_step is None:
            exit_step = "Completed"
            failure_reason = None
        
        trajectories.append({
            'variant': variant_name,
            'variant_desc': STATE_VARIANTS[variant_name]['description'],
            'priors': priors,
            'journey': journey,
            'exit_step': exit_step,
            'failure_reason': failure_reason.value if failure_reason else None,
            'final_state': {
                'cognitive_energy': state.cognitive_energy,
                'perceived_risk': state.perceived_risk,
                'perceived_effort': state.perceived_effort,
                'perceived_value': state.perceived_value,
                'perceived_control': state.perceived_control
            }
        })
    
    return trajectories


# ============================================================================
# BATCH SIMULATION
# ============================================================================

def run_behavioral_simulation(
    df: pd.DataFrame,
    verbose: bool = True,
    product_steps: Optional[Dict] = None
) -> pd.DataFrame:
    """
    Run behavioral simulation on all personas.
    
    For each persona, simulates multiple state variants.
    """
    if verbose:
        print("🧠 Running Behavioral State-Based Simulation")
        print(f"   Personas: {len(df)}")
        print(f"   State variants per persona: {len(STATE_VARIANTS)}")
        print(f"   Total trajectories: {len(df) * len(STATE_VARIANTS)}")
    
    # Derived feature columns
    derived_cols = [
        'urban_rural', 'regional_cluster',
        'digital_literacy_score', 'aspirational_score',
        'english_score', 'openness_score',
        'trust_score', 'status_quo_score',
        'debt_aversion_score', 'cc_relevance_score',
        'generation_bucket'
    ]
    
    all_results = []
    
    for idx, row in df.iterrows():
        # Extract derived features
        derived = {col: row[col] for col in derived_cols if col in row.index}
        
        # Simulate trajectories
        trajectories = simulate_persona_trajectories(row, derived, product_steps=product_steps)
        
        # Aggregate across variants for this persona
        exit_steps = [t['exit_step'] for t in trajectories]
        failure_reasons = [t['failure_reason'] for t in trajectories if t['failure_reason']]
        
        # Most common exit step
        exit_counter = Counter(exit_steps)
        dominant_exit = exit_counter.most_common(1)[0][0]
        
        # Most common failure reason
        if failure_reasons:
            reason_counter = Counter(failure_reasons)
            dominant_reason = reason_counter.most_common(1)[0][0]
        else:
            dominant_reason = None
        
        # Consistency score (how many variants fail at same step)
        consistency = exit_counter.most_common(1)[0][1] / len(trajectories)
        
        # Average final state
        avg_final = {
            'cognitive_energy': np.mean([t['final_state']['cognitive_energy'] for t in trajectories]),
            'perceived_risk': np.mean([t['final_state']['perceived_risk'] for t in trajectories]),
            'perceived_effort': np.mean([t['final_state']['perceived_effort'] for t in trajectories]),
            'perceived_value': np.mean([t['final_state']['perceived_value'] for t in trajectories]),
            'perceived_control': np.mean([t['final_state']['perceived_control'] for t in trajectories])
        }
        
        all_results.append({
            'dominant_exit_step': dominant_exit,
            'dominant_failure_reason': dominant_reason,
            'consistency_score': consistency,
            'variants_completed': sum(1 for t in trajectories if t['exit_step'] == 'Completed'),
            'variants_total': len(trajectories),
            'avg_final_cognitive_energy': avg_final['cognitive_energy'],
            'avg_final_perceived_value': avg_final['perceived_value'],
            'avg_final_perceived_risk': avg_final['perceived_risk'],
            'trajectories': trajectories  # Store full trajectories
        })
        
        if verbose and (idx + 1) % 50 == 0:
            print(f"   Simulated {idx + 1}/{len(df)} personas")
    
    # Merge results
    results_df = pd.DataFrame(all_results)
    final_df = pd.concat([df.reset_index(drop=True), results_df], axis=1)
    
    if verbose:
        print(f"\n✅ Behavioral simulation complete!")
        print(f"   Avg consistency: {results_df['consistency_score'].mean():.2f}")
        print(f"   Avg variants completed: {results_df['variants_completed'].mean():.1f}/{len(STATE_VARIANTS)}")
    
    return final_df


# ============================================================================
# AGGREGATION (Failure Mode Analysis)
# ============================================================================

def aggregate_failure_modes(df: pd.DataFrame, product_steps: Optional[Dict] = None) -> pd.DataFrame:
    """
    Aggregate to show failure rates and reasons per step.
    
    This answers "WHY they dropped at step t" before "WHO".
    """
    steps_to_use = product_steps if product_steps else PRODUCT_STEPS
    
    step_failures = {}
    
    for step_name in steps_to_use.keys():
        step_failures[step_name] = {
            'total_failures': 0,
            'failure_reasons': Counter(),
            'personas': []
        }
    
    # Collect failures from all trajectories
    for _, row in df.iterrows():
        trajectories = row.get('trajectories', [])
        for traj in trajectories:
            if traj['exit_step'] != 'Completed':
                step = traj['exit_step']
                if step in step_failures:
                    step_failures[step]['total_failures'] += 1
                    if traj['failure_reason']:
                        step_failures[step]['failure_reasons'][traj['failure_reason']] += 1
                    step_failures[step]['personas'].append(row.name)
    
    # Build summary table
    summary = []
    total_trajectories = len(df) * len(STATE_VARIANTS)
    
    for step_name in PRODUCT_STEPS.keys():
        failures = step_failures[step_name]
        failure_rate = failures['total_failures'] / total_trajectories * 100
        
        # Primary and secondary reasons
        reasons = failures['failure_reasons']
        if reasons:
            primary = reasons.most_common(1)[0]
            secondary = reasons.most_common(2)[1] if len(reasons) > 1 else None
        else:
            primary = (None, 0)
            secondary = None
        
        summary.append({
            'Step': step_name,
            'Failure Rate %': round(failure_rate, 1),
            'Total Failures': failures['total_failures'],
            'Primary Reason': primary[0] if primary[0] else 'None',
            'Primary Count': primary[1],
            'Secondary Reason': secondary[0] if secondary else 'None',
            'Secondary Count': secondary[1] if secondary else 0
        })
    
    return pd.DataFrame(summary)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("\n🧪 Testing Behavioral Engine...\n")
    
    try:
        from load_dataset import load_and_sample
        from derive_features import derive_all_features
        
        # Load small sample
        df, _ = load_and_sample(n=10, seed=42, verbose=False)
        df = derive_all_features(df, verbose=False)
        
        # Run simulation
        result_df = run_behavioral_simulation(df, verbose=True)
        
        # Aggregate failure modes
        print("\n" + "=" * 80)
        print("📊 FAILURE MODE ANALYSIS (WHY before WHO)")
        print("=" * 80)
        
        failure_modes = aggregate_failure_modes(result_df)
        print(failure_modes.to_string(index=False))
        
        print("\n✅ Test complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


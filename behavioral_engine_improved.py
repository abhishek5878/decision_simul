"""
behavioral_engine_improved.py - Realistic Behavioral Simulation Engine

Improvements over original:
1. Probabilistic continuation decisions (not binary)
2. Cognitive energy can recover (value, progress, reassurance)
3. Value can override fatigue
4. Commitment effect (sunk cost increases persistence)
5. Heterogeneous user behavior (archetype modifiers)
6. Bounded randomness (individual variance)
7. Minimum persistence (prevents total collapse)

Maintains behavioral science grounding while adding realism.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from collections import Counter

# Import original functions we'll reuse
from behavioral_engine import (
    FailureReason,
    STATE_VARIANTS,
    normalize_persona_inputs,
    compile_latent_priors,
    InternalState,
    initialize_state,
    compute_effort_cost,
    compute_risk_cost,
    compute_value_yield,
    compute_reassurance_yield,
    identify_failure_reason
)


# ============================================================================
# IMPROVED COGNITIVE COST (No Death Spiral)
# ============================================================================

def compute_cognitive_cost_improved(
    cognitive_demand: float,
    fatigue_rate: float,
    cognitive_energy: float,
    value_override: float = 0.0
) -> float:
    """
    Cognitive cost that doesn't create death spiral.
    
    Improvements:
    - Uses sqrt to prevent explosion when energy is low
    - Value can reduce effective cognitive cost
    - Maximum cap prevents infinite cost
    """
    # Base cost scales with demand and fatigue (reduced amplification)
    # Made less harsh: reduced from 0.5 to 0.3
    base_cost = cognitive_demand * (1 + fatigue_rate * 0.3)
    
    # Energy penalty: Lower energy increases cost, but with diminishing returns
    # Use sqrt to prevent explosion (not linear)
    # Made less harsh: reduced from 0.5 to 0.3
    energy_penalty = np.sqrt(max(0, 1 - cognitive_energy)) * 0.3
    
    # Value override: High value reduces effective cognitive cost
    # Users can "push through" if value is high
    # Made stronger: increased from 30% to 50% reduction
    value_reduction = value_override * 0.5  # Up to 50% cost reduction
    
    # Progress-based value boost: As users progress, value becomes more effective at reducing cost
    # This compensates for the fact that value amplification happens after cost calculation
    # We approximate progress by checking if value is high (which suggests progress)
    if value_override > 0.5:  # High value suggests progress
        progress_value_boost = (value_override - 0.5) * 0.4  # Additional 20% reduction
        value_reduction += progress_value_boost
    
    total_cost = base_cost * (1 + energy_penalty) - value_reduction
    
    # Cap maximum cost to prevent explosion
    # Made less harsh: reduced from 80% to 60%
    max_cost = 0.6  # Never exceed 60% of current energy
    total_cost = min(total_cost, max_cost)
    
    return max(0, total_cost)


# ============================================================================
# COGNITIVE ENERGY RECOVERY
# ============================================================================

def update_cognitive_energy_with_recovery(
    current_energy: float,
    cognitive_cost: float,
    value_yield: float,
    reassurance_yield: float,
    progress: float,  # 0 to 1
    priors: Dict
) -> float:
    """
    Energy decreases with cost, but can recover with value/reassurance/progress.
    
    Recovery mechanisms:
    - Value boost: Seeing value restores motivation
    - Progress boost: Making progress feels good
    - Reassurance boost: Trust reduces stress
    """
    # 1. BASE DEPLETION: Apply cognitive cost
    new_energy = current_energy - cognitive_cost
    
    # 2. RECOVERY MECHANISMS:
    # a) Value boost: Seeing value restores motivation
    if value_yield > 0.05:  # Lower threshold - any positive value helps
        value_recovery = value_yield * 0.25  # 25% of value converts to energy
        new_energy += value_recovery
    
    # b) Progress boost: Making progress feels good
    if progress > 0.2:  # Past 20% completion (lower threshold)
        progress_boost = progress * 0.15  # Up to 15% energy recovery
        new_energy += progress_boost
    
    # c) Reassurance boost: Trust reduces stress
    if reassurance_yield > 0.1:  # Lower threshold
        reassurance_recovery = reassurance_yield * 0.20  # 20% recovery
        new_energy += reassurance_recovery
    
    # 3. FLOOR: Energy never goes below a minimum (users can push through)
    min_energy = 0.05  # 5% minimum, not zero
    new_energy = max(min_energy, new_energy)
    
    # 4. CEILING: Energy can't exceed cognitive capacity
    max_energy = priors['CC']
    new_energy = min(max_energy, new_energy)
    
    return new_energy


# ============================================================================
# ARCHETYPE MODIFIERS (Heterogeneous Behavior)
# ============================================================================

def compute_archetype_modifiers(priors: Dict, persona_inputs: Dict) -> Dict:
    """
    Compute archetype-specific modifiers that create behavioral diversity.
    
    Different user archetypes have different:
    - Base persistence (some users are more "sticky")
    - Value sensitivity (some care more about value)
    - Fatigue resilience (some are more resilient)
    - Risk tolerance variance
    """
    modifiers = {
        'base_persistence': 1.0,  # Multiplier for continuation probability
        'value_sensitivity': 1.0,   # How much value affects decisions
        'fatigue_resilience': 1.0,  # How well they handle fatigue
        'risk_tolerance_mult': 1.0  # Risk perception multiplier
    }
    
    # High digital literacy → more resilient to fatigue
    if persona_inputs.get('DigitalLiteracy', 0.5) > 0.7:
        modifiers['fatigue_resilience'] = 1.3  # 30% more resilient
        modifiers['base_persistence'] = 1.2     # 20% more persistent
    
    # High aspiration → more value-sensitive
    if persona_inputs.get('AspirationalLevel', 0.5) > 0.7:
        modifiers['value_sensitivity'] = 1.4   # 40% more value-sensitive
    
    # High SEC → more risk-tolerant
    if persona_inputs.get('SEC', 0.5) > 0.7:
        modifiers['risk_tolerance_mult'] = 0.8  # 20% less risk-averse
    
    # Family influence → more cautious (lower persistence)
    if persona_inputs.get('FamilyInfluence', 0.5) > 0.7:
        modifiers['base_persistence'] = 0.85    # 15% less persistent
    
    # Age: Younger users more resilient
    if persona_inputs.get('AgeBucket', 0.5) > 0.7:
        modifiers['fatigue_resilience'] *= 1.15
    
    return modifiers


# ============================================================================
# PROBABILISTIC CONTINUATION DECISION
# ============================================================================

def should_continue_probabilistic(
    state: InternalState,
    priors: Dict,
    step_index: int,
    total_steps: int,
    modifiers: Optional[Dict] = None
) -> float:
    """
    Compute continuation probability (0 to 1), not binary decision.
    
    Improvements:
    - Probabilistic, not deterministic
    - Value can override fatigue
    - Commitment effect (sunk cost increases persistence)
    - Individual variance (bounded randomness)
    - Minimum persistence (prevents total collapse)
    """
    if modifiers is None:
        modifiers = {'base_persistence': 1.0, 'value_sensitivity': 1.0, 
                     'fatigue_resilience': 1.0, 'risk_tolerance_mult': 1.0}
    
    # Base decision strength (current model)
    left = (state.perceived_value * priors['MS']) + state.perceived_control
    right = state.perceived_risk + state.perceived_effort
    base_advantage = left - right  # Can be negative
    
    # 1. VALUE OVERRIDE: High value can overcome fatigue
    value_override = 0.0
    if state.perceived_value > 0.7:  # High value threshold
        # Value reduces effective fatigue cost
        value_override = state.perceived_value * 0.3  # Bonus for high value
    
    # 2. COMMITMENT EFFECT: Sunk cost increases persistence
    # Stronger effect - progress creates momentum
    progress = step_index / total_steps if total_steps > 0 else 0  # 0 to 1
    commitment_boost = progress * 0.8  # Up to 80% boost at end (was 40%)
    
    # Early progress bonus: Getting past first 20% creates momentum
    if progress > 0.2:
        early_progress_bonus = (progress - 0.2) * 0.5  # Additional 40% boost
        commitment_boost += early_progress_bonus
    
    # 3. COGNITIVE RECOVERY: Low energy doesn't mean instant death
    # Users can push through with willpower if value is high
    energy_factor = state.cognitive_energy
    if state.cognitive_energy < 0.2 and state.perceived_value > 0.6:
        # Willpower override: high value allows pushing through low energy
        energy_factor = 0.3  # Minimum floor, not zero
    
    # Adjusted advantage
    adjusted_advantage = base_advantage + value_override + commitment_boost
    
    # 4. PROBABILISTIC MAPPING: Convert advantage to probability
    # Use sigmoid to map advantage to [0, 1] probability
    # Steepness controls how deterministic vs. probabilistic
    # Less steep = more probabilistic, more forgiving
    steepness = 1.2  # Reduced from 1.5 to 1.2 (more forgiving, less deterministic)
    base_prob = 1 / (1 + np.exp(-steepness * adjusted_advantage))
    
    # Progress-based probability boost: As users progress, they become more likely to continue
    # This is separate from value amplification - it's about momentum
    progress_prob_boost = progress * 0.20  # Increased from 0.15 to 0.20 (up to 20% boost)
    base_prob += progress_prob_boost
    
    # 5. APPLY ARCHETYPE MODIFIERS
    adjusted_prob = base_prob * modifiers['base_persistence']
    
    # Value sensitivity: High value has more impact for value-sensitive users
    if state.perceived_value > 0.6:
        value_bonus = (state.perceived_value - 0.6) * 0.2 * modifiers['value_sensitivity']
        adjusted_prob += value_bonus
    
    # Fatigue resilience: Fatigue has less impact for resilient users
    if state.cognitive_energy < 0.3:
        fatigue_penalty = (0.3 - state.cognitive_energy) * 0.15
        fatigue_penalty *= (2.0 - modifiers['fatigue_resilience'])  # Less penalty if resilient
        adjusted_prob -= fatigue_penalty
    
    # 6. BASE COMPLETION BIAS: Users are more persistent than assumed
    # This reflects real-world stickiness
    # Maximum aggressive increase to prevent collapse
    BASE_COMPLETION_PROB = 0.60  # Increased to 0.60 (60% base)
    adjusted_prob = max(BASE_COMPLETION_PROB, adjusted_prob)
    
    # 7. PERSISTENCE BIAS: People continue even when unsure
    # Human stickiness increases with progress
    persistence_bonus = 0.18 + 0.22 * progress  # 18% at start, up to 40% at end
    adjusted_prob += persistence_bonus
    
    # Ensure we don't exceed 95% (cap)
    adjusted_prob = min(adjusted_prob, 0.95)
    
    # 8. INDIVIDUAL VARIANCE: Add bounded randomness
    # Different users have different "stickiness" even with same priors
    # Note: This will be applied in the calling function with a seed
    # For now, we return the base probability
    
    return np.clip(adjusted_prob, 0.05, 0.95)


# ============================================================================
# IMPROVED FAILURE REASON IDENTIFICATION
# ============================================================================

def identify_failure_reason_improved(costs: Dict, state: Optional[InternalState] = None) -> FailureReason:
    """
    Improved failure reason identification that considers relative magnitudes
    and state, not just cost percentages.
    """
    total = costs['total_cost']
    if total == 0:
        return FailureReason.MULTI_FACTOR
    
    # Get absolute costs
    cognitive_cost = costs.get('cognitive_cost', 0)
    effort_cost = costs.get('effort_cost', 0)
    risk_cost = costs.get('risk_cost', 0)
    value_decay = abs(costs.get('value_decay', 0))
    
    # Consider state if provided
    if state:
        # If cognitive energy is very low, fatigue is more likely
        if state.cognitive_energy < 0.1:
            cognitive_cost *= 1.2  # Boost cognitive cost weight
        
        # If perceived effort is very high, effort is more likely
        if state.perceived_effort > 1.5:
            effort_cost *= 1.2
        
        # If perceived risk is very high, risk is more likely
        if state.perceived_risk > 1.5:
            risk_cost *= 1.2
    
    # Normalize to percentages
    adjusted_total = cognitive_cost + effort_cost + risk_cost + value_decay
    if adjusted_total == 0:
        return FailureReason.MULTI_FACTOR
    
    cognitive_pct = cognitive_cost / adjusted_total
    effort_pct = effort_cost / adjusted_total
    risk_pct = risk_cost / adjusted_total
    value_pct = value_decay / adjusted_total
    
    # Find dominant (lower threshold for more diversity)
    max_pct = max(cognitive_pct, effort_pct, risk_pct, value_pct)
    
    # Lower threshold (30% instead of 40%) for more diversity
    if max_pct >= 0.3:
        if cognitive_pct == max_pct:
            return FailureReason.SYSTEM2_FATIGUE
        elif effort_pct == max_pct:
            return FailureReason.LOW_ABILITY
        elif risk_pct == max_pct:
            return FailureReason.LOSS_AVERSION
        elif value_pct == max_pct:
            return FailureReason.TEMPORAL_DISCOUNTING
    
    return FailureReason.MULTI_FACTOR


def should_continue_improved(
    state: InternalState,
    priors: Dict,
    step_index: int,
    total_steps: int,
    modifiers: Optional[Dict] = None,
    seed: Optional[int] = None
) -> bool:
    """
    Probabilistic decision: sample from continuation probability.
    
    Returns True if user continues, False if they drop.
    """
    if seed is not None:
        np.random.seed(seed)
    
    prob = should_continue_probabilistic(state, priors, step_index, total_steps, modifiers)
    
    # Add individual variance (bounded randomness)
    personality_noise = np.random.normal(0, 0.15)  # ±15% variance
    final_prob = np.clip(prob + personality_noise, 0.05, 0.95)
    
    return np.random.random() < final_prob


# ============================================================================
# IMPROVED STATE UPDATE
# ============================================================================

def compute_progressive_value_amplification(
    base_value: float,
    step_index: int,
    total_steps: int,
    priors: Dict
) -> float:
    """
    Amplify perceived value based on progress (goal proximity effect).
    
    As users get closer to the goal:
    - Value becomes more tangible (goal proximity)
    - Sunk cost makes remaining value more attractive
    - Progress feedback is motivating
    
    This is the missing piece that makes simulation less harsh.
    """
    if total_steps <= 0:
        return base_value
    
    # Progress: 0 (start) to 1 (end)
    progress = step_index / total_steps if total_steps > 0 else 0
    
    # Goal proximity amplification: Value increases as you get closer
    # At 0% progress: 1.0x (no amplification)
    # At 25% progress: 1.25x (25% boost) - early progress matters
    # At 50% progress: 1.5x (50% boost)
    # At 75% progress: 1.75x (75% boost)
    # At 100% progress: 2.0x (100% boost - value is realized)
    proximity_multiplier = 1.0 + (progress * 1.0)  # Linear: 1.0 to 2.0
    
    # Sunk cost effect: The more you've invested, the more valuable remaining value feels
    # This makes users more persistent as they progress
    # Stronger effect: up to 50% boost (was 30%)
    sunk_cost_multiplier = 1.0 + (progress * 0.5)  # Up to 50% additional boost
    
    # Motivation sensitivity: Some users are more motivated by progress
    motivation_factor = 1.0 + (priors.get('MS', 0.5) * 0.3)  # Up to 30% more sensitive (was 20%)
    
    # Progress momentum: Early progress creates momentum
    # If past 20% completion, add momentum boost
    momentum_boost = 1.0
    if progress > 0.2:
        momentum_boost = 1.0 + ((progress - 0.2) * 0.4)  # Up to 32% momentum boost
    
    # Combined amplification
    total_multiplier = proximity_multiplier * sunk_cost_multiplier * motivation_factor * momentum_boost
    
    # Apply amplification (but don't exceed max value of 3.0)
    amplified_value = min(3.0, base_value * total_multiplier)
    
    return amplified_value


def update_state_improved(
    state: InternalState,
    step: Dict,
    priors: Dict,
    step_index: int,
    total_steps: int,
    previous_step: Optional[Dict] = None
) -> Tuple[InternalState, Dict]:
    """
    Update internal state with improved cognitive cost and energy recovery.
    
    Improvements:
    - Cognitive cost doesn't create death spiral
    - Energy can recover with value/progress/reassurance
    - Value can reduce cognitive cost
    """
    # Compute transition costs (from original, unchanged)
    from behavioral_engine import compute_transition_cost
    transition_costs = compute_transition_cost(step, previous_step, priors, state)
    
    # Compute step-level costs and yields
    # IMPROVED: Cognitive cost with value override
    cognitive_cost = compute_cognitive_cost_improved(
        step['cognitive_demand'],
        priors['FR'],
        state.cognitive_energy,
        state.perceived_value  # Value override
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
    
    # IMPROVED: Less harsh temporal discounting
    # Original: value_yield = explicit_value * exp(-DR * delay)
    # This is too harsh - exponential decay kills value for early steps
    # New: Use square root of delay to make discounting less harsh
    base_value_yield = compute_value_yield(
        step['explicit_value'],
        priors['DR'],
        step['delay_to_value']
    )
    
    # Progressive discounting: Early steps get less discount (users are optimistic)
    # As they progress, discounting becomes more realistic
    progress = step_index / total_steps if total_steps > 0 else 0
    discount_factor = 1.0 - (progress * 0.3)  # 0% discount at start, 30% at end
    value_yield = base_value_yield * (1.0 + discount_factor * 0.5)  # Up to 50% boost for early steps
    
    # Minimum value floor: Even with heavy discounting, users see some value
    min_value_floor = step['explicit_value'] * 0.2  # At least 20% of explicit value
    value_yield = max(value_yield, min_value_floor)
    
    reassurance_yield = compute_reassurance_yield(
        step['reassurance_signal'],
        step['authority_signal'],
        priors['CN']
    )
    
    # Combine step costs with transition costs
    total_cognitive_cost = cognitive_cost + transition_costs['transition_cognitive_cost']
    total_effort_cost = effort_cost + transition_costs['transition_effort_cost']
    total_risk_cost = risk_cost + transition_costs['transition_risk_cost']
    
    # IMPROVED: Update cognitive energy with recovery
    progress = (step_index + 1) / total_steps if total_steps > 0 else 0
    
    new_cognitive_energy = update_cognitive_energy_with_recovery(
        state.cognitive_energy,
        total_cognitive_cost,
        value_yield,
        reassurance_yield,
        progress,
        priors
    )
    
    # PROGRESSIVE VALUE AMPLIFICATION: The missing piece!
    # As users progress, accumulated value becomes more attractive
    # This makes the simulation less harsh and more realistic
    base_perceived_value = state.perceived_value + value_yield
    amplified_perceived_value = compute_progressive_value_amplification(
        base_perceived_value,
        step_index,
        total_steps,
        priors
    )
    
    # Update other state variables
    new_state = InternalState(
        cognitive_energy=new_cognitive_energy,
        perceived_risk=min(3.0, state.perceived_risk + total_risk_cost),
        perceived_effort=min(3.0, state.perceived_effort + total_effort_cost),
        perceived_value=min(3.0, amplified_perceived_value),  # Use amplified value
        perceived_control=min(2.0, state.perceived_control + reassurance_yield)
    )
    
    new_state.clamp(priors)
    
    # Cost breakdown
    costs = {
        'cognitive_cost': total_cognitive_cost,
        'effort_cost': total_effort_cost,
        'risk_cost': total_risk_cost,
        'value_yield': value_yield,
        'reassurance_yield': reassurance_yield,
        'value_decay': -value_yield if value_yield < 0 else 0,
        'total_cost': total_cognitive_cost + total_effort_cost + total_risk_cost,
        'transition_cognitive_cost': transition_costs['transition_cognitive_cost'],
        'transition_effort_cost': transition_costs['transition_effort_cost'],
        'transition_risk_cost': transition_costs['transition_risk_cost'],
        'transition_total_cost': transition_costs['transition_total_cost'],
        'is_commitment_gate': transition_costs['transition_total_cost'] > 0
    }
    
    return new_state, costs


# ============================================================================
# IMPROVED PERSONA SIMULATION
# ============================================================================

def simulate_persona_trajectories_improved(
    row: pd.Series,
    derived: Dict,
    variant_names: Optional[List[str]] = None,
    product_steps: Optional[Dict] = None,
    seed: Optional[int] = None
) -> List[Dict]:
    """
    Simulate one persona across multiple state variants with improved model.
    
    Improvements:
    - Probabilistic continuation decisions
    - Energy recovery mechanisms
    - Value override for fatigue
    - Commitment effect
    - Heterogeneous behavior
    """
    if variant_names is None:
        variant_names = list(STATE_VARIANTS.keys())
    
    if seed is not None:
        np.random.seed(seed)
    
    # Normalize inputs
    inputs = normalize_persona_inputs(row, derived)
    
    # Compile priors
    priors = compile_latent_priors(inputs)
    
    # Compute archetype modifiers (NEW)
    modifiers = compute_archetype_modifiers(priors, inputs)
    
    # Use custom product steps if provided, else default
    from behavioral_engine import PRODUCT_STEPS
    steps_to_use = product_steps if product_steps else PRODUCT_STEPS
    
    # Simulate each variant
    trajectories = []
    total_steps = len(steps_to_use)
    
    for variant_idx, variant_name in enumerate(variant_names):
        # Use variant index to create unique seed for each variant
        variant_seed = (seed + variant_idx * 1000) if seed is not None else None
        
        # Initialize state
        state = initialize_state(variant_name, priors)
        
        # Track journey
        journey = []
        exit_step = None
        failure_reason = None
        
        # Step through product flow
        previous_step = None
        for step_index, (step_name, step_def) in enumerate(steps_to_use.items()):
            # Update state (IMPROVED: with recovery and better cognitive cost)
            state, costs = update_state_improved(
                state, step_def, priors, step_index, total_steps, previous_step=previous_step
            )
            
            # Record step
            journey.append({
                'step': step_name,
                'cognitive_energy': state.cognitive_energy,
                'perceived_risk': state.perceived_risk,
                'perceived_effort': state.perceived_effort,
                'perceived_value': state.perceived_value,
                'perceived_control': state.perceived_control,
                'costs': costs,
                'continue': "True"  # Will be updated below
            })
            
            # IMPROVED: Probabilistic continuation decision
            if not should_continue_improved(
                state, priors, step_index, total_steps, modifiers, seed=variant_seed
            ):
                exit_step = step_name
                failure_reason = identify_failure_reason_improved(costs, state)
                journey[-1]['continue'] = "False"
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
            'modifiers': modifiers,  # NEW: Include modifiers
            'journey': journey,
            'exit_step': exit_step,
            'failure_reason': failure_reason.value if failure_reason else None,
            'completed': exit_step == "Completed",
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
# BATCH SIMULATION (Improved)
# ============================================================================

def run_behavioral_simulation_improved(
    df: pd.DataFrame,
    verbose: bool = True,
    product_steps: Optional[Dict] = None,
    seed: int = 42
) -> pd.DataFrame:
    """
    Run improved behavioral simulation on all personas.
    
    Improvements:
    - Probabilistic decisions
    - Energy recovery
    - Value override
    - Heterogeneous behavior
    """
    if verbose:
        print("🧠 Running Improved Behavioral Simulation")
        print(f"   Personas: {len(df)}")
        print(f"   State variants per persona: {len(STATE_VARIANTS)}")
        print(f"   Total trajectories: {len(df) * len(STATE_VARIANTS)}")
        print(f"   Seed: {seed} (for reproducibility)")
    
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
        
        # Simulate trajectories (IMPROVED)
        persona_seed = seed + idx * 10000  # Unique seed per persona
        trajectories = simulate_persona_trajectories_improved(
            row, derived, product_steps=product_steps, seed=persona_seed
        )
        
        # Aggregate across variants for this persona
        exit_steps = [t['exit_step'] for t in trajectories]
        failure_reasons = [t['failure_reason'] for t in trajectories if t['failure_reason']]
        completed_count = sum(1 for t in trajectories if t['completed'])
        
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
            'variants_completed': completed_count,
            'variants_total': len(trajectories),
            'completion_rate': completed_count / len(trajectories),  # NEW
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
        print(f"\n✅ Improved behavioral simulation complete!")
        print(f"   Avg consistency: {results_df['consistency_score'].mean():.2f}")
        print(f"   Avg variants completed: {results_df['variants_completed'].mean():.1f}/{len(STATE_VARIANTS)}")
        print(f"   Overall completion rate: {results_df['completion_rate'].mean():.1%}")
        print(f"   Completion rate range: {results_df['completion_rate'].min():.1%} - {results_df['completion_rate'].max():.1%}")
    
    return final_df


# ============================================================================
# MAIN EXECUTION (Testing)
# ============================================================================

if __name__ == "__main__":
    print("\n🧪 Testing Improved Behavioral Engine...\n")
    
    try:
        from load_dataset import load_and_sample
        from derive_features import derive_all_features
        
        # Load small sample
        df, _ = load_and_sample(n=10, seed=42, verbose=False)
        df = derive_all_features(df, verbose=False)
        
        # Run improved simulation
        result_df = run_behavioral_simulation_improved(df, verbose=True, seed=42)
        
        # Show completion rates
        print("\n" + "=" * 80)
        print("📊 COMPLETION RATE ANALYSIS")
        print("=" * 80)
        print(f"Overall completion rate: {result_df['completion_rate'].mean():.1%}")
        print(f"Completion rate by persona:")
        for idx, row in result_df.iterrows():
            print(f"  Persona {idx}: {row['completion_rate']:.1%} ({row['variants_completed']}/{row['variants_total']} variants)")
        
        print("\n✅ Test complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


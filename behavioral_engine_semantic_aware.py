"""
behavioral_engine_semantic_aware.py - Semantic-Aware Behavioral Simulation

Integrates step semantic inference into the behavioral simulation pipeline.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from collections import Counter

# Import improved behavioral engine
from behavioral_engine_improved import (
    run_behavioral_simulation_improved,
    simulate_persona_trajectories_improved,
    should_continue_probabilistic,
    update_state_improved,
    InternalState,
    FailureReason
)

# Import intent-aware layer
from behavioral_engine_intent_aware import (
    run_intent_aware_simulation,
    simulate_persona_trajectory_intent_aware
)

# Import semantic layer
from step_semantics import StepSemanticExtractor, StepSemanticProfile
from step_semantics.schema import IntentAlignmentResult


def simulate_persona_trajectory_semantic_aware(
    row: pd.Series,
    derived: Dict,
    variant_name: str,
    product_steps: Dict,
    intent_distribution: Dict[str, float],
    semantic_extractor: StepSemanticExtractor,
    seed: Optional[int] = None
) -> Dict:
    """
    Simulate one persona trajectory with semantic awareness.
    
    For each step:
    1. Extract semantic profile
    2. Analyze intent alignment
    3. Adjust continuation probability based on semantic factors
    4. Record semantic information in journey
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Sample intent from distribution
    intent_ids = list(intent_distribution.keys())
    intent_probs = list(intent_distribution.values())
    sampled_intent_id = np.random.choice(intent_ids, p=intent_probs)
    
    # Import base functions
    from behavioral_engine import (
        normalize_persona_inputs,
        compile_latent_priors,
        initialize_state
    )
    from behavioral_engine_improved import (
        compute_archetype_modifiers
    )
    
    inputs = normalize_persona_inputs(row, derived)
    priors = compile_latent_priors(inputs)
    modifiers = compute_archetype_modifiers(priors, inputs)
    
    state = initialize_state(variant_name, priors)
    journey = []
    exit_step = None
    failure_reason = None
    semantic_mismatches = []
    
    total_steps = len(product_steps)
    previous_step = None
    
    # Infer persona knowledge level from priors
    persona_knowledge = "medium"  # Default
    if priors.get('Cognitive Capacity', 0.5) > 0.7:
        persona_knowledge = "high"
    elif priors.get('Cognitive Capacity', 0.5) < 0.3:
        persona_knowledge = "low"
    
    for step_index, (step_name, step_def) in enumerate(product_steps.items()):
        # Extract semantic profile
        semantic_profile = semantic_extractor.extract(step_def)
        
        # Analyze intent alignment
        user_intent = {sampled_intent_id: 1.0}  # Single intent for this trajectory
        alignment_result = semantic_extractor.analyze_intent_alignment(
            semantic_profile,
            user_intent,
            persona_knowledge
        )
        
        # Update state (from improved engine)
        state, costs = update_state_improved(
            state, step_def, priors, step_index, total_steps, previous_step=previous_step
        )
        
        # Compute base continuation probability
        base_prob = should_continue_probabilistic(
            state, priors, step_index, total_steps, modifiers
        )
        
        # Apply semantic adjustments
        # 1. Intent alignment adjustment (from intent-aware layer)
        from dropsim_intent_model import compute_intent_conditioned_continuation_prob, CANONICAL_INTENTS
        intent_frame = CANONICAL_INTENTS[sampled_intent_id]
        
        continuation_prob = compute_intent_conditioned_continuation_prob(
            base_prob, intent_frame, step_def, step_index, total_steps, state
        )
        
        # 2. Semantic friction adjustment
        semantic_friction = alignment_result.friction_delta
        continuation_prob *= (1.0 - semantic_friction * 0.15)  # Up to 15% reduction
        
        # 3. Knowledge gap penalty
        if 'knowledge_gap' in alignment_result.conflict_axes:
            continuation_prob *= 0.92  # 8% reduction
        
        # 4. Emotional impact
        if 'anxiety' in semantic_profile.emotional_deltas:
            anxiety_delta = semantic_profile.emotional_deltas['anxiety']
            if anxiety_delta > 0.3:  # Higher threshold
                continuation_prob *= (1.0 - (anxiety_delta - 0.3) * 0.1)  # Up to 10% reduction
        
        # 5. Trust signal boost
        if semantic_profile.trust_signal > 0.7:
            continuation_prob *= 1.1  # 10% boost for high trust
        
        # Add individual variance
        personality_noise = np.random.normal(0, 0.15)
        final_prob = np.clip(continuation_prob + personality_noise, 0.05, 0.95)
        
        # Record semantic mismatch if significant
        if alignment_result.intent_alignment_score < 0.5:
            semantic_mismatches.append({
                'step': step_name,
                'alignment_score': alignment_result.intent_alignment_score,
                'conflict_axes': alignment_result.conflict_axes,
                'semantic_reason': alignment_result.semantic_reason
            })
        
        # Record step with semantic information
        journey.append({
            'step': step_name,
            'cognitive_energy': state.cognitive_energy,
            'perceived_risk': state.perceived_risk,
            'perceived_effort': state.perceived_effort,
            'perceived_value': state.perceived_value,
            'perceived_control': state.perceived_control,
            'costs': costs,
            'semantic_profile': semantic_profile.dict(),
            'intent_alignment': alignment_result.dict(),
            'intent_id': sampled_intent_id,
            'continue': "True"
        })
        
        # Decision
        if np.random.random() >= final_prob:
            exit_step = step_name
            
            # Determine failure reason (semantic-aware)
            if alignment_result.intent_alignment_score < 0.4:
                failure_reason = f"Semantic mismatch: {', '.join(alignment_result.conflict_axes)}"
            elif alignment_result.predicted_effect == "increase_drop_probability":
                failure_reason = f"Semantic friction: {alignment_result.semantic_reason[:50]}"
            else:
                from behavioral_engine_improved import identify_failure_reason_improved
                failure_reason_enum = identify_failure_reason_improved(costs, state)
                failure_reason = failure_reason_enum.value if failure_reason_enum else "Multi-factor"
            
            journey[-1]['continue'] = "False"
            break
        
        previous_step = step_def
    
    if exit_step is None:
        exit_step = "Completed"
        failure_reason = None
    
    return {
        'variant': variant_name,
        'intent_id': sampled_intent_id,
        'journey': journey,
        'exit_step': exit_step,
        'failure_reason': failure_reason,
        'completed': exit_step == "Completed",
        'semantic_mismatches': semantic_mismatches,
        'final_state': {
            'cognitive_energy': state.cognitive_energy,
            'perceived_risk': state.perceived_risk,
            'perceived_effort': state.perceived_effort,
            'perceived_value': state.perceived_value,
            'perceived_control': state.perceived_control
        }
    }


def run_semantic_aware_simulation(
    df: pd.DataFrame,
    product_steps: Dict,
    intent_distribution: Optional[Dict[str, float]] = None,
    use_llm: bool = False,
    llm_client=None,
    verbose: bool = True,
    seed: int = 42
) -> pd.DataFrame:
    """
    Run semantic-aware behavioral simulation.
    
    Args:
        df: Personas DataFrame
        product_steps: Product step definitions
        intent_distribution: Optional pre-computed intent distribution
        use_llm: Whether to use LLM for copy inference
        llm_client: LLM client (if use_llm=True)
        verbose: Print progress
        seed: Random seed
    
    Returns:
        DataFrame with simulation results including semantic information
    """
    if verbose:
        print("🧠 Running Semantic-Aware Behavioral Simulation")
        print(f"   Personas: {len(df)}")
        print(f"   Product Steps: {len(product_steps)}")
        print(f"   Semantic Extraction: {'LLM' if use_llm else 'Rule-based'}")
        print(f"   Seed: {seed}")
    
    # Initialize semantic extractor
    semantic_extractor = StepSemanticExtractor(use_llm=use_llm, llm_client=llm_client)
    
    # Infer intent distribution if not provided
    if intent_distribution is None:
        from dropsim_intent_model import infer_intent_distribution
        first_step = list(product_steps.values())[0]
        entry_text = first_step.get('description', '')
        cta_phrasing = first_step.get('cta_phrasing', '')
        
        intent_result = infer_intent_distribution(
            entry_page_text=entry_text,
            cta_phrasing=cta_phrasing,
            product_type='fintech',
            persona_attributes={'intent': 'medium', 'urgency': 'medium'},
            product_steps=product_steps
        )
        intent_distribution = intent_result['intent_distribution']
        
        if verbose:
            print(f"\n   Inferred Intent Distribution:")
            for intent_id, prob in sorted(intent_distribution.items(), key=lambda x: x[1], reverse=True):
                print(f"     {intent_id}: {prob:.1%}")
    
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
        derived = {col: row[col] for col in derived_cols if col in row.index}
        
        # Simulate all variants with semantic awareness
        trajectories = []
        persona_seed = seed + idx * 10000
        
        for variant_idx, variant_name in enumerate(['fresh_motivated', 'tired_commuter', 'distrustful_arrival', 
                                                    'browsing_casually', 'urgent_need', 'price_sensitive', 
                                                    'tech_savvy_optimistic']):
            variant_seed = persona_seed + variant_idx * 1000
            traj = simulate_persona_trajectory_semantic_aware(
                row, derived, variant_name, product_steps, intent_distribution,
                semantic_extractor, seed=variant_seed
            )
            trajectories.append(traj)
        
        # Aggregate results
        exit_steps = [t['exit_step'] for t in trajectories]
        failure_reasons = [t['failure_reason'] for t in trajectories if t['failure_reason']]
        completed_count = sum(1 for t in trajectories if t['completed'])
        
        # Semantic mismatch analysis
        all_semantic_mismatches = []
        for traj in trajectories:
            all_semantic_mismatches.extend(traj.get('semantic_mismatches', []))
        
        exit_counter = Counter(exit_steps)
        dominant_exit = exit_counter.most_common(1)[0][0]
        
        if failure_reasons:
            reason_counter = Counter(failure_reasons)
            dominant_reason = reason_counter.most_common(1)[0][0]
        else:
            dominant_reason = None
        
        consistency = exit_counter.most_common(1)[0][1] / len(trajectories)
        
        all_results.append({
            'dominant_exit_step': dominant_exit,
            'dominant_failure_reason': dominant_reason,
            'consistency_score': consistency,
            'variants_completed': completed_count,
            'variants_total': len(trajectories),
            'completion_rate': completed_count / len(trajectories),
            'semantic_mismatch_count': len(all_semantic_mismatches),
            'trajectories': trajectories
        })
        
        if verbose and (idx + 1) % 50 == 0:
            print(f"   Simulated {idx + 1}/{len(df)} personas")
    
    results_df = pd.DataFrame(all_results)
    final_df = pd.concat([df.reset_index(drop=True), results_df], axis=1)
    
    if verbose:
        print(f"\n✅ Semantic-aware simulation complete!")
        print(f"   Avg completion rate: {results_df['completion_rate'].mean():.1%}")
        print(f"   Total semantic mismatches: {results_df['semantic_mismatch_count'].sum():,}")
    
    return final_df


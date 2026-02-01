"""
behavioral_engine_intent_aware.py - Intent-Aware Behavioral Simulation Engine

Augments the improved behavioral engine with intent-aware causal reasoning.
This layer explains WHY users act based on their underlying intent, not just behavioral factors.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from collections import Counter
import json
from datetime import datetime

# Import improved behavioral engine
from behavioral_engine_improved import (
    run_behavioral_simulation_improved,
    simulate_persona_trajectories_improved,
    should_continue_probabilistic,
    update_state_improved,
    InternalState,
    FailureReason
)

# Import intent modeling
from dropsim_intent_model import (
    CANONICAL_INTENTS,
    IntentFrame,
    infer_intent_distribution,
    compute_intent_alignment_score,
    identify_intent_mismatch,
    compute_intent_conditioned_continuation_prob,
    CREDIGO_GLOBAL_INTENT
)


# ============================================================================
# INTENT-AWARE SIMULATION
# ============================================================================

def simulate_persona_trajectory_intent_aware(
    row: pd.Series,
    derived: Dict,
    variant_name: str,
    product_steps: Dict,
    intent_distribution: Optional[Dict[str, float]] = None,
    fixed_intent: Optional[IntentFrame] = None,
    seed: Optional[int] = None
) -> Dict:
    """
    Simulate one persona trajectory with intent awareness.
    
    For each trajectory, we:
    1. Use fixed intent if provided, otherwise sample from distribution
    2. Track intent alignment at each step
    3. Adjust continuation probability based on intent alignment
    4. Record intent mismatches as failure reasons
    
    Args:
        fixed_intent: If provided, use this intent for all users (no sampling)
        intent_distribution: If fixed_intent is None, sample from this distribution
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Use fixed intent if provided, otherwise sample from distribution
    if fixed_intent is not None:
        # Fixed global intent (e.g., Credigo - all users want credit card recommendation)
        intent_frame = fixed_intent
        sampled_intent_id = fixed_intent.intent_id
    elif intent_distribution is not None:
        # Probabilistic intent sampling (for products with variable intents)
        intent_ids = list(intent_distribution.keys())
        intent_probs = list(intent_distribution.values())
        sampled_intent_id = np.random.choice(intent_ids, p=intent_probs)
        intent_frame = CANONICAL_INTENTS[sampled_intent_id]
    else:
        raise ValueError("Either fixed_intent or intent_distribution must be provided")
    
    # Run base simulation (reuse improved engine)
    from behavioral_engine_improved import (
        normalize_persona_inputs,
        compile_latent_priors,
        initialize_state,
        compute_archetype_modifiers
    )
    
    inputs = normalize_persona_inputs(row, derived)
    priors = compile_latent_priors(inputs)
    modifiers = compute_archetype_modifiers(priors, inputs)
    
    state = initialize_state(variant_name, priors)
    journey = []
    exit_step = None
    failure_reason = None
    intent_mismatches = []
    decision_traces = []  # NEW: Decision traces for this trajectory
    
    total_steps = len(product_steps)
    previous_step = None
    
    # Get persona ID for traces
    persona_id = f"{row.name}_{variant_name}" if hasattr(row, 'name') else f"persona_{variant_name}"
    
    for step_index, (step_name, step_def) in enumerate(product_steps.items()):
        # Update state (from improved engine)
        state, costs = update_state_improved(
            state, step_def, priors, step_index, total_steps, previous_step=previous_step
        )
        
        # Compute intent alignment
        alignment = compute_intent_alignment_score(step_def, intent_frame, step_index, total_steps)
        
        # Compute base continuation probability (from improved engine)
        base_prob = should_continue_probabilistic(
            state, priors, step_index, total_steps, modifiers
        )
        
        # Adjust for intent alignment (FIXED: bounded additive scoring)
        continuation_prob, prob_diagnostic = compute_intent_conditioned_continuation_prob(
            base_prob, intent_frame, step_def, step_index, total_steps, state
        )
        
        # Add individual variance (reduced noise)
        personality_noise = np.random.normal(0, 0.08)  # Reduced noise
        final_prob = np.clip(continuation_prob + personality_noise, 0.05, 0.95)
        
        # RULE 5: Enforce hard probability bounds (final check)
        # CRITICAL: Final minimum completion probability enforcement
        MIN_FINAL_PROB = 0.35  # 35% absolute minimum (maximum aggressive increase)
        final_prob = np.clip(final_prob, MIN_FINAL_PROB, 0.95)
        
        # Check for intent mismatch (how well does step serve the known goal)
        intent_analysis = identify_intent_mismatch(
            step_def, intent_frame, step_index, total_steps, "System 2 fatigue"
        )
        
        if intent_analysis['is_intent_mismatch']:
            intent_mismatches.append({
                'step': step_name,
                'mismatch_score': intent_analysis['mismatch_score'],
                'violated_intent': intent_analysis['violated_intent'],
                'mismatch_type': intent_analysis['mismatch_type'],
                'explanation': intent_analysis['explanation']
            })
        
        # Record step with intent information and full diagnostic
        journey.append({
            'step': step_name,
            'cognitive_energy': state.cognitive_energy,
            'perceived_risk': state.perceived_risk,
            'perceived_effort': state.perceived_effort,
            'perceived_value': state.perceived_value,
            'perceived_control': state.perceived_control,
            'costs': costs,
            'intent_alignment': alignment,
            'intent_id': sampled_intent_id,
            'probability_diagnostic': prob_diagnostic,  # Full diagnostic output
            'continuation_probability': final_prob,
            'continue': "True"
        })
        
        # NEW: Capture decision trace AT DECISION TIME (before sampling)
        from decision_graph.decision_trace import (
            create_decision_trace,
            DecisionOutcome
        )
        
        # Determine dominant factors from diagnostic and state
        dominant_factors = []
        if prob_diagnostic and isinstance(prob_diagnostic, dict):
            # Extract dominant factors from diagnostic
            if 'penalties' in prob_diagnostic:
                penalties = prob_diagnostic['penalties']
                if penalties.get('intent', 0) > 0.05:
                    dominant_factors.append('intent_mismatch')
                if penalties.get('cognitive', 0) > 0.05:
                    dominant_factors.append('cognitive_fatigue')
                if penalties.get('risk', 0) > 0.05:
                    dominant_factors.append('risk_spike')
                if penalties.get('effort', 0) > 0.05:
                    dominant_factors.append('effort_demand')
        
        # If no dominant factors from diagnostic, use failure reason logic
        if not dominant_factors:
            if intent_analysis.get('is_intent_mismatch') and intent_analysis.get('mismatch_score', 0) > 0.4:
                dominant_factors.append('intent_mismatch')
            if state.cognitive_energy < 0.3:
                dominant_factors.append('cognitive_fatigue')
            if state.perceived_risk > 0.7:
                dominant_factors.append('risk_spike')
            if state.perceived_effort > 0.7:
                dominant_factors.append('effort_demand')
        
        if not dominant_factors:
            dominant_factors = ['multi_factor']
        
        # Sample outcome
        sampled_value = np.random.random()
        sampled_outcome = sampled_value < final_prob  # True = continue, False = drop
        
        # Create decision trace BEFORE we know the outcome
        # (This is the key - capture at decision time)
        decision = DecisionOutcome.CONTINUE if sampled_outcome else DecisionOutcome.DROP
        
        cognitive_state_dict = {
            'cognitive_energy': state.cognitive_energy,
            'perceived_risk': state.perceived_risk,
            'perceived_effort': state.perceived_effort,
            'perceived_value': state.perceived_value,
            'perceived_control': state.perceived_control
        }
        
        intent_info_dict = {
            'inferred_intent': sampled_intent_id,
            'alignment_score': alignment
        }
        
        # Get current policy version (enforced policy versioning)
        try:
            from policy_registry.get_current_policy import get_current_policy_version
            current_policy_version = get_current_policy_version()
        except:
            # Fallback to default if policy registry not available
            current_policy_version = "v1.0"
        
        trace = create_decision_trace(
            persona_id=persona_id,
            step_id=step_name,
            step_index=step_index,
            decision=decision,
            probability_before_sampling=final_prob,
            sampled_outcome=sampled_outcome,
            cognitive_state=cognitive_state_dict,
            intent_info=intent_info_dict,
            dominant_factors=dominant_factors,
            policy_version=current_policy_version
        )
        
        # Compute decision attribution (game-theoretic force attribution)
        try:
            from decision_attribution.shap_attributor import compute_decision_attribution
            
            # Extract step forces from step_def
            step_forces = {
                'step_effort': step_def.get('effort_demand', 0.0),
                'step_risk': step_def.get('risk_signal', 0.0),
                'step_value': step_def.get('explicit_value', 0.0),
                'step_trust': step_def.get('reassurance_signal', 0.0)
            }
            
            # Extract cognitive state with tolerances from priors
            cognitive_state_for_attribution = {
                'cognitive_energy': state.cognitive_energy,
                'perceived_risk': state.perceived_risk,
                'perceived_effort': state.perceived_effort,
                'perceived_value': state.perceived_value,
                'perceived_control': state.perceived_control,
                'effort_tolerance': priors.get('ET', 0.5),  # Effort Tolerance
                'risk_tolerance': priors.get('RT', 0.5),    # Risk Tolerance
                'trust_baseline': priors.get('TB', 0.5),   # Trust Baseline
                'value_expectation': priors.get('MS', 0.5)  # Motivation Strength (value expectation)
            }
            
            # Extract intent info
            intent_attribution_info = {
                'intent_strength': intent_frame.tolerance_for_effort if fixed_intent else 0.5,
                'intent_mismatch': intent_analysis.get('mismatch_score', 0.0) if intent_analysis.get('is_intent_mismatch', False) else 0.0
            }
            
            # Compute attribution
            attribution = compute_decision_attribution(
                cognitive_state=cognitive_state_for_attribution,
                step_forces=step_forces,
                intent_info=intent_attribution_info,
                step_id=step_name,
                step_index=step_index,
                total_steps=total_steps,
                decision=decision.value,
                final_probability=final_prob,
                modifiers=modifiers,
                intent_alignment=alignment
            )
            
            # Attach attribution to trace
            trace.attribution = attribution
        except Exception as e:
            # If attribution fails, continue without it (non-critical)
            import warnings
            warnings.warn(f"Failed to compute attribution for {step_name}: {e}")
        
        decision_traces.append(trace)
        
        # Decision
        if not sampled_outcome:  # Dropped
            exit_step = step_name
            
            # Determine failure reason
            # For fixed intent: focus on friction, not intent mismatch
            # Intent mismatch should only be cited if step clearly blocks the known goal
            if fixed_intent is not None:
                # Fixed intent: explain as friction blocking the known goal
                if intent_analysis['is_intent_mismatch'] and intent_analysis['mismatch_score'] > 0.5:
                    # Step clearly blocks the known goal
                    failure_reason = f"Step blocked comparison goal: {intent_analysis['mismatch_type']}"
                else:
                    # Use behavioral failure reason (friction-based)
                    from behavioral_engine_improved import identify_failure_reason_improved
                    failure_reason_enum = identify_failure_reason_improved(costs, state)
                    failure_reason = failure_reason_enum.value if failure_reason_enum else "High friction"
            else:
                # Probabilistic intent: can cite intent mismatch
                if intent_analysis['is_intent_mismatch'] and intent_analysis['mismatch_score'] > 0.4:
                    failure_reason = f"Intent mismatch: {intent_analysis['mismatch_type']}"
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
    
    # Determine final outcome for decision sequence
    from decision_graph.decision_trace import DecisionOutcome
    final_outcome = DecisionOutcome.CONTINUE if exit_step == "Completed" else DecisionOutcome.DROP
    
    return {
        'variant': variant_name,
        'intent_id': sampled_intent_id,
        'intent_frame': intent_frame.to_dict(),
        'journey': journey,
        'exit_step': exit_step,
        'failure_reason': failure_reason,
        'completed': exit_step == "Completed",
        'intent_mismatches': intent_mismatches,
        'final_state': {
            'cognitive_energy': state.cognitive_energy,
            'perceived_risk': state.perceived_risk,
            'perceived_effort': state.perceived_effort,
            'perceived_value': state.perceived_value,
            'perceived_control': state.perceived_control
        },
        # NEW: Decision traces as first-class data
        'decision_traces': decision_traces,  # List of DecisionTrace objects
        'persona_id': persona_id  # For building sequences
    }


def run_intent_aware_simulation(
    df: pd.DataFrame,
    product_steps: Dict,
    intent_distribution: Optional[Dict[str, float]] = None,
    fixed_intent: Optional[IntentFrame] = None,
    verbose: bool = True,
    seed: int = 42
) -> pd.DataFrame:
    """
    Run intent-aware behavioral simulation.
    
    Args:
        df: Personas DataFrame
        product_steps: Product step definitions
        intent_distribution: Optional pre-computed intent distribution
        verbose: Print progress
        seed: Random seed
    
    Returns:
        DataFrame with simulation results including intent information
    """
    if verbose:
        print("🧠 Running Intent-Aware Behavioral Simulation")
        print(f"   Personas: {len(df)}")
        print(f"   Product Steps: {len(product_steps)}")
        print(f"   Seed: {seed}")
    
        # Use fixed intent if provided, otherwise infer intent distribution
        if fixed_intent is not None:
            # Fixed global intent (e.g., Credigo - all users want credit card recommendation)
            if verbose:
                print(f"\n   Using Fixed Global Intent:")
                print(f"     Intent ID: {fixed_intent.intent_id}")
                print(f"     Description: {fixed_intent.description}")
                print(f"     Primary Goal: {fixed_intent.primary_goal}")
        elif intent_distribution is None:
            # Infer from product characteristics
            # Extract entry page info from first step
            first_step = list(product_steps.values())[0]
            entry_text = first_step.get('description', '')
            cta_phrasing = first_step.get('cta_phrasing', '')
            
            # Infer intent distribution (now with product_steps for better inference)
            intent_result = infer_intent_distribution(
                entry_page_text=entry_text,
                cta_phrasing=cta_phrasing,
                product_type='fintech',  # Default, can be parameterized
                persona_attributes={'intent': 'medium', 'urgency': 'medium'},
                product_steps=product_steps  # Pass steps for intent signal analysis
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
        
        # Simulate all variants with intent awareness
        trajectories = []
        persona_seed = seed + idx * 10000
        
        for variant_idx, variant_name in enumerate(['fresh_motivated', 'tired_commuter', 'distrustful_arrival', 
                                                    'browsing_casually', 'urgent_need', 'price_sensitive', 
                                                    'tech_savvy_optimistic']):
            variant_seed = persona_seed + variant_idx * 1000
            traj = simulate_persona_trajectory_intent_aware(
                row, derived, variant_name, product_steps,
                intent_distribution=intent_distribution if fixed_intent is None else None,
                fixed_intent=fixed_intent,
                seed=variant_seed
            )
            trajectories.append(traj)
        
        # Aggregate results
        exit_steps = [t['exit_step'] for t in trajectories]
        failure_reasons = [t['failure_reason'] for t in trajectories if t['failure_reason']]
        completed_count = sum(1 for t in trajectories if t['completed'])
        
        # Intent distribution in this persona's trajectories
        intent_counts = Counter([t['intent_id'] for t in trajectories])
        
        # Intent mismatch analysis
        all_mismatches = []
        for traj in trajectories:
            all_mismatches.extend(traj.get('intent_mismatches', []))
        
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
            'intent_distribution': dict(intent_counts),
            'intent_mismatch_count': len(all_mismatches),
            'trajectories': trajectories
        })
        
        if verbose and (idx + 1) % 50 == 0:
            print(f"   Simulated {idx + 1}/{len(df)} personas")
    
    results_df = pd.DataFrame(all_results)
    final_df = pd.concat([df.reset_index(drop=True), results_df], axis=1)
    
    if verbose:
        print(f"\n✅ Intent-aware simulation complete!")
        print(f"   Avg completion rate: {results_df['completion_rate'].mean():.1%}")
        print(f"   Total intent mismatches: {results_df['intent_mismatch_count'].sum():,}")
    
    return final_df


# ============================================================================
# INTENT-AWARE ANALYSIS & REPORTING
# ============================================================================

def generate_intent_analysis(
    result_df: pd.DataFrame,
    product_steps: Dict
) -> Dict:
    """
    Generate intent-aware analysis of simulation results.
    
    Returns:
        {
            'intent_profile': {...},
            'intent_weighted_funnel': {...},
            'intent_conflict_matrix': {...},
            'intent_explanations': [...]
        }
    """
    # 1. Intent Profile
    all_intents = []
    for _, row in result_df.iterrows():
        for traj in row['trajectories']:
            all_intents.append(traj['intent_id'])
    
    intent_profile = dict(Counter(all_intents))
    total_trajectories = len(all_intents)
    intent_profile_pct = {intent: float(count / total_trajectories) for intent, count in intent_profile.items()}
    
    # 2. Intent-Weighted Funnel
    # Get unique intents from trajectories (handles both fixed and variable intents)
    unique_intents = set()
    for _, row in result_df.iterrows():
        for traj in row['trajectories']:
            unique_intents.add(traj['intent_id'])
    
    step_intent_exits = {}
    for step_name in product_steps.keys():
        step_intent_exits[step_name] = {}
        for intent_id in unique_intents:
            step_intent_exits[step_name][intent_id] = {'entered': 0, 'exited': 0}
    
    for _, row in result_df.iterrows():
        for traj in row['trajectories']:
            intent_id = traj['intent_id']
            journey = traj.get('journey', [])
            
            for step_data in journey:
                step_name = step_data['step']
                if step_name in step_intent_exits:
                    step_intent_exits[step_name][intent_id]['entered'] += 1
                    
                    if step_data.get('continue', 'True') == 'False':
                        step_intent_exits[step_name][intent_id]['exited'] += 1
    
    # 3. Intent Conflict Matrix
    # Use unique intents from trajectories (handles both fixed and variable intents)
    intent_conflicts = {}
    for step_name, step_def in product_steps.items():
        conflicts = {}
        # Get intent frames for unique intents
        for intent_id in unique_intents:
            # Check if intent is in CANONICAL_INTENTS or is the fixed Credigo intent
            if intent_id in CANONICAL_INTENTS:
                intent_frame = CANONICAL_INTENTS[intent_id]
            elif intent_id == 'compare_credit_cards':
                from dropsim_intent_model import CREDIGO_GLOBAL_INTENT
                intent_frame = CREDIGO_GLOBAL_INTENT
            else:
                continue  # Skip unknown intents
            
            alignment = compute_intent_alignment_score(step_def, intent_frame, 0, len(product_steps))
            conflicts[intent_id] = {
                'alignment': float(alignment),
                'is_conflict': bool(alignment < 0.5)  # Convert numpy bool to Python bool
            }
        intent_conflicts[step_name] = conflicts
    
    # 4. Intent Explanations
    explanations = []
    
    # Aggregate intent mismatches
    all_mismatches_by_step = {}
    for _, row in result_df.iterrows():
        for traj in row['trajectories']:
            for mismatch in traj.get('intent_mismatches', []):
                step_name = mismatch['step']
                if step_name not in all_mismatches_by_step:
                    all_mismatches_by_step[step_name] = []
                all_mismatches_by_step[step_name].append(mismatch)
    
    # Generate explanations
    for step_name, mismatches in all_mismatches_by_step.items():
        if mismatches:
            mismatch_counts = Counter([m['violated_intent'] for m in mismatches])
            dominant_violation = mismatch_counts.most_common(1)[0][0]
            avg_mismatch_score = np.mean([m['mismatch_score'] for m in mismatches])
            
            # Get intent frame (handles both canonical and fixed intents)
            if dominant_violation in CANONICAL_INTENTS:
                intent_frame = CANONICAL_INTENTS[dominant_violation]
            elif dominant_violation == 'compare_credit_cards':
                from dropsim_intent_model import CREDIGO_GLOBAL_INTENT
                intent_frame = CREDIGO_GLOBAL_INTENT
            else:
                # Fallback
                intent_frame = None
            
            if intent_frame:
                explanation = (
                    f"**{step_name}**: Given users came to {intent_frame.primary_goal}, "
                    f"this step blocked that goal because it required commitment/effort "
                    f"that exceeded their threshold. Average mismatch score: {avg_mismatch_score:.2f}. "
                    f"This caused {len(mismatches)} misalignments out of "
                    f"{step_intent_exits[step_name][dominant_violation]['entered']} "
                    f"trajectories."
                )
            else:
                explanation = (
                    f"**{step_name}**: Step blocked user goal. "
                    f"Average mismatch score: {avg_mismatch_score:.2f}. "
                    f"This caused {len(mismatches)} misalignments."
                )
            explanations.append(explanation)
    
    return {
        'intent_profile': intent_profile_pct,
        'intent_weighted_funnel': {
            step_name: {
                intent_id: {
                    'entered': data['entered'],
                    'exited': data['exited'],
                    'drop_rate': float((data['exited'] / data['entered'] * 100) if data['entered'] > 0 else 0)
                }
                for intent_id, data in step_data.items()
            }
            for step_name, step_data in step_intent_exits.items()
        },
        'intent_conflict_matrix': intent_conflicts,
        'intent_explanations': explanations
    }


def export_intent_artifacts(
    result_df: pd.DataFrame,
    product_steps: Dict,
    output_dir: str = "."
) -> Dict[str, str]:
    """
    Export all required intent artifacts.
    
    Returns:
        Dict mapping artifact names to file paths
    """
    analysis = generate_intent_analysis(result_df, product_steps)
    
    artifacts = {}
    
    # 1. intent_profile.json
    profile_path = f"{output_dir}/intent_profile.json"
    with open(profile_path, 'w') as f:
        json.dump(analysis['intent_profile'], f, indent=2)
    artifacts['intent_profile'] = profile_path
    
    # 2. intent_weighted_funnel.json
    funnel_path = f"{output_dir}/intent_weighted_funnel.json"
    with open(funnel_path, 'w') as f:
        json.dump(analysis['intent_weighted_funnel'], f, indent=2)
    artifacts['intent_weighted_funnel'] = funnel_path
    
    # 3. intent_conflict_matrix.json
    conflict_path = f"{output_dir}/intent_conflict_matrix.json"
    with open(conflict_path, 'w') as f:
        json.dump(analysis['intent_conflict_matrix'], f, indent=2)
    artifacts['intent_conflict_matrix'] = conflict_path
    
    # 4. intent_explanation.md
    explanation_path = f"{output_dir}/intent_explanation.md"
    with open(explanation_path, 'w') as f:
        f.write("# Intent-Aware Failure Analysis\n\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n\n")
        f.write("## Intent Distribution\n\n")
        for intent_id, prob in sorted(analysis['intent_profile'].items(), key=lambda x: x[1], reverse=True):
            # Handle both canonical and fixed intents
            if intent_id in CANONICAL_INTENTS:
                intent_frame = CANONICAL_INTENTS[intent_id]
            elif intent_id == 'compare_credit_cards':
                from dropsim_intent_model import CREDIGO_GLOBAL_INTENT
                intent_frame = CREDIGO_GLOBAL_INTENT
            else:
                continue  # Skip unknown intents
            f.write(f"### {intent_id} ({prob:.1%})\n")
            f.write(f"- **Description**: {intent_frame.description}\n")
            f.write(f"- **Primary Goal**: {intent_frame.primary_goal}\n")
            f.write(f"- **Expected Value**: {intent_frame.expected_value_type}\n\n")
        
        f.write("## Intent-Step Conflicts\n\n")
        for step_name, conflicts in analysis['intent_conflict_matrix'].items():
            f.write(f"### {step_name}\n\n")
            for intent_id, conflict_data in conflicts.items():
                status = "⚠️ CONFLICT" if conflict_data['is_conflict'] else "✓ Aligned"
                f.write(f"- **{intent_id}**: {status} (alignment: {conflict_data['alignment']:.2f})\n")
            f.write("\n")
        
        f.write("## Intent-Aware Failure Explanations\n\n")
        for i, explanation in enumerate(analysis['intent_explanations'], 1):
            f.write(f"{i}. {explanation}\n\n")
    
    artifacts['intent_explanation'] = explanation_path
    
    return artifacts

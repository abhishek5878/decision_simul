"""
dropsim_counterfactuals.py - Validation & Counterfactual Engine for DropSim

Enables "what-if" analysis by simulating interventions and quantifying their impact.
Answers:
- "What would have happened if we changed X?"
- "How confident are we in this conclusion?"
- "Which interventions have the highest impact?"

Fully deterministic - no randomness, no ML models.
"""

from typing import Dict, List, Optional, Tuple, Literal
from dataclasses import dataclass
from copy import deepcopy
import math

from dropsim_context_graph import EventTrace, Event
from behavioral_engine import (
    InternalState,
    update_state,
    should_continue,
    identify_failure_reason,
    initialize_state
)


# ============================================================================
# Counterfactual Result Schema
# ============================================================================

@dataclass
class CounterfactualResult:
    """Result of a counterfactual simulation."""
    intervention: Dict
    original_outcome: Literal["completed", "dropped"]
    new_outcome: Literal["completed", "dropped"]
    original_exit_step: Optional[str]
    new_exit_step: Optional[str]
    delta_energy: float  # Change in final cognitive_energy
    delta_risk: float  # Change in final perceived_risk
    delta_effort: float  # Change in final perceived_effort
    delta_value: float  # Change in final perceived_value
    delta_control: float  # Change in final perceived_control
    outcome_changed: bool  # Did the intervention change the outcome?
    effect_size: Literal["none", "small", "medium", "large"]  # Magnitude of change
    sensitivity: Literal["low", "medium", "high"]  # How sensitive is this to changes
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'intervention': self.intervention,
            'original_outcome': self.original_outcome,
            'new_outcome': self.new_outcome,
            'original_exit_step': self.original_exit_step,
            'new_exit_step': self.new_exit_step,
            'delta_energy': self.delta_energy,
            'delta_risk': self.delta_risk,
            'delta_effort': self.delta_effort,
            'delta_value': self.delta_value,
            'delta_control': self.delta_control,
            'outcome_changed': self.outcome_changed,
            'effect_size': self.effect_size,
            'sensitivity': self.sensitivity
        }


# ============================================================================
# Counterfactual Engine
# ============================================================================

def simulate_counterfactual(
    base_trace: EventTrace,
    intervention: Dict,
    product_steps: Dict,
    priors: Dict,
    state_variant_name: str
) -> CounterfactualResult:
    """
    Applies a minimal perturbation to the simulation and recomputes outcome deltas.
    
    Args:
        base_trace: Original EventTrace (baseline)
        intervention: Intervention specification:
            {
                "type": "step_modification",
                "step_id": "upload_documents",
                "delta": {"effort": -0.2, "risk": -0.1}
            }
            or
            {
                "type": "persona_adjustment",
                "field": "cognitive_energy",
                "delta": +0.1
            }
        product_steps: Dict of product steps keyed by step name
        priors: Compiled behavioral priors
        state_variant_name: Name of state variant (for re-initialization)
    
    Returns:
        CounterfactualResult with deltas and impact metrics
    """
    if not base_trace.events:
        # Empty trace - return no-op result
        return CounterfactualResult(
            intervention=intervention,
            original_outcome=base_trace.final_outcome,
            new_outcome=base_trace.final_outcome,
            original_exit_step=None,
            new_exit_step=None,
            delta_energy=0.0,
            delta_risk=0.0,
            delta_effort=0.0,
            delta_value=0.0,
            delta_control=0.0,
            outcome_changed=False,
            effect_size="none",
            sensitivity="low"
        )
    
    # Find intervention point
    intervention_type = intervention.get('type')
    intervention_step_id = intervention.get('step_id')
    intervention_field = intervention.get('field')
    
    # Find the step index where intervention applies
    intervention_index = None
    if intervention_type == "step_modification" and intervention_step_id:
        for i, event in enumerate(base_trace.events):
            if event.step_id == intervention_step_id:
                intervention_index = i
                break
    
    if intervention_index is None and intervention_type == "step_modification":
        # Intervention step not found - return no-op
        return CounterfactualResult(
            intervention=intervention,
            original_outcome=base_trace.final_outcome,
            new_outcome=base_trace.final_outcome,
            original_exit_step=base_trace.events[-1].step_id if base_trace.events else None,
            new_exit_step=base_trace.events[-1].step_id if base_trace.events else None,
            delta_energy=0.0,
            delta_risk=0.0,
            delta_effort=0.0,
            delta_value=0.0,
            delta_control=0.0,
            outcome_changed=False,
            effect_size="none",
            sensitivity="low"
        )
    
    # Get original final state
    original_final_event = base_trace.events[-1]
    original_final_state = original_final_event.state_after
    original_outcome = base_trace.final_outcome
    original_exit_step = None
    if original_outcome == "dropped":
        # Find the step where drop occurred
        for event in base_trace.events:
            if event.decision == "drop":
                original_exit_step = event.step_id
                break
    
    # Reconstruct state up to intervention point
    # Start from initial state
    state = initialize_state(state_variant_name, priors)
    
    # Apply persona adjustment if specified
    if intervention_type == "persona_adjustment" and intervention_field:
        delta = intervention.get('delta', 0.0)
        if intervention_field == "cognitive_energy":
            state.cognitive_energy = max(0.0, min(priors['CC'], state.cognitive_energy + delta))
        elif intervention_field == "perceived_risk":
            state.perceived_risk = max(0.0, min(3.0, state.perceived_risk + delta))
        elif intervention_field == "perceived_effort":
            state.perceived_effort = max(0.0, min(3.0, state.perceived_effort + delta))
        elif intervention_field == "perceived_value":
            state.perceived_value = max(0.0, min(3.0, state.perceived_value + delta))
        elif intervention_field == "perceived_control":
            state.perceived_control = max(0.0, min(2.0, state.perceived_control + delta))
    
    # Replay events up to and including intervention point
    previous_step = None
    new_exit_step = None
    new_outcome = "completed"
    
    # Determine how many events to replay
    events_to_replay = intervention_index + 1 if intervention_index is not None else len(base_trace.events)
    
    for i in range(events_to_replay):
        if i >= len(base_trace.events):
            break
        
        event = base_trace.events[i]
        step_name = event.step_id
        
        # Get step definition
        if step_name not in product_steps:
            # Step not found - use event's state_after as next state
            state = InternalState(
                cognitive_energy=event.state_after.get('cognitive_energy', state.cognitive_energy),
                perceived_risk=event.state_after.get('perceived_risk', state.perceived_risk),
                perceived_effort=event.state_after.get('perceived_effort', state.perceived_effort),
                perceived_value=event.state_after.get('perceived_value', state.perceived_value),
                perceived_control=event.state_after.get('perceived_control', state.perceived_control)
            )
            continue
        
        step_def = product_steps[step_name]
        if isinstance(step_def, dict):
            step_dict = step_def.copy()
        else:
            # Convert object to dict
            step_dict = {
                'cognitive_demand': getattr(step_def, 'cognitive_demand', 0.5),
                'effort_demand': getattr(step_def, 'effort_demand', 0.5),
                'risk_signal': getattr(step_def, 'risk_signal', 0.5),
                'irreversibility': getattr(step_def, 'irreversibility', 0),
                'delay_to_value': getattr(step_def, 'delay_to_value', 0),
                'explicit_value': getattr(step_def, 'explicit_value', 0.5),
                'reassurance_signal': getattr(step_def, 'reassurance_signal', 0.5),
                'authority_signal': getattr(step_def, 'authority_signal', 0.5)
            }
        
        # Apply intervention if this is the intervention step
        if i == intervention_index and intervention_type == "step_modification":
            delta = intervention.get('delta', {})
            if 'effort' in delta:
                step_dict['effort_demand'] = max(0.0, min(1.0, step_dict.get('effort_demand', 0.5) + delta['effort']))
            if 'risk' in delta:
                step_dict['risk_signal'] = max(0.0, min(1.0, step_dict.get('risk_signal', 0.5) + delta['risk']))
            if 'cognitive' in delta:
                step_dict['cognitive_demand'] = max(0.0, min(1.0, step_dict.get('cognitive_demand', 0.5) + delta['cognitive']))
            if 'value' in delta:
                step_dict['explicit_value'] = max(0.0, min(1.0, step_dict.get('explicit_value', 0.5) + delta['value']))
            if 'reassurance' in delta:
                step_dict['reassurance_signal'] = max(0.0, min(1.0, step_dict.get('reassurance_signal', 0.5) + delta['reassurance']))
        
        # Update state
        state, costs = update_state(state, step_dict, priors, previous_step=previous_step)
        
        # Check if we should continue
        if not should_continue(state, priors):
            # Dropped at this step
            new_exit_step = step_name
            new_outcome = "dropped"
            break
        
        previous_step = step_dict
    
    # If we haven't dropped yet, continue through remaining steps
    if new_outcome != "dropped" and intervention_index is not None:
        # Continue from step after intervention
        step_names = list(product_steps.keys())
        try:
            intervention_step_name = base_trace.events[intervention_index].step_id
            if intervention_step_name in step_names:
                start_idx = step_names.index(intervention_step_name) + 1
            else:
                start_idx = intervention_index + 1
        except (ValueError, IndexError):
            start_idx = intervention_index + 1
        
        for step_name in step_names[start_idx:]:
            if step_name not in product_steps:
                continue
            
            step_def = product_steps[step_name]
            if isinstance(step_def, dict):
                step_dict = step_def.copy()
            else:
                step_dict = {
                    'cognitive_demand': getattr(step_def, 'cognitive_demand', 0.5),
                    'effort_demand': getattr(step_def, 'effort_demand', 0.5),
                    'risk_signal': getattr(step_def, 'risk_signal', 0.5),
                    'irreversibility': getattr(step_def, 'irreversibility', 0),
                    'delay_to_value': getattr(step_def, 'delay_to_value', 0),
                    'explicit_value': getattr(step_def, 'explicit_value', 0.5),
                    'reassurance_signal': getattr(step_def, 'reassurance_signal', 0.5),
                    'authority_signal': getattr(step_def, 'authority_signal', 0.5)
                }
            
            # Update state
            state, costs = update_state(state, step_dict, priors, previous_step=previous_step)
            
            # Check continuation
            if not should_continue(state, priors):
                new_exit_step = step_name
                new_outcome = "dropped"
                break
            
            previous_step = step_dict
        else:
            # Completed all steps
            if new_exit_step is None:
                new_outcome = "completed"
    
    # Compute deltas
    new_final_state = {
        'cognitive_energy': state.cognitive_energy,
        'perceived_risk': state.perceived_risk,
        'perceived_effort': state.perceived_effort,
        'perceived_value': state.perceived_value,
        'perceived_control': state.perceived_control
    }
    
    delta_energy = new_final_state['cognitive_energy'] - original_final_state.get('cognitive_energy', 0)
    delta_risk = new_final_state['perceived_risk'] - original_final_state.get('perceived_risk', 0)
    delta_effort = new_final_state['perceived_effort'] - original_final_state.get('perceived_effort', 0)
    delta_value = new_final_state['perceived_value'] - original_final_state.get('perceived_value', 0)
    delta_control = new_final_state['perceived_control'] - original_final_state.get('perceived_control', 0)
    
    # Determine effect size
    outcome_changed = (original_outcome != new_outcome)
    total_delta_magnitude = abs(delta_energy) + abs(delta_risk) + abs(delta_effort) + abs(delta_value) + abs(delta_control)
    
    if outcome_changed:
        effect_size = "large"
    elif total_delta_magnitude > 0.5:
        effect_size = "medium"
    elif total_delta_magnitude > 0.1:
        effect_size = "small"
    else:
        effect_size = "none"
    
    # Determine sensitivity (how much did small change affect outcome?)
    if outcome_changed:
        sensitivity = "high"
    elif total_delta_magnitude > 0.3:
        sensitivity = "medium"
    else:
        sensitivity = "low"
    
    return CounterfactualResult(
        intervention=intervention,
        original_outcome=original_outcome,
        new_outcome=new_outcome,
        original_exit_step=original_exit_step,
        new_exit_step=new_exit_step,
        delta_energy=delta_energy,
        delta_risk=delta_risk,
        delta_effort=delta_effort,
        delta_value=delta_value,
        delta_control=delta_control,
        outcome_changed=outcome_changed,
        effect_size=effect_size,
        sensitivity=sensitivity
    )


# ============================================================================
# Sensitivity Analysis
# ============================================================================

def rank_interventions_by_impact(
    event_traces: List[EventTrace],
    product_steps: Dict,
    priors_map: Dict[str, Dict],  # persona_id -> priors
    state_variant_map: Dict[str, str],  # persona_id -> variant_name
    intervention_candidates: List[Dict],
    top_n: int = 10
) -> List[Dict]:
    """
    Run multiple counterfactuals and rank by impact.
    
    Args:
        event_traces: List of baseline EventTrace objects
        product_steps: Dict of product steps
        priors_map: Map from persona_id to priors
        state_variant_map: Map from persona_id to variant_name
        intervention_candidates: List of intervention dicts to test
        top_n: Number of top interventions to return
    
    Returns:
        List of intervention results sorted by impact (outcome changes first, then effect size)
    """
    results = []
    
    for trace in event_traces:
        persona_id = trace.persona_id
        priors = priors_map.get(persona_id, {})
        variant_name = state_variant_map.get(persona_id, "fresh_motivated")
        
        if not priors:
            continue
        
        for intervention in intervention_candidates:
            try:
                result = simulate_counterfactual(
                    trace,
                    intervention,
                    product_steps,
                    priors,
                    variant_name
                )
                results.append({
                    'persona_id': persona_id,
                    'variant_id': trace.variant_id,
                    'intervention': intervention,
                    'result': result
                })
            except Exception:
                continue
    
    # Aggregate results by intervention
    intervention_impact = {}
    for item in results:
        intervention_key = str(item['intervention'])
        if intervention_key not in intervention_impact:
            intervention_impact[intervention_key] = {
                'intervention': item['intervention'],
                'outcome_changes': 0,
                'total_effect_size': 0.0,
                'total_sensitivity': 0.0,
                'count': 0,
                'examples': []
            }
        
        impact = intervention_impact[intervention_key]
        impact['count'] += 1
        
        result = item['result']
        if result.outcome_changed:
            impact['outcome_changes'] += 1
        
        # Score effect size (large=3, medium=2, small=1, none=0)
        effect_score = {"none": 0, "small": 1, "medium": 2, "large": 3}.get(result.effect_size, 0)
        impact['total_effect_size'] += effect_score
        
        # Score sensitivity (high=3, medium=2, low=1)
        sensitivity_score = {"low": 1, "medium": 2, "high": 3}.get(result.sensitivity, 1)
        impact['total_sensitivity'] += sensitivity_score
        
        if len(impact['examples']) < 3:
            impact['examples'].append(result.to_dict())
    
    # Compute average scores
    for impact in intervention_impact.values():
        if impact['count'] > 0:
            impact['avg_effect_size'] = impact['total_effect_size'] / impact['count']
            impact['avg_sensitivity'] = impact['total_sensitivity'] / impact['count']
            impact['outcome_change_rate'] = impact['outcome_changes'] / impact['count']
        else:
            impact['avg_effect_size'] = 0.0
            impact['avg_sensitivity'] = 0.0
            impact['outcome_change_rate'] = 0.0
    
    # Sort by impact (outcome changes first, then effect size, then sensitivity)
    ranked = sorted(
        intervention_impact.values(),
        key=lambda x: (
            x['outcome_change_rate'],  # Primary: outcome changes
            x['avg_effect_size'],  # Secondary: effect size
            x['avg_sensitivity']  # Tertiary: sensitivity
        ),
        reverse=True
    )
    
    return ranked[:top_n]


def generate_intervention_candidates(product_steps: Dict, fragile_steps: List[Dict]) -> List[Dict]:
    """
    Generate a set of intervention candidates based on fragile steps.
    
    Args:
        product_steps: Dict of product steps
        fragile_steps: List of fragile step info from context graph
    
    Returns:
        List of intervention dicts to test
    """
    candidates = []
    
    # For each fragile step, generate interventions
    for step_info in fragile_steps[:5]:  # Top 5 fragile steps
        step_id = step_info.get('step_id')
        if step_id not in product_steps:
            continue
        
        # Reduce effort
        candidates.append({
            'type': 'step_modification',
            'step_id': step_id,
            'delta': {'effort': -0.2}
        })
        
        # Reduce risk
        candidates.append({
            'type': 'step_modification',
            'step_id': step_id,
            'delta': {'risk': -0.15}
        })
        
        # Reduce cognitive demand
        candidates.append({
            'type': 'step_modification',
            'step_id': step_id,
            'delta': {'cognitive': -0.2}
        })
        
        # Increase value
        candidates.append({
            'type': 'step_modification',
            'step_id': step_id,
            'delta': {'value': +0.2}
        })
        
        # Increase reassurance
        candidates.append({
            'type': 'step_modification',
            'step_id': step_id,
            'delta': {'reassurance': +0.2}
        })
        
        # Combined: reduce effort + risk
        candidates.append({
            'type': 'step_modification',
            'step_id': step_id,
            'delta': {'effort': -0.15, 'risk': -0.1}
        })
    
    return candidates


# ============================================================================
# Sensitivity Map
# ============================================================================

def compute_sensitivity_map(
    event_traces: List[EventTrace],
    product_steps: Dict,
    priors_map: Dict[str, Dict],
    state_variant_map: Dict[str, str]
) -> Dict:
    """
    Compute sensitivity map showing which variables are most sensitive.
    
    Returns:
        Dict with sensitivity scores for each variable type
    """
    # Test small perturbations for each variable type
    test_interventions = [
        {'type': 'step_modification', 'step_id': step_id, 'delta': {'effort': -0.1}}
        for step_id in product_steps.keys()
    ] + [
        {'type': 'step_modification', 'step_id': step_id, 'delta': {'risk': -0.1}}
        for step_id in product_steps.keys()
    ] + [
        {'type': 'step_modification', 'step_id': step_id, 'delta': {'cognitive': -0.1}}
        for step_id in product_steps.keys()
    ]
    
    # Count outcome changes per variable type
    effort_changes = 0
    risk_changes = 0
    cognitive_changes = 0
    total_tested = 0
    
    for trace in event_traces[:100]:  # Sample first 100 for speed
        persona_id = trace.persona_id
        priors = priors_map.get(persona_id, {})
        variant_name = state_variant_map.get(persona_id, "fresh_motivated")
        
        if not priors:
            continue
        
        for intervention in test_interventions:
            try:
                result = simulate_counterfactual(
                    trace,
                    intervention,
                    product_steps,
                    priors,
                    variant_name
                )
                total_tested += 1
                
                if result.outcome_changed:
                    delta = intervention.get('delta', {})
                    if 'effort' in delta:
                        effort_changes += 1
                    elif 'risk' in delta:
                        risk_changes += 1
                    elif 'cognitive' in delta:
                        cognitive_changes += 1
            except Exception:
                continue
    
    # Compute sensitivity scores
    effort_sensitivity = effort_changes / max(total_tested / 3, 1) if total_tested > 0 else 0.0
    risk_sensitivity = risk_changes / max(total_tested / 3, 1) if total_tested > 0 else 0.0
    cognitive_sensitivity = cognitive_changes / max(total_tested / 3, 1) if total_tested > 0 else 0.0
    
    return {
        'effort_sensitivity': effort_sensitivity,
        'risk_sensitivity': risk_sensitivity,
        'cognitive_sensitivity': cognitive_sensitivity,
        'most_sensitive': max(
            [('effort', effort_sensitivity), ('risk', risk_sensitivity), ('cognitive', cognitive_sensitivity)],
            key=lambda x: x[1]
        )[0] if total_tested > 0 else 'unknown'
    }


# ============================================================================
# Robustness Score
# ============================================================================

def compute_robustness_score(
    event_traces: List[EventTrace],
    product_steps: Dict,
    priors_map: Dict[str, Dict],
    state_variant_map: Dict[str, str]
) -> float:
    """
    Compute robustness score (0-1) indicating how stable results are to small perturbations.
    
    Higher score = more robust (less sensitive to small changes)
    Lower score = less robust (highly sensitive to changes)
    """
    # Test small random perturbations
    test_interventions = []
    for step_id in list(product_steps.keys())[:3]:  # Test first 3 steps
        test_interventions.extend([
            {'type': 'step_modification', 'step_id': step_id, 'delta': {'effort': -0.05}},
            {'type': 'step_modification', 'step_id': step_id, 'delta': {'risk': -0.05}},
        ])
    
    outcome_changes = 0
    total_tested = 0
    
    for trace in event_traces[:50]:  # Sample for speed
        persona_id = trace.persona_id
        priors = priors_map.get(persona_id, {})
        variant_name = state_variant_map.get(persona_id, "fresh_motivated")
        
        if not priors:
            continue
        
        for intervention in test_interventions:
            try:
                result = simulate_counterfactual(
                    trace,
                    intervention,
                    product_steps,
                    priors,
                    variant_name
                )
                total_tested += 1
                if result.outcome_changed:
                    outcome_changes += 1
            except Exception:
                continue
    
    if total_tested == 0:
        return 0.5  # Default moderate robustness
    
    # Robustness = 1 - (outcome_change_rate)
    # Higher = more robust (fewer outcome changes from small perturbations)
    outcome_change_rate = outcome_changes / total_tested
    robustness = 1.0 - outcome_change_rate
    
    return max(0.0, min(1.0, robustness))


# ============================================================================
# Top Interventions Analysis
# ============================================================================

def analyze_top_interventions(
    event_traces: List[EventTrace],
    product_steps: Dict,
    priors_map: Dict[str, Dict],
    state_variant_map: Dict[str, str],
    fragile_steps: List[Dict],
    top_n: int = 5
) -> Dict:
    """
    Analyze and rank top interventions.
    
    Returns:
        Dict with top_interventions, sensitivity_map, most_impactful_step, robustness_score
    """
    # Generate intervention candidates
    candidates = generate_intervention_candidates(product_steps, fragile_steps)
    
    # Rank by impact
    top_interventions = rank_interventions_by_impact(
        event_traces,
        product_steps,
        priors_map,
        state_variant_map,
        candidates,
        top_n=top_n
    )
    
    # Compute sensitivity map
    sensitivity_map = compute_sensitivity_map(
        event_traces,
        product_steps,
        priors_map,
        state_variant_map
    )
    
    # Find most impactful step
    most_impactful_step = None
    if top_interventions:
        # Get step from top intervention
        top_intervention = top_interventions[0]
        intervention = top_intervention.get('intervention', {})
        if intervention.get('type') == 'step_modification':
            most_impactful_step = intervention.get('step_id')
    
    # Compute robustness
    robustness_score = compute_robustness_score(
        event_traces,
        product_steps,
        priors_map,
        state_variant_map
    )
    
    return {
        'top_interventions': [
            {
                'intervention': item['intervention'],
                'outcome_change_rate': item['outcome_change_rate'],
                'avg_effect_size': item['avg_effect_size'],
                'avg_sensitivity': item['avg_sensitivity'],
                'examples': item['examples'][:2]  # Top 2 examples
            }
            for item in top_interventions
        ],
        'sensitivity_map': sensitivity_map,
        'most_impactful_step': most_impactful_step,
        'robustness_score': robustness_score
    }


#!/usr/bin/env python3
"""
Credigo Decision-First Results

Shows Credigo simulation results using decision-first queries (not analytics).
"""

import json
import sys
from decision_graph.decision_trace import DecisionTrace, DecisionSequence, DecisionOutcome
from decision_graph.graph_queries import (
    query_decision_boundaries,
    query_persona_differentiation,
    query_stable_precedents,
    query_competing_explanations,
    query_acceptance_surface
)


def load_sequences_from_result(result_file: str):
    """Load decision sequences from pipeline result file."""
    with open(result_file, 'r') as f:
        data = json.load(f)
    
    traces_data = data.get('decision_traces', [])
    if not traces_data:
        print("No decision traces found in result file")
        return [], {}
    
    # Get product steps from traces (more reliable)
    step_ids_dict = {}
    for trace_dict in traces_data:
        step_id = trace_dict.get('step_id', '')
        step_idx = trace_dict.get('step_index', -1)
        if step_id and step_idx >= 0:
            step_ids_dict[step_id] = step_idx
    
    # Create product_steps dict sorted by index
    product_steps = {step_id: {} for step_id, _ in sorted(step_ids_dict.items(), key=lambda x: x[1])}
    
    # Group traces by persona_id and variant to build sequences
    sequences_dict = {}
    
    for trace_dict in traces_data:
        persona_id = trace_dict.get('persona_id', 'unknown')
        if '_' in persona_id:
            parts = persona_id.split('_', 1)
            variant = parts[1] if len(parts) > 1 else 'default'
            base_id = parts[0]
        else:
            variant = 'default'
            base_id = persona_id
        
        key = (base_id, variant)
        
        if key not in sequences_dict:
            sequences_dict[key] = {
                'persona_id': base_id,
                'variant_name': variant,
                'traces': [],
                'final_outcome': DecisionOutcome.CONTINUE,
                'exit_step': None
            }
        
        trace = DecisionTrace.from_dict(trace_dict)
        sequences_dict[key]['traces'].append(trace)
        
        if trace.decision == DecisionOutcome.DROP:
            sequences_dict[key]['final_outcome'] = DecisionOutcome.DROP
            if sequences_dict[key]['exit_step'] is None:
                sequences_dict[key]['exit_step'] = trace.step_id
    
    sequences = []
    for key, seq_data in sequences_dict.items():
        seq_data['traces'].sort(key=lambda t: t.step_index)
        sequence = DecisionSequence(
            persona_id=seq_data['persona_id'],
            variant_name=seq_data['variant_name'],
            traces=seq_data['traces'],
            final_outcome=seq_data['final_outcome'],
            exit_step=seq_data['exit_step']
        )
        sequences.append(sequence)
    
    return sequences, product_steps


def main():
    result_file = 'output/credigo_pipeline_result.json'
    
    print("=" * 80)
    print("CREDIGO: DECISION-FIRST RESULTS")
    print("=" * 80)
    print()
    
    # Load data
    sequences, product_steps = load_sequences_from_result(result_file)
    print(f"Loaded {len(sequences)} decision sequences")
    print(f"Product steps: {len(product_steps)}")
    print()
    
    if not sequences:
        print("No sequences to analyze")
        return 1
    
    # Get step list for queries
    step_list = list(product_steps.keys())
    
    # QUERY 1: Decision Boundaries at Landing Page
    print("=" * 80)
    print("DECISION BOUNDARIES: Landing Page")
    print("=" * 80)
    print()
    
    landing_step = step_list[0] if step_list else "Find the Best Credit Card In 60 seconds"
    boundaries = query_decision_boundaries(sequences, landing_step)
    
    print(f"Step: {landing_step}")
    print(f"Persona classes at decision boundary: {len(boundaries)}")
    print()
    
    for boundary in boundaries:
        print(f"Persona Class: {boundary.persona_class}")
        print(f"  Accepted: {boundary.accepted_count:,}")
        print(f"  Rejected: {boundary.rejected_count:,}")
        if boundary.cognitive_thresholds:
            thresholds = boundary.cognitive_thresholds
            print(f"  Cognitive Thresholds (accepted personas):")
            if 'energy' in thresholds:
                e_min, e_max = thresholds['energy']
                print(f"    Energy: {e_min:.2f} - {e_max:.2f}")
            if 'risk' in thresholds:
                r_min, r_max = thresholds['risk']
                print(f"    Risk: {r_min:.2f} - {r_max:.2f}")
        print()
    
    # QUERY 2: Stable Precedents
    print("=" * 80)
    print("STABLE PRECEDENTS: Top 15 Recurring Decision Patterns")
    print("=" * 80)
    print()
    
    precedents = query_stable_precedents(sequences, minimum_occurrence=50)
    print(f"Found {len(precedents)} stable precedents (min 50 occurrences)")
    print()
    
    for i, precedent in enumerate(precedents[:15], 1):
        print(f"{i:2d}. Step: {precedent.step_id[:55]}")
        print(f"    Persona Class: {precedent.persona_class}")
        print(f"    Factors: {', '.join(precedent.dominant_factors)}")
        print(f"    Outcome: {precedent.outcome.value}")
        print(f"    Occurrences: {precedent.occurrence_count:,}")
        print()
    
    # QUERY 3: Competing Explanations
    print("=" * 80)
    print("COMPETING EXPLANATIONS: Multi-Factor Reasoning")
    print("=" * 80)
    print()
    
    competing = query_competing_explanations(sequences, primary_factor="intent_alignment")
    print(f"Found {len(competing)} competing explanations")
    print()
    
    # Group by outcome
    drops_despite_high = [e for e in competing if e.outcome == DecisionOutcome.DROP]
    continues_despite_low = [e for e in competing if e.outcome == DecisionOutcome.CONTINUE]
    
    if drops_despite_high:
        print("DROPS despite HIGH intent alignment:")
        for explanation in drops_despite_high[:5]:
            print(f"  Step: {explanation.step_id[:55]}")
            print(f"    Intent Alignment: {explanation.primary_factor_value:.2f} (HIGH)")
            print(f"    But dropped due to: {', '.join(explanation.competing_factors)}")
            print(f"    Traces: {explanation.trace_count:,}")
            print()
    
    if continues_despite_low:
        print("CONTINUATIONS despite LOW intent alignment:")
        for explanation in continues_despite_low[:5]:
            print(f"  Step: {explanation.step_id[:55]}")
            print(f"    Intent Alignment: {explanation.primary_factor_value:.2f} (LOW)")
            print(f"    But continued due to: {', '.join(explanation.competing_factors)}")
            print(f"    Traces: {explanation.trace_count:,}")
            print()
    
    # QUERY 4: Acceptance Surface
    print("=" * 80)
    print("ACCEPTANCE SURFACE: Deepest Step per Persona Class")
    print("=" * 80)
    print()
    
    surfaces = query_acceptance_surface(sequences, product_steps)
    print(f"Found {len(surfaces)} persona class acceptance surfaces")
    print()
    
    # Sort by deepest step index
    surfaces_sorted = sorted(surfaces, key=lambda s: s.deepest_step_index, reverse=True)
    
    for surface in surfaces_sorted:
        print(f"Persona Class: {surface.persona_class}")
        print(f"  Deepest Step: {surface.deepest_step_id[:55]}")
        print(f"  Step Index: {surface.deepest_step_index}")
        print(f"  Traces Reaching Step: {surface.traces_reaching_step:,}")
        print(f"  Traces Completing Funnel: {surface.traces_completing_funnel:,}")
        if surface.continuation_collapse_step:
            print(f"  Continuation Collapse: {surface.continuation_collapse_step}")
        print()
    
    # QUERY 5: Decision Boundaries at Key Steps
    print("=" * 80)
    print("DECISION BOUNDARIES: Key Steps (First 3 Steps)")
    print("=" * 80)
    print()
    
    for step_idx in range(min(3, len(step_list))):
        step_id = step_list[step_idx]
        boundaries = query_decision_boundaries(sequences, step_id)
        
        print(f"Step {step_idx + 1}: {step_id[:55]}")
        print(f"  Persona classes: {len(boundaries)}")
        
        # Summarize by outcome
        total_accepted = sum(b.accepted_count for b in boundaries)
        total_rejected = sum(b.rejected_count for b in boundaries)
        
        print(f"  Total Accepted: {total_accepted:,}")
        print(f"  Total Rejected: {total_rejected:,}")
        print()
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print("All results are decision-first (not analytics-style):")
    print("  ✓ Decision boundaries per persona class")
    print("  ✓ Stable precedents (recurring patterns)")
    print("  ✓ Competing explanations (multi-factor)")
    print("  ✓ Acceptance surfaces per persona class")
    print()
    print("No global drop rates, funnel percentages, or monocausal claims.")
    print("All insights are precedent-based and audit-safe.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())


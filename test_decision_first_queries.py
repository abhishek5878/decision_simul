#!/usr/bin/env python3
"""
Test Decision-First Queries

Demonstrates the new decision-first query primitives (not analytics-style).
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
        return []
    
    # Group traces by persona_id and variant to build sequences
    sequences_dict = {}  # (persona_id, variant) -> sequence data
    
    for trace_dict in traces_data:
        persona_id = trace_dict.get('persona_id', 'unknown')
        # Extract variant from persona_id if possible
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
        
        # Update final outcome if this is a drop
        if trace.decision == DecisionOutcome.DROP:
            sequences_dict[key]['final_outcome'] = DecisionOutcome.DROP
            if sequences_dict[key]['exit_step'] is None:
                sequences_dict[key]['exit_step'] = trace.step_id
    
    # Build DecisionSequence objects
    sequences = []
    for key, seq_data in sequences_dict.items():
        # Sort traces by step_index
        seq_data['traces'].sort(key=lambda t: t.step_index)
        
        sequence = DecisionSequence(
            persona_id=seq_data['persona_id'],
            variant_name=seq_data['variant_name'],
            traces=seq_data['traces'],
            final_outcome=seq_data['final_outcome'],
            exit_step=seq_data['exit_step']
        )
        sequences.append(sequence)
    
    return sequences


def main():
    result_file = 'output/credigo_pipeline_result.json'
    
    print("=" * 80)
    print("DECISION-FIRST QUERY DEMONSTRATION")
    print("=" * 80)
    print()
    
    # Load sequences
    print(f"Loading decision sequences from {result_file}...")
    sequences = load_sequences_from_result(result_file)
    print(f"✓ Loaded {len(sequences)} decision sequences")
    print()
    
    if not sequences:
        print("No sequences to query. Exiting.")
        return 1
    
    # Get product steps from result file
    with open(result_file, 'r') as f:
        data = json.load(f)
    
    # Extract step list from traces
    step_ids = set()
    for seq in sequences:
        for trace in seq.traces:
            step_ids.add(trace.step_id)
    
    product_steps = {step_id: {} for step_id in sorted(step_ids)}
    
    # Query 1: Decision Boundaries at Landing Page
    print("=" * 80)
    print("QUERY 1: Decision Boundaries at Landing Page")
    print("=" * 80)
    print()
    
    landing_step = "Find the Best Credit Card In 60 seconds"
    boundaries = query_decision_boundaries(sequences, landing_step)
    
    print(f"Decision boundaries at step: {landing_step}")
    print(f"Found {len(boundaries)} persona classes")
    print()
    
    for i, boundary in enumerate(boundaries[:5], 1):  # Show top 5
        print(f"{i}. Persona Class: {boundary.persona_class}")
        print(f"   Accepted: {boundary.accepted_count}")
        print(f"   Rejected: {boundary.rejected_count}")
        if boundary.cognitive_thresholds:
            thresholds = boundary.cognitive_thresholds
            print(f"   Cognitive Thresholds:")
            print(f"     Energy: {thresholds.get('energy', (0, 0))[0]:.2f} - {thresholds.get('energy', (0, 0))[1]:.2f}")
            print(f"     Risk: {thresholds.get('risk', (0, 0))[0]:.2f} - {thresholds.get('risk', (0, 0))[1]:.2f}")
        print(f"   Has counterexample (accepted): {boundary.counterexample_accepted is not None}")
        print(f"   Has counterexample (rejected): {boundary.counterexample_rejected is not None}")
        print()
    
    # Query 2: Stable Precedents
    print("=" * 80)
    print("QUERY 2: Stable Precedents (Recurring Decision Patterns)")
    print("=" * 80)
    print()
    
    precedents = query_stable_precedents(sequences, minimum_occurrence=10)
    print(f"Found {len(precedents)} stable precedents (min 10 occurrences)")
    print()
    
    for i, precedent in enumerate(precedents[:10], 1):  # Show top 10
        print(f"{i}. Step: {precedent.step_id[:50]}")
        print(f"   Persona Class: {precedent.persona_class}")
        print(f"   Dominant Factors: {list(precedent.dominant_factors)}")
        print(f"   Outcome: {precedent.outcome.value}")
        print(f"   Occurrences: {precedent.occurrence_count}")
        print(f"   Example Traces: {len(precedent.example_traces)}")
        print()
    
    # Query 3: Competing Explanations
    print("=" * 80)
    print("QUERY 3: Competing Explanations (Multi-Factor Reasoning)")
    print("=" * 80)
    print()
    
    competing = query_competing_explanations(sequences, primary_factor="intent_alignment")
    print(f"Found {len(competing)} competing explanations")
    print()
    
    for i, explanation in enumerate(competing[:10], 1):  # Show top 10
        print(f"{i}. Step: {explanation.step_id[:50]}")
        print(f"   Outcome: {explanation.outcome.value}")
        print(f"   Primary Factor ({explanation.primary_factor}): {explanation.primary_factor_value:.2f}")
        print(f"   Competing Factors: {explanation.competing_factors}")
        print(f"   Trace Count: {explanation.trace_count}")
        print()
    
    # Query 4: Acceptance Surface
    print("=" * 80)
    print("QUERY 4: Acceptance Surface (Deepest Step per Persona Class)")
    print("=" * 80)
    print()
    
    surfaces = query_acceptance_surface(sequences, product_steps)
    print(f"Found {len(surfaces)} persona class acceptance surfaces")
    print()
    
    for i, surface in enumerate(surfaces[:10], 1):  # Show top 10
        print(f"{i}. Persona Class: {surface.persona_class}")
        print(f"   Deepest Step: {surface.deepest_step_id[:50]}")
        print(f"   Step Index: {surface.deepest_step_index}")
        print(f"   Traces Reaching Step: {surface.traces_reaching_step}")
        print(f"   Traces Completing Funnel: {surface.traces_completing_funnel}")
        print()
    
    print("=" * 80)
    print("QUERY DEMONSTRATION COMPLETE")
    print("=" * 80)
    print()
    print("All queries are decision-first (not analytics-style):")
    print("  ✓ No global drop rates or funnel percentages")
    print("  ✓ No monocausal explanations")
    print("  ✓ All insights are precedent-based")
    print("  ✓ Counterexamples included to prevent monocausal claims")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())


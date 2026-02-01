#!/usr/bin/env python3
"""
Generate Trial1 Decision Ledger

Produces audit-grade, interpretation-free decision ledger.
"""

import json
import sys
from decision_graph.decision_trace import DecisionTrace, DecisionSequence, DecisionOutcome
from decision_graph.decision_ledger import generate_decision_ledger
from decision_graph.ledger_formatter import format_decision_ledger_as_text


def load_sequences_from_result(result_file: str):
    """Load decision sequences from pipeline result file."""
    with open(result_file, 'r') as f:
        data = json.load(f)
    
    traces_data = data.get('decision_traces', [])
    if not traces_data:
        return [], {}
    
    # Get step list from traces
    step_ids_dict = {}
    for trace_dict in traces_data:
        step_id = trace_dict.get('step_id', '')
        step_idx = trace_dict.get('step_index', -1)
        if step_id and step_idx >= 0:
            step_ids_dict[step_id] = step_idx
    
    product_steps = {step_id: {} for step_id, _ in sorted(step_ids_dict.items(), key=lambda x: x[1])}
    
    # Build sequences
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
    result_file = 'output/trial1_pipeline_result.json'
    
    print(f"Loading pipeline result: {result_file}")
    sequences, product_steps = load_sequences_from_result(result_file)
    
    if not sequences:
        print("No sequences found. Please run the pipeline first.")
        return
    
    print(f"Loaded {len(sequences)} decision sequences")
    
    # Generate ledger
    print("Generating decision ledger...")
    ledger_data = generate_decision_ledger(sequences, product_steps)
    
    # Save JSON
    json_file = 'trial1_decision_ledger.json'
    with open(json_file, 'w') as f:
        json.dump(ledger_data, f, indent=2)
    print(f"✓ Saved: {json_file}")
    
    # Generate formatted text
    text_file = 'trial1_decision_ledger.txt'
    formatted_text = format_decision_ledger_as_text(ledger_data)
    with open(text_file, 'w') as f:
        f.write(formatted_text)
    print(f"✓ Saved: {text_file}")
    
    # Print summary
    print(f"\nLedger Summary:")
    print(f"  Decision Boundaries: {len(ledger_data.get('decision_boundaries', []))}")
    print(f"  Acceptance Precedents: {len(ledger_data.get('precedents_acceptance', []))}")
    print(f"  Rejection Precedents: {len(ledger_data.get('precedents_rejection', []))}")
    print(f"  Termination Points: {len(ledger_data.get('decision_termination_points', []))}")


if __name__ == '__main__':
    main()

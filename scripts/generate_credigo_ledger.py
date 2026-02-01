#!/usr/bin/env python3
import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

"""
Generate Credigo Decision Ledger

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
    result_file = 'output/credigo_pipeline_result.json'
    
    print("Loading decision sequences...")
    sequences, product_steps = load_sequences_from_result(result_file)
    print(f"Loaded {len(sequences)} sequences")
    print(f"Product steps: {len(product_steps)}")
    print()
    
    print("Generating decision ledger...")
    ledger_data = generate_decision_ledger(sequences, product_steps)
    
    # Export JSON
    json_file = 'credigo_decision_ledger.json'
    with open(json_file, 'w') as f:
        json.dump(ledger_data, f, indent=2)
    print(f"✓ Ledger exported to: {json_file}")
    
    # Export text format
    text_file = 'credigo_decision_ledger.txt'
    ledger_text = format_decision_ledger_as_text(ledger_data)
    with open(text_file, 'w') as f:
        f.write(ledger_text)
    print(f"✓ Ledger text exported to: {text_file}")
    
    # Print summary (factual only)
    print()
    print("=" * 80)
    print("LEDGER GENERATION COMPLETE")
    print("=" * 80)
    print(f"Decision Boundary Assertions: {len(ledger_data['decision_boundaries'])}")
    print(f"Precedent Assertions: {len(ledger_data['precedents'])}")
    print(f"Decision Density Assertions: {len(ledger_data['decision_density'])}")
    print()
    print("Output is audit-grade and interpretation-free.")
    print("All assertions are machine-verifiable facts from DecisionTrace objects.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())


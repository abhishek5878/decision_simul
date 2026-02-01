#!/usr/bin/env python3
"""
Generate attribution summary for Credigo simulation results.
"""

import json
from collections import defaultdict
from decision_attribution.attribution_utils import format_attribution_summary

def load_traces(filepath: str):
    """Load decision traces from pipeline result."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Convert dict traces to DecisionTrace objects if needed
    traces_dict = data.get('decision_traces', [])
    return traces_dict

def aggregate_step_attribution_summary(traces_dict: list, decision: str = "DROP"):
    """
    Aggregate attribution by step for a specific decision type.
    
    Returns dict mapping step_id to formatted summary string.
    """
    step_attributions = defaultdict(list)
    
    for trace in traces_dict:
        if trace.get('decision') == decision and trace.get('attribution'):
            step_id = trace['step_id']
            attr = trace['attribution']
            if attr.get('shap_values'):
                step_attributions[step_id].append(attr['shap_values'])
    
    summaries = {}
    for step_id, attrs in step_attributions.items():
        if not attrs:
            continue
        
        # Average SHAP values for this step
        avg_shap = defaultdict(float)
        for attr_dict in attrs:
            for force, value in attr_dict.items():
                avg_shap[force] += abs(value)  # Use absolute value
        
        n = len(attrs)
        avg_shap = {k: v/n for k, v in avg_shap.items()}
        
        # Normalize to percentages
        total = sum(avg_shap.values())
        if total > 0:
            avg_shap_pct = {k: (v/total)*100 for k, v in avg_shap.items()}
            summaries[step_id] = avg_shap_pct
    
    return summaries

def main():
    print("=" * 80)
    print("CREDIGO DECISION ATTRIBUTION SUMMARY")
    print("=" * 80)
    print()
    
    # Load traces
    traces = load_traces('credigo_pipeline_result.json')
    print(f"Total traces: {len(traces)}")
    
    traces_with_attr = [t for t in traces if t.get('attribution')]
    print(f"Traces with attribution: {len(traces_with_attr)}/{len(traces)}")
    print()
    
    # Aggregate by step for DROP decisions
    print("=" * 80)
    print("ATTRIBUTION BY STEP (DROP Decisions)")
    print("=" * 80)
    print()
    
    summaries = aggregate_step_attribution_summary(traces, decision="DROP")
    
    for step_id in sorted(summaries.keys()):
        shap_pct = summaries[step_id]
        sorted_forces = sorted(shap_pct.items(), key=lambda x: x[1], reverse=True)
        
        print(f"{step_id}:")
        print(f"  At {step_id}, ", end="")
        parts = []
        for force, pct in sorted_forces[:3]:
            parts.append(f"{force} explains {pct:.0f}% of rejection pressure")
        print(", ".join(parts))
        print()
    
    # Overall summary
    print("=" * 80)
    print("OVERALL ATTRIBUTION PATTERNS")
    print("=" * 80)
    print()
    
    all_attrs = defaultdict(float)
    count = 0
    for trace in traces:
        if trace.get('decision') == 'DROP' and trace.get('attribution'):
            attr = trace['attribution']
            if attr.get('shap_values'):
                for force, value in attr['shap_values'].items():
                    all_attrs[force] += abs(value)
                count += 1
    
    if count > 0:
        avg_attrs = {k: v/count for k, v in all_attrs.items()}
        total = sum(avg_attrs.values())
        if total > 0:
            avg_attrs_pct = {k: (v/total)*100 for k, v in avg_attrs.items()}
            sorted_forces = sorted(avg_attrs_pct.items(), key=lambda x: x[1], reverse=True)
            
            print("Across all DROP decisions:")
            for force, pct in sorted_forces[:5]:
                print(f"  {force}: {pct:.1f}%")
    
    print()
    print("=" * 80)

if __name__ == "__main__":
    main()


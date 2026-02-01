#!/usr/bin/env python3
"""
Deep attribution analysis for Blink Money.
"""

import json
import sys
from collections import defaultdict
import numpy as np

# Import analysis functions
sys.path.insert(0, '.')
from deep_attribution_analysis import (
    load_traces,
    analyze_continue_vs_drop_patterns,
    analyze_step_fragility,
    analyze_force_transitions,
    analyze_force_interactions,
    analyze_progression_patterns
)

def main():
    print("=" * 80)
    print("BLINK MONEY DEEP ATTRIBUTION ANALYSIS")
    print("=" * 80)
    print()
    
    # Load traces
    traces = load_traces('blink_money_pipeline_result.json')
    print(f"Total traces: {len(traces):,}")
    traces_with_attr = sum(1 for t in traces if t.get('attribution'))
    print(f"Traces with attribution: {traces_with_attr:,}/{len(traces):,}")
    print()
    
    # 1. CONTINUE vs DROP patterns
    print("=" * 80)
    print("1. CONTINUE vs DROP: What Forces Drive Success vs Failure?")
    print("=" * 80)
    print()
    
    continue_drop = analyze_continue_vs_drop_patterns(traces)
    
    print("DROP Decisions - Force Contribution (%):")
    for force, pct in sorted(continue_drop['drop_percentages'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {force:20s}: {pct:5.1f}%")
    print()
    
    # 2. Step fragility
    print("=" * 80)
    print("2. Step Fragility: Which Steps Are Most Fragile?")
    print("=" * 80)
    print()
    
    fragility = analyze_step_fragility(traces)
    sorted_fragility = sorted(fragility.items(), key=lambda x: x[1]['drop_rate'], reverse=True)
    
    print("Steps ranked by drop rate:")
    for step_id, stats in sorted_fragility:
        print(f"\n{step_id}:")
        print(f"  Drop rate: {stats['drop_rate']:.1%} ({stats['drop_count']}/{stats['total']})")
        if stats['dominant_force']:
            print(f"  Dominant force: {stats['dominant_force']} ({stats['dominant_force_pct']:.1f}% of drops)")
    print()
    
    # 3. Force transitions
    print("=" * 80)
    print("3. Force Transitions: How Do Forces Change Through the Funnel?")
    print("=" * 80)
    print()
    
    transitions = analyze_force_transitions(traces)
    
    print("Force dominance by step (for DROP decisions):")
    for step_idx in sorted(transitions.keys()):
        trans = transitions[step_idx]
        print(f"\nStep {step_idx}: {trans['step_id']}")
        print(f"  Drops: {trans['drop_count']}")
        print(f"  Dominant force: {trans['dominant_force']} ({trans['dominant_pct']:.1f}%)")
        print(f"  Top 3 forces:")
        sorted_forces = sorted(trans['all_forces'].items(), key=lambda x: x[1], reverse=True)
        for force, pct in sorted_forces[:3]:
            print(f"    {force}: {pct:.1f}%")
    print()
    
    # 4. Force interactions
    print("=" * 80)
    print("4. Force Interactions: Which Forces Co-Occur?")
    print("=" * 80)
    print()
    
    interactions = analyze_force_interactions(traces)
    
    print("Top force pairs in DROP decisions:")
    for pair, count in list(interactions['pairs'].items())[:5]:
        print(f"  {pair[0]} + {pair[1]}: {count} occurrences")
    print()
    
    print("=" * 80)
    
    return traces

if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
Deep attribution analysis - extracting actionable insights from decision attribution data.
"""

import json
from collections import defaultdict
import numpy as np
from typing import Dict, List, Tuple

def load_traces(filepath: str) -> List[Dict]:
    """Load decision traces from pipeline result."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data.get('decision_traces', [])

def analyze_force_transitions(traces: List[Dict]) -> Dict:
    """
    Analyze how force dominance changes as users progress through steps.
    """
    # Group traces by step index
    step_traces = defaultdict(lambda: {'continue': [], 'drop': []})
    
    for trace in traces:
        if trace.get('attribution'):
            step_index = trace.get('step_index', 0)
            decision = trace['decision']
            step_traces[step_index][decision.lower()].append(trace)
    
    transitions = {}
    for step_idx in sorted(step_traces.keys()):
        drop_traces = step_traces[step_idx]['drop']
        if not drop_traces:
            continue
        
        # Aggregate forces for drops at this step
        force_sums = defaultdict(float)
        for trace in drop_traces:
            attr = trace['attribution']
            shap = attr.get('shap_values', {})
            for force, value in shap.items():
                force_sums[force] += abs(value)
        
        n = len(drop_traces)
        if n > 0:
            force_avg = {k: v/n for k, v in force_sums.items()}
            total = sum(force_avg.values())
            if total > 0:
                force_pct = {k: (v/total)*100 for k, v in force_avg.items()}
                dominant = max(force_pct.items(), key=lambda x: x[1])
                transitions[step_idx] = {
                    'dominant_force': dominant[0],
                    'dominant_pct': dominant[1],
                    'all_forces': force_pct,
                    'step_id': drop_traces[0]['step_id'],
                    'drop_count': n
                }
    
    return transitions

def analyze_continue_vs_drop_patterns(traces: List[Dict]) -> Dict:
    """
    Compare what forces drive CONTINUE vs DROP decisions.
    """
    continue_forces = defaultdict(list)
    drop_forces = defaultdict(list)
    
    for trace in traces:
        if trace.get('attribution'):
            attr = trace['attribution']
            shap = attr.get('shap_values', {})
            decision = trace['decision']
            
            if decision == 'CONTINUE':
                for force, value in shap.items():
                    continue_forces[force].append(value)
            else:
                for force, value in shap.items():
                    drop_forces[force].append(abs(value))  # Use absolute for drops
    
    # Compute statistics
    continue_stats = {}
    for force, values in continue_forces.items():
        continue_stats[force] = {
            'mean': np.mean(values),
            'std': np.std(values),
            'median': np.median(values)
        }
    
    drop_stats = {}
    for force, values in drop_forces.items():
        drop_stats[force] = {
            'mean': np.mean(values),
            'std': np.std(values),
            'median': np.median(values),
            'total': np.sum(values)
        }
    
    # Normalize drop forces to percentages
    drop_total = sum(stats['total'] for stats in drop_stats.values())
    if drop_total > 0:
        drop_pct = {
            force: (stats['total']/drop_total)*100
            for force, stats in drop_stats.items()
        }
    else:
        drop_pct = {}
    
    return {
        'continue': continue_stats,
        'drop': drop_stats,
        'drop_percentages': drop_pct
    }

def analyze_step_fragility(traces: List[Dict]) -> Dict:
    """
    Identify which steps are most fragile (most drops) and what drives them.
    """
    step_drops = defaultdict(list)
    step_continues = defaultdict(list)
    
    for trace in traces:
        step_id = trace['step_id']
        if trace.get('attribution'):
            decision = trace['decision']
            if decision == 'DROP':
                step_drops[step_id].append(trace)
            else:
                step_continues[step_id].append(trace)
    
    fragility = {}
    for step_id in set(list(step_drops.keys()) + list(step_continues.keys())):
        drops = step_drops[step_id]
        continues = step_continues[step_id]
        total = len(drops) + len(continues)
        
        if total > 0:
            drop_rate = len(drops) / total
            
            # Get dominant force for drops at this step
            dominant_force = None
            dominant_pct = 0.0
            if drops:
                force_sums = defaultdict(float)
                for trace in drops:
                    attr = trace['attribution']
                    shap = attr.get('shap_values', {})
                    for force, value in shap.items():
                        force_sums[force] += abs(value)
                
                n = len(drops)
                force_avg = {k: v/n for k, v in force_sums.items()}
                total_force = sum(force_avg.values())
                if total_force > 0:
                    force_pct = {k: (v/total_force)*100 for k, v in force_avg.items()}
                    dominant_force, dominant_pct = max(force_pct.items(), key=lambda x: x[1])
            
            fragility[step_id] = {
                'drop_rate': drop_rate,
                'drop_count': len(drops),
                'continue_count': len(continues),
                'total': total,
                'dominant_force': dominant_force,
                'dominant_force_pct': dominant_pct
            }
    
    return fragility

def analyze_force_interactions(traces: List[Dict]) -> Dict:
    """
    Analyze which forces co-occur in drop decisions.
    """
    # For each drop trace, identify top 2 forces
    force_pairs = defaultdict(int)
    force_triplets = defaultdict(int)
    
    for trace in traces:
        if trace.get('decision') == 'DROP' and trace.get('attribution'):
            attr = trace['attribution']
            shap = attr.get('shap_values', {})
            
            # Get absolute values and sort
            forces_sorted = sorted(
                [(force, abs(value)) for force, value in shap.items()],
                key=lambda x: x[1],
                reverse=True
            )
            
            # Top 2 forces
            if len(forces_sorted) >= 2:
                top2 = tuple(sorted([forces_sorted[0][0], forces_sorted[1][0]]))
                force_pairs[top2] += 1
            
            # Top 3 forces
            if len(forces_sorted) >= 3:
                top3 = tuple(sorted([forces_sorted[0][0], forces_sorted[1][0], forces_sorted[2][0]]))
                force_triplets[top3] += 1
    
    return {
        'pairs': dict(sorted(force_pairs.items(), key=lambda x: x[1], reverse=True)[:10]),
        'triplets': dict(sorted(force_triplets.items(), key=lambda x: x[1], reverse=True)[:10])
    }

def analyze_progression_patterns(traces: List[Dict]) -> Dict:
    """
    Analyze how attribution changes as users progress through the funnel.
    """
    # Group by step index
    step_attributions = defaultdict(lambda: {'drops': [], 'continues': []})
    
    for trace in traces:
        if trace.get('attribution'):
            step_idx = trace.get('step_index', 0)
            decision = trace['decision']
            step_attributions[step_idx][decision.lower() + 's'].append(trace)
    
    progression = {}
    for step_idx in sorted(step_attributions.keys()):
        drops = step_attributions[step_idx]['drops']
        if drops:
            # Aggregate forces
            force_sums = defaultdict(float)
            for trace in drops:
                attr = trace['attribution']
                shap = attr.get('shap_values', {})
                for force, value in shap.items():
                    force_sums[force] += abs(value)
            
            n = len(drops)
            force_avg = {k: v/n for k, v in force_sums.items()}
            total = sum(force_avg.values())
            if total > 0:
                force_pct = {k: (v/total)*100 for k, v in force_avg.items()}
                progression[step_idx] = {
                    'step_id': drops[0]['step_id'],
                    'drop_count': n,
                    'forces': force_pct,
                    'dominant': max(force_pct.items(), key=lambda x: x[1])
                }
    
    return progression

def main():
    print("=" * 80)
    print("DEEP ATTRIBUTION ANALYSIS")
    print("=" * 80)
    print()
    
    # Load traces
    traces = load_traces('credigo_pipeline_result.json')
    print(f"Total traces: {len(traces):,}")
    print(f"Traces with attribution: {sum(1 for t in traces if t.get('attribution')):,}")
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
    
    # 2. Step fragility analysis
    print("=" * 80)
    print("2. Step Fragility: Which Steps Are Most Fragile?")
    print("=" * 80)
    print()
    
    fragility = analyze_step_fragility(traces)
    
    # Sort by drop rate
    sorted_fragility = sorted(fragility.items(), key=lambda x: x[1]['drop_rate'], reverse=True)
    
    print("Steps ranked by drop rate:")
    for step_id, stats in sorted_fragility[:10]:
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
    
    print("Top force triplets in DROP decisions:")
    for triplet, count in list(interactions['triplets'].items())[:5]:
        print(f"  {triplet[0]} + {triplet[1]} + {triplet[2]}: {count} occurrences")
    print()
    
    # 5. Progression patterns
    print("=" * 80)
    print("5. Funnel Progression: How Do Forces Evolve?")
    print("=" * 80)
    print()
    
    progression = analyze_progression_patterns(traces)
    
    print("Force evolution through funnel (DROP decisions):")
    print("\nEarly Funnel (Steps 0-3):")
    for step_idx in [0, 1, 2, 3]:
        if step_idx in progression:
            prog = progression[step_idx]
            print(f"  Step {step_idx} ({prog['step_id'][:40]}...):")
            print(f"    Dominant: {prog['dominant'][0]} ({prog['dominant'][1]:.1f}%)")
            print(f"    Drops: {prog['drop_count']}")
    
    print("\nMid Funnel (Steps 4-7):")
    for step_idx in [4, 5, 6, 7]:
        if step_idx in progression:
            prog = progression[step_idx]
            print(f"  Step {step_idx} ({prog['step_id'][:40]}...):")
            print(f"    Dominant: {prog['dominant'][0]} ({prog['dominant'][1]:.1f}%)")
            print(f"    Drops: {prog['drop_count']}")
    
    print("\nLate Funnel (Steps 8+):")
    for step_idx in sorted([k for k in progression.keys() if k >= 8]):
        prog = progression[step_idx]
        print(f"  Step {step_idx} ({prog['step_id'][:40]}...):")
        print(f"    Dominant: {prog['dominant'][0]} ({prog['dominant'][1]:.1f}%)")
        print(f"    Drops: {prog['drop_count']}")
    
    print()
    print("=" * 80)
    
    # Save detailed results (convert tuples to strings for JSON)
    results = {
        'continue_vs_drop': continue_drop,
        'fragility': fragility,
        'transitions': transitions,
        'interactions': {
            'pairs': {str(k): v for k, v in interactions['pairs'].items()},
            'triplets': {str(k): v for k, v in interactions['triplets'].items()}
        },
        'progression': progression
    }
    
    with open('credigo_deep_attribution_analysis.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print("\n✅ Detailed analysis saved to: credigo_deep_attribution_analysis.json")
    print("=" * 80)

if __name__ == "__main__":
    main()


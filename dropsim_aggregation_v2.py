"""
dropsim_aggregation_v2.py - New Aggregation Format

Focuses on:
- Earliest failure step per variant
- Dominant failure reason per step
- Consistency across variants
- Interpretation (structural flaw vs intent-sensitive vs fatigue-sensitive)
"""

import pandas as pd
from typing import Dict, List, Optional
from collections import Counter, defaultdict
from behavioral_engine import FailureReason


def aggregate_simulation_results(
    result_df: pd.DataFrame,
    product_steps: Dict,
    verbose: bool = True
) -> Dict:
    """
    Aggregate results in the new format:
    - Earliest failure step per variant
    - Dominant failure reason per step
    - Consistency across variants
    - Interpretation
    
    Args:
        result_df: DataFrame with simulation results (one row per persona)
        product_steps: Dict of product steps keyed by step name
        verbose: Print results
    
    Returns:
        Dict with aggregated results and interpretations
    """
    # Get step names in order
    step_names = list(product_steps.keys())
    
    # Track failures per step
    step_failures = defaultdict(lambda: {
        'variants': [],
        'reasons': Counter(),
        'personas': set()
    })
    
    # Track per-persona patterns
    persona_patterns = []
    
    for idx, row in result_df.iterrows():
        trajectories = row.get('trajectories', [])
        if not trajectories:
            continue
        
        # Find earliest failure step across all variants for this persona
        earliest_failures = []
        variant_failures = {}
        
        for traj in trajectories:
            exit_step = traj.get('exit_step')
            failure_reason = traj.get('failure_reason')
            variant = traj.get('variant')
            
            if exit_step and exit_step != 'Completed':
                # Find step index
                try:
                    step_idx = step_names.index(exit_step)
                except ValueError:
                    step_idx = len(step_names)  # Unknown step, treat as last
                
                earliest_failures.append((step_idx, exit_step, failure_reason, variant))
                variant_failures[variant] = (exit_step, failure_reason)
                
                # Track in step_failures
                step_failures[exit_step]['variants'].append(variant)
                step_failures[exit_step]['personas'].add(idx)
                if failure_reason:
                    step_failures[exit_step]['reasons'][failure_reason] += 1
        
        # Earliest failure for this persona
        if earliest_failures:
            earliest_failures.sort(key=lambda x: x[0])  # Sort by step index
            earliest_step_idx, earliest_step, earliest_reason, earliest_variant = earliest_failures[0]
        else:
            earliest_step = "Completed"
            earliest_reason = None
            earliest_variant = None
        
        # Consistency: how many variants fail at the same step?
        if variant_failures:
            exit_steps = [v[0] for v in variant_failures.values()]
            exit_counter = Counter(exit_steps)
            most_common_exit = exit_counter.most_common(1)[0]
            consistency = most_common_exit[1] / len(trajectories)
        else:
            consistency = 1.0  # All completed
            most_common_exit = ("Completed", len(trajectories))
        
        persona_patterns.append({
            'persona_name': row.get('persona_name', f'Persona_{idx}'),
            'earliest_failure_step': earliest_step,
            'earliest_failure_reason': earliest_reason,
            'earliest_failure_variant': earliest_variant,
            'most_common_exit_step': most_common_exit[0],
            'consistency': consistency,
            'variant_failures': variant_failures,
            'total_variants': len(trajectories),
            'completed_variants': sum(1 for t in trajectories if t.get('exit_step') == 'Completed' or not t.get('exit_step'))
        })
    
    # Aggregate per step
    step_summary = {}
    for step_name in step_names:
        failures = step_failures[step_name]
        total_variants = sum(len(row.get('trajectories', [])) for _, row in result_df.iterrows())
        failure_count = len(failures['variants'])
        failure_rate = (failure_count / total_variants * 100) if total_variants > 0 else 0
        
        # Dominant failure reason
        reasons = failures['reasons']
        dominant_reason = reasons.most_common(1)[0] if reasons else (None, 0)
        secondary_reason = reasons.most_common(2)[1] if len(reasons) > 1 else None
        
        step_summary[step_name] = {
            'failure_count': failure_count,
            'failure_rate': failure_rate,
            'persona_count': len(failures['personas']),
            'dominant_reason': dominant_reason[0] if dominant_reason[0] else None,
            'dominant_reason_count': dominant_reason[1],
            'secondary_reason': secondary_reason[0] if secondary_reason else None,
            'secondary_reason_count': secondary_reason[1] if secondary_reason else 0
        }
    
    # Interpretation: Analyze patterns
    interpretations = interpret_failure_patterns(persona_patterns, step_summary, step_names)
    
    return {
        'step_summary': step_summary,
        'persona_patterns': persona_patterns,
        'interpretations': interpretations,
        'total_personas': len(result_df),
        'total_variants': sum(len(row.get('trajectories', [])) for _, row in result_df.iterrows())
    }


def interpret_failure_patterns(
    persona_patterns: List[Dict],
    step_summary: Dict,
    step_names: List[str]
) -> Dict:
    """
    Interpret failure patterns:
    - Structural product flaw (most variants fail at same step)
    - Intent-sensitive (variants fail at different steps)
    - Fatigue-sensitive (only low-energy variants fail)
    
    Returns:
        Dict with interpretations
    """
    interpretations = {
        'structural_flaws': [],  # Steps where most personas fail consistently
        'intent_sensitive_steps': [],  # Steps where failure varies by variant
        'fatigue_sensitive_steps': [],  # Steps where only low-energy variants fail
        'overall_pattern': None
    }
    
    # Analyze each step
    for step_name in step_names:
        step_data = step_summary[step_name]
        
        # Get personas that fail at this step
        failing_personas = [
            p for p in persona_patterns
            if p['most_common_exit_step'] == step_name
        ]
        
        if not failing_personas:
            continue
        
        # Calculate consistency
        avg_consistency = sum(p['consistency'] for p in failing_personas) / len(failing_personas) if failing_personas else 0
        
        # Structural flaw: high consistency (≥70% of variants fail at same step)
        if avg_consistency >= 0.7:
            interpretations['structural_flaws'].append({
                'step': step_name,
                'persona_count': len(failing_personas),
                'avg_consistency': avg_consistency,
                'dominant_reason': step_data['dominant_reason'],
                'interpretation': f"Structural product flaw: {len(failing_personas)} personas consistently fail at '{step_name}' ({avg_consistency*100:.1f}% consistency). This suggests a fundamental issue with this step, not just user intent."
            })
        
        # Intent-sensitive: low consistency (variants fail at different steps)
        elif avg_consistency < 0.5:
            interpretations['intent_sensitive_steps'].append({
                'step': step_name,
                'persona_count': len(failing_personas),
                'avg_consistency': avg_consistency,
                'interpretation': f"Intent-sensitive: {len(failing_personas)} personas fail at '{step_name}' but with low consistency ({avg_consistency*100:.1f}%). Failure depends on user's arrival state (motivation, energy), not just the step itself."
            })
        
        # Fatigue-sensitive: check if only low-energy variants fail
        # (This requires checking variant names - low energy variants like "tired_commuter")
        low_energy_variants = ['tired_commuter', 'low_energy_high_intent', 'browsing_casually']
        fatigue_only_failures = 0
        total_failures = 0
        
        for persona in failing_personas:
            variant_failures = persona.get('variant_failures', {})
            for variant, (exit_step, reason) in variant_failures.items():
                if exit_step == step_name:
                    total_failures += 1
                    if variant in low_energy_variants:
                        fatigue_only_failures += 1
        
        if total_failures > 0 and (fatigue_only_failures / total_failures) >= 0.7:
            interpretations['fatigue_sensitive_steps'].append({
                'step': step_name,
                'fatigue_failure_rate': fatigue_only_failures / total_failures,
                'interpretation': f"Fatigue-sensitive: '{step_name}' fails primarily for low-energy variants ({fatigue_only_failures}/{total_failures} = {fatigue_only_failures/total_failures*100:.1f}%). This step is cognitively demanding and fails when users arrive tired."
            })
    
    # Overall pattern
    if interpretations['structural_flaws']:
        interpretations['overall_pattern'] = "Structural product flaws detected. Most failures are consistent across variants, suggesting fundamental issues with specific steps rather than user intent."
    elif interpretations['intent_sensitive_steps']:
        interpretations['overall_pattern'] = "Intent-sensitive pattern. Failures vary by user's arrival state (motivation, energy), suggesting the product flow is sensitive to user context."
    elif interpretations['fatigue_sensitive_steps']:
        interpretations['overall_pattern'] = "Fatigue-sensitive pattern. Failures occur primarily when users arrive with low cognitive energy, suggesting high cognitive demand in the flow."
    else:
        interpretations['overall_pattern'] = "Mixed pattern. Failures are distributed across steps and variants without a clear dominant pattern."
    
    return interpretations


def format_aggregated_results(aggregated: Dict, verbose: bool = True) -> str:
    """
    Format aggregated results in the new format.
    
    Returns:
        Formatted string report
    """
    lines = []
    lines.append("=" * 80)
    lines.append("📊 DROPSIM AGGREGATION RESULTS")
    lines.append("=" * 80)
    lines.append("")
    
    # Step-level summary
    lines.append("## STEP-LEVEL FAILURE ANALYSIS")
    lines.append("-" * 80)
    
    step_summary = aggregated['step_summary']
    for step_name, data in step_summary.items():
        lines.append(f"\n{step_name}:")
        lines.append(f"  Fails for: {data['failure_count']} variants ({data['failure_rate']:.1f}%)")
        lines.append(f"  Affects: {data['persona_count']} personas")
        if data['dominant_reason']:
            lines.append(f"  Dominant failure reason: {data['dominant_reason']} ({data['dominant_reason_count']} variants)")
        if data['secondary_reason']:
            lines.append(f"  Secondary failure reason: {data['secondary_reason']} ({data['secondary_reason_count']} variants)")
    
    lines.append("")
    lines.append("-" * 80)
    
    # Interpretations
    interpretations = aggregated['interpretations']
    lines.append("\n## INTERPRETATION")
    lines.append("-" * 80)
    
    if interpretations['structural_flaws']:
        lines.append("\n🔴 STRUCTURAL PRODUCT FLAWS:")
        for flaw in interpretations['structural_flaws']:
            lines.append(f"  • {flaw['interpretation']}")
    
    if interpretations['intent_sensitive_steps']:
        lines.append("\n🟡 INTENT-SENSITIVE STEPS:")
        for step in interpretations['intent_sensitive_steps']:
            lines.append(f"  • {step['interpretation']}")
    
    if interpretations['fatigue_sensitive_steps']:
        lines.append("\n🟠 FATIGUE-SENSITIVE STEPS:")
        for step in interpretations['fatigue_sensitive_steps']:
            lines.append(f"  • {step['interpretation']}")
    
    lines.append(f"\n📋 OVERALL PATTERN:")
    lines.append(f"  {interpretations['overall_pattern']}")
    
    lines.append("")
    lines.append("=" * 80)
    
    return "\n".join(lines)


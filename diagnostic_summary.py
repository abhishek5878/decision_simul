"""
Diagnostic Summary Generator - Analyzes simulation runs for health and explainability.
"""

import json
from typing import Dict, List, Optional
from collections import Counter, defaultdict
import numpy as np


def generate_diagnostic_summary(
    result_df,
    product_steps: Dict,
    output_path: Optional[str] = None
) -> Dict:
    """
    Generate comprehensive diagnostic summary for a simulation run.
    
    Returns:
        {
            "avg_completion_prob": 0.27,
            "largest_penalty": "semantic_mismatch",
            "dominant_drop_step": "step_3",
            "probability_health": "OK",
            "explanation": "...",
            ...
        }
    """
    # Collect all probability traces
    all_traces = []
    step_probabilities = defaultdict(list)
    step_penalties = defaultdict(list)
    step_amplifiers = defaultdict(list)
    
    completion_probs = []
    drop_steps = []
    failure_reasons = []
    
    for _, row in result_df.iterrows():
        for traj in row['trajectories']:
            journey = traj.get('journey', [])
            completed = traj.get('completed', False)
            
            if completed:
                completion_probs.append(1.0)
            else:
                completion_probs.append(0.0)
                drop_steps.append(traj.get('exit_step', 'Unknown'))
                failure_reasons.append(traj.get('failure_reason', 'Unknown'))
            
            # Extract probability traces
            for step_data in journey:
                step_name = step_data.get('step', 'Unknown')
                trace = step_data.get('probability_trace')
                
                if trace:
                    all_traces.append(trace)
                    step_probabilities[step_name].append(trace.get('final_probability', 0.5))
                    
                    # Extract penalties
                    penalties = trace.get('penalties', {})
                    for penalty_type, penalty_value in penalties.items():
                        step_penalties[step_name].append(abs(penalty_value))
                    
                    # Extract amplifiers
                    amplifiers = trace.get('amplifiers', {})
                    for amp_type, amp_value in amplifiers.items():
                        step_amplifiers[step_name].append(amp_value)
    
    # Calculate metrics
    avg_completion_prob = np.mean(completion_probs) if completion_probs else 0.0
    
    # Find largest penalty type
    penalty_totals = defaultdict(float)
    for trace in all_traces:
        penalties = trace.get('penalties', {})
        for penalty_type, penalty_value in penalties.items():
            penalty_totals[penalty_type] += abs(penalty_value)
    
    largest_penalty = max(penalty_totals.items(), key=lambda x: x[1])[0] if penalty_totals else "none"
    
    # Find dominant drop step
    drop_step_counts = Counter(drop_steps)
    dominant_drop_step = drop_step_counts.most_common(1)[0][0] if drop_step_counts else "none"
    
    # Assess probability health
    avg_probs_by_step = {
        step: np.mean(probs) if probs else 0.0
        for step, probs in step_probabilities.items()
    }
    
    min_prob = min(avg_probs_by_step.values()) if avg_probs_by_step else 0.0
    max_prob = max(avg_probs_by_step.values()) if avg_probs_by_step else 0.0
    
    if min_prob < 0.1:
        health = "CRITICAL - Probabilities collapsing"
    elif min_prob < 0.2:
        health = "WARNING - Low probabilities detected"
    elif avg_completion_prob < 0.05:
        health = "WARNING - Very low completion rate"
    elif avg_completion_prob > 0.5:
        health = "WARNING - Unusually high completion rate"
    else:
        health = "OK"
    
    # Generate explanation
    explanation_parts = []
    
    if avg_completion_prob < 0.1:
        explanation_parts.append(f"Completion rate is critically low ({avg_completion_prob:.1%}).")
    
    if min_prob < 0.15:
        worst_step = min(avg_probs_by_step.items(), key=lambda x: x[1])[0]
        explanation_parts.append(f"Step '{worst_step}' has very low continuation probability ({min_prob:.1%}).")
    
    if largest_penalty != "none":
        penalty_total = penalty_totals[largest_penalty]
        explanation_parts.append(f"Largest penalty source: {largest_penalty} (total impact: {penalty_total:.2f}).")
    
    if dominant_drop_step != "none" and dominant_drop_step != "Completed":
        drop_count = drop_step_counts[dominant_drop_step]
        explanation_parts.append(f"Most users drop at: {dominant_drop_step} ({drop_count} trajectories).")
    
    # Failure reason distribution
    failure_reason_counts = Counter(failure_reasons)
    dominant_failure = failure_reason_counts.most_common(1)[0] if failure_reason_counts else "none"
    
    explanation = " ".join(explanation_parts) if explanation_parts else "Simulation appears healthy."
    
    summary = {
        "avg_completion_prob": round(avg_completion_prob, 3),
        "completion_rate": round(avg_completion_prob, 3),
        "largest_penalty": largest_penalty,
        "penalty_totals": {k: round(v, 3) for k, v in penalty_totals.items()},
        "dominant_drop_step": dominant_drop_step,
        "drop_step_distribution": dict(drop_step_counts),
        "dominant_failure_reason": dominant_failure,
        "failure_reason_distribution": dict(failure_reason_counts),
        "probability_health": health,
        "min_probability": round(min_prob, 3),
        "max_probability": round(max_prob, 3),
        "avg_probability_by_step": {k: round(v, 3) for k, v in avg_probs_by_step.items()},
        "explanation": explanation,
        "total_trajectories": len(completion_probs),
        "completed_trajectories": sum(completion_probs),
        "diagnostic_timestamp": None  # Will be set by caller
    }
    
    if output_path:
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
    
    return summary


def explain_probability_collapse(summary: Dict) -> str:
    """
    Generate plain-language explanation of why completion is near-zero.
    
    Design Rule: If system predicts near-zero completion, it must explain why.
    """
    if summary['completion_rate'] > 0.05:
        return f"Completion rate is {summary['completion_rate']:.1%}, which is above the critical threshold."
    
    explanation = f"Completion rate is critically low ({summary['completion_rate']:.1%}). "
    
    # Check penalties
    if summary['largest_penalty'] != "none":
        penalty_total = summary['penalty_totals'].get(summary['largest_penalty'], 0)
        explanation += f"The primary issue is {summary['largest_penalty']} (total impact: {penalty_total:.2f}). "
    
    # Check drop step
    if summary['dominant_drop_step'] != "none" and summary['dominant_drop_step'] != "Completed":
        drop_count = summary['drop_step_distribution'].get(summary['dominant_drop_step'], 0)
        total = summary['total_trajectories']
        pct = (drop_count / total * 100) if total > 0 else 0
        explanation += f"{pct:.1f}% of users drop at '{summary['dominant_drop_step']}'. "
    
    # Check failure reason
    if summary['dominant_failure_reason'] != "none":
        explanation += f"Primary failure reason: {summary['dominant_failure_reason']}. "
    
    # Check probability health
    if summary['probability_health'] == "CRITICAL":
        min_prob = summary['min_probability']
        explanation += f"Minimum continuation probability is {min_prob:.1%}, which is below the safe threshold (20%). "
        explanation += "This suggests penalties are overwhelming amplifiers, or base values are too low."
    
    return explanation.strip()


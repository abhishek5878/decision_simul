"""
Decision-first aggregation utilities for attribution.

Answers questions like:
- "Which force dominates drops at Step 4?"
- "Which forces stop mattering after Step 2?"
- "Which personas are effort-sensitive vs risk-sensitive?"
"""

from typing import Dict, List, Tuple, Optional
from collections import defaultdict, Counter

from decision_attribution.attribution_types import DecisionAttribution
from decision_graph.decision_trace import DecisionTrace


def aggregate_step_attribution(
    traces: List[DecisionTrace],
    step_id: str,
    decision: Optional[str] = None
) -> Dict[str, float]:
    """
    Aggregate attribution for a specific step.
    
    Args:
        traces: List of DecisionTrace objects
        step_id: Step identifier
        decision: Optional filter ("CONTINUE" or "DROP")
    
    Returns:
        Dict mapping force names to average contribution
    """
    step_traces = [
        t for t in traces
        if t.step_id == step_id and (decision is None or t.decision.value == decision)
    ]
    
    if not step_traces:
        return {}
    
    # Aggregate SHAP values
    force_sums = defaultdict(float)
    count = 0
    
    for trace in step_traces:
        if hasattr(trace, 'attribution') and trace.attribution:
            attribution = trace.attribution
            for force_name, contrib in attribution.shap_values.items():
                force_sums[force_name] += contrib
            count += 1
    
    if count == 0:
        return {}
    
    # Average
    return {force: contrib / count for force, contrib in force_sums.items()}


def aggregate_decision_attribution(
    traces: List[DecisionTrace],
    decision: str  # "CONTINUE" or "DROP"
) -> Dict[str, float]:
    """
    Aggregate attribution across all steps for a specific decision type.
    
    Args:
        traces: List of DecisionTrace objects
        decision: "CONTINUE" or "DROP"
    
    Returns:
        Dict mapping force names to average contribution
    """
    decision_traces = [t for t in traces if t.decision.value == decision]
    
    if not decision_traces:
        return {}
    
    # Aggregate SHAP values
    force_sums = defaultdict(float)
    count = 0
    
    for trace in decision_traces:
        if hasattr(trace, 'attribution') and trace.attribution:
            attribution = trace.attribution
            for force_name, contrib in attribution.shap_values.items():
                force_sums[force_name] += contrib
            count += 1
    
    if count == 0:
        return {}
    
    # Average
    return {force: contrib / count for force, contrib in force_sums.items()}


def get_dominant_forces_by_step(
    traces: List[DecisionTrace],
    decision: Optional[str] = None
) -> Dict[str, List[Tuple[str, float]]]:
    """
    Get dominant forces for each step.
    
    Args:
        traces: List of DecisionTrace objects
        decision: Optional filter ("CONTINUE" or "DROP")
    
    Returns:
        Dict mapping step_id to list of (force_name, contribution) tuples
    """
    step_attributions = defaultdict(list)
    
    for trace in traces:
        if decision is None or trace.decision.value == decision:
            if hasattr(trace, 'attribution') and trace.attribution:
                attribution = trace.attribution
                step_attributions[trace.step_id].append(attribution)
    
    result = {}
    for step_id, attributions in step_attributions.items():
        # Aggregate for this step
        force_sums = defaultdict(float)
        count = len(attributions)
        
        for attr in attributions:
            for force_name, contrib in attr.shap_values.items():
                force_sums[force_name] += contrib
        
        if count > 0:
            # Average and rank
            force_avgs = {force: contrib / count for force, contrib in force_sums.items()}
            dominant = sorted(
                force_avgs.items(),
                key=lambda x: abs(x[1]),
                reverse=True
            )
            result[step_id] = dominant
    
    return result


def get_force_contribution_by_persona(
    traces: List[DecisionTrace],
    persona_class: str,
    decision: Optional[str] = None
) -> Dict[str, float]:
    """
    Get force contributions for a specific persona class.
    
    Args:
        traces: List of DecisionTrace objects
        persona_class: Persona class identifier
        decision: Optional filter ("CONTINUE" or "DROP")
    
    Returns:
        Dict mapping force names to average contribution
    """
    # Filter by persona class (would need persona_class in trace)
    # For now, aggregate all traces
    return aggregate_decision_attribution(traces, decision) if decision else {}


def format_attribution_summary(
    attribution: Dict[str, float],
    top_n: int = 3
) -> str:
    """
    Format attribution as human-readable summary.
    
    Example: "At Step 4, effort explains 62% of rejection pressure, risk 21%, intent 6%."
    
    Args:
        attribution: Dict mapping force names to contributions
        top_n: Number of top forces to include
    
    Returns:
        Formatted string
    """
    if not attribution:
        return "No attribution data available."
    
    # Sort by absolute contribution
    sorted_forces = sorted(
        attribution.items(),
        key=lambda x: abs(x[1]),
        reverse=True
    )[:top_n]
    
    # Format as percentages
    parts = []
    for force_name, contrib in sorted_forces:
        pct = abs(contrib) * 100
        parts.append(f"{force_name} {pct:.0f}%")
    
    return ", ".join(parts)


"""
ledger_formatter.py - Ledger-Style Text Formatting

Formats decision ledger output as plain text ledger (not narrative).

Language constraints:
- No adjectives (high, low, significant, major)
- No interpretive verbs (shows, indicates, suggests, implies)
- Use ledger-style terms only: observed, recorded, present, absent, first_seen, last_seen
"""

from typing import Dict, List
from decision_graph.decision_ledger import (
    DecisionBoundaryAssertion,
    PrecedentAssertion,
    DecisionTerminationPoint
)


def format_decision_ledger_as_text(ledger_data: Dict) -> str:
    """
    Format decision ledger as plain text (ledger-style).
    
    No narrative. No interpretation. Only facts.
    Uses ledger language only (observed, recorded, present, absent).
    """
    lines = []
    
    lines.append("=" * 80)
    lines.append("DECISION LEDGER")
    lines.append("=" * 80)
    lines.append("")
    lines.append("Generated: " + ledger_data.get('generated_timestamp', ''))
    lines.append("Sequences recorded: " + str(ledger_data.get('total_sequences', 0)))
    lines.append("Steps recorded: " + str(ledger_data.get('total_steps', 0)))
    lines.append("")
    lines.append("This output is a decision ledger, not an analysis or recommendation.")
    lines.append("All assertions are machine-verifiable facts from DecisionTrace objects.")
    lines.append("")
    
    # Decision Boundaries (stable only)
    lines.append("-" * 80)
    lines.append("DECISION BOUNDARIES")
    lines.append("-" * 80)
    lines.append("")
    
    boundaries = ledger_data.get('decision_boundaries', [])
    lines.append(f"Assertions recorded: {len(boundaries)}")
    lines.append("")
    
    for i, boundary in enumerate(boundaries, 1):
        lines.append(f"[{i}] Step: {boundary['step_id']}")
        lines.append(f"     Step Index: {boundary['step_index']}")
        lines.append(f"     Persona Class: {boundary['persona_class']}")
        
        coherence = boundary['persona_class_coherence']
        lines.append(f"     Coherence Score: {coherence['coherence_score']:.3f}")
        lines.append(f"     Coherence Stable: {coherence['is_stable']}")
        lines.append(f"     Supporting Traces: {boundary['supporting_trace_count']}")
        
        lines.append(f"     Accepted Count: {boundary['accepted_count']}")
        lines.append(f"     Rejected Count: {boundary['rejected_count']}")
        
        thresholds = boundary['cognitive_thresholds']
        if thresholds:
            lines.append(f"     Cognitive Thresholds (accepted):")
            for dim, (min_val, max_val) in thresholds.items():
                lines.append(f"       {dim}: [{min_val:.3f}, {max_val:.3f}]")
        
        # Factor presence (not categorical labels)
        factor_presence = boundary.get('factor_presence', [])
        if factor_presence:
            lines.append(f"     Factor Presence:")
            for fp in factor_presence[:10]:  # Limit to 10 for readability
                lines.append(f"       {fp['factor_name']}: present_in_traces = {fp['present_in_traces']}")
        
        # Replay-complete counterexamples
        counterexamples = boundary.get('counterexamples', [])
        if counterexamples:
            lines.append(f"     Counterexamples recorded: {len(counterexamples)}")
            for ce in counterexamples[:3]:  # Limit to 3 for readability
                lines.append(f"       Persona ID: {ce['persona_id']}")
                for dim, violation in ce['violated_thresholds'].items():
                    lines.append(f"         {dim}: threshold=[{violation['threshold_min']:.3f}, {violation['threshold_max']:.3f}], observed={violation['observed']:.3f}")
        
        lines.append(f"     First Observed: {boundary['first_observed_timestamp']}")
        lines.append(f"     Last Observed: {boundary['last_observed_timestamp']}")
        lines.append(f"     Occurrence Count: {boundary['occurrence_count']}")
        lines.append("")
    
    # Precedents — Acceptance
    lines.append("-" * 80)
    lines.append("PRECEDENTS — ACCEPTANCE")
    lines.append("-" * 80)
    lines.append("")
    
    acceptance_precedents = ledger_data.get('precedents_acceptance', [])
    lines.append(f"Assertions recorded: {len(acceptance_precedents)}")
    lines.append("")
    
    for i, precedent in enumerate(acceptance_precedents[:50], 1):  # Limit to 50 for readability
        lines.append(f"[{i}] Step: {precedent['step_id']}")
        lines.append(f"     Persona Class: {precedent['persona_class']}")
        
        # Factor presence (not categorical labels)
        factor_presence = precedent.get('factor_presence', [])
        if factor_presence:
            lines.append(f"     Factor Presence:")
            for fp in factor_presence[:5]:  # Limit to 5 for readability
                lines.append(f"       {fp['factor_name']}: present_in_traces = {fp['present_in_traces']}")
        
        lines.append(f"     Outcome: {precedent['outcome']}")
        lines.append(f"     Occurrence Count: {precedent['occurrence_count']}")
        lines.append(f"     First Observed: {precedent['first_observed_timestamp']}")
        lines.append(f"     Last Observed: {precedent['last_observed_timestamp']}")
        lines.append(f"     Time Span (seconds): {precedent['time_span_seconds']}")
        lines.append(f"     Stable: {precedent['is_stable']}")
        lines.append("")
    
    # Precedents — Rejection
    lines.append("-" * 80)
    lines.append("PRECEDENTS — REJECTION")
    lines.append("-" * 80)
    lines.append("")
    
    rejection_precedents = ledger_data.get('precedents_rejection', [])
    lines.append(f"Assertions recorded: {len(rejection_precedents)}")
    lines.append("")
    
    for i, precedent in enumerate(rejection_precedents[:50], 1):  # Limit to 50 for readability
        lines.append(f"[{i}] Step: {precedent['step_id']}")
        lines.append(f"     Persona Class: {precedent['persona_class']}")
        
        # Factor presence (not categorical labels)
        factor_presence = precedent.get('factor_presence', [])
        if factor_presence:
            lines.append(f"     Factor Presence:")
            for fp in factor_presence[:5]:  # Limit to 5 for readability
                lines.append(f"       {fp['factor_name']}: present_in_traces = {fp['present_in_traces']}")
        
        lines.append(f"     Outcome: {precedent['outcome']}")
        lines.append(f"     Occurrence Count: {precedent['occurrence_count']}")
        lines.append(f"     First Observed: {precedent['first_observed_timestamp']}")
        lines.append(f"     Last Observed: {precedent['last_observed_timestamp']}")
        lines.append(f"     Time Span (seconds): {precedent['time_span_seconds']}")
        lines.append(f"     Stable: {precedent['is_stable']}")
        lines.append("")
    
    # Decision Termination Points
    lines.append("-" * 80)
    lines.append("DECISION TERMINATION POINTS")
    lines.append("-" * 80)
    lines.append("")
    
    termination_points = ledger_data.get('decision_termination_points', [])
    lines.append(f"Assertions recorded: {len(termination_points)}")
    lines.append("")
    
    for assertion in termination_points:
        lines.append(f"Step: {assertion['step_id']}")
        lines.append(f"     Step Index: {assertion['step_index']}")
        lines.append(f"     Has Observed Rejections: {assertion['has_observed_rejections']}")
        lines.append(f"     Rejection Decision Count: {assertion['rejection_decision_count']}")
        if assertion['first_rejection_timestamp']:
            lines.append(f"     First Rejection: {assertion['first_rejection_timestamp']}")
        if assertion['last_rejection_timestamp']:
            lines.append(f"     Last Rejection: {assertion['last_rejection_timestamp']}")
        lines.append("")
    
    # Non-Binding Observations (Excluded)
    excluded = ledger_data.get('non_binding_observations_excluded', [])
    if excluded:
        lines.append("-" * 80)
        lines.append("NON-BINDING OBSERVATIONS (EXCLUDED)")
        lines.append("-" * 80)
        lines.append("")
        lines.append(f"Patterns recorded: {len(excluded)}")
        lines.append("")
        lines.append("These patterns do not meet stability requirements:")
        lines.append("- Pattern Stable == True")
        lines.append("- Supporting Traces >= MIN_BOUNDARY_SUPPORT")
        lines.append("")
        
        for i, pattern in enumerate(excluded[:20], 1):  # Limit to 20 for readability
            lines.append(f"[{i}] Step: {pattern['step_id']}")
            lines.append(f"     Persona Class: {pattern['persona_class']}")
            lines.append(f"     Trace Count: {pattern['trace_count']}")
            lines.append(f"     Coherence Stable: {pattern['coherence_stable']}")
            lines.append(f"     Meets Support Threshold: {pattern['meets_support_threshold']}")
            lines.append("")
    
    return "\n".join(lines)

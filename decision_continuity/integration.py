"""
Integration with existing DropSim components.

Shows how Decision Continuity & Precedent Engine integrates with:
- DecisionTrace
- ContextGraph
- DecisionAutopsy
"""

from typing import List, Dict, Optional
from decision_continuity import ContinuityEngine, DecisionEvent
from decision_graph.decision_trace import DecisionTrace, DecisionSequence


def integrate_traces_with_continuity(
    traces: List[DecisionTrace],
    entity_id: str,
    entity_type: str,
    engine: ContinuityEngine
) -> List[DecisionEvent]:
    """
    Integrate existing DecisionTraces with ContinuityEngine.
    
    Converts all traces to DecisionEvents and records them.
    
    Args:
        traces: List of DecisionTraces from simulation
        entity_id: Entity identifier (e.g., "product_credigo")
        entity_type: Entity type (e.g., "product")
        engine: ContinuityEngine instance
    
    Returns:
        List of created DecisionEvents
    """
    events = []
    previous_event = None
    
    for trace in traces:
        # Determine action based on decision
        if trace.decision.value == "CONTINUE":
            action_considered = "Continue to next step"
            action_taken = "Continue to next step"
            alternatives_rejected = ["Drop", "Skip step"]
            outcome_observed = "User continued"
        else:
            action_considered = "Continue to next step"
            action_taken = "Drop"
            alternatives_rejected = ["Continue", "Skip step"]
            outcome_observed = "User dropped"
        
        # Create event from trace
        event = engine.record_event_from_trace(
            trace=trace,
            entity_id=entity_id,
            entity_type=entity_type,
            action_considered=action_considered,
            action_taken=action_taken,
            alternatives_rejected=alternatives_rejected,
            outcome_observed=outcome_observed,
            confidence_level=trace.probability_before_sampling,
            context={
                "dominant_factors": trace.dominant_factors,
                "persona_id": trace.persona_id
            }
        )
        
        # Link to previous event
        if previous_event:
            event.parent_event_id = previous_event.event_id
        
        events.append(event)
        previous_event = event
    
    return events


def integrate_sequences_with_continuity(
    sequences: List[DecisionSequence],
    entity_id: str,
    entity_type: str,
    engine: ContinuityEngine
) -> Dict[str, List[DecisionEvent]]:
    """
    Integrate DecisionSequences with ContinuityEngine.
    
    Converts all sequences to DecisionEvents, grouped by persona.
    
    Args:
        sequences: List of DecisionSequences from simulation
        entity_id: Entity identifier
        entity_type: Entity type
        engine: ContinuityEngine instance
    
    Returns:
        Dict mapping persona_id to list of DecisionEvents
    """
    persona_events = {}
    
    for sequence in sequences:
        persona_id = sequence.persona_id
        events = integrate_traces_with_continuity(
            sequence.traces,
            entity_id,
            entity_type,
            engine
        )
        persona_events[persona_id] = events
    
    return persona_events


def query_precedents_for_autopsy(
    engine: ContinuityEngine,
    step_id: str,
    trust: float,
    value: float,
    commitment: float,
    risk: float,
    intent: float,
    factors: List[str]
) -> Dict:
    """
    Query precedents to inform DecisionAutopsy generation.
    
    This provides historical context for understanding why
    decisions were made in similar situations.
    
    Returns:
        Dict with precedent matches and recommendations
    """
    precedents = engine.query_precedents(
        step_id=step_id,
        trust=trust,
        value=value,
        commitment=commitment,
        risk=risk,
        intent=intent,
        factors=set(factors)
    )
    
    # Extract recommendations
    recommendations = []
    for precedent in precedents[:5]:  # Top 5
        for action, dist in precedent['action_distributions'].items():
            if dist['success_rate'] > 0.6:  # Only successful actions
                recommendations.append({
                    'action': action,
                    'success_rate': dist['success_rate'],
                    'occurrences': dist['total_occurrences'],
                    'confidence': dist['average_confidence']
                })
    
    return {
        'precedent_matches': len(precedents),
        'recommendations': sorted(recommendations, key=lambda x: x['success_rate'], reverse=True),
        'top_precedents': precedents[:3]
    }


def get_continuity_context_for_autopsy(
    engine: ContinuityEngine,
    entity_id: str,
    entity_type: str
) -> Dict:
    """
    Get continuity context to inform DecisionAutopsy.
    
    Provides historical belief state and irreversible events
    that may have influenced current decisions.
    """
    continuity = engine.get_continuity_state(entity_id, entity_type)
    
    if not continuity:
        return {
            'has_history': False,
            'message': 'No continuity history for this entity'
        }
    
    return {
        'has_history': True,
        'cumulative_trust': continuity.cumulative_trust,
        'cumulative_value': continuity.cumulative_value_realized,
        'cumulative_commitment': continuity.cumulative_commitment,
        'total_events': continuity.total_events,
        'irreversible_events': [
            {
                'type': e.event_type,
                'description': e.description,
                'impact': e.impact
            }
            for e in continuity.irreversible_events[-5:]  # Last 5
        ],
        'active_hypotheses': [
            {
                'description': h.description,
                'confidence': h.confidence,
                'evidence_for': h.evidence_for,
                'evidence_against': h.evidence_against
            }
            for h in continuity.active_hypotheses
        ]
    }


def enrich_autopsy_with_precedents(
    autopsy_data: Dict,
    engine: ContinuityEngine,
    entity_id: str,
    entity_type: str
) -> Dict:
    """
    Enrich DecisionAutopsy output with precedent insights.
    
    Adds a new section showing what has worked historically
    in similar situations.
    """
    # Get continuity context
    continuity_context = get_continuity_context_for_autopsy(engine, entity_id, entity_type)
    
    # Query precedents for the belief break step
    if 'beliefBreak' in autopsy_data and 'step_id' in autopsy_data['beliefBreak']:
        step_id = autopsy_data['beliefBreak']['step_id']
        
        # Extract belief state from autopsy (if available)
        # This is a simplified extraction - in practice would parse from autopsy
        precedents = engine.query_what_usually_works(
            condition_description=autopsy_data.get('verdict', ''),
            step_id=step_id
        )
        
        autopsy_data['precedent_insights'] = {
            'continuity_context': continuity_context,
            'historical_recommendations': precedents[:5],
            'query': f"What usually works when {autopsy_data.get('verdict', '')}?"
        }
    
    return autopsy_data


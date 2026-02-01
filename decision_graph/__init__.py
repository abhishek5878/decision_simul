"""
decision_graph - Decision Trace and Context Graph Module

This module implements the Decision Trace Layer - a system-of-record
primitive for capturing why personas continue or drop at each step.

This enables answering:
- "Which user types does this product work for?"
- "Which user types does it reject?"
- "What decisions caused that outcome?"
"""

from decision_graph.decision_trace import (
    DecisionTrace,
    DecisionOutcome,
    DecisionSequence,
    CognitiveStateSnapshot,
    IntentSnapshot,
    create_decision_trace
)

from decision_graph.decision_event import DecisionEvent

from decision_graph.context_graph import (
    ContextGraph,
    ContextGraphNode,
    ContextGraphEdge,
    ContextGraphSummary,
    build_context_graph_from_traces
)

from decision_graph.graph_queries import (
    query_decision_boundaries,
    query_persona_differentiation,
    query_stable_precedents,
    query_competing_explanations,
    query_acceptance_surface,
    DecisionBoundary,
    PersonaDifferentiation,
    StablePrecedent,
    CompetingExplanation,
    AcceptanceSurface
)

__all__ = [
    # Decision traces
    'DecisionTrace',
    'DecisionOutcome',
    'DecisionSequence',
    'CognitiveStateSnapshot',
    'IntentSnapshot',
    'create_decision_trace',
    
    # Decision events
    'DecisionEvent',
    
    # Context graph
    'ContextGraph',
    'ContextGraphNode',
    'ContextGraphEdge',
    'ContextGraphSummary',
    'build_context_graph_from_traces',
    
    # Decision-first queries
    'query_decision_boundaries',
    'query_persona_differentiation',
    'query_stable_precedents',
    'query_competing_explanations',
    'query_acceptance_surface',
    'DecisionBoundary',
    'PersonaDifferentiation',
    'StablePrecedent',
    'CompetingExplanation',
    'AcceptanceSurface'
]


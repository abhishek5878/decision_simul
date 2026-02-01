"""
Decision Continuity & Precedent Engine

Extends DropSim from a decision autopsy engine into a decision continuity system.

This layer:
- Captures decision traces DURING execution, not just post-simulation
- Maintains persistent belief state per entity (product / user / account)
- Converts past decision traces into reusable precedents
- Enables compounding learning across runs
"""

from .decision_event import DecisionEvent, DecisionEventType, BeliefState
from .continuity_state import ContinuityState, EntityType
from .precedent_graph import PrecedentGraph, PrecedentNode, PrecedentEdge
from .continuity_engine import ContinuityEngine

__all__ = [
    'DecisionEvent',
    'DecisionEventType',
    'BeliefState',
    'ContinuityState',
    'EntityType',
    'PrecedentGraph',
    'PrecedentNode',
    'PrecedentEdge',
    'ContinuityEngine'
]


"""
ContinuityState - Persistent Belief State per Entity

Maintains cumulative belief state that persists across simulation runs.
This enables compounding learning and continuity tracking.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
from datetime import datetime
from enum import Enum


class EntityType(Enum):
    """Type of entity for continuity tracking."""
    PRODUCT = "product"
    USER = "user"
    ACCOUNT = "account"
    COHORT = "cohort"


@dataclass
class IrreversibleEvent:
    """Record of an irreversible event that affects future decisions."""
    event_id: str
    timestamp: str
    event_type: str
    description: str
    impact: Dict[str, float]  # Impact on trust, value, commitment, etc.
    
    def to_dict(self) -> Dict:
        return {
            'event_id': self.event_id,
            'timestamp': self.timestamp,
            'event_type': self.event_type,
            'description': self.description,
            'impact': self.impact
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'IrreversibleEvent':
        return cls(
            event_id=data['event_id'],
            timestamp=data['timestamp'],
            event_type=data['event_type'],
            description=data['description'],
            impact=data.get('impact', {})
        )


@dataclass
class ActiveHypothesis:
    """An active hypothesis being tested."""
    hypothesis_id: str
    description: str
    created_at: str
    test_conditions: Dict[str, Any]
    expected_outcome: str
    confidence: float  # 0.0 to 1.0
    evidence_for: int = 0
    evidence_against: int = 0
    
    def to_dict(self) -> Dict:
        return {
            'hypothesis_id': self.hypothesis_id,
            'description': self.description,
            'created_at': self.created_at,
            'test_conditions': self.test_conditions,
            'expected_outcome': self.expected_outcome,
            'confidence': float(self.confidence),
            'evidence_for': self.evidence_for,
            'evidence_against': self.evidence_against
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ActiveHypothesis':
        return cls(
            hypothesis_id=data['hypothesis_id'],
            description=data['description'],
            created_at=data['created_at'],
            test_conditions=data['test_conditions'],
            expected_outcome=data['expected_outcome'],
            confidence=data.get('confidence', 0.5),
            evidence_for=data.get('evidence_for', 0),
            evidence_against=data.get('evidence_against', 0)
        )


@dataclass
class ContinuityState:
    """
    Persistent belief state that accumulates across simulation runs.
    
    This is the "memory" of the system - it tracks what has been learned
    about an entity (product, user, account) over time.
    
    Key invariant: ContinuityState is append-only. Historical records
    are never mutated, only new events are added.
    """
    # Identity
    entity_id: str
    entity_type: EntityType
    
    # Cumulative belief metrics (weighted averages over time)
    cumulative_trust: float = 0.5  # 0.0 to 1.0
    cumulative_value_realized: float = 0.0  # 0.0 to 1.0
    cumulative_commitment: float = 0.0  # 0.0 to 1.0
    
    # History
    commitment_history: List[Dict[str, Any]] = field(default_factory=list)
    value_realization_history: List[Dict[str, Any]] = field(default_factory=list)
    trust_change_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Irreversible events (these permanently affect future decisions)
    irreversible_events: List[IrreversibleEvent] = field(default_factory=list)
    
    # Active hypotheses being tested
    active_hypotheses: List[ActiveHypothesis] = field(default_factory=list)
    
    # Metadata
    first_seen: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    total_events: int = 0
    total_runs: int = 0
    
    # Context
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'entity_id': self.entity_id,
            'entity_type': self.entity_type.value,
            'cumulative_trust': float(self.cumulative_trust),
            'cumulative_value_realized': float(self.cumulative_value_realized),
            'cumulative_commitment': float(self.cumulative_commitment),
            'commitment_history': self.commitment_history,
            'value_realization_history': self.value_realization_history,
            'trust_change_history': self.trust_change_history,
            'irreversible_events': [e.to_dict() for e in self.irreversible_events],
            'active_hypotheses': [h.to_dict() for h in self.active_hypotheses],
            'first_seen': self.first_seen,
            'last_updated': self.last_updated,
            'total_events': self.total_events,
            'total_runs': self.total_runs,
            'context': self.context
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ContinuityState':
        """Create from dict."""
        return cls(
            entity_id=data['entity_id'],
            entity_type=EntityType(data['entity_type']),
            cumulative_trust=data.get('cumulative_trust', 0.5),
            cumulative_value_realized=data.get('cumulative_value_realized', 0.0),
            cumulative_commitment=data.get('cumulative_commitment', 0.0),
            commitment_history=data.get('commitment_history', []),
            value_realization_history=data.get('value_realization_history', []),
            trust_change_history=data.get('trust_change_history', []),
            irreversible_events=[
                IrreversibleEvent.from_dict(e) for e in data.get('irreversible_events', [])
            ],
            active_hypotheses=[
                ActiveHypothesis.from_dict(h) for h in data.get('active_hypotheses', [])
            ],
            first_seen=data.get('first_seen', datetime.now().isoformat()),
            last_updated=data.get('last_updated', datetime.now().isoformat()),
            total_events=data.get('total_events', 0),
            total_runs=data.get('total_runs', 0),
            context=data.get('context', {})
        )
    
    def update_from_event(self, event: 'DecisionEvent', weight: float = 1.0):
        """
        Update continuity state from a DecisionEvent.
        
        This is append-only - we never mutate historical records,
        only add new events and update cumulative metrics.
        
        Args:
            event: DecisionEvent to incorporate
            weight: Weight for this event (default 1.0, can be adjusted for recency)
        """
        from .decision_event import DecisionEvent
        
        self.total_events += 1
        self.last_updated = datetime.now().isoformat()
        
        # Update cumulative metrics (exponentially weighted moving average)
        alpha = 0.1 * weight  # Learning rate
        
        self.cumulative_trust = (
            (1 - alpha) * self.cumulative_trust +
            alpha * event.belief_state_after.trust_level
        )
        
        self.cumulative_commitment = (
            (1 - alpha) * self.cumulative_commitment +
            alpha * event.belief_state_after.commitment_level
        )
        
        # Track value realization
        if event.event_type.value == "value_realized":
            value_delta = event.belief_state_after.value_perception - event.belief_state_before.value_perception
            self.cumulative_value_realized = (
                (1 - alpha) * self.cumulative_value_realized +
                alpha * max(0.0, value_delta)
            )
            self.value_realization_history.append({
                'timestamp': event.timestamp,
                'step_id': event.step_id,
                'value_delta': float(value_delta),
                'event_id': event.event_id
            })
        
        # Track commitment changes
        commitment_delta = (
            event.belief_state_after.commitment_level -
            event.belief_state_before.commitment_level
        )
        if abs(commitment_delta) > 0.1:  # Significant change
            self.commitment_history.append({
                'timestamp': event.timestamp,
                'step_id': event.step_id,
                'commitment_delta': float(commitment_delta),
                'event_id': event.event_id
            })
        
        # Track trust changes
        trust_delta = (
            event.belief_state_after.trust_level -
            event.belief_state_before.trust_level
        )
        if abs(trust_delta) > 0.05:  # Significant change
            self.trust_change_history.append({
                'timestamp': event.timestamp,
                'step_id': event.step_id,
                'trust_delta': float(trust_delta),
                'event_id': event.event_id
            })
        
        # Record irreversible events
        if event.is_irreversible():
            irreversible_event = IrreversibleEvent(
                event_id=event.event_id,
                timestamp=event.timestamp,
                event_type=event.event_type.value,
                description=f"{event.action_taken} at {event.step_id}",
                impact=event.get_belief_delta()
            )
            self.irreversible_events.append(irreversible_event)
    
    def get_current_belief_state(self) -> Dict[str, float]:
        """Get current belief state as a dict."""
        return {
            'trust': self.cumulative_trust,
            'value': self.cumulative_value_realized,
            'commitment': self.cumulative_commitment
        }
    
    def has_irreversible_event(self, event_type: str) -> bool:
        """Check if entity has experienced a specific type of irreversible event."""
        return any(e.event_type == event_type for e in self.irreversible_events)


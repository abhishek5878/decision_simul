"""
DecisionEvent - Core Primitive for Decision Continuity

A DecisionEvent records a decision made during simulation execution.
This is captured DURING execution, not post-hoc.

Key invariant: DecisionEvents are immutable once created.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class DecisionEventType(Enum):
    """Type of decision event."""
    CONTINUATION = "continuation"  # User continued to next step
    DROP = "drop"  # User dropped at this step
    VALUE_REALIZED = "value_realized"  # User saw value
    TRUST_CHANGE = "trust_change"  # Trust level changed
    COMMITMENT_MADE = "commitment_made"  # Irreversible commitment
    HYPOTHESIS_TESTED = "hypothesis_tested"  # A hypothesis was tested


@dataclass
class BeliefState:
    """
    Belief state at a point in time.
    
    Captures the user's internal state: trust, value perception, commitment level, etc.
    """
    trust_level: float  # 0.0 to 1.0
    value_perception: float  # 0.0 to 1.0
    commitment_level: float  # 0.0 to 1.0
    cognitive_energy: float  # 0.0 to 1.0
    risk_perception: float  # 0.0 to 1.0
    intent_strength: float  # 0.0 to 1.0
    
    # Metadata
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'trust_level': float(self.trust_level),
            'value_perception': float(self.value_perception),
            'commitment_level': float(self.commitment_level),
            'cognitive_energy': float(self.cognitive_energy),
            'risk_perception': float(self.risk_perception),
            'intent_strength': float(self.intent_strength),
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'BeliefState':
        """Create from dict."""
        return cls(
            trust_level=data.get('trust_level', 0.5),
            value_perception=data.get('value_perception', 0.0),
            commitment_level=data.get('commitment_level', 0.0),
            cognitive_energy=data.get('cognitive_energy', 0.5),
            risk_perception=data.get('risk_perception', 0.5),
            intent_strength=data.get('intent_strength', 0.5),
            timestamp=data.get('timestamp', datetime.now().isoformat())
        )
    
    def delta(self, other: 'BeliefState') -> Dict[str, float]:
        """Compute delta between two belief states."""
        return {
            'trust_delta': other.trust_level - self.trust_level,
            'value_delta': other.value_perception - self.value_perception,
            'commitment_delta': other.commitment_level - self.commitment_level,
            'cognitive_delta': other.cognitive_energy - self.cognitive_energy,
            'risk_delta': other.risk_perception - self.risk_perception,
            'intent_delta': other.intent_strength - self.intent_strength
        }


@dataclass
class DecisionEvent:
    """
    DecisionEvent - Immutable record of a decision made during execution.
    
    This is the core primitive for decision continuity. Each DecisionEvent
    captures the complete context of a decision: what was considered, what
    was chosen, what was rejected, and what happened as a result.
    
    Key properties:
    - Immutable once created
    - Captured DURING execution (not post-hoc)
    - Contains full belief state before/after
    - Records alternatives considered but not taken
    - Links to observed outcomes
    """
    # Identity
    event_id: str
    entity_id: str  # Product ID, User ID, Account ID, etc.
    entity_type: str  # "product", "user", "account", etc.
    step_id: str
    step_index: int
    
    # Event type
    event_type: DecisionEventType
    
    # Belief state transition
    belief_state_before: BeliefState
    belief_state_after: BeliefState
    
    # Decision context
    action_considered: str  # What action was being considered
    action_taken: str  # What action was actually taken
    alternatives_rejected: List[str]  # What alternatives were considered but rejected
    
    # Outcome
    outcome_observed: Optional[str] = None  # What actually happened after the decision
    outcome_timestamp: Optional[str] = None  # When outcome was observed
    
    # Confidence
    confidence_level: float = 0.5  # 0.0 to 1.0 - confidence in the decision
    
    # Context
    context: Dict[str, Any] = field(default_factory=dict)  # Additional context
    
    # Metadata
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    policy_version: str = "v1.0"
    simulation_run_id: Optional[str] = None
    
    # Links to other events
    parent_event_id: Optional[str] = None  # Previous event in sequence
    related_trace_id: Optional[str] = None  # Link to DecisionTrace if exists
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'event_id': self.event_id,
            'entity_id': self.entity_id,
            'entity_type': self.entity_type,
            'step_id': self.step_id,
            'step_index': self.step_index,
            'event_type': self.event_type.value,
            'belief_state_before': self.belief_state_before.to_dict(),
            'belief_state_after': self.belief_state_after.to_dict(),
            'action_considered': self.action_considered,
            'action_taken': self.action_taken,
            'alternatives_rejected': self.alternatives_rejected,
            'outcome_observed': self.outcome_observed,
            'outcome_timestamp': self.outcome_timestamp,
            'confidence_level': float(self.confidence_level),
            'context': self.context,
            'timestamp': self.timestamp,
            'policy_version': self.policy_version,
            'simulation_run_id': self.simulation_run_id,
            'parent_event_id': self.parent_event_id,
            'related_trace_id': self.related_trace_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DecisionEvent':
        """Create from dict."""
        return cls(
            event_id=data['event_id'],
            entity_id=data['entity_id'],
            entity_type=data['entity_type'],
            step_id=data['step_id'],
            step_index=data['step_index'],
            event_type=DecisionEventType(data['event_type']),
            belief_state_before=BeliefState.from_dict(data['belief_state_before']),
            belief_state_after=BeliefState.from_dict(data['belief_state_after']),
            action_considered=data['action_considered'],
            action_taken=data['action_taken'],
            alternatives_rejected=data.get('alternatives_rejected', []),
            outcome_observed=data.get('outcome_observed'),
            outcome_timestamp=data.get('outcome_timestamp'),
            confidence_level=data.get('confidence_level', 0.5),
            context=data.get('context', {}),
            timestamp=data.get('timestamp', datetime.now().isoformat()),
            policy_version=data.get('policy_version', 'v1.0'),
            simulation_run_id=data.get('simulation_run_id'),
            parent_event_id=data.get('parent_event_id'),
            related_trace_id=data.get('related_trace_id')
        )
    
    def get_belief_delta(self) -> Dict[str, float]:
        """Get belief state delta."""
        return self.belief_state_before.delta(self.belief_state_after)
    
    def is_irreversible(self) -> bool:
        """Check if this event represents an irreversible decision."""
        return (
            self.event_type == DecisionEventType.COMMITMENT_MADE or
            self.belief_state_after.commitment_level > 0.7
        )


def create_decision_event_from_trace(
    trace: 'DecisionTrace',  # Forward reference
    entity_id: str,
    entity_type: str,
    action_considered: str,
    action_taken: str,
    alternatives_rejected: List[str],
    outcome_observed: Optional[str] = None,
    confidence_level: float = 0.5,
    context: Optional[Dict] = None
) -> DecisionEvent:
    """
    Create a DecisionEvent from an existing DecisionTrace.
    
    This bridges the existing DecisionTrace system with the new DecisionEvent system.
    """
    from decision_graph.decision_trace import DecisionTrace, DecisionOutcome
    
    # Extract belief state from cognitive state snapshot
    cognitive_state = trace.cognitive_state_snapshot
    
    belief_before = BeliefState(
        trust_level=cognitive_state.control,  # Using control as proxy for trust
        value_perception=cognitive_state.value,
        commitment_level=0.0,  # Will be inferred
        cognitive_energy=cognitive_state.energy,
        risk_perception=cognitive_state.risk,
        intent_strength=trace.intent.alignment_score
    )
    
    # Infer belief state after based on decision
    if trace.decision == DecisionOutcome.CONTINUE:
        belief_after = BeliefState(
            trust_level=min(1.0, belief_before.trust_level + 0.1),
            value_perception=belief_before.value_perception,
            commitment_level=min(1.0, belief_before.commitment_level + 0.2),
            cognitive_energy=max(0.0, belief_before.cognitive_energy - 0.1),
            risk_perception=belief_before.risk_perception,
            intent_strength=belief_before.intent_strength
        )
        event_type = DecisionEventType.CONTINUATION
    else:
        belief_after = BeliefState(
            trust_level=max(0.0, belief_before.trust_level - 0.2),
            value_perception=belief_before.value_perception,
            commitment_level=belief_before.commitment_level,
            cognitive_energy=belief_before.cognitive_energy,
            risk_perception=min(1.0, belief_before.risk_perception + 0.2),
            intent_strength=belief_before.intent_strength
        )
        event_type = DecisionEventType.DROP
    
    import hashlib
    event_id = hashlib.md5(
        f"{trace.persona_id}_{trace.step_id}_{trace.timestamp}".encode()
    ).hexdigest()[:16]
    
    return DecisionEvent(
        event_id=event_id,
        entity_id=entity_id,
        entity_type=entity_type,
        step_id=trace.step_id,
        step_index=trace.step_index,
        event_type=event_type,
        belief_state_before=belief_before,
        belief_state_after=belief_after,
        action_considered=action_considered,
        action_taken=action_taken,
        alternatives_rejected=alternatives_rejected,
        outcome_observed=outcome_observed,
        confidence_level=confidence_level,
        context=context or {},
        policy_version=trace.policy_version,
        related_trace_id=f"{trace.persona_id}_{trace.step_id}",
        timestamp=trace.timestamp
    )


"""
decision_trace.py - Decision Trace System of Record

DecisionTrace is a first-class primitive that captures WHY a persona
continued or dropped at a specific step. This is not logs, metrics, or
explanations - it is a system-of-record primitive.

This enables answering: "Which user types does this product work for,
and which ones does it reject?"
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Literal
from datetime import datetime
from enum import Enum


class DecisionOutcome(Enum):
    """Decision outcome types."""
    CONTINUE = "CONTINUE"
    DROP = "DROP"


@dataclass
class CognitiveStateSnapshot:
    """Snapshot of cognitive state at decision time."""
    energy: float
    risk: float
    effort: float
    value: float
    control: float
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'energy': float(self.energy),
            'risk': float(self.risk),
            'effort': float(self.effort),
            'value': float(self.value),
            'control': float(self.control)
        }


@dataclass
class IntentSnapshot:
    """Snapshot of intent state at decision time."""
    inferred_intent: str
    alignment_score: float
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'inferred_intent': self.inferred_intent,
            'alignment_score': float(self.alignment_score)
        }


@dataclass
class DecisionTrace:
    """
    DecisionTrace - System of Record Primitive
    
    A structured, durable record of why a persona continued or dropped
    at a specific step. This is captured at decision time, not post-hoc.
    
    This enables answering:
    - "Which user types does this product work for?"
    - "Which user types does it reject?"
    - "What decisions caused that outcome?"
    """
    # Identity
    persona_id: str
    step_id: str
    step_index: int
    
    # Decision
    decision: DecisionOutcome  # CONTINUE or DROP
    probability_before_sampling: float  # Continuation probability before random sampling
    sampled_outcome: bool  # Actual sampled outcome (True = continue, False = drop)
    
    # State at decision time
    cognitive_state_snapshot: CognitiveStateSnapshot
    intent: IntentSnapshot
    
    # Explanation
    dominant_factors: List[str]  # e.g., ["intent_mismatch", "cognitive_fatigue", "risk_spike"]
    
    # Decision Attribution (game-theoretic force attribution)
    attribution: Optional['DecisionAttribution'] = None  # Forward reference
    
    # Metadata
    policy_version: str = "v1.0"  # Behavioral ruleset version
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        import numpy as np
        # Convert numpy bool_ to native bool for JSON serialization
        sampled_outcome = bool(self.sampled_outcome) if isinstance(self.sampled_outcome, (np.bool_, bool)) else self.sampled_outcome
        result = {
            'persona_id': self.persona_id,
            'step_id': self.step_id,
            'step_index': self.step_index,
            'decision': self.decision.value,
            'probability_before_sampling': float(self.probability_before_sampling),
            'sampled_outcome': sampled_outcome,
            'cognitive_state_snapshot': self.cognitive_state_snapshot.to_dict(),
            'intent': self.intent.to_dict(),
            'dominant_factors': self.dominant_factors,
            'policy_version': self.policy_version,
            'timestamp': self.timestamp
        }
        # Include attribution if present
        if self.attribution is not None:
            result['attribution'] = self.attribution.to_dict()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DecisionTrace':
        """Create from dict."""
        # Import here to avoid circular import
        attribution = None
        if 'attribution' in data and data['attribution']:
            from decision_attribution.attribution_types import DecisionAttribution
            attribution = DecisionAttribution.from_dict(data['attribution'])
        
        return cls(
            persona_id=data['persona_id'],
            step_id=data['step_id'],
            step_index=data['step_index'],
            decision=DecisionOutcome(data['decision']),
            probability_before_sampling=data['probability_before_sampling'],
            sampled_outcome=data['sampled_outcome'],
            cognitive_state_snapshot=CognitiveStateSnapshot(**data['cognitive_state_snapshot']),
            intent=IntentSnapshot(**data['intent']),
            dominant_factors=data['dominant_factors'],
            attribution=attribution,
            policy_version=data.get('policy_version', 'v1.0'),
            timestamp=data.get('timestamp', datetime.now().isoformat())
        )


@dataclass
class DecisionSequence:
    """
    Sequence of decisions for a single persona trajectory.
    
    This represents one persona's decision history through the funnel.
    """
    persona_id: str
    variant_name: str
    traces: List[DecisionTrace]
    final_outcome: DecisionOutcome
    exit_step: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'persona_id': self.persona_id,
            'variant_name': self.variant_name,
            'traces': [t.to_dict() for t in self.traces],
            'final_outcome': self.final_outcome.value,
            'exit_step': self.exit_step
        }
    
    def get_drop_trace(self) -> Optional[DecisionTrace]:
        """Get the trace where persona dropped (if any)."""
        for trace in self.traces:
            if trace.decision == DecisionOutcome.DROP:
                return trace
        return None
    
    def get_continuation_traces(self) -> List[DecisionTrace]:
        """Get all traces where persona continued."""
        return [t for t in self.traces if t.decision == DecisionOutcome.CONTINUE]


def create_decision_trace(
    persona_id: str,
    step_id: str,
    step_index: int,
    decision: DecisionOutcome,
    probability_before_sampling: float,
    sampled_outcome: bool,
    cognitive_state: Dict,
    intent_info: Dict,
    dominant_factors: List[str],
    policy_version: str = "v1.0"
) -> DecisionTrace:
    """
    Create a DecisionTrace from decision-time information.
    
    This is called AT DECISION TIME, not post-hoc.
    
    Args:
        persona_id: Persona identifier
        step_id: Step identifier
        step_index: Step index (0-based)
        decision: CONTINUE or DROP
        probability_before_sampling: Continuation probability before sampling
        sampled_outcome: Actual sampled outcome
        cognitive_state: Dict with energy, risk, effort, value, control
        intent_info: Dict with inferred_intent and alignment_score
        dominant_factors: List of dominant factor names
        policy_version: Behavioral ruleset version
    
    Returns:
        DecisionTrace object
    """
    cognitive_snapshot = CognitiveStateSnapshot(
        energy=cognitive_state.get('cognitive_energy', 0.0),
        risk=cognitive_state.get('perceived_risk', 0.0),
        effort=cognitive_state.get('perceived_effort', 0.0),
        value=cognitive_state.get('perceived_value', 0.0),
        control=cognitive_state.get('perceived_control', 0.0)
    )
    
    intent_snapshot = IntentSnapshot(
        inferred_intent=intent_info.get('inferred_intent', 'unknown'),
        alignment_score=intent_info.get('alignment_score', 0.0)
    )
    
    return DecisionTrace(
        persona_id=persona_id,
        step_id=step_id,
        step_index=step_index,
        decision=decision,
        probability_before_sampling=probability_before_sampling,
        sampled_outcome=sampled_outcome,
        cognitive_state_snapshot=cognitive_snapshot,
        intent=intent_snapshot,
        dominant_factors=dominant_factors,
        policy_version=policy_version
    )


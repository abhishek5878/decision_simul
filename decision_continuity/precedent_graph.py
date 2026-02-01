"""
PrecedentGraph - Aggregates Historical DecisionEvents into Reusable Precedents

The PrecedentGraph converts past DecisionEvents into patterns that can be
queried and reused in future simulations.

Key invariant: Precedents are derived from historical events, never mutated.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
from datetime import datetime
import hashlib


@dataclass
class ConditionSignature:
    """
    A condition signature represents a pattern of conditions that lead to decisions.
    
    This is a hashable representation of a decision context.
    """
    step_id: str
    trust_range: Tuple[float, float]  # (min, max)
    value_range: Tuple[float, float]
    commitment_range: Tuple[float, float]
    risk_range: Tuple[float, float]
    intent_range: Tuple[float, float]
    dominant_factors: Set[str]
    
    def to_dict(self) -> Dict:
        return {
            'step_id': self.step_id,
            'trust_range': list(self.trust_range),
            'value_range': list(self.value_range),
            'commitment_range': list(self.commitment_range),
            'risk_range': list(self.risk_range),
            'intent_range': list(self.intent_range),
            'dominant_factors': list(self.dominant_factors)
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConditionSignature':
        return cls(
            step_id=data['step_id'],
            trust_range=tuple(data['trust_range']),
            value_range=tuple(data['value_range']),
            commitment_range=tuple(data['commitment_range']),
            risk_range=tuple(data['risk_range']),
            intent_range=tuple(data['intent_range']),
            dominant_factors=set(data['dominant_factors'])
        )
    
    def matches(self, trust: float, value: float, commitment: float, 
                risk: float, intent: float, factors: Set[str]) -> bool:
        """Check if given conditions match this signature."""
        return (
            self.trust_range[0] <= trust <= self.trust_range[1] and
            self.value_range[0] <= value <= self.value_range[1] and
            self.commitment_range[0] <= commitment <= self.commitment_range[1] and
            self.risk_range[0] <= risk <= self.risk_range[1] and
            self.intent_range[0] <= intent <= self.intent_range[1] and
            self.dominant_factors.issubset(factors)
        )
    
    def to_hash(self) -> str:
        """Generate hash for this signature."""
        sig_str = (
            f"{self.step_id}_"
            f"{self.trust_range}_{self.value_range}_{self.commitment_range}_"
            f"{self.risk_range}_{self.intent_range}_"
            f"{sorted(self.dominant_factors)}"
        )
        return hashlib.md5(sig_str.encode()).hexdigest()[:16]


@dataclass
class ActionOutcomeDistribution:
    """
    Distribution of outcomes for a given action under specific conditions.
    """
    action: str
    total_occurrences: int = 0
    outcome_counts: Dict[str, int] = field(default_factory=dict)
    outcome_probabilities: Dict[str, float] = field(default_factory=dict)
    average_confidence: float = 0.0
    success_rate: float = 0.0  # For CONTINUATION outcomes
    
    def update(self, outcome: str, confidence: float, is_success: bool = False):
        """Update distribution with new outcome."""
        self.total_occurrences += 1
        self.outcome_counts[outcome] = self.outcome_counts.get(outcome, 0) + 1
        
        # Recalculate probabilities
        self.outcome_probabilities = {
            outcome: count / self.total_occurrences
            for outcome, count in self.outcome_counts.items()
        }
        
        # Update average confidence (exponentially weighted)
        alpha = 0.1
        self.average_confidence = (
            (1 - alpha) * self.average_confidence + alpha * confidence
        )
        
        # Update success rate
        if is_success:
            current_success = sum(1 for o in self.outcome_counts.keys() if "continue" in o.lower() or "success" in o.lower())
            self.success_rate = current_success / self.total_occurrences
    
    def to_dict(self) -> Dict:
        return {
            'action': self.action,
            'total_occurrences': self.total_occurrences,
            'outcome_counts': self.outcome_counts,
            'outcome_probabilities': self.outcome_probabilities,
            'average_confidence': float(self.average_confidence),
            'success_rate': float(self.success_rate)
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ActionOutcomeDistribution':
        dist = cls(
            action=data['action'],
            total_occurrences=data['total_occurrences'],
            outcome_counts=data['outcome_counts'],
            outcome_probabilities=data['outcome_probabilities'],
            average_confidence=data.get('average_confidence', 0.0),
            success_rate=data.get('success_rate', 0.0)
        )
        return dist


@dataclass
class PrecedentNode:
    """
    A node in the PrecedentGraph representing a condition signature.
    """
    signature: ConditionSignature
    signature_hash: str
    total_events: int = 0
    first_seen: str = field(default_factory=lambda: datetime.now().isoformat())
    last_seen: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Action → outcome distributions
    action_distributions: Dict[str, ActionOutcomeDistribution] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'signature': self.signature.to_dict(),
            'signature_hash': self.signature_hash,
            'total_events': self.total_events,
            'first_seen': self.first_seen,
            'last_seen': self.last_seen,
            'action_distributions': {
                action: dist.to_dict()
                for action, dist in self.action_distributions.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PrecedentNode':
        return cls(
            signature=ConditionSignature.from_dict(data['signature']),
            signature_hash=data['signature_hash'],
            total_events=data['total_events'],
            first_seen=data['first_seen'],
            last_seen=data['last_seen'],
            action_distributions={
                action: ActionOutcomeDistribution.from_dict(dist)
                for action, dist in data['action_distributions'].items()
            }
        )


@dataclass
class PrecedentEdge:
    """
    An edge in the PrecedentGraph representing a transition between condition signatures.
    """
    from_signature_hash: str
    to_signature_hash: str
    transition_count: int = 0
    transition_probability: float = 0.0
    average_confidence: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'from_signature_hash': self.from_signature_hash,
            'to_signature_hash': self.to_signature_hash,
            'transition_count': self.transition_count,
            'transition_probability': float(self.transition_probability),
            'average_confidence': float(self.average_confidence)
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PrecedentEdge':
        return cls(
            from_signature_hash=data['from_signature_hash'],
            to_signature_hash=data['to_signature_hash'],
            transition_count=data['transition_count'],
            transition_probability=data.get('transition_probability', 0.0),
            average_confidence=data.get('average_confidence', 0.0)
        )


class PrecedentGraph:
    """
    PrecedentGraph - Aggregates historical DecisionEvents into reusable precedents.
    
    The graph structure:
    - Nodes: Condition signatures (patterns of conditions)
    - Edges: Transitions between condition signatures
    - Node data: Action → outcome distributions
    
    Key invariant: Precedents are derived from historical events, never mutated.
    New events are added, but historical precedents remain unchanged.
    """
    
    def __init__(self):
        """Initialize empty PrecedentGraph."""
        self.nodes: Dict[str, PrecedentNode] = {}  # signature_hash -> PrecedentNode
        self.edges: Dict[Tuple[str, str], PrecedentEdge] = {}  # (from, to) -> PrecedentEdge
        self.total_events_processed: int = 0
    
    def add_event(self, event: 'DecisionEvent', previous_event: Optional['DecisionEvent'] = None):
        """
        Add a DecisionEvent to the graph.
        
        This creates or updates precedents based on the event.
        Historical precedents are never mutated - new events create new
        or update existing precedents incrementally.
        
        Args:
            event: DecisionEvent to add
            previous_event: Previous event in sequence (for edge creation)
        """
        from .decision_event import DecisionEvent
        
        self.total_events_processed += 1
        
        # Create condition signature from event
        belief_before = event.belief_state_before
        signature = ConditionSignature(
            step_id=event.step_id,
            trust_range=(belief_before.trust_level, belief_before.trust_level),
            value_range=(belief_before.value_perception, belief_before.value_perception),
            commitment_range=(belief_before.commitment_level, belief_before.commitment_level),
            risk_range=(belief_before.risk_perception, belief_before.risk_perception),
            intent_range=(belief_before.intent_strength, belief_before.intent_strength),
            dominant_factors=set(event.context.get('dominant_factors', []))
        )
        
        # Find or create node
        sig_hash = signature.to_hash()
        if sig_hash not in self.nodes:
            self.nodes[sig_hash] = PrecedentNode(
                signature=signature,
                signature_hash=sig_hash,
                first_seen=event.timestamp
            )
        
        node = self.nodes[sig_hash]
        node.total_events += 1
        node.last_seen = event.timestamp
        
        # Update action distribution
        action = event.action_taken
        if action not in node.action_distributions:
            node.action_distributions[action] = ActionOutcomeDistribution(action=action)
        
        dist = node.action_distributions[action]
        outcome = event.outcome_observed or event.event_type.value
        is_success = event.event_type.value in ["continuation", "value_realized"]
        dist.update(outcome, event.confidence_level, is_success)
        
        # Create edge if previous event exists
        if previous_event:
            prev_signature = ConditionSignature(
                step_id=previous_event.step_id,
                trust_range=(previous_event.belief_state_before.trust_level, previous_event.belief_state_before.trust_level),
                value_range=(previous_event.belief_state_before.value_perception, previous_event.belief_state_before.value_perception),
                commitment_range=(previous_event.belief_state_before.commitment_level, previous_event.belief_state_before.commitment_level),
                risk_range=(previous_event.belief_state_before.risk_perception, previous_event.belief_state_before.risk_perception),
                intent_range=(previous_event.belief_state_before.intent_strength, previous_event.belief_state_before.intent_strength),
                dominant_factors=set(previous_event.context.get('dominant_factors', []))
            )
            prev_hash = prev_signature.to_hash()
            
            edge_key = (prev_hash, sig_hash)
            if edge_key not in self.edges:
                self.edges[edge_key] = PrecedentEdge(
                    from_signature_hash=prev_hash,
                    to_signature_hash=sig_hash
                )
            
            edge = self.edges[edge_key]
            edge.transition_count += 1
            # Update transition probability (simplified - would need total out-degree)
            edge.average_confidence = (
                (edge.average_confidence * (edge.transition_count - 1) + event.confidence_level) /
                edge.transition_count
            )
    
    def query_precedents(
        self,
        step_id: str,
        trust: float,
        value: float,
        commitment: float,
        risk: float,
        intent: float,
        factors: Set[str],
        action: Optional[str] = None
    ) -> List[Dict]:
        """
        Query precedents matching given conditions.
        
        Returns list of precedents with:
        - Matching condition signature
        - Action → outcome distributions
        - Confidence scores
        
        Args:
            step_id: Step identifier
            trust: Trust level
            value: Value perception
            commitment: Commitment level
            risk: Risk perception
            intent: Intent strength
            factors: Dominant factors
            action: Optional specific action to query
        
        Returns:
            List of precedent matches with outcome distributions
        """
        matches = []
        
        for node in self.nodes.values():
            if node.signature.step_id == step_id:
                if node.signature.matches(trust, value, commitment, risk, intent, factors):
                    match = {
                        'signature': node.signature.to_dict(),
                        'total_occurrences': node.total_events,
                        'first_seen': node.first_seen,
                        'last_seen': node.last_seen,
                        'action_distributions': {}
                    }
                    
                    # Filter by action if specified
                    if action:
                        if action in node.action_distributions:
                            match['action_distributions'][action] = node.action_distributions[action].to_dict()
                    else:
                        match['action_distributions'] = {
                            a: d.to_dict() for a, d in node.action_distributions.items()
                        }
                    
                    matches.append(match)
        
        # Sort by total occurrences (most common first)
        matches.sort(key=lambda x: x['total_occurrences'], reverse=True)
        
        return matches
    
    def query_what_usually_works(
        self,
        condition_description: str,
        step_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Query: "What usually works when [condition_description]?"
        
        This is a high-level query that searches for precedents matching
        the condition and returns actions with highest success rates.
        
        Args:
            condition_description: Natural language description (e.g., "belief collapses due to delayed value")
            step_id: Optional step filter
        
        Returns:
            List of actions with success rates, sorted by success rate
        """
        # This is a simplified implementation
        # In production, would use NLP to parse condition_description
        
        results = []
        
        for node in self.nodes.values():
            if step_id and node.signature.step_id != step_id:
                continue
            
            for action, dist in node.action_distributions.items():
                if dist.success_rate > 0.5:  # Only successful actions
                    results.append({
                        'action': action,
                        'success_rate': dist.success_rate,
                        'total_occurrences': dist.total_occurrences,
                        'average_confidence': dist.average_confidence,
                        'step_id': node.signature.step_id,
                        'condition_signature': node.signature.to_dict()
                    })
        
        # Sort by success rate
        results.sort(key=lambda x: x['success_rate'], reverse=True)
        
        return results
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'nodes': {hash: node.to_dict() for hash, node in self.nodes.items()},
            'edges': {
                f"{from_hash}_{to_hash}": edge.to_dict()
                for (from_hash, to_hash), edge in self.edges.items()
            },
            'total_events_processed': self.total_events_processed
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PrecedentGraph':
        """Create from dict."""
        graph = cls()
        graph.total_events_processed = data.get('total_events_processed', 0)
        
        # Load nodes
        for hash, node_data in data.get('nodes', {}).items():
            graph.nodes[hash] = PrecedentNode.from_dict(node_data)
        
        # Load edges
        for edge_key, edge_data in data.get('edges', {}).items():
            from_hash, to_hash = edge_key.split('_', 1)
            graph.edges[(from_hash, to_hash)] = PrecedentEdge.from_dict(edge_data)
        
        return graph


"""
dropsim_decision_traces.py - Decision Trace Abstraction

Records, persists, and reasons over real decision traces.
Transforms the system from "simulator of reasoning" to "system of record for decision-making."
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import os
import hashlib


class ActorType(Enum):
    """Type of decision maker."""
    HUMAN = "human"
    AGENT = "agent"
    SYSTEM = "system"


@dataclass
class DecisionTrace:
    """A first-class record of a decision that was made."""
    decision_id: str
    timestamp: str
    actor_type: str  # "human", "agent", "system"
    context_snapshot: Dict  # What information was available at that moment
    options_considered: List[Dict]  # What alternatives were considered
    chosen_action: Dict  # What decision was made
    rationale: str  # What reasoning or rule triggered the decision
    constraints: List[str]  # What constraints were active
    downstream_outcome: Optional[Dict] = None  # What happened afterward
    confidence: float = 0.5  # Confidence in the decision
    precedent_ids: List[str] = field(default_factory=list)  # Similar past decisions
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'decision_id': self.decision_id,
            'timestamp': self.timestamp,
            'actor_type': self.actor_type,
            'context_snapshot': self.context_snapshot,
            'options_considered': self.options_considered,
            'chosen_action': self.chosen_action,
            'rationale': self.rationale,
            'constraints': self.constraints,
            'downstream_outcome': self.downstream_outcome,
            'confidence': self.confidence,
            'precedent_ids': self.precedent_ids
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DecisionTrace':
        """Create from dict."""
        return cls(
            decision_id=data['decision_id'],
            timestamp=data['timestamp'],
            actor_type=data['actor_type'],
            context_snapshot=data['context_snapshot'],
            options_considered=data['options_considered'],
            chosen_action=data['chosen_action'],
            rationale=data['rationale'],
            constraints=data.get('constraints', []),
            downstream_outcome=data.get('downstream_outcome'),
            confidence=data.get('confidence', 0.5),
            precedent_ids=data.get('precedent_ids', [])
        )
    
    def compute_similarity_key(self) -> str:
        """Compute a key for finding similar decisions."""
        # Hash based on context and action type
        key_parts = [
            str(self.chosen_action.get('action_type', '')),
            str(self.context_snapshot.get('step_id', '')),
            str(self.context_snapshot.get('persona_type', '')),
        ]
        key_str = '|'.join(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()[:16]


class DecisionTraceStore:
    """Persistent store for decision traces."""
    
    def __init__(self, store_path: str = "decision_traces.json"):
        self.store_path = store_path
        self.traces: List[DecisionTrace] = []
        self._load()
    
    def _load(self):
        """Load traces from disk."""
        if os.path.exists(self.store_path):
            try:
                with open(self.store_path, 'r') as f:
                    data = json.load(f)
                    self.traces = [DecisionTrace.from_dict(t) for t in data.get('traces', [])]
            except Exception:
                self.traces = []
        else:
            self.traces = []
    
    def _save(self):
        """Save traces to disk."""
        data = {
            'traces': [t.to_dict() for t in self.traces],
            'last_updated': datetime.now().isoformat()
        }
        with open(self.store_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def add_trace(self, trace: DecisionTrace):
        """Add a decision trace."""
        # Find similar past decisions
        similar = self.find_similar_decisions(trace)
        trace.precedent_ids = [t.decision_id for t in similar[:5]]  # Top 5 similar
        
        self.traces.append(trace)
        self._save()
    
    def find_similar_decisions(
        self,
        query_trace: DecisionTrace,
        limit: int = 10
    ) -> List[DecisionTrace]:
        """
        Find similar past decisions.
        
        This is the "killer query": Show me all past decisions similar to this one,
        what was chosen, and what happened afterward.
        """
        if not self.traces:
            return []
        
        query_key = query_trace.compute_similarity_key()
        
        # Find traces with similar keys
        similar = []
        for trace in self.traces:
            if trace.decision_id == query_trace.decision_id:
                continue  # Skip self
            
            trace_key = trace.compute_similarity_key()
            
            # Exact key match
            if trace_key == query_key:
                similar.append(trace)
            # Similar context
            elif self._context_similarity(query_trace, trace) > 0.7:
                similar.append(trace)
        
        # Sort by similarity (exact key matches first, then by context similarity)
        similar.sort(key=lambda t: (
            0 if t.compute_similarity_key() == query_key else 1,
            -self._context_similarity(query_trace, t)
        ))
        
        return similar[:limit]
    
    def _context_similarity(self, trace1: DecisionTrace, trace2: DecisionTrace) -> float:
        """Compute similarity between two traces based on context."""
        score = 0.0
        matches = 0
        
        ctx1 = trace1.context_snapshot
        ctx2 = trace2.context_snapshot
        
        # Compare step_id
        if ctx1.get('step_id') == ctx2.get('step_id'):
            score += 0.3
            matches += 1
        
        # Compare persona_type
        if ctx1.get('persona_type') == ctx2.get('persona_type'):
            score += 0.2
            matches += 1
        
        # Compare action type
        if trace1.chosen_action.get('action_type') == trace2.chosen_action.get('action_type'):
            score += 0.3
            matches += 1
        
        # Compare constraints
        constraints1 = set(trace1.constraints)
        constraints2 = set(trace2.constraints)
        if constraints1 and constraints2:
            overlap = len(constraints1 & constraints2) / len(constraints1 | constraints2)
            score += overlap * 0.2
        
        return min(1.0, score)
    
    def get_trace(self, decision_id: str) -> Optional[DecisionTrace]:
        """Get a trace by ID."""
        for trace in self.traces:
            if trace.decision_id == decision_id:
                return trace
        return None
    
    def get_traces_by_actor(self, actor_type: str) -> List[DecisionTrace]:
        """Get all traces for a specific actor type."""
        return [t for t in self.traces if t.actor_type == actor_type]
    
    def get_traces_by_time_range(
        self,
        start_time: str,
        end_time: str
    ) -> List[DecisionTrace]:
        """Get traces within a time range."""
        return [
            t for t in self.traces
            if start_time <= t.timestamp <= end_time
        ]


# ============================================================================
# Decision Trace Creation Helpers
# ============================================================================

def create_decision_trace(
    actor_type: str,
    context_snapshot: Dict,
    options_considered: List[Dict],
    chosen_action: Dict,
    rationale: str,
    constraints: List[str] = None,
    confidence: float = 0.5
) -> DecisionTrace:
    """
    Create a decision trace.
    
    Args:
        actor_type: "human", "agent", or "system"
        context_snapshot: What information was available
        options_considered: What alternatives were considered
        chosen_action: What decision was made
        rationale: What reasoning triggered the decision
        constraints: What constraints were active
        confidence: Confidence in the decision
    
    Returns:
        DecisionTrace
    """
    decision_id = f"decision_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    return DecisionTrace(
        decision_id=decision_id,
        timestamp=datetime.now().isoformat(),
        actor_type=actor_type,
        context_snapshot=context_snapshot,
        options_considered=options_considered or [],
        chosen_action=chosen_action,
        rationale=rationale,
        constraints=constraints or [],
        confidence=confidence
    )


def extract_decision_traces_from_simulation(
    simulation_result: Dict,
    actor_type: str = "system"
) -> List[DecisionTrace]:
    """
    Extract decision traces from a simulation result.
    
    This converts simulation outputs into decision traces.
    """
    traces = []
    
    # Extract from decision report (can be nested in scenario_result)
    decision_report = None
    if 'decision_report' in simulation_result:
        decision_report = simulation_result['decision_report']
    elif 'scenario_result' in simulation_result:
        scenario = simulation_result['scenario_result']
        if 'decision_report' in scenario:
            decision_report = scenario['decision_report']
    
    if decision_report and isinstance(decision_report, dict):
        if 'recommended_actions' in decision_report:
            actions = decision_report['recommended_actions']
            if isinstance(actions, list):
                for i, action in enumerate(actions):
                    if isinstance(action, dict):
                        context_snapshot = {
                            'step_id': action.get('target_step', ''),
                            'product': simulation_result.get('product_name', '') or simulation_result.get('scenario_result', {}).get('product_name', ''),
                            'persona_type': simulation_result.get('persona_type', '') or simulation_result.get('scenario_result', {}).get('persona_type', '')
                        }
                        
                        # All options considered
                        options = [a for a in actions if isinstance(a, dict)]
                        
                        trace = create_decision_trace(
                            actor_type=actor_type,
                            context_snapshot=context_snapshot,
                            options_considered=options,
                            chosen_action={
                                'action_type': action.get('change_type', 'unknown'),
                                'target_step': action.get('target_step', ''),
                                'estimated_impact': action.get('estimated_impact', 0.0)
                            },
                            rationale=action.get('rationale', '') or action.get('action', ''),
                            constraints=action.get('tradeoffs', []) or [],
                            confidence=action.get('confidence', decision_report.get('overall_confidence', 0.5))
                        )
                        traces.append(trace)
    
    # Extract from context graph (step-level decisions)
    context_graph = None
    if 'context_graph' in simulation_result:
        context_graph = simulation_result['context_graph']
    elif 'scenario_result' in simulation_result:
        scenario = simulation_result['scenario_result']
        if 'context_graph' in scenario:
            context_graph = scenario['context_graph']
    
    if context_graph and isinstance(context_graph, dict):
        nodes = context_graph.get('nodes', [])
        if isinstance(nodes, list):
            for node in nodes:
                if isinstance(node, dict):
                    step_id = node.get('step_id', '') or node.get('step_name', '')
                    if step_id:
                        context_snapshot = {
                            'step_id': step_id,
                            'drop_rate': node.get('drop_rate', 0.0),
                            'effort': node.get('avg_perceived_effort', 0.0),
                            'risk': node.get('avg_perceived_risk', 0.0),
                            'total_entries': node.get('total_entries', 0)
                        }
                        
                        # Decision: continue or drop
                        drop_rate = node.get('drop_rate', 0.5)
                        decision = "continue" if drop_rate < 0.5 else "drop"
                        
                        trace = create_decision_trace(
                            actor_type=actor_type,
                            context_snapshot=context_snapshot,
                            options_considered=[
                                {'action': 'continue', 'expected_outcome': 'proceed'},
                                {'action': 'drop', 'expected_outcome': 'abandon'}
                            ],
                            chosen_action={
                                'action_type': decision,
                                'step_id': step_id
                            },
                            rationale=f"Drop rate: {drop_rate:.1%}, Effort: {node.get('avg_perceived_effort', 0.0):.1%}",
                            constraints=[],
                            confidence=1.0 - abs(drop_rate - 0.5) * 2  # Higher confidence when drop rate is extreme
                        )
                        traces.append(trace)
    
    # Extract from interpretation (root cause decisions)
    interpretation = None
    if 'interpretation' in simulation_result:
        interpretation = simulation_result['interpretation']
    elif 'scenario_result' in simulation_result:
        scenario = simulation_result['scenario_result']
        if 'interpretation' in scenario:
            interpretation = scenario['interpretation']
    
    if interpretation and isinstance(interpretation, dict):
        root_causes = interpretation.get('root_causes', [])
        if isinstance(root_causes, list):
            for cause in root_causes:
                if isinstance(cause, dict):
                    context_snapshot = {
                        'step_id': cause.get('step_id', ''),
                        'failure_mode': cause.get('dominant_failure_mode', ''),
                        'confidence': cause.get('confidence', 0.5)
                    }
                    
                    trace = create_decision_trace(
                        actor_type=actor_type,
                        context_snapshot=context_snapshot,
                        options_considered=[
                            {'diagnosis': cause.get('dominant_failure_mode', 'unknown')}
                        ],
                        chosen_action={
                            'action_type': 'diagnosis',
                            'failure_mode': cause.get('dominant_failure_mode', ''),
                            'step_id': cause.get('step_id', '')
                        },
                        rationale=cause.get('explanation', '') or cause.get('rationale', ''),
                        constraints=[],
                        confidence=cause.get('confidence', 0.5)
                    )
                    traces.append(trace)
    
    return traces


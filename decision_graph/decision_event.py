"""
decision_event.py - Decision Event Abstraction

Reframes each step as a decision event, not just a computation.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from decision_graph.decision_trace import DecisionTrace, DecisionOutcome


@dataclass
class DecisionEvent:
    """
    Decision Event - reframes step as event, not computation.
    
    Each step = decision event
    Each persona run = decision sequence
    Each simulation = decision history
    """
    step_id: str
    step_index: int
    traces: List[DecisionTrace]  # All traces for this step across all personas
    
    def get_continuation_rate(self) -> float:
        """Get continuation rate for this step."""
        if not self.traces:
            return 0.0
        continuations = sum(1 for t in self.traces if t.decision == DecisionOutcome.CONTINUE)
        return continuations / len(self.traces)
    
    def get_drop_rate(self) -> float:
        """Get drop rate for this step."""
        return 1.0 - self.get_continuation_rate()
    
    def get_dominant_factors(self) -> Dict[str, int]:
        """Get count of each dominant factor for drops."""
        drop_traces = [t for t in self.traces if t.decision == DecisionOutcome.DROP]
        factor_counts = {}
        for trace in drop_traces:
            for factor in trace.dominant_factors:
                factor_counts[factor] = factor_counts.get(factor, 0) + 1
        return factor_counts
    
    def get_persona_rejection_pattern(self) -> Dict[str, List[str]]:
        """
        Get which persona types were rejected at this step.
        
        Returns:
            Dict mapping persona_id -> dominant factors that caused rejection
        """
        rejection_pattern = {}
        for trace in self.traces:
            if trace.decision == DecisionOutcome.DROP:
                rejection_pattern[trace.persona_id] = trace.dominant_factors
        return rejection_pattern
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'step_id': self.step_id,
            'step_index': self.step_index,
            'continuation_rate': self.get_continuation_rate(),
            'drop_rate': self.get_drop_rate(),
            'dominant_factors': self.get_dominant_factors(),
            'rejection_pattern': self.get_persona_rejection_pattern(),
            'total_decisions': len(self.traces)
        }


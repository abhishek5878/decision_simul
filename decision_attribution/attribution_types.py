"""
Data types for decision attribution.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from datetime import datetime


@dataclass
class DecisionAttribution:
    """
    Game-theoretic attribution of decision forces.
    
    Quantifies which internal forces (effort, risk, value, trust, intent)
    contributed to a specific decision outcome.
    """
    step_id: str
    decision: str  # "CONTINUE" or "DROP"
    baseline_probability: float  # Probability with all features at baseline
    final_probability: float  # Actual probability after all forces
    
    # Shapley values (force contributions)
    shap_values: Dict[str, float]  # {force_name: relative_contribution} (normalized percentages)
    
    # Dominant forces (ranked by absolute contribution)
    dominant_forces: List[Tuple[str, float]]  # [(force_name, contribution), ...]
    
    # Raw values (optional, for transparency)
    shap_values_raw: Optional[Dict[str, float]] = None  # Raw SHAP values (not normalized)
    total_contribution: Optional[float] = None  # Total absolute contribution magnitude
    
    # Attribution metadata
    attribution_method: str = "shapley_values"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        result = {
            'step_id': self.step_id,
            'decision': self.decision,
            'baseline_probability': float(self.baseline_probability),
            'final_probability': float(self.final_probability),
            'shap_values': {k: float(v) for k, v in self.shap_values.items()},
            'dominant_forces': [(name, float(contrib)) for name, contrib in self.dominant_forces],
            'attribution_method': self.attribution_method,
            'timestamp': self.timestamp
        }
        # Include raw values if present
        if self.shap_values_raw is not None:
            result['shap_values_raw'] = {k: float(v) for k, v in self.shap_values_raw.items()}
        if self.total_contribution is not None:
            result['total_contribution'] = float(self.total_contribution)
        return result
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DecisionAttribution':
        """Create from dict."""
        return cls(
            step_id=data['step_id'],
            decision=data['decision'],
            baseline_probability=data['baseline_probability'],
            final_probability=data['final_probability'],
            shap_values=data['shap_values'],
            dominant_forces=[tuple(x) for x in data['dominant_forces']],
            shap_values_raw=data.get('shap_values_raw'),
            total_contribution=data.get('total_contribution'),
            attribution_method=data.get('attribution_method', 'shapley_values'),
            timestamp=data.get('timestamp', datetime.now().isoformat())
        )


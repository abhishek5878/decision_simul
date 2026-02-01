"""
Extended Decision Trace for Sensitivity Analysis

Captures detailed state transitions and force contributions.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List
from enum import Enum
from datetime import datetime


class DecisionOutcome(Enum):
    CONTINUE = "CONTINUE"
    DROP = "DROP"


@dataclass
class ForcesApplied:
    """
    Forces applied at a decision point.
    """
    effort: float = 0.0
    risk: float = 0.0
    value: float = 0.0
    trust: float = 0.0
    intent_mismatch: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'effort': float(self.effort),
            'risk': float(self.risk),
            'value': float(self.value),
            'trust': float(self.trust),
            'intent_mismatch': float(self.intent_mismatch)
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ForcesApplied':
        return cls(
            effort=data.get('effort', 0.0),
            risk=data.get('risk', 0.0),
            value=data.get('value', 0.0),
            trust=data.get('trust', 0.0),
            intent_mismatch=data.get('intent_mismatch', 0.0)
        )


@dataclass
class PersonaState:
    """
    Persona state at a decision point.
    """
    cognitive_energy: float
    risk_tolerance: float
    effort_tolerance: float
    intent_strength: float
    trust_baseline: float
    urgency: float
    value_expectation: float
    
    def to_dict(self) -> Dict:
        return {
            'cognitive_energy': float(self.cognitive_energy),
            'risk_tolerance': float(self.risk_tolerance),
            'effort_tolerance': float(self.effort_tolerance),
            'intent_strength': float(self.intent_strength),
            'trust_baseline': float(self.trust_baseline),
            'urgency': float(self.urgency),
            'value_expectation': float(self.value_expectation)
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PersonaState':
        return cls(
            cognitive_energy=data['cognitive_energy'],
            risk_tolerance=data['risk_tolerance'],
            effort_tolerance=data['effort_tolerance'],
            intent_strength=data['intent_strength'],
            trust_baseline=data['trust_baseline'],
            urgency=data['urgency'],
            value_expectation=data['value_expectation']
        )


@dataclass
class SensitivityDecisionTrace:
    """
    Extended decision trace for sensitivity analysis.
    
    Captures state before, forces applied, decision, state after.
    """
    step_id: str
    step_index: int
    persona_id: str
    
    # State before decision
    state_before: PersonaState
    
    # Forces applied at this step
    forces_applied: ForcesApplied
    
    # Decision outcome
    decision: DecisionOutcome
    
    # State after decision (may be modified by step)
    state_after: PersonaState
    
    # Continuation probability (before sampling)
    continuation_probability: float
    
    # Metadata
    experiment_id: str = "baseline"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            'step_id': self.step_id,
            'step_index': self.step_index,
            'persona_id': self.persona_id,
            'state_before': self.state_before.to_dict(),
            'forces_applied': self.forces_applied.to_dict(),
            'decision': self.decision.value,
            'state_after': self.state_after.to_dict(),
            'continuation_probability': float(self.continuation_probability),
            'experiment_id': self.experiment_id,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SensitivityDecisionTrace':
        return cls(
            step_id=data['step_id'],
            step_index=data['step_index'],
            persona_id=data['persona_id'],
            state_before=PersonaState.from_dict(data['state_before']),
            forces_applied=ForcesApplied.from_dict(data['forces_applied']),
            decision=DecisionOutcome(data['decision']),
            state_after=PersonaState.from_dict(data['state_after']),
            continuation_probability=data['continuation_probability'],
            experiment_id=data.get('experiment_id', 'baseline'),
            timestamp=data.get('timestamp', '')
        )


@dataclass
class ForceContribution:
    """
    Contribution of a force to a decision.
    
    Used for explainability (not prediction).
    """
    force_name: str
    contribution: float  # 0-1, relative contribution to decision
    
    def to_dict(self) -> Dict:
        return {
            'force_name': self.force_name,
            'contribution': float(self.contribution)
        }


def compute_force_contributions(
    state: PersonaState,
    forces: ForcesApplied,
    decision: DecisionOutcome
) -> List[ForceContribution]:
    """
    Compute relative contribution of each force to the decision.
    
    Uses SHAP-style local attribution logic.
    """
    # Map forces to state sensitivities
    # Higher force + lower tolerance = higher contribution to drop
    
    contributions = {}
    
    # Effort contribution: effort_demand vs effort_tolerance
    if forces.effort > 0:
        effort_deficit = max(0, forces.effort - state.effort_tolerance)
        contributions['effort'] = effort_deficit
    
    # Risk contribution: risk_signal vs risk_tolerance
    if forces.risk > 0:
        risk_deficit = max(0, forces.risk - state.risk_tolerance)
        contributions['risk'] = risk_deficit
    
    # Value contribution (negative - value reduces drop probability)
    if forces.value > 0:
        value_surplus = max(0, state.value_expectation - forces.value)
        contributions['value'] = value_surplus
    
    # Trust contribution: trust_signal vs trust_baseline
    if forces.trust > 0:
        trust_deficit = max(0, forces.trust - state.trust_baseline)
        contributions['trust'] = trust_deficit
    
    # Intent mismatch contribution: mismatch vs intent_strength
    if forces.intent_mismatch > 0:
        intent_deficit = max(0, forces.intent_mismatch - state.intent_strength)
        contributions['intent_mismatch'] = intent_deficit
    
    # Normalize to relative contributions (sum to 1.0)
    total = sum(contributions.values())
    if total > 0:
        contributions_normalized = {k: v / total for k, v in contributions.items()}
    else:
        # If no contributions, assign equal weights
        contributions_normalized = {k: 1.0 / len(contributions) for k in contributions.keys()}
    
    # Convert to list of ForceContribution objects
    result = [
        ForceContribution(force_name=k, contribution=v)
        for k, v in sorted(contributions_normalized.items(), key=lambda x: x[1], reverse=True)
    ]
    
    return result


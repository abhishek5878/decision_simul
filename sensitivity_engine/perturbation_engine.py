"""
Perturbation Engine for Decision Sensitivity Analysis

Implements controlled perturbations (one variable at a time).
"""

from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class PerturbationType(Enum):
    """Types of perturbations."""
    REDUCE_EFFORT = "reduce_effort"
    DELAY_STEP = "delay_step"
    INCREASE_VALUE_SIGNAL = "increase_value_signal"
    REMOVE_QUESTION = "remove_question"
    REDUCE_RISK = "reduce_risk"
    INCREASE_TRUST = "increase_trust"
    REDUCE_INTENT_MISMATCH = "reduce_intent_mismatch"


@dataclass
class Perturbation:
    """
    A single perturbation to apply.
    """
    perturbation_type: PerturbationType
    step_id: Optional[str] = None  # Which step to perturb
    step_index: Optional[int] = None  # Alternative: step index
    magnitude: float = 0.2  # How much to perturb (e.g., 0.2 = 20% reduction)
    delay_by_steps: Optional[int] = None  # For DELAY_STEP type
    experiment_id: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'perturbation_type': self.perturbation_type.value,
            'step_id': self.step_id,
            'step_index': self.step_index,
            'magnitude': float(self.magnitude),
            'delay_by_steps': self.delay_by_steps,
            'experiment_id': self.experiment_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Perturbation':
        return cls(
            perturbation_type=PerturbationType(data['perturbation_type']),
            step_id=data.get('step_id'),
            step_index=data.get('step_index'),
            magnitude=data.get('magnitude', 0.2),
            delay_by_steps=data.get('delay_by_steps'),
            experiment_id=data.get('experiment_id', '')
        )


class PerturbationEngine:
    """
    Applies perturbations to product step configurations.
    """
    
    def __init__(self):
        self.perturbation_handlers = {
            PerturbationType.REDUCE_EFFORT: self._reduce_effort,
            PerturbationType.DELAY_STEP: self._delay_step,
            PerturbationType.INCREASE_VALUE_SIGNAL: self._increase_value_signal,
            PerturbationType.REMOVE_QUESTION: self._remove_question,
            PerturbationType.REDUCE_RISK: self._reduce_risk,
            PerturbationType.INCREASE_TRUST: self._increase_trust,
            PerturbationType.REDUCE_INTENT_MISMATCH: self._reduce_intent_mismatch,
        }
    
    def apply_perturbation(
        self,
        product_steps: Dict,
        perturbation: Perturbation
    ) -> Dict:
        """
        Apply a single perturbation to product steps.
        
        Returns a new dictionary (does not modify original).
        """
        # Deep copy to avoid modifying original
        import copy
        perturbed_steps = copy.deepcopy(product_steps)
        
        # Get handler
        handler = self.perturbation_handlers.get(perturbation.perturbation_type)
        if not handler:
            raise ValueError(f"Unknown perturbation type: {perturbation.perturbation_type}")
        
        # Apply perturbation
        return handler(perturbed_steps, perturbation)
    
    def _reduce_effort(self, steps: Dict, pert: Perturbation) -> Dict:
        """Reduce effort demand at a step."""
        step_key = self._get_step_key(steps, pert)
        if step_key and step_key in steps:
            steps[step_key]['effort_demand'] = max(0.0, 
                steps[step_key].get('effort_demand', 0.5) * (1 - pert.magnitude))
        return steps
    
    def _delay_step(self, steps: Dict, pert: Perturbation) -> Dict:
        """Delay a step by N positions."""
        if pert.delay_by_steps is None:
            return steps
        
        # Convert to list for reordering
        step_items = list(steps.items())
        
        # Find step to delay
        step_index = pert.step_index if pert.step_index is not None else self._find_step_index(steps, pert.step_id)
        if step_index is None or step_index >= len(step_items):
            return steps
        
        # Remove step
        step_to_delay = step_items.pop(step_index)
        
        # Insert at new position
        new_index = min(step_index + pert.delay_by_steps, len(step_items))
        step_items.insert(new_index, step_to_delay)
        
        # Reconstruct dict
        return dict(step_items)
    
    def _increase_value_signal(self, steps: Dict, pert: Perturbation) -> Dict:
        """Increase value signal at a step."""
        step_key = self._get_step_key(steps, pert)
        if step_key and step_key in steps:
            steps[step_key]['explicit_value'] = min(1.0,
                steps[step_key].get('explicit_value', 0.5) + pert.magnitude)
        return steps
    
    def _remove_question(self, steps: Dict, pert: Perturbation) -> Dict:
        """Remove a step entirely."""
        step_key = self._get_step_key(steps, pert)
        if step_key and step_key in steps:
            del steps[step_key]
        return steps
    
    def _reduce_risk(self, steps: Dict, pert: Perturbation) -> Dict:
        """Reduce risk signal at a step."""
        step_key = self._get_step_key(steps, pert)
        if step_key and step_key in steps:
            steps[step_key]['risk_signal'] = max(0.0,
                steps[step_key].get('risk_signal', 0.5) * (1 - pert.magnitude))
        return steps
    
    def _increase_trust(self, steps: Dict, pert: Perturbation) -> Dict:
        """Increase trust/reassurance signal at a step."""
        step_key = self._get_step_key(steps, pert)
        if step_key and step_key in steps:
            steps[step_key]['reassurance_signal'] = min(1.0,
                steps[step_key].get('reassurance_signal', 0.5) + pert.magnitude)
        return steps
    
    def _reduce_intent_mismatch(self, steps: Dict, pert: Perturbation) -> Dict:
        """Reduce intent mismatch (increase alignment)."""
        step_key = self._get_step_key(steps, pert)
        if step_key and step_key in steps:
            # Increase intent alignment in intent_signals
            if 'intent_signals' in steps[step_key]:
                for intent_key in steps[step_key]['intent_signals']:
                    steps[step_key]['intent_signals'][intent_key] = min(1.0,
                        steps[step_key]['intent_signals'][intent_key] + pert.magnitude)
        return steps
    
    def _get_step_key(self, steps: Dict, pert: Perturbation) -> Optional[str]:
        """Get step key from perturbation."""
        if pert.step_id:
            # Try to find by step_id
            for key in steps.keys():
                if key == pert.step_id:
                    return key
        elif pert.step_index is not None:
            # Get by index
            step_list = list(steps.keys())
            if 0 <= pert.step_index < len(step_list):
                return step_list[pert.step_index]
        return None
    
    def _find_step_index(self, steps: Dict, step_id: Optional[str]) -> Optional[int]:
        """Find step index by step_id."""
        if not step_id:
            return None
        step_list = list(steps.keys())
        for i, key in enumerate(step_list):
            if key == step_id:
                return i
        return None


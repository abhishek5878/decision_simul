"""
Sensitivity Simulator

Runs personas through product flows and captures detailed decision traces.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np

from sensitivity_engine.fixed_personas import FixedPersona
from sensitivity_engine.decision_trace_extended import (
    SensitivityDecisionTrace,
    ForcesApplied,
    PersonaState,
    DecisionOutcome
)


@dataclass
class SimulationConfig:
    """Configuration for sensitivity simulation."""
    experiment_id: str = "baseline"
    product_name: str = ""
    seed: int = 42


class SensitivitySimulator:
    """
    Simulates personas through product flows and captures decision traces.
    
    Integrates with existing behavioral engine to extract state transitions.
    """
    
    def __init__(self, behavioral_engine_module):
        """
        Initialize with behavioral engine module.
        
        Args:
            behavioral_engine_module: Module containing simulation functions
        """
        self.behavioral_engine = behavioral_engine_module
    
    def simulate_personas(
        self,
        personas: List[FixedPersona],
        product_steps: Dict,
        intent_frame,
        config: SimulationConfig
    ) -> List[SensitivityDecisionTrace]:
        """
        Simulate all personas through product flow.
        
        Returns detailed decision traces for sensitivity analysis.
        """
        traces = []
        
        for persona in personas:
            persona_traces = self._simulate_single_persona(
                persona, product_steps, intent_frame, config
            )
            traces.extend(persona_traces)
        
        return traces
    
    def _simulate_single_persona(
        self,
        persona: FixedPersona,
        product_steps: Dict,
        intent_frame,
        config: SimulationConfig
    ) -> List[SensitivityDecisionTrace]:
        """
        Simulate a single persona through the flow.
        
        Returns decision traces for each step.
        """
        traces = []
        
        # Initialize state from persona
        current_state = PersonaState(
            cognitive_energy=persona.cognitive_energy,
            risk_tolerance=persona.risk_tolerance,
            effort_tolerance=persona.effort_tolerance,
            intent_strength=persona.intent_strength,
            trust_baseline=persona.trust_baseline,
            urgency=persona.urgency,
            value_expectation=persona.value_expectation
        )
        
        # Process each step
        step_list = list(product_steps.items())
        
        for step_index, (step_id, step_config) in enumerate(step_list):
            # Compute forces applied at this step
            forces = self._compute_forces(step_config, current_state, intent_frame)
            
            # Compute continuation probability
            continuation_prob = self._compute_continuation_probability(
                current_state, forces
            )
            
            # Sample decision
            decision = self._sample_decision(continuation_prob, config.seed + step_index)
            
            # Create trace
            state_after = self._update_state(current_state, step_config, decision)
            
            trace = SensitivityDecisionTrace(
                step_id=step_id,
                step_index=step_index,
                persona_id=persona.persona_id,
                state_before=current_state,
                forces_applied=forces,
                decision=decision,
                state_after=state_after,
                continuation_probability=continuation_prob,
                experiment_id=config.experiment_id
            )
            
            traces.append(trace)
            
            # Update state for next step
            current_state = state_after
            
            # Stop if dropped
            if decision == DecisionOutcome.DROP:
                break
        
        return traces
    
    def _compute_forces(
        self,
        step_config: Dict,
        state: PersonaState,
        intent_frame
    ) -> ForcesApplied:
        """
        Compute forces applied at a step.
        
        This extracts forces from step configuration and persona state.
        """
        # Effort force
        effort_demand = step_config.get('effort_demand', 0.5)
        effort_force = max(0, effort_demand - state.effort_tolerance)
        
        # Risk force
        risk_signal = step_config.get('risk_signal', 0.5)
        risk_force = max(0, risk_signal - state.risk_tolerance)
        
        # Value force (negative - value reduces drop probability)
        explicit_value = step_config.get('explicit_value', 0.5)
        value_force = max(0, state.value_expectation - explicit_value)
        
        # Trust force
        reassurance = step_config.get('reassurance_signal', 0.5)
        trust_force = max(0, 1.0 - reassurance - state.trust_baseline)
        
        # Intent mismatch force
        intent_signals = step_config.get('intent_signals', {})
        if intent_signals:
            max_alignment = max(intent_signals.values()) if intent_signals else 0.5
            intent_mismatch = max(0, state.intent_strength - max_alignment)
        else:
            intent_mismatch = 0.0
        
        return ForcesApplied(
            effort=effort_force,
            risk=risk_force,
            value=value_force,
            trust=trust_force,
            intent_mismatch=intent_mismatch
        )
    
    def _compute_continuation_probability(
        self,
        state: PersonaState,
        forces: ForcesApplied
    ) -> float:
        """
        Compute continuation probability from state and forces.
        
        Simplified model: base probability reduced by forces.
        """
        # Base probability
        base_prob = 0.8
        
        # Reduce by forces
        effort_penalty = forces.effort * 0.3
        risk_penalty = forces.risk * 0.25
        value_bonus = forces.value * 0.2  # Negative force, so bonus
        trust_penalty = forces.trust * 0.15
        intent_penalty = forces.intent_mismatch * 0.2
        
        continuation_prob = base_prob - effort_penalty - risk_penalty - trust_penalty - intent_penalty + value_bonus
        
        # Clamp to [0.05, 0.95]
        continuation_prob = max(0.05, min(0.95, continuation_prob))
        
        return continuation_prob
    
    def _sample_decision(
        self,
        continuation_prob: float,
        seed: int
    ) -> DecisionOutcome:
        """Sample decision from continuation probability."""
        rng = np.random.default_rng(seed)
        if rng.random() < continuation_prob:
            return DecisionOutcome.CONTINUE
        else:
            return DecisionOutcome.DROP
    
    def _update_state(
        self,
        state: PersonaState,
        step_config: Dict,
        decision: DecisionOutcome
    ) -> PersonaState:
        """
        Update state after a step.
        
        State degrades slightly with each step (cognitive fatigue).
        """
        # Cognitive energy decreases
        cognitive_demand = step_config.get('cognitive_demand', 0.3)
        new_energy = max(0.0, state.cognitive_energy - cognitive_demand * 0.1)
        
        # Other state variables remain relatively stable
        # (in a full implementation, these could be modified by step outcomes)
        
        return PersonaState(
            cognitive_energy=new_energy,
            risk_tolerance=state.risk_tolerance,
            effort_tolerance=state.effort_tolerance,
            intent_strength=state.intent_strength,
            trust_baseline=state.trust_baseline,
            urgency=state.urgency,
            value_expectation=state.value_expectation
        )


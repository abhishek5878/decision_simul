"""
Dominant Belief Break Analyzer

Calculates the dominant belief break through counterfactual analysis.
The dominant belief break is the earliest step which when neutralized 
causes a structural shift in downstream failures.
"""

import json
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import numpy as np

from decision_graph.decision_trace import DecisionTrace, DecisionOutcome


class DominantBeliefBreakAnalyzer:
    """
    Analyzes which step, when neutralized, causes the largest structural shift
    in downstream failures.
    """
    
    def __init__(self, product_steps: Dict[str, Dict]):
        """
        Initialize analyzer.
        
        Args:
            product_steps: Dictionary mapping step_id to step definition
        """
        self.product_steps = product_steps
        self.step_order = list(product_steps.keys())
    
    def compute_baseline_downstream_failures(self, traces: List[DecisionTrace], step_id: str) -> float:
        """
        Compute baseline downstream failure rate for a given step.
        
        Returns the fraction of personas that drop at or after this step.
        """
        # Get all personas that reached this step
        step_index = self.step_order.index(step_id) if step_id in self.step_order else -1
        if step_index == -1:
            return 0.0
        
        # Group traces by persona
        persona_journeys = defaultdict(list)
        for trace in traces:
            base_persona = trace.persona_id.split('_')[0] if '_' in trace.persona_id else trace.persona_id
            persona_journeys[base_persona].append(trace)
        
        # For each persona that reached this step, check if they failed downstream
        personas_reached = set()
        personas_failed_downstream = set()
        
        for persona_id, journey in persona_journeys.items():
            journey.sort(key=lambda t: t.step_index)
            
            # Check if persona reached this step
            reached_step = any(t.step_id == step_id and t.decision == DecisionOutcome.CONTINUE 
                              for t in journey)
            if not reached_step:
                # Check if they dropped at this step (they reached it but dropped)
                dropped_at_step = any(t.step_id == step_id and t.decision == DecisionOutcome.DROP 
                                     for t in journey)
                if dropped_at_step:
                    reached_step = True
            
            if reached_step:
                personas_reached.add(persona_id)
                
                # Check downstream failures (drops at later steps)
                for trace in journey:
                    if trace.step_index > step_index and trace.decision == DecisionOutcome.DROP:
                        personas_failed_downstream.add(persona_id)
                        break
        
        if len(personas_reached) == 0:
            return 0.0
        
        return len(personas_failed_downstream) / len(personas_reached)
    
    def simulate_neutralization(self, traces: List[DecisionTrace], step_id: str, 
                               neutralization_type: str = "value_delay") -> List[DecisionTrace]:
        """
        Simulate neutralizing a step by modifying traces.
        
        Neutralization methods:
        - value_delay: Assume value is shown earlier (reduce delay_to_value)
        - irreversibility: Make step reversible (set irreversibility to 0)
        - commitment: Reduce commitment demand (reduce effort/risk)
        - trust: Add trust signals (increase trust baseline)
        
        Returns modified traces (simulated).
        """
        step_index = self.step_order.index(step_id) if step_id in self.step_order else -1
        if step_index == -1:
            return traces
        
        # For now, we'll simulate by modifying the decision probability
        # In a full implementation, this would re-run the behavioral engine
        # with modified step parameters
        
        modified_traces = []
        
        for trace in traces:
            if trace.step_id == step_id:
                # Simulate neutralization effect
                # If step is neutralized, continuation probability increases
                if trace.decision == DecisionOutcome.DROP:
                    # Simulate: if step was neutralized, some drops become continues
                    # Use a probability based on neutralization type
                    if neutralization_type == "value_delay":
                        # Value shown earlier -> higher continuation probability
                        # Assume 40% of drops would continue
                        continue_prob = 0.4
                    elif neutralization_type == "irreversibility":
                        # Made reversible -> 50% of drops would continue
                        continue_prob = 0.5
                    elif neutralization_type == "commitment":
                        # Reduced commitment -> 35% of drops would continue
                        continue_prob = 0.35
                    elif neutralization_type == "trust":
                        # Added trust -> 45% of drops would continue
                        continue_prob = 0.45
                    else:
                        continue_prob = 0.4
                    
                    # Simulate: with probability continue_prob, this becomes a continue
                    # We'll use the original probability_before_sampling as a proxy
                    if trace.probability_before_sampling < (1 - continue_prob):
                        # Create a modified trace that continues
                        modified_trace = DecisionTrace(
                            persona_id=trace.persona_id,
                            step_id=trace.step_id,
                            step_index=trace.step_index,
                            decision=DecisionOutcome.CONTINUE,
                            probability_before_sampling=min(1.0, trace.probability_before_sampling + continue_prob),
                            sampled_outcome=True,
                            cognitive_state_snapshot=trace.cognitive_state_snapshot,
                            intent=trace.intent,
                            dominant_factors=trace.dominant_factors,
                            attribution=trace.attribution,
                            policy_version=trace.policy_version,
                            timestamp=trace.timestamp
                        )
                        modified_traces.append(modified_trace)
                    else:
                        modified_traces.append(trace)
                else:
                    modified_traces.append(trace)
            else:
                modified_traces.append(trace)
        
        return modified_traces
    
    def compute_structural_shift(self, baseline_failures: float, 
                                  neutralized_failures: float) -> float:
        """
        Compute structural shift from neutralization.
        
        Returns the reduction in downstream failure rate.
        """
        if baseline_failures == 0:
            return 0.0
        
        shift = baseline_failures - neutralized_failures
        return max(0.0, shift)  # Only positive shifts
    
    def find_dominant_belief_break(self, traces: List[DecisionTrace], 
                                   neutralization_type: str = "value_delay",
                                   min_shift_threshold: float = 0.05) -> Optional[Tuple[str, float, Dict]]:
        """
        Find the dominant belief break through counterfactual analysis.
        
        Returns:
            Tuple of (step_id, structural_shift, analysis_details) or None
        """
        shifts = []
        
        # Analyze each step in order
        for step_id in self.step_order:
            # Compute baseline downstream failures
            baseline_failures = self.compute_baseline_downstream_failures(traces, step_id)
            
            # Simulate neutralization
            neutralized_traces = self.simulate_neutralization(traces, step_id, neutralization_type)
            
            # Compute neutralized downstream failures
            neutralized_failures = self.compute_baseline_downstream_failures(neutralized_traces, step_id)
            
            # Compute structural shift
            shift = self.compute_structural_shift(baseline_failures, neutralized_failures)
            
            shifts.append({
                'step_id': step_id,
                'step_index': self.step_order.index(step_id),
                'baseline_failures': baseline_failures,
                'neutralized_failures': neutralized_failures,
                'structural_shift': shift,
                'shift_percentage': (shift / baseline_failures * 100) if baseline_failures > 0 else 0.0
            })
        
        # Find earliest step with maximum structural shift above threshold
        valid_shifts = [s for s in shifts if s['structural_shift'] >= min_shift_threshold]
        
        if not valid_shifts:
            return None
        
        # Sort by step_index (earliest first), then by structural_shift (largest first)
        valid_shifts.sort(key=lambda x: (x['step_index'], -x['structural_shift']))
        
        # The dominant belief break is the earliest step with significant shift
        dominant = valid_shifts[0]
        
        # But if there's a later step with much larger shift, prefer that
        max_shift = max(s['structural_shift'] for s in valid_shifts)
        if max_shift > dominant['structural_shift'] * 1.5:
            # Find earliest step with shift close to max
            for s in valid_shifts:
                if s['structural_shift'] >= max_shift * 0.8:
                    dominant = s
                    break
        
        return (
            dominant['step_id'],
            dominant['structural_shift'],
            {
                'baseline_failures': dominant['baseline_failures'],
                'neutralized_failures': dominant['neutralized_failures'],
                'shift_percentage': dominant['shift_percentage'],
                'all_shifts': shifts
            }
        )
    
    def analyze_all_neutralization_types(self, traces: List[DecisionTrace]) -> Dict[str, Optional[Tuple[str, float, Dict]]]:
        """
        Analyze all neutralization types and return the best one.
        """
        results = {}
        neutralization_types = ["value_delay", "irreversibility", "commitment", "trust"]
        
        for ntype in neutralization_types:
            result = self.find_dominant_belief_break(traces, neutralization_type=ntype)
            results[ntype] = result
        
        return results


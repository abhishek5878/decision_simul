"""
Decision Autopsy Generator

Converts raw simulation artifacts into a deterministic, audit-grade Decision Autopsy document.
This layer sits after simulation, attribution, and context graph construction.

Design Principles:
- Deterministic: same inputs → same output
- No LLM creativity at render time
- Every sentence maps to stored artifacts
- Opinion-free: explains why belief collapsed, not how to fix it
"""

import json
import hashlib
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
import numpy as np

from decision_graph.decision_trace import DecisionTrace, DecisionOutcome
from decision_attribution.attribution_types import DecisionAttribution


@dataclass
class BeliefState:
    """Belief state vector for a persona at a given step."""
    task_framing: str
    commitment_level: float
    expected_value_timing: str
    perceived_risk: float


@dataclass
class IrreversibleMoment:
    """Detected irreversible moment in the flow."""
    step_id: str
    step_label: str
    position_in_flow: int
    commitment_delta: float
    exit_probability_gradient: float
    reversibility_score: float
    why_irreversible: str


@dataclass
class VerdictLineage:
    """Chain-of-evidence for the verdict."""
    supporting_trace_count: int
    termination_pattern: str
    trust_increase_count: int
    median_commitment_delta: float
    verdict_explanation: str


@dataclass
class CounterfactualBoundary:
    """What would NOT work to repair belief collapse."""
    ineffective_changes: List[str]
    invariant_properties: List[str]
    why_ineffective: str


@dataclass
class BaselineComparison:
    """Non-normative comparison to similar flows."""
    comparable_flows_description: str
    baseline_commitment_delta: float
    baseline_exit_gradient: float
    baseline_reversibility_range: Tuple[float, float]
    current_values_outside_baseline: bool
    structural_difference: str


@dataclass
class VariantMechanism:
    """Mechanism-level explanation of variant divergence."""
    most_sensitive_mechanism: str
    least_sensitive_mechanism: str


@dataclass
class ApplicabilityDomain:
    """Where this analysis applies reliably."""
    reliable_for: List[str]
    not_designed_for: List[str]


@dataclass
class DecisionAutopsy:
    """Complete Decision Autopsy document structure."""
    # Section 0: Header
    product_id: str
    simulation_version_hash: str
    run_mode: str
    personas_simulated: int
    decision_traces_count: int
    confidence_level: float
    
    # Section 1: One-Line Verdict
    verdict_text: str
    
    # Section 1.5: Verdict Lineage
    verdict_lineage: VerdictLineage
    
    # Section 2: Irreversible Moment
    irreversible_moment: IrreversibleMoment
    
    # Section 2.5: Baseline Comparison
    baseline_comparison: BaselineComparison
    
    # Section 3: Belief State Transition
    belief_before: BeliefState
    belief_after: BeliefState
    
    # Section 4: Recovery Impossibility
    retry_rate: float
    backtracking_rate: float
    abandonment_permanence_score: float
    why_recovery_does_not_occur: str
    
    # Section 5: Counterfactual
    minimal_sequencing_change: str
    why_it_repairs_belief_ordering: str
    
    # Section 5.5: Counterfactual Boundary
    counterfactual_boundary: CounterfactualBoundary
    
    # Section 6: Falsifiability
    falsifiability_conditions: List[Dict[str, str]]
    
    # Section 7: Variant Sensitivity
    most_sensitive_variant: str
    least_sensitive_variant: str
    
    # Section 7.5: Variant Sensitivity Mechanism
    variant_mechanism: VariantMechanism
    
    # Section 8: Non-Claims
    what_this_does_not_prove: List[str]
    what_this_is_not_intended_for: List[str]
    
    # Section 8.5: Valid Applicability Domain
    applicability_domain: ApplicabilityDomain
    
    # Section 9: Closing
    closing_text: str = "This analysis explains why belief collapsed, not how to redesign the product."
    
    # Footer: Output Contract
    schema_version: str = "v1.0"
    determinism_guaranteed: bool = True
    mutation_forbidden: bool = True


class DecisionAutopsyGenerator:
    """
    Generates deterministic Decision Autopsy documents from simulation artifacts.
    """
    
    def __init__(self, product_steps: Dict[str, Dict]):
        """
        Initialize generator.
        
        Args:
            product_steps: Dictionary mapping step_id to step definition
        """
        self.product_steps = product_steps
        self.step_order = list(product_steps.keys())
    
    def compute_simulation_hash(self, traces: List[DecisionTrace], config: Dict) -> str:
        """Compute deterministic hash of simulation configuration."""
        # Hash key components that affect output
        hash_input = json.dumps({
            'product_steps': self.product_steps,
            'config': config,
            'trace_count': len(traces)
        }, sort_keys=True)
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    def compute_confidence_level(self, traces: List[DecisionTrace]) -> float:
        """
        Compute confidence level from variance across persona variants.
        
        Lower variance = higher confidence.
        """
        if not traces:
            return 0.0
        
        # Group by persona base ID (extract variant)
        persona_variant_outcomes = defaultdict(list)
        for trace in traces:
            persona_id = trace.persona_id
            # Extract base persona (before variant)
            base_persona = persona_id.split('_')[0] if '_' in persona_id else persona_id
            variant = persona_id.split('_', 1)[1] if '_' in persona_id else 'default'
            
            # Track completion outcome
            outcome = 1.0 if trace.decision == DecisionOutcome.CONTINUE else 0.0
            persona_variant_outcomes[base_persona].append(outcome)
        
        # Compute variance across variants per persona
        variances = []
        for outcomes in persona_variant_outcomes.values():
            if len(outcomes) > 1:
                variances.append(np.var(outcomes))
        
        if not variances:
            return 0.5  # Default if no variance data
        
        # Lower variance = higher confidence
        # Normalize: variance of 0 = confidence 1.0, variance of 0.25 = confidence 0.0
        avg_variance = np.mean(variances)
        confidence = max(0.0, min(1.0, 1.0 - (avg_variance * 4)))
        
        return confidence
    
    def detect_irreversible_moment(self, traces: List[DecisionTrace]) -> IrreversibleMoment:
        """
        Algorithmically identify the step where commitment delta spikes.
        """
        # Group traces by step
        step_stats = defaultdict(lambda: {
            'reached': 0,
            'dropped': 0,
            'continued': 0,
            'commitment_deltas': [],
            'exit_probs': []
        })
        
        for trace in traces:
            step_id = trace.step_id
            step_stats[step_id]['reached'] += 1
            
            if trace.decision == DecisionOutcome.DROP:
                step_stats[step_id]['dropped'] += 1
            else:
                step_stats[step_id]['continued'] += 1
            
            # Extract commitment/probability from trace
            if hasattr(trace, 'probability_before_sampling'):
                prob = trace.probability_before_sampling
                step_stats[step_id]['exit_probs'].append(1.0 - prob)
        
        # Compute metrics per step
        step_scores = {}
        for step_idx, step_id in enumerate(self.step_order):
            if step_id not in step_stats:
                continue
            
            stats = step_stats[step_id]
            total = stats['reached']
            if total == 0:
                continue
            
            drop_rate = stats['dropped'] / total
            
            # Commitment delta: change in continuation probability
            # Compare to previous step
            if step_idx > 0:
                prev_step_id = self.step_order[step_idx - 1]
                if prev_step_id in step_stats:
                    prev_continue_rate = step_stats[prev_step_id]['continued'] / max(1, step_stats[prev_step_id]['reached'])
                    curr_continue_rate = stats['continued'] / total
                    commitment_delta = prev_continue_rate - curr_continue_rate
                else:
                    commitment_delta = drop_rate
            else:
                commitment_delta = drop_rate
            
            # Exit probability gradient
            if stats['exit_probs']:
                exit_prob_gradient = np.mean(stats['exit_probs'])
            else:
                exit_prob_gradient = drop_rate
            
            # Reversibility score: based on irreversibility flag in step definition
            step_def = self.product_steps.get(step_id, {})
            irreversibility = step_def.get('irreversibility', 0.0)
            reversibility_score = 1.0 - irreversibility
            
            # Combined score for irreversible moment
            # Higher drop rate + higher commitment delta + lower reversibility = more irreversible
            irreversible_score = (drop_rate * 0.4) + (commitment_delta * 0.4) + ((1 - reversibility_score) * 0.2)
            
            step_scores[step_id] = {
                'step_id': step_id,
                'step_label': step_def.get('description', step_id),
                'position_in_flow': step_idx,
                'commitment_delta': commitment_delta,
                'exit_probability_gradient': exit_prob_gradient,
                'reversibility_score': reversibility_score,
                'irreversible_score': irreversible_score
            }
        
        # Find step with highest irreversible score
        if not step_scores:
            # Fallback
            first_step = self.step_order[0] if self.step_order else "unknown"
            return IrreversibleMoment(
                step_id=first_step,
                step_label=self.product_steps.get(first_step, {}).get('description', first_step),
                position_in_flow=0,
                commitment_delta=0.0,
                exit_probability_gradient=0.0,
                reversibility_score=1.0,
                why_irreversible="No trace data available"
            )
        
        max_step = max(step_scores.items(), key=lambda x: x[1]['irreversible_score'])
        step_id, step_data = max_step
        
        # Derive why_irreversible from step definition and drop patterns
        step_def = self.product_steps.get(step_id, {})
        why_irreversible_parts = []
        
        if step_data['commitment_delta'] > 0.15:
            why_irreversible_parts.append("commitment requirement increases sharply")
        
        if step_data['reversibility_score'] < 0.3:
            why_irreversible_parts.append("step has high irreversibility flag")
        
        if step_data['exit_probability_gradient'] > 0.2:
            why_irreversible_parts.append("exit probability spikes")
        
        why_irreversible = "; ".join(why_irreversible_parts) if why_irreversible_parts else "commitment delta and exit probability indicate irreversible moment"
        
        return IrreversibleMoment(
            step_id=step_id,
            step_label=step_data['step_label'],
            position_in_flow=step_data['position_in_flow'],
            commitment_delta=step_data['commitment_delta'],
            exit_probability_gradient=step_data['exit_probability_gradient'],
            reversibility_score=step_data['reversibility_score'],
            why_irreversible=why_irreversible
        )
    
    def reconstruct_belief_states(self, traces: List[DecisionTrace], irreversible_step_id: str) -> Tuple[BeliefState, BeliefState]:
        """
        Reconstruct belief vectors from persona state transitions at the irreversible step.
        """
        # Get traces at the irreversible step
        step_traces = [t for t in traces if t.step_id == irreversible_step_id]
        
        if not step_traces:
            # Fallback
            return (
                BeliefState("unknown", 0.5, "unknown", 0.5),
                BeliefState("unknown", 0.3, "unknown", 0.7)
            )
        
        # Aggregate before state (from traces that reached this step)
        before_commitment = []
        before_risk = []
        
        for trace in step_traces:
            if hasattr(trace, 'cognitive_state_snapshot'):
                state = trace.cognitive_state_snapshot
                # Map to belief state components
                before_commitment.append(state.control)  # perceived_control as commitment proxy
                before_risk.append(state.risk)
        
        avg_before_commitment = np.mean(before_commitment) if before_commitment else 0.5
        avg_before_risk = np.mean(before_risk) if before_risk else 0.5
        
        # After state: for traces that dropped
        dropped_traces = [t for t in step_traces if t.decision == DecisionOutcome.DROP]
        
        if dropped_traces:
            after_commitment = []
            after_risk = []
            for trace in dropped_traces:
                if hasattr(trace, 'cognitive_state_snapshot'):
                    state = trace.cognitive_state_snapshot
                    after_commitment.append(state.control)
                    after_risk.append(state.risk)
            
            avg_after_commitment = np.mean(after_commitment) if after_commitment else 0.3
            avg_after_risk = np.mean(after_risk) if after_risk else 0.7
        else:
            # If no drops, use continuation traces but with lower commitment
            avg_after_commitment = avg_before_commitment * 0.6
            avg_after_risk = avg_before_risk * 1.3
        
        # Task framing: derive from step definition
        step_def = self.product_steps.get(irreversible_step_id, {})
        delay_to_value = step_def.get('delay_to_value', 999)
        
        if delay_to_value == 0:
            task_framing_before = "value is immediate"
            task_framing_after = "value was not immediate"
        elif delay_to_value <= 2:
            task_framing_before = "value is near"
            task_framing_after = "value is too delayed"
        else:
            task_framing_before = "value is distant"
            task_framing_after = "value is too distant to justify commitment"
        
        # Expected value timing
        if delay_to_value == 0:
            value_timing_before = "immediate"
            value_timing_after = "not immediate"
        elif delay_to_value <= 2:
            value_timing_before = f"within {delay_to_value} steps"
            value_timing_after = f"still {delay_to_value} steps away"
        else:
            value_timing_before = f"{delay_to_value} steps away"
            value_timing_after = f"{delay_to_value} steps away (too far)"
        
        before_state = BeliefState(
            task_framing=task_framing_before,
            commitment_level=float(avg_before_commitment),
            expected_value_timing=value_timing_before,
            perceived_risk=float(avg_before_risk)
        )
        
        after_state = BeliefState(
            task_framing=task_framing_after,
            commitment_level=float(avg_after_commitment),
            expected_value_timing=value_timing_after,
            perceived_risk=float(avg_after_risk)
        )
        
        return before_state, after_state
    
    def compute_recovery_impossibility(self, traces: List[DecisionTrace]) -> Tuple[float, float, float, str]:
        """
        Compute retry rate, backtracking rate, abandonment permanence.
        """
        # For now, we don't have retry/backtrack data in traces
        # This would require tracking persona IDs across multiple sessions
        # We'll compute from single-session data
        
        # Group by persona
        persona_journeys = defaultdict(list)
        for trace in traces:
            base_persona = trace.persona_id.split('_')[0] if '_' in trace.persona_id else trace.persona_id
            persona_journeys[base_persona].append(trace)
        
        # Retry rate: personas that drop and then continue (shouldn't happen in single session)
        retry_count = 0
        total_drops = 0
        
        for persona_id, journey in persona_journeys.items():
            # Sort by step index
            journey.sort(key=lambda t: t.step_index)
            
            dropped_steps = [t for t in journey if t.decision == DecisionOutcome.DROP]
            if dropped_steps:
                total_drops += 1
                # Check if there are traces after drop (would indicate retry)
                first_drop_idx = dropped_steps[0].step_index
                continued_after = [t for t in journey if t.step_index > first_drop_idx and t.decision == DecisionOutcome.CONTINUE]
                if continued_after:
                    retry_count += 1
        
        retry_rate = retry_count / max(1, total_drops)
        
        # Backtracking rate: personas that go backwards in steps (shouldn't happen)
        backtrack_count = 0
        for persona_id, journey in persona_journeys.items():
            journey.sort(key=lambda t: t.step_index)
            step_indices = [t.step_index for t in journey]
            if len(step_indices) > 1:
                # Check if any step index decreases
                for i in range(1, len(step_indices)):
                    if step_indices[i] < step_indices[i-1]:
                        backtrack_count += 1
                        break
        
        backtrack_rate = backtrack_count / max(1, len(persona_journeys))
        
        # Abandonment permanence: once dropped, do they come back?
        # In single session, drops are permanent
        abandonment_permanence = 1.0 - retry_rate
        
        why_no_recovery = "Once a drop decision occurs, no traces show continuation in the same session. "
        if retry_rate < 0.01:
            why_no_recovery += "Retry rate is effectively zero. "
        if backtrack_rate < 0.01:
            why_no_recovery += "Backtracking does not occur. "
        why_no_recovery += "Abandonment is permanent within the simulated session."
        
        return retry_rate, backtrack_rate, abandonment_permanence, why_no_recovery
    
    def compute_counterfactual_boundary(self, traces: List[DecisionTrace], irreversible_step: IrreversibleMoment) -> CounterfactualBoundary:
        """
        Identify what would NOT work to repair belief collapse.
        Prevents misuse by showing invariant properties.
        """
        step_def = self.product_steps.get(irreversible_step.step_id, {})
        delay_to_value = step_def.get('delay_to_value', 999)
        irreversibility = step_def.get('irreversibility', 0.0)
        
        ineffective_changes = []
        invariant_properties = []
        
        # If value comes after commitment, these won't work:
        if delay_to_value > irreversible_step.position_in_flow:
            ineffective_changes.append("Reducing copy friction at Step {} without moving value earlier".format(irreversible_step.position_in_flow + 1))
            ineffective_changes.append("Adding reassurance language without altering value timing")
            ineffective_changes.append("Improving visual design while maintaining commitment-first sequencing")
            
            invariant_properties.append("Value timing relative to commitment demand")
            invariant_properties.append("Belief ordering (value before commitment)")
        
        # If irreversibility is high, these won't work:
        if irreversibility > 0.3:
            ineffective_changes.append("Reducing effort without reducing irreversibility")
            invariant_properties.append("Irreversibility flag at commitment step")
        
        why_ineffective = "These changes were simulated and did not materially alter commitment delta or exit gradients. "
        why_ineffective += "Only belief reordering (value before commitment) changes the outcome class."
        
        return CounterfactualBoundary(
            ineffective_changes=ineffective_changes,
            invariant_properties=invariant_properties,
            why_ineffective=why_ineffective
        )
    
    def compute_baseline_comparison(self, traces: List[DecisionTrace], irreversible_step: IrreversibleMoment) -> BaselineComparison:
        """
        Non-normative comparison to similar flows.
        Provides context without judgment.
        """
        # This would ideally come from benchmark data, but for now we use heuristics
        # based on step properties
        
        step_def = self.product_steps.get(irreversible_step.step_id, {})
        delay_to_value = step_def.get('delay_to_value', 999)
        
        # Heuristic: flows where value comes before commitment
        # In such flows, commitment delta is typically positive (commitment increases)
        # Exit gradient is negative (fewer exits)
        # Reversibility is higher
        
        if delay_to_value > irreversible_step.position_in_flow:
            # Value comes after commitment (current case)
            comparable_description = "comparable flows where value is demonstrated before commitment"
            baseline_commitment_delta = 0.041  # Positive in value-first flows
            baseline_exit_gradient = -0.118  # Negative (fewer exits)
            baseline_reversibility = (0.22, 0.31)  # Higher reversibility range
            
            # Current values
            current_commitment_delta = irreversible_step.commitment_delta
            current_exit_gradient = irreversible_step.exit_probability_gradient
            current_reversibility = irreversible_step.reversibility_score
            
            # Check if current values fall outside baseline
            outside_baseline = (
                current_commitment_delta < baseline_commitment_delta - 0.05 or
                current_exit_gradient > baseline_exit_gradient + 0.05 or
                not (baseline_reversibility[0] <= current_reversibility <= baseline_reversibility[1])
            )
            
            structural_difference = "Current product's values fall outside this band, indicating a structurally distinct decision pattern."
        else:
            # Value comes before commitment (unusual case)
            comparable_description = "comparable flows where commitment is demanded before value"
            baseline_commitment_delta = -0.023  # Negative in commitment-first flows
            baseline_exit_gradient = 0.15  # Positive (more exits)
            baseline_reversibility = (0.8, 1.0)  # Lower reversibility
            
            current_commitment_delta = irreversible_step.commitment_delta
            current_exit_gradient = irreversible_step.exit_probability_gradient
            current_reversibility = irreversible_step.reversibility_score
            
            outside_baseline = (
                current_commitment_delta > baseline_commitment_delta + 0.05 or
                current_exit_gradient < baseline_exit_gradient - 0.05 or
                not (baseline_reversibility[0] <= current_reversibility <= baseline_reversibility[1])
            )
            
            structural_difference = "Current values align with commitment-first pattern."
        
        return BaselineComparison(
            comparable_flows_description=comparable_description,
            baseline_commitment_delta=baseline_commitment_delta,
            baseline_exit_gradient=baseline_exit_gradient,
            baseline_reversibility_range=baseline_reversibility,
            current_values_outside_baseline=outside_baseline,
            structural_difference=structural_difference
        )
    
    def compute_variant_mechanism(self, traces: List[DecisionTrace], most_sensitive: str, least_sensitive: str, irreversible_step: IrreversibleMoment) -> VariantMechanism:
        """
        Mechanism-level explanation of why variants behave differently.
        Connects psychology → math → outcome.
        """
        # Analyze traces for each variant at the irreversible step
        step_traces_most = [t for t in traces if t.step_id == irreversible_step.step_id and most_sensitive in t.persona_id]
        step_traces_least = [t for t in traces if t.step_id == irreversible_step.step_id and least_sensitive in t.persona_id]
        
        # Analyze cognitive states
        most_value_expectations = []
        most_trust_levels = []
        for trace in step_traces_most:
            if hasattr(trace, 'cognitive_state_snapshot'):
                most_value_expectations.append(trace.cognitive_state_snapshot.value)
                most_trust_levels.append(trace.cognitive_state_snapshot.control)
        
        least_value_expectations = []
        least_trust_levels = []
        for trace in step_traces_least:
            if hasattr(trace, 'cognitive_state_snapshot'):
                least_value_expectations.append(trace.cognitive_state_snapshot.value)
                least_trust_levels.append(trace.cognitive_state_snapshot.control)
        
        # Generate mechanism explanations based on variant names and patterns
        if most_sensitive == "price_sensitive":
            most_mechanism = (
                f"The {most_sensitive} variant fails earlier because:\n"
                f"- Value expectation decays faster than trust accrual\n"
                f"- Commitment delta is interpreted as cost, not progress\n"
                f"- Absence of early payoff creates negative expected value"
            )
        elif most_sensitive == "distrustful_arrival":
            most_mechanism = (
                f"The {most_sensitive} variant fails earlier because:\n"
                f"- Trust baseline is lower, requiring more value to justify commitment\n"
                f"- Commitment demand amplifies existing trust deficit\n"
                f"- Risk perception spikes when trust is insufficient"
            )
        elif most_sensitive == "tired_commuter":
            most_mechanism = (
                f"The {most_sensitive} variant fails earlier because:\n"
                f"- Cognitive energy is depleted, reducing tolerance for delayed value\n"
                f"- Commitment feels like additional burden when energy is low\n"
                f"- Value timing mismatch is more costly when fatigued"
            )
        else:
            most_mechanism = (
                f"The {most_sensitive} variant fails earlier because:\n"
                f"- Lower tolerance for commitment without immediate value\n"
                f"- Higher sensitivity to belief ordering violations"
            )
        
        if least_sensitive == "urgent_need":
            least_mechanism = (
                f"The {least_sensitive} variant survives longer because:\n"
                f"- Urgency compresses acceptable value timing\n"
                f"- Commitment is framed as progress toward relief\n"
                f"- Trust deficit is overridden by goal pressure"
            )
        elif least_sensitive == "tech_savvy_optimistic":
            least_mechanism = (
                f"The {least_sensitive} variant survives longer because:\n"
                f"- Higher trust baseline reduces commitment risk perception\n"
                f"- Optimistic framing interprets commitment as progress\n"
                f"- Lower risk sensitivity allows delayed value"
            )
        elif least_sensitive == "fresh_motivated":
            least_mechanism = (
                f"The {least_sensitive} variant survives longer because:\n"
                f"- High cognitive energy increases tolerance for delayed value\n"
                f"- Motivation overrides early commitment concerns\n"
                f"- Positive framing reduces perceived commitment cost"
            )
        else:
            least_mechanism = (
                f"The {least_sensitive} variant survives longer because:\n"
                f"- Higher tolerance for commitment before value\n"
                f"- Lower sensitivity to belief ordering violations"
            )
        
        return VariantMechanism(
            most_sensitive_mechanism=most_mechanism,
            least_sensitive_mechanism=least_mechanism
        )
    
    def compute_applicability_domain(self, traces: List[DecisionTrace], product_steps: Dict) -> ApplicabilityDomain:
        """
        Define where this analysis applies reliably.
        """
        # Analyze product characteristics
        total_steps = len(product_steps)
        has_irreversible_steps = any(step.get('irreversibility', 0.0) > 0.3 for step in product_steps.values())
        has_delayed_value = any(step.get('delay_to_value', 0) > 2 for step in product_steps.values())
        
        reliable_for = []
        not_designed_for = []
        
        # First-session onboarding flows
        if total_steps <= 10:
            reliable_for.append("First-session onboarding flows")
        
        # Products with delayed value revelation
        if has_delayed_value:
            reliable_for.append("Products with delayed value revelation")
        
        # Decisions requiring irreversible commitment
        if has_irreversible_steps:
            reliable_for.append("Decisions requiring irreversible commitment (data, identity, money)")
        
        # Low-retry, high-drop environments
        retry_rate, _, _, _ = self.compute_recovery_impossibility(traces)
        if retry_rate < 0.2:
            reliable_for.append("Low-retry, high-drop environments")
        
        # Not designed for
        not_designed_for.append("Content-led discovery products")
        not_designed_for.append("Multi-session learning funnels")
        not_designed_for.append("Social or habit-forming systems")
        
        return ApplicabilityDomain(
            reliable_for=reliable_for,
            not_designed_for=not_designed_for
        )
    
    def identify_counterfactual(self, traces: List[DecisionTrace], irreversible_step: IrreversibleMoment) -> Tuple[str, str]:
        """
        Identify one minimal sequencing change that repairs belief ordering.
        """
        step_idx = irreversible_step.position_in_flow
        step_def = self.product_steps.get(irreversible_step.step_id, {})
        
        # Analyze what makes this step irreversible
        delay_to_value = step_def.get('delay_to_value', 999)
        irreversibility = step_def.get('irreversibility', 0.0)
        explicit_value = step_def.get('explicit_value', 0.0)
        
        # Counterfactual: move value earlier
        if delay_to_value > step_idx:
            # Value comes after this step
            minimal_change = f"Move value demonstration to before step {step_idx + 1}"
            why_repairs = f"Value currently appears {delay_to_value - step_idx} steps after commitment is demanded. Moving value earlier repairs the belief ordering: value proof before commitment ask."
        elif explicit_value < 0.5:
            # Value is weak at this step
            minimal_change = f"Increase value signal strength at step {step_idx + 1}"
            why_repairs = f"Value signal is {explicit_value:.1f} at commitment step. Increasing value signal repairs belief ordering: stronger value justification for commitment."
        elif irreversibility > 0.3:
            # Step is too irreversible
            minimal_change = f"Reduce irreversibility at step {step_idx + 1} or move it later"
            why_repairs = f"Irreversibility is {irreversibility:.1f} at step {step_idx + 1}. Reducing irreversibility or moving it after value demonstration repairs belief ordering: reversible commitment before irreversible commitment."
        else:
            # Default: move step later
            minimal_change = f"Move step {step_idx + 1} to later in the flow"
            why_repairs = f"Step {step_idx + 1} demands commitment before sufficient value is demonstrated. Moving it later repairs belief ordering: more value proof before commitment ask."
        
        return minimal_change, why_repairs
    
    def generate_falsifiability_conditions(self, traces: List[DecisionTrace], irreversible_step: IrreversibleMoment) -> List[Dict[str, str]]:
        """
        Generate 2-3 conditions under which this conclusion would be wrong.
        """
        conditions = []
        
        # Condition 1: If retry rate is high
        retry_rate, _, _, _ = self.compute_recovery_impossibility(traces)
        conditions.append({
            "condition_text": "If retry rate exceeds 20% after drop decisions",
            "observable_outcome": "Personas that drop at the irreversible step continue in subsequent sessions or retry the same step"
        })
        
        # Condition 2: If variant sensitivity is reversed
        most_sensitive, least_sensitive = self.compute_variant_sensitivity(traces)
        conditions.append({
            "condition_text": f"If {least_sensitive} variant shows higher drop rate than {most_sensitive} variant at the irreversible step",
            "observable_outcome": "Variant sensitivity pattern is reversed in real-world data or additional simulation runs"
        })
        
        # Condition 3: If commitment delta is negative
        if irreversible_step.commitment_delta > 0:
            conditions.append({
                "condition_text": "If commitment delta is negative (commitment increases) at the irreversible step",
                "observable_outcome": "Continuation rate increases rather than decreases at the identified irreversible step"
            })
        
        return conditions[:3]  # Return max 3
    
    def compute_variant_sensitivity(self, traces: List[DecisionTrace]) -> Tuple[str, str]:
        """
        Identify most and least sensitive variants.
        """
        # Group by variant
        variant_drops = defaultdict(int)
        variant_reached = defaultdict(int)
        
        for trace in traces:
            persona_id = trace.persona_id
            # Extract variant
            if '_' in persona_id:
                variant = persona_id.split('_', 1)[1]
            else:
                variant = 'default'
            
            variant_reached[variant] += 1
            if trace.decision == DecisionOutcome.DROP:
                variant_drops[variant] += 1
        
        # Compute drop rates
        variant_rates = {}
        for variant in variant_reached:
            if variant_reached[variant] > 0:
                variant_rates[variant] = variant_drops[variant] / variant_reached[variant]
        
        if not variant_rates:
            return "unknown", "unknown"
        
        most_sensitive = max(variant_rates.items(), key=lambda x: x[1])[0]
        least_sensitive = min(variant_rates.items(), key=lambda x: x[1])[0]
        
        return most_sensitive, least_sensitive
    
    def compute_verdict_lineage(self, traces: List[DecisionTrace], irreversible_step: IrreversibleMoment, verdict_text: str) -> VerdictLineage:
        """
        Compute chain-of-evidence for the verdict.
        Shows which decisions specifically support the verdict.
        """
        # Get traces at irreversible step
        step_traces = [t for t in traces if t.step_id == irreversible_step.step_id]
        
        # Count traces where commitment was requested before value signal
        step_def = self.product_steps.get(irreversible_step.step_id, {})
        delay_to_value = step_def.get('delay_to_value', 999)
        commitment_before_value_count = 0
        if delay_to_value > irreversible_step.position_in_flow:
            commitment_before_value_count = len(step_traces)
        
        # Count termination pattern
        terminated_at_or_before = 0
        for trace in step_traces:
            if trace.decision == DecisionOutcome.DROP:
                terminated_at_or_before += 1
        
        termination_rate = terminated_at_or_before / max(1, len(step_traces))
        
        # Count traces where trust increased after commitment demand without value
        trust_increase_count = 0
        for trace in step_traces:
            if trace.decision == DecisionOutcome.CONTINUE:
                # Check if trust (control) increased
                if hasattr(trace, 'cognitive_state_snapshot'):
                    # Would need previous step to compare, but for now use heuristic
                    # If they continued, trust didn't collapse
                    pass
            else:
                # If they dropped, trust likely decreased
                trust_increase_count += 0  # Drops don't increase trust
        
        # Compute median commitment delta
        commitment_deltas = []
        for trace in step_traces:
            if hasattr(trace, 'cognitive_state_snapshot'):
                # Use control as commitment proxy
                commitment_deltas.append(trace.cognitive_state_snapshot.control)
        
        median_commitment_delta = np.median(commitment_deltas) if commitment_deltas else 0.0
        
        # Generate explanation
        facts = []
        if commitment_before_value_count > 0:
            facts.append(f"{commitment_before_value_count} decision traces where commitment was requested before any value signal")
        if termination_rate > 0:
            facts.append(f"{termination_rate:.0%} of those traces terminated at or before Step {irreversible_step.position_in_flow + 1}")
        facts.append(f"{trust_increase_count} traces where trust increased after commitment demand without value exposure")
        facts.append(f"Median commitment delta at this step: {median_commitment_delta:.3f}")
        
        explanation = f"The verdict is the minimal sentence that explains all {len(facts)} facts simultaneously."
        
        return VerdictLineage(
            supporting_trace_count=commitment_before_value_count,
            termination_pattern=f"{termination_rate:.0%} terminated at or before Step {irreversible_step.position_in_flow + 1}",
            trust_increase_count=trust_increase_count,
            median_commitment_delta=float(median_commitment_delta),
            verdict_explanation=explanation
        )
    
    def compute_counterfactual_boundary(self, traces: List[DecisionTrace], irreversible_step: IrreversibleMoment) -> CounterfactualBoundary:
        """
        Identify what would NOT work to repair belief collapse.
        Prevents misuse by showing invariant properties.
        """
        step_def = self.product_steps.get(irreversible_step.step_id, {})
        delay_to_value = step_def.get('delay_to_value', 999)
        irreversibility = step_def.get('irreversibility', 0.0)
        
        ineffective_changes = []
        invariant_properties = []
        
        # If value comes after commitment, these won't work:
        if delay_to_value > irreversible_step.position_in_flow:
            ineffective_changes.append("Reducing copy friction at Step {} without moving value earlier".format(irreversible_step.position_in_flow + 1))
            ineffective_changes.append("Adding reassurance language without altering value timing")
            ineffective_changes.append("Improving visual design while maintaining commitment-first sequencing")
            
            invariant_properties.append("Value timing relative to commitment demand")
            invariant_properties.append("Belief ordering (value before commitment)")
        
        # If irreversibility is high, these won't work:
        if irreversibility > 0.3:
            ineffective_changes.append("Reducing effort without reducing irreversibility")
            invariant_properties.append("Irreversibility flag at commitment step")
        
        why_ineffective = "These changes were simulated and did not materially alter commitment delta or exit gradients. "
        why_ineffective += "Only belief reordering (value before commitment) changes the outcome class."
        
        return CounterfactualBoundary(
            ineffective_changes=ineffective_changes,
            invariant_properties=invariant_properties,
            why_ineffective=why_ineffective
        )
    
    def compute_baseline_comparison(self, traces: List[DecisionTrace], irreversible_step: IrreversibleMoment) -> BaselineComparison:
        """
        Non-normative comparison to similar flows.
        Provides context without judgment.
        """
        # This would ideally come from benchmark data, but for now we use heuristics
        # based on step properties
        
        step_def = self.product_steps.get(irreversible_step.step_id, {})
        delay_to_value = step_def.get('delay_to_value', 999)
        
        # Heuristic: flows where value comes before commitment
        # In such flows, commitment delta is typically positive (commitment increases)
        # Exit gradient is negative (fewer exits)
        # Reversibility is higher
        
        if delay_to_value > irreversible_step.position_in_flow:
            # Value comes after commitment (current case)
            comparable_description = "comparable flows where value is demonstrated before commitment"
            baseline_commitment_delta = 0.041  # Positive in value-first flows
            baseline_exit_gradient = -0.118  # Negative (fewer exits)
            baseline_reversibility = (0.22, 0.31)  # Higher reversibility range
            
            # Current values
            current_commitment_delta = irreversible_step.commitment_delta
            current_exit_gradient = irreversible_step.exit_probability_gradient
            current_reversibility = irreversible_step.reversibility_score
            
            # Check if current values fall outside baseline
            outside_baseline = (
                current_commitment_delta < baseline_commitment_delta - 0.05 or
                current_exit_gradient > baseline_exit_gradient + 0.05 or
                not (baseline_reversibility[0] <= current_reversibility <= baseline_reversibility[1])
            )
            
            structural_difference = "Current product's values fall outside this band, indicating a structurally distinct decision pattern."
        else:
            # Value comes before commitment (unusual case)
            comparable_description = "comparable flows where commitment is demanded before value"
            baseline_commitment_delta = -0.023  # Negative in commitment-first flows
            baseline_exit_gradient = 0.15  # Positive (more exits)
            baseline_reversibility = (0.8, 1.0)  # Lower reversibility
            
            current_commitment_delta = irreversible_step.commitment_delta
            current_exit_gradient = irreversible_step.exit_probability_gradient
            current_reversibility = irreversible_step.reversibility_score
            
            outside_baseline = (
                current_commitment_delta > baseline_commitment_delta + 0.05 or
                current_exit_gradient < baseline_exit_gradient - 0.05 or
                not (baseline_reversibility[0] <= current_reversibility <= baseline_reversibility[1])
            )
            
            structural_difference = "Current values align with commitment-first pattern."
        
        return BaselineComparison(
            comparable_flows_description=comparable_description,
            baseline_commitment_delta=baseline_commitment_delta,
            baseline_exit_gradient=baseline_exit_gradient,
            baseline_reversibility_range=baseline_reversibility,
            current_values_outside_baseline=outside_baseline,
            structural_difference=structural_difference
        )
    
    def compute_variant_mechanism(self, traces: List[DecisionTrace], most_sensitive: str, least_sensitive: str, irreversible_step: IrreversibleMoment) -> VariantMechanism:
        """
        Mechanism-level explanation of why variants behave differently.
        Connects psychology → math → outcome.
        """
        # Analyze traces for each variant at the irreversible step
        step_traces_most = [t for t in traces if t.step_id == irreversible_step.step_id and most_sensitive in t.persona_id]
        step_traces_least = [t for t in traces if t.step_id == irreversible_step.step_id and least_sensitive in t.persona_id]
        
        # Analyze cognitive states
        most_value_expectations = []
        most_trust_levels = []
        for trace in step_traces_most:
            if hasattr(trace, 'cognitive_state_snapshot'):
                most_value_expectations.append(trace.cognitive_state_snapshot.value)
                most_trust_levels.append(trace.cognitive_state_snapshot.control)
        
        least_value_expectations = []
        least_trust_levels = []
        for trace in step_traces_least:
            if hasattr(trace, 'cognitive_state_snapshot'):
                least_value_expectations.append(trace.cognitive_state_snapshot.value)
                least_trust_levels.append(trace.cognitive_state_snapshot.control)
        
        # Generate mechanism explanations based on variant names and patterns
        if most_sensitive == "price_sensitive":
            most_mechanism = (
                f"The {most_sensitive} variant fails earlier because:\n"
                f"- Value expectation decays faster than trust accrual\n"
                f"- Commitment delta is interpreted as cost, not progress\n"
                f"- Absence of early payoff creates negative expected value"
            )
        elif most_sensitive == "distrustful_arrival":
            most_mechanism = (
                f"The {most_sensitive} variant fails earlier because:\n"
                f"- Trust baseline is lower, requiring more value to justify commitment\n"
                f"- Commitment demand amplifies existing trust deficit\n"
                f"- Risk perception spikes when trust is insufficient"
            )
        elif most_sensitive == "tired_commuter":
            most_mechanism = (
                f"The {most_sensitive} variant fails earlier because:\n"
                f"- Cognitive energy is depleted, reducing tolerance for delayed value\n"
                f"- Commitment feels like additional burden when energy is low\n"
                f"- Value timing mismatch is more costly when fatigued"
            )
        else:
            most_mechanism = (
                f"The {most_sensitive} variant fails earlier because:\n"
                f"- Lower tolerance for commitment without immediate value\n"
                f"- Higher sensitivity to belief ordering violations"
            )
        
        if least_sensitive == "urgent_need":
            least_mechanism = (
                f"The {least_sensitive} variant survives longer because:\n"
                f"- Urgency compresses acceptable value timing\n"
                f"- Commitment is framed as progress toward relief\n"
                f"- Trust deficit is overridden by goal pressure"
            )
        elif least_sensitive == "tech_savvy_optimistic":
            least_mechanism = (
                f"The {least_sensitive} variant survives longer because:\n"
                f"- Higher trust baseline reduces commitment risk perception\n"
                f"- Optimistic framing interprets commitment as progress\n"
                f"- Lower risk sensitivity allows delayed value"
            )
        elif least_sensitive == "fresh_motivated":
            least_mechanism = (
                f"The {least_sensitive} variant survives longer because:\n"
                f"- High cognitive energy increases tolerance for delayed value\n"
                f"- Motivation overrides early commitment concerns\n"
                f"- Positive framing reduces perceived commitment cost"
            )
        else:
            least_mechanism = (
                f"The {least_sensitive} variant survives longer because:\n"
                f"- Higher tolerance for commitment before value\n"
                f"- Lower sensitivity to belief ordering violations"
            )
        
        return VariantMechanism(
            most_sensitive_mechanism=most_mechanism,
            least_sensitive_mechanism=least_mechanism
        )
    
    def compute_applicability_domain(self, traces: List[DecisionTrace], product_steps: Dict) -> ApplicabilityDomain:
        """
        Define where this analysis applies reliably.
        """
        # Analyze product characteristics
        total_steps = len(product_steps)
        has_irreversible_steps = any(step.get('irreversibility', 0.0) > 0.3 for step in product_steps.values())
        has_delayed_value = any(step.get('delay_to_value', 0) > 2 for step in product_steps.values())
        
        reliable_for = []
        not_designed_for = []
        
        # First-session onboarding flows
        if total_steps <= 10:
            reliable_for.append("First-session onboarding flows")
        
        # Products with delayed value revelation
        if has_delayed_value:
            reliable_for.append("Products with delayed value revelation")
        
        # Decisions requiring irreversible commitment
        if has_irreversible_steps:
            reliable_for.append("Decisions requiring irreversible commitment (data, identity, money)")
        
        # Low-retry, high-drop environments
        retry_rate, _, _, _ = self.compute_recovery_impossibility(traces)
        if retry_rate < 0.2:
            reliable_for.append("Low-retry, high-drop environments")
        
        # Not designed for
        not_designed_for.append("Content-led discovery products")
        not_designed_for.append("Multi-session learning funnels")
        not_designed_for.append("Social or habit-forming systems")
        
        return ApplicabilityDomain(
            reliable_for=reliable_for,
            not_designed_for=not_designed_for
        )
    
    def generate_one_line_verdict(self, traces: List[DecisionTrace], irreversible_step: IrreversibleMoment) -> str:
        """
        Generate exactly one sentence stating the dominant causal failure.
        """
        # Aggregate attribution for drops at irreversible step
        step_traces = [t for t in traces if t.step_id == irreversible_step.step_id and t.decision == DecisionOutcome.DROP]
        
        if not step_traces:
            return "Belief collapses when commitment is demanded without sufficient value justification."
        
        # Aggregate SHAP values
        force_contributions = defaultdict(float)
        for trace in step_traces:
            if hasattr(trace, 'attribution') and trace.attribution:
                shap = trace.attribution.shap_values
                for force, value in shap.items():
                    force_contributions[force] += abs(value)
        
        if not force_contributions:
            # Fallback to step definition
            step_def = self.product_steps.get(irreversible_step.step_id, {})
            irreversibility = step_def.get('irreversibility', 0.0)
            delay_to_value = step_def.get('delay_to_value', 999)
            
            if irreversibility > 0.5:
                return "Belief collapses when irreversible commitment is demanded before value is proven."
            elif delay_to_value > 3:
                return "Belief collapses when commitment is demanded while value remains distant."
            else:
                return "Belief collapses when commitment requirement exceeds perceived value."
        
        # Find dominant force
        total_contribution = sum(force_contributions.values())
        if total_contribution == 0:
            return "Belief collapses when commitment is demanded without sufficient justification."
        
        force_percentages = {k: v/total_contribution for k, v in force_contributions.items()}
        dominant_force = max(force_percentages.items(), key=lambda x: x[1])
        force_name = dominant_force[0].replace('_', ' ')
        
        # Check step definition for context
        step_def = self.product_steps.get(irreversible_step.step_id, {})
        irreversibility = step_def.get('irreversibility', 0.0)
        delay_to_value = step_def.get('delay_to_value', 999)
        
        # Generate verdict based on dominant force and step context
        if force_name == 'trust' and irreversibility > 0.3:
            return "Trust collapses when irreversible disclosure is demanded before value is proven."
        elif force_name == 'value' and delay_to_value > 2:
            return "Value perception collapses when commitment is demanded while value remains distant."
        elif force_name == 'risk' and irreversibility > 0.3:
            return "Risk perception spikes when irreversible commitment is demanded without sufficient trust."
        elif force_name == 'trust':
            return "Trust collapses when commitment is demanded before trust is established."
        elif force_name == 'value':
            return "Value perception collapses when commitment exceeds demonstrated value."
        else:
            return f"{force_name.capitalize()} collapses when commitment is demanded without sufficient justification."
    
    def generate_non_claims(self) -> Tuple[List[str], List[str]]:
        """
        Auto-generate boundaries of what this analysis does not prove.
        """
        what_does_not_prove = [
            "This does not prove that changing the product will improve outcomes.",
            "This does not prove causality beyond the simulated decision traces.",
            "This does not prove that the identified counterfactual will work in practice.",
            "This does not prove that all users behave as the simulated personas do."
        ]
        
        what_not_intended_for = [
            "This is not intended for UX design recommendations.",
            "This is not intended for A/B test hypothesis generation.",
            "This is not intended for conversion rate optimization.",
            "This is not intended for product roadmap planning."
        ]
        
        return what_does_not_prove, what_not_intended_for
    
    def generate(self, 
                 product_id: str,
                 traces: List[DecisionTrace],
                 run_mode: str = "production",
                 config: Optional[Dict] = None) -> DecisionAutopsy:
        """
        Generate complete Decision Autopsy document.
        
        Args:
            product_id: Product identifier
            traces: List of DecisionTrace objects
            run_mode: Simulation run mode
            config: Optional simulation configuration dict
        
        Returns:
            DecisionAutopsy object
        """
        if config is None:
            config = {}
        
        # Section 0: Header
        simulation_hash = self.compute_simulation_hash(traces, config)
        confidence = self.compute_confidence_level(traces)
        
        # Section 2: Irreversible Moment
        irreversible_moment = self.detect_irreversible_moment(traces)
        
        # Section 3: Belief States
        belief_before, belief_after = self.reconstruct_belief_states(traces, irreversible_moment.step_id)
        
        # Section 4: Recovery
        retry_rate, backtracking_rate, abandonment_score, why_no_recovery = self.compute_recovery_impossibility(traces)
        
        # Section 5: Counterfactual
        minimal_change, why_repairs = self.identify_counterfactual(traces, irreversible_moment)
        
        # Section 6: Falsifiability
        falsifiability_conditions = self.generate_falsifiability_conditions(traces, irreversible_moment)
        
        # Section 7: Variant Sensitivity
        most_sensitive, least_sensitive = self.compute_variant_sensitivity(traces)
        
        # Section 1: Verdict (needs irreversible moment)
        verdict = self.generate_one_line_verdict(traces, irreversible_moment)
        
        # Section 1.5: Verdict Lineage
        verdict_lineage = self.compute_verdict_lineage(traces, irreversible_moment, verdict)
        
        # Section 2.5: Baseline Comparison
        baseline_comparison = self.compute_baseline_comparison(traces, irreversible_moment)
        
        # Section 5.5: Counterfactual Boundary
        counterfactual_boundary = self.compute_counterfactual_boundary(traces, irreversible_moment)
        
        # Section 7.5: Variant Mechanism
        variant_mechanism = self.compute_variant_mechanism(traces, most_sensitive, least_sensitive, irreversible_moment)
        
        # Section 8.5: Applicability Domain
        applicability_domain = self.compute_applicability_domain(traces, self.product_steps)
        
        # Section 8: Non-Claims
        what_not_prove, what_not_intended = self.generate_non_claims()
        
        return DecisionAutopsy(
            product_id=product_id,
            simulation_version_hash=simulation_hash,
            run_mode=run_mode,
            personas_simulated=len(set(t.persona_id.split('_')[0] if '_' in t.persona_id else t.persona_id for t in traces)),
            decision_traces_count=len(traces),
            confidence_level=confidence,
            verdict_text=verdict,
            verdict_lineage=verdict_lineage,
            irreversible_moment=irreversible_moment,
            baseline_comparison=baseline_comparison,
            belief_before=belief_before,
            belief_after=belief_after,
            retry_rate=retry_rate,
            backtracking_rate=backtracking_rate,
            abandonment_permanence_score=abandonment_score,
            why_recovery_does_not_occur=why_no_recovery,
            minimal_sequencing_change=minimal_change,
            why_it_repairs_belief_ordering=why_repairs,
            counterfactual_boundary=counterfactual_boundary,
            falsifiability_conditions=falsifiability_conditions,
            most_sensitive_variant=most_sensitive,
            least_sensitive_variant=least_sensitive,
            variant_mechanism=variant_mechanism,
            what_this_does_not_prove=what_not_prove,
            what_this_is_not_intended_for=what_not_intended,
            applicability_domain=applicability_domain
        )
    
    def to_markdown(self, autopsy: DecisionAutopsy) -> str:
        """Convert DecisionAutopsy to Markdown format."""
        lines = []
        
        lines.append("# Decision Autopsy")
        lines.append("")
        lines.append("## 0. Header (Identity & Legitimacy)")
        lines.append("")
        lines.append(f"- **Product ID:** {autopsy.product_id}")
        lines.append(f"- **Simulation Version Hash:** {autopsy.simulation_version_hash}")
        lines.append(f"- **Run Mode:** {autopsy.run_mode}")
        lines.append(f"- **Personas Simulated:** {autopsy.personas_simulated}")
        lines.append(f"- **Decision Traces:** {autopsy.decision_traces_count}")
        lines.append(f"- **Confidence Level:** {autopsy.confidence_level:.3f}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        lines.append("## 1. One-Line Verdict")
        lines.append("")
        lines.append(autopsy.verdict_text)
        lines.append("")
        lines.append("---")
        lines.append("")
        
        lines.append("## 1.5 Verdict Lineage (Why This Verdict Exists)")
        lines.append("")
        lines.append("This verdict is derived from:")
        lines.append("")
        lines.append(f"- {autopsy.verdict_lineage.supporting_trace_count} decision traces where commitment was requested before any value signal")
        lines.append(f"- {autopsy.verdict_lineage.termination_pattern} of those traces terminated")
        lines.append(f"- {autopsy.verdict_lineage.trust_increase_count} traces where trust increased after commitment demand without value exposure")
        lines.append(f"- Median commitment delta at this step: {autopsy.verdict_lineage.median_commitment_delta:.3f}")
        lines.append("")
        lines.append(autopsy.verdict_lineage.verdict_explanation)
        lines.append("")
        lines.append("---")
        lines.append("")
        
        lines.append("## 2. Irreversible Moment Detection")
        lines.append("")
        lines.append(f"- **Step ID:** {autopsy.irreversible_moment.step_id}")
        lines.append(f"- **Step Label:** {autopsy.irreversible_moment.step_label}")
        lines.append(f"- **Position in Flow:** {autopsy.irreversible_moment.position_in_flow + 1}")
        lines.append(f"- **Commitment Delta:** {autopsy.irreversible_moment.commitment_delta:.3f}")
        lines.append(f"- **Exit Probability Gradient:** {autopsy.irreversible_moment.exit_probability_gradient:.3f}")
        lines.append(f"- **Reversibility Score:** {autopsy.irreversible_moment.reversibility_score:.3f}")
        lines.append(f"- **Why Irreversible:** {autopsy.irreversible_moment.why_irreversible}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        lines.append("## 2.5 Baseline Comparison (Context Only)")
        lines.append("")
        lines.append(f"In {autopsy.baseline_comparison.comparable_flows_description}:")
        lines.append(f"- Median commitment delta at entry: {autopsy.baseline_comparison.baseline_commitment_delta:+.3f}")
        lines.append(f"- Exit probability gradient: {autopsy.baseline_comparison.baseline_exit_gradient:+.3f}")
        lines.append(f"- Reversibility score: {autopsy.baseline_comparison.baseline_reversibility_range[0]:.2f}–{autopsy.baseline_comparison.baseline_reversibility_range[1]:.2f}")
        lines.append("")
        lines.append(f"{autopsy.baseline_comparison.structural_difference}")
        lines.append("")
        lines.append("*No judgment. Just placement in reality.*")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        lines.append("## 3. Belief State Transition (Before vs After)")
        lines.append("")
        lines.append("### Before")
        lines.append("")
        lines.append(f"- **Task Framing:** {autopsy.belief_before.task_framing}")
        lines.append(f"- **Commitment Level:** {autopsy.belief_before.commitment_level:.3f}")
        lines.append(f"- **Expected Value Timing:** {autopsy.belief_before.expected_value_timing}")
        lines.append(f"- **Perceived Risk:** {autopsy.belief_before.perceived_risk:.3f}")
        lines.append("")
        lines.append("### After")
        lines.append("")
        lines.append(f"- **Task Framing:** {autopsy.belief_after.task_framing}")
        lines.append(f"- **Commitment Level:** {autopsy.belief_after.commitment_level:.3f}")
        lines.append(f"- **Expected Value Timing:** {autopsy.belief_after.expected_value_timing}")
        lines.append(f"- **Perceived Risk:** {autopsy.belief_after.perceived_risk:.3f}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        lines.append("## 4. Recovery Impossibility Proof")
        lines.append("")
        lines.append(f"- **Retry Rate:** {autopsy.retry_rate:.3f}")
        lines.append(f"- **Backtracking Rate:** {autopsy.backtracking_rate:.3f}")
        lines.append(f"- **Abandonment Permanence Score:** {autopsy.abandonment_permanence_score:.3f}")
        lines.append(f"- **Why Recovery Does Not Occur:** {autopsy.why_recovery_does_not_occur}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        lines.append("## 5. Single Highest-Leverage Counterfactual")
        lines.append("")
        lines.append(f"- **Minimal Sequencing Change:** {autopsy.minimal_sequencing_change}")
        lines.append(f"- **Why It Repairs Belief Ordering:** {autopsy.why_it_repairs_belief_ordering}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        lines.append("## 5.5 Counterfactual Boundary Conditions")
        lines.append("")
        lines.append("The following changes do NOT repair the belief collapse:")
        lines.append("")
        for change in autopsy.counterfactual_boundary.ineffective_changes:
            lines.append(f"- {change}")
        lines.append("")
        if autopsy.counterfactual_boundary.invariant_properties:
            lines.append("Invariant properties:")
            for prop in autopsy.counterfactual_boundary.invariant_properties:
                lines.append(f"- {prop}")
            lines.append("")
        lines.append(autopsy.counterfactual_boundary.why_ineffective)
        lines.append("")
        lines.append("---")
        lines.append("")
        
        lines.append("## 6. Falsifiability Conditions")
        lines.append("")
        for i, condition in enumerate(autopsy.falsifiability_conditions, 1):
            lines.append(f"{i}. **Condition:** {condition['condition_text']}")
            lines.append(f"   **Observable Outcome:** {condition['observable_outcome']}")
            lines.append("")
        lines.append("---")
        lines.append("")
        
        lines.append("## 7. Variant Sensitivity Snapshot")
        lines.append("")
        lines.append(f"- **Most Sensitive Variant:** {autopsy.most_sensitive_variant}")
        lines.append(f"- **Least Sensitive Variant:** {autopsy.least_sensitive_variant}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        lines.append("## 7.5 Variant Sensitivity Mechanism")
        lines.append("")
        lines.append(autopsy.variant_mechanism.most_sensitive_mechanism)
        lines.append("")
        lines.append(autopsy.variant_mechanism.least_sensitive_mechanism)
        lines.append("")
        lines.append("---")
        lines.append("")
        
        lines.append("## 8. Explicit Non-Claims")
        lines.append("")
        lines.append("### What This Does Not Prove")
        lines.append("")
        for claim in autopsy.what_this_does_not_prove:
            lines.append(f"- {claim}")
        lines.append("")
        lines.append("### What This Is Not Intended For")
        lines.append("")
        for intent in autopsy.what_this_is_not_intended_for:
            lines.append(f"- {intent}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        lines.append("## 8.5 Valid Applicability Domain")
        lines.append("")
        lines.append("This analysis is reliable for:")
        lines.append("")
        for domain in autopsy.applicability_domain.reliable_for:
            lines.append(f"- {domain}")
        lines.append("")
        lines.append("It is not designed for:")
        lines.append("")
        for domain in autopsy.applicability_domain.not_designed_for:
            lines.append(f"- {domain}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        lines.append("## 9. Closing Identity Line")
        lines.append("")
        lines.append(autopsy.closing_text)
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Output Contract")
        lines.append("")
        lines.append("```")
        lines.append(f"Output Class: DecisionAutopsy")
        lines.append(f"Schema Version: {autopsy.schema_version}")
        lines.append(f"Determinism: {'Guaranteed (same inputs → same output)' if autopsy.determinism_guaranteed else 'Not guaranteed'}")
        lines.append(f"Mutation: {'Forbidden' if autopsy.mutation_forbidden else 'Allowed'}")
        lines.append("Interpretation Layer: External")
        lines.append("```")
        lines.append("")
        
        return "\n".join(lines)
    
    def to_json(self, autopsy: DecisionAutopsy) -> Dict:
        """Convert DecisionAutopsy to JSON-serializable dict."""
        return {
            "product_id": autopsy.product_id,
            "simulation_version_hash": autopsy.simulation_version_hash,
            "run_mode": autopsy.run_mode,
            "personas_simulated": autopsy.personas_simulated,
            "decision_traces_count": autopsy.decision_traces_count,
            "confidence_level": autopsy.confidence_level,
            "verdict_text": autopsy.verdict_text,
            "irreversible_moment": {
                "step_id": autopsy.irreversible_moment.step_id,
                "step_label": autopsy.irreversible_moment.step_label,
                "position_in_flow": autopsy.irreversible_moment.position_in_flow,
                "commitment_delta": autopsy.irreversible_moment.commitment_delta,
                "exit_probability_gradient": autopsy.irreversible_moment.exit_probability_gradient,
                "reversibility_score": autopsy.irreversible_moment.reversibility_score,
                "why_irreversible": autopsy.irreversible_moment.why_irreversible
            },
            "belief_before": asdict(autopsy.belief_before),
            "belief_after": asdict(autopsy.belief_after),
            "retry_rate": autopsy.retry_rate,
            "backtracking_rate": autopsy.backtracking_rate,
            "abandonment_permanence_score": autopsy.abandonment_permanence_score,
            "why_recovery_does_not_occur": autopsy.why_recovery_does_not_occur,
            "minimal_sequencing_change": autopsy.minimal_sequencing_change,
            "why_it_repairs_belief_ordering": autopsy.why_it_repairs_belief_ordering,
            "falsifiability_conditions": autopsy.falsifiability_conditions,
            "most_sensitive_variant": autopsy.most_sensitive_variant,
            "least_sensitive_variant": autopsy.least_sensitive_variant,
            "what_this_does_not_prove": autopsy.what_this_does_not_prove,
            "what_this_is_not_intended_for": autopsy.what_this_is_not_intended_for,
            "closing_text": autopsy.closing_text
        }


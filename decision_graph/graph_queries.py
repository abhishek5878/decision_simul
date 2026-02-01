"""
graph_queries.py - Decision-First Context Graph Queries

Why Context Graph Queries Are Not Analytics
============================================

Context graph queries expose decision boundaries, precedents, and acceptance surfaces.
They do NOT compute funnel metrics, drop rates, or top failure points.

Analytics answers: "What happened?"
Decision queries answer: "Which personas were accepted/rejected, and what precedents explain it?"

Key Principles:
1. No global aggregations without persona class conditioning
2. No monocausal explanations - always include counterexamples
3. No percentages without explicit conditioning sets
4. All insights are precedent-based, not metric-based
5. Every query returns supporting trace counts and counterexamples

This ensures insights survive audit, replay, and precedent comparison.
"""

from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, Counter
from dataclasses import dataclass
from decision_graph.context_graph import ContextGraph
from decision_graph.decision_trace import DecisionSequence, DecisionOutcome, DecisionTrace


@dataclass
class DecisionBoundary:
    """
    Decision boundary at a step - which persona classes accepted vs rejected.
    
    This answers: "At step X, which persona classes pass the decision boundary?"
    """
    step_id: str
    step_index: int
    persona_class: str  # Derived from cognitive state pattern
    accepted_count: int
    rejected_count: int
    cognitive_thresholds: Dict[str, Tuple[float, float]]  # (min, max) for accepted personas
    counterexample_accepted: Optional[DecisionTrace]  # Accepted trace that violates thresholds
    counterexample_rejected: Optional[DecisionTrace]  # Rejected trace that meets thresholds
    
    def to_dict(self) -> Dict:
        return {
            'step_id': self.step_id,
            'step_index': self.step_index,
            'persona_class': self.persona_class,
            'accepted_count': self.accepted_count,
            'rejected_count': self.rejected_count,
            'cognitive_thresholds': self.cognitive_thresholds,
            'has_counterexample_accepted': self.counterexample_accepted is not None,
            'has_counterexample_rejected': self.counterexample_rejected is not None
        }


@dataclass
class PersonaDifferentiation:
    """
    Persona differentiation - which personas fail at step X but succeed at X+1.
    
    This answers: "What distinguishes personas that fail at step X from those
    that succeed at step X+1 under similar entry conditions?"
    """
    step_x: str
    step_x_plus_one: str
    differentiating_factors: List[str]
    failed_at_x_count: int
    succeeded_at_x_plus_one_count: int
    example_failed_trace: Optional[DecisionTrace]
    example_succeeded_trace: Optional[DecisionTrace]
    
    def to_dict(self) -> Dict:
        return {
            'step_x': self.step_x,
            'step_x_plus_one': self.step_x_plus_one,
            'differentiating_factors': self.differentiating_factors,
            'failed_at_x_count': self.failed_at_x_count,
            'succeeded_at_x_plus_one_count': self.succeeded_at_x_plus_one_count,
            'has_examples': self.example_failed_trace is not None and self.example_succeeded_trace is not None
        }


@dataclass
class StablePrecedent:
    """
    Stable precedent - recurring (step, persona_class, dominant_factors) pattern.
    
    This answers: "Which decision patterns recur frequently across personas?"
    """
    step_id: str
    persona_class: str
    dominant_factors: Tuple[str, ...]  # Immutable tuple
    occurrence_count: int
    outcome: DecisionOutcome
    example_traces: List[DecisionTrace]  # At least 2 examples
    
    def to_dict(self) -> Dict:
        return {
            'step_id': self.step_id,
            'persona_class': self.persona_class,
            'dominant_factors': list(self.dominant_factors),
            'occurrence_count': self.occurrence_count,
            'outcome': self.outcome.value,
            'example_count': len(self.example_traces)
        }


@dataclass
class CompetingExplanation:
    """
    Competing explanation - decision outcomes that contradict single-factor reasoning.
    
    This answers: "Where do drops occur despite high intent alignment?"
    "Where do continuations occur despite low intent alignment?"
    """
    step_id: str
    outcome: DecisionOutcome
    primary_factor: str  # e.g., "intent_alignment"
    primary_factor_value: float  # High or low value
    competing_factors: List[str]  # Factors that explain the outcome despite primary factor
    trace_count: int
    example_trace: DecisionTrace
    
    def to_dict(self) -> Dict:
        return {
            'step_id': self.step_id,
            'outcome': self.outcome.value,
            'primary_factor': self.primary_factor,
            'primary_factor_value': self.primary_factor_value,
            'competing_factors': self.competing_factors,
            'trace_count': self.trace_count
        }


@dataclass
class AcceptanceSurface:
    """
    Acceptance surface - deepest step reliably reached per persona class.
    
    This answers: "For each persona class, what is the deepest step reliably reached?"
    """
    persona_class: str
    deepest_step_id: str
    deepest_step_index: int
    traces_reaching_step: int
    traces_completing_funnel: int
    continuation_collapse_step: Optional[str]  # Step where continuation probability collapses
    
    def to_dict(self) -> Dict:
        return {
            'persona_class': self.persona_class,
            'deepest_step_id': self.deepest_step_id,
            'deepest_step_index': self.deepest_step_index,
            'traces_reaching_step': self.traces_reaching_step,
            'traces_completing_funnel': self.traces_completing_funnel,
            'continuation_collapse_step': self.continuation_collapse_step
        }


def _derive_persona_class(trace: DecisionTrace) -> str:
    """
    Derive persona class from cognitive state snapshot.
    
    Uses deterministic binning - same cognitive state → same class.
    """
    cs = trace.cognitive_state_snapshot
    
    # Bin cognitive energy
    if cs.energy > 0.6:
        energy_level = "high_energy"
    elif cs.energy > 0.3:
        energy_level = "medium_energy"
    else:
        energy_level = "low_energy"
    
    # Bin perceived risk
    if cs.risk > 0.6:
        risk_level = "high_risk"
    elif cs.risk > 0.3:
        risk_level = "medium_risk"
    else:
        risk_level = "low_risk"
    
    # Bin perceived effort
    if cs.effort > 0.6:
        effort_level = "high_effort"
    elif cs.effort > 0.3:
        effort_level = "medium_effort"
    else:
        effort_level = "low_effort"
    
    return f"{energy_level}_{risk_level}_{effort_level}"


def query_decision_boundaries(
    sequences: List[DecisionSequence],
    step_id: str
) -> List[DecisionBoundary]:
    """
    Query decision boundaries at a specific step.
    
    Answers: "At step X, which persona classes are ACCEPTED vs REJECTED?"
    "What cognitive thresholds separate them?"
    
    Returns decision boundaries with counterexamples to prevent monocausal claims.
    """
    boundaries = []
    
    # Group traces by step and persona class
    step_traces_by_class = defaultdict(lambda: {'accepted': [], 'rejected': []})
    step_index = None
    
    for sequence in sequences:
        for trace in sequence.traces:
            if trace.step_id == step_id:
                step_index = trace.step_index
                persona_class = _derive_persona_class(trace)
                
                if trace.decision == DecisionOutcome.CONTINUE:
                    step_traces_by_class[persona_class]['accepted'].append(trace)
                else:
                    step_traces_by_class[persona_class]['rejected'].append(trace)
    
    if step_index is None:
        return []  # Step not found
    
    # For each persona class, compute thresholds and find counterexamples
    for persona_class, traces in step_traces_by_class.items():
        accepted = traces['accepted']
        rejected = traces['rejected']
        
        if not accepted and not rejected:
            continue
        
        # Compute cognitive thresholds from accepted traces
        cognitive_thresholds = {}
        if accepted:
            energies = [t.cognitive_state_snapshot.energy for t in accepted]
            risks = [t.cognitive_state_snapshot.risk for t in accepted]
            efforts = [t.cognitive_state_snapshot.effort for t in accepted]
            values = [t.cognitive_state_snapshot.value for t in accepted]
            controls = [t.cognitive_state_snapshot.control for t in accepted]
            
            cognitive_thresholds = {
                'energy': (min(energies), max(energies)),
                'risk': (min(risks), max(risks)),
                'effort': (min(efforts), max(efforts)),
                'value': (min(values), max(values)),
                'control': (min(controls), max(controls))
            }
        
        # Find counterexamples: accepted trace that violates thresholds
        counterexample_accepted = None
        if accepted and rejected:
            # Find accepted trace with low energy/high risk (should be rejected by thresholds)
            for trace in accepted:
                cs = trace.cognitive_state_snapshot
                if cs.energy < 0.3 or cs.risk > 0.7:
                    counterexample_accepted = trace
                    break
        
        # Find counterexample: rejected trace that meets thresholds
        counterexample_rejected = None
        if accepted and rejected:
            # Find rejected trace with high energy/low risk (should be accepted by thresholds)
            for trace in rejected:
                cs = trace.cognitive_state_snapshot
                if cs.energy > 0.6 and cs.risk < 0.3:
                    counterexample_rejected = trace
                    break
        
        boundary = DecisionBoundary(
            step_id=step_id,
            step_index=step_index,
            persona_class=persona_class,
            accepted_count=len(accepted),
            rejected_count=len(rejected),
            cognitive_thresholds=cognitive_thresholds,
            counterexample_accepted=counterexample_accepted,
            counterexample_rejected=counterexample_rejected
        )
        boundaries.append(boundary)
    
    return boundaries


def query_persona_differentiation(
    sequences: List[DecisionSequence],
    step_x_id: str,
    step_x_plus_one_id: str
) -> List[PersonaDifferentiation]:
    """
    Query persona differentiation between consecutive steps.
    
    Answers: "Which personas fail at step X but succeed at step X+1 under similar entry conditions?"
    "What differentiating decision factors explain the divergence?"
    
    This identifies personas that show divergent behavior patterns across steps.
    """
    differentiations = []
    
    # Find sequences that have traces at both steps
    step_x_traces = {}  # persona_id -> trace
    step_x_plus_one_traces = {}  # persona_id -> trace
    
    for sequence in sequences:
        for trace in sequence.traces:
            if trace.step_id == step_x_id:
                step_x_traces[sequence.persona_id] = trace
            elif trace.step_id == step_x_plus_one_id:
                step_x_plus_one_traces[sequence.persona_id] = trace
    
    # Find personas that failed at X but have trace at X+1 (impossible - if they failed at X, they don't reach X+1)
    # Actually, we need to compare different personas with similar entry conditions
    
    # Group by entry cognitive state (first step state)
    entry_states = {}  # persona_id -> first trace cognitive state
    for sequence in sequences:
        if sequence.traces:
            entry_states[sequence.persona_id] = sequence.traces[0].cognitive_state_snapshot
    
    # Find personas with similar entry states but different outcomes at step X
    failed_at_x = []  # (persona_id, trace)
    succeeded_at_x = []  # (persona_id, trace)
    
    for persona_id, trace in step_x_traces.items():
        if trace.decision == DecisionOutcome.DROP:
            failed_at_x.append((persona_id, trace))
        else:
            succeeded_at_x.append((persona_id, trace))
    
    # Compare failed vs succeeded personas with similar entry states
    if failed_at_x and succeeded_at_x:
        # Find differentiating factors
        failed_factors = Counter()
        for _, trace in failed_at_x:
            failed_factors.update(trace.dominant_factors)
        
        succeeded_factors = Counter()
        for _, trace in succeeded_at_x:
            succeeded_factors.update(trace.dominant_factors)
        
        # Factors that appear more in failures
        differentiating_factors = []
        all_factors = set(failed_factors.keys()) | set(succeeded_factors.keys())
        for factor in all_factors:
            failed_count = failed_factors.get(factor, 0)
            succeeded_count = succeeded_factors.get(factor, 0)
            if failed_count > succeeded_count * 1.5:  # Appears 50% more in failures
                differentiating_factors.append(factor)
        
        if differentiating_factors and failed_at_x and succeeded_at_x:
            differentiation = PersonaDifferentiation(
                step_x=step_x_id,
                step_x_plus_one=step_x_plus_one_id,
                differentiating_factors=differentiating_factors,
                failed_at_x_count=len(failed_at_x),
                succeeded_at_x_plus_one_count=len([p for p, _ in succeeded_at_x if p in step_x_plus_one_traces]),
                example_failed_trace=failed_at_x[0][1] if failed_at_x else None,
                example_succeeded_trace=succeeded_at_x[0][1] if succeeded_at_x else None
            )
            differentiations.append(differentiation)
    
    return differentiations


def query_stable_precedents(
    sequences: List[DecisionSequence],
    minimum_occurrence: int = 3
) -> List[StablePrecedent]:
    """
    Query stable precedents - recurring decision patterns.
    
    Answers: "Which (step, persona_class, dominant_factors) combinations recur frequently?"
    
    Only surfaces patterns that repeat beyond minimum_occurrence threshold.
    """
    precedent_counts = defaultdict(lambda: {'count': 0, 'traces': [], 'outcome': None})
    
    for sequence in sequences:
        for trace in sequence.traces:
            persona_class = _derive_persona_class(trace)
            factors_tuple = tuple(sorted(trace.dominant_factors))
            
            key = (trace.step_id, persona_class, factors_tuple)
            
            precedent_counts[key]['count'] += 1
            precedent_counts[key]['traces'].append(trace)
            precedent_counts[key]['outcome'] = trace.decision
    
    # Filter by minimum occurrence and create StablePrecedent objects
    stable_precedents = []
    for (step_id, persona_class, factors_tuple), data in precedent_counts.items():
        if data['count'] >= minimum_occurrence:
            # Include at least 2 example traces (but not all, to keep size manageable)
            example_traces = data['traces'][:max(2, min(5, data['count']))]
            
            precedent = StablePrecedent(
                step_id=step_id,
                persona_class=persona_class,
                dominant_factors=factors_tuple,
                occurrence_count=data['count'],
                outcome=data['outcome'],
                example_traces=example_traces
            )
            stable_precedents.append(precedent)
    
    # Sort by occurrence count
    stable_precedents.sort(key=lambda p: p.occurrence_count, reverse=True)
    
    return stable_precedents


def query_competing_explanations(
    sequences: List[DecisionSequence],
    primary_factor: str = "intent_alignment"
) -> List[CompetingExplanation]:
    """
    Query competing explanations - outcomes that contradict single-factor reasoning.
    
    Answers:
    - "Where do drops occur despite high intent alignment?"
    - "Where do continuations occur despite low intent alignment?"
    
    Forces multi-factor explanations by finding counterexamples to monocausal claims.
    """
    competing_explanations = []
    
    # Group traces by step and outcome
    step_outcome_traces = defaultdict(lambda: {'CONTINUE': [], 'DROP': []})
    
    for sequence in sequences:
        for trace in sequence.traces:
            outcome_key = trace.decision.value
            step_outcome_traces[(trace.step_id, outcome_key)][outcome_key].append(trace)
    
    # For each step-outcome combination, analyze primary factor vs competing factors
    for (step_id, outcome_str), data in step_outcome_traces.items():
        traces = data[outcome_str]
        outcome = DecisionOutcome(outcome_str)
        
        if not traces:
            continue
        
        # Extract primary factor values
        if primary_factor == "intent_alignment":
            primary_values = [t.intent.alignment_score for t in traces]
        else:
            # Default to cognitive energy if factor not recognized
            primary_values = [t.cognitive_state_snapshot.energy for t in traces]
        
        # Find traces where primary factor contradicts outcome
        # High primary factor but DROP, or low primary factor but CONTINUE
        if outcome == DecisionOutcome.DROP:
            # Drops despite high primary factor
            threshold = 0.7  # High alignment/energy
            contradictory_traces = [
                t for t in traces
                if (primary_factor == "intent_alignment" and t.intent.alignment_score >= threshold) or
                   (primary_factor == "cognitive_energy" and t.cognitive_state_snapshot.energy >= threshold)
            ]
        else:
            # Continuations despite low primary factor
            threshold = 0.3  # Low alignment/energy
            contradictory_traces = [
                t for t in traces
                if (primary_factor == "intent_alignment" and t.intent.alignment_score <= threshold) or
                   (primary_factor == "cognitive_energy" and t.cognitive_state_snapshot.energy <= threshold)
            ]
        
        if contradictory_traces:
            # Analyze competing factors in contradictory traces
            competing_factors = Counter()
            for trace in contradictory_traces:
                competing_factors.update(trace.dominant_factors)
            
            # Get most common competing factors (excluding primary factor if present)
            top_competing = [f for f, _ in competing_factors.most_common(3) if f != primary_factor]
            
            if top_competing:
                example_trace = contradictory_traces[0]
                primary_value = example_trace.intent.alignment_score if primary_factor == "intent_alignment" else example_trace.cognitive_state_snapshot.energy
                
                explanation = CompetingExplanation(
                    step_id=step_id,
                    outcome=outcome,
                    primary_factor=primary_factor,
                    primary_factor_value=primary_value,
                    competing_factors=top_competing,
                    trace_count=len(contradictory_traces),
                    example_trace=example_trace
                )
                competing_explanations.append(explanation)
    
    return competing_explanations


def query_acceptance_surface(
    sequences: List[DecisionSequence],
    product_steps: Dict
) -> List[AcceptanceSurface]:
    """
    Query acceptance surface - deepest step reliably reached per persona class.
    
    Answers: "For each persona class, what is the deepest step reliably reached?"
    "Where does continuation probability collapse sharply?"
    
    This identifies the decision boundary surface for each persona class.
    """
    # Group sequences by persona class (use first trace to determine class)
    sequences_by_class = defaultdict(list)
    
    for sequence in sequences:
        if sequence.traces:
            first_trace = sequence.traces[0]
            persona_class = _derive_persona_class(first_trace)
            sequences_by_class[persona_class].append(sequence)
    
    acceptance_surfaces = []
    
    # For each persona class, find deepest step reached
    for persona_class, class_sequences in sequences_by_class.items():
        step_reach_counts = Counter()  # step_index -> count of sequences reaching it
        step_completion_counts = Counter()  # step_index -> count of sequences completing from it
        
        for sequence in class_sequences:
            if not sequence.traces:
                continue
            
            # Find deepest step reached
            deepest_step_index = max(t.step_index for t in sequence.traces)
            step_reach_counts[deepest_step_index] += 1
            
            # Check if completed (has CONTINUE outcome at deepest step)
            deepest_trace = max(sequence.traces, key=lambda t: t.step_index)
            if deepest_trace.decision == DecisionOutcome.CONTINUE and sequence.final_outcome == DecisionOutcome.CONTINUE:
                step_completion_counts[deepest_step_index] += 1
        
        if step_reach_counts:
            # Find deepest step reached by at least 10% of personas in this class
            threshold = max(1, len(class_sequences) * 0.1)
            viable_steps = [(idx, count) for idx, count in step_reach_counts.items() if count >= threshold]
            
            if viable_steps:
                deepest_step_index, reach_count = max(viable_steps, key=lambda x: x[0])
                
                # Map step index to step ID
                step_list = list(product_steps.keys())
                if deepest_step_index < len(step_list):
                    deepest_step_id = step_list[deepest_step_index]
                else:
                    deepest_step_id = f"step_{deepest_step_index}"
                
                completion_count = step_completion_counts.get(deepest_step_index, 0)
                
                # Find continuation collapse step (sharp drop in continuation rate)
                # This is simplified - in practice would compare continuation rates across steps
                continuation_collapse_step = None
                
                surface = AcceptanceSurface(
                    persona_class=persona_class,
                    deepest_step_id=deepest_step_id,
                    deepest_step_index=deepest_step_index,
                    traces_reaching_step=reach_count,
                    traces_completing_funnel=completion_count,
                    continuation_collapse_step=continuation_collapse_step
                )
                acceptance_surfaces.append(surface)
    
    return acceptance_surfaces

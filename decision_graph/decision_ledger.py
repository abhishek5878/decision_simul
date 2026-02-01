"""
decision_ledger.py - Decision Ledger Output Generation

This output is a decision ledger, not an analysis or recommendation.

All outputs are audit-grade and interpretation-free.
Every assertion must be verifiable directly from DecisionTrace objects.
No narrative, interpretation, or funnel language is permitted.

───────────────────────────────────────────────────────────────────────────────
LEDGER INVARIANTS — READ BEFORE MODIFYING
───────────────────────────────────────────────────────────────────────────────

1. NO RATES OR NORMALIZED VALUES
   - Remove occurrence rates, densities, percentages, or ratios.
   - Keep only raw counts, timestamps, and presence/absence facts.
   - If a value implies comparison, it does not belong in the ledger.

2. STABLE-ONLY DECISION BOUNDARIES
   - Decision Boundaries MUST include only:
     - Pattern Stable == True
     - Supporting Traces >= MIN_BOUNDARY_SUPPORT (default: 10)
   - Unstable patterns must be excluded and placed in:
     "NON-BINDING OBSERVATIONS (EXCLUDED)"

3. DOMINANT FACTORS AS SETS, NOT LABELS
   - Replace categorical "Dominant Factors" with factor presence sets.
   - Presence count per factor (no percentages).
   - Example: cognitive_fatigue: present_in_traces = 4021

4. REPLAY-COMPLETE COUNTEREXAMPLES
   - Every counterexample MUST include:
     - persona_id
     - violated_threshold(s)
     - observed_value vs threshold
   - Counterexamples without violation context are invalid.

5. PRECEDENT SEPARATION
   - Split precedents into two distinct sections:
     - PRECEDENTS — ACCEPTANCE
     - PRECEDENTS — REJECTION
   - Never mix CONTINUE and DROP outcomes in the same list.

6. LEDGER LANGUAGE RULE
   - No adjectives (high, low, significant, major).
   - No interpretive verbs (shows, indicates, suggests, implies).
   - Use ledger-style terms only:
     observed, recorded, present, absent, first_seen, last_seen.

If a value helps interpretation, remove it.
If a value helps replay, keep it.
"""

from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from decision_graph.decision_trace import DecisionTrace, DecisionSequence, DecisionOutcome
import numpy as np
from datetime import datetime


# Constants
MIN_BOUNDARY_SUPPORT = 10  # Minimum traces required for a stable boundary


@dataclass
class PersonaClassCoherence:
    """
    Persona class coherence metrics.
    
    Persona classes are artifacts, not truth. This measures their internal stability.
    """
    persona_class: str
    trace_count: int
    
    # Internal variance (cognitive state dimensions)
    energy_variance: float
    risk_variance: float
    effort_variance: float
    value_variance: float
    control_variance: float
    
    # Dominant factor variance (how consistent are factors within class)
    dominant_factor_variance: float  # Jaccard distance or similar
    
    # Counterexample rate (traces that violate expected class behavior)
    counterexample_rate: float
    
    # Coherence threshold: if variance exceeds threshold, class is UNSTABLE
    coherence_score: float  # 0-1, higher = more coherent
    is_stable: bool
    
    def to_dict(self) -> Dict:
        return {
            'persona_class': self.persona_class,
            'trace_count': self.trace_count,
            'energy_variance': float(self.energy_variance),
            'risk_variance': float(self.risk_variance),
            'effort_variance': float(self.effort_variance),
            'value_variance': float(self.value_variance),
            'control_variance': float(self.control_variance),
            'dominant_factor_variance': float(self.dominant_factor_variance),
            'counterexample_rate': float(self.counterexample_rate),
            'coherence_score': float(self.coherence_score),
            'is_stable': self.is_stable
        }


@dataclass
class FactorPresence:
    """
    Factor presence record (ledger-style, not categorical).
    
    Records presence count, not percentage or rate.
    """
    factor_name: str
    present_in_traces: int  # Raw count only
    
    def to_dict(self) -> Dict:
        return {
            'factor_name': self.factor_name,
            'present_in_traces': self.present_in_traces
        }


@dataclass
class CounterexampleRecord:
    """
    Replay-complete counterexample record.
    
    Must include all information needed to replay the violation.
    """
    persona_id: str
    violated_thresholds: Dict[str, Dict[str, float]]  # {dimension: {"threshold_min": x, "threshold_max": y, "observed": z}}
    
    def to_dict(self) -> Dict:
        return {
            'persona_id': self.persona_id,
            'violated_thresholds': self.violated_thresholds
        }


@dataclass
class DecisionBoundaryAssertion:
    """
    Decision boundary assertion (assertion layer only).
    
    Machine-verifiable facts about decision boundaries.
    Only stable patterns are included.
    """
    step_id: str
    step_index: int
    persona_class: str
    persona_class_coherence: PersonaClassCoherence
    
    accepted_count: int
    rejected_count: int
    
    # Observed cognitive thresholds (from accepted traces only)
    cognitive_thresholds: Dict[str, Tuple[float, float]]  # (min, max) per dimension
    
    # Supporting trace counts (raw count only)
    supporting_trace_count: int
    
    # Factor presence sets (not categorical labels)
    factor_presence: List[FactorPresence]
    
    # Replay-complete counterexamples
    counterexamples: List[CounterexampleRecord]
    
    # Precedent layer (timestamps only, no rates)
    first_observed_timestamp: str
    last_observed_timestamp: str
    occurrence_count: int
    is_stable_pattern: bool
    
    def to_dict(self) -> Dict:
        return {
            'step_id': self.step_id,
            'step_index': self.step_index,
            'persona_class': self.persona_class,
            'persona_class_coherence': self.persona_class_coherence.to_dict(),
            'accepted_count': self.accepted_count,
            'rejected_count': self.rejected_count,
            'cognitive_thresholds': {
                k: [float(v[0]), float(v[1])] for k, v in self.cognitive_thresholds.items()
            },
            'supporting_trace_count': self.supporting_trace_count,
            'factor_presence': [fp.to_dict() for fp in self.factor_presence],
            'counterexamples': [ce.to_dict() for ce in self.counterexamples],
            'first_observed_timestamp': self.first_observed_timestamp,
            'last_observed_timestamp': self.last_observed_timestamp,
            'occurrence_count': self.occurrence_count,
            'is_stable_pattern': self.is_stable_pattern
        }


@dataclass
class PrecedentAssertion:
    """
    Precedent assertion (assertion layer only).
    
    Historical grounding for recurring patterns.
    Contains only raw counts and timestamps (no rates).
    """
    step_id: str
    persona_class: str
    factor_presence: List[FactorPresence]
    outcome: DecisionOutcome
    
    occurrence_count: int  # Raw count only
    first_observed_timestamp: str
    last_observed_timestamp: str
    time_span_seconds: int  # Raw seconds, not days or normalized
    
    # Stability flag (based on occurrence count, not rate)
    is_stable: bool  # Based on occurrence_count >= MIN_BOUNDARY_SUPPORT
    
    def to_dict(self) -> Dict:
        return {
            'step_id': self.step_id,
            'persona_class': self.persona_class,
            'factor_presence': [fp.to_dict() for fp in self.factor_presence],
            'outcome': self.outcome.value,
            'occurrence_count': self.occurrence_count,
            'first_observed_timestamp': self.first_observed_timestamp,
            'last_observed_timestamp': self.last_observed_timestamp,
            'time_span_seconds': self.time_span_seconds,
            'is_stable': self.is_stable
        }


@dataclass
class DecisionTerminationPoint:
    """
    Decision termination point (replaces "decision density").
    
    Records last step where rejections are observed.
    Contains only raw counts and timestamps (no densities).
    """
    step_id: str
    step_index: int
    
    # Decision boundary presence
    has_observed_rejections: bool
    rejection_decision_count: int  # Raw count only
    
    # Precedent layer (timestamps only)
    first_rejection_timestamp: Optional[str]
    last_rejection_timestamp: Optional[str]
    
    def to_dict(self) -> Dict:
        return {
            'step_id': self.step_id,
            'step_index': self.step_index,
            'has_observed_rejections': self.has_observed_rejections,
            'rejection_decision_count': self.rejection_decision_count,
            'first_rejection_timestamp': self.first_rejection_timestamp,
            'last_rejection_timestamp': self.last_rejection_timestamp
        }


def _derive_persona_class(trace: DecisionTrace) -> str:
    """Derive persona class from cognitive state (deterministic binning)."""
    cs = trace.cognitive_state_snapshot
    
    energy_level = "high_energy" if cs.energy > 0.6 else ("medium_energy" if cs.energy > 0.3 else "low_energy")
    risk_level = "high_risk" if cs.risk > 0.6 else ("medium_risk" if cs.risk > 0.3 else "low_risk")
    effort_level = "high_effort" if cs.effort > 0.6 else ("medium_effort" if cs.effort > 0.3 else "low_effort")
    
    return f"{energy_level}_{risk_level}_{effort_level}"


def compute_persona_class_coherence(
    traces: List[DecisionTrace],
    persona_class: str,
    coherence_threshold: float = 0.7
) -> PersonaClassCoherence:
    """
    Compute persona class coherence metrics.
    
    Measures internal stability of a persona class.
    If coherence is low, class is marked UNSTABLE.
    """
    if not traces:
        return PersonaClassCoherence(
            persona_class=persona_class,
            trace_count=0,
            energy_variance=0.0,
            risk_variance=0.0,
            effort_variance=0.0,
            value_variance=0.0,
            control_variance=0.0,
            dominant_factor_variance=0.0,
            counterexample_rate=0.0,
            coherence_score=0.0,
            is_stable=False
        )
    
    # Compute cognitive state variance
    energies = [t.cognitive_state_snapshot.energy for t in traces]
    risks = [t.cognitive_state_snapshot.risk for t in traces]
    efforts = [t.cognitive_state_snapshot.effort for t in traces]
    values = [t.cognitive_state_snapshot.value for t in traces]
    controls = [t.cognitive_state_snapshot.control for t in traces]
    
    energy_variance = float(np.var(energies))
    risk_variance = float(np.var(risks))
    effort_variance = float(np.var(efforts))
    value_variance = float(np.var(values))
    control_variance = float(np.var(controls))
    
    # Compute dominant factor variance (Jaccard distance)
    factor_sets = [set(t.dominant_factors) for t in traces]
    if len(factor_sets) > 1:
        # Average pairwise Jaccard distance
        jaccard_distances = []
        for i in range(len(factor_sets)):
            for j in range(i + 1, len(factor_sets)):
                intersection = len(factor_sets[i] & factor_sets[j])
                union = len(factor_sets[i] | factor_sets[j])
                if union > 0:
                    jaccard = 1.0 - (intersection / union)
                    jaccard_distances.append(jaccard)
        dominant_factor_variance = float(np.mean(jaccard_distances)) if jaccard_distances else 0.0
    else:
        dominant_factor_variance = 0.0
    
    # Coherence score (inverse of normalized variance)
    # Lower variance = higher coherence
    max_variance = 0.25  # Theoretical max for 0-1 range
    normalized_variance = (
        (energy_variance + risk_variance + effort_variance + value_variance + control_variance) / 5.0
    ) / max_variance
    
    coherence_score = max(0.0, 1.0 - normalized_variance - dominant_factor_variance)
    is_stable = coherence_score >= coherence_threshold
    
    # Counterexample rate (simplified - would need expected behavior definition)
    counterexample_rate = 0.0  # Placeholder - would compute based on expected class behavior
    
    return PersonaClassCoherence(
        persona_class=persona_class,
        trace_count=len(traces),
        energy_variance=energy_variance,
        risk_variance=risk_variance,
        effort_variance=effort_variance,
        value_variance=value_variance,
        control_variance=control_variance,
        dominant_factor_variance=dominant_factor_variance,
        counterexample_rate=counterexample_rate,
        coherence_score=coherence_score,
        is_stable=is_stable
    )


def _compute_factor_presence(traces: List[DecisionTrace]) -> List[FactorPresence]:
    """
    Compute factor presence counts (not percentages).
    
    Returns list of FactorPresence objects with raw counts only.
    """
    factor_counts = Counter()
    for trace in traces:
        for factor in trace.dominant_factors:
            factor_counts[factor] += 1
    
    return [
        FactorPresence(factor_name=factor, present_in_traces=count)
        for factor, count in sorted(factor_counts.items(), key=lambda x: x[1], reverse=True)
    ]


def _find_replay_complete_counterexamples(
    accepted_traces: List[DecisionTrace],
    rejected_traces: List[DecisionTrace],
    cognitive_thresholds: Dict[str, Tuple[float, float]]
) -> List[CounterexampleRecord]:
    """
    Find replay-complete counterexamples.
    
    Each counterexample includes persona_id, violated thresholds, and observed values.
    """
    counterexamples = []
    
    if not cognitive_thresholds or not rejected_traces:
        return counterexamples
    
    # Find rejected traces that meet thresholds (should have been accepted)
    for trace in rejected_traces[:5]:  # Limit to 5 for ledger size
        cs = trace.cognitive_state_snapshot
        violated = {}
        
        for dimension, (threshold_min, threshold_max) in cognitive_thresholds.items():
            if dimension == 'energy':
                observed = cs.energy
                if threshold_min <= observed <= threshold_max:
                    # Met threshold but was rejected
                    violated[dimension] = {
                        'threshold_min': float(threshold_min),
                        'threshold_max': float(threshold_max),
                        'observed': float(observed)
                    }
            elif dimension == 'risk':
                observed = cs.risk
                if threshold_min <= observed <= threshold_max:
                    violated[dimension] = {
                        'threshold_min': float(threshold_min),
                        'threshold_max': float(threshold_max),
                        'observed': float(observed)
                    }
            elif dimension == 'effort':
                observed = cs.effort
                if threshold_min <= observed <= threshold_max:
                    violated[dimension] = {
                        'threshold_min': float(threshold_min),
                        'threshold_max': float(threshold_max),
                        'observed': float(observed)
                    }
            elif dimension == 'value':
                observed = cs.value
                if threshold_min <= observed <= threshold_max:
                    violated[dimension] = {
                        'threshold_min': float(threshold_min),
                        'threshold_max': float(threshold_max),
                        'observed': float(observed)
                    }
            elif dimension == 'control':
                observed = cs.control
                if threshold_min <= observed <= threshold_max:
                    violated[dimension] = {
                        'threshold_min': float(threshold_min),
                        'threshold_max': float(threshold_max),
                        'observed': float(observed)
                    }
        
        if violated:
            counterexamples.append(CounterexampleRecord(
                persona_id=trace.persona_id,
                violated_thresholds=violated
            ))
    
    return counterexamples


def generate_decision_boundary_assertions(
    sequences: List[DecisionSequence],
    step_id: str
) -> Tuple[List[DecisionBoundaryAssertion], List[Dict]]:
    """
    Generate decision boundary assertions for a step.
    
    Returns:
    - List of stable boundary assertions (for ledger)
    - List of unstable patterns (for exclusion section)
    
    Only includes patterns with:
    - Pattern Stable == True
    - Supporting Traces >= MIN_BOUNDARY_SUPPORT
    """
    stable_assertions = []
    unstable_patterns = []
    
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
        return [], []
    
    # Generate assertions for each persona class
    for persona_class, traces in step_traces_by_class.items():
        accepted = traces['accepted']
        rejected = traces['rejected']
        all_traces = accepted + rejected
        
        if not all_traces:
            continue
        
        # Compute coherence
        coherence = compute_persona_class_coherence(all_traces, persona_class)
        
        # Check stability requirements
        is_stable_pattern = (
            coherence.is_stable and
            len(all_traces) >= MIN_BOUNDARY_SUPPORT
        )
        
        if not is_stable_pattern:
            # Record as unstable pattern (excluded from ledger)
            unstable_patterns.append({
                'step_id': step_id,
                'persona_class': persona_class,
                'trace_count': len(all_traces),
                'coherence_stable': coherence.is_stable,
                'meets_support_threshold': len(all_traces) >= MIN_BOUNDARY_SUPPORT
            })
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
                'energy': (float(min(energies)), float(max(energies))),
                'risk': (float(min(risks)), float(max(risks))),
                'effort': (float(min(efforts)), float(max(efforts))),
                'value': (float(min(values)), float(max(values))),
                'control': (float(min(controls)), float(max(controls)))
            }
        
        # Compute factor presence (not categorical labels)
        factor_presence = _compute_factor_presence(all_traces)
        
        # Find replay-complete counterexamples
        counterexamples = _find_replay_complete_counterexamples(
            accepted, rejected, cognitive_thresholds
        )
        
        # Precedent layer: timestamps
        timestamps = [t.timestamp for t in all_traces if t.timestamp]
        first_timestamp = min(timestamps) if timestamps else datetime.now().isoformat()
        last_timestamp = max(timestamps) if timestamps else datetime.now().isoformat()
        
        assertion = DecisionBoundaryAssertion(
            step_id=step_id,
            step_index=step_index,
            persona_class=persona_class,
            persona_class_coherence=coherence,
            accepted_count=len(accepted),
            rejected_count=len(rejected),
            cognitive_thresholds=cognitive_thresholds,
            supporting_trace_count=len(all_traces),
            factor_presence=factor_presence,
            counterexamples=counterexamples,
            first_observed_timestamp=first_timestamp,
            last_observed_timestamp=last_timestamp,
            occurrence_count=len(all_traces),
            is_stable_pattern=True  # Only stable patterns reach here
        )
        stable_assertions.append(assertion)
    
    return stable_assertions, unstable_patterns


def generate_precedent_assertions(
    sequences: List[DecisionSequence],
    outcome: DecisionOutcome,
    minimum_occurrence: int = MIN_BOUNDARY_SUPPORT
) -> List[PrecedentAssertion]:
    """
    Generate precedent assertions for a specific outcome.
    
    Separate function for ACCEPTANCE and REJECTION precedents.
    Contains only raw counts and timestamps (no rates).
    """
    precedent_data = defaultdict(lambda: {
        'count': 0,
        'traces': [],
        'personas': set()
    })
    
    for sequence in sequences:
        for trace in sequence.traces:
            if trace.decision != outcome:
                continue
            
            persona_class = _derive_persona_class(trace)
            factors_tuple = tuple(sorted(trace.dominant_factors))
            
            key = (trace.step_id, persona_class, factors_tuple)
            
            precedent_data[key]['count'] += 1
            precedent_data[key]['traces'].append(trace)
            precedent_data[key]['personas'].add(sequence.persona_id)
    
    assertions = []
    
    for (step_id, persona_class, factors_tuple), data in precedent_data.items():
        if data['count'] < minimum_occurrence:
            continue
        
        traces = data['traces']
        timestamps = [t.timestamp for t in traces if t.timestamp]
        
        if not timestamps:
            continue
        
        first_timestamp = min(timestamps)
        last_timestamp = max(timestamps)
        
        # Compute time span in seconds (raw, not normalized)
        try:
            first_dt = datetime.fromisoformat(first_timestamp.replace('Z', '+00:00'))
            last_dt = datetime.fromisoformat(last_timestamp.replace('Z', '+00:00'))
            time_span_seconds = int((last_dt - first_dt).total_seconds())
        except:
            time_span_seconds = 0
        
        # Factor presence (not categorical labels)
        factor_presence = _compute_factor_presence(traces)
        
        # Stability based on occurrence count (not rate)
        is_stable = data['count'] >= MIN_BOUNDARY_SUPPORT
        
        assertion = PrecedentAssertion(
            step_id=step_id,
            persona_class=persona_class,
            factor_presence=factor_presence,
            outcome=outcome,
            occurrence_count=data['count'],
            first_observed_timestamp=first_timestamp,
            last_observed_timestamp=last_timestamp,
            time_span_seconds=time_span_seconds,
            is_stable=is_stable
        )
        assertions.append(assertion)
    
    # Sort by occurrence count
    assertions.sort(key=lambda a: a.occurrence_count, reverse=True)
    
    return assertions


def generate_decision_termination_points(
    sequences: List[DecisionSequence],
    product_steps: Dict
) -> List[DecisionTerminationPoint]:
    """
    Generate decision termination points.
    
    Records last step where rejections are observed.
    Contains only raw counts and timestamps (no densities).
    """
    # Build step index mapping
    step_indices = {}
    for idx, step_id in enumerate(product_steps.keys()):
        step_indices[step_id] = idx
    
    # Collect rejection decisions per step
    step_rejections = defaultdict(lambda: {'count': 0, 'timestamps': []})
    
    for sequence in sequences:
        for trace in sequence.traces:
            if trace.decision == DecisionOutcome.DROP:
                step_id = trace.step_id
                step_rejections[step_id]['count'] += 1
                if trace.timestamp:
                    step_rejections[step_id]['timestamps'].append(trace.timestamp)
    
    assertions = []
    
    for step_id in product_steps.keys():
        step_index = step_indices.get(step_id, -1)
        rejection_data = step_rejections.get(step_id, {'count': 0, 'timestamps': []})
        
        has_rejections = rejection_data['count'] > 0
        rejection_count = rejection_data['count']
        
        timestamps = rejection_data['timestamps']
        first_rejection_timestamp = min(timestamps) if timestamps else None
        last_rejection_timestamp = max(timestamps) if timestamps else None
        
        assertion = DecisionTerminationPoint(
            step_id=step_id,
            step_index=step_index,
            has_observed_rejections=has_rejections,
            rejection_decision_count=rejection_count,
            first_rejection_timestamp=first_rejection_timestamp,
            last_rejection_timestamp=last_rejection_timestamp
        )
        assertions.append(assertion)
    
    return assertions


def generate_decision_ledger(
    sequences: List[DecisionSequence],
    product_steps: Dict,
    step_ids: Optional[List[str]] = None
) -> Dict:
    """
    Generate complete decision ledger.
    
    Returns audit-grade, interpretation-free output.
    No narrative, no interpretation, no funnel language.
    
    Structure:
    - Metadata
    - DECISION BOUNDARIES (stable only)
    - PRECEDENTS — ACCEPTANCE
    - PRECEDENTS — REJECTION
    - DECISION TERMINATION POINTS
    - NON-BINDING OBSERVATIONS (EXCLUDED)
    """
    if step_ids is None:
        step_ids = list(product_steps.keys())
    
    # Generate assertions
    decision_boundaries = []
    unstable_patterns = []
    for step_id in step_ids:
        boundaries, unstable = generate_decision_boundary_assertions(sequences, step_id)
        decision_boundaries.extend(boundaries)
        unstable_patterns.extend(unstable)
    
    # Separate precedents by outcome
    acceptance_precedents = generate_precedent_assertions(sequences, DecisionOutcome.CONTINUE, minimum_occurrence=MIN_BOUNDARY_SUPPORT)
    rejection_precedents = generate_precedent_assertions(sequences, DecisionOutcome.DROP, minimum_occurrence=MIN_BOUNDARY_SUPPORT)
    
    decision_termination_points = generate_decision_termination_points(sequences, product_steps)
    
    return {
        'decision_boundaries': [b.to_dict() for b in decision_boundaries],
        'precedents_acceptance': [p.to_dict() for p in acceptance_precedents],
        'precedents_rejection': [p.to_dict() for p in rejection_precedents],
        'decision_termination_points': [d.to_dict() for d in decision_termination_points],
        'non_binding_observations_excluded': unstable_patterns,
        'generated_timestamp': datetime.now().isoformat(),
        'total_sequences': len(sequences),
        'total_steps': len(product_steps)
    }

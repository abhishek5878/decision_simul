#!/usr/bin/env python3
"""
Credigo Decision System Analyzer

Analyzes Credigo as a decision-making machine from decision traces.
"""

import json
from typing import Dict, List
from collections import defaultdict, Counter
from dataclasses import dataclass
from pathlib import Path

from sensitivity_engine.decision_trace_extended import SensitivityDecisionTrace, DecisionOutcome


@dataclass
class DecisionGate:
    """A decision gate where the product accepts or rejects users."""
    step_id: str
    step_index: int
    signal_demanded: str
    passes_count: int
    fails_count: int
    total_count: int
    pass_rate: float
    
    # Who passes (from traces)
    passing_persona_characteristics: Dict[str, float]  # e.g., {'high_energy': 0.8, 'low_risk': 0.9}
    failing_persona_characteristics: Dict[str, float]
    
    # Forces at this gate
    avg_forces_pass: Dict[str, float]
    avg_forces_fail: Dict[str, float]


def analyze_credigo_decision_system(ledger_file: str) -> Dict:
    """
    Analyze Credigo as a decision-making system.
    
    Returns analysis structured for founder narrative.
    """
    # Load ledger
    with open(ledger_file, 'r') as f:
        ledger_data = json.load(f)
    
    # Extract Credigo traces
    credigo_traces = [
        SensitivityDecisionTrace.from_dict(t)
        for t in ledger_data.get('target_traces', [])
    ]
    
    print(f"Analyzing {len(credigo_traces)} decision traces...")
    
    # Step 1: Identify decision gates
    decision_gates = identify_decision_gates(credigo_traces)
    
    # Step 2: Analyze who passes vs fails at each gate
    gate_analysis = analyze_gates(credigo_traces, decision_gates)
    
    # Step 3: Infer implicit user contract
    user_contract = infer_user_contract(credigo_traces, gate_analysis)
    
    # Step 4: Analyze filtering patterns
    filtering_patterns = analyze_filtering_patterns(credigo_traces, gate_analysis)
    
    # Step 5: Extract tradeoffs
    tradeoffs = extract_tradeoffs(credigo_traces, gate_analysis)
    
    return {
        'decision_gates': gate_analysis,
        'user_contract': user_contract,
        'filtering_patterns': filtering_patterns,
        'tradeoffs': tradeoffs,
        'raw_traces_count': len(credigo_traces)
    }


def identify_decision_gates(traces: List[SensitivityDecisionTrace]) -> List[str]:
    """Identify steps where meaningful rejection occurs."""
    # Group by step
    by_step = defaultdict(list)
    for trace in traces:
        by_step[trace.step_id].append(trace)
    
    # Find steps with rejections
    gates = []
    for step_id, step_traces in by_step.items():
        rejections = sum(1 for t in step_traces if t.decision == DecisionOutcome.DROP)
        if rejections > 0:
            rejection_rate = rejections / len(step_traces)
            if rejection_rate > 0.05:  # At least 5% rejection
                gates.append(step_id)
    
    # Sort by step index
    step_indices = {}
    for trace in traces:
        if trace.step_id not in step_indices:
            step_indices[trace.step_id] = trace.step_index
    
    return sorted(gates, key=lambda s: step_indices.get(s, 999))


def analyze_gates(
    traces: List[SensitivityDecisionTrace],
    gate_steps: List[str]
) -> List[Dict]:
    """Analyze each decision gate."""
    gates_data = []
    
    # Group traces by step
    by_step = defaultdict(list)
    for trace in traces:
        by_step[trace.step_id].append(trace)
    
    for step_id in gate_steps:
        step_traces = by_step[step_id]
        if not step_traces:
            continue
        
        # Split into passes and fails
        passes = [t for t in step_traces if t.decision == DecisionOutcome.CONTINUE]
        fails = [t for t in step_traces if t.decision == DecisionOutcome.DROP]
        
        # Get step index
        step_index = step_traces[0].step_index
        
        # Infer signal demanded (from step name/forces)
        signal_demanded = infer_signal_demanded(step_traces[0])
        
        # Analyze persona characteristics
        passing_chars = analyze_persona_characteristics(passes)
        failing_chars = analyze_persona_characteristics(fails)
        
        # Analyze forces
        avg_forces_pass = compute_avg_forces(passes)
        avg_forces_fail = compute_avg_forces(fails)
        
        gate_data = {
            'step_id': step_id,
            'step_index': step_index,
            'signal_demanded': signal_demanded,
            'passes_count': len(passes),
            'fails_count': len(fails),
            'total_count': len(step_traces),
            'pass_rate': len(passes) / len(step_traces) if step_traces else 0.0,
            'passing_persona_characteristics': passing_chars,
            'failing_persona_characteristics': failing_chars,
            'avg_forces_pass': avg_forces_pass,
            'avg_forces_fail': avg_forces_fail
        }
        
        gates_data.append(gate_data)
    
    return gates_data


def infer_signal_demanded(trace: SensitivityDecisionTrace) -> str:
    """Infer what signal the step is demanding from step_id."""
    step_id = trace.step_id.lower()
    
    # Map based on common patterns in Credigo flow
    if 'step_0' in step_id or ('landing' in step_id and 'best' in step_id):
        return "Initial commitment to proceed"
    elif 'perks' in step_id or ('step_1' in step_id and 'preference' in step_id):
        return "Preference articulation (what you value)"
    elif 'fee' in step_id or ('step_2' in step_id and 'annual' in step_id):
        return "Price sensitivity signal"
    elif 'spend' in step_id or 'spending' in step_id or ('step_4' in step_id or 'step_5' in step_id or 'step_6' in step_id):
        return "Personal financial information"
    elif 'existing' in step_id or 'cards' in step_id or 'step_7' in step_id:
        return "Current product context"
    elif 'personal' in step_id or 'personalise' in step_id or 'step_8' in step_id:
        return "Willingness to share for personalization"
    elif 'deal' in step_id or 'recommendation' in step_id or ('step_10' in step_id or 'step_9' in step_id):
        return "Acceptance of recommendation"
    else:
        return "Signal at this step"


def analyze_persona_characteristics(traces: List[SensitivityDecisionTrace]) -> Dict[str, float]:
    """Analyze characteristics of personas in this group."""
    if not traces:
        return {}
    
    # Group by energy, risk tolerance, effort tolerance
    energy_levels = []
    risk_levels = []
    effort_levels = []
    intent_levels = []
    
    for trace in traces:
        state = trace.state_before
        energy_levels.append(state.cognitive_energy)
        risk_levels.append(state.risk_tolerance)
        effort_levels.append(state.effort_tolerance)
        intent_levels.append(state.intent_strength)
    
    return {
        'avg_cognitive_energy': sum(energy_levels) / len(energy_levels) if energy_levels else 0.0,
        'avg_risk_tolerance': sum(risk_levels) / len(risk_levels) if risk_levels else 0.0,
        'avg_effort_tolerance': sum(effort_levels) / len(effort_levels) if effort_levels else 0.0,
        'avg_intent_strength': sum(intent_levels) / len(intent_levels) if intent_levels else 0.0
    }


def compute_avg_forces(traces: List[SensitivityDecisionTrace]) -> Dict[str, float]:
    """Compute average forces for this group."""
    if not traces:
        return {}
    
    forces_sum = defaultdict(float)
    for trace in traces:
        forces = trace.forces_applied
        forces_sum['effort'] += forces.effort
        forces_sum['risk'] += forces.risk
        forces_sum['value'] += forces.value
        forces_sum['trust'] += forces.trust
        forces_sum['intent_mismatch'] += forces.intent_mismatch
    
    n = len(traces)
    return {
        force_name: forces_sum[force_name] / n
        for force_name in ['effort', 'risk', 'value', 'trust', 'intent_mismatch']
    }


def infer_user_contract(
    traces: List[SensitivityDecisionTrace],
    gate_analysis: List[Dict]
) -> List[str]:
    """Infer the implicit user contract from survival patterns."""
    contract = []
    
    # Find personas that completed all steps
    by_persona = defaultdict(list)
    for trace in traces:
        by_persona[trace.persona_id].append(trace)
    
    completers = []
    for persona_id, persona_traces in by_persona.items():
        # Check if completed (last trace is CONTINUE and reached last step)
        if persona_traces:
            last_trace = max(persona_traces, key=lambda t: t.step_index)
            if last_trace.decision == DecisionOutcome.CONTINUE:
                completers.extend(persona_traces)
    
    if completers:
        completer_chars = analyze_persona_characteristics(completers)
        
        # Generate contract statements
        if completer_chars['avg_intent_strength'] > 0.7:
            contract.append("has high intent strength (already committed to getting a recommendation)")
        
        if completer_chars['avg_effort_tolerance'] > 0.6:
            contract.append("is willing to tolerate effort (will answer multiple questions)")
        
        if completer_chars['avg_risk_tolerance'] > 0.5:
            contract.append("is willing to share personal financial information")
        
        if completer_chars['avg_cognitive_energy'] > 0.6:
            contract.append("has sufficient cognitive energy to complete the flow")
    
    # Analyze first gate (who gets filtered immediately)
    if gate_analysis:
        first_gate = gate_analysis[0]
        failing_chars = first_gate['failing_persona_characteristics']
        
        if failing_chars.get('avg_intent_strength', 1.0) < 0.6:
            contract.append("does not need education or convincing before starting")
        
        if failing_chars.get('avg_risk_tolerance', 1.0) < 0.4:
            contract.append("does not require reassurance before sharing information")
    
    return contract


def analyze_filtering_patterns(
    traces: List[SensitivityDecisionTrace],
    gate_analysis: List[Dict]
) -> Dict:
    """Analyze what Credigo filters out and why."""
    patterns = {
        'intolerances': [],
        'optimizations': [],
        'refusals': []
    }
    
    # Analyze first gate (early filtering)
    if gate_analysis:
        first_gate = gate_analysis[0]
        failing_chars = first_gate['failing_persona_characteristics']
        failing_forces = first_gate['avg_forces_fail']
        
        # What uncertainty is rejected
        if failing_chars.get('avg_intent_strength', 1.0) < 0.5:
            patterns['intolerances'].append({
                'type': 'uncertainty_about_intent',
                'description': 'Users who are uncertain whether they want a recommendation',
                'evidence': f"{first_gate['fails_count']} users filtered at {first_gate['step_id']} with avg intent strength {failing_chars.get('avg_intent_strength', 0):.2f}"
            })
        
        # What hesitation is rejected
        if failing_forces.get('risk', 0) > 0.3:
            patterns['intolerances'].append({
                'type': 'risk_hesitation',
                'description': 'Users who hesitate due to perceived risk',
                'evidence': f"Avg risk force for failures: {failing_forces.get('risk', 0):.2f}"
            })
        
        # What motivation is rewarded
        passing_chars = first_gate['passing_persona_characteristics']
        if passing_chars.get('avg_intent_strength', 0) > 0.7:
            patterns['optimizations'].append({
                'type': 'high_intent_users',
                'description': 'Users who are already committed to getting a recommendation',
                'evidence': f"{first_gate['passes_count']} users passed with avg intent strength {passing_chars.get('avg_intent_strength', 0):.2f}"
            })
    
    return patterns


def extract_tradeoffs(
    traces: List[SensitivityDecisionTrace],
    gate_analysis: List[Dict]
) -> List[Dict]:
    """Extract explicit tradeoffs for each major gate."""
    tradeoffs = []
    
    for gate in gate_analysis[:5]:  # Top 5 gates
        # What does Credigo gain by making this decision early?
        gains = []
        
        if gate['step_index'] == 0:
            gains.append("Filters out low-intent users immediately, saving computational resources")
            gains.append("Ensures remaining users are committed to the process")
        
        elif 'spend' in gate['signal_demanded'].lower() or 'financial' in gate['signal_demanded'].lower() or gate['step_index'] == 4:
            gains.append("Gets detailed personalization data early, enabling better recommendations")
            gains.append("Commits users who have already shared sensitive information")
        
        # What does Credigo lose?
        losses = []
        loss_count = gate['fails_count']
        loss_rate = 1.0 - gate['pass_rate']
        
        if gate['step_index'] == 0:
            losses.append(f"Permanently loses {loss_count} users ({loss_rate:.1%}) who might convert with more education")
            losses.append("Cannot recover users who need convincing before starting")
        
        elif 'spend' in gate['signal_demanded'].lower() or 'financial' in gate['signal_demanded'].lower() or gate['step_index'] == 4:
            losses.append(f"Permanently loses {loss_count} users ({loss_rate:.1%}) who would share info after seeing value")
            losses.append("Cannot convert users who need value demonstration before commitment")
        
        tradeoffs.append({
            'decision': f"Ask for {gate['signal_demanded']} at {gate['step_id']} (step {gate['step_index']})",
            'gains': gains,
            'losses': losses,
            'evidence': {
                'passes': gate['passes_count'],
                'fails': gate['fails_count'],
                'pass_rate': gate['pass_rate']
            }
        })
    
    return tradeoffs


if __name__ == '__main__':
    import sys
    
    ledger_file = sys.argv[1] if len(sys.argv) > 1 else 'credigo_benchmark_decision_ledger.json'
    
    analysis = analyze_credigo_decision_system(ledger_file)
    
    # Save analysis
    output_file = 'credigo_decision_system_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"✓ Analysis saved to {output_file}")


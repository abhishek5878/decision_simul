"""
dropsim_interpreter.py - Reasoning & Abstraction Layer for DropSim

Transforms raw findings (drop rates, deltas, step metrics) into structural explanations.
Answers:
- What is fundamentally broken?
- Why is it breaking?
- What kind of product change would fix it?
- Is this a local issue or a systemic one?

This layer does not run simulations. It interprets their results.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict


# ============================================================================
# Failure Mode Taxonomy
# ============================================================================

FAILURE_MODES = [
    "Cognitive Overload",
    "Unclear Value Proposition",
    "Perceived Risk Too High",
    "Excessive Effort",
    "Motivation Mismatch",
    "Premature Commitment",
    "Information Overload"
]

FAILURE_MODE_DESCRIPTIONS = {
    "Cognitive Overload": "Users are overwhelmed by too many decisions or complex information",
    "Unclear Value Proposition": "Users don't understand what they're getting or why they should continue",
    "Perceived Risk Too High": "Users feel the action is too risky or irreversible",
    "Excessive Effort": "Users perceive the required effort as too high relative to value",
    "Motivation Mismatch": "Users lack sufficient motivation to overcome barriers",
    "Premature Commitment": "Users are asked to commit before value is established",
    "Information Overload": "Users are presented with too much information at once"
}


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class FailureAttribution:
    """Attribution of a failure mode to a step."""
    step_id: str
    dominant_failure_mode: str
    confidence: float  # [0, 1]
    supporting_signals: List[str]
    contributing_factors: List[str]  # Other factors that contribute
    behavioral_cause: str  # Human-readable explanation
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'step_id': self.step_id,
            'dominant_failure_mode': self.dominant_failure_mode,
            'confidence': self.confidence,
            'supporting_signals': self.supporting_signals,
            'contributing_factors': self.contributing_factors,
            'behavioral_cause': self.behavioral_cause
        }


@dataclass
class StructuralPattern:
    """A structural pattern detected across the product flow."""
    pattern_name: str
    evidence: List[str]  # Step IDs or transitions that show this pattern
    impact: str  # Human-readable impact description
    recommended_direction: str  # What kind of change would fix it
    confidence: float  # [0, 1]
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'pattern_name': self.pattern_name,
            'evidence': self.evidence,
            'impact': self.impact,
            'recommended_direction': self.recommended_direction,
            'confidence': self.confidence
        }


@dataclass
class InterpretationReport:
    """Complete interpretation report."""
    root_causes: List[FailureAttribution]
    dominant_patterns: List[StructuralPattern]
    behavioral_summary: str
    recommended_design_shifts: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'root_causes': [rc.to_dict() for rc in self.root_causes],
            'dominant_patterns': [dp.to_dict() for dp in self.dominant_patterns],
            'behavioral_summary': self.behavioral_summary,
            'recommended_design_shifts': self.recommended_design_shifts
        }


# ============================================================================
# Failure Attribution Engine
# ============================================================================

def analyze_step_signals(
    step_id: str,
    context_graph: Dict,
    calibration: Optional[Dict] = None,
    counterfactuals: Optional[Dict] = None
) -> Dict:
    """
    Analyze signals for a specific step.
    
    Returns:
        Dict with signal values
    """
    signals = {
        'drop_rate': 0.0,
        'cognitive_energy_delta': 0.0,
        'risk_delta': 0.0,
        'effort_delta': 0.0,
        'value_delta': 0.0,
        'control_delta': 0.0,
        'step_position': None,
        'dominant_failure_factor': None,
        'total_entries': 0
    }
    
    # Get from context graph
    nodes = context_graph.get('nodes', [])
    for node in nodes:
        if isinstance(node, dict) and node.get('step_id') == step_id:
            signals['drop_rate'] = node.get('drop_rate', 0.0)
            signals['total_entries'] = node.get('total_entries', 0)
            signals['dominant_failure_factor'] = node.get('dominant_failure_factor', '')
            
            # Get average state values
            signals['cognitive_energy_delta'] = -node.get('avg_cognitive_energy', 0.0) * 0.1  # Estimate
            signals['risk_delta'] = node.get('avg_perceived_risk', 0.0) * 0.1
            signals['effort_delta'] = node.get('avg_perceived_effort', 0.0) * 0.1
            signals['value_delta'] = node.get('avg_perceived_value', 0.0) * 0.1
            signals['control_delta'] = node.get('avg_perceived_control', 0.0) * 0.1
            break
    
    # Get step position
    step_names = list(context_graph.get('nodes', []))
    if isinstance(step_names[0], dict):
        step_names = [n.get('step_id') for n in step_names if isinstance(n, dict)]
    if step_id in step_names:
        signals['step_position'] = step_names.index(step_id)
    
    # Get from edges (transitions)
    edges = context_graph.get('edges', [])
    for edge in edges:
        if isinstance(edge, dict):
            # Try different edge formats
            to_step = edge.get('to_step')
            if not to_step:
                # Try edge_key format "from->to"
                edge_key = edge.get('edge_key', '')
                if '->' in str(edge_key):
                    to_step = str(edge_key).split('->')[-1]
            
            if to_step == step_id:
                signals['cognitive_energy_delta'] = edge.get('avg_energy_delta', edge.get('avg_energy_delta', signals['cognitive_energy_delta']))
                signals['risk_delta'] = edge.get('avg_risk_delta', signals['risk_delta'])
                signals['effort_delta'] = edge.get('avg_effort_delta', signals['effort_delta'])
                signals['value_delta'] = edge.get('avg_value_delta', signals['value_delta'])
                signals['control_delta'] = edge.get('avg_control_delta', signals['control_delta'])
                break
    
    return signals


def map_signals_to_failure_mode(signals: Dict) -> Tuple[str, float, List[str]]:
    """
    Map step signals to a failure mode.
    
    Returns:
        (failure_mode, confidence, supporting_signals)
    """
    drop_rate = signals.get('drop_rate', 0.0)
    step_position = signals.get('step_position', 999)
    cognitive_delta = signals.get('cognitive_energy_delta', 0.0)
    risk_delta = signals.get('risk_delta', 0.0)
    effort_delta = signals.get('effort_delta', 0.0)
    value_delta = signals.get('value_delta', 0.0)
    control_delta = signals.get('control_delta', 0.0)
    dominant_factor = signals.get('dominant_failure_factor', '').lower()
    
    # Score each failure mode
    scores = {}
    supporting = {}
    
    # Cognitive Overload
    cognitive_score = 0.0
    cognitive_signals = []
    if cognitive_delta < -0.1:  # High cognitive cost
        cognitive_score += 0.4
        cognitive_signals.append(f"High cognitive energy loss ({cognitive_delta:.2f})")
    if 'fatigue' in dominant_factor:
        cognitive_score += 0.3
        cognitive_signals.append("System 2 fatigue detected")
    if drop_rate > 0.3 and step_position < 5:  # Early high drop
        cognitive_score += 0.2
        cognitive_signals.append("Early funnel cognitive overload")
    scores["Cognitive Overload"] = min(1.0, cognitive_score)
    supporting["Cognitive Overload"] = cognitive_signals
    
    # Perceived Risk Too High
    risk_score = 0.0
    risk_signals = []
    if risk_delta > 0.1:
        risk_score += 0.4
        risk_signals.append(f"High risk perception increase ({risk_delta:.2f})")
    if 'risk' in dominant_factor or 'loss' in dominant_factor:
        risk_score += 0.3
        risk_signals.append("Loss aversion triggered")
    if step_position < 3 and drop_rate > 0.2:  # Early commitment
        risk_score += 0.2
        risk_signals.append("Premature risk exposure")
    scores["Perceived Risk Too High"] = min(1.0, risk_score)
    supporting["Perceived Risk Too High"] = risk_signals
    
    # Excessive Effort
    effort_score = 0.0
    effort_signals = []
    if effort_delta > 0.1:
        effort_score += 0.4
        effort_signals.append(f"High effort perception ({effort_delta:.2f})")
    if 'effort' in dominant_factor:
        effort_score += 0.3
        effort_signals.append("Effort barrier detected")
    if drop_rate > 0.2:
        effort_score += 0.2
        effort_signals.append("High abandonment rate")
    scores["Excessive Effort"] = min(1.0, effort_score)
    supporting["Excessive Effort"] = effort_signals
    
    # Unclear Value Proposition
    value_score = 0.0
    value_signals = []
    if value_delta < 0.05:  # Low value perception
        value_score += 0.4
        value_signals.append("Low perceived value")
    if step_position < 3 and drop_rate > 0.15:  # Early drop with low value
        value_score += 0.3
        value_signals.append("Value not established before commitment")
    if control_delta < 0.05:  # Low control/trust
        value_score += 0.2
        value_signals.append("Low trust/control perception")
    scores["Unclear Value Proposition"] = min(1.0, value_score)
    supporting["Unclear Value Proposition"] = value_signals
    
    # Premature Commitment
    commitment_score = 0.0
    commitment_signals = []
    if step_position < 3 and drop_rate > 0.2:
        commitment_score += 0.4
        commitment_signals.append("Early funnel high drop rate")
    if risk_delta > 0.1 and value_delta < 0.05:
        commitment_score += 0.3
        commitment_signals.append("Risk before value established")
    if step_position == 1 or step_position == 2:  # Very early
        commitment_score += 0.2
        commitment_signals.append("Commitment gate too early")
    scores["Premature Commitment"] = min(1.0, commitment_score)
    supporting["Premature Commitment"] = commitment_signals
    
    # Motivation Mismatch
    motivation_score = 0.0
    motivation_signals = []
    if drop_rate > 0.3 and value_delta < 0.1:
        motivation_score += 0.4
        motivation_signals.append("High drop despite low value perception")
    if effort_delta > 0.1 and value_delta < 0.05:
        motivation_score += 0.3
        motivation_signals.append("Effort exceeds perceived value")
    scores["Motivation Mismatch"] = min(1.0, motivation_score)
    supporting["Motivation Mismatch"] = motivation_signals
    
    # Information Overload
    info_score = 0.0
    info_signals = []
    if cognitive_delta < -0.15 and step_position < 5:
        info_score += 0.4
        info_signals.append("High cognitive cost early in flow")
    if drop_rate > 0.2 and cognitive_delta < -0.1:
        info_score += 0.3
        info_signals.append("Cognitive overload causing drops")
    scores["Information Overload"] = min(1.0, info_score)
    supporting["Information Overload"] = info_signals
    
    # Find dominant failure mode
    if not scores or max(scores.values()) < 0.3:
        return "Excessive Effort", 0.3, ["High drop rate detected"]
    
    dominant_mode = max(scores.items(), key=lambda x: x[1])
    return dominant_mode[0], dominant_mode[1], supporting.get(dominant_mode[0], [])


def infer_failure_modes(
    context_graph: Dict,
    calibration: Optional[Dict] = None,
    decision_results: Optional[Dict] = None
) -> List[FailureAttribution]:
    """
    Infer failure modes from context graph and other signals.
    
    Args:
        context_graph: Context graph data
        calibration: Optional calibration report
        decision_results: Optional decision engine results
    
    Returns:
        List of FailureAttribution objects
    """
    attributions = []
    
    # Get fragile steps
    fragile_steps = context_graph.get('fragile_transitions', [])
    if not fragile_steps:
        # Fallback: get from nodes
        nodes = context_graph.get('nodes', [])
        fragile_steps = []
        for node in nodes:
            if isinstance(node, dict):
                drop_rate = node.get('drop_rate', 0.0)
                if drop_rate > 0.1:  # High drop rate
                    fragile_steps.append({
                        'step_id': node.get('step_id'),
                        'drop_rate': drop_rate
                    })
    
    # Analyze each fragile step
    for step_info in fragile_steps[:10]:  # Top 10 fragile steps
        step_id = step_info.get('step_id') if isinstance(step_info, dict) else step_info
        if not step_id:
            continue
        
        # Analyze signals
        signals = analyze_step_signals(step_id, context_graph, calibration, decision_results)
        
        # Map to failure mode
        failure_mode, confidence, supporting_signals = map_signals_to_failure_mode(signals)
        
        # Get contributing factors
        contributing = []
        if signals.get('risk_delta', 0) > 0.05:
            contributing.append("Risk perception")
        if signals.get('effort_delta', 0) > 0.05:
            contributing.append("Effort perception")
        if signals.get('cognitive_energy_delta', 0) < -0.05:
            contributing.append("Cognitive fatigue")
        if signals.get('value_delta', 0) < 0.05:
            contributing.append("Low value perception")
        
        # Generate behavioral cause
        behavioral_cause = generate_behavioral_cause(failure_mode, signals, supporting_signals)
        
        attribution = FailureAttribution(
            step_id=step_id,
            dominant_failure_mode=failure_mode,
            confidence=confidence,
            supporting_signals=supporting_signals,
            contributing_factors=contributing,
            behavioral_cause=behavioral_cause
        )
        
        attributions.append(attribution)
    
    return attributions


def generate_behavioral_cause(
    failure_mode: str,
    signals: Dict,
    supporting_signals: List[str]
) -> str:
    """Generate human-readable behavioral cause explanation."""
    step_position = signals.get('step_position', 999)
    drop_rate = signals.get('drop_rate', 0.0)
    
    if failure_mode == "Cognitive Overload":
        if step_position < 3:
            return f"Users are overwhelmed by cognitive demands early in the flow, causing {drop_rate:.0%} to abandon before value is established."
        else:
            return f"Users experience cognitive fatigue at this step, with {drop_rate:.0%} dropping due to decision overload."
    
    elif failure_mode == "Perceived Risk Too High":
        if step_position < 3:
            return f"Users perceive high risk before value is established, triggering loss aversion and causing {drop_rate:.0%} to abandon."
        else:
            return f"Users feel the action is too risky or irreversible, with {drop_rate:.0%} abandoning due to risk perception."
    
    elif failure_mode == "Excessive Effort":
        return f"Users perceive the required effort as too high relative to value, causing {drop_rate:.0%} to abandon."
    
    elif failure_mode == "Unclear Value Proposition":
        if step_position < 3:
            return f"Users don't understand the value proposition before being asked to commit, causing {drop_rate:.0%} to abandon."
        else:
            return f"Users lack clarity on what they're getting, with {drop_rate:.0%} abandoning due to unclear value."
    
    elif failure_mode == "Premature Commitment":
        return f"Users are asked to commit before value is established, triggering loss aversion and causing {drop_rate:.0%} to abandon."
    
    elif failure_mode == "Motivation Mismatch":
        return f"Users lack sufficient motivation to overcome barriers, with {drop_rate:.0%} abandoning when effort exceeds perceived value."
    
    elif failure_mode == "Information Overload":
        return f"Users are presented with too much information at once, causing cognitive overload and {drop_rate:.0%} to abandon."
    
    else:
        return f"Users abandon at this step ({drop_rate:.0%} drop rate) due to {failure_mode.lower()}."


# ============================================================================
# Structural Pattern Detection
# ============================================================================

def detect_structural_patterns(
    context_graph: Dict,
    failure_attributions: List[FailureAttribution],
    counterfactuals: Optional[Dict] = None
) -> List[StructuralPattern]:
    """
    Detect structural patterns across the product flow.
    
    Returns:
        List of StructuralPattern objects
    """
    patterns = []
    
    # Get step information
    nodes = context_graph.get('nodes', [])
    step_names = []
    step_positions = {}
    for i, node in enumerate(nodes):
        if isinstance(node, dict):
            step_id = node.get('step_id')
            if step_id:
                step_names.append(step_id)
                step_positions[step_id] = i
    
    # Pattern 1: Early Commitment Spike
    early_drops = []
    for attr in failure_attributions:
        step_id = attr.step_id
        if step_positions.get(step_id, 999) < 3 and attr.dominant_failure_mode in ["Premature Commitment", "Perceived Risk Too High"]:
            early_drops.append(step_id)
    
    if len(early_drops) >= 2:
        patterns.append(StructuralPattern(
            pattern_name="Early Commitment Spike",
            evidence=early_drops,
            impact="High abandonment in early steps due to premature commitment",
            recommended_direction="Delay commitment until value is demonstrated",
            confidence=0.8 if len(early_drops) >= 3 else 0.6
        ))
    
    # Pattern 2: Cognitive Overload Cluster
    cognitive_steps = []
    for attr in failure_attributions:
        if attr.dominant_failure_mode == "Cognitive Overload":
            cognitive_steps.append(attr.step_id)
    
    if len(cognitive_steps) >= 3:
        patterns.append(StructuralPattern(
            pattern_name="Cognitive Overload Cluster",
            evidence=cognitive_steps,
            impact="Multiple steps causing cognitive fatigue, leading to cumulative abandonment",
            recommended_direction="Simplify flow, reduce decisions per step, break into smaller chunks",
            confidence=0.7
        ))
    
    # Pattern 3: Trust-Before-Value Violation
    trust_value_steps = []
    for attr in failure_attributions:
        step_id = attr.step_id
        pos = step_positions.get(step_id, 999)
        if pos < 3 and attr.dominant_failure_mode in ["Unclear Value Proposition", "Perceived Risk Too High"]:
            trust_value_steps.append(step_id)
    
    if len(trust_value_steps) >= 2:
        patterns.append(StructuralPattern(
            pattern_name="Trust-Before-Value Violation",
            evidence=trust_value_steps,
            impact="Users asked to trust/commit before understanding value",
            recommended_direction="Establish value proposition before asking for commitment or personal information",
            confidence=0.75
        ))
    
    # Pattern 4: Late-Funnel Fatigue
    late_drops = []
    for attr in failure_attributions:
        step_id = attr.step_id
        pos = step_positions.get(step_id, 999)
        if pos >= 5 and attr.dominant_failure_mode == "Cognitive Overload":
            late_drops.append(step_id)
    
    if len(late_drops) >= 2:
        patterns.append(StructuralPattern(
            pattern_name="Late-Funnel Fatigue",
            evidence=late_drops,
            impact="Users experience cognitive fatigue after multiple steps",
            recommended_direction="Reduce cognitive load in later steps, add value reinforcement",
            confidence=0.7
        ))
    
    # Pattern 5: Effort-Value Mismatch
    effort_value_steps = []
    for attr in failure_attributions:
        if attr.dominant_failure_mode in ["Excessive Effort", "Motivation Mismatch"]:
            effort_value_steps.append(attr.step_id)
    
    if len(effort_value_steps) >= 3:
        patterns.append(StructuralPattern(
            pattern_name="Effort-Value Mismatch",
            evidence=effort_value_steps,
            impact="Effort required exceeds perceived value across multiple steps",
            recommended_direction="Reduce effort requirements or increase value signals",
            confidence=0.65
        ))
    
    return patterns


# ============================================================================
# Narrative Synthesis
# ============================================================================

def synthesize_behavioral_narrative(
    failure_attributions: List[FailureAttribution],
    structural_patterns: List[StructuralPattern],
    context_graph: Dict
) -> str:
    """
    Synthesize a human-readable behavioral narrative.
    
    Returns:
        Narrative summary string
    """
    if not failure_attributions:
        return "No significant failure patterns detected."
    
    # Find dominant failure mode
    failure_mode_counts = defaultdict(int)
    for attr in failure_attributions:
        failure_mode_counts[attr.dominant_failure_mode] += 1
    
    dominant_mode = max(failure_mode_counts.items(), key=lambda x: x[1])[0] if failure_mode_counts else None
    
    # Find most fragile step
    fragile_steps = context_graph.get('fragile_transitions', [])
    most_fragile = None
    if fragile_steps:
        most_fragile = fragile_steps[0].get('step_id') if isinstance(fragile_steps[0], dict) else fragile_steps[0]
    
    # Build narrative
    narrative_parts = []
    
    # Opening
    if most_fragile:
        narrative_parts.append(f"Users primarily abandon the flow at '{most_fragile}'")
    else:
        narrative_parts.append("Users abandon the flow at multiple points")
    
    # Dominant failure mode
    if dominant_mode:
        narrative_parts.append(f"due to {dominant_mode.lower()}")
    
    # Structural patterns
    if structural_patterns:
        primary_pattern = structural_patterns[0]
        narrative_parts.append(f". The flow exhibits a '{primary_pattern.pattern_name}' pattern")
        narrative_parts.append(f"where {primary_pattern.impact.lower()}")
    
    # Specific example
    if failure_attributions:
        top_attr = failure_attributions[0]
        narrative_parts.append(f". For example, at '{top_attr.step_id}', {top_attr.behavioral_cause.lower()}")
    
    # Recommendation
    if structural_patterns:
        narrative_parts.append(f". {structural_patterns[0].recommended_direction}")
    
    return " ".join(narrative_parts) + "."


def generate_design_shifts(
    structural_patterns: List[StructuralPattern],
    failure_attributions: List[FailureAttribution]
) -> List[str]:
    """
    Generate recommended design shifts based on patterns and failures.
    
    Returns:
        List of design shift recommendations
    """
    shifts = []
    
    # Analyze patterns
    for pattern in structural_patterns:
        if pattern.pattern_name == "Early Commitment Spike":
            shifts.append("Move commitment gates later in the flow, after value is demonstrated")
        elif pattern.pattern_name == "Cognitive Overload Cluster":
            shifts.append("Break complex steps into smaller, sequential decisions")
        elif pattern.pattern_name == "Trust-Before-Value Violation":
            shifts.append("Establish value proposition before requesting personal information or commitment")
        elif pattern.pattern_name == "Late-Funnel Fatigue":
            shifts.append("Reduce cognitive load in later steps and reinforce value")
        elif pattern.pattern_name == "Effort-Value Mismatch":
            shifts.append("Reduce effort requirements or increase value signals throughout the flow")
    
    # Analyze failure modes
    failure_modes = set(attr.dominant_failure_mode for attr in failure_attributions)
    
    if "Perceived Risk Too High" in failure_modes:
        shifts.append("Add trust signals, reduce perceived irreversibility, provide escape hatches")
    
    if "Unclear Value Proposition" in failure_modes:
        shifts.append("Clarify value proposition earlier, use concrete examples, show immediate benefits")
    
    if "Cognitive Overload" in failure_modes or "Information Overload" in failure_modes:
        shifts.append("Simplify information architecture, reduce choices per step, use progressive disclosure")
    
    if "Excessive Effort" in failure_modes:
        shifts.append("Reduce form fields, simplify inputs, provide defaults, enable autofill")
    
    # Remove duplicates while preserving order
    seen = set()
    unique_shifts = []
    for shift in shifts:
        if shift not in seen:
            seen.add(shift)
            unique_shifts.append(shift)
    
    return unique_shifts[:5]  # Top 5


# ============================================================================
# Main Interpretation Function
# ============================================================================

def interpret_results(
    context_graph: Dict,
    calibration: Optional[Dict] = None,
    counterfactuals: Optional[Dict] = None,
    decision_results: Optional[Dict] = None
) -> InterpretationReport:
    """
    Main interpretation function that converts raw findings into insights.
    
    Args:
        context_graph: Context graph data
        calibration: Optional calibration report
        counterfactuals: Optional counterfactual analysis
        decision_results: Optional decision engine results
    
    Returns:
        InterpretationReport with root causes, patterns, and recommendations
    """
    # Infer failure modes
    root_causes = infer_failure_modes(context_graph, calibration, decision_results)
    
    # Detect structural patterns
    dominant_patterns = detect_structural_patterns(context_graph, root_causes, counterfactuals)
    
    # Synthesize narrative
    behavioral_summary = synthesize_behavioral_narrative(root_causes, dominant_patterns, context_graph)
    
    # Generate design shifts
    recommended_design_shifts = generate_design_shifts(dominant_patterns, root_causes)
    
    return InterpretationReport(
        root_causes=root_causes,
        dominant_patterns=dominant_patterns,
        behavioral_summary=behavioral_summary,
        recommended_design_shifts=recommended_design_shifts
    )


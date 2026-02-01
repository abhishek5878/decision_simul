"""
dropsim_decision_engine.py - Decision Engine for DropSim

Converts calibrated insights into actionable, ranked recommendations.
Answers: "Given what we now know, what should the product team change first — and why?"

This is a reasoned decision layer, not a recommender model.
Fully deterministic, explainable, and traceable.
"""

from typing import Dict, List, Optional, Tuple, Literal
from dataclasses import dataclass
import math


# ============================================================================
# Decision Candidate Definition
# ============================================================================

@dataclass
class DecisionCandidate:
    """A single recommended action with full reasoning."""
    action_id: str
    target_step: str
    change_type: Literal[
        "reduce_effort",
        "increase_value",
        "reduce_risk",
        "increase_trust",
        "reduce_cognitive",
        "reorder_steps",
        "remove_step"
    ]
    estimated_impact: float  # Expected drop reduction (0-1)
    confidence: float  # Confidence in recommendation [0, 1]
    rationale: List[str]  # Explanation of why this action
    evidence: List[str]  # Supporting evidence points
    tradeoffs: List[str]  # Potential downsides or considerations
    affected_users: Optional[int] = None  # Number of users affected
    implementation_complexity: float = 1.0  # Relative complexity [0.1, 10.0]
    priority_score: float = 0.0  # Computed: (impact × confidence) / complexity
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'action_id': self.action_id,
            'target_step': self.target_step,
            'change_type': self.change_type,
            'estimated_impact': self.estimated_impact,
            'expected_impact_pct': f"+{self.estimated_impact * 100:.1f}% completion",
            'confidence': self.confidence,
            'rationale': self.rationale,
            'evidence': self.evidence,
            'tradeoffs': self.tradeoffs,
            'affected_users': self.affected_users,
            'implementation_complexity': self.implementation_complexity,
            'priority_score': self.priority_score
        }


@dataclass
class DecisionReport:
    """Complete decision report with ranked recommendations."""
    recommended_actions: List[DecisionCandidate]
    overall_confidence: float
    total_actions_evaluated: int
    top_impact_opportunity: Optional[str]  # Step with highest potential impact
    summary: str  # High-level summary
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'recommended_actions': [action.to_dict() for action in self.recommended_actions],
            'overall_confidence': self.overall_confidence,
            'total_actions_evaluated': self.total_actions_evaluated,
            'top_impact_opportunity': self.top_impact_opportunity,
            'summary': self.summary
        }


# ============================================================================
# Decision Generation Logic
# ============================================================================

def identify_levers_from_calibration(
    calibration_report: Dict,
    context_graph: Optional[Dict] = None
) -> List[Dict]:
    """
    Identify actionable levers from calibration results.
    
    Args:
        calibration_report: Calibration report with bias summary
        context_graph: Optional context graph for step-level analysis
    
    Returns:
        List of lever specifications
    """
    levers = []
    
    bias_summary = calibration_report.get('bias_summary', {})
    step_metrics = calibration_report.get('step_metrics', [])
    
    # Analyze each step for potential levers
    for metric in step_metrics:
        step_id = metric.get('step_id')
        predicted = metric.get('predicted_drop_rate', 0.0)
        observed = metric.get('observed_drop_rate', 0.0)
        error = metric.get('absolute_error', 0.0)
        direction = metric.get('error_direction', 'accurate')
        
        # Skip if accurate (within 2%)
        if error < 0.02:
            continue
        
        # High drop rate → potential for improvement
        if predicted > 0.1 or observed > 0.1:
            # Check if we're overestimating (model thinks it's worse than reality)
            if direction == 'overestimate' and predicted > observed:
                # Reality is better → can reduce effort/risk
                levers.append({
                    'step_id': step_id,
                    'type': 'reduce_effort',
                    'priority': error * predicted,  # Higher error + higher drop = higher priority
                    'reason': f'Model overestimates drop rate ({predicted:.1%} vs {observed:.1%})'
                })
                levers.append({
                    'step_id': step_id,
                    'type': 'reduce_risk',
                    'priority': error * predicted * 0.8,
                    'reason': f'Model overestimates drop rate ({predicted:.1%} vs {observed:.1%})'
                })
            
            # Check if we're underestimating (reality is worse than model)
            elif direction == 'underestimate' and observed > predicted:
                # Reality is worse → need to reduce effort/risk more aggressively
                levers.append({
                    'step_id': step_id,
                    'type': 'reduce_effort',
                    'priority': error * observed * 1.2,  # Higher priority for underestimation
                    'reason': f'Model underestimates drop rate ({predicted:.1%} vs {observed:.1%})'
                })
                levers.append({
                    'step_id': step_id,
                    'type': 'reduce_risk',
                    'priority': error * observed * 1.0,
                    'reason': f'Model underestimates drop rate ({predicted:.1%} vs {observed:.1%})'
                })
                levers.append({
                    'step_id': step_id,
                    'type': 'increase_value',
                    'priority': error * observed * 0.6,
                    'reason': f'Model underestimates drop rate ({predicted:.1%} vs {observed:.1%})'
                })
    
    # Analyze bias summary for systematic levers
    fatigue_bias = bias_summary.get('fatigue_bias', 0.0)
    effort_bias = bias_summary.get('effort_bias', 0.0)
    risk_bias = bias_summary.get('risk_bias', 0.0)
    trust_bias = bias_summary.get('trust_bias', 0.0)
    
    # If fatigue is overestimated (negative bias), we can reduce cognitive load
    if fatigue_bias < -0.05:
        levers.append({
            'step_id': 'all_high_cognitive_steps',
            'type': 'reduce_cognitive',
            'priority': abs(fatigue_bias) * 0.5,
            'reason': f'Systematic overestimation of fatigue (bias: {fatigue_bias:.3f})'
        })
    
    # If effort is underestimated (positive bias), we need to reduce effort more
    if effort_bias > 0.05:
        levers.append({
            'step_id': 'all_high_effort_steps',
            'type': 'reduce_effort',
            'priority': effort_bias * 0.5,
            'reason': f'Systematic underestimation of effort (bias: {effort_bias:.3f})'
        })
    
    # If risk is underestimated, we need to reduce risk more
    if risk_bias > 0.05:
        levers.append({
            'step_id': 'all_high_risk_steps',
            'type': 'reduce_risk',
            'priority': risk_bias * 0.5,
            'reason': f'Systematic underestimation of risk (bias: {risk_bias:.3f})'
        })
    
    # If trust is overestimated, we need to increase trust signals
    if trust_bias < -0.05:
        levers.append({
            'step_id': 'all_low_trust_steps',
            'type': 'increase_trust',
            'priority': abs(trust_bias) * 0.5,
            'reason': f'Systematic overestimation of trust (bias: {trust_bias:.3f})'
        })
    
    return levers


def estimate_impact_from_counterfactuals(
    step_id: str,
    change_type: str,
    counterfactuals: Dict,
    context_graph: Optional[Dict] = None
) -> Tuple[float, List[str]]:
    """
    Estimate impact of a change using counterfactual results.
    
    Args:
        step_id: Target step
        change_type: Type of change
        counterfactuals: Counterfactual analysis results
        context_graph: Optional context graph
    
    Returns:
        (estimated_impact, evidence_list)
    """
    impact = 0.0
    evidence = []
    
    # Look for relevant counterfactuals
    top_interventions = counterfactuals.get('top_interventions', [])
    
    for intervention in top_interventions:
        interv = intervention.get('intervention', {})
        if interv.get('type') != 'step_modification':
            continue
        
        target_step = interv.get('step_id')
        if target_step != step_id:
            continue
        
        delta = interv.get('delta', {})
        
        # Match change type
        if change_type == 'reduce_effort' and 'effort' in delta and delta['effort'] < 0:
            outcome_change_rate = intervention.get('outcome_change_rate', 0.0)
            impact = max(impact, outcome_change_rate)
            evidence.append(f"Counterfactual: reducing effort by {abs(delta['effort']):.2f} → {outcome_change_rate:.1%} outcome change rate")
        
        elif change_type == 'reduce_risk' and 'risk' in delta and delta['risk'] < 0:
            outcome_change_rate = intervention.get('outcome_change_rate', 0.0)
            impact = max(impact, outcome_change_rate)
            evidence.append(f"Counterfactual: reducing risk by {abs(delta['risk']):.2f} → {outcome_change_rate:.1%} outcome change rate")
        
        elif change_type == 'reduce_cognitive' and 'cognitive' in delta and delta['cognitive'] < 0:
            outcome_change_rate = intervention.get('outcome_change_rate', 0.0)
            impact = max(impact, outcome_change_rate)
            evidence.append(f"Counterfactual: reducing cognitive demand by {abs(delta['cognitive']):.2f} → {outcome_change_rate:.1%} outcome change rate")
        
        elif change_type == 'increase_value' and 'value' in delta and delta['value'] > 0:
            outcome_change_rate = intervention.get('outcome_change_rate', 0.0)
            impact = max(impact, outcome_change_rate)
            evidence.append(f"Counterfactual: increasing value by {delta['value']:.2f} → {outcome_change_rate:.1%} outcome change rate")
        
        elif change_type == 'increase_trust' and 'reassurance' in delta and delta['reassurance'] > 0:
            outcome_change_rate = intervention.get('outcome_change_rate', 0.0)
            impact = max(impact, outcome_change_rate)
            evidence.append(f"Counterfactual: increasing reassurance by {delta['reassurance']:.2f} → {outcome_change_rate:.1%} outcome change rate")
    
    # If no counterfactual found, use sensitivity map
    if impact == 0.0:
        sensitivity_map = counterfactuals.get('sensitivity_map', {})
        most_sensitive = sensitivity_map.get('most_sensitive', '')
        
        if change_type == 'reduce_effort' and most_sensitive == 'effort':
            impact = sensitivity_map.get('effort_sensitivity', 0.0) * 0.3  # Conservative estimate
            evidence.append(f"Sensitivity analysis: effort is most sensitive variable")
        elif change_type == 'reduce_risk' and most_sensitive == 'risk':
            impact = sensitivity_map.get('risk_sensitivity', 0.0) * 0.3
            evidence.append(f"Sensitivity analysis: risk is most sensitive variable")
        elif change_type == 'reduce_cognitive' and most_sensitive == 'cognitive':
            impact = sensitivity_map.get('cognitive_sensitivity', 0.0) * 0.3
            evidence.append(f"Sensitivity analysis: cognitive is most sensitive variable")
    
    return impact, evidence


def compute_confidence(
    calibration_report: Dict,
    counterfactuals: Dict,
    step_id: str,
    change_type: str
) -> float:
    """
    Compute confidence in a recommendation.
    
    Based on:
    - Calibration stability
    - Sensitivity strength
    - Variance across personas
    
    Returns:
        Confidence score [0, 1]
    """
    confidence = 0.5  # Base confidence
    
    # Calibration stability
    stability_score = calibration_report.get('stability_score', 0.5)
    confidence += stability_score * 0.3
    
    # Calibration score
    calibration_score = calibration_report.get('calibration_score', 0.5)
    confidence += calibration_score * 0.2
    
    # Counterfactual confidence
    top_interventions = counterfactuals.get('top_interventions', [])
    for intervention in top_interventions:
        interv = intervention.get('intervention', {})
        if interv.get('step_id') == step_id:
            avg_sensitivity = intervention.get('avg_sensitivity', 0.0) / 3.0  # Normalize to [0, 1]
            confidence += avg_sensitivity * 0.2
    
    # Robustness score
    robustness_score = counterfactuals.get('robustness_score', 0.5)
    confidence += robustness_score * 0.3
    
    return min(1.0, max(0.0, confidence))


def estimate_affected_users(
    step_id: str,
    context_graph: Optional[Dict] = None
) -> int:
    """Estimate number of users affected by a change."""
    if not context_graph:
        return 0
    
    nodes = context_graph.get('nodes', [])
    for node in nodes:
        if isinstance(node, dict) and node.get('step_id') == step_id:
            return node.get('total_entries', 0)
        elif hasattr(node, 'step_id') and node.step_id == step_id:
            return node.total_entries if hasattr(node, 'total_entries') else 0
    
    return 0


def get_implementation_complexity(change_type: str) -> float:
    """
    Estimate implementation complexity.
    
    Lower = easier to implement
    """
    complexity_map = {
        'reduce_effort': 1.0,  # Easy: simplify UI, reduce fields
        'reduce_risk': 1.5,  # Medium: add reassurances, reduce friction
        'reduce_cognitive': 2.0,  # Medium: simplify flow, reduce decisions
        'increase_value': 2.5,  # Medium-Hard: add value props, messaging
        'increase_trust': 1.5,  # Medium: add trust signals, badges
        'reorder_steps': 3.0,  # Hard: requires flow redesign
        'remove_step': 4.0  # Very Hard: requires product changes
    }
    
    return complexity_map.get(change_type, 2.0)


def generate_decision_candidates(
    calibration_report: Dict,
    counterfactuals: Dict,
    context_graph: Optional[Dict] = None,
    top_n: int = 5
) -> List[DecisionCandidate]:
    """
    Generate ranked decision candidates from analysis.
    
    Args:
        calibration_report: Calibration report
        counterfactuals: Counterfactual analysis results
        context_graph: Optional context graph
        top_n: Number of top recommendations to return
    
    Returns:
        List of DecisionCandidate objects, ranked by priority
    """
    candidates = []
    
    # Identify levers from calibration
    levers = identify_levers_from_calibration(calibration_report, context_graph)
    
    # If no levers from calibration, generate from context graph and counterfactuals
    if not levers and context_graph:
        # Get fragile steps from context graph
        nodes = context_graph.get('nodes', [])
        for node in nodes:
            if isinstance(node, dict):
                step_id = node.get('step_id')
                drop_rate = node.get('drop_rate', 0.0)
                if drop_rate > 0.1:  # High drop rate
                    levers.append({
                        'step_id': step_id,
                        'type': 'reduce_effort',
                        'priority': drop_rate * 0.5,
                        'reason': f'High drop rate ({drop_rate:.1%})'
                    })
                    levers.append({
                        'step_id': step_id,
                        'type': 'reduce_risk',
                        'priority': drop_rate * 0.4,
                        'reason': f'High drop rate ({drop_rate:.1%})'
                    })
    
    # If still no levers, use counterfactuals
    if not levers and counterfactuals:
        top_interventions = counterfactuals.get('top_interventions', [])
        for intervention in top_interventions[:top_n]:
            interv = intervention.get('intervention', {})
            if interv.get('type') == 'step_modification':
                step_id = interv.get('step_id')
                delta = interv.get('delta', {})
                outcome_change_rate = intervention.get('outcome_change_rate', 0.0)
                
                if 'effort' in delta and delta['effort'] < 0:
                    levers.append({
                        'step_id': step_id,
                        'type': 'reduce_effort',
                        'priority': outcome_change_rate,
                        'reason': f'Counterfactual shows {outcome_change_rate:.1%} outcome change rate'
                    })
                elif 'risk' in delta and delta['risk'] < 0:
                    levers.append({
                        'step_id': step_id,
                        'type': 'reduce_risk',
                        'priority': outcome_change_rate,
                        'reason': f'Counterfactual shows {outcome_change_rate:.1%} outcome change rate'
                    })
                elif 'cognitive' in delta and delta['cognitive'] < 0:
                    levers.append({
                        'step_id': step_id,
                        'type': 'reduce_cognitive',
                        'priority': outcome_change_rate,
                        'reason': f'Counterfactual shows {outcome_change_rate:.1%} outcome change rate'
                    })
    
    # Sort by priority
    levers.sort(key=lambda x: x.get('priority', 0.0), reverse=True)
    
    # Generate candidates for top levers
    for lever in levers[:top_n * 2]:  # Generate more, then filter
        step_id = lever.get('step_id')
        change_type = lever.get('type')
        
        # Skip if step_id is a pattern (like 'all_high_effort_steps')
        if step_id.startswith('all_'):
            # Find actual steps matching the pattern
            if context_graph:
                nodes = context_graph.get('nodes', [])
                for node in nodes:
                    if isinstance(node, dict):
                        node_step_id = node.get('step_id')
                        drop_rate = node.get('drop_rate', 0.0)
                        
                        # Match pattern
                        if change_type == 'reduce_effort' and drop_rate > 0.1:
                            step_id = node_step_id
                            break
                        elif change_type == 'reduce_risk' and drop_rate > 0.1:
                            step_id = node_step_id
                            break
                        elif change_type == 'reduce_cognitive' and drop_rate > 0.1:
                            step_id = node_step_id
                            break
            
            if step_id.startswith('all_'):
                continue  # Skip if we couldn't find a specific step
        
        # Estimate impact
        impact, evidence = estimate_impact_from_counterfactuals(
            step_id,
            change_type,
            counterfactuals,
            context_graph
        )
        
        # If no impact found, use lever priority as proxy
        if impact == 0.0:
            impact = min(0.3, lever.get('priority', 0.0))  # Cap at 30%
            evidence.append(f"Calibration analysis: {lever.get('reason', '')}")
        
        # Compute confidence
        confidence = compute_confidence(
            calibration_report,
            counterfactuals,
            step_id,
            change_type
        )
        
        # Estimate affected users
        affected_users = estimate_affected_users(step_id, context_graph)
        
        # Get implementation complexity
        complexity = get_implementation_complexity(change_type)
        
        # Compute priority score
        priority_score = (impact * confidence) / complexity if complexity > 0 else 0.0
        
        # Generate rationale
        rationale = [
            f"Step '{step_id}' shows high drop rate",
            lever.get('reason', ''),
            f"Estimated impact: {impact:.1%} completion improvement"
        ]
        
        # Generate tradeoffs
        tradeoffs = []
        if change_type == 'reduce_effort':
            tradeoffs.append("May reduce data quality if fields are removed")
        elif change_type == 'reduce_risk':
            tradeoffs.append("May require additional trust signals or guarantees")
        elif change_type == 'reduce_cognitive':
            tradeoffs.append("May require simplifying user flow or reducing choices")
        elif change_type == 'increase_value':
            tradeoffs.append("May require product changes or messaging updates")
        elif change_type == 'increase_trust':
            tradeoffs.append("May require adding trust badges or security indicators")
        
        # Create candidate
        candidate = DecisionCandidate(
            action_id=f"{step_id}_{change_type}",
            target_step=step_id,
            change_type=change_type,
            estimated_impact=impact,
            confidence=confidence,
            rationale=rationale,
            evidence=evidence,
            tradeoffs=tradeoffs,
            affected_users=affected_users,
            implementation_complexity=complexity,
            priority_score=priority_score
        )
        
        candidates.append(candidate)
    
    # Rank by priority score
    candidates.sort(key=lambda x: x.priority_score, reverse=True)
    
    # Return top N
    return candidates[:top_n]


# ============================================================================
# Main Decision Engine Function
# ============================================================================

def generate_decision_report(
    calibration_report: Dict,
    counterfactuals: Dict,
    context_graph: Optional[Dict] = None,
    top_n: int = 5
) -> DecisionReport:
    """
    Generate complete decision report with ranked recommendations.
    
    Args:
        calibration_report: Calibration report
        counterfactuals: Counterfactual analysis results
        context_graph: Optional context graph
        top_n: Number of top recommendations
    
    Returns:
        DecisionReport with ranked actions
    """
    # Generate candidates
    candidates = generate_decision_candidates(
        calibration_report,
        counterfactuals,
        context_graph,
        top_n
    )
    
    # Compute overall confidence
    if candidates:
        overall_confidence = sum(c.confidence for c in candidates) / len(candidates)
    else:
        overall_confidence = 0.0
    
    # Find top impact opportunity
    top_impact_opportunity = None
    if candidates:
        top_candidate = candidates[0]
        top_impact_opportunity = f"{top_candidate.target_step} ({top_candidate.change_type})"
    
    # Generate summary
    if candidates:
        summary = f"Generated {len(candidates)} ranked recommendations. "
        summary += f"Top priority: {top_impact_opportunity} with {candidates[0].estimated_impact:.1%} expected impact. "
        summary += f"Overall confidence: {overall_confidence:.1%}."
    else:
        summary = "No actionable recommendations generated. Insufficient data or all steps are well-calibrated."
    
    return DecisionReport(
        recommended_actions=candidates,
        overall_confidence=overall_confidence,
        total_actions_evaluated=len(candidates),
        top_impact_opportunity=top_impact_opportunity,
        summary=summary
    )


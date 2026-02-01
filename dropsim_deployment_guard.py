"""
dropsim_deployment_guard.py - Deployment Validation Layer for DropSim

Ensures recommendations are:
- Safe to deploy
- Measurably effective
- Monitored over time
- Automatically reversible if incorrect

This layer does not change model logic — it governs how decisions are trusted and applied.
This is not experimentation — it is guarded execution.
"""

from typing import Dict, List, Optional, Tuple, Literal
from dataclasses import dataclass
from datetime import datetime
import math


# ============================================================================
# Core Data Structures
# ============================================================================

@dataclass
class DeploymentCandidate:
    """A decision candidate being evaluated for deployment."""
    decision_id: str
    recommended_action: str  # Human-readable action description
    target_step: str
    change_type: str
    estimated_impact: float  # Expected gain (0-1)
    confidence: float  # Confidence in recommendation [0, 1]
    risk_score: float  # Computed risk score [0, 1]
    rollback_threshold: float  # Threshold for automatic rollback
    affected_users: Optional[int] = None
    implementation_complexity: float = 1.0
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'decision_id': self.decision_id,
            'recommended_action': self.recommended_action,
            'target_step': self.target_step,
            'change_type': self.change_type,
            'estimated_impact': self.estimated_impact,
            'confidence': self.confidence,
            'risk_score': self.risk_score,
            'rollback_threshold': self.rollback_threshold,
            'affected_users': self.affected_users,
            'implementation_complexity': self.implementation_complexity
        }


@dataclass
class DeploymentEvaluation:
    """Evaluation result for a deployment candidate."""
    expected_gain: float  # Expected improvement (0-1)
    estimated_risk: float  # Estimated risk [0, 1]
    confidence_interval: Tuple[float, float]  # (lower, upper) confidence bounds
    rollout_recommendation: Literal["safe", "caution", "do_not_deploy"]
    risk_factors: List[str]  # List of risk factors identified
    safety_score: float  # Overall safety score [0, 1]
    reasoning_summary: str  # Human-readable explanation
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'expected_gain': self.expected_gain,
            'estimated_risk': self.estimated_risk,
            'confidence_interval': (self.confidence_interval[0], self.confidence_interval[1]),
            'rollout_recommendation': self.rollout_recommendation,
            'risk_factors': self.risk_factors,
            'safety_score': self.safety_score,
            'reasoning_summary': self.reasoning_summary
        }


@dataclass
class MonitoringPlan:
    """Plan for monitoring post-deployment performance."""
    metrics: List[str]  # Metrics to track
    alert_thresholds: Dict[str, float]  # metric -> threshold
    check_interval_hours: int  # How often to check
    rollback_conditions: List[str]  # Conditions that trigger rollback
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'metrics': self.metrics,
            'alert_thresholds': self.alert_thresholds,
            'check_interval_hours': self.check_interval_hours,
            'rollback_conditions': self.rollback_conditions
        }


@dataclass
class DeploymentReport:
    """Complete deployment validation report."""
    candidate: DeploymentCandidate
    evaluation: DeploymentEvaluation
    monitoring_plan: MonitoringPlan
    shadow_evaluation_result: Optional[Dict] = None  # If shadow mode was run
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'candidate': self.candidate.to_dict(),
            'evaluation': self.evaluation.to_dict(),
            'monitoring_plan': self.monitoring_plan.to_dict(),
            'shadow_evaluation_result': self.shadow_evaluation_result
        }


# ============================================================================
# Pre-Deployment Validation Logic
# ============================================================================

def compute_risk_score(
    candidate: DeploymentCandidate,
    calibration_data: Optional[Dict] = None,
    counterfactuals: Optional[Dict] = None
) -> Tuple[float, List[str]]:
    """
    Compute risk score for a deployment candidate.
    
    Risk factors:
    - High impact but low confidence
    - Low calibration stability
    - High sensitivity to changes
    - Global changes (affecting many steps)
    - Complex implementation
    
    Returns:
        (risk_score, risk_factors)
    """
    risk_score = 0.0
    risk_factors = []
    
    # Factor 1: Confidence vs Impact mismatch
    # High impact with low confidence = risky
    if candidate.estimated_impact > 0.2 and candidate.confidence < 0.7:
        risk_penalty = (0.2 - candidate.confidence) * (candidate.estimated_impact / 0.2)
        risk_score += risk_penalty * 0.3
        risk_factors.append(f"High impact ({candidate.estimated_impact:.1%}) but low confidence ({candidate.confidence:.1%})")
    
    # Factor 2: Calibration stability
    if calibration_data:
        stability_score = calibration_data.get('stability_score', 0.5)
        if stability_score < 0.7:
            risk_penalty = (0.7 - stability_score) / 0.7
            risk_score += risk_penalty * 0.2
            risk_factors.append(f"Low calibration stability ({stability_score:.1%})")
    
    # Factor 3: Counterfactual robustness
    if counterfactuals:
        robustness_score = counterfactuals.get('robustness_score', 0.5)
        if robustness_score < 0.7:
            risk_penalty = (0.7 - robustness_score) / 0.7
            risk_score += risk_penalty * 0.2
            risk_factors.append(f"Low robustness to perturbations ({robustness_score:.1%})")
    
    # Factor 4: Implementation complexity
    # Higher complexity = higher risk
    if candidate.implementation_complexity > 2.0:
        complexity_risk = min(0.3, (candidate.implementation_complexity - 2.0) / 8.0)
        risk_score += complexity_risk
        risk_factors.append(f"High implementation complexity ({candidate.implementation_complexity:.1f})")
    
    # Factor 5: Affected user count
    # More users = higher risk if something goes wrong
    if candidate.affected_users and candidate.affected_users > 1000:
        user_risk = min(0.2, (candidate.affected_users - 1000) / 10000)
        risk_score += user_risk
        if candidate.affected_users > 5000:
            risk_factors.append(f"Large user base affected ({candidate.affected_users:,} users)")
    
    # Factor 6: Change type risk
    # Some change types are riskier than others
    high_risk_changes = ['remove_step', 'reorder_steps']
    if candidate.change_type in high_risk_changes:
        risk_score += 0.2
        risk_factors.append(f"High-risk change type: {candidate.change_type}")
    
    # Clamp to [0, 1]
    risk_score = min(1.0, max(0.0, risk_score))
    
    return risk_score, risk_factors


def compute_confidence_interval(
    estimated_impact: float,
    confidence: float,
    calibration_data: Optional[Dict] = None
) -> Tuple[float, float]:
    """
    Compute confidence interval for estimated impact.
    
    Uses confidence score and calibration stability to estimate bounds.
    """
    # Base uncertainty from confidence
    uncertainty = (1.0 - confidence) * 0.3  # Max 30% uncertainty
    
    # Adjust based on calibration stability
    if calibration_data:
        stability = calibration_data.get('stability_score', 0.5)
        uncertainty *= (2.0 - stability)  # Lower stability = higher uncertainty
    
    lower = max(0.0, estimated_impact - uncertainty)
    upper = min(1.0, estimated_impact + uncertainty)
    
    return (lower, upper)


def evaluate_deployment(
    candidate: DeploymentCandidate,
    calibration_data: Optional[Dict] = None,
    counterfactuals: Optional[Dict] = None
) -> DeploymentEvaluation:
    """
    Evaluate whether a deployment candidate is safe to deploy.
    
    Validation rules:
    - Penalize high-impact but low-confidence changes
    - Reject actions where estimated risk > benefit
    - Downgrade confidence if historical stability is low
    - Prefer changes affecting localized steps over global ones
    
    Args:
        candidate: Deployment candidate to evaluate
        calibration_data: Optional calibration report
        counterfactuals: Optional counterfactual analysis
    
    Returns:
        DeploymentEvaluation with go/no-go recommendation
    """
    # Compute risk score
    risk_score, risk_factors = compute_risk_score(candidate, calibration_data, counterfactuals)
    
    # Compute confidence interval
    confidence_interval = compute_confidence_interval(
        candidate.estimated_impact,
        candidate.confidence,
        calibration_data
    )
    
    # Compute safety score
    # Safety = (1 - risk) * confidence
    safety_score = (1.0 - risk_score) * candidate.confidence
    
    # Determine rollout recommendation
    if risk_score > 0.7 or safety_score < 0.3:
        recommendation = "do_not_deploy"
        reasoning = f"High risk ({risk_score:.1%}) or low safety ({safety_score:.1%}). "
    elif risk_score > 0.4 or safety_score < 0.6:
        recommendation = "caution"
        reasoning = f"Moderate risk ({risk_score:.1%}) or moderate safety ({safety_score:.1%}). "
    else:
        recommendation = "safe"
        reasoning = f"Low risk ({risk_score:.1%}) and high safety ({safety_score:.1%}). "
    
    # Add specific reasoning
    if risk_factors:
        reasoning += f"Risk factors: {', '.join(risk_factors[:3])}. "
    
    if candidate.confidence > 0.8:
        reasoning += "High confidence in recommendation. "
    elif candidate.confidence < 0.6:
        reasoning += "Low confidence - consider additional validation. "
    
    if candidate.estimated_impact > 0.15:
        reasoning += f"Expected gain: {candidate.estimated_impact:.1%}. "
    
    # Check if risk > benefit
    if risk_score > candidate.estimated_impact:
        recommendation = "do_not_deploy"
        reasoning = f"Risk ({risk_score:.1%}) exceeds expected benefit ({candidate.estimated_impact:.1%}). "
    
    return DeploymentEvaluation(
        expected_gain=candidate.estimated_impact,
        estimated_risk=risk_score,
        confidence_interval=confidence_interval,
        rollout_recommendation=recommendation,
        risk_factors=risk_factors,
        safety_score=safety_score,
        reasoning_summary=reasoning
    )


# ============================================================================
# Shadow Evaluation (Dry Run Mode)
# ============================================================================

def run_shadow_evaluation(
    candidate: DeploymentCandidate,
    counterfactuals: Optional[Dict] = None,
    context_graph: Optional[Dict] = None
) -> Dict:
    """
    Run shadow evaluation (dry run) of a deployment candidate.
    
    The change is simulated but not applied.
    Effects are estimated using existing counterfactual logic.
    Results are logged for comparison.
    
    Args:
        candidate: Deployment candidate to evaluate
        counterfactuals: Counterfactual analysis results
        context_graph: Optional context graph
    
    Returns:
        Shadow evaluation results
    """
    # Find matching counterfactual
    shadow_result = {
        'simulated': True,
        'timestamp': datetime.now().isoformat(),
        'candidate_id': candidate.decision_id,
        'estimated_impact': candidate.estimated_impact,
        'confidence': candidate.confidence
    }
    
    # Look for matching counterfactual intervention
    if counterfactuals:
        top_interventions = counterfactuals.get('top_interventions', [])
        for intervention in top_interventions:
            interv = intervention.get('intervention', {})
            if (interv.get('step_id') == candidate.target_step and
                interv.get('type') == 'step_modification'):
                delta = interv.get('delta', {})
                
                # Check if change type matches
                matches = False
                if candidate.change_type == 'reduce_effort' and 'effort' in delta and delta['effort'] < 0:
                    matches = True
                elif candidate.change_type == 'reduce_risk' and 'risk' in delta and delta['risk'] < 0:
                    matches = True
                elif candidate.change_type == 'reduce_cognitive' and 'cognitive' in delta and delta['cognitive'] < 0:
                    matches = True
                elif candidate.change_type == 'increase_value' and 'value' in delta and delta['value'] > 0:
                    matches = True
                elif candidate.change_type == 'increase_trust' and 'reassurance' in delta and delta['reassurance'] > 0:
                    matches = True
                
                if matches:
                    shadow_result['counterfactual_match'] = True
                    shadow_result['outcome_change_rate'] = intervention.get('outcome_change_rate', 0.0)
                    shadow_result['avg_effect_size'] = intervention.get('avg_effect_size', 0.0)
                    shadow_result['avg_sensitivity'] = intervention.get('avg_sensitivity', 0.0)
                    break
        
        if 'counterfactual_match' not in shadow_result:
            shadow_result['counterfactual_match'] = False
            shadow_result['note'] = 'No matching counterfactual found'
    
    # Estimate affected users
    if context_graph:
        nodes = context_graph.get('nodes', [])
        for node in nodes:
            if isinstance(node, dict) and node.get('step_id') == candidate.target_step:
                shadow_result['affected_users'] = node.get('total_entries', 0)
                break
    
    return shadow_result


# ============================================================================
# Monitoring Plan Generation
# ============================================================================

def generate_monitoring_plan(
    candidate: DeploymentCandidate,
    evaluation: DeploymentEvaluation
) -> MonitoringPlan:
    """
    Generate monitoring plan for post-deployment tracking.
    
    Args:
        candidate: Deployment candidate
        evaluation: Deployment evaluation
    
    Returns:
        MonitoringPlan with metrics, thresholds, and rollback conditions
    """
    # Base metrics to track
    metrics = ['drop_rate', 'completion_rate']
    
    # Add step-specific metrics
    if candidate.target_step:
        metrics.append(f'{candidate.target_step}_drop_rate')
        metrics.append(f'{candidate.target_step}_completion_rate')
    
    # Set alert thresholds based on expected gain
    alert_thresholds = {
        'drop_rate': evaluation.expected_gain * 0.5,  # Alert if drop rate doesn't improve by at least 50% of expected
        'completion_rate': evaluation.expected_gain * 0.5  # Alert if completion doesn't improve by at least 50% of expected
    }
    
    # Rollback conditions
    rollback_conditions = []
    
    # If actual performance is worse than baseline
    rollback_conditions.append(f"Drop rate increases by >5%")
    rollback_conditions.append(f"Completion rate decreases by >3%")
    
    # If performance is significantly below expected
    if evaluation.expected_gain > 0.1:
        rollback_conditions.append(f"Actual gain < {evaluation.expected_gain * 0.3:.1%} (30% of expected)")
    
    # If confidence degrades
    rollback_conditions.append(f"Model confidence drops below {candidate.confidence * 0.7:.1%}")
    
    # Check interval based on risk
    if evaluation.estimated_risk > 0.5:
        check_interval_hours = 1  # High risk: check hourly
    elif evaluation.estimated_risk > 0.3:
        check_interval_hours = 6  # Medium risk: check every 6 hours
    else:
        check_interval_hours = 24  # Low risk: check daily
    
    return MonitoringPlan(
        metrics=metrics,
        alert_thresholds=alert_thresholds,
        check_interval_hours=check_interval_hours,
        rollback_conditions=rollback_conditions
    )


# ============================================================================
# Main Deployment Guard Function
# ============================================================================

def evaluate_deployment_candidate(
    decision_candidate: Dict,  # From Decision Engine
    calibration_data: Optional[Dict] = None,
    counterfactuals: Optional[Dict] = None,
    context_graph: Optional[Dict] = None,
    run_shadow: bool = True
) -> DeploymentReport:
    """
    Complete deployment validation for a decision candidate.
    
    Args:
        decision_candidate: Decision candidate from Decision Engine
        calibration_data: Optional calibration report
        counterfactuals: Optional counterfactual analysis
        context_graph: Optional context graph
        run_shadow: Whether to run shadow evaluation
    
    Returns:
        DeploymentReport with complete validation
    """
    # Convert decision candidate to deployment candidate
    candidate = DeploymentCandidate(
        decision_id=decision_candidate.get('action_id', 'unknown'),
        recommended_action=f"{decision_candidate.get('change_type', 'unknown')} at {decision_candidate.get('target_step', 'unknown')}",
        target_step=decision_candidate.get('target_step', ''),
        change_type=decision_candidate.get('change_type', ''),
        estimated_impact=decision_candidate.get('estimated_impact', 0.0),
        confidence=decision_candidate.get('confidence', 0.5),
        risk_score=0.0,  # Will be computed
        rollback_threshold=0.05,  # Default: rollback if drop rate increases by 5%
        affected_users=decision_candidate.get('affected_users'),
        implementation_complexity=decision_candidate.get('implementation_complexity', 1.0)
    )
    
    # Evaluate deployment
    evaluation = evaluate_deployment(candidate, calibration_data, counterfactuals)
    
    # Update candidate with computed risk score
    candidate.risk_score = evaluation.estimated_risk
    
    # Set rollback threshold based on expected gain
    candidate.rollback_threshold = max(0.03, evaluation.expected_gain * 0.3)
    
    # Run shadow evaluation if requested
    shadow_result = None
    if run_shadow:
        shadow_result = run_shadow_evaluation(candidate, counterfactuals, context_graph)
    
    # Generate monitoring plan
    monitoring_plan = generate_monitoring_plan(candidate, evaluation)
    
    return DeploymentReport(
        candidate=candidate,
        evaluation=evaluation,
        monitoring_plan=monitoring_plan,
        shadow_evaluation_result=shadow_result
    )


def validate_all_recommendations(
    decision_report: Dict,
    calibration_data: Optional[Dict] = None,
    counterfactuals: Optional[Dict] = None,
    context_graph: Optional[Dict] = None
) -> List[DeploymentReport]:
    """
    Validate all recommendations from a decision report.
    
    Args:
        decision_report: Decision report from Decision Engine
        calibration_data: Optional calibration report
        counterfactuals: Optional counterfactual analysis
        context_graph: Optional context graph
    
    Returns:
        List of DeploymentReport objects, one per recommendation
    """
    recommendations = decision_report.get('recommended_actions', [])
    deployment_reports = []
    
    for rec in recommendations:
        report = evaluate_deployment_candidate(
            rec,
            calibration_data,
            counterfactuals,
            context_graph,
            run_shadow=True
        )
        deployment_reports.append(report)
    
    return deployment_reports


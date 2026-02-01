"""
dropsim_signal_quality.py - Signal Quality Evaluation for DropSim

Evaluates whether system outputs are:
- Useful and discriminative (not just technically correct)
- Meaningfully different for different inputs
- Not overconfident despite weak evidence
- Decision-worthy

This module does NOT add new modeling layers.
It evaluates epistemic quality of existing outputs.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import math
import statistics


# ============================================================================
# Signal Strength Scoring
# ============================================================================

@dataclass
class SignalStrength:
    """Signal strength assessment for a conclusion."""
    score: float  # [0, 1] - overall signal strength
    consistency: float  # [0, 1] - consistency across simulations
    sensitivity: float  # [0, 1] - sensitivity to perturbation
    evidence_diversity: float  # [0, 1] - diversity of evidence sources
    confidence_band: Tuple[float, float]  # Lower and upper bounds
    reasoning: str  # Explanation of score
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'score': self.score,
            'consistency': self.consistency,
            'sensitivity': self.sensitivity,
            'evidence_diversity': self.evidence_diversity,
            'confidence_band': self.confidence_band,
            'reasoning': self.reasoning
        }


@dataclass
class SignalJudgment:
    """Final judgment on signal quality."""
    classification: str  # "strong_signal", "weak_signal", "inconclusive"
    explanation: str  # Why this classification
    trustworthy_conclusions: List[str]  # What can be trusted
    uncertain_conclusions: List[str]  # What is uncertain
    improvement_suggestions: List[str]  # What would improve confidence
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'classification': self.classification,
            'explanation': self.explanation,
            'trustworthy_conclusions': self.trustworthy_conclusions,
            'uncertain_conclusions': self.uncertain_conclusions,
            'improvement_suggestions': self.improvement_suggestions
        }


@dataclass
class StabilityMetrics:
    """Stability metrics across multiple runs."""
    variance_score: float  # [0, 1] - lower = more stable
    consistency_score: float  # [0, 1] - higher = more consistent
    top_recommendation_stability: float  # [0, 1] - how often same top recommendation
    root_cause_stability: float  # [0, 1] - how consistent root causes are
    instability_flags: List[str]  # Flags for unstable areas
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'variance_score': self.variance_score,
            'consistency_score': self.consistency_score,
            'top_recommendation_stability': self.top_recommendation_stability,
            'root_cause_stability': self.root_cause_stability,
            'instability_flags': self.instability_flags
        }


@dataclass
class ConfidenceCalibration:
    """Confidence calibration assessment."""
    overconfidence_detected: bool
    calibrated_confidence: float  # Adjusted confidence
    original_confidence: float  # Original confidence
    calibration_factor: float  # Multiplier applied
    reliability_modifier: float  # Based on signal diversity and consistency
    warnings: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'overconfidence_detected': self.overconfidence_detected,
            'calibrated_confidence': self.calibrated_confidence,
            'original_confidence': self.original_confidence,
            'calibration_factor': self.calibration_factor,
            'reliability_modifier': self.reliability_modifier,
            'warnings': self.warnings
        }


@dataclass
class SensitivityAnalysis:
    """Sensitivity analysis results."""
    robustness_score: float  # [0, 1] - higher = more robust
    sensitivity_score: float  # [0, 1] - higher = more sensitive
    volatility_score: float  # [0, 1] - higher = more volatile
    robust_insights: List[str]  # Insights that are robust
    sensitive_insights: List[str]  # Insights that are sensitive
    unstable_insights: List[str]  # Insights that are unstable
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'robustness_score': self.robustness_score,
            'sensitivity_score': self.sensitivity_score,
            'volatility_score': self.volatility_score,
            'robust_insights': self.robust_insights,
            'sensitive_insights': self.sensitive_insights,
            'unstable_insights': self.unstable_insights
        }


# ============================================================================
# Signal Strength Computation
# ============================================================================

def compute_consistency_score(
    results: List[Dict],
    key_metric: str = "decision_report"
) -> float:
    """
    Compute consistency across multiple simulation runs.
    
    Higher consistency = more reliable signal.
    """
    if len(results) < 2:
        return 0.5  # Can't assess consistency with single run
    
    # Extract top recommendations from each run
    top_recommendations = []
    for result in results:
        if key_metric in result:
            dr = result[key_metric]
            if dr and 'recommended_actions' in dr:
                actions = dr['recommended_actions']
                if actions:
                    top_recommendations.append(actions[0].get('target_step', ''))
    
    if not top_recommendations:
        return 0.0
    
    # Count how many times the same step appears as top recommendation
    from collections import Counter
    counts = Counter(top_recommendations)
    most_common_count = counts.most_common(1)[0][1] if counts else 0
    
    # Consistency = proportion of runs with same top recommendation
    consistency = most_common_count / len(results)
    
    return consistency


def compute_sensitivity_score(
    baseline_result: Dict,
    perturbed_result: Dict,
    perturbation_type: str = "persona_change"
) -> float:
    """
    Compute sensitivity to perturbation.
    
    Higher sensitivity = system detects meaningful differences.
    """
    # Compare top recommendations
    baseline_top = None
    perturbed_top = None
    
    if 'decision_report' in baseline_result:
        dr = baseline_result['decision_report']
        if dr and 'recommended_actions' in dr and dr['recommended_actions']:
            baseline_top = dr['recommended_actions'][0].get('target_step')
    
    if 'decision_report' in perturbed_result:
        dr = perturbed_result['decision_report']
        if dr and 'recommended_actions' in dr and dr['recommended_actions']:
            perturbed_top = dr['recommended_actions'][0].get('target_step')
    
    # If recommendations changed, that's good (system is sensitive)
    if baseline_top and perturbed_top:
        if baseline_top != perturbed_top:
            return 0.8  # System detected change
        else:
            return 0.3  # System didn't detect change (might be insensitive)
    
    # Compare interpretation root causes
    baseline_causes = set()
    perturbed_causes = set()
    
    if 'interpretation' in baseline_result:
        interp = baseline_result['interpretation']
        if interp and 'root_causes' in interp:
            baseline_causes = set(c.get('step_id') for c in interp['root_causes'][:3])
    
    if 'interpretation' in perturbed_result:
        interp = perturbed_result['interpretation']
        if interp and 'root_causes' in interp:
            perturbed_causes = set(c.get('step_id') for c in interp['root_causes'][:3])
    
    if baseline_causes and perturbed_causes:
        # Jaccard similarity - lower = more different = better sensitivity
        intersection = len(baseline_causes & perturbed_causes)
        union = len(baseline_causes | perturbed_causes)
        similarity = intersection / union if union > 0 else 1.0
        
        # Sensitivity is inverse of similarity
        sensitivity = 1.0 - similarity
        return sensitivity
    
    return 0.5  # Default moderate sensitivity


def compute_evidence_diversity(
    result: Dict
) -> float:
    """
    Compute diversity of evidence sources.
    
    Higher diversity = more trustworthy conclusion.
    """
    evidence_sources = []
    
    # Check which layers provided evidence
    if result.get('context_graph'):
        evidence_sources.append('context_graph')
    
    if result.get('counterfactuals'):
        evidence_sources.append('counterfactuals')
    
    if result.get('decision_report'):
        evidence_sources.append('decision_engine')
    
    if result.get('deployment_validation'):
        evidence_sources.append('deployment_guard')
    
    if result.get('interpretation'):
        evidence_sources.append('interpreter')
    
    # More sources = higher diversity
    diversity = len(evidence_sources) / 5.0  # Normalize to [0, 1]
    
    # Also check if interpretation uses multiple failure modes
    if 'interpretation' in result:
        interp = result['interpretation']
        if interp and 'root_causes' in interp:
            failure_modes = set(c.get('dominant_failure_mode') for c in interp['root_causes'])
            # More diverse failure modes = better
            mode_diversity = min(1.0, len(failure_modes) / 3.0)
            diversity = (diversity + mode_diversity) / 2.0
    
    return diversity


def compute_signal_strength(
    result: Dict,
    comparison_results: Optional[List[Dict]] = None,
    perturbed_result: Optional[Dict] = None
) -> SignalStrength:
    """
    Compute overall signal strength for a result.
    
    Args:
        result: Main result to evaluate
        comparison_results: Optional list of results for consistency check
        perturbed_result: Optional perturbed result for sensitivity check
    
    Returns:
        SignalStrength assessment
    """
    # Compute components
    consistency = 0.5  # Default if no comparisons
    if comparison_results:
        consistency = compute_consistency_score(comparison_results)
    
    sensitivity = 0.5  # Default if no perturbation
    if perturbed_result:
        sensitivity = compute_sensitivity_score(result, perturbed_result)
    
    evidence_diversity = compute_evidence_diversity(result)
    
    # Overall score: weighted average
    # Consistency and evidence_diversity are more important
    score = (
        consistency * 0.4 +
        sensitivity * 0.2 +
        evidence_diversity * 0.4
    )
    
    # Compute confidence band
    # Wider band = less certain
    uncertainty = 1.0 - score
    lower = max(0.0, score - uncertainty * 0.3)
    upper = min(1.0, score + uncertainty * 0.3)
    confidence_band = (lower, upper)
    
    # Generate reasoning
    reasoning_parts = []
    if consistency > 0.7:
        reasoning_parts.append("High consistency across runs")
    elif consistency < 0.4:
        reasoning_parts.append("Low consistency - results vary")
    
    if sensitivity > 0.6:
        reasoning_parts.append("System detects meaningful differences")
    elif sensitivity < 0.3:
        reasoning_parts.append("System may be insensitive to changes")
    
    if evidence_diversity > 0.7:
        reasoning_parts.append("Multiple evidence sources")
    elif evidence_diversity < 0.4:
        reasoning_parts.append("Limited evidence sources")
    
    reasoning = ". ".join(reasoning_parts) if reasoning_parts else "Moderate signal quality"
    
    return SignalStrength(
        score=score,
        consistency=consistency,
        sensitivity=sensitivity,
        evidence_diversity=evidence_diversity,
        confidence_band=confidence_band,
        reasoning=reasoning
    )


# ============================================================================
# False Certainty Detection
# ============================================================================

def detect_false_certainty(
    result: Dict
) -> List[str]:
    """
    Detect cases where system is overconfident despite weak evidence.
    
    Returns:
        List of warnings about false certainty
    """
    warnings = []
    
    # Check decision report confidence vs evidence
    if 'decision_report' in result:
        dr = result['decision_report']
        if dr:
            overall_confidence = dr.get('overall_confidence', 0.0)
            actions = dr.get('recommended_actions', [])
            
            # High confidence but few recommendations = suspicious
            if overall_confidence > 0.8 and len(actions) < 3:
                warnings.append(f"High confidence ({overall_confidence:.1%}) but only {len(actions)} recommendations")
            
            # High confidence but low evidence diversity
            evidence_diversity = compute_evidence_diversity(result)
            if overall_confidence > 0.8 and evidence_diversity < 0.5:
                warnings.append(f"High confidence ({overall_confidence:.1%}) but low evidence diversity ({evidence_diversity:.1%})")
    
    # Check interpretation confidence
    if 'interpretation' in result:
        interp = result['interpretation']
        if interp and 'root_causes' in interp:
            causes = interp['root_causes']
            if causes:
                # Check if all causes have same failure mode (low diversity)
                failure_modes = [c.get('dominant_failure_mode') for c in causes]
                unique_modes = len(set(failure_modes))
                
                if len(causes) > 3 and unique_modes == 1:
                    warnings.append(f"All {len(causes)} root causes have same failure mode - may be oversimplified")
                
                # Check confidence scores
                avg_confidence = sum(c.get('confidence', 0) for c in causes) / len(causes)
                if avg_confidence > 0.7 and unique_modes < 2:
                    warnings.append(f"High average confidence ({avg_confidence:.1%}) but low failure mode diversity")
    
    # Check deployment validation
    if 'deployment_validation' in result:
        dv = result['deployment_validation']
        if dv:
            safe_count = sum(1 for r in dv if r.get('evaluation', {}).get('rollout_recommendation') == 'safe')
            if safe_count == len(dv) and len(dv) > 3:
                warnings.append(f"All {len(dv)} recommendations marked safe - may be overconfident")
    
    return warnings


# ============================================================================
# Final Judgment Layer
# ============================================================================

def make_signal_judgment(
    result: Dict,
    signal_strength: SignalStrength,
    false_certainty_warnings: List[str]
) -> SignalJudgment:
    """
    Make final judgment on signal quality.
    
    Returns:
        SignalJudgment with classification and explanation
    """
    score = signal_strength.score
    
    # Classify
    if score >= 0.7 and len(false_certainty_warnings) == 0:
        classification = "strong_signal"
        explanation = f"Signal strength is high ({score:.1%}) with consistent evidence and no false certainty warnings."
    elif score >= 0.5 and len(false_certainty_warnings) <= 1:
        classification = "weak_signal"
        explanation = f"Signal strength is moderate ({score:.1%}). Some conclusions are reliable, but caution is advised."
    else:
        classification = "inconclusive"
        explanation = f"Signal strength is low ({score:.1%}) or false certainty detected. Results should be interpreted with caution."
    
    # Identify trustworthy conclusions
    trustworthy = []
    uncertain = []
    
    # Decision report
    if 'decision_report' in result:
        dr = result['decision_report']
        if dr and 'recommended_actions' in dr:
            actions = dr['recommended_actions']
            if actions and signal_strength.consistency > 0.6:
                top_action = actions[0]
                trustworthy.append(f"Top recommendation: {top_action.get('target_step')} ({top_action.get('change_type')})")
            elif actions:
                uncertain.append("Decision recommendations may vary across runs")
    
    # Interpretation
    if 'interpretation' in result:
        interp = result['interpretation']
        if interp:
            if signal_strength.evidence_diversity > 0.6:
                if 'dominant_patterns' in interp and interp['dominant_patterns']:
                    pattern = interp['dominant_patterns'][0]
                    trustworthy.append(f"Structural pattern: {pattern.get('pattern_name')}")
            else:
                uncertain.append("Interpretation based on limited evidence")
            
            if 'root_causes' in interp:
                causes = interp['root_causes']
                if causes and len(set(c.get('dominant_failure_mode') for c in causes)) > 1:
                    trustworthy.append(f"Multiple failure modes identified ({len(causes)} root causes)")
                elif causes:
                    uncertain.append("All root causes have same failure mode - may be oversimplified")
    
    # Deployment validation
    if 'deployment_validation' in result:
        dv = result['deployment_validation']
        if dv:
            safe_count = sum(1 for r in dv if r.get('evaluation', {}).get('rollout_recommendation') == 'safe')
            if safe_count > 0 and safe_count < len(dv):
                trustworthy.append(f"{safe_count}/{len(dv)} recommendations validated as safe to deploy")
            elif safe_count == len(dv):
                uncertain.append("All recommendations marked safe - verify risk assessment")
    
    # Improvement suggestions
    improvements = []
    
    if signal_strength.consistency < 0.5:
        improvements.append("Run multiple simulations to assess consistency")
    
    if signal_strength.evidence_diversity < 0.5:
        improvements.append("Gather more diverse evidence (calibration data, counterfactuals)")
    
    if signal_strength.sensitivity < 0.4:
        improvements.append("Test with perturbed inputs to verify sensitivity")
    
    if len(false_certainty_warnings) > 0:
        improvements.append("Review confidence scores - may be overconfident")
    
    if not improvements:
        improvements.append("Signal quality is good - continue monitoring")
    
    return SignalJudgment(
        classification=classification,
        explanation=explanation,
        trustworthy_conclusions=trustworthy,
        uncertain_conclusions=uncertain,
        improvement_suggestions=improvements
    )


# ============================================================================
# Stability Assessment
# ============================================================================

def assess_stability(
    results: List[Dict]
) -> StabilityMetrics:
    """
    Assess stability across multiple runs with identical inputs.
    
    Args:
        results: List of results from multiple runs
    
    Returns:
        StabilityMetrics assessment
    """
    if len(results) < 2:
        return StabilityMetrics(
            variance_score=0.5,
            consistency_score=0.5,
            top_recommendation_stability=0.5,
            root_cause_stability=0.5,
            instability_flags=["Cannot assess stability - need at least 2 runs"]
        )
    
    # Extract top recommendations
    top_recommendations = []
    for result in results:
        if 'decision_report' in result and result['decision_report']:
            dr = result['decision_report']
            if 'recommended_actions' in dr and dr['recommended_actions']:
                top_recommendations.append(dr['recommended_actions'][0].get('target_step', ''))
    
    # Top recommendation stability
    from collections import Counter
    if top_recommendations:
        counts = Counter(top_recommendations)
        most_common_count = counts.most_common(1)[0][1]
        top_recommendation_stability = most_common_count / len(results)
    else:
        top_recommendation_stability = 0.0
    
    # Root cause stability
    root_cause_sets = []
    for result in results:
        if 'interpretation' in result and result['interpretation']:
            interp = result['interpretation']
            if 'root_causes' in interp:
                causes = set(c.get('step_id') for c in interp['root_causes'][:5])
                root_cause_sets.append(causes)
    
    if root_cause_sets:
        # Compute Jaccard similarity between all pairs
        similarities = []
        for i in range(len(root_cause_sets)):
            for j in range(i + 1, len(root_cause_sets)):
                intersection = len(root_cause_sets[i] & root_cause_sets[j])
                union = len(root_cause_sets[i] | root_cause_sets[j])
                if union > 0:
                    similarities.append(intersection / union)
        
        root_cause_stability = statistics.mean(similarities) if similarities else 0.0
    else:
        root_cause_stability = 0.0
    
    # Overall consistency
    consistency_score = (top_recommendation_stability + root_cause_stability) / 2.0
    
    # Variance score (inverse of stability)
    variance_score = 1.0 - consistency_score
    
    # Instability flags
    instability_flags = []
    if top_recommendation_stability < 0.5:
        instability_flags.append("Top recommendations vary across runs")
    
    if root_cause_stability < 0.5:
        instability_flags.append("Root causes vary across runs")
    
    if variance_score > 0.5:
        instability_flags.append("High variance detected - results are unstable")
    
    return StabilityMetrics(
        variance_score=variance_score,
        consistency_score=consistency_score,
        top_recommendation_stability=top_recommendation_stability,
        root_cause_stability=root_cause_stability,
        instability_flags=instability_flags
    )


# ============================================================================
# Confidence Calibration
# ============================================================================

def calibrate_confidence(
    result: Dict,
    signal_strength: SignalStrength,
    stability: Optional[StabilityMetrics] = None
) -> ConfidenceCalibration:
    """
    Calibrate confidence scores to detect and correct overconfidence.
    
    Args:
        result: Result to calibrate
        signal_strength: Signal strength assessment
        stability: Optional stability metrics
    
    Returns:
        ConfidenceCalibration with adjusted confidence
    """
    # Extract original confidence
    original_confidence = 0.5  # Default
    if 'decision_report' in result and result['decision_report']:
        original_confidence = result['decision_report'].get('overall_confidence', 0.5)
    
    # Detect overconfidence
    overconfidence_detected = False
    warnings = []
    
    # Check if confidence is too high relative to evidence
    evidence_diversity = signal_strength.evidence_diversity
    if original_confidence > 0.9 and evidence_diversity < 0.6:
        overconfidence_detected = True
        warnings.append(f"High confidence ({original_confidence:.1%}) but low evidence diversity ({evidence_diversity:.1%})")
    
    # Check if confidence is too high relative to consistency
    consistency = signal_strength.consistency
    if original_confidence > 0.9 and consistency < 0.6:
        overconfidence_detected = True
        warnings.append(f"High confidence ({original_confidence:.1%}) but low consistency ({consistency:.1%})")
    
    # Check for 100% confidence
    if original_confidence >= 1.0:
        overconfidence_detected = True
        warnings.append("100% confidence detected - likely overconfident")
    
    # Compute reliability modifier
    # Based on signal diversity and consistency
    reliability_modifier = (evidence_diversity * 0.5 + consistency * 0.5)
    
    # If stability data available, incorporate it
    if stability:
        reliability_modifier = (reliability_modifier + stability.consistency_score) / 2.0
    
    # Check for risk flags (contradictions detected)
    risk_flags_penalty = 0.0
    if 'signal_quality' in result:
        sq = result['signal_quality']
        if isinstance(sq, dict):
            risk_flags = sq.get('risk_flags', [])
            if risk_flags:
                # Each risk flag reduces confidence
                risk_flags_penalty = min(0.3, len(risk_flags) * 0.1)
                overconfidence_detected = True  # Risk flags indicate problems
                warnings.append(f"{len(risk_flags)} risk flags detected - reducing confidence")
    
    # Calibration factor: reduce confidence if overconfident or risk flags present
    if overconfidence_detected or risk_flags_penalty > 0:
        # Reduce confidence proportionally to reliability and risk flags
        calibration_factor = reliability_modifier * (1.0 - risk_flags_penalty)
    else:
        # Slight adjustment based on reliability
        calibration_factor = 0.9 + (reliability_modifier * 0.1)
    
    # Apply calibration
    calibrated_confidence = min(0.95, original_confidence * calibration_factor)
    
    # Additional penalty for risk flags
    calibrated_confidence = max(0.0, calibrated_confidence - risk_flags_penalty)
    
    # Ensure minimum confidence if evidence is weak
    if evidence_diversity < 0.4:
        calibrated_confidence = min(calibrated_confidence, 0.6)
    
    return ConfidenceCalibration(
        overconfidence_detected=overconfidence_detected,
        calibrated_confidence=calibrated_confidence,
        original_confidence=original_confidence,
        calibration_factor=calibration_factor,
        reliability_modifier=reliability_modifier,
        warnings=warnings
    )


# ============================================================================
# Sensitivity Analysis
# ============================================================================

def analyze_sensitivity(
    baseline_result: Dict,
    perturbed_results: List[Tuple[str, Dict]]  # List of (perturbation_type, result)
) -> SensitivityAnalysis:
    """
    Analyze sensitivity to controlled perturbations.
    
    Args:
        baseline_result: Baseline result
        perturbed_results: List of (perturbation_type, result) tuples
    
    Returns:
        SensitivityAnalysis with robustness/sensitivity assessment
    """
    if not perturbed_results:
        return SensitivityAnalysis(
            robustness_score=0.5,
            sensitivity_score=0.5,
            volatility_score=0.5,
            robust_insights=[],
            sensitive_insights=[],
            unstable_insights=["No perturbation tests available"]
        )
    
    # Extract baseline insights
    baseline_top = None
    baseline_causes = set()
    
    if 'decision_report' in baseline_result and baseline_result['decision_report']:
        dr = baseline_result['decision_report']
        if 'recommended_actions' in dr and dr['recommended_actions']:
            baseline_top = dr['recommended_actions'][0].get('target_step')
    
    if 'interpretation' in baseline_result and baseline_result['interpretation']:
        interp = baseline_result['interpretation']
        if 'root_causes' in interp:
            baseline_causes = set(c.get('step_id') for c in interp['root_causes'][:5])
    
    # Compare with perturbed results
    changes = []
    robust_items = []
    sensitive_items = []
    unstable_items = []
    
    for perturbation_type, perturbed_result in perturbed_results:
        perturbed_top = None
        perturbed_causes = set()
        
        if 'decision_report' in perturbed_result and perturbed_result['decision_report']:
            dr = perturbed_result['decision_report']
            if 'recommended_actions' in dr and dr['recommended_actions']:
                perturbed_top = dr['recommended_actions'][0].get('target_step')
        
        if 'interpretation' in perturbed_result and perturbed_result['interpretation']:
            interp = perturbed_result['interpretation']
            if 'root_causes' in interp:
                perturbed_causes = set(c.get('step_id') for c in interp['root_causes'][:5])
        
        # Check if top recommendation changed
        if baseline_top and perturbed_top:
            if baseline_top == perturbed_top:
                robust_items.append(f"Top recommendation: {baseline_top}")
            else:
                sensitive_items.append(f"Top recommendation changed: {baseline_top} → {perturbed_top} ({perturbation_type})")
                changes.append(1.0)
        
        # Check root cause overlap
        if baseline_causes and perturbed_causes:
            overlap = len(baseline_causes & perturbed_causes)
            total = len(baseline_causes | perturbed_causes)
            similarity = overlap / total if total > 0 else 0.0
            
            if similarity > 0.8:
                robust_items.append(f"Root causes stable ({perturbation_type})")
            elif similarity > 0.5:
                sensitive_items.append(f"Root causes partially changed ({perturbation_type})")
                changes.append(1.0 - similarity)
            else:
                unstable_items.append(f"Root causes highly volatile ({perturbation_type})")
                changes.append(1.0)
    
    # Compute scores
    if changes:
        volatility_score = statistics.mean(changes) if changes else 0.5
        sensitivity_score = min(1.0, volatility_score * 1.2)  # Slight amplification
        robustness_score = 1.0 - volatility_score
    else:
        volatility_score = 0.5
        sensitivity_score = 0.5
        robustness_score = 0.5
    
    # Deduplicate lists
    robust_insights = list(set(robust_items))
    sensitive_insights = list(set(sensitive_items))
    unstable_insights = list(set(unstable_items))
    
    return SensitivityAnalysis(
        robustness_score=robustness_score,
        sensitivity_score=sensitivity_score,
        volatility_score=volatility_score,
        robust_insights=robust_insights,
        sensitive_insights=sensitive_insights,
        unstable_insights=unstable_insights
    )


# ============================================================================
# Trust Index Computation
# ============================================================================

def compute_trust_index(
    signal_strength: SignalStrength,
    stability: Optional[StabilityMetrics] = None,
    confidence_calibration: Optional[ConfidenceCalibration] = None,
    sensitivity: Optional[SensitivityAnalysis] = None
) -> float:
    """
    Compute overall trust index (0-1).
    
    Higher = more trustworthy.
    """
    # Base components
    consistency = signal_strength.consistency
    evidence_diversity = signal_strength.evidence_diversity
    sensitivity_stability = signal_strength.sensitivity
    
    # Incorporate stability if available
    if stability:
        consistency = (consistency + stability.consistency_score) / 2.0
    
    # Incorporate confidence calibration if available
    if confidence_calibration:
        # Trust is reduced if overconfidence detected
        if confidence_calibration.overconfidence_detected:
            consistency *= 0.8
    
    # Incorporate sensitivity if available
    if sensitivity:
        # Higher robustness = higher trust
        consistency = (consistency + sensitivity.robustness_score) / 2.0
    
    # Check for contradictory signals
    contradictory_penalty = 0.0
    if confidence_calibration and confidence_calibration.overconfidence_detected:
        contradictory_penalty += 0.15
    
    if sensitivity and sensitivity.volatility_score > 0.7:
        contradictory_penalty += 0.15
    
    # Trust index = weighted combination
    trust_index = (
        consistency * 0.3 +
        evidence_diversity * 0.3 +
        sensitivity_stability * 0.2 +
        (1.0 - contradictory_penalty) * 0.2
    )
    
    # Apply minimum bounds
    if evidence_diversity < 0.3:
        trust_index = min(trust_index, 0.5)
    
    return max(0.0, min(1.0, trust_index))


# ============================================================================
# Final Evaluation Summary
# ============================================================================

def generate_final_evaluation(
    result: Dict,
    signal_strength: SignalStrength,
    stability: Optional[StabilityMetrics] = None,
    confidence_calibration: Optional[ConfidenceCalibration] = None,
    sensitivity: Optional[SensitivityAnalysis] = None,
    false_certainty_warnings: Optional[List[str]] = None
) -> Dict:
    """
    Generate final evaluation summary.
    
    Returns:
        Complete evaluation with trust index, risk flags, safe to act on, needs validation
    """
    # Compute trust index
    trust_index = compute_trust_index(
        signal_strength,
        stability,
        confidence_calibration,
        sensitivity
    )
    
    # Apply additional penalty if risk flags are present in result
    # (Risk flags will be generated in this function, so we check after)
    # This is handled by checking false_certainty_warnings and confidence_calibration
    
    # Collect risk flags
    risk_flags = []
    
    if false_certainty_warnings:
        risk_flags.extend(false_certainty_warnings)
    
    if stability and stability.instability_flags:
        risk_flags.extend(stability.instability_flags)
    
    if confidence_calibration and confidence_calibration.overconfidence_detected:
        risk_flags.append("Overconfident recommendations detected")
    
    if sensitivity and sensitivity.volatility_score > 0.6:
        risk_flags.append(f"High sensitivity to perturbations (volatility: {sensitivity.volatility_score:.1%})")
    
    # Identify safe to act on
    safe_to_act_on = []
    
    # Structural patterns are usually robust
    if 'interpretation' in result and result['interpretation']:
        interp = result['interpretation']
        if 'dominant_patterns' in interp and interp['dominant_patterns']:
            if sensitivity and sensitivity.robustness_score > 0.6:
                for pattern in interp['dominant_patterns']:
                    safe_to_act_on.append(f"Structural pattern: {pattern.get('pattern_name')}")
            elif not sensitivity or signal_strength.evidence_diversity > 0.7:
                # If no sensitivity test but high evidence diversity
                for pattern in interp['dominant_patterns']:
                    safe_to_act_on.append(f"Structural pattern: {pattern.get('pattern_name')}")
    
    # High evidence diversity conclusions
    if signal_strength.evidence_diversity > 0.7:
        if 'interpretation' in result and result['interpretation']:
            interp = result['interpretation']
            if 'root_causes' in interp:
                # Check for common failure modes
                failure_modes = [c.get('dominant_failure_mode') for c in interp['root_causes']]
                unique_modes = set(failure_modes)
                if len(unique_modes) > 1:
                    safe_to_act_on.append(f"Multiple failure modes identified: {', '.join(list(unique_modes)[:3])}")
    
    # Stable recommendations
    if stability and stability.top_recommendation_stability > 0.7:
        if 'decision_report' in result and result['decision_report']:
            dr = result['decision_report']
            if 'recommended_actions' in dr and dr['recommended_actions']:
                top = dr['recommended_actions'][0]
                safe_to_act_on.append(f"Stable top recommendation: {top.get('target_step')}")
    
    # Needs validation
    needs_validation = []
    
    # High confidence but low evidence
    if confidence_calibration and confidence_calibration.overconfidence_detected:
        needs_validation.append("Magnitude of impact estimates")
        needs_validation.append("Exact ranking of recommendations")
    
    # Unstable areas
    if stability and stability.variance_score > 0.5:
        needs_validation.append("Recommendation rankings (high variance)")
        needs_validation.append("Root cause prioritization")
    
    # Sensitive areas
    if sensitivity and sensitivity.volatility_score > 0.6:
        needs_validation.append("Persona-specific insights")
        needs_validation.append("Step-level recommendations")
    
    # Low evidence diversity
    if signal_strength.evidence_diversity < 0.5:
        needs_validation.append("All conclusions (limited evidence)")
    
    # Build summary
    stability_score = stability.consistency_score if stability else 0.5
    confidence_reliability = confidence_calibration.reliability_modifier if confidence_calibration else 0.5
    
    return {
        "signal_quality": {
            "strength": signal_strength.score,
            "stability": stability_score,
            "confidence_calibration": confidence_reliability,
            "overall_trust_index": trust_index
        },
        "risk_flags": risk_flags,
        "safe_to_act_on": safe_to_act_on if safe_to_act_on else ["No high-confidence conclusions identified"],
        "needs_validation": needs_validation if needs_validation else ["All conclusions need validation"]
    }


# ============================================================================
# Main Evaluation Function
# ============================================================================

def evaluate_signal_quality(
    result: Dict,
    comparison_results: Optional[List[Dict]] = None,
    perturbed_result: Optional[Dict] = None,
    perturbed_results: Optional[List[Tuple[str, Dict]]] = None
) -> Dict:
    """
    Complete signal quality evaluation with stability, calibration, and sensitivity.
    
    Args:
        result: Main result to evaluate
        comparison_results: Optional list of results from multiple runs (for stability)
        perturbed_result: Optional single perturbed result (for sensitivity)
        perturbed_results: Optional list of (perturbation_type, result) tuples (for sensitivity analysis)
    
    Returns:
        Complete evaluation report with trust index and final summary
    """
    # Compute signal strength
    signal_strength = compute_signal_strength(result, comparison_results, perturbed_result)
    
    # Assess stability
    stability = None
    if comparison_results and len(comparison_results) >= 2:
        stability = assess_stability(comparison_results)
    
    # Calibrate confidence
    confidence_calibration = calibrate_confidence(result, signal_strength, stability)
    
    # Analyze sensitivity
    sensitivity = None
    if perturbed_results:
        sensitivity = analyze_sensitivity(result, perturbed_results)
    elif perturbed_result:
        sensitivity = analyze_sensitivity(result, [("single_perturbation", perturbed_result)])
    
    # Detect false certainty
    false_certainty_warnings = detect_false_certainty(result)
    
    # Make final judgment
    judgment = make_signal_judgment(result, signal_strength, false_certainty_warnings)
    
    # Generate final evaluation summary
    final_evaluation = generate_final_evaluation(
        result,
        signal_strength,
        stability,
        confidence_calibration,
        sensitivity,
        false_certainty_warnings
    )
    
    return {
        'signal_strength': signal_strength.to_dict(),
        'stability': stability.to_dict() if stability else None,
        'confidence_calibration': confidence_calibration.to_dict(),
        'sensitivity': sensitivity.to_dict() if sensitivity else None,
        'false_certainty_warnings': false_certainty_warnings,
        'judgment': judgment.to_dict(),
        'final_evaluation': final_evaluation,
        'summary': {
            'overall_score': signal_strength.score,
            'classification': judgment.classification,
            'confidence_band': signal_strength.confidence_band,
            'trust_index': final_evaluation['signal_quality']['overall_trust_index']
        }
    }


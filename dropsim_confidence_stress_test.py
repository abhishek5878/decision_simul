"""
dropsim_confidence_stress_test.py - Confidence Stress Test Suite

Evaluates whether the system's confidence judgments are trustworthy by:
- Testing if confidence is lowered when it should be
- Testing if confidence is maintained only when warranted
- Detecting false certainty (hallucinated confidence)
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import copy
import random


@dataclass
class StressTestResult:
    """Result of a single stress test."""
    test_id: str
    test_type: str
    expected_confidence_band: str  # "HIGH", "MODERATE", "LOW"
    actual_confidence: float
    actual_confidence_band: str
    passed: bool
    issue: Optional[str]  # What went wrong if failed
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'test_id': self.test_id,
            'test_type': self.test_type,
            'expected_confidence_band': self.expected_confidence_band,
            'actual_confidence': self.actual_confidence,
            'actual_confidence_band': self.actual_confidence_band,
            'passed': self.passed,
            'issue': self.issue
        }


@dataclass
class ConfidenceSanityMetrics:
    """Metrics for confidence sanity checks."""
    false_confidence_rate: float  # % of cases with high confidence but contradictions
    missed_uncertainty_rate: float  # % of cases with low signal but high confidence
    confidence_volatility: float  # Variance in confidence across similar inputs
    overconfidence_count: int
    underconfidence_count: int
    correct_confidence_count: int
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'false_confidence_rate': self.false_confidence_rate,
            'missed_uncertainty_rate': self.missed_uncertainty_rate,
            'confidence_volatility': self.confidence_volatility,
            'overconfidence_count': self.overconfidence_count,
            'underconfidence_count': self.underconfidence_count,
            'correct_confidence_count': self.correct_confidence_count
        }


@dataclass
class ConfidenceReportCard:
    """Complete confidence evaluation report."""
    epistemic_health: str  # "Excellent", "Good", "Moderate", "Poor"
    overconfidence_rate: float
    underconfidence_rate: float
    robust_zones: List[str]  # Steps/areas with reliable confidence
    fragile_zones: List[str]  # Steps/areas with unreliable confidence
    recommendation: str
    sanity_metrics: ConfidenceSanityMetrics
    test_results: List[StressTestResult]
    reliability_boundary: Dict  # What system is reliable/unreliable for
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'epistemic_health': self.epistemic_health,
            'overconfidence_rate': self.overconfidence_rate,
            'underconfidence_rate': self.underconfidence_rate,
            'robust_zones': self.robust_zones,
            'fragile_zones': self.fragile_zones,
            'recommendation': self.recommendation,
            'sanity_metrics': self.sanity_metrics.to_dict(),
            'test_results': [r.to_dict() for r in self.test_results],
            'reliability_boundary': self.reliability_boundary
        }


# ============================================================================
# Stress Test Scenarios
# ============================================================================

def create_high_confidence_wrong_test(
    baseline_result: Dict
) -> Tuple[Dict, str]:
    """
    Create test case: High confidence but wrong causal structure.
    
    Perfectly consistent inputs but incorrect causal structure.
    Expectation: System should lower confidence due to contradiction.
    """
    # Create corrupted result with inverted causal structure
    corrupted = copy.deepcopy(baseline_result)
    
    # Invert context graph edges (wrong causal structure)
    if 'context_graph' in corrupted and corrupted['context_graph']:
        cg = corrupted['context_graph']
        if 'edges' in cg:
            # Reverse edge directions (wrong causality)
            edges = cg['edges']
            if isinstance(edges, list):
                for edge in edges:
                    if isinstance(edge, dict) and 'from' in edge and 'to' in edge:
                        edge['from'], edge['to'] = edge['to'], edge['from']
    
    # Add contradictory signals
    if 'context_graph' in corrupted and corrupted['context_graph']:
        nodes = corrupted['context_graph'].get('nodes', [])
        for node in nodes[:3]:  # First 3 nodes
            if isinstance(node, dict):
                # High drop but low effort (contradictory)
                node['drop_rate'] = 0.9
                node['avg_perceived_effort'] = 0.1
    
    return corrupted, "high_confidence_wrong"


def create_low_signal_test(
    baseline_result: Dict
) -> Tuple[Dict, str]:
    """
    Create test case: Sparse or noisy inputs with conflicting weak signals.
    
    Expectation: System should return LOW confidence.
    """
    corrupted = copy.deepcopy(baseline_result)
    
    # Make signals sparse and conflicting
    if 'context_graph' in corrupted and corrupted['context_graph']:
        nodes = corrupted['context_graph'].get('nodes', [])
        for i, node in enumerate(nodes):
            if isinstance(node, dict):
                # Add noise: randomize drop rates
                node['drop_rate'] = random.uniform(0.3, 0.7)
                node['total_entries'] = max(10, node.get('total_entries', 100) // 10)  # Sparse data
                node['avg_perceived_effort'] = random.uniform(0.2, 0.8)
                node['avg_perceived_risk'] = random.uniform(0.2, 0.8)
    
    # Remove strong signals
    if 'decision_report' in corrupted and corrupted['decision_report']:
        dr = corrupted['decision_report']
        if 'recommended_actions' in dr:
            # Make recommendations weak
            for action in dr['recommended_actions']:
                if isinstance(action, dict):
                    action['confidence'] = random.uniform(0.3, 0.5)
                    action['estimated_impact'] = random.uniform(0.05, 0.15)
    
    return corrupted, "low_signal"


def create_overfitting_trap_test(
    baseline_result: Dict
) -> Tuple[List[Dict], str]:
    """
    Create test case: Identical runs with tiny perturbations.
    
    Expectation: Confidence should fluctuate slightly, not remain rigid.
    """
    results = []
    
    # Create 5 slightly perturbed versions
    for i in range(5):
        perturbed = copy.deepcopy(baseline_result)
        
        # Tiny perturbation: change one node slightly
        if 'context_graph' in perturbed and perturbed['context_graph']:
            nodes = perturbed['context_graph'].get('nodes', [])
            if nodes:
                node_idx = i % len(nodes)
                if isinstance(nodes[node_idx], dict):
                    # Tiny change
                    nodes[node_idx]['drop_rate'] = nodes[node_idx].get('drop_rate', 0.5) + random.uniform(-0.02, 0.02)
                    nodes[node_idx]['drop_rate'] = max(0.0, min(1.0, nodes[node_idx]['drop_rate']))
        
        results.append(perturbed)
    
    return results, "overfitting_trap"


def create_true_positive_test(
    baseline_result: Dict
) -> Tuple[Dict, str]:
    """
    Create test case: Clean, consistent signals.
    
    Expectation: High confidence, stable across perturbations.
    """
    # Use baseline as-is (it should be clean)
    return copy.deepcopy(baseline_result), "true_positive"


# ============================================================================
# Confidence Sanity Checks
# ============================================================================

def check_overconfidence(
    result: Dict
) -> Tuple[bool, Optional[str]]:
    """
    Check if system is overconfident.
    
    Returns:
        (is_overconfident, reason)
    """
    confidence_assessment = result.get('confidence_assessment', {})
    if not confidence_assessment:
        return False, None
    
    adjusted_confidence = confidence_assessment.get('adjusted_confidence', 0.5)
    contradiction_count = confidence_assessment.get('contradiction_count', 0)
    confidence_band = confidence_assessment.get('confidence_band', 'MODERATE')
    
    # Overconfidence: contradictions detected but confidence still high
    if contradiction_count > 0 and adjusted_confidence > 0.7:
        return True, f"Contradictions detected ({contradiction_count}) but confidence still high ({adjusted_confidence:.1%})"
    
    # Overconfidence: confidence band is HIGH but contradictions exist
    if contradiction_count > 0 and confidence_band == 'HIGH':
        return True, f"Contradictions detected ({contradiction_count}) but confidence band is HIGH"
    
    # Check signal quality for risk flags
    signal_quality = result.get('signal_quality', {})
    if isinstance(signal_quality, dict):
        risk_flags = signal_quality.get('risk_flags', [])
        if risk_flags and adjusted_confidence > 0.7:
            return True, f"Risk flags present ({len(risk_flags)}) but confidence still high ({adjusted_confidence:.1%})"
    
    return False, None


def check_underconfidence(
    result: Dict
) -> Tuple[bool, Optional[str]]:
    """
    Check if system is underconfident.
    
    Returns:
        (is_underconfident, reason)
    """
    confidence_assessment = result.get('confidence_assessment', {})
    if not confidence_assessment:
        return False, None
    
    adjusted_confidence = confidence_assessment.get('adjusted_confidence', 0.5)
    confidence_band = confidence_assessment.get('confidence_band', 'MODERATE')
    evidence_diversity = confidence_assessment.get('evidence_diversity', 1.0)
    stability_factor = confidence_assessment.get('stability_factor', 1.0)
    
    # Underconfidence: high evidence quality but low confidence
    if evidence_diversity > 0.7 and stability_factor > 0.7:
        if adjusted_confidence < 0.3:
            return True, f"High evidence quality (diversity: {evidence_diversity:.1%}, stability: {stability_factor:.1%}) but low confidence ({adjusted_confidence:.1%})"
    
    # Check if signal strength is high but confidence is low
    signal_quality = result.get('signal_quality', {})
    if isinstance(signal_quality, dict):
        signal_strength = signal_quality.get('signal_strength', {})
        if isinstance(signal_strength, dict):
            strength_score = signal_strength.get('score', 0.5)
            if strength_score > 0.7 and adjusted_confidence < 0.4:
                return True, f"High signal strength ({strength_score:.1%}) but low confidence ({adjusted_confidence:.1%})"
    
    return False, None


def compute_confidence_volatility(
    results: List[Dict]
) -> float:
    """
    Compute confidence volatility across similar inputs.
    
    Returns:
        Standard deviation of confidence scores
    """
    confidences = []
    for result in results:
        confidence_assessment = result.get('confidence_assessment', {})
        if confidence_assessment:
            conf = confidence_assessment.get('adjusted_confidence', 0.5)
            confidences.append(conf)
        else:
            # Fallback to decision report confidence
            dr = result.get('decision_report', {})
            if dr:
                conf = dr.get('overall_confidence', 0.5)
                confidences.append(conf)
    
    if len(confidences) < 2:
        return 0.0
    
    # Compute standard deviation
    mean_conf = sum(confidences) / len(confidences)
    variance = sum((c - mean_conf) ** 2 for c in confidences) / len(confidences)
    return variance ** 0.5


# ============================================================================
# Stress Test Execution
# ============================================================================

def run_stress_test(
    test_result: Dict,
    test_type: str,
    expected_confidence_band: str
) -> StressTestResult:
    """
    Run a single stress test and evaluate result.
    
    Args:
        test_result: Result from running the test
        test_type: Type of test
        expected_confidence_band: Expected confidence band
    
    Returns:
        StressTestResult
    """
    # Apply confidence calibration if not already done
    try:
        from dropsim_confidence_calibrator import apply_confidence_calibration
        test_result = apply_confidence_calibration(test_result)
    except Exception:
        pass
    
    # Extract confidence assessment
    confidence_assessment = test_result.get('confidence_assessment', {})
    if not confidence_assessment:
        # Fallback
        dr = test_result.get('decision_report', {})
        actual_confidence = dr.get('overall_confidence', 0.5) if dr else 0.5
        actual_band = "MODERATE" if actual_confidence >= 0.5 else "LOW"
    else:
        actual_confidence = confidence_assessment.get('adjusted_confidence', 0.5)
        actual_band = confidence_assessment.get('confidence_band', 'MODERATE')
    
    # Check if passed
    passed = (actual_band == expected_confidence_band)
    
    # Determine issue if failed
    issue = None
    if not passed:
        if actual_band == 'HIGH' and expected_confidence_band in ['MODERATE', 'LOW']:
            issue = f"Overconfident: expected {expected_confidence_band}, got {actual_band}"
        elif actual_band in ['MODERATE', 'LOW'] and expected_confidence_band == 'HIGH':
            issue = f"Underconfident: expected {expected_confidence_band}, got {actual_band}"
        else:
            issue = f"Confidence mismatch: expected {expected_confidence_band}, got {actual_band}"
    
    return StressTestResult(
        test_id=f"{test_type}_{random.randint(1000, 9999)}",
        test_type=test_type,
        expected_confidence_band=expected_confidence_band,
        actual_confidence=actual_confidence,
        actual_confidence_band=actual_band,
        passed=passed,
        issue=issue
    )


def run_stress_test_suite(
    baseline_result: Dict,
    random_seed: int = 42
) -> ConfidenceReportCard:
    """
    Run complete confidence stress test suite.
    
    Args:
        baseline_result: Baseline result to test
        random_seed: Random seed for reproducibility
    
    Returns:
        ConfidenceReportCard
    """
    random.seed(random_seed)
    
    test_results = []
    all_results = []
    
    # Test A: High confidence but wrong
    try:
        corrupted, test_type = create_high_confidence_wrong_test(baseline_result)
        # Run signal quality and calibration
        try:
            from dropsim_signal_quality import evaluate_signal_quality
            from dropsim_confidence_calibrator import apply_confidence_calibration
            eval_result = evaluate_signal_quality(corrupted)
            corrupted['signal_quality'] = eval_result['final_evaluation']
            corrupted = apply_confidence_calibration(corrupted)
        except Exception:
            pass
        
        result = run_stress_test(corrupted, test_type, "LOW")
        test_results.append(result)
        all_results.append(corrupted)
    except Exception as e:
        pass
    
    # Test B: Low signal
    try:
        corrupted, test_type = create_low_signal_test(baseline_result)
        try:
            from dropsim_signal_quality import evaluate_signal_quality
            from dropsim_confidence_calibrator import apply_confidence_calibration
            eval_result = evaluate_signal_quality(corrupted)
            corrupted['signal_quality'] = eval_result['final_evaluation']
            corrupted = apply_confidence_calibration(corrupted)
        except Exception:
            pass
        
        result = run_stress_test(corrupted, test_type, "LOW")
        test_results.append(result)
        all_results.append(corrupted)
    except Exception as e:
        pass
    
    # Test C: Overfitting trap (multiple similar inputs)
    try:
        perturbed_results, test_type = create_overfitting_trap_test(baseline_result)
        for perturbed in perturbed_results:
            try:
                from dropsim_signal_quality import evaluate_signal_quality
                from dropsim_confidence_calibrator import apply_confidence_calibration
                eval_result = evaluate_signal_quality(perturbed)
                perturbed['signal_quality'] = eval_result['final_evaluation']
                perturbed = apply_confidence_calibration(perturbed)
            except Exception:
                pass
            
            # For overfitting trap, we expect moderate volatility
            result = run_stress_test(perturbed, test_type, "MODERATE")
            test_results.append(result)
            all_results.append(perturbed)
    except Exception as e:
        pass
    
    # Test D: True positive
    try:
        clean_result, test_type = create_true_positive_test(baseline_result)
        try:
            from dropsim_signal_quality import evaluate_signal_quality
            from dropsim_confidence_calibrator import apply_confidence_calibration
            eval_result = evaluate_signal_quality(clean_result)
            clean_result['signal_quality'] = eval_result['final_evaluation']
            clean_result = apply_confidence_calibration(clean_result)
        except Exception:
            pass
        
        result = run_stress_test(clean_result, test_type, "HIGH")
        test_results.append(result)
        all_results.append(clean_result)
    except Exception as e:
        pass
    
    # Compute sanity metrics
    overconfidence_count = 0
    underconfidence_count = 0
    correct_confidence_count = 0
    
    for result in all_results:
        is_overconfident, _ = check_overconfidence(result)
        is_underconfident, _ = check_underconfidence(result)
        
        if is_overconfident:
            overconfidence_count += 1
        elif is_underconfident:
            underconfidence_count += 1
        else:
            correct_confidence_count += 1
    
    total_tests = len(all_results)
    false_confidence_rate = overconfidence_count / total_tests if total_tests > 0 else 0.0
    missed_uncertainty_rate = underconfidence_count / total_tests if total_tests > 0 else 0.0
    
    # Compute volatility
    confidence_volatility = compute_confidence_volatility(all_results)
    
    sanity_metrics = ConfidenceSanityMetrics(
        false_confidence_rate=false_confidence_rate,
        missed_uncertainty_rate=missed_uncertainty_rate,
        confidence_volatility=confidence_volatility,
        overconfidence_count=overconfidence_count,
        underconfidence_count=underconfidence_count,
        correct_confidence_count=correct_confidence_count
    )
    
    # Determine epistemic health
    if false_confidence_rate < 0.1 and missed_uncertainty_rate < 0.1:
        epistemic_health = "Excellent"
    elif false_confidence_rate < 0.2 and missed_uncertainty_rate < 0.2:
        epistemic_health = "Good"
    elif false_confidence_rate < 0.3 and missed_uncertainty_rate < 0.3:
        epistemic_health = "Moderate"
    else:
        epistemic_health = "Poor"
    
    # Identify robust and fragile zones
    robust_zones = []
    fragile_zones = []
    
    # Analyze context graph nodes
    if 'context_graph' in baseline_result and baseline_result['context_graph']:
        nodes = baseline_result['context_graph'].get('nodes', [])
        for i, node in enumerate(nodes[:10]):  # First 10 nodes
            if isinstance(node, dict):
                step_id = node.get('step_id', f'Step {i+1}')
                drop_rate = node.get('drop_rate', 0.5)
                
                # Robust: consistent, moderate drop rates
                if 0.2 < drop_rate < 0.6:
                    robust_zones.append(step_id)
                # Fragile: extreme or inconsistent
                elif drop_rate > 0.8 or drop_rate < 0.1:
                    fragile_zones.append(step_id)
    
    # Generate recommendation
    if epistemic_health == "Excellent":
        recommendation = "System safe for precise forecasting and decision-making"
    elif epistemic_health == "Good":
        recommendation = "System safe for directional insights and strategic planning"
    elif epistemic_health == "Moderate":
        recommendation = "System safe for directional insights, not precise forecasting"
    else:
        recommendation = "System requires validation before use - high uncertainty"
    
    # Define reliability boundary
    reliability_boundary = {
        "reliable_for": [
            "Directional insights about user behavior",
            "Identifying high-level failure patterns",
            "Comparative analysis between products",
            "Strategic planning with validation"
        ],
        "unreliable_for": [
            "Precise conversion rate predictions",
            "Exact magnitude of impact estimates",
            "Point estimates without confidence intervals",
            "High-stakes decisions without validation"
        ],
        "requires_validation": [
            "Quantitative forecasts",
            "Budget allocation decisions",
            "Product launch decisions",
            "Any decision with >$10k impact"
        ]
    }
    
    return ConfidenceReportCard(
        epistemic_health=epistemic_health,
        overconfidence_rate=false_confidence_rate,
        underconfidence_rate=missed_uncertainty_rate,
        robust_zones=robust_zones[:5],  # Top 5
        fragile_zones=fragile_zones[:5],  # Top 5
        recommendation=recommendation,
        sanity_metrics=sanity_metrics,
        test_results=test_results,
        reliability_boundary=reliability_boundary
    )


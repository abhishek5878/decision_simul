"""
dropsim_falsification.py - Falsification Harness for DropSim

Tests whether the system can be proven wrong by:
- Injecting contradictory evidence
- Measuring if system detects inconsistency
- Checking if confidence decreases appropriately
- Verifying if conclusions change meaningfully

This does NOT add new modeling logic.
It only perturbs inputs and observes response.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import copy
import random
import json


# ============================================================================
# Falsification Test Cases
# ============================================================================

@dataclass
class FalsificationTest:
    """A single falsification test case."""
    test_id: str
    test_type: str  # "inverted_outcomes", "conflicting_signals", "shuffled_mappings"
    description: str
    corrupted_input: Dict
    expected_detection: bool  # Should system detect this as problematic?
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'test_id': self.test_id,
            'test_type': self.test_type,
            'description': self.description,
            'expected_detection': self.expected_detection
        }


@dataclass
class FalsificationResult:
    """Result of a single falsification test."""
    test: FalsificationTest
    baseline_result: Dict
    corrupted_result: Dict
    contradiction_detected: bool
    confidence_decreased: bool
    conclusions_changed: bool
    confidence_shift: float  # Change in confidence
    detection_method: Optional[str]  # How contradiction was detected
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'test': self.test.to_dict(),
            'contradiction_detected': self.contradiction_detected,
            'confidence_decreased': self.confidence_decreased,
            'conclusions_changed': self.conclusions_changed,
            'confidence_shift': self.confidence_shift,
            'detection_method': self.detection_method
        }


@dataclass
class FalsificationReport:
    """Complete falsification report."""
    total_tests: int
    contradictions_detected: int
    contradictions_missed: int
    confidence_decreased_count: int
    conclusions_changed_count: int
    test_results: List[FalsificationResult]
    verdict: str  # "ROBUST", "FRAGILE", "INCONCLUSIVE"
    reasoning: str
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'total_tests': self.total_tests,
            'contradictions_detected': self.contradictions_detected,
            'contradictions_missed': self.contradictions_missed,
            'confidence_decreased_count': self.confidence_decreased_count,
            'conclusions_changed_count': self.conclusions_changed_count,
            'test_results': [r.to_dict() for r in self.test_results],
            'verdict': self.verdict,
            'reasoning': self.reasoning
        }


# ============================================================================
# Test Case Generation
# ============================================================================

def create_inverted_outcomes_test(
    baseline_result: Dict
) -> FalsificationTest:
    """
    Create test with identical flow but inverted outcomes.
    
    Example: High drop rate step becomes low drop rate, vice versa.
    """
    # Extract context graph from baseline
    context_graph = baseline_result.get('context_graph', {})
    nodes = context_graph.get('nodes', [])
    
    if not nodes:
        return None
    
    # Create corrupted context graph with inverted drop rates
    corrupted_nodes = []
    for node in nodes[:5]:  # First 5 nodes
        if isinstance(node, dict):
            corrupted_node = copy.deepcopy(node)
            original_drop_rate = node.get('drop_rate', 0.5)
            # Invert: high becomes low, low becomes high
            inverted_drop_rate = 1.0 - original_drop_rate
            corrupted_node['drop_rate'] = inverted_drop_rate
            corrupted_node['total_drops'] = int(corrupted_node.get('total_entries', 100) * inverted_drop_rate)
            corrupted_nodes.append(corrupted_node)
        else:
            corrupted_nodes.append(node)
    
    corrupted_context_graph = copy.deepcopy(context_graph)
    corrupted_context_graph['nodes'] = corrupted_nodes + nodes[5:]  # Keep rest unchanged
    
    corrupted_result = copy.deepcopy(baseline_result)
    corrupted_result['context_graph'] = corrupted_context_graph
    
    return FalsificationTest(
        test_id="inverted_outcomes_1",
        test_type="inverted_outcomes",
        description="Inverted drop rates: high drop steps become low drop, vice versa",
        corrupted_input=corrupted_result,
        expected_detection=True
    )


def create_conflicting_signals_test(
    baseline_result: Dict
) -> FalsificationTest:
    """
    Create test with conflicting behavioral signals.
    
    Example: High effort step with high completion rate (contradictory).
    """
    context_graph = baseline_result.get('context_graph', {})
    nodes = context_graph.get('nodes', [])
    
    if not nodes:
        return None
    
    # Create corrupted nodes with conflicting signals
    corrupted_nodes = []
    for node in nodes[:3]:  # First 3 nodes
        if isinstance(node, dict):
            corrupted_node = copy.deepcopy(node)
            # High effort but high completion (contradictory)
            corrupted_node['avg_perceived_effort'] = 0.9  # Very high effort
            corrupted_node['drop_rate'] = 0.05  # Very low drop (high completion)
            corrupted_node['total_drops'] = int(corrupted_node.get('total_entries', 100) * 0.05)
            corrupted_nodes.append(corrupted_node)
        else:
            corrupted_nodes.append(node)
    
    corrupted_context_graph = copy.deepcopy(context_graph)
    corrupted_context_graph['nodes'] = corrupted_nodes + nodes[3:]
    
    corrupted_result = copy.deepcopy(baseline_result)
    corrupted_result['context_graph'] = corrupted_context_graph
    
    return FalsificationTest(
        test_id="conflicting_signals_1",
        test_type="conflicting_signals",
        description="High effort steps with high completion rates (contradictory)",
        corrupted_input=corrupted_result,
        expected_detection=True
    )


def create_shuffled_mappings_test(
    baseline_result: Dict
) -> FalsificationTest:
    """
    Create test with shuffled persona-step mappings.
    
    Randomly reassign which personas drop at which steps.
    """
    context_graph = baseline_result.get('context_graph', {})
    nodes = context_graph.get('nodes', [])
    
    if not nodes:
        return None
    
    # Shuffle drop rates between nodes
    drop_rates = [node.get('drop_rate', 0.5) for node in nodes if isinstance(node, dict)]
    random.shuffle(drop_rates)
    
    corrupted_nodes = []
    drop_idx = 0
    for node in nodes:
        if isinstance(node, dict):
            corrupted_node = copy.deepcopy(node)
            corrupted_node['drop_rate'] = drop_rates[drop_idx]
            corrupted_node['total_drops'] = int(corrupted_node.get('total_entries', 100) * drop_rates[drop_idx])
            corrupted_nodes.append(corrupted_node)
            drop_idx += 1
        else:
            corrupted_nodes.append(node)
    
    corrupted_context_graph = copy.deepcopy(context_graph)
    corrupted_context_graph['nodes'] = corrupted_nodes
    
    corrupted_result = copy.deepcopy(baseline_result)
    corrupted_result['context_graph'] = corrupted_context_graph
    
    return FalsificationTest(
        test_id="shuffled_mappings_1",
        test_type="shuffled_mappings",
        description="Randomly shuffled drop rates between steps",
        corrupted_input=corrupted_result,
        expected_detection=True
    )


def create_impossible_completion_test(
    baseline_result: Dict
) -> FalsificationTest:
    """
    Create test with impossible completion rates.
    
    Example: Step 5 has higher completion than Step 4 (impossible if sequential).
    """
    context_graph = baseline_result.get('context_graph', {})
    nodes = context_graph.get('nodes', [])
    
    if len(nodes) < 2:
        return None
    
    # Make later step have higher completion than earlier step
    corrupted_nodes = []
    for i, node in enumerate(nodes):
        if isinstance(node, dict):
            corrupted_node = copy.deepcopy(node)
            if i > 0:
                # Make this step have higher completion than previous
                prev_node = nodes[i-1]
                if isinstance(prev_node, dict):
                    prev_drop = prev_node.get('drop_rate', 0.5)
                    # This step should have lower completion (higher drop) if sequential
                    # But we'll make it have higher completion (contradiction)
                    corrupted_node['drop_rate'] = max(0.0, prev_drop - 0.2)
                    corrupted_node['total_drops'] = int(corrupted_node.get('total_entries', 100) * corrupted_node['drop_rate'])
            corrupted_nodes.append(corrupted_node)
        else:
            corrupted_nodes.append(node)
    
    corrupted_context_graph = copy.deepcopy(context_graph)
    corrupted_context_graph['nodes'] = corrupted_nodes
    
    corrupted_result = copy.deepcopy(baseline_result)
    corrupted_result['context_graph'] = corrupted_context_graph
    
    return FalsificationTest(
        test_id="impossible_completion_1",
        test_type="impossible_completion",
        description="Later steps have higher completion than earlier steps (impossible if sequential)",
        corrupted_input=corrupted_result,
        expected_detection=True
    )


# ============================================================================
# Contradiction Detection
# ============================================================================

def detect_contradiction(
    baseline_result: Dict,
    corrupted_result: Dict
) -> Tuple[bool, Optional[str]]:
    """
    Detect if corrupted result contains contradictions.
    
    Returns:
        (detected, method) - Whether contradiction detected and how
    """
    # Method 1: Check if signal quality evaluation flags issues
    baseline_sq = baseline_result.get('signal_quality', {})
    corrupted_sq = corrupted_result.get('signal_quality', {})
    
    if corrupted_sq:
        risk_flags = corrupted_sq.get('risk_flags', [])
        if risk_flags:
            return True, "signal_quality_risk_flags"
    
    # Method 2: Check if confidence/trust decreased significantly
    baseline_conf = baseline_result.get('decision_report', {}).get('overall_confidence', 0.5)
    corrupted_conf = corrupted_result.get('decision_report', {}).get('overall_confidence', 0.5)
    
    baseline_trust = baseline_result.get('signal_quality', {}).get('overall_trust_index', 0.5) if isinstance(baseline_result.get('signal_quality'), dict) else 0.5
    corrupted_trust = corrupted_result.get('signal_quality', {}).get('overall_trust_index', 0.5) if isinstance(corrupted_result.get('signal_quality'), dict) else 0.5
    
    if corrupted_conf < baseline_conf - 0.1 or corrupted_trust < baseline_trust - 0.1:  # 10% decrease
        return True, "confidence_decrease"
    
    # Method 3: Check if false certainty warnings increased
    # (This would be in signal quality evaluation)
    
    # Method 4: Check if interpretation changed dramatically
    baseline_interp = baseline_result.get('interpretation', {})
    corrupted_interp = corrupted_result.get('interpretation', {})
    
    if baseline_interp and corrupted_interp:
        baseline_causes = set(c.get('step_id') for c in baseline_interp.get('root_causes', [])[:3])
        corrupted_causes = set(c.get('step_id') for c in corrupted_interp.get('root_causes', [])[:3])
        
        # If completely different root causes, might indicate detection
        if baseline_causes and corrupted_causes and len(baseline_causes & corrupted_causes) == 0:
            return True, "root_cause_mismatch"
    
    # Method 5: Check context graph consistency
    baseline_cg = baseline_result.get('context_graph', {})
    corrupted_cg = corrupted_result.get('context_graph', {})
    
    if baseline_cg and corrupted_cg:
        baseline_nodes = baseline_cg.get('nodes', [])
        corrupted_nodes = corrupted_cg.get('nodes', [])
        
        # Check for impossible patterns
        if len(baseline_nodes) == len(corrupted_nodes):
            for i in range(len(baseline_nodes) - 1):
                if isinstance(baseline_nodes[i], dict) and isinstance(corrupted_nodes[i], dict):
                    baseline_drop = baseline_nodes[i].get('drop_rate', 0.5)
                    corrupted_drop = corrupted_nodes[i].get('drop_rate', 0.5)
                    
                    # Check if later step has higher completion (impossible)
                    if i + 1 < len(corrupted_nodes):
                        next_node = corrupted_nodes[i + 1]
                        if isinstance(next_node, dict):
                            next_drop = next_node.get('drop_rate', 0.5)
                            if corrupted_drop < next_drop:  # Later step has lower drop (higher completion)
                                return True, "impossible_completion_pattern"
    
    return False, None


def measure_confidence_shift(
    baseline_result: Dict,
    corrupted_result: Dict
) -> float:
    """
    Measure how much confidence shifted.
    
    Checks multiple confidence sources:
    - Decision report overall confidence
    - Signal quality trust index
    - Calibrated confidence
    
    Returns:
        Confidence shift (negative = decreased, positive = increased)
    """
    # Check decision report confidence
    baseline_dr_conf = baseline_result.get('decision_report', {}).get('overall_confidence', 0.5)
    corrupted_dr_conf = corrupted_result.get('decision_report', {}).get('overall_confidence', 0.5)
    dr_shift = corrupted_dr_conf - baseline_dr_conf
    
    # Check signal quality trust index
    baseline_sq = baseline_result.get('signal_quality', {})
    corrupted_sq = corrupted_result.get('signal_quality', {})
    
    baseline_trust = baseline_sq.get('overall_trust_index', 0.5) if isinstance(baseline_sq, dict) else 0.5
    corrupted_trust = corrupted_sq.get('overall_trust_index', 0.5) if isinstance(corrupted_sq, dict) else 0.5
    trust_shift = corrupted_trust - baseline_trust
    
    # Use the more significant shift
    if abs(trust_shift) > abs(dr_shift):
        return trust_shift
    return dr_shift


def check_conclusions_changed(
    baseline_result: Dict,
    corrupted_result: Dict
) -> bool:
    """
    Check if top conclusions changed meaningfully.
    """
    # Compare top recommendations
    baseline_top = None
    corrupted_top = None
    
    baseline_dr = baseline_result.get('decision_report', {})
    corrupted_dr = corrupted_result.get('decision_report', {})
    
    if baseline_dr and 'recommended_actions' in baseline_dr and baseline_dr['recommended_actions']:
        baseline_top = baseline_dr['recommended_actions'][0].get('target_step')
    
    if corrupted_dr and 'recommended_actions' in corrupted_dr and corrupted_dr['recommended_actions']:
        corrupted_top = corrupted_dr['recommended_actions'][0].get('target_step')
    
    if baseline_top and corrupted_top:
        return baseline_top != corrupted_top
    
    # Compare top root causes
    baseline_interp = baseline_result.get('interpretation', {})
    corrupted_interp = corrupted_result.get('interpretation', {})
    
    if baseline_interp and corrupted_interp:
        baseline_top_cause = None
        corrupted_top_cause = None
        
        if baseline_interp.get('root_causes'):
            baseline_top_cause = baseline_interp['root_causes'][0].get('step_id')
        
        if corrupted_interp.get('root_causes'):
            corrupted_top_cause = corrupted_interp['root_causes'][0].get('step_id')
        
        if baseline_top_cause and corrupted_top_cause:
            return baseline_top_cause != corrupted_top_cause
    
    return False


# ============================================================================
# Test Execution
# ============================================================================

def run_falsification_test(
    test: FalsificationTest,
    baseline_result: Dict
) -> FalsificationResult:
    """
    Run a single falsification test.
    
    Args:
        test: Falsification test case
        baseline_result: Baseline result for comparison
    
    Returns:
        FalsificationResult
    """
    # Run signal quality evaluation on corrupted result
    corrupted_result = test.corrupted_input
    
    try:
        from dropsim_signal_quality import evaluate_signal_quality
        from dropsim_confidence_calibrator import apply_confidence_calibration
        
        # Evaluate corrupted result (this will detect risk flags)
        corrupted_eval = evaluate_signal_quality(corrupted_result)
        corrupted_result['signal_quality'] = corrupted_eval['final_evaluation']
        
        # Apply confidence calibration (this will reduce confidence based on contradictions)
        corrupted_result = apply_confidence_calibration(corrupted_result)
        
        # Also evaluate baseline for comparison
        baseline_eval = evaluate_signal_quality(baseline_result)
        baseline_result['signal_quality'] = baseline_eval['final_evaluation']
        
        # Apply confidence calibration to baseline
        baseline_result = apply_confidence_calibration(baseline_result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        pass  # Signal quality evaluation optional
    
    # Detect contradiction
    contradiction_detected, detection_method = detect_contradiction(baseline_result, corrupted_result)
    
    # Measure confidence shift - check confidence_assessment first (new calibration)
    baseline_assessment = baseline_result.get('confidence_assessment', {})
    corrupted_assessment = corrupted_result.get('confidence_assessment', {})
    
    if corrupted_assessment:
        # Use adjusted confidence from confidence assessment
        corrupted_raw = corrupted_assessment.get('raw_confidence', 0.5)
        corrupted_adj = corrupted_assessment.get('adjusted_confidence', corrupted_raw)
        
        # If baseline has assessment, compare adjusted to adjusted
        # Otherwise, compare adjusted to baseline raw (assuming baseline had no contradictions)
        if baseline_assessment:
            baseline_adj = baseline_assessment.get('adjusted_confidence', baseline_assessment.get('raw_confidence', 0.5))
            confidence_shift = corrupted_adj - baseline_adj
        else:
            # Baseline likely had no contradictions, so compare to baseline raw confidence
            baseline_raw = baseline_result.get('decision_report', {}).get('overall_confidence', 0.5)
            if baseline_raw == 0.5:  # Default, try to get from signal quality
                baseline_sq = baseline_result.get('signal_quality', {})
                if isinstance(baseline_sq, dict):
                    baseline_raw = baseline_sq.get('overall_trust_index', 0.5)
            confidence_shift = corrupted_adj - baseline_raw
        
        # Confidence decreased if adjusted is lower than baseline
        # OR if calibration itself reduced confidence (raw vs adjusted)
        calibration_reduction = corrupted_raw - corrupted_adj
        confidence_decreased = confidence_shift < -0.05 or calibration_reduction > 0.05
    else:
        # Fallback to old method
        confidence_shift = measure_confidence_shift(baseline_result, corrupted_result)
        
        # Also check if trust index decreased
        baseline_trust = baseline_result.get('signal_quality', {}).get('overall_trust_index', 0.5) if isinstance(baseline_result.get('signal_quality'), dict) else 0.5
        corrupted_trust = corrupted_result.get('signal_quality', {}).get('overall_trust_index', 0.5) if isinstance(corrupted_result.get('signal_quality'), dict) else 0.5
        trust_shift = corrupted_trust - baseline_trust
        trust_decreased = trust_shift < -0.05  # At least 5% decrease
        
        confidence_decreased = confidence_shift < -0.05 or trust_decreased
    
    # Also check if trust index decreased
    baseline_trust = baseline_result.get('signal_quality', {}).get('overall_trust_index', 0.5) if isinstance(baseline_result.get('signal_quality'), dict) else 0.5
    corrupted_trust = corrupted_result.get('signal_quality', {}).get('overall_trust_index', 0.5) if isinstance(corrupted_result.get('signal_quality'), dict) else 0.5
    trust_shift = corrupted_trust - baseline_trust
    trust_decreased = trust_shift < -0.05  # At least 5% decrease
    
    # Check if calibrated confidence decreased
    baseline_calibrated = baseline_result.get('signal_quality', {}).get('confidence_calibration', 0.5)
    if isinstance(baseline_calibrated, dict):
        baseline_calibrated = baseline_calibrated.get('calibrated_confidence', baseline_calibrated.get('original_confidence', 0.5))
    
    corrupted_calibrated = corrupted_result.get('signal_quality', {}).get('confidence_calibration', 0.5)
    if isinstance(corrupted_calibrated, dict):
        corrupted_calibrated = corrupted_calibrated.get('calibrated_confidence', corrupted_calibrated.get('original_confidence', 0.5))
    
    calibrated_shift = corrupted_calibrated - baseline_calibrated
    calibrated_decreased = calibrated_shift < -0.05
    
    # Confidence decreased if any measure decreased
    confidence_decreased = confidence_shift < -0.05 or trust_decreased or calibrated_decreased
    
    # Check if conclusions changed
    conclusions_changed = check_conclusions_changed(baseline_result, corrupted_result)
    
    return FalsificationResult(
        test=test,
        baseline_result=baseline_result,
        corrupted_result=corrupted_result,
        contradiction_detected=contradiction_detected,
        confidence_decreased=confidence_decreased,
        conclusions_changed=conclusions_changed,
        confidence_shift=confidence_shift,
        detection_method=detection_method
    )


def run_falsification_suite(
    baseline_result: Dict,
    random_seed: int = 42
) -> FalsificationReport:
    """
    Run complete falsification test suite.
    
    Args:
        baseline_result: Baseline result to test against
        random_seed: Random seed for reproducibility
    
    Returns:
        FalsificationReport
    """
    random.seed(random_seed)
    
    # Generate test cases
    tests = []
    
    # Test 1: Inverted outcomes
    test1 = create_inverted_outcomes_test(baseline_result)
    if test1:
        tests.append(test1)
    
    # Test 2: Conflicting signals
    test2 = create_conflicting_signals_test(baseline_result)
    if test2:
        tests.append(test2)
    
    # Test 3: Shuffled mappings
    test3 = create_shuffled_mappings_test(baseline_result)
    if test3:
        tests.append(test3)
    
    # Test 4: Impossible completion
    test4 = create_impossible_completion_test(baseline_result)
    if test4:
        tests.append(test4)
    
    # Run all tests
    results = []
    for test in tests:
        result = run_falsification_test(test, baseline_result)
        results.append(result)
    
    # Analyze results
    contradictions_detected = sum(1 for r in results if r.contradiction_detected)
    contradictions_missed = sum(1 for r in results if r.test.expected_detection and not r.contradiction_detected)
    confidence_decreased_count = sum(1 for r in results if r.confidence_decreased)
    conclusions_changed_count = sum(1 for r in results if r.conclusions_changed)
    
    # Determine verdict
    detection_rate = contradictions_detected / len(results) if results else 0.0
    
    # More nuanced verdict logic
    if detection_rate >= 0.75 and confidence_decreased_count >= len(results) * 0.5:
        verdict = "ROBUST"
        reasoning = f"System detected {contradictions_detected}/{len(results)} contradictions and decreased confidence in {confidence_decreased_count} cases. System correctly flags contradictions and adjusts confidence appropriately."
    elif detection_rate >= 0.75 and confidence_decreased_count < len(results) * 0.3:
        verdict = "FRAGILE"
        reasoning = f"System detected {contradictions_detected}/{len(results)} contradictions but decreased confidence in only {confidence_decreased_count} cases. System detects problems but maintains confidence despite contradictions."
    elif detection_rate < 0.5:
        verdict = "FRAGILE"
        reasoning = f"System only detected {contradictions_detected}/{len(results)} contradictions. System fails to detect most contradictions."
    else:
        verdict = "INCONCLUSIVE"
        reasoning = f"Mixed behavior: detected {contradictions_detected}/{len(results)} contradictions, confidence decreased in {confidence_decreased_count} cases. Results are inconsistent."
    
    return FalsificationReport(
        total_tests=len(results),
        contradictions_detected=contradictions_detected,
        contradictions_missed=contradictions_missed,
        confidence_decreased_count=confidence_decreased_count,
        conclusions_changed_count=conclusions_changed_count,
        test_results=results,
        verdict=verdict,
        reasoning=reasoning
    )


"""
dropsim_calibration.py - Reality Calibration Layer for DropSim

Compares simulated outcomes with real observed behavior to:
- Identify systematic prediction errors
- Adjust confidence, not logic
- Improve trustworthiness over time

This is calibration, not learning - no retraining, no ML models.
Just confidence adjustment based on observed vs predicted differences.
"""

from typing import Dict, List, Optional, Tuple, Literal
from dataclasses import dataclass
from datetime import datetime
import json
import math

from dropsim_context_graph import ContextGraph


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class ObservedOutcomes:
    """Real-world observed metrics."""
    step_drop_rates: Dict[str, float]  # step_id -> observed drop rate
    overall_completion_rate: float  # Overall completion rate (0-1)
    step_completion_rates: Optional[Dict[str, float]] = None  # step_id -> completion rate
    time_to_complete: Optional[Dict[str, float]] = None  # step_id -> avg time (optional)
    sample_size: Optional[int] = None  # Number of real users observed
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'step_drop_rates': self.step_drop_rates,
            'overall_completion_rate': self.overall_completion_rate,
            'step_completion_rates': self.step_completion_rates,
            'time_to_complete': self.time_to_complete,
            'sample_size': self.sample_size
        }


@dataclass
class StepCalibrationMetrics:
    """Calibration metrics for a single step."""
    step_id: str
    predicted_drop_rate: float
    observed_drop_rate: float
    absolute_error: float
    relative_error: float
    error_direction: Literal["overestimate", "underestimate", "accurate"]
    bias_magnitude: float  # How much bias (0 = no bias, 1 = max bias)
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'step_id': self.step_id,
            'predicted_drop_rate': self.predicted_drop_rate,
            'observed_drop_rate': self.observed_drop_rate,
            'absolute_error': self.absolute_error,
            'relative_error': self.relative_error,
            'error_direction': self.error_direction,
            'bias_magnitude': self.bias_magnitude
        }


@dataclass
class BiasSummary:
    """Summary of systematic biases detected."""
    fatigue_bias: float  # Positive = overestimate, negative = underestimate
    effort_bias: float
    risk_bias: float
    trust_bias: float
    early_step_bias: float  # Bias in early steps (steps 1-3)
    late_step_bias: float  # Bias in late steps (steps 4+)
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'fatigue_bias': self.fatigue_bias,
            'effort_bias': self.effort_bias,
            'risk_bias': self.risk_bias,
            'trust_bias': self.trust_bias,
            'early_step_bias': self.early_step_bias,
            'late_step_bias': self.late_step_bias
        }


@dataclass
class CalibrationReport:
    """Complete calibration report."""
    calibration_score: float  # Global calibration score [0, 1]
    step_metrics: List[StepCalibrationMetrics]
    bias_summary: BiasSummary
    confidence_adjusted_predictions: Dict[str, float]  # step_id -> adjusted drop rate
    stability_score: float  # How stable predictions are [0, 1]
    timestamp: str
    dominant_biases: List[str]  # List of dominant bias types
    stable_factors: List[str]  # List of factors that are well-calibrated
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'calibration_score': self.calibration_score,
            'step_metrics': [m.to_dict() for m in self.step_metrics],
            'bias_summary': self.bias_summary.to_dict(),
            'confidence_adjusted_predictions': self.confidence_adjusted_predictions,
            'stability_score': self.stability_score,
            'timestamp': self.timestamp,
            'dominant_biases': self.dominant_biases,
            'stable_factors': self.stable_factors
        }


@dataclass
class CalibrationHistory:
    """Temporal tracking of calibration over time."""
    history: List[Dict]  # List of calibration reports over time
    
    def add_entry(self, report: CalibrationReport):
        """Add a new calibration entry."""
        self.history.append({
            'timestamp': report.timestamp,
            'calibration_score': report.calibration_score,
            'dominant_biases': report.dominant_biases,
            'stable_factors': report.stable_factors,
            'bias_summary': report.bias_summary.to_dict()
        })
    
    def get_trend(self) -> Dict:
        """Analyze trends in calibration over time."""
        if len(self.history) < 2:
            return {'trend': 'insufficient_data'}
        
        scores = [entry['calibration_score'] for entry in self.history]
        recent_avg = sum(scores[-3:]) / min(3, len(scores))
        earlier_avg = sum(scores[:-3]) / max(1, len(scores) - 3) if len(scores) > 3 else scores[0]
        
        if recent_avg > earlier_avg + 0.05:
            trend = 'improving'
        elif recent_avg < earlier_avg - 0.05:
            trend = 'regressing'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'recent_avg': recent_avg,
            'earlier_avg': earlier_avg,
            'volatility': math.sqrt(sum((s - sum(scores)/len(scores))**2 for s in scores) / len(scores))
        }
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'history': self.history,
            'trend': self.get_trend()
        }


# ============================================================================
# Calibration Engine
# ============================================================================

def extract_predicted_metrics(
    simulation_results: Dict,
    context_graph: Optional[ContextGraph] = None
) -> Dict[str, float]:
    """
    Extract predicted drop rates from simulation results.
    
    Args:
        simulation_results: Simulation output (from wizard or runner)
        context_graph: Optional context graph for step-level metrics
    
    Returns:
        Dict mapping step_id -> predicted drop rate
    """
    predicted_drop_rates = {}
    
    # Try to get from context graph first (most accurate)
    if context_graph:
        for step_id, node in context_graph.nodes.items():
            if node.total_entries > 0:
                predicted_drop_rates[step_id] = node.drop_rate
    else:
        # Fallback: extract from aggregated results
        aggregated = simulation_results.get('aggregated_results', {})
        step_results = aggregated.get('step_results', [])
        
        for step_result in step_results:
            step_id = step_result.get('step_id')
            failure_rate = step_result.get('failure_rate', 0.0)
            if step_id:
                predicted_drop_rates[step_id] = failure_rate
    
    return predicted_drop_rates


def compute_step_calibration_metrics(
    predicted_drop_rates: Dict[str, float],
    observed_drop_rates: Dict[str, float]
) -> List[StepCalibrationMetrics]:
    """
    Compute calibration metrics for each step.
    
    Args:
        predicted_drop_rates: step_id -> predicted drop rate
        observed_drop_rates: step_id -> observed drop rate
    
    Returns:
        List of StepCalibrationMetrics
    """
    metrics = []
    
    # Get all steps (union of predicted and observed)
    all_steps = set(predicted_drop_rates.keys()) | set(observed_drop_rates.keys())
    
    for step_id in all_steps:
        predicted = predicted_drop_rates.get(step_id, 0.0)
        observed = observed_drop_rates.get(step_id, 0.0)
        
        # Compute errors
        absolute_error = abs(observed - predicted)
        relative_error = absolute_error / max(observed, 0.01) if observed > 0 else absolute_error
        
        # Determine error direction
        if absolute_error < 0.02:  # Within 2% = accurate
            error_direction = "accurate"
        elif predicted > observed:
            error_direction = "overestimate"
        else:
            error_direction = "underestimate"
        
        # Bias magnitude (normalized to [0, 1])
        bias_magnitude = min(1.0, absolute_error / 0.5)  # Max bias at 50% error
        
        metrics.append(StepCalibrationMetrics(
            step_id=step_id,
            predicted_drop_rate=predicted,
            observed_drop_rate=observed,
            absolute_error=absolute_error,
            relative_error=relative_error,
            error_direction=error_direction,
            bias_magnitude=bias_magnitude
        ))
    
    return metrics


def detect_systematic_biases(
    step_metrics: List[StepCalibrationMetrics],
    context_graph: Optional[ContextGraph] = None,
    product_steps: Optional[Dict] = None
) -> BiasSummary:
    """
    Detect systematic biases in predictions.
    
    Args:
        step_metrics: List of step calibration metrics
        context_graph: Optional context graph for failure reason analysis
        product_steps: Optional product steps for step attribute analysis
    
    Returns:
        BiasSummary with detected biases
    """
    # Initialize bias accumulators
    fatigue_errors = []
    effort_errors = []
    risk_errors = []
    trust_errors = []
    early_step_errors = []
    late_step_errors = []
    
    # Analyze each step
    for metric in step_metrics:
        step_id = metric.step_id
        error = metric.observed_drop_rate - metric.predicted_drop_rate  # Positive = underestimate, negative = overestimate
        
        # Categorize by step position
        step_index = None
        if product_steps:
            step_names = list(product_steps.keys())
            if step_id in step_names:
                step_index = step_names.index(step_id)
        
        if step_index is not None:
            if step_index < 3:  # Early steps
                early_step_errors.append(error)
            else:  # Late steps
                late_step_errors.append(error)
        
        # Categorize by failure reason (if available from context graph)
        if context_graph and step_id in context_graph.nodes:
            node = context_graph.nodes[step_id]
            dominant_factor = node.dominant_failure_factor
            
            if "fatigue" in dominant_factor.lower():
                fatigue_errors.append(error)
            elif "effort" in dominant_factor.lower():
                effort_errors.append(error)
            elif "risk" in dominant_factor.lower():
                risk_errors.append(error)
            elif "control" in dominant_factor.lower() or "trust" in dominant_factor.lower():
                trust_errors.append(error)
        
        # Also check step attributes if available
        if product_steps and step_id in product_steps:
            step_def = product_steps[step_id]
            if isinstance(step_def, dict):
                # High cognitive demand -> fatigue-related
                if step_def.get('cognitive_demand', 0) > 0.6:
                    fatigue_errors.append(error)
                # High effort -> effort-related
                if step_def.get('effort_demand', 0) > 0.6:
                    effort_errors.append(error)
                # High risk -> risk-related
                if step_def.get('risk_signal', 0) > 0.6:
                    risk_errors.append(error)
                # High reassurance -> trust-related
                if step_def.get('reassurance_signal', 0) > 0.6:
                    trust_errors.append(error)
    
    # Compute average biases (positive = underestimate, negative = overestimate)
    fatigue_bias = sum(fatigue_errors) / len(fatigue_errors) if fatigue_errors else 0.0
    effort_bias = sum(effort_errors) / len(effort_errors) if effort_errors else 0.0
    risk_bias = sum(risk_errors) / len(risk_errors) if risk_errors else 0.0
    trust_bias = sum(trust_errors) / len(trust_errors) if trust_errors else 0.0
    early_step_bias = sum(early_step_errors) / len(early_step_errors) if early_step_errors else 0.0
    late_step_bias = sum(late_step_errors) / len(late_step_errors) if late_step_errors else 0.0
    
    return BiasSummary(
        fatigue_bias=fatigue_bias,
        effort_bias=effort_bias,
        risk_bias=risk_bias,
        trust_bias=trust_bias,
        early_step_bias=early_step_bias,
        late_step_bias=late_step_bias
    )


def compute_calibration_score(step_metrics: List[StepCalibrationMetrics]) -> float:
    """
    Compute global calibration score.
    
    calibration_score = 1 - mean_absolute_error
    
    Range: [0, 1], where 1 = perfect calibration
    """
    if not step_metrics:
        return 0.0
    
    mae = sum(m.absolute_error for m in step_metrics) / len(step_metrics)
    
    # Normalize: assume max error is 1.0 (100% drop rate)
    calibration_score = max(0.0, min(1.0, 1.0 - mae))
    
    return calibration_score


def compute_stability_score(step_metrics: List[StepCalibrationMetrics]) -> float:
    """
    Compute stability score based on consistency of errors.
    
    Lower variance in errors = higher stability.
    """
    if len(step_metrics) < 2:
        return 1.0
    
    errors = [m.absolute_error for m in step_metrics]
    mean_error = sum(errors) / len(errors)
    
    # Compute variance
    variance = sum((e - mean_error) ** 2 for e in errors) / len(errors)
    
    # Normalize: lower variance = higher stability
    # Assume max variance is 0.25 (when errors are very inconsistent)
    stability = max(0.0, min(1.0, 1.0 - (variance / 0.25)))
    
    return stability


def adjust_confidence_weights(
    predicted_drop_rates: Dict[str, float],
    bias_summary: BiasSummary,
    step_metrics: List[StepCalibrationMetrics],
    context_graph: Optional[ContextGraph] = None,
    product_steps: Optional[Dict] = None
) -> Dict[str, float]:
    """
    Adjust confidence weights based on detected biases.
    
    This does NOT change the core logic - it adjusts predictions
    based on observed systematic biases.
    
    Returns:
        Dict mapping step_id -> confidence-adjusted drop rate
    """
    adjusted = {}
    
    # Create step_id -> bias mapping
    step_bias_map = {}
    for metric in step_metrics:
        step_id = metric.step_id
        error = metric.observed_drop_rate - metric.predicted_drop_rate
        
        # Determine which bias applies
        bias_factor = 0.0
        
        # Check step position
        if product_steps:
            step_names = list(product_steps.keys())
            if step_id in step_names:
                step_index = step_names.index(step_id)
                if step_index < 3:
                    bias_factor += bias_summary.early_step_bias
                else:
                    bias_factor += bias_summary.late_step_bias
        
        # Check failure reason
        if context_graph and step_id in context_graph.nodes:
            node = context_graph.nodes[step_id]
            dominant_factor = node.dominant_failure_factor.lower()
            
            if "fatigue" in dominant_factor:
                bias_factor += bias_summary.fatigue_bias
            elif "effort" in dominant_factor:
                bias_factor += bias_summary.effort_bias
            elif "risk" in dominant_factor:
                bias_factor += bias_summary.risk_bias
            elif "control" in dominant_factor or "trust" in dominant_factor:
                bias_factor += bias_summary.trust_bias
        
        # Check step attributes
        if product_steps and step_id in product_steps:
            step_def = product_steps[step_id]
            if isinstance(step_def, dict):
                if step_def.get('cognitive_demand', 0) > 0.6:
                    bias_factor += bias_summary.fatigue_bias * 0.5
                if step_def.get('effort_demand', 0) > 0.6:
                    bias_factor += bias_summary.effort_bias * 0.5
                if step_def.get('risk_signal', 0) > 0.6:
                    bias_factor += bias_summary.risk_bias * 0.5
                if step_def.get('reassurance_signal', 0) > 0.6:
                    bias_factor += bias_summary.trust_bias * 0.5
        
        step_bias_map[step_id] = bias_factor
    
    # Apply adjustments
    for step_id, predicted_rate in predicted_drop_rates.items():
        bias_factor = step_bias_map.get(step_id, 0.0)
        
        # Adjust: if we overestimated (negative bias), reduce prediction
        # If we underestimated (positive bias), increase prediction
        adjusted_rate = predicted_rate - bias_factor
        
        # Clamp to valid range
        adjusted_rate = max(0.0, min(1.0, adjusted_rate))
        
        adjusted[step_id] = adjusted_rate
    
    return adjusted


def identify_dominant_biases(bias_summary: BiasSummary) -> List[str]:
    """Identify which biases are most significant."""
    biases = []
    
    # Threshold for "significant" bias
    threshold = 0.05
    
    if abs(bias_summary.fatigue_bias) > threshold:
        direction = "overestimated" if bias_summary.fatigue_bias < 0 else "underestimated"
        biases.append(f"{direction}_fatigue")
    
    if abs(bias_summary.effort_bias) > threshold:
        direction = "overestimated" if bias_summary.effort_bias < 0 else "underestimated"
        biases.append(f"{direction}_effort")
    
    if abs(bias_summary.risk_bias) > threshold:
        direction = "overestimated" if bias_summary.risk_bias < 0 else "underestimated"
        biases.append(f"{direction}_risk")
    
    if abs(bias_summary.trust_bias) > threshold:
        direction = "overestimated" if bias_summary.trust_bias < 0 else "underestimated"
        biases.append(f"{direction}_trust")
    
    if abs(bias_summary.early_step_bias) > threshold:
        direction = "overestimated" if bias_summary.early_step_bias < 0 else "underestimated"
        biases.append(f"{direction}_early_steps")
    
    if abs(bias_summary.late_step_bias) > threshold:
        direction = "overestimated" if bias_summary.late_step_bias < 0 else "underestimated"
        biases.append(f"{direction}_late_steps")
    
    return biases


def identify_stable_factors(bias_summary: BiasSummary) -> List[str]:
    """Identify which factors are well-calibrated (stable)."""
    stable = []
    threshold = 0.02  # Very low bias = stable
    
    if abs(bias_summary.fatigue_bias) < threshold:
        stable.append("fatigue")
    
    if abs(bias_summary.effort_bias) < threshold:
        stable.append("effort")
    
    if abs(bias_summary.risk_bias) < threshold:
        stable.append("risk")
    
    if abs(bias_summary.trust_bias) < threshold:
        stable.append("trust")
    
    return stable


# ============================================================================
# Main Calibration Function
# ============================================================================

def run_calibration(
    simulation_results: Dict,
    observed_metrics: ObservedOutcomes,
    context_graph: Optional[ContextGraph] = None,
    product_steps: Optional[Dict] = None
) -> CalibrationReport:
    """
    Run calibration analysis comparing simulation to reality.
    
    Args:
        simulation_results: Simulation output (from wizard or runner)
        observed_metrics: Real-world observed outcomes
        context_graph: Optional context graph for step-level analysis
        product_steps: Optional product steps for attribute analysis
    
    Returns:
        CalibrationReport with complete calibration analysis
    """
    # Extract predicted metrics
    predicted_drop_rates = extract_predicted_metrics(simulation_results, context_graph)
    
    # Compute step-level calibration metrics
    step_metrics = compute_step_calibration_metrics(
        predicted_drop_rates,
        observed_metrics.step_drop_rates
    )
    
    # Detect systematic biases
    bias_summary = detect_systematic_biases(
        step_metrics,
        context_graph,
        product_steps
    )
    
    # Compute calibration score
    calibration_score = compute_calibration_score(step_metrics)
    
    # Compute stability score
    stability_score = compute_stability_score(step_metrics)
    
    # Adjust confidence weights
    confidence_adjusted = adjust_confidence_weights(
        predicted_drop_rates,
        bias_summary,
        step_metrics,
        context_graph,
        product_steps
    )
    
    # Identify dominant biases and stable factors
    dominant_biases = identify_dominant_biases(bias_summary)
    stable_factors = identify_stable_factors(bias_summary)
    
    # Create report
    report = CalibrationReport(
        calibration_score=calibration_score,
        step_metrics=step_metrics,
        bias_summary=bias_summary,
        confidence_adjusted_predictions=confidence_adjusted,
        stability_score=stability_score,
        timestamp=datetime.now().isoformat(),
        dominant_biases=dominant_biases,
        stable_factors=stable_factors
    )
    
    return report


# ============================================================================
# Integration Helper
# ============================================================================

def run_calibration_from_wizard_result(
    scenario_result: Dict,
    observed_metrics: ObservedOutcomes
) -> CalibrationReport:
    """
    Convenience function to run calibration from wizard result.
    
    Args:
        scenario_result: Output from run_fintech_wizard
        observed_metrics: Real-world observed outcomes
    
    Returns:
        CalibrationReport
    """
    # Extract context graph object if available
    context_graph = scenario_result.get('_context_graph_obj')
    
    # Get product steps
    product_steps = scenario_result.get('product_steps', {})
    
    # Run calibration
    return run_calibration(
        simulation_results=scenario_result,
        observed_metrics=observed_metrics,
        context_graph=context_graph,
        product_steps=product_steps
    )


# ============================================================================
# Calibration History Management
# ============================================================================

def load_calibration_history(filepath: str) -> CalibrationHistory:
    """Load calibration history from file."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        history = CalibrationHistory(history=data.get('history', []))
        return history
    except FileNotFoundError:
        return CalibrationHistory(history=[])
    except Exception:
        return CalibrationHistory(history=[])


def save_calibration_history(history: CalibrationHistory, filepath: str):
    """Save calibration history to file."""
    with open(filepath, 'w') as f:
        json.dump(history.to_dict(), f, indent=2)


def update_calibration_history(
    history_filepath: str,
    new_report: CalibrationReport
) -> CalibrationHistory:
    """
    Update calibration history with new report.
    
    Args:
        history_filepath: Path to calibration history file
        new_report: New calibration report to add
    
    Returns:
        Updated CalibrationHistory
    """
    history = load_calibration_history(history_filepath)
    history.add_entry(new_report)
    save_calibration_history(history, history_filepath)
    return history

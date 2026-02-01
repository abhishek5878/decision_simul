"""
drift_metrics.py - Model Drift Detection Metrics

Detects drift between current predictions and historical baselines.
Measures drift in entry rates, completion rates, and parameter values.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class DriftSeverity(Enum):
    """Drift severity classification."""
    STABLE = "stable"  # < 5% change
    WARNING = "warning"  # 5-15% change
    CRITICAL = "critical"  # > 15% change


@dataclass
class DriftMetric:
    """Single drift metric result."""
    metric_name: str
    baseline_value: float
    current_value: float
    absolute_change: float
    relative_change_pct: float
    severity: DriftSeverity
    threshold_warning: float = 5.0  # 5% warning threshold
    threshold_critical: float = 15.0  # 15% critical threshold
    
    def __post_init__(self):
        """Classify severity based on relative change."""
        abs_change_pct = abs(self.relative_change_pct)
        if abs_change_pct < self.threshold_warning:
            self.severity = DriftSeverity.STABLE
        elif abs_change_pct < self.threshold_critical:
            self.severity = DriftSeverity.WARNING
        else:
            self.severity = DriftSeverity.CRITICAL
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'metric_name': self.metric_name,
            'baseline_value': float(self.baseline_value),
            'current_value': float(self.current_value),
            'absolute_change': float(self.absolute_change),
            'relative_change_pct': float(self.relative_change_pct),
            'severity': self.severity.value,
            'threshold_warning': float(self.threshold_warning),
            'threshold_critical': float(self.threshold_critical)
        }


@dataclass
class DriftSummary:
    """Summary of drift across all metrics."""
    overall_severity: DriftSeverity
    metrics: List[DriftMetric]
    stable_count: int
    warning_count: int
    critical_count: int
    timestamp: str
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'overall_severity': self.overall_severity.value,
            'metrics': [m.to_dict() for m in self.metrics],
            'stable_count': self.stable_count,
            'warning_count': self.warning_count,
            'critical_count': self.critical_count,
            'timestamp': self.timestamp
        }


# ============================================================================
# DRIFT DETECTION FUNCTIONS
# ============================================================================

def compute_relative_change(baseline: float, current: float) -> Tuple[float, float]:
    """
    Compute absolute and relative change between baseline and current.
    
    Args:
        baseline: Baseline value
        current: Current value
    
    Returns:
        Tuple of (absolute_change, relative_change_pct)
    """
    absolute_change = current - baseline
    
    if baseline == 0:
        # Handle zero baseline
        if current == 0:
            relative_change_pct = 0.0
        else:
            relative_change_pct = 100.0 if current > 0 else -100.0
    else:
        relative_change_pct = (absolute_change / baseline) * 100.0
    
    return absolute_change, relative_change_pct


def detect_entry_rate_drift(
    baseline_entry_rate: float,
    current_entry_rate: float,
    threshold_warning: float = 5.0,
    threshold_critical: float = 15.0
) -> DriftMetric:
    """
    Detect drift in entry rate.
    
    Args:
        baseline_entry_rate: Historical baseline entry rate
        current_entry_rate: Current entry rate
        threshold_warning: Warning threshold (%)
        threshold_critical: Critical threshold (%)
    
    Returns:
        DriftMetric for entry rate
    """
    abs_change, rel_change_pct = compute_relative_change(
        baseline_entry_rate,
        current_entry_rate
    )
    
    metric = DriftMetric(
        metric_name='entry_rate',
        baseline_value=baseline_entry_rate,
        current_value=current_entry_rate,
        absolute_change=abs_change,
        relative_change_pct=rel_change_pct,
        severity=DriftSeverity.STABLE,  # Will be set in __post_init__
        threshold_warning=threshold_warning,
        threshold_critical=threshold_critical
    )
    
    return metric


def detect_completion_rate_drift(
    baseline_completion_rate: float,
    current_completion_rate: float,
    threshold_warning: float = 5.0,
    threshold_critical: float = 15.0
) -> DriftMetric:
    """
    Detect drift in completion rate.
    
    Args:
        baseline_completion_rate: Historical baseline completion rate
        current_completion_rate: Current completion rate
        threshold_warning: Warning threshold (%)
        threshold_critical: Critical threshold (%)
    
    Returns:
        DriftMetric for completion rate
    """
    abs_change, rel_change_pct = compute_relative_change(
        baseline_completion_rate,
        current_completion_rate
    )
    
    metric = DriftMetric(
        metric_name='completion_rate',
        baseline_value=baseline_completion_rate,
        current_value=current_completion_rate,
        absolute_change=abs_change,
        relative_change_pct=rel_change_pct,
        severity=DriftSeverity.STABLE,  # Will be set in __post_init__
        threshold_warning=threshold_warning,
        threshold_critical=threshold_critical
    )
    
    return metric


def detect_total_conversion_drift(
    baseline_total_conversion: float,
    current_total_conversion: float,
    threshold_warning: float = 5.0,
    threshold_critical: float = 15.0
) -> DriftMetric:
    """
    Detect drift in total conversion rate (entry × completion).
    
    Args:
        baseline_total_conversion: Historical baseline total conversion
        current_total_conversion: Current total conversion
        threshold_warning: Warning threshold (%)
        threshold_critical: Critical threshold (%)
    
    Returns:
        DriftMetric for total conversion
    """
    abs_change, rel_change_pct = compute_relative_change(
        baseline_total_conversion,
        current_total_conversion
    )
    
    metric = DriftMetric(
        metric_name='total_conversion',
        baseline_value=baseline_total_conversion,
        current_value=current_total_conversion,
        absolute_change=abs_change,
        relative_change_pct=rel_change_pct,
        severity=DriftSeverity.STABLE,  # Will be set in __post_init__
        threshold_warning=threshold_warning,
        threshold_critical=threshold_critical
    )
    
    return metric


def detect_step_level_drift(
    baseline_step_rates: Dict[str, float],
    current_step_rates: Dict[str, float],
    threshold_warning: float = 5.0,
    threshold_critical: float = 15.0
) -> List[DriftMetric]:
    """
    Detect drift in step-level completion rates.
    
    Args:
        baseline_step_rates: Historical baseline step completion rates
        current_step_rates: Current step completion rates
        threshold_warning: Warning threshold (%)
        threshold_critical: Critical threshold (%)
    
    Returns:
        List of DriftMetrics for each step
    """
    metrics = []
    
    # Check all steps that exist in either baseline or current
    all_steps = set(baseline_step_rates.keys()) | set(current_step_rates.keys())
    
    for step_name in all_steps:
        baseline_rate = baseline_step_rates.get(step_name, 0.0)
        current_rate = current_step_rates.get(step_name, 0.0)
        
        abs_change, rel_change_pct = compute_relative_change(
            baseline_rate,
            current_rate
        )
        
        metric = DriftMetric(
            metric_name=f'step_{step_name}',
            baseline_value=baseline_rate,
            current_value=current_rate,
            absolute_change=abs_change,
            relative_change_pct=rel_change_pct,
            severity=DriftSeverity.STABLE,  # Will be set in __post_init__
            threshold_warning=threshold_warning,
            threshold_critical=threshold_critical
        )
        
        metrics.append(metric)
    
    return metrics


def detect_parameter_drift(
    baseline_parameters: Dict[str, float],
    current_parameters: Dict[str, float],
    threshold_warning: float = 5.0,
    threshold_critical: float = 15.0
) -> List[DriftMetric]:
    """
    Detect drift in calibrated parameters.
    
    Args:
        baseline_parameters: Historical baseline parameter values
        current_parameters: Current parameter values
        threshold_warning: Warning threshold (%)
        threshold_critical: Critical threshold (%)
    
    Returns:
        List of DriftMetrics for each parameter
    """
    metrics = []
    
    # Check all parameters that exist in either baseline or current
    all_params = set(baseline_parameters.keys()) | set(current_parameters.keys())
    
    for param_name in all_params:
        baseline_val = baseline_parameters.get(param_name, 0.0)
        current_val = current_parameters.get(param_name, 0.0)
        
        abs_change, rel_change_pct = compute_relative_change(
            baseline_val,
            current_val
        )
        
        metric = DriftMetric(
            metric_name=f'parameter_{param_name}',
            baseline_value=baseline_val,
            current_value=current_val,
            absolute_change=abs_change,
            relative_change_pct=rel_change_pct,
            severity=DriftSeverity.STABLE,  # Will be set in __post_init__
            threshold_warning=threshold_warning,
            threshold_critical=threshold_critical
        )
        
        metrics.append(metric)
    
    return metrics


def compute_overall_drift_severity(metrics: List[DriftMetric]) -> DriftSeverity:
    """
    Compute overall drift severity from list of metrics.
    
    Uses worst-case severity: if any metric is critical, overall is critical.
    If any metric is warning, overall is warning. Otherwise stable.
    
    Args:
        metrics: List of drift metrics
    
    Returns:
        Overall drift severity
    """
    if not metrics:
        return DriftSeverity.STABLE
    
    severities = [m.severity for m in metrics]
    
    if DriftSeverity.CRITICAL in severities:
        return DriftSeverity.CRITICAL
    elif DriftSeverity.WARNING in severities:
        return DriftSeverity.WARNING
    else:
        return DriftSeverity.STABLE


def summarize_drift(metrics: List[DriftMetric]) -> DriftSummary:
    """
    Summarize drift across all metrics.
    
    Args:
        metrics: List of drift metrics
    
    Returns:
        DriftSummary with overall severity and counts
    """
    overall_severity = compute_overall_drift_severity(metrics)
    
    stable_count = sum(1 for m in metrics if m.severity == DriftSeverity.STABLE)
    warning_count = sum(1 for m in metrics if m.severity == DriftSeverity.WARNING)
    critical_count = sum(1 for m in metrics if m.severity == DriftSeverity.CRITICAL)
    
    return DriftSummary(
        overall_severity=overall_severity,
        metrics=metrics,
        stable_count=stable_count,
        warning_count=warning_count,
        critical_count=critical_count,
        timestamp=datetime.now().isoformat()
    )


# ============================================================================
# STATISTICAL DRIFT TESTS
# ============================================================================

def compute_kl_divergence(
    baseline_distribution: np.ndarray,
    current_distribution: np.ndarray,
    epsilon: float = 1e-10
) -> float:
    """
    Compute Kullback-Leibler divergence between distributions.
    
    Args:
        baseline_distribution: Baseline probability distribution
        current_distribution: Current probability distribution
        epsilon: Small value to avoid log(0)
    
    Returns:
        KL divergence value
    """
    # Normalize distributions
    baseline_norm = baseline_distribution / (baseline_distribution.sum() + epsilon)
    current_norm = current_distribution / (current_distribution.sum() + epsilon)
    
    # Add epsilon to avoid log(0)
    baseline_norm = baseline_norm + epsilon
    current_norm = current_norm + epsilon
    
    # Normalize again
    baseline_norm = baseline_norm / baseline_norm.sum()
    current_norm = current_norm / current_norm.sum()
    
    # Compute KL divergence
    kl = np.sum(baseline_norm * np.log(baseline_norm / current_norm))
    
    return float(kl)


def compute_js_divergence(
    baseline_distribution: np.ndarray,
    current_distribution: np.ndarray
) -> float:
    """
    Compute Jensen-Shannon divergence (symmetric version of KL).
    
    Args:
        baseline_distribution: Baseline probability distribution
        current_distribution: Current probability distribution
    
    Returns:
        JS divergence value (0-1, where 1 = completely different)
    """
    # Normalize distributions
    baseline_norm = baseline_distribution / (baseline_distribution.sum() + 1e-10)
    current_norm = current_distribution / (current_distribution.sum() + 1e-10)
    
    # Compute average distribution
    avg_dist = (baseline_norm + current_norm) / 2.0
    
    # Compute KL divergences
    kl_baseline = compute_kl_divergence(baseline_norm, avg_dist)
    kl_current = compute_kl_divergence(current_norm, avg_dist)
    
    # JS divergence is average of the two KL divergences
    js = (kl_baseline + kl_current) / 2.0
    
    return float(js)


def detect_distribution_drift(
    baseline_distribution: Dict[str, float],
    current_distribution: Dict[str, float],
    method: str = 'js_divergence'
) -> Dict:
    """
    Detect drift in probability distributions (e.g., step drop-off distribution).
    
    Args:
        baseline_distribution: Baseline distribution
        current_distribution: Current distribution
        method: Method to use ('js_divergence' or 'kl_divergence')
    
    Returns:
        Dict with drift metrics
    """
    # Get all keys
    all_keys = set(baseline_distribution.keys()) | set(current_distribution.keys())
    
    # Create arrays in same order
    baseline_array = np.array([baseline_distribution.get(k, 0.0) for k in all_keys])
    current_array = np.array([current_distribution.get(k, 0.0) for k in all_keys])
    
    # Compute divergence
    if method == 'js_divergence':
        divergence = compute_js_divergence(baseline_array, current_array)
    else:
        divergence = compute_kl_divergence(baseline_array, current_array)
    
    # Classify severity
    if divergence < 0.1:
        severity = DriftSeverity.STABLE
    elif divergence < 0.3:
        severity = DriftSeverity.WARNING
    else:
        severity = DriftSeverity.CRITICAL
    
    return {
        'divergence': divergence,
        'method': method,
        'severity': severity.value,
        'baseline_distribution': {k: float(v) for k, v in baseline_distribution.items()},
        'current_distribution': {k: float(v) for k, v in current_distribution.items()}
    }


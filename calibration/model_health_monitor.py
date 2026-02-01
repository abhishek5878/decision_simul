"""
model_health_monitor.py - Model Health and Drift Monitoring

Monitors model health by detecting drift between current predictions
and historical baselines. Answers: "Is this model still valid?"
"""

import json
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from calibration.drift_metrics import (
    DriftMetric,
    DriftSeverity,
    DriftSummary,
    detect_entry_rate_drift,
    detect_completion_rate_drift,
    detect_total_conversion_drift,
    detect_step_level_drift,
    detect_parameter_drift,
    detect_distribution_drift,
    summarize_drift
)


@dataclass
class ModelBaseline:
    """Historical baseline for model performance."""
    entry_rate: float
    completion_rate: float
    total_conversion: float
    step_completion_rates: Dict[str, float]
    parameters: Dict[str, float]
    dropoff_distribution: Dict[str, float]
    timestamp: str
    sample_size: int
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'entry_rate': float(self.entry_rate),
            'completion_rate': float(self.completion_rate),
            'total_conversion': float(self.total_conversion),
            'step_completion_rates': {k: float(v) for k, v in self.step_completion_rates.items()},
            'parameters': {k: float(v) for k, v in self.parameters.items()},
            'dropoff_distribution': {k: float(v) for k, v in self.dropoff_distribution.items()},
            'timestamp': self.timestamp,
            'sample_size': self.sample_size
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ModelBaseline':
        """Create from dict."""
        return cls(
            entry_rate=data['entry_rate'],
            completion_rate=data['completion_rate'],
            total_conversion=data['total_conversion'],
            step_completion_rates=data['step_completion_rates'],
            parameters=data['parameters'],
            dropoff_distribution=data['dropoff_distribution'],
            timestamp=data['timestamp'],
            sample_size=data.get('sample_size', 0)
        )


@dataclass
class CurrentModelState:
    """Current model predictions/state."""
    entry_rate: float
    completion_rate: float
    total_conversion: float
    step_completion_rates: Dict[str, float]
    parameters: Dict[str, float]
    dropoff_distribution: Dict[str, float]
    timestamp: str
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'entry_rate': float(self.entry_rate),
            'completion_rate': float(self.completion_rate),
            'total_conversion': float(self.total_conversion),
            'step_completion_rates': {k: float(v) for k, v in self.step_completion_rates.items()},
            'parameters': {k: float(v) for k, v in self.parameters.items()},
            'dropoff_distribution': {k: float(v) for k, v in self.dropoff_distribution.items()},
            'timestamp': self.timestamp
        }


@dataclass
class DriftReport:
    """Complete drift monitoring report."""
    overall_severity: str
    overall_status: str  # "valid" or "needs_recalibration"
    drift_summary: DriftSummary
    entry_rate_drift: DriftMetric
    completion_rate_drift: DriftMetric
    total_conversion_drift: DriftMetric
    step_drifts: List[DriftMetric]
    parameter_drifts: List[DriftMetric]
    distribution_drift: Dict
    baseline: ModelBaseline
    current: CurrentModelState
    recommendations: List[str]
    timestamp: str
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'overall_severity': self.overall_severity,
            'overall_status': self.overall_status,
            'drift_summary': self.drift_summary.to_dict(),
            'entry_rate_drift': self.entry_rate_drift.to_dict(),
            'completion_rate_drift': self.completion_rate_drift.to_dict(),
            'total_conversion_drift': self.total_conversion_drift.to_dict(),
            'step_drifts': [m.to_dict() for m in self.step_drifts],
            'parameter_drifts': [m.to_dict() for m in self.parameter_drifts],
            'distribution_drift': self.distribution_drift,
            'baseline': self.baseline.to_dict(),
            'current': self.current.to_dict(),
            'recommendations': self.recommendations,
            'timestamp': self.timestamp
        }


class ModelHealthMonitor:
    """Monitor model health and detect drift."""
    
    def __init__(
        self,
        baseline_file: Optional[str] = None,
        threshold_warning: float = 5.0,
        threshold_critical: float = 15.0
    ):
        """
        Initialize model health monitor.
        
        Args:
            baseline_file: Path to baseline JSON file
            threshold_warning: Warning threshold for drift (%)
            threshold_critical: Critical threshold for drift (%)
        """
        self.baseline_file = baseline_file
        self.threshold_warning = threshold_warning
        self.threshold_critical = threshold_critical
        self.baseline: Optional[ModelBaseline] = None
        
        if baseline_file and Path(baseline_file).exists():
            self.load_baseline(baseline_file)
    
    def load_baseline(self, filepath: str) -> ModelBaseline:
        """Load baseline from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.baseline = ModelBaseline.from_dict(data)
        return self.baseline
    
    def save_baseline(self, baseline: ModelBaseline, filepath: str):
        """Save baseline to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(baseline.to_dict(), f, indent=2)
    
    def create_baseline_from_simulation(
        self,
        entry_rate: float,
        completion_rate: float,
        total_conversion: float,
        step_completion_rates: Dict[str, float],
        parameters: Dict[str, float],
        dropoff_distribution: Dict[str, float],
        sample_size: int = 0
    ) -> ModelBaseline:
        """
        Create baseline from simulation results.
        
        Args:
            entry_rate: Entry probability
            completion_rate: Completion probability (conditional on entry)
            total_conversion: Total conversion (entry × completion)
            step_completion_rates: Step-level completion rates
            parameters: Calibrated parameters
            dropoff_distribution: Drop-off distribution by step
            sample_size: Sample size used for baseline
        
        Returns:
            ModelBaseline object
        """
        baseline = ModelBaseline(
            entry_rate=entry_rate,
            completion_rate=completion_rate,
            total_conversion=total_conversion,
            step_completion_rates=step_completion_rates,
            parameters=parameters,
            dropoff_distribution=dropoff_distribution,
            timestamp=datetime.now().isoformat(),
            sample_size=sample_size
        )
        
        self.baseline = baseline
        return baseline
    
    def monitor_drift(
        self,
        current_entry_rate: float,
        current_completion_rate: float,
        current_total_conversion: float,
        current_step_completion_rates: Dict[str, float],
        current_parameters: Dict[str, float],
        current_dropoff_distribution: Dict[str, float]
    ) -> DriftReport:
        """
        Monitor drift between current state and baseline.
        
        Args:
            current_entry_rate: Current entry probability
            current_completion_rate: Current completion probability
            current_total_conversion: Current total conversion
            current_step_completion_rates: Current step completion rates
            current_parameters: Current parameter values
            current_dropoff_distribution: Current drop-off distribution
        
        Returns:
            DriftReport with all drift metrics
        """
        if self.baseline is None:
            raise ValueError("No baseline loaded. Create or load a baseline first.")
        
        # Create current state
        current_state = CurrentModelState(
            entry_rate=current_entry_rate,
            completion_rate=current_completion_rate,
            total_conversion=current_total_conversion,
            step_completion_rates=current_step_completion_rates,
            parameters=current_parameters,
            dropoff_distribution=current_dropoff_distribution,
            timestamp=datetime.now().isoformat()
        )
        
        # Detect drifts
        entry_drift = detect_entry_rate_drift(
            self.baseline.entry_rate,
            current_entry_rate,
            self.threshold_warning,
            self.threshold_critical
        )
        
        completion_drift = detect_completion_rate_drift(
            self.baseline.completion_rate,
            current_completion_rate,
            self.threshold_warning,
            self.threshold_critical
        )
        
        total_drift = detect_total_conversion_drift(
            self.baseline.total_conversion,
            current_total_conversion,
            self.threshold_warning,
            self.threshold_critical
        )
        
        step_drifts = detect_step_level_drift(
            self.baseline.step_completion_rates,
            current_step_completion_rates,
            self.threshold_warning,
            self.threshold_critical
        )
        
        # Only detect parameter drift for calibratable parameters
        # (exclude non-calibratable parameters that might have different defaults)
        from calibration.real_world_calibration import CALIBRATABLE_PARAMETERS
        
        baseline_calibratable = {
            k: v for k, v in self.baseline.parameters.items()
            if k in CALIBRATABLE_PARAMETERS
        }
        current_calibratable = {
            k: v for k, v in current_parameters.items()
            if k in CALIBRATABLE_PARAMETERS
        }
        
        parameter_drifts = detect_parameter_drift(
            baseline_calibratable,
            current_calibratable,
            self.threshold_warning,
            self.threshold_critical
        )
        
        distribution_drift = detect_distribution_drift(
            self.baseline.dropoff_distribution,
            current_dropoff_distribution,
            method='js_divergence'
        )
        
        # Collect all metrics
        all_metrics = [
            entry_drift,
            completion_drift,
            total_drift
        ]
        all_metrics.extend(step_drifts)
        all_metrics.extend(parameter_drifts)
        
        # Create summary
        drift_summary = summarize_drift(all_metrics)
        
        # Determine overall status
        overall_severity = drift_summary.overall_severity.value
        if overall_severity == 'critical':
            overall_status = 'needs_recalibration'
        elif overall_severity == 'warning':
            overall_status = 'monitor_closely'
        else:
            overall_status = 'valid'
        
        # Generate recommendations
        recommendations = self._generate_recommendations(drift_summary, distribution_drift)
        
        # Create report
        report = DriftReport(
            overall_severity=overall_severity,
            overall_status=overall_status,
            drift_summary=drift_summary,
            entry_rate_drift=entry_drift,
            completion_rate_drift=completion_drift,
            total_conversion_drift=total_drift,
            step_drifts=step_drifts,
            parameter_drifts=parameter_drifts,
            distribution_drift=distribution_drift,
            baseline=self.baseline,
            current=current_state,
            recommendations=recommendations,
            timestamp=datetime.now().isoformat()
        )
        
        return report
    
    def _generate_recommendations(
        self,
        drift_summary: DriftSummary,
        distribution_drift: Dict
    ) -> List[str]:
        """Generate recommendations based on drift."""
        recommendations = []
        
        if drift_summary.overall_severity == DriftSeverity.CRITICAL:
            recommendations.append("🚨 CRITICAL: Model shows significant drift. Recalibration required immediately.")
            recommendations.append("   - Review recent changes to product or user base")
            recommendations.append("   - Run full calibration with latest observed data")
            recommendations.append("   - Validate new parameters on holdout set")
        elif drift_summary.overall_severity == DriftSeverity.WARNING:
            recommendations.append("⚠️  WARNING: Model shows moderate drift. Monitor closely.")
            recommendations.append("   - Investigate causes of drift")
            recommendations.append("   - Consider recalibration if drift persists")
            recommendations.append("   - Review parameter changes")
        else:
            recommendations.append("✅ Model is stable. No immediate action required.")
            recommendations.append("   - Continue monitoring")
            recommendations.append("   - Schedule periodic recalibration")
        
        # Specific recommendations based on metrics
        critical_metrics = [m for m in drift_summary.metrics if m.severity == DriftSeverity.CRITICAL]
        if critical_metrics:
            recommendations.append(f"\nCritical drifts detected in:")
            for metric in critical_metrics[:3]:  # Top 3
                recommendations.append(f"   - {metric.metric_name}: {metric.relative_change_pct:+.1f}%")
        
        if distribution_drift['severity'] == 'critical':
            recommendations.append(f"\n⚠️  Distribution drift detected (JS divergence: {distribution_drift['divergence']:.3f})")
            recommendations.append("   - Step drop-off pattern has changed significantly")
            recommendations.append("   - May indicate product changes or user behavior shifts")
        
        return recommendations
    
    def export_drift_report(self, report: DriftReport, filepath: str = 'drift_report.json'):
        """Export drift report to JSON."""
        with open(filepath, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
        
        return filepath
    
    def print_drift_report(self, report: DriftReport):
        """Print human-readable drift report."""
        print("\n" + "=" * 80)
        print("MODEL HEALTH MONITORING REPORT")
        print("=" * 80)
        print(f"\nOverall Status: {report.overall_status.upper()}")
        print(f"Overall Severity: {report.overall_severity.upper()}")
        print(f"Timestamp: {report.timestamp}")
        
        print(f"\n📊 Drift Summary:")
        print(f"   Stable metrics: {report.drift_summary.stable_count}")
        print(f"   Warning metrics: {report.drift_summary.warning_count}")
        print(f"   Critical metrics: {report.drift_summary.critical_count}")
        
        print(f"\n📈 Key Metrics:")
        print(f"   Entry Rate:")
        print(f"     Baseline: {report.baseline.entry_rate:.2%}")
        print(f"     Current:  {report.current.entry_rate:.2%}")
        print(f"     Change:   {report.entry_rate_drift.relative_change_pct:+.1f}% ({report.entry_rate_drift.severity.value})")
        
        print(f"   Completion Rate:")
        print(f"     Baseline: {report.baseline.completion_rate:.2%}")
        print(f"     Current:  {report.current.completion_rate:.2%}")
        print(f"     Change:   {report.completion_rate_drift.relative_change_pct:+.1f}% ({report.completion_rate_drift.severity.value})")
        
        print(f"   Total Conversion:")
        print(f"     Baseline: {report.baseline.total_conversion:.2%}")
        print(f"     Current:  {report.current.total_conversion:.2%}")
        print(f"     Change:   {report.total_conversion_drift.relative_change_pct:+.1f}% ({report.total_conversion_drift.severity.value})")
        
        # Show critical drifts
        critical_drifts = [m for m in report.drift_summary.metrics if m.severity == DriftSeverity.CRITICAL]
        if critical_drifts:
            print(f"\n🚨 Critical Drifts:")
            for metric in critical_drifts[:5]:  # Top 5
                print(f"   {metric.metric_name}: {metric.relative_change_pct:+.1f}%")
        
        # Distribution drift
        if report.distribution_drift['severity'] != 'stable':
            print(f"\n📊 Distribution Drift:")
            print(f"   JS Divergence: {report.distribution_drift['divergence']:.3f}")
            print(f"   Severity: {report.distribution_drift['severity']}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        for rec in report.recommendations:
            print(f"   {rec}")
        
        print("\n" + "=" * 80)
        print(f"Answer: {'❌ Model needs recalibration' if report.overall_status == 'needs_recalibration' else '✅ Model is valid'}")
        print("=" * 80 + "\n")


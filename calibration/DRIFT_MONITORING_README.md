# Model Drift and Health Monitoring

## 🎯 Purpose

Monitors model health by detecting drift between current predictions and historical baselines. Answers the critical question:

**"Is this model still valid, or does it need recalibration?"**

## 📊 What It Does

1. **Detects drift** in entry rates, completion rates, and parameter values
2. **Measures step-level drift** to identify where behavior has changed
3. **Classifies drift severity** (stable / warning / critical)
4. **Generates recommendations** for model maintenance
5. **Outputs diagnostics** (human-readable and machine-readable)

## 🔧 Components

### 1. `drift_metrics.py`
Core drift detection functions:
- Entry rate drift detection
- Completion rate drift detection
- Step-level drift detection
- Parameter value drift detection
- Distribution drift detection (KL/JS divergence)

### 2. `model_health_monitor.py`
Main monitoring orchestrator:
- Baseline management (load/save)
- Drift monitoring
- Report generation
- Recommendations

### 3. Output Artifacts
- `drift_report.json` - Machine-readable drift report
- `baseline.json` - Historical baseline for comparison

## 🚀 Usage

### Basic Usage

```python
from calibration import ModelHealthMonitor

# Initialize monitor
monitor = ModelHealthMonitor(
    baseline_file='baseline.json',
    threshold_warning=5.0,  # 5% warning threshold
    threshold_critical=15.0  # 15% critical threshold
)

# Monitor drift
report = monitor.monitor_drift(
    current_entry_rate=0.35,
    current_completion_rate=0.77,
    current_total_conversion=0.27,
    current_step_completion_rates={...},
    current_parameters={...},
    current_dropoff_distribution={...}
)

# Print report
monitor.print_drift_report(report)

# Export report
monitor.export_drift_report(report, 'drift_report.json')
```

### Creating a Baseline

```python
from calibration import ModelHealthMonitor

monitor = ModelHealthMonitor()

# Create baseline from simulation results
baseline = monitor.create_baseline_from_simulation(
    entry_rate=0.55,
    completion_rate=0.77,
    total_conversion=0.42,
    step_completion_rates={'Step 1': 0.95, ...},
    parameters={'BASE_COMPLETION_RATE': 0.60, ...},
    dropoff_distribution={'Step 1': 0.05, ...},
    sample_size=1000
)

# Save baseline
monitor.save_baseline(baseline, 'baseline.json')
```

### Running Monitoring

```bash
python3 calibration/run_drift_monitoring.py
```

## 📊 Drift Severity Classification

### Stable (< 5% change)
- Model is performing as expected
- No immediate action required
- Continue monitoring

### Warning (5-15% change)
- Moderate drift detected
- Investigate causes
- Consider recalibration if drift persists

### Critical (> 15% change)
- Significant drift detected
- Recalibration required immediately
- Review recent changes to product/user base

## 📈 Output Format

### `drift_report.json`
```json
{
  "overall_severity": "warning",
  "overall_status": "monitor_closely",
  "drift_summary": {
    "overall_severity": "warning",
    "stable_count": 8,
    "warning_count": 2,
    "critical_count": 0
  },
  "entry_rate_drift": {
    "metric_name": "entry_rate",
    "baseline_value": 0.55,
    "current_value": 0.50,
    "relative_change_pct": -9.1,
    "severity": "warning"
  },
  "completion_rate_drift": {...},
  "step_drifts": [...],
  "parameter_drifts": [...],
  "recommendations": [
    "⚠️  WARNING: Model shows moderate drift. Monitor closely.",
    "   - Investigate causes of drift",
    "   - Consider recalibration if drift persists"
  ]
}
```

### Human-Readable Output
```
================================================================================
MODEL HEALTH MONITORING REPORT
================================================================================

Overall Status: MONITOR_CLOSELY
Overall Severity: WARNING

📊 Drift Summary:
   Stable metrics: 8
   Warning metrics: 2
   Critical metrics: 0

📈 Key Metrics:
   Entry Rate:
     Baseline: 55.00%
     Current:  50.00%
     Change:   -9.1% (warning)

   Completion Rate:
     Baseline: 77.00%
     Current:  75.00%
     Change:   -2.6% (stable)

💡 Recommendations:
   ⚠️  WARNING: Model shows moderate drift. Monitor closely.
      - Investigate causes of drift
      - Consider recalibration if drift persists

================================================================================
Answer: ✅ Model is valid
================================================================================
```

## 🔍 What Gets Monitored

1. **Entry Rate** - Probability user enters funnel
2. **Completion Rate** - Probability user completes (conditional on entry)
3. **Total Conversion** - Entry × Completion
4. **Step-Level Rates** - Completion rate for each step
5. **Parameter Values** - Calibrated parameter values
6. **Drop-off Distribution** - Distribution of drop-offs across steps

## ✅ Key Features

✅ **No Core Logic Changes**
- Monitoring layer is separate
- Does not modify behavioral logic
- Does not modify calibration logic

✅ **Reversible**
- Baseline can be updated
- Historical baselines preserved
- Can compare multiple baselines

✅ **Actionable**
- Clear severity classification
- Specific recommendations
- Identifies which metrics are drifting

✅ **Production-Ready**
- Machine-readable JSON output
- Human-readable diagnostics
- Timestamped reports

## 🎯 Use Cases

### 1. Periodic Health Checks
Run weekly/monthly to check if model is still valid.

### 2. Post-Deployment Monitoring
After deploying new features, check if model predictions still match.

### 3. Parameter Drift Detection
Monitor if calibrated parameters are drifting over time.

### 4. Product Change Impact
After product changes, check if model needs recalibration.

## 💡 Recommendations

The system generates specific recommendations:

- **Stable**: Continue monitoring, schedule periodic recalibration
- **Warning**: Investigate causes, consider recalibration if persists
- **Critical**: Recalibrate immediately, review recent changes

## 🔄 Integration

The monitoring layer integrates seamlessly:

1. **Uses existing simulation results** - No changes to simulation
2. **Uses existing calibration outputs** - Reads calibration summaries
3. **Independent operation** - Can run separately from simulation

## 📊 Example: Credigo SS Monitoring

```bash
# First run: Create baseline
python3 calibration/run_drift_monitoring.py
# Output: Baseline created and saved

# Later runs: Monitor drift
python3 calibration/run_drift_monitoring.py
# Output: Drift report with recommendations
```

---

**This monitoring layer ensures your model remains valid and production-ready over time.**


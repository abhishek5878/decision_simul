# Model Evaluation Layer

Comprehensive evaluation layer that assesses model reliability, confidence, and stability without modifying model behavior.

## 🎯 Purpose

Answers key questions:
- **"How much should we trust these predictions?"**
- **"Where do they break down?"**
- **"Which assumptions matter most?"**
- **"If this changes slightly, what breaks?"**

## 📊 Components

### 1. Confidence Interval Estimation
Runs N stochastic simulations to estimate prediction variance:

```python
from calibration import estimate_confidence_intervals

confidence = estimate_confidence_intervals(
    simulation_function=run_behavioral_simulation_improved,
    simulation_args={'df': df, 'product_steps': steps, ...},
    n_simulations=50
)

print(f"Mean: {confidence.mean_completion:.2%}")
print(f"90% CI: [{confidence.p10:.2%}, {confidence.p90:.2%}]")
print(f"Stability: {confidence.stability_score:.4f}")
```

**Output:**
- Mean completion rate
- Percentiles (p10, p25, p50, p75, p90)
- Variance and standard deviation
- Stability score (1 - normalized variance)

### 2. Sensitivity Analysis
Varies parameters ±20% and measures impact:

```python
from calibration import analyze_all_parameter_sensitivities

sensitivity = analyze_all_parameter_sensitivities(
    baseline_parameters=calibrated_params,
    simulation_function=run_behavioral_simulation_improved,
    simulation_args={'df': df, 'product_steps': steps, ...},
    product_steps=steps,
    variation_pct=0.20
)

# Get summary
from calibration import compute_sensitivity_summary
summary = compute_sensitivity_summary(sensitivity)
print(summary)  # {'persistence_bonus': 0.31, 'intent_penalty': 0.18, ...}
```

**Output:**
- Sensitivity for each parameter (relative sensitivity)
- Ranked by impact
- Identifies which assumptions actually matter

### 3. Prediction Intervals
Get confidence bands for predictions:

```python
from calibration import get_prediction_interval

interval = get_prediction_interval(
    confidence_estimate=confidence,
    confidence=0.90  # 90% confidence
)

print(f"90% Prediction Interval: [{interval.lower_bound:.2%}, {interval.upper_bound:.2%}]")
print(f"Median: {interval.median:.2%}")
```

**Output:**
- Lower bound, median, upper bound
- At specified confidence level (e.g., 90%, 95%)

### 4. Stability Score
Single scalar metric for model reliability:

```python
from calibration import assess_stability

stability = assess_stability(confidence)
print(f"Stability: {stability.stability_score:.4f} ({stability.interpretation})")
```

**Interpretation:**
- `> 0.8` → **very stable**
- `0.5-0.8` → **moderately sensitive**
- `< 0.5` → **unstable / overfitted**

### 5. Comprehensive Evaluation
Run all evaluations at once:

```python
from calibration import evaluate_model, export_evaluation_report

report = evaluate_model(
    simulation_function=run_behavioral_simulation_improved,
    simulation_args={'df': df, 'product_steps': steps, ...},
    product_steps=steps,
    baseline_parameters=calibrated_params,
    n_stochastic_runs=50,
    confidence_level=0.90,
    verbose=True
)

# Export all reports
export_evaluation_report(report, 'evaluation_report.json')
export_calibration_report(report, 'calibration_report.json')
export_sensitivity_report(report, 'sensitivity_report.json')
export_confidence_intervals(report, 'confidence_intervals.json')
```

## 📄 Output Artifacts

### `calibration_report.json`
Confidence intervals and stability metrics:
```json
{
  "overall_confidence": {
    "mean_completion": 0.27,
    "p10": 0.18,
    "p50": 0.26,
    "p90": 0.34,
    "stability_score": 0.82
  },
  "overall_stability": {
    "stability_score": 0.82,
    "interpretation": "very_stable"
  },
  "overall_prediction_interval": {
    "lower_bound": 0.18,
    "median": 0.26,
    "upper_bound": 0.34,
    "confidence_level": 0.90
  }
}
```

### `sensitivity_report.json`
Parameter sensitivity rankings:
```json
{
  "parameter_sensitivity": {
    "persistence_bonus": {
      "relative_sensitivity": 0.31,
      "impact_rank": 1
    },
    "intent_penalty": {
      "relative_sensitivity": 0.18,
      "impact_rank": 2
    }
  },
  "ranked_by_sensitivity": [...]
}
```

### `confidence_intervals.json`
Prediction intervals for overall and step-level metrics:
```json
{
  "overall_prediction_interval": {
    "lower_bound": 0.18,
    "median": 0.26,
    "upper_bound": 0.34
  },
  "step_prediction_intervals": {
    "Step 1": {...},
    "Step 2": {...}
  }
}
```

## 🎯 Success Criteria

You can now answer:

✅ **"How confident are we in this number?"**
- Use `overall_prediction_interval` or `step_prediction_intervals`
- Stability score tells you reliability

✅ **"Which assumptions matter most?"**
- Check `sensitivity_report.json` - parameters ranked by impact
- Higher relative sensitivity = more important

✅ **"If this changes slightly, what breaks?"**
- Sensitivity analysis shows impact of ±20% parameter changes
- High sensitivity = fragile assumption

## 🧠 Design Principles

- **No ML libraries required** (only numpy)
- **Deterministic where possible** (stochastic only for variance estimation)
- **No changes to core behavioral logic** (evaluation only)
- **Plug-and-play** with existing pipeline
- **Human-readable and machine-parseable** JSON outputs


# Real-World Calibration

## 🎯 Purpose

Converts the system from **theoretically calibrated** to **empirically grounded** by fitting a small set of parameters to real observed funnel data.

**Key Principle:** Calibrate parameters only - do NOT change model structure or behavioral logic.

## 📊 What It Does

1. **Accepts observed funnel data** from real users
2. **Compares** against model predictions
3. **Optimizes** 4-5 key parameters to minimize error
4. **Validates** improvement with before/after metrics
5. **Exports** calibrated parameters and diagnostics

## 🔧 Calibratable Parameters

Only these parameters can be tuned (limited set):

1. **BASE_COMPLETION_RATE** (default: 0.60)
   - Base completion probability floor
   - Bounds: [0.05, 0.90]

2. **PERSISTENCE_BONUS_START** (default: 0.18)
   - Persistence bonus at journey start
   - Bounds: [0.0, 0.40]

3. **PERSISTENCE_BONUS_RATE** (default: 0.22)
   - Rate persistence bonus increases with progress
   - Bounds: [0.0, 0.50]

4. **INTENT_PENALTY_WEIGHT** (default: 0.025)
   - Weight for intent mismatch penalties
   - Bounds: [0.0, 0.15]

5. **ENTRY_PROBABILITY_SCALE** (default: 1.0)
   - Scaling factor for entry probability
   - Bounds: [0.5, 2.0]

## 📥 Input: Observed Funnel Data

```python
from calibration import ObservedFunnelData

observed_funnel = ObservedFunnelData(
    entry_count=10000,  # Total visitors/impressions
    step_completions={
        "Step 1": 3500,  # Number who completed step 1
        "Step 2": 2800,  # Number who completed step 2
        ...
        "Completed": 500  # Number who completed entire funnel
    },
    total_completions=500
)
```

**Data Sources:**
- Google Analytics
- Mixpanel
- Amplitude
- Custom analytics

## 🚀 Usage

### Basic Calibration

```python
from calibration import (
    ObservedFunnelData,
    calibrate_to_real_data,
    export_calibration_summary,
    export_calibration_diagnostics
)
from behavioral_engine_improved import run_behavioral_simulation_improved

# Observed data
observed_funnel = ObservedFunnelData(
    entry_count=10000,
    step_completions={...},
    total_completions=500
)

# Run calibration
calibrated_params, summary, diagnostics = calibrate_to_real_data(
    observed_funnel=observed_funnel,
    simulation_function=run_behavioral_simulation_improved,
    simulation_args={'df': df, 'product_steps': steps, ...},
    product_steps=steps,
    regularization_weight=0.1,
    max_iterations=20,
    verbose=True
)

# Export results
export_calibration_summary(summary, 'calibration_summary.json')
export_calibration_diagnostics(diagnostics, 'calibration_diagnostics.json')
```

### With Entry Model

```python
# Include entry signals for full funnel calibration
entry_signals = {
    'referrer': 'direct',
    'intent_frame': {'commitment_threshold': 0.7},
    'landing_page_text': 'Find the Best Credit Card In 60 seconds'
}

calibrated_params, summary, diagnostics = calibrate_to_real_data(
    observed_funnel=observed_funnel,
    simulation_function=run_behavioral_simulation_improved,
    simulation_args=simulation_args,
    product_steps=steps,
    entry_signals=entry_signals,  # Include entry model
    regularization_weight=0.1,
    max_iterations=20
)
```

## 📊 Output Artifacts

### `calibration_summary.json`
```json
{
  "before_error": 0.1523,
  "after_error": 0.0845,
  "improvement_pct": 44.5,
  "calibrated_parameters": {
    "BASE_COMPLETION_RATE": 0.65,
    "PERSISTENCE_BONUS_START": 0.20,
    ...
  },
  "parameter_changes": {
    "BASE_COMPLETION_RATE": 8.3,
    "PERSISTENCE_BONUS_START": 11.1,
    ...
  },
  "confidence_ranges": {
    "BASE_COMPLETION_RATE": [0.60, 0.70],
    ...
  },
  "fit_score": 0.9155
}
```

### `calibration_diagnostics.json`
```json
{
  "per_step_errors_before": {
    "Step 1": 0.12,
    "Step 2": 0.08,
    ...
  },
  "per_step_errors_after": {
    "Step 1": 0.05,
    "Step 2": 0.03,
    ...
  },
  "parameter_sensitivity": {
    "BASE_COMPLETION_RATE": 0.45,
    "PERSISTENCE_BONUS_START": 0.22,
    ...
  },
  "regularization_penalty": 0.0023
}
```

### `parameter_changes.log`
Human-readable audit log of all parameter changes.

## ✅ Guardrails

### 1. **No Model Structure Changes**
- Only parameter values change
- Behavioral logic unchanged
- Model structure preserved

### 2. **Reversible Calibration**
- Default parameters preserved
- Can revert to defaults
- All changes logged

### 3. **Regularization**
- Prevents overfitting
- Penalizes large parameter changes
- Configurable weight (default: 0.1)

### 4. **Parameter Bounds**
- All parameters within valid bounds
- Prevents unrealistic values
- Enforces model constraints

### 5. **Audit Trail**
- All changes logged
- Timestamped
- Reversible

## 📈 Validation Output

After calibration, you get:

```
Before calibration:
  Mean absolute error = 0.1523

After calibration:
  Mean absolute error = 0.0845

Improvement: 44.5%
```

This shows:
- ✅ Calibration improved fit
- ✅ Quantified improvement
- ✅ Model is now grounded in real data

## 🎯 Success Criteria

After calibration, you can say:

✅ **"This model is grounded in real observed data"**
- Parameters fitted to actual user behavior
- Not just theoretical assumptions

✅ **"Deviations are quantified and controlled"**
- Error metrics show fit quality
- Confidence ranges show uncertainty
- Regularization prevents overfitting

✅ **"Model is production-credible"**
- Validated against real data
- Parameters are explainable
- Changes are reversible

## 🔄 Integration with Existing System

The calibration integrates seamlessly:

1. **Uses existing behavioral engine** (no changes)
2. **Uses existing entry model** (optional)
3. **Uses existing calibration infrastructure**
4. **Preserves all existing functionality**

## 💡 Example: Credigo Calibration

```bash
python3 calibration/run_real_world_calibration.py
```

**Output:**
```
Before calibration:
  Mean absolute error = 0.1523

After calibration:
  Mean absolute error = 0.0845

Improvement: 44.5%
Fit score: 0.9155

Calibrated parameters:
  BASE_COMPLETION_RATE: 0.65 (default: 0.60, change: +8.3%)
  PERSISTENCE_BONUS_START: 0.20 (default: 0.18, change: +11.1%)
  ...
```

## ⚠️ Important Notes

1. **Replace example data with real data** - The example uses placeholder data
2. **Validate on holdout set** - Don't overfit to calibration data
3. **Monitor parameter drift** - Recalibrate periodically
4. **Use regularization** - Prevents overfitting to specific scenarios

## 🎯 Next Steps

1. **Collect real funnel data** from analytics
2. **Run calibration** with real data
3. **Validate** on holdout set
4. **Deploy** calibrated parameters
5. **Monitor** and recalibrate periodically

---

**This is the final step before calling the system production-credible.**


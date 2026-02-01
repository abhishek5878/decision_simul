# Decision Explainability Module

SHAP-style explainability for behavioral simulation decisions.

## Overview

This module adds explainability to the decision simulation system by computing SHAP-like values that quantify which features actually caused each decision. It answers questions like:

- "At Step 4, effort tolerance explains 63% of drop decisions."
- "Intent strength stops mattering after Step 2."
- "Credigo is more sensitive to trust than value at entry."

## Architecture

### Core Components

1. **`shap_model.py`**
   - `DecisionSurrogateModel`: Lightweight surrogate model (logistic regression or decision tree)
   - `prepare_decision_features`: Extract features from decision traces
   - `compute_shap_values_for_decision`: Compute SHAP values for individual decisions

2. **`shap_aggregator.py`**
   - `aggregate_step_importance`: Mean absolute SHAP per feature per step
   - `aggregate_drop_trigger_analysis`: Analyze features causing DROP decisions
   - `aggregate_persona_sensitivity`: Compare SHAP distributions across persona classes

3. **`shap_report_generator.py`**
   - `generate_feature_importance_report`: Per-step feature importance
   - `generate_step_fragility_report`: Drop trigger analysis
   - `generate_persona_sensitivity_report`: Persona-class comparisons

4. **`decision_shap_runner.py`**
   - Main execution script
   - Orchestrates the full pipeline

## Usage

### Basic Usage

```bash
python3 decision_explainability/decision_shap_runner.py credigo_benchmark_decision_ledger.json --output-dir .
```

### Options

- `--output-dir`: Directory for output reports (default: current directory)
- `--use-tree`: Use decision tree instead of logistic regression
- `--save-traces`: Save traces with SHAP values to JSON file

### Output Files

1. **`decision_feature_importance.md`**
   - Per-step feature importance rankings
   - Mean absolute SHAP values
   - Top features by decision influence

2. **`step_fragility_shap.md`**
   - Drop trigger analysis
   - Features causing DROP decisions
   - Per-step drop analysis

3. **`persona_sensitivity_shap.md`**
   - Feature importance by persona class
   - Cross-persona comparisons
   - Features that matter only for certain users

## Feature Set

Each decision is explained using these features:

1. **Persona State Features:**
   - `cognitive_energy`
   - `risk_tolerance`
   - `effort_tolerance`
   - `intent_strength`
   - `trust_baseline`
   - `value_expectation`

2. **Step Force Features:**
   - `step_effort_force`
   - `step_risk_force`
   - `step_value_force`
   - `step_trust_force`
   - `step_intent_mismatch`

## Design Constraints

✅ **What This Module Does:**
- Explains past simulated decisions only
- Fully traceable back to DecisionTrace IDs
- Deterministic and reproducible
- Uses interpretable surrogate models

❌ **What This Module Does NOT Do:**
- Black-box ML explanations
- Optimization suggestions
- Prediction claims
- Modify decision logic

## Methodology

1. **Surrogate Model:** Fit a lightweight model (logistic regression or decision tree) to approximate the decision function from traces.

2. **SHAP Computation:** For logistic regression, uses coefficient-based approximation: `SHAP ≈ coefficient × (feature_value - mean_feature_value)`. For trees, uses feature importance scaling.

3. **Aggregation:** Mean absolute SHAP values are computed per step, per outcome type (CONTINUE/DROP), and per persona class.

4. **Reporting:** Human-readable markdown reports with tables and rankings, no charts.

## Dependencies

- `numpy`
- `scikit-learn` (for surrogate models)

## Examples

### Example: Step 4 Analysis

From `decision_feature_importance.md`:
```
## Step: step_4

**Total Decisions:** 90 (CONTINUE: 4, DROP: 86)

| Feature | Mean Absolute SHAP | Importance Rank |
|---------|-------------------|-----------------|
| effort_tolerance | 0.0632 | 1 |
| step_effort_force | 0.0521 | 2 |
| step_value_force | 0.0418 | 3 |
```

This shows that at Step 4, `effort_tolerance` has the highest mean absolute SHAP value (0.0632), indicating it's the most important feature in explaining decisions at this step.

### Example: Drop Trigger Analysis

From `step_fragility_shap.md`:
```
### Features Most Strongly Causing Drops

| Feature | Mean Negative SHAP | Impact |
|---------|-------------------|--------|
| step_effort_force | -0.0821 | High |
| effort_tolerance | -0.0643 | High |
```

Negative SHAP values indicate features pushing decisions toward DROP. Here, `step_effort_force` has the strongest negative impact.

## Integration

This module operates on decision traces (from `SensitivityDecisionTrace` or similar structures). It does not modify the behavioral simulation engine - it only analyzes its outputs.

## Future Enhancements

- Per-step drop trigger analysis (currently only overall)
- More sophisticated SHAP computation (e.g., using SHAP library)
- Visualization support (charts/graphs)
- Feature interaction analysis


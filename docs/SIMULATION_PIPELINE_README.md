# Canonical Simulation Pipeline

## 🎯 Purpose

**This is the ONLY supported way to run simulations.**

All other execution paths are deprecated. Use `simulation_pipeline.run_simulation()` as the single entry point.

---

## ✅ Quick Start

```python
from simulation_pipeline import run_simulation

# Run simulation
result = run_simulation(
    product_config="credigo",
    mode="production",
    n_personas=1000
)

# Access results
print(f"Total conversion: {result.final_metrics['total_conversion']:.2%}")

# Export
result.export('simulation_result.json')
```

---

## 📊 Execution Modes

### `mode="research"`
Quick experiments, no evaluation/drift:
- ✅ Entry model
- ✅ Behavioral engine
- ❌ Calibration (skipped)
- ❌ Evaluation (skipped)
- ❌ Drift monitoring (skipped)

### `mode="evaluation"`
Full analysis with evaluation:
- ✅ Entry model
- ✅ Behavioral engine
- ✅ Calibration (if available)
- ✅ Evaluation
- ❌ Drift monitoring (skipped)

### `mode="production"`
Production deployment with monitoring:
- ✅ Entry model
- ✅ Behavioral engine
- ✅ Calibration (if available)
- ✅ Evaluation
- ✅ Drift monitoring

---

## 🔧 Pipeline Stages

The pipeline runs in fixed order:

1. **Load Product + Persona Data**
   - Loads product steps configuration
   - Loads and derives persona features

2. **Run Entry Model**
   - Estimates entry probability
   - Uses traffic source, intent, landing page signals

3. **Run Behavioral + Intent Engine**
   - Uses ONLY canonical engine (`behavioral_engine_intent_aware`)
   - Applies intent-aware modeling
   - Computes completion rates

4. **Apply Calibrated Parameters** (if available)
   - Loads calibration file if exists
   - Re-runs engine with calibrated parameters
   - Skips in research mode

5. **Compute Full Funnel Metrics**
   - Combines entry × completion
   - Step-level metrics
   - Drop-off distributions

6. **Run Evaluation** (evaluation/production modes)
   - Confidence intervals
   - Sensitivity analysis
   - Stability metrics

7. **Run Drift Monitoring** (production mode only)
   - Compares to baseline
   - Detects drift
   - Provides recommendations

---

## 📦 Unified Output

The pipeline returns a `PipelineResult` object with:

```python
{
    "entry": {...},           # Entry model results
    "behavioral": {...},      # Behavioral engine results
    "intent": {...},          # Intent analysis
    "calibration": {...},     # Calibration data (if available)
    "evaluation": {...},      # Evaluation results (if mode allows)
    "drift": {...},           # Drift monitoring (if production mode)
    "final_metrics": {        # Final funnel metrics
        "entry_rate": 0.55,
        "completion_rate": 0.77,
        "total_conversion": 0.42,
        ...
    },
    "model_version": "v1.0",
    "execution_mode": "production",
    "timestamp": "2026-01-02T..."
}
```

---

## 🚫 What's Deprecated

See `DEPRECATED.md` for full list. In short:

- ❌ Direct engine imports (use pipeline instead)
- ❌ Old run scripts (use pipeline instead)
- ❌ Bypassing pipeline stages

---

## ✅ Success Criteria

After using the pipeline, you get:

- ✅ Full funnel prediction (entry × completion)
- ✅ Calibrated output (if calibration file exists)
- ✅ Confidence intervals (if evaluation mode)
- ✅ Drift status (if production mode)
- ✅ One authoritative answer

---

## 📝 Example

```python
from simulation_pipeline import run_simulation

# Production run
result = run_simulation(
    product_config="credigo",
    mode="production",
    n_personas=1000,
    seed=42,
    calibration_file="credigo_ss_calibration_summary.json",
    baseline_file="credigo_ss_baseline.json",
    verbose=True
)

# Access unified results
print(f"Entry: {result.final_metrics['entry_rate']:.2%}")
print(f"Completion: {result.final_metrics['completion_rate']:.2%}")
print(f"Total: {result.final_metrics['total_conversion']:.2%}")

if result.drift:
    print(f"Drift status: {result.drift['overall_status']}")

# Export
result.export('my_simulation.json')
```

---

**This is the ONLY way to run simulations. All other paths are deprecated.**


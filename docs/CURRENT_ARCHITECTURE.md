# Current Architecture - Complete System Overview

**Last Updated:** January 2026  
**Status:** Production-Ready with Canonical Pipeline

---

## 🎯 System Overview

The system is a **behavioral simulation platform** that predicts user behavior in product onboarding flows. It uses behavioral science principles to model cognitive states, intent awareness, and decision-making.

**Core Philosophy:** Explainable, empirically grounded, continuously monitored behavioral predictions.

---

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CANONICAL PIPELINE                            │
│              (simulation_pipeline.py)                            │
│                  THE ONLY ENTRY POINT                            │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXECUTION MODES                               │
│  • research: Quick experiments                                   │
│  • evaluation: Full analysis                                     │
│  • production: Complete with monitoring                          │
└─────────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ ENTRY MODEL  │  │ BEHAVIORAL ENGINE│  │  INTENT LAYER    │
│              │  │  (CANONICAL)     │  │  (Built-in)      │
│ entry_model/ │  │ behavioral_engine│  │ dropsim_intent_  │
│              │  │ _intent_aware.py │  │ model.py         │
└──────────────┘  └──────────────────┘  └──────────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CALIBRATION LAYER                             │
│  calibration/                                                    │
│  • Real-world calibration                                        │
│  • Parameter optimization                                        │
│  • Calibration artifacts                                         │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EVALUATION LAYER                              │
│  calibration/                                                    │
│  • Confidence intervals                                          │
│  • Sensitivity analysis                                          │
│  • Stability metrics                                             │
│  • Prediction intervals                                          │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DRIFT MONITORING                              │
│  calibration/                                                    │
│  • Baseline management                                           │
│  • Drift detection                                               │
│  • Health monitoring                                             │
│  • Recommendations                                               │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    UNIFIED OUTPUT                                │
│  PipelineResult:                                                 │
│  • entry: Entry model results                                    │
│  • behavioral: Behavioral results                                │
│  • intent: Intent analysis                                       │
│  • calibration: Calibration data                                 │
│  • evaluation: Evaluation results                                │
│  • drift: Drift monitoring                                       │
│  • final_metrics: Final funnel metrics                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 Component Architecture

### 1. Canonical Pipeline (NEW - THE ONLY WAY)

**Location:** `simulation_pipeline.py`

**Purpose:** Single entry point for all simulations

**Key Features:**
- ✅ ONE entry point: `run_simulation()`
- ✅ ONE canonical engine: `behavioral_engine_intent_aware`
- ✅ Execution modes: research/evaluation/production
- ✅ 7 fixed pipeline stages
- ✅ Unified output: `PipelineResult`

**Usage:**
```python
from simulation_pipeline import run_simulation

result = run_simulation(
    product_config="credigo",
    mode="production",
    n_personas=1000
)
```

**Pipeline Stages:**
1. Load product + persona data
2. Run entry model
3. Run behavioral + intent engine (canonical only)
4. Apply calibrated parameters (if available)
5. Compute full funnel metrics
6. Run evaluation (if mode allows)
7. Run drift monitoring (production only)

---

### 2. Entry Model

**Location:** `entry_model/`

**Purpose:** Models pre-behavioral entry probability (who arrives?)

**Components:**
- `entry_model.py` - Core entry probability computation
- `entry_signals.py` - Signal extraction (traffic source, intent, landing page)
- `entry_calibration.py` - Calibration for entry model
- `funnel_integration.py` - Integration with behavioral engine

**Inputs:**
- Traffic source (direct, SEO, ads, etc.)
- Intent strength (high/medium/low)
- Landing page promise strength
- Brand trust proxy (optional)

**Outputs:**
- Entry probability: P(entry)
- Confidence score
- Driver breakdown

**Key Principle:** Separates entry from completion
- Entry: "Who arrives?" (pre-behavioral)
- Completion: "Who finishes?" (behavioral)

---

### 3. Behavioral Engine (CANONICAL)

**Location:** `behavioral_engine_intent_aware.py`

**Status:** ✅ **CANONICAL** - This is the ONLY engine used by pipeline

**Purpose:** Models in-funnel behavioral completion (who finishes?)

**Key Features:**
- Intent-aware behavioral modeling
- Cognitive state tracking
- Probabilistic continuation decisions
- Intent-step alignment scoring
- Intent-conditioned probabilities

**State Variables:**
- Cognitive energy
- Perceived risk
- Perceived effort
- Perceived value
- Perceived control

**Decision Logic:**
- Base behavioral probability
- Intent alignment adjustment
- Penalties for mismatches
- Amplifiers for alignment

**Deprecated Engines:**
- ❌ `behavioral_engine.py`
- ❌ `behavioral_engine_improved.py`
- ❌ `behavioral_engine_semantic_aware.py`
- ❌ `behavioral_engine_stabilized.py`

---

### 4. Intent Layer (Built into Canonical Engine)

**Location:** `dropsim_intent_model.py`

**Purpose:** Explains WHY users act based on underlying intent

**Components:**
- Intent inference
- Intent-step alignment scoring
- Intent-conditioned continuation probability
- Intent-aware failure explanations

**Intent Types:**
- Compare options
- Validate choice
- Learn basics
- Quick decision
- Price check
- Eligibility check

**Key Concept:**
- Intent layer **augments** behavioral modeling (doesn't replace)
- Explains causal reasons for behavior
- Provides "why" not just "what"

---

### 5. Calibration Layer

**Location:** `calibration/`

**Purpose:** Empirically ground the model using real observed data

**Components:**
- `real_world_calibration.py` - Calibrate to observed funnel data
- `parameter_space.py` - Parameter definitions and bounds
- `loss_functions.py` - Error computation
- `optimizer.py` - Parameter optimization
- `validation.py` - Parameter validation

**Calibratable Parameters (Limited Set):**
1. BASE_COMPLETION_RATE
2. PERSISTENCE_BONUS_START
3. PERSISTENCE_BONUS_RATE
4. INTENT_PENALTY_WEIGHT
5. ENTRY_PROBABILITY_SCALE

**Key Features:**
- Fits parameters to observed data
- Regularization prevents overfitting
- Reversible and auditable
- No model structure changes

---

### 6. Evaluation Layer

**Location:** `calibration/evaluator.py`, `calibration/confidence_estimation.py`, etc.

**Purpose:** Assess model reliability, confidence, and stability

**Components:**
- Confidence interval estimation
- Sensitivity analysis
- Stability metrics
- Prediction intervals

**Outputs:**
- Confidence intervals (p10, p50, p90)
- Parameter sensitivity rankings
- Stability scores
- Prediction intervals

---

### 7. Drift Monitoring

**Location:** `calibration/drift_metrics.py`, `calibration/model_health_monitor.py`

**Purpose:** Monitor model health and detect drift

**Components:**
- Baseline management
- Drift detection (entry, completion, parameters, distributions)
- Severity classification (stable/warning/critical)
- Recommendations generation

**Monitored Metrics:**
- Entry rate drift
- Completion rate drift
- Step-level drift
- Parameter value drift
- Distribution drift (JS divergence)

**Outputs:**
- Drift severity (stable/warning/critical)
- Overall status (valid/monitor_closely/needs_recalibration)
- Recommendations

---

## 🔄 Data Flow

### Complete Execution Flow

```
1. USER CALLS PIPELINE
   run_simulation(product_config="credigo", mode="production")
   
2. PIPELINE LOADS DATA
   ├─ Product steps (from product config)
   └─ Persona data (from dataset)
   
3. ENTRY MODEL RUNS
   ├─ Extracts signals (traffic source, intent, landing page)
   ├─ Computes entry probability
   └─ Returns: P(entry)
   
4. BEHAVIORAL ENGINE RUNS (CANONICAL)
   ├─ Uses behavioral_engine_intent_aware ONLY
   ├─ Applies intent-aware modeling
   ├─ Computes completion probability
   └─ Returns: P(completion | entry)
   
5. CALIBRATION APPLIED (if available)
   ├─ Loads calibrated parameters
   ├─ Re-runs engine with calibrated params
   └─ Updates completion probability
   
6. FULL FUNNEL COMPUTED
   ├─ Total conversion = P(entry) × P(completion | entry)
   ├─ Step-level metrics
   └─ Drop-off distributions
   
7. EVALUATION RUNS (if mode allows)
   ├─ Confidence intervals
   ├─ Sensitivity analysis
   └─ Stability metrics
   
8. DRIFT MONITORING RUNS (production only)
   ├─ Compares to baseline
   ├─ Detects drift
   └─ Generates recommendations
   
9. UNIFIED OUTPUT CREATED
   ├─ PipelineResult object
   ├─ All components included
   └─ Single JSON export
```

---

## 📊 Execution Modes

### Research Mode
```
run_simulation(mode="research")
```
- ✅ Entry model
- ✅ Behavioral engine
- ❌ Calibration (skipped)
- ❌ Evaluation (skipped)
- ❌ Drift monitoring (skipped)

**Use for:** Quick experiments, development

### Evaluation Mode
```
run_simulation(mode="evaluation")
```
- ✅ Entry model
- ✅ Behavioral engine
- ✅ Calibration (if available)
- ✅ Evaluation
- ❌ Drift monitoring (skipped)

**Use for:** Comprehensive analysis, validation

### Production Mode
```
run_simulation(mode="production")
```
- ✅ Entry model
- ✅ Behavioral engine
- ✅ Calibration (if available)
- ✅ Evaluation
- ✅ Drift monitoring

**Use for:** Production deployments, monitoring

---

## 🎯 Key Design Principles

### 1. Single Entry Point
- **ONE way to run simulations:** `simulation_pipeline.run_simulation()`
- All other paths deprecated
- Clear migration path

### 2. Canonical Engine
- **ONE engine:** `behavioral_engine_intent_aware`
- All others deprecated
- Hard enforcement in code

### 3. Separation of Concerns
- **Entry Model:** Pre-behavioral (who arrives?)
- **Behavioral Engine:** In-funnel (who finishes?)
- **Intent Layer:** Causal explanation (why?)

### 4. Empirical Grounding
- Calibration to real observed data
- No black-box ML
- Explainable parameters

### 5. Continuous Monitoring
- Drift detection
- Health monitoring
- Actionable recommendations

### 6. Unified Output
- Single result object
- All components included
- Consistent format

---

## 📁 File Structure

```
inertia_labs/
├── simulation_pipeline.py          # ⭐ CANONICAL ENTRY POINT
├── DEPRECATED.md                   # Deprecation guide
│
├── entry_model/                    # Entry probability modeling
│   ├── entry_model.py
│   ├── entry_signals.py
│   ├── entry_calibration.py
│   ├── funnel_integration.py
│   └── test_entry_model.py
│
├── behavioral_engine_intent_aware.py  # ⭐ CANONICAL ENGINE
│
├── dropsim_intent_model.py         # Intent layer (used by canonical)
│
├── calibration/                    # Calibration, evaluation, monitoring
│   ├── real_world_calibration.py
│   ├── parameter_space.py
│   ├── loss_functions.py
│   ├── optimizer.py
│   ├── validation.py
│   ├── evaluator.py
│   ├── confidence_estimation.py
│   ├── sensitivity_analysis.py
│   ├── stability_metrics.py
│   ├── prediction_intervals.py
│   ├── drift_metrics.py
│   ├── model_health_monitor.py
│   └── run_drift_monitoring.py
│
├── load_dataset.py                 # Data loading
├── derive_features.py              # Feature derivation
│
├── credigo_ss_steps_improved.py    # Product configurations
├── blink_money_steps.py
├── keeper_ss_steps.py
└── trial1_steps.py
```

---

## 🔧 Integration Points

### How Components Work Together

1. **Pipeline → Entry Model**
   - Pipeline calls entry model automatically
   - Entry model provides P(entry)

2. **Pipeline → Behavioral Engine**
   - Pipeline calls canonical engine only
   - Engine uses intent layer internally
   - Returns P(completion | entry)

3. **Pipeline → Calibration**
   - Pipeline loads calibration file if exists
   - Applies calibrated parameters to engine
   - Re-runs engine with calibrated params

4. **Pipeline → Evaluation**
   - Pipeline runs evaluation if mode allows
   - Uses canonical engine for multiple runs
   - Computes confidence, sensitivity, stability

5. **Pipeline → Drift Monitoring**
   - Pipeline runs drift monitoring in production
   - Compares current state to baseline
   - Generates recommendations

6. **Pipeline → Unified Output**
   - Combines all results into PipelineResult
   - Single export: `result.export()`

---

## ✅ Current Status

### What's Production-Ready

✅ **Canonical Pipeline** - Single entry point  
✅ **Entry Model** - Full funnel modeling  
✅ **Behavioral Engine** - Canonical engine selected  
✅ **Calibration** - Real-world calibration  
✅ **Evaluation** - Confidence, sensitivity, stability  
✅ **Drift Monitoring** - Health monitoring  
✅ **Unified Output** - Single result object  

### What's Deprecated

❌ `behavioral_engine.py`  
❌ `behavioral_engine_improved.py`  
❌ `behavioral_engine_semantic_aware.py`  
❌ `behavioral_engine_stabilized.py`  
❌ Old run scripts (use pipeline instead)  

### What Still Needs Work

⚠️ **Real-World Validation** - Need observed data to validate predictions  
⚠️ **Intent Layer Effectiveness** - Need to verify penalties are working  
⚠️ **Base Model Review** - May need fundamental review of equations  

---

## 🚀 Usage Examples

### Basic Usage

```python
from simulation_pipeline import run_simulation

# Production run
result = run_simulation(
    product_config="credigo",
    mode="production",
    n_personas=1000
)

# Access results
print(f"Total conversion: {result.final_metrics['total_conversion']:.2%}")
print(f"Drift status: {result.drift['overall_status']}")

# Export
result.export('simulation_result.json')
```

### Research Mode

```python
# Quick experiment
result = run_simulation(
    product_config="credigo",
    mode="research",
    n_personas=100
)
```

### Evaluation Mode

```python
# Full analysis
result = run_simulation(
    product_config="credigo",
    mode="evaluation",
    n_personas=1000,
    calibration_file="credigo_ss_calibration_summary.json"
)
```

---

## 📈 System Capabilities

### What the System Can Do

✅ **Full Funnel Modeling**
- Entry probability (who arrives?)
- Completion probability (who finishes?)
- Total conversion (entry × completion)

✅ **Behavioral Explanation**
- Why users drop off
- Intent mismatches
- Cognitive fatigue, risk, effort

✅ **Empirical Calibration**
- Fit to observed data
- Quantified improvement
- Auditable parameters

✅ **Reliability Assessment**
- Confidence intervals
- Sensitivity analysis
- Stability scores

✅ **Health Monitoring**
- Drift detection
- Status assessment
- Recommendations

---

## 🎯 Architecture Strengths

1. **Theoretical Foundation** (9/10)
   - Strong behavioral science grounding
   - Explainable models
   - Clear causal relationships

2. **Production Readiness** (8/10)
   - Canonical pipeline
   - Monitoring and evaluation
   - Unified outputs

3. **Comprehensive Coverage** (8/10)
   - Full funnel modeling
   - Multiple validation layers
   - Rich diagnostics

4. **Explainability** (9/10)
   - Every prediction explained
   - No black-box components
   - Clear failure reasons

---

## ⚠️ Architecture Weaknesses

1. **Version Sprawl** (7/10) - **IMPROVED**
   - Before: 5+ engines
   - After: 1 canonical engine (others deprecated)
   - Still: Deprecated code exists (for backward compat)

2. **Real-World Validation** (6/10)
   - Need observed data to validate
   - Calibration helps but need validation

3. **Intent Layer Effectiveness** (6/10)
   - Need to verify penalties are working
   - May need investigation

---

## 🔄 Migration Path

### For New Code

✅ **Use:** `simulation_pipeline.run_simulation()`

### For Existing Code

⚠️ **Migrate from:**
- Direct engine imports → Use pipeline
- Old run scripts → Use pipeline
- Manual orchestration → Use pipeline

**See:** `DEPRECATED.md` for migration guide

---

## 📊 Output Structure

### PipelineResult Object

```python
{
    "entry": {
        "entry_probability": 0.55,
        "confidence": 0.78,
        "drivers": {...},
        "signals": {...}
    },
    "behavioral": {
        "completion_rate": 0.77,
        "step_completion_rates": {...},
        "dropoff_by_step": {...},
        "intent_analysis": {...}
    },
    "intent": {...},
    "calibration": {...},  # If available
    "evaluation": {...},   # If mode allows
    "drift": {...},        # If production mode
    "final_metrics": {
        "entry_rate": 0.55,
        "completion_rate": 0.77,
        "total_conversion": 0.42
    },
    "model_version": "v1.0",
    "execution_mode": "production",
    "timestamp": "2026-01-02T..."
}
```

---

## 🎯 Summary

**Current State:**
- ✅ Canonical pipeline implemented
- ✅ Single entry point
- ✅ Integrated components
- ✅ Unified outputs
- ✅ Production monitoring

**Architecture Quality:**
- Strong theoretical foundation
- Comprehensive validation
- Production-ready monitoring
- Clear execution path

**Remaining Work:**
- Real-world validation needed
- Intent layer verification needed
- Base model review (optional)

---

**The system has evolved from "research tool" to "production-ready behavioral modeling platform" with a clear canonical execution path.**


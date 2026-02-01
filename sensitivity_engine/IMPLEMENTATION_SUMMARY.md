# Decision Sensitivity Simulation Engine - Implementation Summary

## Overview

A deterministic, traceable system for analyzing how product onboarding decisions respond to controlled perturbations. This engine enables explainable sensitivity analysis by comparing baseline vs perturbed decision traces.

---

## Architecture

### Core Modules

1. **`fixed_personas.py`**
   - Generates 100 fixed personas with 7 state variants each
   - Uses stratified sampling for coverage
   - Personas remain identical across experiments (reproducibility)

2. **`decision_trace_extended.py`**
   - Extended decision trace structure: `state_before → forces_applied → decision → state_after`
   - Force contribution computation (SHAP-style local attribution)
   - Immutable decision records

3. **`perturbation_engine.py`**
   - Controlled perturbations (one variable at a time)
   - Supports: reduce_effort, delay_step, increase_value_signal, remove_question, reduce_risk, increase_trust, reduce_intent_mismatch
   - Ensures all other variables remain constant

4. **`sensitivity_simulator.py`**
   - Runs personas through product flows
   - Captures detailed decision traces with state transitions
   - Computes forces applied at each step
   - Integrates with behavioral engine logic

5. **`sensitivity_analyzer.py`**
   - Compares baseline vs perturbed traces
   - Computes decision change rates, fragility scores
   - Identifies responsive persona segments
   - Per-step sensitivity analysis

6. **`sensitivity_report.py`**
   - Generates DecisionSensitivityReport
   - Identifies top leverage steps (highest sensitivity)
   - Ranks forces by impact
   - Human-readable markdown reports

7. **`run_sensitivity_analysis.py`**
   - Main execution script
   - Orchestrates entire analysis pipeline
   - Command-line interface

---

## Execution Flow

```
1. Generate/Load Fixed Personas (100 personas, 7 state variants)
   ↓
2. Run Baseline Simulation
   - Simulate all personas through target product
   - Capture decision traces (state → forces → decision → state)
   ↓
3. Apply Perturbations (one at a time)
   - Reduce effort at step X
   - Increase value signal at step Y
   - Delay step Z
   - etc.
   ↓
4. Run Perturbed Simulations
   - Same personas, same seed
   - Only perturbed variable changes
   ↓
5. Compare Traces
   - Compute decision change rates
   - Identify fragile vs stable steps
   - Rank forces by impact
   ↓
6. Generate Report
   - Top leverage steps
   - Forces that move decisions
   - Responsive persona segments
```

---

## Key Data Structures

### FixedPersona
```python
@dataclass
class FixedPersona:
    persona_id: str
    cognitive_energy: float      # 0-1
    risk_tolerance: float        # 0-1
    effort_tolerance: float      # 0-1
    intent_strength: float       # 0-1
    trust_baseline: float        # 0-1
    urgency: float               # 0-1
    value_expectation: float     # 0-1
```

### SensitivityDecisionTrace
```python
@dataclass
class SensitivityDecisionTrace:
    step_id: str
    step_index: int
    persona_id: str
    state_before: PersonaState
    forces_applied: ForcesApplied
    decision: DecisionOutcome  # CONTINUE or DROP
    state_after: PersonaState
    continuation_probability: float
    experiment_id: str
```

### Perturbation
```python
@dataclass
class Perturbation:
    perturbation_type: PerturbationType
    step_id: Optional[str]
    step_index: Optional[int]
    magnitude: float
    delay_by_steps: Optional[int]
    experiment_id: str
```

### DecisionSensitivityReport
```python
@dataclass
class DecisionSensitivityReport:
    product_name: str
    baseline_experiment_id: str
    top_leverage_steps: List[Dict]
    force_impact_rankings: List[Dict]
    responsive_persona_segments: Dict[str, float]
    perturbation_results: List[PerturbationSensitivity]
```

---

## Design Principles

1. **Determinism**: Same personas, same seed → same results
2. **Traceability**: Every decision is traceable to state and forces
3. **Reproducibility**: Fixed personas ensure comparability across experiments
4. **One-Variable-At-A-Time**: Controlled perturbations ensure clean causal attribution
5. **Explainability**: Force contributions, not predictions
6. **No Black-Box ML**: All logic is explicit and traceable

---

## Usage

### Command Line

```bash
python sensitivity_engine/run_sensitivity_analysis.py trial1 --personas 100
```

### Programmatic

```python
from sensitivity_engine.run_sensitivity_analysis import run_sensitivity_analysis

results = run_sensitivity_analysis(
    product_config="trial1",
    n_personas=100,
    output_dir="./sensitivity_results"
)
```

### Custom Perturbations

```python
from sensitivity_engine.perturbation_engine import Perturbation, PerturbationType

perturbations = [
    Perturbation(
        perturbation_type=PerturbationType.REDUCE_EFFORT,
        step_index=1,
        magnitude=0.3,  # 30% reduction
        experiment_id="reduce_effort_step1"
    ),
]

results = run_sensitivity_analysis(
    product_config="trial1",
    perturbations=perturbations
)
```

---

## Output Files

1. **`fixed_personas.json`** - Fixed persona definitions
2. **`{product}_baseline_traces.json`** - Baseline decision traces
3. **`{product}_sensitivity_report.json`** - Machine-readable report
4. **`{product}_sensitivity_report.md`** - Human-readable report

---

## Report Structure

The DecisionSensitivityReport contains:

1. **Top Leverage Steps**
   - Steps with highest sensitivity (fragility × change rate)
   - Ranked by combined score
   - Identifies steps where changes have highest impact

2. **Force Impact Rankings**
   - Forces ranked by total impact on decisions
   - Shows which forces actually move decisions
   - Useful for prioritizing optimizations

3. **Responsive Persona Segments**
   - Persona classes most responsive to changes
   - Groups by cognitive_energy ranges (low/medium/high)
   - Helps target optimizations to specific user segments

4. **Perturbation Results**
   - Detailed results for each perturbation
   - Decision change rates per step
   - Persona-class elasticity
   - Steps affected by each perturbation

---

## Integration Notes

- The sensitivity engine uses a simplified simulation model in `sensitivity_simulator.py`
- For production use, integrate with existing `behavioral_engine_intent_aware.py` to leverage full behavioral logic
- The simulator currently uses simplified force computation; can be enhanced with full behavioral engine integration

---

## Next Steps

1. **Integration with Behavioral Engine**
   - Replace simplified simulator with full behavioral engine integration
   - Use existing state transition logic
   - Leverage intent-aware computation

2. **Enhanced Force Computation**
   - Use actual behavioral engine force calculations
   - Incorporate intent alignment logic
   - Add more sophisticated attribution methods

3. **Visualization**
   - Add sensitivity heatmaps
   - Visualize force impact rankings
   - Show persona segment responsiveness

4. **Benchmark Integration**
   - Compare against benchmark "good" onboarding flows
   - Identify deviations from best practices
   - Quantify improvement opportunities

5. **Validation**
   - Test with real A/B test results
   - Validate sensitivity predictions
   - Calibrate force contribution models

---

## Status

✅ Core architecture implemented
✅ Data structures defined
✅ Perturbation engine functional
✅ Sensitivity analyzer complete
✅ Report generation working
⏳ Integration with behavioral engine (pending)
⏳ Visualization (pending)
⏳ Validation (pending)


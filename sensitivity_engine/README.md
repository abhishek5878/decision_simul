# Decision Sensitivity Simulation Engine

A deterministic, traceable system for analyzing how product onboarding decisions respond to controlled perturbations.

---

## Architecture Overview

### Core Components

1. **Fixed Personas** (`fixed_personas.py`)
   - Generates 100 fixed personas with 7 state variants each
   - Personas remain identical across all experiments
   - Ensures reproducibility and comparability

2. **Extended Decision Traces** (`decision_trace_extended.py`)
   - Captures state_before, forces_applied, decision, state_after
   - Includes force contribution computation (SHAP-style attribution)
   - Immutable decision records

3. **Perturbation Engine** (`perturbation_engine.py`)
   - Applies controlled perturbations (one variable at a time)
   - Supports: reduce_effort, delay_step, increase_value_signal, remove_question, etc.
   - Ensures all other variables remain constant

4. **Sensitivity Analyzer** (`sensitivity_analyzer.py`)
   - Compares baseline vs perturbed traces
   - Computes decision change rates, fragility scores
   - Identifies responsive persona segments

5. **Sensitivity Simulator** (`sensitivity_simulator.py`)
   - Runs personas through product flows
   - Captures detailed decision traces
   - Integrates with behavioral engine logic

6. **Report Generator** (`sensitivity_report.py`)
   - Generates DecisionSensitivityReport
   - Identifies top leverage steps
   - Ranks forces by impact
   - Outputs human-readable reports

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

## Data Structures

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

### ForcesApplied
```python
@dataclass
class ForcesApplied:
    effort: float
    risk: float
    value: float
    trust: float
    intent_mismatch: float
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

---

## Usage

### Basic Usage

```python
from sensitivity_engine.run_sensitivity_analysis import run_sensitivity_analysis

# Run sensitivity analysis for a product
results = run_sensitivity_analysis(
    product_config="trial1",
    n_personas=100,
    output_dir="./sensitivity_results"
)
```

### Command Line

```bash
python sensitivity_engine/run_sensitivity_analysis.py trial1 --personas 100
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
    Perturbation(
        perturbation_type=PerturbationType.INCREASE_VALUE_SIGNAL,
        step_index=0,
        magnitude=0.3,  # 30% increase
        experiment_id="increase_value_step0"
    ),
]

results = run_sensitivity_analysis(
    product_config="trial1",
    perturbations=perturbations
)
```

---

## Output Files

1. **fixed_personas.json** - Fixed persona definitions
2. **{product}_baseline_traces.json** - Baseline decision traces
3. **{product}_sensitivity_report.json** - Machine-readable report
4. **{product}_sensitivity_report.md** - Human-readable report

---

## Report Structure

The DecisionSensitivityReport contains:

1. **Top Leverage Steps**
   - Steps with highest sensitivity (fragility × change rate)
   - Ranked by combined score

2. **Force Impact Rankings**
   - Forces ranked by total impact on decisions
   - Shows which forces actually move decisions

3. **Responsive Persona Segments**
   - Persona classes most responsive to changes
   - Useful for targeting optimizations

4. **Perturbation Results**
   - Detailed results for each perturbation
   - Decision change rates per step
   - Persona-class elasticity

---

## Design Principles

1. **Determinism**: Same personas, same seed → same results
2. **Traceability**: Every decision is traceable to state and forces
3. **Reproducibility**: Fixed personas ensure comparability
4. **One-Variable-At-A-Time**: Controlled perturbations
5. **Explainability**: Force contributions, not predictions
6. **No Black-Box ML**: All logic is explicit and traceable

---

## Integration with Existing System

The sensitivity engine:
- Uses existing behavioral engine logic for state transitions
- Captures decision traces in extended format
- Integrates with product step configurations
- Compatible with intent frames and persona data

---

## Next Steps

1. Integrate with existing behavioral engine for state computation
2. Add more perturbation types as needed
3. Extend force contribution computation (more sophisticated attribution)
4. Add visualization for sensitivity results
5. Benchmark against real-world A/B test results


# Complete Architecture Documentation
## Behavioral Simulation Engine with Intent-Aware Causal Reasoning

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Layers](#architecture-layers)
3. [Core Components](#core-components)
4. [Data Flow](#data-flow)
5. [Behavioral Model](#behavioral-model)
6. [Intent-Aware Layer](#intent-aware-layer)
7. [Integration & Augmentation](#integration--augmentation)
8. [Key Concepts](#key-concepts)
9. [File Structure](#file-structure)
10. [Usage Guide](#usage-guide)
11. [Output Artifacts](#output-artifacts)
12. [Validation & Falsification](#validation--falsification)

---

## 🎯 System Overview

This system simulates user behavior in product onboarding flows using a **multi-layered architecture**:

1. **Behavioral Layer**: Models cognitive states, perceived costs/benefits, and decision-making
2. **Intent-Aware Layer**: Explains WHY users act based on underlying intent, not just behavioral factors
3. **Augmentation Principle**: Intent layer augments (does not replace) behavioral modeling

### Core Philosophy

**Before (Behavioral Only):**
> "Users dropped because effort was high."

**After (Intent-Aware):**
> "Users dropped because the system asked for commitment before satisfying their underlying intent (e.g., comparison, validation, exploration)."

---

## 🏗️ Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    INTENT-AWARE LAYER                        │
│  (dropsim_intent_model.py, behavioral_engine_intent_aware.py)│
│  • Intent inference                                          │
│  • Intent-step alignment                                     │
│  • Intent-conditioned continuation probability              │
│  • Intent-aware failure explanations                         │
└─────────────────────────────────────────────────────────────┘
                            ↓ augments
┌─────────────────────────────────────────────────────────────┐
│              IMPROVED BEHAVIORAL ENGINE                      │
│         (behavioral_engine_improved.py)                      │
│  • Probabilistic decisions                                   │
│  • Energy recovery mechanisms                                │
│  • Value override                                            │
│  • Commitment effect                                         │
│  • Archetype modifiers                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓ builds on
┌─────────────────────────────────────────────────────────────┐
│              BASE BEHAVIORAL ENGINE                          │
│            (behavioral_engine.py)                             │
│  • Cognitive state tracking                                  │
│  • Cost/benefit computation                                 │
│  • State updates                                            │
│  • Persona compilation                                      │
└─────────────────────────────────────────────────────────────┘
                            ↓ uses
┌─────────────────────────────────────────────────────────────┐
│              DATA & FEATURE LAYER                            │
│  (load_dataset.py, derive_features.py)                      │
│  • Persona loading                                          │
│  • Feature derivation                                      │
│  • Latent prior compilation                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧩 Core Components

### 1. Data & Feature Layer

#### `load_dataset.py`
- **Purpose**: Load and sample personas from dataset
- **Key Functions**:
  - `load_and_sample(n, seed, verbose)`: Load n personas with sampling
  - Returns DataFrame with persona attributes

#### `derive_features.py`
- **Purpose**: Derive behavioral features from persona attributes
- **Key Functions**:
  - `derive_all_features(df, verbose)`: Compute all derived features
- **Derived Features**:
  - `digital_literacy_score`: Comfort with technology
  - `aspirational_score`: Growth orientation
  - `trust_score`: Trust in institutions
  - `debt_aversion_score`: Aversion to debt/credit
  - `cc_relevance_score`: Credit card relevance
  - `generation_bucket`: Age-based grouping

---

### 2. Base Behavioral Engine

#### `behavioral_engine.py`

**Purpose**: Core behavioral simulation logic

**Key Classes & Functions**:

##### `STATE_VARIANTS`
Dictionary of initial cognitive states:
- `fresh_motivated`: High energy, low risk
- `tired_commuter`: Low energy, moderate risk
- `distrustful_arrival`: Low trust, high risk
- `browsing_casually`: Low intent, low effort
- `urgent_need`: High intent, high urgency
- `price_sensitive`: High price sensitivity
- `tech_savvy_optimistic`: High digital literacy, high trust

##### `InternalState` (dataclass)
Tracks user's cognitive state:
- `cognitive_energy`: 0-1, depletes with cognitive demand
- `perceived_risk`: 0-1, increases with risk signals
- `perceived_effort`: 0-1, increases with effort demand
- `perceived_value`: 0-1, increases with explicit value
- `perceived_control`: 0-1, increases with reassurance

##### `normalize_persona_inputs(row, derived)`
Converts persona attributes to normalized inputs for simulation

##### `compile_latent_priors(inputs)`
Compiles behavioral traits:
- `Cognitive Capacity`: Ability to process information
- `Risk Tolerance`: Comfort with risk
- `Effort Tolerance`: Willingness to put in effort
- `Value Sensitivity`: Responsiveness to value signals
- `Control Preference`: Need for control/reassurance

##### `initialize_state(variant_name, priors)`
Creates initial `InternalState` based on variant and priors

##### `update_state(state, step_def, priors, step_index, total_steps)`
Updates cognitive state based on step characteristics:
- Decreases `cognitive_energy` based on `cognitive_demand`
- Increases `perceived_risk` based on `risk_signal`
- Increases `perceived_effort` based on `effort_demand`
- Updates `perceived_value` based on `explicit_value`
- Updates `perceived_control` based on `reassurance_signal`

##### `should_continue(state, priors)`
**Original (Deterministic)**: Binary decision
```python
costs = cognitive_cost + effort_cost + risk_cost
benefits = value_yield + reassurance_yield
return benefits > costs
```

##### `identify_failure_reason(costs, state)`
Identifies why user dropped:
- `System 2 fatigue`: High cognitive cost
- `Loss aversion`: High risk cost
- `Effort aversion`: High effort cost
- `Unclear value`: Low value yield

---

### 3. Improved Behavioral Engine

#### `behavioral_engine_improved.py`

**Purpose**: Enhanced behavioral simulation with realism improvements

**Key Improvements**:

##### Probabilistic Decisions
**Before**: `should_continue()` → binary True/False
**After**: `should_continue_probabilistic()` → probability 0-1

```python
def should_continue_probabilistic(state, priors, step_index, total_steps, modifiers):
    # Compute advantage (benefits - costs)
    advantage = (value_yield + reassurance_yield) - (cognitive_cost + effort_cost + risk_cost)
    
    # Apply modifiers (archetype, commitment effect, value override)
    advantage += commitment_boost + value_override + archetype_modifier
    
    # Convert to probability using sigmoid
    prob = 1 / (1 + np.exp(-advantage * 5))
    
    # Apply minimum persistence floor
    prob = max(prob, 0.05)  # At least 5% chance
    
    return prob
```

##### Energy Recovery
**Before**: `cognitive_energy` only decreases
**After**: `update_cognitive_energy_with_recovery()` allows recovery

```python
def update_cognitive_energy_with_recovery(current_energy, cognitive_cost, value_yield, 
                                         reassurance_yield, progress, priors):
    # Base depletion
    new_energy = current_energy - cognitive_cost
    
    # Recovery mechanisms
    if value_yield > 0.3:  # High value
        recovery = value_yield * 0.2
        new_energy += recovery
    
    if progress > 0.5:  # Progress boost
        progress_boost = (progress - 0.5) * 0.1
        new_energy += progress_boost
    
    if reassurance_yield > 0.4:  # Reassurance recovery
        reassurance_recovery = reassurance_yield * 0.15
        new_energy += reassurance_recovery
    
    return np.clip(new_energy, 0.0, 1.0)
```

##### Value Override
High perceived value can override effort/fatigue:
```python
if perceived_value > 0.7:
    effective_cognitive_cost *= 0.7  # Reduce cost by 30%
    effective_effort_cost *= 0.7
```

##### Commitment Effect
Persistence increases with progress:
```python
commitment_boost = (step_index / total_steps) * 0.3  # Up to 30% boost
```

##### Archetype Modifiers
Different user archetypes behave differently:
```python
def compute_archetype_modifiers(priors, persona_inputs):
    # Base persistence varies by archetype
    # Value sensitivity varies by archetype
    # Fatigue resilience varies by archetype
    # Risk tolerance multiplier varies by archetype
```

##### Individual Variance
Adds personality noise to prevent identical behavior:
```python
personality_noise = np.random.normal(0, 0.15)
final_prob = np.clip(continuation_prob + personality_noise, 0.05, 0.95)
```

---

### 4. Intent-Aware Layer

#### `dropsim_intent_model.py`

**Purpose**: Intent modeling and inference

**Key Components**:

##### `IntentFrame` (dataclass)
Represents a user's underlying intent:
```python
@dataclass
class IntentFrame:
    intent_id: str                    # e.g., "compare_options"
    description: str                  # Human-readable description
    primary_goal: str                 # What user is trying to achieve
    tolerance_for_effort: float       # 0-1, how much effort they'll accept
    tolerance_for_risk: float        # 0-1, how much risk they'll accept
    expected_value_type: str          # "comparison", "speed", "certainty", etc.
    commitment_threshold: float       # 0-1, commitment before seeing value
    expected_reward: str              # What they expect to get
    acceptable_friction: float        # 0-1, friction tolerance
    typical_exit_triggers: List[str] # What causes them to leave
    expected_completion_behavior: str  # How they typically complete
```

##### Canonical Intent Set
6 canonical intents defined:

1. **compare_options**
   - Goal: Compare multiple options before deciding
   - Commitment threshold: 0.3 (low - doesn't want to commit early)
   - Expected value: Comparison view
   - Exit trigger: Asked for personal info before showing options

2. **validate_choice**
   - Goal: Validate their choice is correct
   - Commitment threshold: 0.5 (moderate)
   - Expected value: Certainty/confirmation
   - Exit trigger: Can't verify without committing

3. **learn_basics**
   - Goal: Learn about the product
   - Commitment threshold: 0.2 (very low - just learning)
   - Expected value: Clarity/education
   - Exit trigger: Forced to sign up to learn

4. **quick_decision**
   - Goal: Make fast decision
   - Commitment threshold: 0.6 (higher - will commit if fast)
   - Expected value: Speed
   - Exit trigger: Too many steps, slow loading

5. **price_check**
   - Goal: Check pricing/costs
   - Commitment threshold: 0.2 (low - just checking)
   - Expected value: Clarity on pricing
   - Exit trigger: Pricing hidden behind signup

6. **eligibility_check**
   - Goal: Check if eligible
   - Commitment threshold: 0.4 (moderate)
   - Expected value: Certainty on eligibility
   - Exit trigger: Eligibility check requires too much info

##### `infer_intent_distribution(...)`
Infers probabilistic intent distribution from entry signals:

**Inputs**:
- `entry_page_text`: Text from landing page
- `cta_phrasing`: CTA button text
- `product_steps`: Step definitions with `intent_signals`
- `persona_attributes`: Persona traits
- `product_type`: Type of product

**Output**:
```python
{
    "intent_distribution": {
        "compare_options": 0.42,
        "learn_basics": 0.31,
        "quick_decision": 0.18,
        ...
    },
    "primary_intent": "compare_options",
    "primary_intent_confidence": 0.42
}
```

**Inference Logic**:
1. **CTA Phrasing Analysis**:
   - "Find the Best", "Compare" → boosts `compare_options`
   - "Check Eligibility" → boosts `eligibility_check`
   - "60 seconds", "Quick" → boosts `quick_decision`

2. **Product Steps Analysis**:
   - Uses `intent_signals` from step definitions
   - First step's `intent_signals` heavily weighted

3. **Persona Attributes**:
   - High intent → boosts `quick_decision`
   - Risk-averse → boosts `validate_choice`
   - High urgency → boosts `quick_decision`

4. **Product Type**:
   - Financial products → boosts `eligibility_check`, `validate_choice`
   - E-commerce → boosts `compare_options`, `price_check`

##### `compute_intent_alignment_score(step, intent_frame, step_index, total_steps)`
Computes how well a step aligns with user's intent (0-1 scale).

**Alignment Factors**:
1. **Intent Signals** (if available in step):
   ```python
   if 'intent_signals' in step:
       alignment = step['intent_signals'][intent_frame.intent_id]
   ```

2. **Commitment Threshold Check**:
   ```python
   if step_commitment > intent_frame.commitment_threshold:
       alignment -= excess * 0.5  # Penalty
   ```

3. **Comparison Availability** (for `compare_options`):
   ```python
   if intent_frame.intent_id == 'compare_options':
       if not step.get('comparison_available', False) and step_index > 2:
           alignment -= 0.3  # Major penalty
   ```

4. **Value Type Alignment**:
   ```python
   if step_value_type != intent_frame.expected_value_type:
       alignment -= 0.2
   ```

5. **Effort/Risk Tolerance**:
   ```python
   if step_effort > intent_frame.acceptable_friction:
       alignment -= excess * 0.3
   ```

##### `compute_intent_conditioned_continuation_prob(base_prob, intent_frame, step, ...)`
Adjusts continuation probability based on intent alignment:

```python
alignment = compute_intent_alignment_score(...)

# High alignment → boost probability
if alignment >= 0.8:
    intent_modifier = 1.0 + (alignment - 0.8) * 0.5  # Up to 10% boost

# Low alignment → reduce probability
elif alignment < 0.5:
    intent_modifier = alignment * 1.5  # Reduce by up to 50%

adjusted_prob = base_prob * intent_modifier

# Intent-specific adjustments
if intent_frame.intent_id == "quick_decision":
    if step.get('delay_to_value', 5) > 3:
        adjusted_prob *= 0.8  # Penalize delays
```

##### `identify_intent_mismatch(step, intent_frame, step_index, total_steps, failure_reason)`
Identifies if failure was due to intent mismatch:

**Returns**:
```python
{
    'is_intent_mismatch': bool,
    'mismatch_score': float,  # 0-1, higher = worse mismatch
    'violated_intent': str,
    'mismatch_type': str,  # "commitment_threshold", "effort_tolerance", etc.
    'explanation': str  # Human-readable explanation
}
```

---

#### `behavioral_engine_intent_aware.py`

**Purpose**: Intent-aware simulation engine

**Key Functions**:

##### `simulate_persona_trajectory_intent_aware(...)`
Simulates one persona trajectory with intent awareness:

1. **Sample Intent**:
   ```python
   sampled_intent_id = np.random.choice(intent_ids, p=intent_probs)
   intent_frame = CANONICAL_INTENTS[sampled_intent_id]
   ```

2. **For Each Step**:
   - Compute base continuation probability (from improved engine)
   - Compute intent alignment
   - Adjust probability based on alignment
   - Detect intent mismatches
   - Record intent information in journey

3. **Failure Reason**:
   ```python
   if intent_analysis['is_intent_mismatch'] and mismatch_score > 0.4:
       failure_reason = f"Intent mismatch: {intent_analysis['mismatch_type']}"
   else:
       failure_reason = behavioral_failure_reason
   ```

##### `run_intent_aware_simulation(df, product_steps, intent_distribution, ...)`
Runs batch simulation with intent awareness:
- Infers intent distribution if not provided
- Simulates all personas with intent sampling
- Tracks intent mismatches
- Returns DataFrame with intent information

##### `generate_intent_analysis(result_df, product_steps)`
Generates intent-aware analysis:

1. **Intent Profile**: Distribution of intents across trajectories
2. **Intent-Weighted Funnel**: Drop rates by intent for each step
3. **Intent Conflict Matrix**: Alignment scores for each step-intent pair
4. **Intent Explanations**: Human-readable failure explanations

##### `export_intent_artifacts(result_df, product_steps, output_dir)`
Exports all required artifacts:
- `intent_profile.json`
- `intent_weighted_funnel.json`
- `intent_conflict_matrix.json`
- `intent_explanation.md`

---

## 🔄 Data Flow

### Complete Simulation Flow

```
1. LOAD DATA
   load_dataset.py → DataFrame of personas
   
2. DERIVE FEATURES
   derive_features.py → Add behavioral features
   
3. INFER INTENT DISTRIBUTION
   dropsim_intent_model.infer_intent_distribution()
   → Uses: entry page text, CTA phrasing, product steps, persona attributes
   → Returns: {intent_id: probability}
   
4. FOR EACH PERSONA:
   a. Normalize inputs (normalize_persona_inputs)
   b. Compile latent priors (compile_latent_priors)
   c. Compute archetype modifiers (compute_archetype_modifiers)
   
5. FOR EACH VARIANT (7 variants per persona):
   a. Initialize state (initialize_state)
   b. Sample intent from distribution
   c. FOR EACH STEP:
      - Update state (update_state_improved)
      - Compute costs/benefits
      - Compute base continuation probability (should_continue_probabilistic)
      - Compute intent alignment (compute_intent_alignment_score)
      - Adjust probability for intent (compute_intent_conditioned_continuation_prob)
      - Add individual variance
      - Check for intent mismatch (identify_intent_mismatch)
      - Make decision (random draw from probability)
      - If drop: identify failure reason (intent-aware or behavioral)
      - Record journey with intent information
   
6. AGGREGATE RESULTS
   - Completion rates
   - Exit steps
   - Failure reasons
   - Intent mismatches
   
7. GENERATE ANALYSIS
   generate_intent_analysis()
   → Intent profile
   → Intent-weighted funnel
   → Intent conflict matrix
   → Intent explanations
   
8. EXPORT ARTIFACTS
   export_intent_artifacts()
   → JSON files
   → Markdown explanations
```

---

## 🧠 Behavioral Model

### Cognitive State Evolution

```
Initial State (variant-dependent)
    ↓
Step 1: Update State
    - cognitive_energy -= cognitive_cost
    - perceived_risk += risk_signal
    - perceived_effort += effort_demand
    - perceived_value += explicit_value
    - perceived_control += reassurance_signal
    ↓
Compute Continuation Probability
    - base_prob = sigmoid(advantage)
    - advantage = benefits - costs
    - Apply modifiers (commitment, value override, archetype)
    - Apply intent alignment adjustment
    - Add individual variance
    ↓
Decision: Continue or Drop?
    ↓
If Continue: Next Step
If Drop: Record failure reason
```

### Cost/Benefit Computation

**Costs**:
- `cognitive_cost = cognitive_demand * (1 - cognitive_energy)`
- `effort_cost = effort_demand * (1 - effort_tolerance)`
- `risk_cost = risk_signal * (1 - risk_tolerance)`

**Benefits**:
- `value_yield = explicit_value * value_sensitivity`
- `reassurance_yield = reassurance_signal * control_preference`

**Advantage**:
```python
advantage = (value_yield + reassurance_yield) - (cognitive_cost + effort_cost + risk_cost)
```

### Energy Recovery

```python
# Base depletion
cognitive_energy -= cognitive_cost

# Recovery mechanisms
if value_yield > 0.3:
    cognitive_energy += value_yield * 0.2  # Value recovery

if progress > 0.5:
    cognitive_energy += (progress - 0.5) * 0.1  # Progress boost

if reassurance_yield > 0.4:
    cognitive_energy += reassurance_yield * 0.15  # Reassurance recovery
```

---

## 🎯 Intent-Aware Layer

### Intent Inference Flow

```
Entry Signals
    ↓
CTA Phrasing Analysis
    - "Find the Best" → compare_options
    - "60 seconds" → quick_decision
    - "Check Eligibility" → eligibility_check
    ↓
Product Steps Analysis
    - Use intent_signals from first step
    - Weight by signal strength
    ↓
Persona Attributes
    - High intent → quick_decision
    - Risk-averse → validate_choice
    ↓
Product Type
    - Financial → eligibility_check
    - E-commerce → compare_options
    ↓
Normalize to Probabilities
    ↓
Intent Distribution
```

### Intent-Step Alignment Flow

```
For Each Step:
    ↓
Get Intent Signals (if available)
    alignment = step['intent_signals'][intent_id]
    ↓
Check Commitment Threshold
    if step_commitment > intent.commitment_threshold:
        alignment -= penalty
    ↓
Check Comparison Availability (for compare_options)
    if not comparison_available and step_index > 2:
        alignment -= 0.3
    ↓
Check Value Type Match
    if step_value_type != intent.expected_value_type:
        alignment -= 0.2
    ↓
Check Effort/Risk Tolerance
    if step_effort > intent.acceptable_friction:
        alignment -= penalty
    ↓
Final Alignment Score (0-1)
```

### Intent-Conditioned Decision Flow

```
Base Continuation Probability (from behavioral engine)
    ↓
Compute Intent Alignment
    alignment = compute_intent_alignment_score(...)
    ↓
Apply Intent Modifier
    if alignment >= 0.8:
        modifier = 1.0 + (alignment - 0.8) * 0.5  # Boost
    elif alignment < 0.5:
        modifier = alignment * 1.5  # Reduce
    ↓
Apply Intent-Specific Adjustments
    - quick_decision: Penalize delays
    - compare_options: Penalize no comparison
    - learn_basics: Boost educational content
    ↓
Final Continuation Probability
```

---

## 🔗 Integration & Augmentation

### How Intent Layer Augments Behavioral Engine

**Principle**: Intent layer **augments**, does **not replace** behavioral modeling.

**Behavioral Factors Still Considered**:
- Cognitive energy
- Perceived risk
- Perceived effort
- Perceived value
- Perceived control

**Intent Adds**:
- Causal explanation layer
- Intent-step alignment
- Intent-conditioned probability adjustment
- Intent-aware failure reasons

**Integration Point**:
```python
# Base probability from behavioral engine
base_prob = should_continue_probabilistic(state, priors, step_index, total_steps, modifiers)

# Intent alignment
alignment = compute_intent_alignment_score(step, intent_frame, step_index, total_steps)

# Intent-conditioned adjustment
continuation_prob = compute_intent_conditioned_continuation_prob(
    base_prob, intent_frame, step, step_index, total_steps, state
)

# Final decision
final_prob = continuation_prob + personality_noise
```

### Backward Compatibility

- Can run without intent layer (original improved engine)
- Intent layer is optional parameter
- Existing reports still work
- Behavioral factors always considered

---

## 📚 Key Concepts

### 1. Cognitive State
Internal representation of user's mental state:
- **cognitive_energy**: Mental resources available (depletes with use)
- **perceived_risk**: How risky the step feels
- **perceived_effort**: How much effort required
- **perceived_value**: How valuable the step feels
- **perceived_control**: How much control user feels

### 2. Latent Priors
Compiled behavioral traits from persona attributes:
- **Cognitive Capacity**: Ability to process information
- **Risk Tolerance**: Comfort with risk
- **Effort Tolerance**: Willingness to put in effort
- **Value Sensitivity**: Responsiveness to value signals
- **Control Preference**: Need for control/reassurance

### 3. State Variants
Different initial conditions for same persona:
- **fresh_motivated**: High energy, low risk
- **tired_commuter**: Low energy, moderate risk
- **distrustful_arrival**: Low trust, high risk
- etc.

### 4. Intent Frames
User's underlying goal/intent:
- **compare_options**: Wants to compare before deciding
- **validate_choice**: Wants to validate their choice
- **learn_basics**: Wants to learn about product
- **quick_decision**: Wants fast decision
- **price_check**: Wants to check pricing
- **eligibility_check**: Wants to check eligibility

### 5. Intent Alignment
How well a step matches user's intent (0-1 scale):
- **1.0**: Perfect alignment
- **0.8-1.0**: Good alignment (may boost continuation)
- **0.5-0.8**: Moderate alignment
- **<0.5**: Poor alignment (mismatch, reduces continuation)

### 6. Intent Mismatch
When step characteristics don't align with user's intent:
- **commitment_threshold**: Step requires more commitment than intent allows
- **effort_tolerance**: Step requires more effort than intent allows
- **risk_tolerance**: Step has more risk than intent allows
- **value_type_mismatch**: Step provides wrong type of value

### 7. Probabilistic Decisions
Continuation is probabilistic, not deterministic:
- Base probability from behavioral factors
- Adjusted by intent alignment
- Individual variance added
- Minimum persistence floor (5%)

### 8. Energy Recovery
Cognitive energy can recover:
- High value steps → energy recovery
- Progress milestones → progress boost
- Reassurance signals → reassurance recovery

### 9. Value Override
High perceived value can override negative factors:
- If `perceived_value > 0.7`:
  - Effective cognitive cost reduced by 30%
  - Effective effort cost reduced by 30%

### 10. Commitment Effect
Persistence increases with progress:
- Early steps: Lower continuation probability
- Later steps: Higher continuation probability (sunk cost)

---

## 📁 File Structure

```
inertia_labs/
├── Core Behavioral Engine
│   ├── behavioral_engine.py              # Base behavioral simulation
│   ├── behavioral_engine_improved.py     # Improved with realism
│   └── behavioral_engine_intent_aware.py # Intent-aware layer
│
├── Intent Modeling
│   ├── dropsim_intent_model.py           # Intent frames, inference, alignment
│   └── dropsim_intent_validation.py     # Validation & falsification
│
├── Data & Features
│   ├── load_dataset.py                   # Load personas
│   └── derive_features.py                # Derive behavioral features
│
├── Product Step Definitions
│   ├── credigo_11_steps.py               # Original Credigo steps
│   ├── credigo_ss_steps_improved.py      # Improved Credigo steps (intent-aware)
│   └── blink_money_steps.py             # Blink Money steps
│
├── Runners
│   ├── run_credigo_improved.py          # Run improved simulation for Credigo
│   ├── run_blink_money_improved.py      # Run improved simulation for Blink Money
│   └── run_intent_aware_simulation.py   # Run intent-aware simulation
│
├── Reporting
│   ├── generate_pdf_report.py           # Generate PDF from results
│   └── generate_improved_pdf_report.py  # Generate PDF from improved results
│
└── Documentation
    ├── ARCHITECTURE_COMPLETE.md          # This file
    ├── INTENT_LAYER_IMPLEMENTATION.md    # Intent layer details
    ├── INTENT_LAYER_SUMMARY.md          # Intent layer overview
    ├── INTENT_LAYER_QUICK_START.md      # Quick start guide
    ├── INTENT_LAYER_VALIDATION.md       # Validation results
    ├── BEHAVIORAL_MODEL_AUDIT.md        # Behavioral model audit
    ├── IMPROVEMENTS_SUMMARY.md          # Improvements summary
    └── CREDIGO_SS_INTENT_ANALYSIS.md    # Credigo SS analysis
```

---

## 🚀 Usage Guide

### 1. Run Improved Behavioral Simulation (No Intent)

```bash
# Credigo
python3 run_credigo_improved.py

# Blink Money
python3 run_blink_money_improved.py
```

**Output**: `credigo_improved_results.json` or `blink_money_improved_results.json`

### 2. Run Intent-Aware Simulation

```bash
# Credigo with intent-aware layer
python3 run_intent_aware_simulation.py --product credigo --n 1000

# Blink Money with intent-aware layer
python3 run_intent_aware_simulation.py --product blink_money --n 1000
```

**Output**:
- `intent_profile.json`
- `intent_weighted_funnel.json`
- `intent_conflict_matrix.json`
- `intent_explanation.md`

### 3. Generate PDF Reports

```bash
# From improved results
python3 generate_improved_pdf_report.py --input credigo_improved_results.json --output report.pdf

# From intent-aware results (use intent_explanation.md)
```

---

## 📊 Output Artifacts

### Behavioral Simulation Output

**`credigo_improved_results.json`**:
```json
{
  "simulation_type": "improved_behavioral_engine",
  "total_personas": 1000,
  "overall_completion_rate": 0.152,
  "funnel_analysis": {
    "Step Name": {
      "entered": 7000,
      "exited": 3593,
      "drop_rate": 51.3
    }
  },
  "failure_reasons": {
    "System 2 fatigue": 5935,
    "Loss aversion": 2
  },
  "energy_recovery": {
    "total_events": 515,
    "recovery_rate": 3.6
  }
}
```

### Intent-Aware Output

**`intent_profile.json`**:
```json
{
  "compare_options": 0.247,
  "eligibility_check": 0.178,
  "validate_choice": 0.164,
  "learn_basics": 0.137,
  "quick_decision": 0.137,
  "price_check": 0.137
}
```

**`intent_weighted_funnel.json`**:
```json
{
  "Step Name": {
    "compare_options": {
      "entered": 1688,
      "exited": 888,
      "drop_rate": 52.6
    },
    "quick_decision": {
      "entered": 954,
      "exited": 612,
      "drop_rate": 64.2
    }
  }
}
```

**`intent_conflict_matrix.json`**:
```json
{
  "Step Name": {
    "compare_options": {
      "alignment": 0.70,
      "is_conflict": false
    },
    "validate_choice": {
      "alignment": 0.10,
      "is_conflict": true
    }
  }
}
```

**`intent_explanation.md`**:
- Intent distribution
- Intent-step conflicts
- Intent-aware failure explanations

---

## ✅ Validation & Falsification

### Validation Tests

1. **Intent Sensitivity**: Does changing intent distribution change conclusions?
2. **Mismatch Correlation**: Do intent mismatches correlate with actual drop-offs?
3. **Explanation Specificity**: Are explanations specific enough to be falsifiable?

### Falsification Tests

1. **Step Removal Impact**: Does removing a step resolve intent conflict?
2. **Intent Mix Impact**: Does same UI perform differently under different intent mixes?
3. **Explanation Specificity**: Can explanations be falsified?

### Success Criteria

1. ✅ **Different intents → different diagnoses**
   - Evidence: `quick_decision` has 64% drop vs `compare_options` has 48% drop

2. ✅ **"Unclear value" is derived, not default**
   - Failure reasons include "Intent mismatch: {type}"
   - Explanations reference intent characteristics

3. ✅ **Reports explain why users wanted something different**
   - "Users entered with comparison intent but encountered commitment-heavy step"
   - References specific thresholds and expectations

---

## 🔧 Configuration

### Product Step Definition Format

```python
PRODUCT_STEPS = {
    "Step Name": {
        # Behavioral attributes
        "cognitive_demand": 0.3,
        "effort_demand": 0.2,
        "risk_signal": 0.15,
        "irreversibility": 0,
        "delay_to_value": 5,
        "explicit_value": 0.3,
        "reassurance_signal": 0.4,
        "authority_signal": 0.2,
        
        # Intent-aware attributes (optional but recommended)
        "cta_phrasing": "Find the Best Credit Card",
        "value_proposition": "Quick credit card comparison",
        "commitment_gate": False,
        "comparison_available": False,
        "personal_info_required": False,
        "intent_signals": {
            "compare_options": 0.7,
            "quick_decision": 0.8,
            "learn_basics": 0.3,
            "eligibility_check": 0.2,
            "price_check": 0.4,
            "validate_choice": 0.3
        },
        "description": "Step description"
    }
}
```

---

## 📈 Performance Characteristics

### Simulation Speed
- **1000 personas**: ~35-40 seconds
- **7 variants per persona**: 7,000 total trajectories
- **Per trajectory**: ~0.005 seconds

### Memory Usage
- **1000 personas**: ~50-100 MB
- **Results JSON**: ~5-10 MB

### Scalability
- Linear scaling with number of personas
- Can handle 10,000+ personas (takes ~6-7 minutes)

---

## 🎓 Behavioral Science Grounding

### Cognitive Load Theory
- **cognitive_demand**: Represents cognitive load
- **cognitive_energy**: Limited cognitive resources
- **System 2 fatigue**: Depletion of cognitive resources

### Prospect Theory
- **Loss aversion**: Risk costs weighted more than gains
- **Risk tolerance**: Individual differences in risk perception

### Information Foraging Theory
- **compare_options intent**: Users forage for information before committing
- **Value signals**: Guide information search

### Temporal Discounting
- **quick_decision intent**: Users discount future value for immediate decisions
- **Delay to value**: Affects continuation probability

### Sunk Cost Effect
- **Commitment effect**: Persistence increases with progress
- **Irreversibility**: Steps that can't be undone increase commitment

---

## 🔮 Future Enhancements

1. **LLM-Enhanced Intent Inference**: Use LLM to infer intents from product copy
2. **Dynamic Intent Shifts**: Model how intents change during journey
3. **Intent-Specific Interventions**: Recommend fixes based on intent mismatches
4. **Multi-Intent Modeling**: Users can have multiple simultaneous intents
5. **Intent Calibration**: Calibrate intent distributions with real user data
6. **A/B Testing Integration**: Test different flows with different intent distributions

---

## 📝 Summary

This architecture provides:

1. **Behavioral Simulation**: Realistic modeling of user cognitive states and decisions
2. **Intent-Aware Reasoning**: Causal explanations based on user intent
3. **Augmentation Principle**: Intent layer enhances, doesn't replace behavioral modeling
4. **Actionable Insights**: Identifies specific intent mismatches and recommends fixes
5. **Comprehensive Output**: Multiple artifacts for different analysis needs

**The system transforms from "users dropped because effort was high" to "users dropped because the system asked for commitment before satisfying their comparison intent" - providing deeper, more actionable insights for product improvement.**

---

**Last Updated**: 2025-12-30  
**Version**: 2.0 (Intent-Aware)


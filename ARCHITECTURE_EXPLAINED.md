# DropSim Architecture & Working Explanation

## 🎯 Overview

DropSim is a **deterministic behavioral simulation engine** that predicts why users drop off at each step of a product funnel. Unlike black-box ML models, DropSim uses behavioral economics principles to explain drop-offs with labeled reasons (System 2 fatigue, Loss aversion, Temporal discounting, Low ability).

---

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DROPSIM SYSTEM ARCHITECTURE                   │
└─────────────────────────────────────────────────────────────────┘

INPUT LAYER
├── Product Screenshots/URL/Text
├── Persona Descriptions
└── Target Group Filters
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│              LLM INGESTION LAYER (dropsim_llm_ingestion.py)     │
│  • Extracts product steps from screenshots                      │
│  • Infers personas from descriptions                            │
│  • Classifies fintech archetypes                                │
│  • Generates LiteScenario (human-friendly format)               │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│              WIZARD LAYER (dropsim_wizard.py)                   │
│  • Orchestrates LLM ingestion + simulation                      │
│  • Consolidates product context (URL, text, screenshots)        │
│  • Runs end-to-end pipeline                                     │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│         PERSONA DATABASE LAYER (load_dataset.py)                │
│  • Loads 1M+ personas from Hugging Face                        │
│  • Filters by target group (age, location, etc.)                │
│  • Samples N personas for simulation                            │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│      PERSONA COMPILATION LAYER (behavioral_engine.py)           │
│  • Converts raw persona fields → Normalized inputs [0,1]        │
│  • Compiles 9 latent priors (CC, FR, RT, LAM, ET, TB, DR, CN, MS)│
│  • Extracts meta tags for filtering                             │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│         BEHAVIORAL SIMULATION ENGINE (behavioral_engine.py)     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ STATE ENGINE                                              │  │
│  │ • Tracks 5 internal state variables                       │  │
│  │ • Computes costs/yields per step                          │  │
│  │ • Applies transition costs (commitment gates)              │  │
│  │ • Decides continue vs drop                                │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ STATE VARIANTS                                            │  │
│  │ • 7 deterministic variants per persona                    │  │
│  │ • Models same person on different days                    │  │
│  │ • (fresh_motivated, tired_commuter, etc.)                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│      AGGREGATION LAYER (dropsim_aggregation_v2.py)              │
│  • Computes failure rates per step                             │
│  • Identifies dominant failure reasons                         │
│  • Analyzes consistency across variants                        │
│  • Generates interpretations (structural, intent-sensitive)     │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│      CONTEXT GRAPH LAYER (dropsim_context_graph.py)             │
│  • Captures event-level behavioral traces                      │
│  • Builds directed graph (nodes=steps, edges=transitions)       │
│  • Tracks energy/risk evolution across steps                    │
│  • Enables path-based reasoning and causal inspection          │
│  • Query functions: paths to failure, energy collapse, etc.     │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│   COUNTERFACTUAL ENGINE (dropsim_counterfactuals.py)            │
│  • Simulates "what-if" interventions                            │
│  • Quantifies impact of changes (effort, risk, cognitive)       │
│  • Ranks interventions by effectiveness                        │
│  • Computes sensitivity map and robustness score               │
│  • Answers: "What would prevent the drop?"                     │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│   REALITY CALIBRATION LAYER (dropsim_calibration.py)           │
│  • Compares simulated vs observed outcomes                     │
│  • Identifies systematic prediction errors                     │
│  • Adjusts confidence, not logic                               │
│  • Tracks calibration over time                                │
│  • Answers: "Where is the model wrong and by how much?"      │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│   DECISION ENGINE (dropsim_decision_engine.py)                 │
│  • Converts insights into actionable recommendations          │
│  • Quantifies expected impact                                 │
│  • Explains reasoning with evidence                           │
│  • Ranks by priority (impact × confidence / complexity)       │
│  • Answers: "What should we change first — and why?"         │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│   DEPLOYMENT GUARD (dropsim_deployment_guard.py)               │
│  • Validates deployment safety                                │
│  • Assesses risks and generates monitoring plans             │
│  • Enables shadow evaluation (dry-run mode)                   │
│  • Tracks post-deployment performance                         │
│  • Answers: "Is this safe to deploy?"                         │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│   REASONING & ABSTRACTION LAYER (dropsim_interpreter.py)       │
│  • Converts raw findings into high-level insights             │
│  • Identifies root causes and failure modes                   │
│  • Detects structural patterns                                │
│  • Generates behavioral narratives                            │
│  • Answers: "What is fundamentally broken and why?"          │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│              OUTPUT LAYER                                        │
│  • Step-level failure analysis                                 │
│  • Narrative summaries                                         │
│  • Context graph (nodes, edges, dominant paths)                 │
│  • Exportable traces (JSON/CSV)                                │
│  • Plot-ready data for visualization                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔬 Core Components Deep Dive

### 1. Persona Database Layer (`load_dataset.py`)

**Purpose**: Load and sample personas from the Nemotron-Personas-India dataset.

**How it works**:
- **Hugging Face Integration**: Loads 1M+ personas directly from `nvidia/Nemotron-Personas-India`
- **Language Splits**: Supports `en_IN`, `hi_Deva_IN`, `hi_Latn_IN`
- **Sampling**: Randomly samples N personas with reproducibility (seed-based)
- **Progress Tracking**: Shows download progress with percentages automatically

**Key Functions**:
```python
load_and_sample(n=1000, seed=42, language="en_IN", use_huggingface=True)
# Returns: (DataFrame with personas, metadata dict)
```

**Data Structure**:
- 28 fields per persona: demographics, geography, interests, persona descriptions
- Example fields: `age`, `sex`, `state`, `occupation`, `education_level`, `professional_persona`, etc.

---

### 2. Persona Compilation Layer (`behavioral_engine.py`)

**Purpose**: Convert raw persona data into behavioral priors.

**Process**:

#### Step 1: Normalize Raw Inputs
Raw persona fields → Normalized [0,1] inputs:
- `SEC` (Socio-Economic Class): 0.0 (low) to 1.0 (high)
- `UrbanRuralTier`: 0.0 (rural) to 1.0 (metro)
- `DigitalLiteracy`: 0.0 (low) to 1.0 (high)
- `FamilyInfluence`: 0.0 (low) to 1.0 (high)
- ... (14 total fields)

#### Step 2: Compile Latent Priors
Normalized inputs → 9 behavioral priors:

1. **CC (Cognitive Capacity)**: How much cognitive energy a person has
   - Formula: `0.35 × DigitalLiteracy + 0.25 × EnglishProficiency + 0.20 × HobbyDiversity + 0.20 × AgeBucket`
   - Range: [0.2, 0.9]

2. **FR (Fatigue Rate)**: How fast cognitive energy depletes
   - Formula: `1 - (0.5 × DigitalLiteracy + 0.3 × AgeBucket + 0.2 × EnglishProficiency)`
   - Range: [0.1, 0.8]
   - Higher FR = faster burnout

3. **RT (Risk Tolerance)**: Willingness to take risks
   - Formula: `0.4 × SEC + 0.3 × (1 - FamilyInfluence) + 0.2 × AspirationalLevel + 0.1 × (1 - PriceSensitivity)`
   - Range: [0.1, 0.9]

4. **LAM (Loss Aversion Multiplier)**: How much losses loom larger than gains
   - Formula: `1 + (0.6 × FamilyInfluence + 0.4 × PriceSensitivity)`
   - Range: [1.0, 2.5]
   - Higher LAM = more loss-averse

5. **ET (Effort Tolerance)**: Ability to handle effortful tasks
   - Formula: `0.5 × DigitalLiteracy + 0.3 × HobbyDiversity + 0.2 × CareerAmbition`
   - Range: [0.2, 0.9]

6. **TB (Trust Baseline)**: Baseline trust in digital systems
   - Formula: `0.4 × UrbanRuralTier + 0.3 × ProfessionalSector + 0.3 × InfluencerTrust`
   - Range: [0.2, 0.9]

7. **DR (Discount Rate)**: How much future value is discounted
   - Formula: `0.5 × PriceSensitivity + 0.3 × (1 - AgeBucket) + 0.2 × AspirationalLevel`
   - Range: [0.05, 0.9]
   - Higher DR = more impatient

8. **CN (Control Need)**: Need for control/autonomy
   - Formula: `0.5 × FamilyInfluence + 0.3 × RegionalCulture + 0.2 × (1 - UrbanRuralTier)`
   - Range: [0.2, 0.9]

9. **MS (Motivation Strength)**: Initial motivation/intent
   - Formula: `0.6 × AspirationalLevel + 0.4 × DigitalLiteracy`
   - Range: [0.3, 1.0]

**Key Insight**: These priors are **fixed** for each persona - they represent the person's behavioral constraints.

---

### 3. State Variants (`behavioral_engine.py`)

**Purpose**: Model the same persona in different internal states (arrival conditions).

**Concept**: The same person behaves differently depending on:
- Energy level (tired vs fresh)
- Motivation (browsing vs urgent need)
- Trust state (distrustful vs optimistic)
- Context (commuting vs relaxed)

**7 Default State Variants**:

1. **fresh_motivated**
   - `cognitive_energy = 0.9 × CC`
   - `perceived_value = 0.8`
   - `perceived_risk = 0.1`
   - High motivation, high energy

2. **tired_commuter**
   - `cognitive_energy = 0.5 × CC`
   - `perceived_value = 0.6`
   - `perceived_risk = 0.2`
   - Low energy, moderate motivation

3. **distrustful_arrival**
   - `cognitive_energy = 0.8 × CC`
   - `perceived_value = 0.6`
   - `perceived_risk = 0.4`
   - High risk perception, low trust

4. **browsing_casually**
   - `cognitive_energy = 0.9 × CC`
   - `perceived_value = 0.3`
   - `perceived_risk = 0.1`
   - Low urgency, exploring

5. **urgent_need**
   - `cognitive_energy = 0.7 × CC`
   - `perceived_value = 0.9`
   - `perceived_risk = 0.2`
   - High urgency, strong motivation

6. **price_sensitive**
   - `cognitive_energy = 0.8 × CC`
   - `perceived_value = 0.4`
   - `perceived_risk = 0.3`
   - Highly price-conscious

7. **tech_savvy_optimistic**
   - `cognitive_energy = 0.95 × CC`
   - `perceived_value = 0.7`
   - `perceived_risk = 0.05`
   - High digital literacy, optimistic

**Key Insight**: State variants are **deterministic** - same persona + same variant = same initial state.

---

### 4. Behavioral Simulation Engine (`behavioral_engine.py`)

**Purpose**: Simulate persona journeys through product steps.

#### 4.1 Internal State Variables

Each trajectory tracks 5 state variables:

1. **cognitive_energy**: Current cognitive energy level [0, CC]
   - Depletes with cognitive load
   - Clamped to persona's CC (max capacity)

2. **perceived_risk**: Perceived risk level [0, 3.0]
   - Increases with risk signals
   - Amplified by loss aversion (LAM)

3. **perceived_effort**: Perceived effort level [0, 3.0]
   - Increases with effort demands
   - Higher for users with lower ET

4. **perceived_value**: Perceived value level [0, 3.0]
   - Increases with explicit value signals
   - Decays with temporal discounting (DR)

5. **perceived_control**: Perceived control/trust [0, 2.0]
   - Increases with reassurance/authority signals
   - Higher for users with lower CN

#### 4.2 Step Processing

For each product step:

**Step 1: Compute Costs & Yields**

```python
# Cognitive cost (System 2 fatigue)
cognitive_cost = cognitive_demand × (1 + FR) × (1 - cognitive_energy)
# Higher when user is already low on energy

# Effort cost (Fogg Ability model)
effort_cost = effort_demand × (1 - ET)
# Higher for users with lower effort tolerance

# Risk cost (Prospect Theory / Loss Aversion)
risk_cost = risk_signal × LAM × (1 + irreversibility)
# Amplified by loss aversion and irreversibility

# Value yield (Temporal Discounting)
value_yield = explicit_value × exp(-DR × delay_to_value)
# Future value decays exponentially

# Reassurance yield (Control Need)
reassurance_yield = (reassurance_signal + authority_signal) × (1 - CN)
# Less effective for users with high control need
```

**Step 2: Compute Transition Costs** (NEW - Commitment Gates)

When moving from a **passive step** (landing page) to an **active step** (quiz start):

```python
# Commitment gate detected: passive → active transition
transition_cognitive = 0.25 × (1 - cognitive_energy) × (1 + FR)
transition_effort = 0.30 × (1 - ET)
transition_risk = 0.35 × LAM × (1 - perceived_control)
```

**Why**: The behavioral shift from "browsing" to "committing" requires:
- Decision-making energy (cognitive cost)
- Activation energy to start (effort cost)
- Loss of optionality feels risky (risk cost)

**Step 3: Update State**

```python
cognitive_energy = max(0, cognitive_energy - cognitive_cost - transition_cognitive)
perceived_risk = min(3.0, perceived_risk + risk_cost + transition_risk)
perceived_effort = min(3.0, perceived_effort + effort_cost + transition_effort)
perceived_value = min(3.0, perceived_value + value_yield)
perceived_control = min(2.0, perceived_control + reassurance_yield)
```

**Step 4: Drop-Off Decision**

```python
# CONTINUE if: (value × motivation) + control > risk + effort
left = (perceived_value × MS) + perceived_control
right = perceived_risk + perceived_effort

if left > right:
    continue
else:
    drop_at_current_step()
    identify_dominant_cost()  # System 2 fatigue, Loss aversion, etc.
```

**Key Insight**: Single inequality determines drop-off with labeled reasons.

---

### 5. LLM Ingestion Layer (`dropsim_llm_ingestion.py`)

**Purpose**: Extract structured product flow and personas from unstructured input.

**Input**:
- Product URL
- Product text description
- Screenshot analysis texts
- Persona notes
- Target group notes

**Process**:

1. **Firecrawl Analysis** (if URL provided):
   - Crawls the product URL
   - Extracts content, structure, CTAs
   - Analyzes with LLM for context

2. **Screenshot Analysis** (if screenshots provided):
   - Uses OpenAI Vision API to analyze images
   - Extracts step names, questions, UI elements
   - **Direct Extraction**: 1:1 mapping from screenshots to steps (no consolidation)

3. **LLM Inference**:
   - Consolidates all context (URL, text, screenshots, notes)
   - Extracts:
     - Product steps (with attributes: effort, risk, value, etc.)
     - Personas (2-4 distinct personas)
     - Target group filters
     - Fintech archetype classification

4. **Step Normalization**:
   - Orders steps chronologically
   - Removes duplicates
   - Clamps to 3-10 steps
   - Infers missing core steps if needed

5. **Persona Deduplication**:
   - Merges redundant personas
   - Caps total personas
   - Prefers personas matching target group

**Output**: `LiteScenario` (human-friendly format) + `TargetGroup`

---

### 6. Wizard Layer (`dropsim_wizard.py`)

**Purpose**: Orchestrate end-to-end pipeline from input to simulation results.

**Flow**:

1. **Consolidate Context**:
   - Merges product URL, text, screenshots into single context string
   - Analyzes with Firecrawl if URL provided
   - Analyzes screenshots with Vision API if provided

2. **LLM Ingestion**:
   - Calls `infer_lite_scenario_and_target_from_llm()`
   - Gets `LiteScenario` + `TargetGroup`

3. **Convert to Full Scenario**:
   - Converts `LiteScenario` → Full `ScenarioConfig`
   - Maps human-friendly labels (low/medium/high) → numeric values

4. **Load Personas**:
   - If `use_database_personas=True`:
     - Loads from Hugging Face dataset
     - Filters by target group
     - Samples N personas (with `min_matched` guarantee)
   - Else:
     - Uses preset personas from `fintech_presets.py`

5. **Run Simulation**:
   - Calls `run_simulation_with_database_personas()`
   - For each persona × each state variant:
     - Compiles priors
     - Simulates journey through steps
     - Records drop-off point and reason

6. **Aggregate Results**:
   - Calls `aggregate_simulation_results()`
   - Computes failure rates per step
   - Identifies dominant failure reasons
   - Generates interpretations

7. **Build Context Graph**:
   - Collects all event traces from simulation
   - Builds directed graph (nodes=steps, edges=transitions)
   - Computes transition frequencies, energy deltas, failure probabilities
   - Generates queryable insights (paths to failure, energy collapse, etc.)

8. **Generate Narrative**:
   - Calls `generate_narrative_summary()`
   - Creates plain-language insights

**Output**: Complete result dictionary with scenario, results, narrative, traces, context_graph

---

### 7. Aggregation Layer (`dropsim_aggregation_v2.py`)

**Purpose**: Aggregate simulation results into actionable insights.

**Process**:

1. **Step-Level Aggregation**:
   - Count failures per step
   - Compute failure rate: `failures / total_trajectories`
   - Identify dominant failure reason (if ≥40% of failures)

2. **Persona-Level Analysis**:
   - For each persona, check consistency across variants
   - If ≥70% variants fail at same step → **structural failure**
   - If failures vary by variant → **intent-sensitive**

3. **Interpretation**:
   - **Structural Flaw**: Step fails for most variants → step itself is problematic
   - **Intent-Sensitive**: Failures vary by arrival state → step is sensitive to user context
   - **Fatigue-Sensitive**: Only low-energy variants fail → step is fatigue-sensitive

**Output**: Formatted report with step-level analysis and interpretations

---

### 8. Context Graph Layer (`dropsim_context_graph.py`)

**Purpose**: Record event-level behavioral traces and enable path-based reasoning.

**Process**:

1. **Event Capture** (during simulation):
   - At each step, capture `state_before` and `state_after`
   - Record `cost_components`, `decision`, and `dominant_factor`
   - Create `Event` object for each transition
   - Build `EventTrace` per persona × variant

2. **Graph Construction**:
   - Aggregate all `EventTrace` objects
   - Build directed graph:
     - **Nodes** = product steps (with entry/exit/drop counts, avg state values)
     - **Edges** = transitions between steps (with frequency, avg deltas, failure probability)

3. **Query Functions**:
   - `get_most_common_paths()`: Most frequent paths through product
   - `get_highest_loss_transitions()`: Transitions with highest energy loss
   - `get_most_fragile_steps()`: Steps with highest drop rate
   - `get_paths_leading_to_drop()`: Paths that most often lead to failure
   - `get_successful_paths()`: Paths that succeed despite high risk/effort

**Key Features**:
- **Deterministic**: Pure aggregation, no randomness
- **Causal**: Enables "why did this happen?" explanations
- **Path-based**: Understands user journey patterns
- **Queryable**: Structured insights, not just summaries

---

### 9. Counterfactual Engine (`dropsim_counterfactuals.py`)

**Purpose**: Enable "what-if" analysis by simulating interventions and quantifying their impact.

**Process**:

1. **Counterfactual Simulation**:
   - Takes a baseline `EventTrace` and an intervention specification
   - Replays simulation up to intervention point
   - Applies perturbation (e.g., reduce effort at step X)
   - Re-runs only affected downstream steps (efficient)
   - Compares baseline vs counterfactual outcomes

2. **Intervention Types**:
   - **Step Modification**: Change step attributes (effort, risk, cognitive demand, value, reassurance)
   - **Persona Adjustment**: Modify initial state variables (cognitive_energy, perceived_risk, etc.)

3. **Impact Analysis**:
   - Ranks interventions by outcome change rate
   - Computes sensitivity map (which variables are most sensitive)
   - Calculates robustness score (how stable results are to perturbations)
   - Identifies most impactful steps

**Key Functions**:
- `simulate_counterfactual()`: Run single counterfactual simulation
- `rank_interventions_by_impact()`: Rank interventions by effectiveness
- `compute_sensitivity_map()`: Identify most sensitive variables
- `compute_robustness_score()`: Quantify result stability
- `analyze_top_interventions()`: Complete analysis pipeline

**Key Features**:
- **Deterministic**: Same intervention → same result (always)
- **Efficient**: Only re-runs affected downstream steps
- **Actionable**: Provides specific intervention recommendations
- **Quantified**: Measures impact, sensitivity, robustness
- **Non-breaking**: Existing outputs unchanged

**Output Schema**:
```python
{
    "top_interventions": [
        {
            "intervention": {...},
            "outcome_change_rate": 0.35,
            "avg_effect_size": 2.1,
            "avg_sensitivity": 2.5
        }
    ],
    "sensitivity_map": {
        "effort_sensitivity": 0.42,
        "risk_sensitivity": 0.38,
        "cognitive_sensitivity": 0.31,
        "most_sensitive": "effort"
    },
    "most_impactful_step": "step_5",
    "robustness_score": 0.82
}
```

**Answers**:
- "What would have happened if we changed X?"
- "How confident are we in this conclusion?"
- "Which interventions have the highest impact?"
- "What's the minimum change that fixes it?"

---

### 10. Reality Calibration Layer (`dropsim_calibration.py`)

**Purpose**: Compare simulated outcomes with real observed behavior to identify systematic errors and adjust confidence over time.

**Process**:

1. **Error Decomposition**:
   - For each step, compute absolute and relative error
   - Identify error direction (overestimate, underestimate, accurate)
   - Measure bias magnitude

2. **Bias Detection**:
   - Detect systematic biases: fatigue, effort, risk, trust
   - Identify early vs late step biases
   - Categorize by failure reason and step attributes

3. **Calibration Metrics**:
   - **Calibration Score**: `1 - mean_absolute_error` [0, 1]
   - **Stability Score**: Consistency of errors across steps
   - **Confidence Reweighting**: Adjust predictions based on detected biases

4. **Temporal Tracking**:
   - Store calibration history over time
   - Detect trends (improving, regressing, stable)
   - Enable regression alerts

**Key Functions**:
- `run_calibration()`: Main calibration analysis
- `compute_step_calibration_metrics()`: Per-step error analysis
- `detect_systematic_biases()`: Identify systematic biases
- `adjust_confidence_weights()`: Reweight predictions (not retrain)
- `update_calibration_history()`: Track calibration over time

**Key Features**:
- **Calibration, not learning**: Adjusts confidence, not logic
- **Deterministic**: Same inputs → same outputs
- **Temporal**: Tracks calibration over time
- **Actionable**: Identifies specific biases and adjustments
- **Non-breaking**: Existing outputs unchanged

**Output Schema**:
```python
{
    "calibration_score": 0.84,
    "bias_summary": {
        "fatigue_bias": -0.12,
        "effort_bias": 0.03,
        "risk_bias": 0.01,
        "trust_bias": -0.05
    },
    "confidence_adjusted_predictions": {...},
    "stability_score": 0.91,
    "dominant_biases": ["overestimated_fatigue"],
    "stable_factors": ["effort", "risk"]
}
```

**Answers**:
- "Where is the model accurate vs inaccurate?"
- "What systematic biases exist?"
- "How well does the model predict reality?"
- "What are the adjusted predictions?"
- "How is calibration changing over time?"

**Output**: Context graph with nodes, edges, and pre-computed query results

**Example Queries**:
- "Which paths most often lead to failure?" → `get_paths_leading_to_drop()`
- "Where does energy collapse occur?" → `get_highest_loss_transitions()`
- "Which transitions are most fragile?" → `get_most_fragile_steps()`

---

### 13. Reasoning & Abstraction Layer (`dropsim_interpreter.py`)

**Purpose**: Convert raw findings into high-level, decision-grade insights.

**Process**:

1. **Failure Attribution**:
   - Analyze step signals (drop rate, state deltas, failure factors)
   - Map signals to failure modes using fixed taxonomy
   - Assign confidence scores based on signal strength
   - Generate behavioral cause explanations

2. **Structural Pattern Detection**:
   - Detect patterns across multiple steps
   - Identify systemic vs local issues
   - Classify patterns (Early Commitment Spike, Cognitive Overload Cluster, etc.)

3. **Narrative Synthesis**:
   - Convert raw analysis into human-readable insights
   - Explain "why" not just "what"
   - Connect patterns to behavioral causes

4. **Design Shift Recommendations**:
   - Generate specific product change recommendations
   - Based on detected patterns and failure modes
   - Actionable design guidance

**Key Functions**:
- `interpret_results()`: Main interpretation function
- `infer_failure_modes()`: Failure attribution engine
- `detect_structural_patterns()`: Pattern detection
- `synthesize_behavioral_narrative()`: Narrative generation
- `generate_design_shifts()`: Design recommendations

**Key Features**:
- **Deterministic**: Same inputs → same interpretations
- **Explainable**: Every failure mode has clear signals
- **Structural**: Detects patterns, not just individual failures
- **Actionable**: Provides specific design shift recommendations
- **No ML**: Fixed taxonomy, rule-based mapping

**Failure Mode Taxonomy** (Fixed, No ML):
1. Cognitive Overload
2. Unclear Value Proposition
3. Perceived Risk Too High
4. Excessive Effort
5. Motivation Mismatch
6. Premature Commitment
7. Information Overload

**Output Schema**:
```python
{
    "root_causes": [
        {
            "step_id": "identity_verification",
            "dominant_failure_mode": "Perceived Risk Too High",
            "confidence": 0.82,
            "supporting_signals": [...],
            "behavioral_cause": "Users perceive high risk before value is established..."
        }
    ],
    "dominant_patterns": [
        {
            "pattern_name": "Trust-Before-Value Violation",
            "evidence": ["Step 1", "Step 2"],
            "impact": "Users asked to trust/commit before understanding value",
            "recommended_direction": "Establish value proposition before commitment"
        }
    ],
    "behavioral_summary": "Users abandon the flow at 'identity_verification' not because the step is long, but because it introduces irreversible commitment before perceived value is established.",
    "recommended_design_shifts": [...]
}
```

**Answers**:
- "What is fundamentally broken?"
- "Why is it breaking?"
- "What kind of product change would fix it?"
- "Is this a local issue or a systemic one?"

**Transformation**:
- **Before**: "Step 12 causes drop-off."
- **After**: "Users abandon the flow because the system demands irreversible commitment before value is perceived, triggering loss aversion and cognitive fatigue."

---

## 🔄 End-to-End Flow Example

### Example: Credigo.club Simulation

1. **Input**:
   - Product URL: `https://credigo.club`
   - 10 screenshots (ss1-ss10)
   - Target: "21-35, working professionals, tier-1/tier-2"

2. **LLM Ingestion**:
   - Analyzes screenshots → extracts 10 steps
   - Infers personas: "Credit card seekers, salaried professionals"
   - Classifies as: `personal_finance_manager` archetype

3. **Persona Loading**:
   - Loads 1M personas from Hugging Face
   - Filters: age 21-35, metro/tier-2, working professionals
   - Samples 840 matching personas

4. **Simulation**:
   - For each of 840 personas:
     - Compile priors (CC, FR, RT, LAM, etc.)
     - For each of 7 state variants:
       - Initialize state (e.g., `tired_commuter`)
       - Step 1: Landing page (CrediGo)
         - Compute costs (effort: high, risk: medium - commitment gate)
         - Apply transition cost (Step 1 → Step 2)
         - Update state
         - Check: `(value × MS) + control > risk + effort`?
         - If no → drop, record reason
         - If yes → continue
       - Step 2: "What kind of perks..."
         - Compute costs
         - Update state
         - Check drop-off
       - ... (continue through all 10 steps)

5. **Aggregation**:
   - Step 1: 207 failures (3.5%) → System 2 fatigue
   - Step 6: 2,219 failures (37.7%) → System 2 fatigue
   - Step 7: 2,136 failures (36.3%) → System 2 fatigue

6. **Context Graph**:
   - Captures 5,880 event traces (840 personas × 7 variants)
   - Builds graph with 10 nodes (steps) and 9 edges (transitions)
   - Identifies: Step 1→2 transition has highest energy loss (-0.15 avg)
   - Finds: Step 6 is most fragile (37.7% drop rate)
   - Discovers: Paths through Step 1→2→3 have 85% success rate

7. **Output**:
   - Step-level failure analysis
   - Dominant failure reasons
   - Interpretations (intent-sensitive pattern)
   - Context graph (nodes, edges, dominant paths, fragile transitions)
   - Narrative summary

---

## 🎯 Key Design Principles

### 1. Deterministic, Not Stochastic
- Same inputs → same outputs
- No randomness in simulation
- Reproducible results

### 2. Behavioral Grounding
- Based on behavioral economics (System 2 fatigue, Prospect Theory, etc.)
- Explainable with labeled reasons
- Not a black box

### 3. Persona vs State Separation
- **Persona** = fixed behavioral constraints (priors)
- **State** = arrival conditions (variants)
- Same person, different days → different outcomes

### 4. Single Inequality Decision
- One clear rule: `(value × motivation) + control > risk + effort`
- Labeled failure reasons (not just probabilities)
- Actionable insights

### 5. Transition Costs
- Models commitment gates (passive → active transitions)
- Captures behavioral shift from browsing to committing
- Explains Step 1 → Step 2 drop-offs

---

## 📊 Output Format

### Step-Level Analysis
```
Step 1: CrediGo
  Fails for: 207 variants (3.5%)
  Affects: 199 personas
  Dominant failure reason: System 2 fatigue (207 variants)
```

### Interpretations
```
🟡 INTENT-SENSITIVE STEPS:
  • Intent-sensitive: 1 personas fail at 'CrediGo' but with low consistency (42.9%).
    Failure depends on user's arrival state (motivation, energy), not just the step itself.
```

### Narrative Summary
```
Most failures happen at the "Do you track your monthly spending?" step (37.7%),
driven by System 2 fatigue. Low-energy variants drop earlier, indicating
fatigue-sensitive onboarding.
```

---

## 🔧 Extension Points

1. **New Verticals**: Add presets in `fintech_presets.py` or create new preset files
2. **Custom State Variants**: Add variants to `STATE_VARIANTS` in `behavioral_engine.py`
3. **New Cost Types**: Extend cost computation functions in `behavioral_engine.py`
4. **Custom Aggregation**: Modify `dropsim_aggregation_v2.py` for different insights
5. **LLM Providers**: Swap `OpenAILLMClient` for other LLM providers

---

## 🚀 Usage

### CLI
```bash
python dropsim_cli.py wizard-fintech \
  --product-url https://credigo.club \
  --screenshot-texts credigo_screenshots_ordered.txt \
  --persona-notes "Credit card seekers" \
  --target-group-notes "21-35, working professionals" \
  --n-personas 1000 \
  --use-database-personas
```

### Python API
```python
from dropsim_wizard import WizardInput, run_fintech_wizard
from dropsim_llm_ingestion import OpenAILLMClient

wizard_input = WizardInput(
    product_url="https://credigo.club",
    screenshot_texts=[...],
    persona_notes="...",
    target_group_notes="..."
)

result = run_fintech_wizard(
    wizard_input,
    OpenAILLMClient(api_key="..."),
    simulate=True,
    n_personas=1000,
    use_database_personas=True
)
```

---

## 📈 Why This Architecture Works

1. **Explainable**: Every drop-off has a labeled reason
2. **Reproducible**: Deterministic = same inputs → same outputs
3. **Scalable**: Handles 1M+ personas efficiently
4. **Actionable**: Insights directly inform product decisions
5. **Grounded**: Based on behavioral economics, not heuristics
6. **Flexible**: Works for any multi-step product flow

---

This architecture enables PMs and founders to understand **why** users drop at each step, not just **where** they drop. The Context Graph layer adds **path-based reasoning**, enabling questions like "Which paths lead to failure?" and "Where does energy collapse occur?" — all derived deterministically from the simulation traces.


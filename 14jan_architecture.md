# Decision Simulation Engine Architecture
**Date:** January 14, 2026  
**Status:** Production-Ready with Enhanced Inference Generation

---

## 🎯 System Overview

The Decision Simulation Engine is a **behavioral simulation platform** that predicts user behavior in product onboarding flows. It uses behavioral science principles, intent-aware modeling, and LLM-enhanced inference generation to identify where and why users drop off.

**Core Philosophy:** Explainable, empirically grounded, step-specific behavioral predictions with actionable recommendations.

---

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ENTRY POINT                                   │
│              (run_circlepe_simulation.py)                        │
│              (run_blink_money_enhanced_inference.py)             │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│         PERSONA DATABASE LAYER                                  │
│  • NVIDIA Nemotron-Personas-India (1M+ personas)                │
│  • Target group filtering (age, location, employment)            │
│  • Persona compilation (behavioral priors)                      │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│      BEHAVIORAL SIMULATION ENGINE                               │
│  • Intent-aware behavioral modeling                             │
│  • Cognitive state tracking (energy, risk, effort, value)        │
│  • Decision trace generation                                    │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│      ENHANCED INFERENCE GENERATION                              │
│  • LLM-powered step-specific inferences                          │
│  • Product-specific context awareness                           │
│  • Multi-level comprehension (30%, 60%, 100%)                  │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│      DECISION AUTOPSY GENERATION                                │
│  • Belief break identification                                  │
│  • Step-specific recommendations                                │
│  • Context graph visualization                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 Core Components

### 1. Persona Database Layer

**File:** `load_dataset.py`, `dropsim_simulation_runner.py`

**Purpose:** Load and filter realistic Indian personas from NVIDIA database.

**Key Functions:**
- `load_and_sample(n, seed, language="en_IN")`: Loads personas from Hugging Face
- `run_simulation_with_database_personas()`: Runs simulation with database personas
- `TargetGroup`: Filters personas by age, location, employment, digital skill, intent

**Data Source:**
- **NVIDIA Nemotron-Personas-India**: 3M personas (1M English, 1M Hindi Devanagari, 1M Hindi Latin)
- 28 fields: demographics, geography, interests, persona descriptions
- Language: `en_IN` (English India) for simulation clarity

**Example Usage:**
```python
target_group = TargetGroup(
    age_bucket=["young", "middle"],  # 22-35
    urban_rural=["metro", "tier2"],  # Tier-1 cities
    digital_skill=["medium", "high"],
    intent=["medium", "high"]
)

result_df = run_simulation_with_database_personas(
    product_steps=CIRCLEPE_STEPS,
    n_personas=100,
    target_group=target_group,
    seed=42
)
```

---

### 2. Behavioral Simulation Engine

**File:** `behavioral_engine_intent_aware.py`, `behavioral_engine_improved.py`

**Purpose:** Simulate user decision-making through product steps using behavioral science principles.

**Key Components:**

#### 2.1 Internal State Model
Tracks 5 cognitive state variables:
- **Energy**: Cognitive energy available (0.0 = exhausted, 1.0 = fresh)
- **Risk**: Perceived risk of current action (0.0 = safe, 1.0 = very risky)
- **Effort**: Perceived effort required (0.0 = easy, 1.0 = very hard)
- **Value**: Perceived value received (0.0 = no value, 1.0 = high value)
- **Control**: Sense of control over situation (0.0 = no control, 1.0 = full control)

#### 2.2 Intent-Aware Layer
- **Intent Inference**: Infers user intent from product entry point
- **Intent-Step Alignment**: Computes alignment between user intent and product asks
- **Intent-Conditioned Probability**: Adjusts continuation probability based on intent alignment
- **Intent Mismatch Detection**: Identifies when product asks don't match user intent

**Key Functions:**
- `run_intent_aware_simulation()`: Main simulation function
- `simulate_persona_trajectory_intent_aware()`: Simulates single persona through flow
- `should_continue_probabilistic()`: Decides continue vs drop based on state
- `update_state_improved()`: Updates cognitive state after each step

**Decision Logic:**
```python
continuation_prob = base_probability * intent_alignment * state_factors
if continuation_prob < threshold:
    decision = DROP
else:
    decision = CONTINUE
```

---

### 3. Enhanced Inference Generation

**File:** `circlepe_enhanced_inference.py`, `user_inference_generator.py`

**Purpose:** Generate rich, step-specific inferences about what users see, think, understand, and feel at each step.

**Key Components:**

#### 3.1 LLM-Enhanced Inference Generator
- **Product-Specific Context**: Understands product type (fintech, rental, etc.)
- **Step Attributes**: Considers risk, value, delay, effort, irreversibility
- **Multi-Level Comprehension**: Generates 30%, 60%, 100% level inferences
- **WhatsApp-Specific**: Understands WhatsApp bot interface patterns

**Inference Levels:**
- **30%**: Surface-level, first impression
- **60%**: Moderate understanding, connects some dots
- **100%**: Full understanding, sees complete picture

**LLM Prompt Structure:**
```
1. Product context (CirclePe zero deposit rental)
2. Current step information (step name, description, attributes)
3. Step-specific considerations (WhatsApp interface, value delay)
4. Task: Generate what user sees, thinks, understands, feels
```

**Example Output:**
```json
{
  "what_user_sees": "WhatsApp message with welcome, IIT-IIM branding, partner logos",
  "what_user_thinks": "This is a rental platform. They want me to explore zero deposit options.",
  "what_user_understands": "Branding shown but value delayed 3 steps. Need to proceed to see eligibility.",
  "emotional_state": "Slightly anxious - want to see value, not just branding"
}
```

---

### 4. Decision Trace Generation

**File:** `decision_graph/decision_trace.py`, `run_circlepe_simulation.py`

**Purpose:** Convert simulation results into structured DecisionTrace objects.

**DecisionTrace Structure:**
```python
@dataclass
class DecisionTrace:
    persona_id: str
    step_id: str
    step_index: int
    decision: DecisionOutcome  # CONTINUE or DROP
    probability_before_sampling: float
    sampled_outcome: bool
    cognitive_state_snapshot: CognitiveStateSnapshot
    intent: IntentSnapshot
    dominant_factors: List[str]
```

**Key Functions:**
- `run_simulation_and_generate_traces()`: Main trace generation function
- Extracts drop points from simulation trajectories
- Creates DecisionTrace objects with cognitive state and intent
- Handles fallback when simulation doesn't generate enough traces

**Trace Generation Flow:**
```
1. Run intent-aware simulation → result_df with trajectories
2. Extract drop points from trajectories
3. For each drop point:
   - Extract cognitive state
   - Extract intent information
   - Create DecisionTrace object
4. Return list of DecisionTrace objects
```

---

### 5. Decision Autopsy Generation

**File:** `decision_autopsy_result_generator.py`, `decision_autopsy_generator.py`

**Purpose:** Generate comprehensive analysis of user drop-offs with actionable recommendations.

**Key Components:**

#### 5.1 Product-Specific Result Generator
Each product has a custom generator (e.g., `CirclePeResultGenerator`):
- **Custom Cohort Inference**: Product-specific user cohort description
- **Custom User Context**: Product-specific user context
- **Custom Verdict**: Product-specific abandonment reasons
- **Custom Belief Break**: Step-specific belief break descriptions

#### 5.2 Decision Autopsy Sections

**Core Verdict:**
- One-line summary of why users abandon
- Product-specific language (e.g., "WhatsApp bot asks for commitment before value")

**Belief Break:**
- Identifies step where most users drop
- Describes irreversible action required
- Explains psychology behind abandonment

**Why Belief Breaks:**
- User beliefs vs product asks
- Why the mismatch causes failure

**The One Bet:**
- Specific, actionable recommendation
- Step-specific (e.g., "Show value at Step 2 BEFORE Step 3")
- Includes:
  - Minimality & Reversibility
  - Execution Specificity
  - Learning Payoff

**Decision Simulation:**
- Step-by-step inferences (30%, 60%, 100%)
- What user sees, thinks, understands, feels at each step

**Falsifiable Conditions:**
- Testable conditions that would prove analysis wrong
- Enables validation of recommendations

---

### 6. Product Steps Definition

**File:** `circlepe_steps.py`, `blink_money_steps.py`

**Purpose:** Define product onboarding flow with step attributes.

**Step Attributes:**
- `cognitive_demand`: Cognitive load required (0.0-1.0)
- `effort_demand`: Effort required (0.0-1.0)
- `risk_signal`: Perceived risk (0.0-1.0)
- `irreversibility`: How irreversible the action feels (0.0-1.0)
- `delay_to_value`: Steps remaining until value is shown
- `explicit_value`: Value shown at this step (0.0-1.0)
- `reassurance_signal`: Trust/reassurance signals (0.0-1.0)
- `authority_signal`: Authority/credibility signals (0.0-1.0)
- `description`: Detailed step description

**Example:**
```python
CIRCLEPE_STEPS = {
    "Welcome & Personalization": {
        "cognitive_demand": 0.2,
        "effort_demand": 0.1,
        "risk_signal": 0.1,
        "irreversibility": 0.0,
        "delay_to_value": 3,
        "explicit_value": 0.0,
        "reassurance_signal": 0.6,
        "authority_signal": 0.7,
        "description": "Greeting with IIT-IIM branding, partner logos..."
    }
}
```

---

## 🔄 Data Flow

### Complete Simulation Flow

```
1. ENTRY POINT
   └─> run_circlepe_simulation.py
       └─> Initialize CirclePeResultGenerator
       └─> Load LLM client (if available)

2. PERSONA LOADING
   └─> run_simulation_and_generate_traces()
       └─> run_simulation_with_database_personas()
           └─> load_and_sample() from NVIDIA database
           └─> Filter by TargetGroup
           └─> Convert to compiled priors

3. INTENT INFERENCE
   └─> infer_intent_distribution()
       └─> Analyzes product entry point
       └─> Returns intent distribution

4. BEHAVIORAL SIMULATION
   └─> run_intent_aware_simulation()
       └─> For each persona:
           └─> simulate_persona_trajectory_intent_aware()
               └─> For each step:
                   └─> update_state_improved()
                   └─> should_continue_probabilistic()
                   └─> If DROP: record exit step
                   └─> If CONTINUE: proceed to next step

5. TRACE GENERATION
   └─> Extract drop points from trajectories
   └─> Create DecisionTrace objects
   └─> Include cognitive state and intent

6. INFERENCE GENERATION
   └─> CirclePeEnhancedInferenceGenerator
       └─> For each step:
           └─> generate_inference_for_step() (30%, 60%, 100%)
           └─> Uses LLM if available, else rule-based

7. DECISION AUTOPSY GENERATION
   └─> generator.generate()
       └─> Generate verdict
       └─> Identify belief break
       └─> Generate one bet
       └─> Generate decision simulation
       └─> Generate falsifiable conditions

8. OUTPUT
   └─> CIRCLEPE_DECISION_AUTOPSY_RESULT.json
   └─> circlepe_context_graph.pdf
```

---

## 🎨 Product-Specific Customizations

### CirclePe Customizations

**File:** `run_circlepe_simulation.py`

**Custom Methods:**
1. **`infer_cohort()`**: Returns CirclePe-specific cohort description
2. **`infer_user_context()`**: Returns WhatsApp bot user context
3. **`simplify_verdict()`**: CirclePe-specific abandonment reasons
4. **`generate_belief_break_section()`**: Step-specific belief break descriptions
5. **`generate_decision_simulation()`**: Uses CirclePeEnhancedInferenceGenerator

**Key Features:**
- WhatsApp-specific language and context
- Zero deposit rental value proposition understanding
- Step-specific recommendations (e.g., "Show value at Step 2 BEFORE Step 3")

---

## 🤖 LLM Integration

**Purpose:** Enhance inference generation with product-specific, context-aware insights.

**Implementation:**
- **LLM Client**: OpenAI GPT-4o-mini (via `dropsim_llm_ingestion.py`)
- **Fallback**: Rule-based inference if LLM unavailable
- **Prompt Engineering**: Product-specific prompts with step attributes

**Benefits:**
- More accurate "what user sees/thinks/understands/feels"
- Product-specific context awareness
- Better understanding of WhatsApp interface patterns

**Example Prompt Structure:**
```
1. Product context (CirclePe zero deposit rental)
2. Current step (name, description, attributes)
3. Step-specific considerations (WhatsApp, value delay, risk)
4. Task: Generate 4-part inference (sees, thinks, understands, feels)
```

---

## 📊 Output Artifacts

### 1. Decision Autopsy JSON
**File:** `CIRCLEPE_DECISION_AUTOPSY_RESULT.json`

**Contents:**
- Core verdict
- Belief break (step, action, psychology)
- Why belief breaks (user beliefs vs product asks)
- The one bet (headline, support, execution specificity)
- Decision simulation (step-by-step inferences)
- Falsifiable conditions
- Product context

### 2. Context Graph PDF
**File:** `circlepe_context_graph.pdf`

**Contents:**
- Visual context graph (steps with risk/value/delay)
- Decision simulation results
- Step-by-step analysis
- Key findings and recommendations

---

## 🔧 Key Design Decisions

### 1. Database Personas vs Generated Personas
- **Database Personas**: Realistic Indian personas from NVIDIA (preferred)
- **Generated Personas**: Fallback when database unavailable
- **Target Group Filtering**: Ensures personas match product target audience

### 2. Intent-Aware vs Behavioral-Only
- **Intent-Aware**: Explains WHY users act (intent alignment)
- **Behavioral-Only**: Explains HOW users act (cognitive state)
- **Combined**: Both layers work together for complete picture

### 3. LLM-Enhanced vs Rule-Based
- **LLM-Enhanced**: Product-specific, context-aware inferences (preferred)
- **Rule-Based**: Generic, fallback when LLM unavailable
- **Hybrid**: LLM for complex steps, rules for simple steps

### 4. Step-Specific vs Generic Recommendations
- **Step-Specific**: "Show value at Step 2 BEFORE Step 3" (preferred)
- **Generic**: "Show value earlier" (less actionable)
- **Implementation**: Analyzes drop distribution to identify exact steps

---

## 🚀 Usage Example

### Running CirclePe Simulation

```python
# 1. Initialize generator with LLM
llm_client = OpenAILLMClient(api_key=OPENAI_API_KEY, model="gpt-4o-mini")
generator = CirclePeResultGenerator(
    product_steps=CIRCLEPE_STEPS,
    product_name="CIRCLEPE",
    llm_client=llm_client
)

# 2. Run simulation with 100 personas from database
traces = run_simulation_and_generate_traces(n_personas=100, seed=42)

# 3. Generate decision autopsy
result = generator.generate(traces, run_mode="production")

# 4. Save results
with open('CIRCLEPE_DECISION_AUTOPSY_RESULT.json', 'w') as f:
    json.dump(result, f, indent=2)
```

---

## 📈 Performance Characteristics

### Scalability
- **Personas**: Handles 100-5000 personas efficiently
- **Steps**: Supports 3-10 step flows
- **LLM Calls**: ~15 calls per simulation (5 steps × 3 inference levels)

### Accuracy
- **Belief Break Detection**: Based on actual drop distribution (not algorithm)
- **Step-Specific Recommendations**: Derived from trace analysis
- **Intent Alignment**: Validated through intent-aware modeling

### Reproducibility
- **Seed-Based**: All random operations use seed for reproducibility
- **Deterministic**: Same seed → same results
- **Traceable**: Every decision trace includes full context

---

## 🔮 Future Enhancements

### Planned Improvements
1. **Multi-Product Learning**: Learn from multiple products to improve accuracy
2. **Real-Time Updates**: Update recommendations based on A/B test results
3. **Advanced Visualizations**: Interactive context graphs
4. **Persona Clustering**: Identify persona segments with similar behavior
5. **Counterfactual Simulation**: "What if we changed Step X?"

---

## 📚 Key Files Reference

### Core Engine
- `behavioral_engine_intent_aware.py`: Intent-aware simulation
- `behavioral_engine_improved.py`: Behavioral state management
- `dropsim_simulation_runner.py`: Database persona loading

### Product-Specific
- `run_circlepe_simulation.py`: CirclePe simulation runner
- `circlepe_steps.py`: CirclePe product steps
- `circlepe_enhanced_inference.py`: CirclePe inference generator

### Result Generation
- `decision_autopsy_result_generator.py`: Base result generator
- `decision_autopsy_generator.py`: Core autopsy logic
- `user_inference_generator.py`: Base inference generator

### Utilities
- `load_dataset.py`: Persona database loading
- `derive_features.py`: Persona feature derivation
- `dropsim_target_filter.py`: Target group filtering
- `dropsim_intent_model.py`: Intent inference

---

## ✅ Validation & Testing

### Falsifiability
Every recommendation includes falsifiable conditions:
- **Test**: What to measure
- **Hypothesis**: What we expect
- **Falsifier**: What would prove us wrong

### Trace Verification
- All metrics derived from DecisionTrace objects
- No hardcoded values
- Full traceability from simulation to recommendations

---

**Last Updated:** January 14, 2026  
**Version:** 2.0 (Enhanced Inference Generation)

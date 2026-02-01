# DropSim: Product & System Design

## What is DropSim?

DropSim is a deterministic behavioral simulation engine that predicts why users drop off at each step of your product funnel—before you build or launch. Built for fintech, edtech, and consumer apps with multi-step onboarding flows, DropSim simulates synthetic users through your funnel to surface the exact behavioral drivers of drop-off: cognitive fatigue, loss aversion, temporal discounting, or low ability.

**What makes DropSim unique:**

- **Deterministic engine, not black-box ML**: Every output is explainable and reproducible. Same inputs always produce same outputs—critical for A/B documentation and VC pitches.
- **Persona priors + state variants**: We model both who the user is (cultural background, risk tolerance, effort capacity) and how they arrive (energy level, motivation, trust state). This separation captures the reality that the same person behaves differently on different days.
- **Single inequality with labeled reasons**: At each step, a single behavioral inequality decides "continue vs drop," and we label the dominant cost (System 2 fatigue, loss aversion, temporal discounting, or low ability). No guessing—just causal attribution.

**From persona to drop-off insight:**

1. **Start**: PM defines personas in raw field-space (SEC, DigitalLiteracy, FamilyInfluence, AspirationalLevel, PriceSensitivity, RegionalCulture, etc.), all normalized to [0,1] or categorical.

2. **Engine compiles priors**: The persona compiler transforms raw inputs into 9 latent behavioral priors:
   - **CC (Cognitive Capacity)**: Mental endurance before fatigue
   - **FR (Cognitive Fatigue Rate)**: How fast cognitive energy drains
   - **RT (Risk Tolerance)**: Tolerance for irreversible/financial/data risk
   - **LAM (Loss Aversion Multiplier)**: Amplifies perceived risk (Prospect Theory)
   - **ET (Effort Tolerance)**: Tolerance for forms, OTPs, retries (Fogg Ability)
   - **TB (Trust Baseline)**: Initial comfort with systems asking for data/payment
   - **DR (Temporal Discount Rate)**: How aggressively future value decays
   - **CN (Control Need)**: Need to feel in control before proceeding
   - **MS (Motivation Strength)**: Intent strength (from problem severity + urgency)

3. **PM defines product steps**: Each step is defined by 8 attributes:
   - `cognitive_demand`, `effort_demand`, `risk_signal`, `irreversibility` (0 or 1), `delay_to_value`, `explicit_value`, `reassurance_signal`, `authority_signal`

4. **Engine simulates persona × state-variants**: For each persona, we run 7–15 deterministic state variants (e.g., `fresh_motivated`, `tired_commuter`, `distrustful_arrival`). Each variant starts with different initial conditions:
   - `cognitive_energy_0` (bounded by CC)
   - `perceived_risk_0`, `perceived_effort_0`
   - `perceived_value_0` (from MS)
   - `perceived_control_0` (from TB)

5. **State updates at each step**: The engine computes:
   - **Cognitive cost**: `cognitive_demand × (1 + FR) × (1 - cognitive_energy_t)` (System 2 fatigue amplification)
   - **Effort cost**: `effort_demand × (1 - ET)` (Fogg Ability model)
   - **Risk cost**: `risk_signal × LAM × (1 + irreversibility)` (Prospect Theory)
   - **Value yield**: `explicit_value × exp(-DR × delay_to_value)` (temporal discounting)
   - **Reassurance yield**: `(reassurance_signal + authority_signal) × (1 - CN)` (control need)

   Then updates state: `cognitive_energy_{t+1} = cognitive_energy_t - cognitive_cost_t`, etc.

6. **Drop-off inequality decides**: At each step, the engine checks:
   ```
   CONTINUE if: (perceived_value_{t+1} × MS + perceived_control_{t+1}) > (perceived_risk_{t+1} + perceived_effort_{t+1})
   Else → DROP at step t
   ```

7. **Aggregator surfaces insights**: The aggregator computes:
   - `FailureRate(step t)` = % of state-variants that drop at step t
   - `PrimaryCost(step t)` = dominant cost label (System 2 fatigue, loss aversion, temporal discounting, or low ability) if it exceeds 40% of total cost
   - `SecondaryCost(step t)` = second-most common cost, or "multi-factor" if no single cost dominates

**Output example**: "Step 4 (PAN + Bank Linking) fails for 40% of state-variants. Primary cost: Loss aversion (100% of failures). Secondary cost: None."

---

## System Architecture

### Core Modules

#### `persona_compiler`

**Implemented as:** `behavioral_engine.compile_latent_priors()` and `behavioral_engine.normalize_persona_inputs()`

**Responsibilities:**
- Normalizes raw persona inputs to [0,1] ranges (clamps outliers)
- Compiles 9 latent behavioral priors from raw fields using fixed coefficient formulas
- Annotates each prior with interpretation bands (e.g., FR < 0.3 = slow fatigue, FR > 0.6 = fast burnout)
- Validates that all priors are within spec-defined ranges

**Input:**
- Raw persona dict: `{SEC, UrbanRuralTier, DigitalLiteracy, FamilyInfluence, AspirationalLevel, PriceSensitivity, RegionalCulture, InfluencerTrust, ProfessionalSector, EnglishProficiency, HobbyDiversity, CareerAmbition, AgeBucket, GenderMarital}`

**Output:**
- Θ_persona dict: `{CC, FR, RT, LAM, ET, TB, DR, CN, MS}` with:
  - All values clamped to spec ranges (e.g., CC ∈ [0.2, 0.9], LAM ∈ [1.0, 2.5])
  - Interpretation annotations (e.g., "CC = 0.65 → high cognitive endurance")

**Extension points:**
- v1: All coefficients are fixed (e.g., CC = 0.35 × DigitalLiteracy + 0.25 × EnglishProficiency + ...)
- v2+: Coefficients can be learned from real funnel data via calibration API
- Vertical-specific compilers (fintech vs edtech may weight FamilyInfluence differently)

**Key formulas (from spec):**
- CC = clamp(0.35 × DigitalLiteracy + 0.25 × EnglishProficiency + 0.20 × HobbyDiversity + 0.20 × (1 - AgeBucket), 0.2, 0.9)
- FR = clamp(1 - (0.5 × DigitalLiteracy + 0.3 × (1 - AgeBucket) + 0.2 × EnglishProficiency), 0.1, 0.8)
- RT = clamp(0.4 × SEC + 0.3 × (1 - FamilyInfluence) + 0.2 × AspirationalLevel + 0.1 × (1 - PriceSensitivity), 0.1, 0.9)
- LAM = clamp(1 + (0.6 × FamilyInfluence + 0.4 × PriceSensitivity), 1.0, 2.5)
- ET = clamp(0.5 × DigitalLiteracy + 0.3 × HobbyDiversity + 0.2 × CareerAmbition, 0.2, 0.9)
- TB = clamp(0.4 × UrbanRuralTier + 0.3 × ProfessionalSector + 0.3 × InfluencerTrust, 0.2, 0.9)
- DR = clamp(0.5 × PriceSensitivity + 0.3 × (1 - AgeBucket) + 0.2 × AspirationalLevel, 0.05, 0.9)
- CN = clamp(0.5 × FamilyInfluence + 0.3 × RegionalCulture + 0.2 × (1 - UrbanRuralTier), 0.2, 0.9)
- MS = clamp(0.6 × ProblemSeverity + 0.4 × Urgency, 0.3, 1.0) (Note: ProblemSeverity and Urgency are derived from AspirationalLevel and DigitalLiteracy in v1)

---

#### `state_engine`

**Implemented as:** `behavioral_engine.update_state()`, `behavioral_engine.should_continue()`, `behavioral_engine.identify_failure_reason()`

**Responsibilities:**
- Takes current state M_t and product step S_t, computes all per-step costs/yields
- Updates state to M_{t+1} with clamping to valid ranges
- Evaluates drop-off inequality to decide continue vs drop
- Identifies dominant cost label (System 2 fatigue, loss aversion, temporal discounting, low ability) if drop occurs

**Input:**
- Θ_persona: `{CC, FR, RT, LAM, ET, TB, DR, CN, MS}`
- Current state M_t: `{cognitive_energy, perceived_risk, perceived_effort, perceived_value, perceived_control}`
- Product step S_t: `{cognitive_demand, effort_demand, risk_signal, irreversibility, delay_to_value, explicit_value, reassurance_signal, authority_signal}`

**Output:**
- Per-step metrics: `{cognitive_cost_t, effort_cost_t, risk_cost_t, value_yield_t, reassurance_yield_t, value_decay_t, total_cost}`
- Next state M_{t+1} (all clamped: cognitive_energy ∈ [0, CC], perceived_risk/effort/value ∈ [0, 3.0], perceived_control ∈ [0, 2.0])
- Drop decision: `{continue: bool, dominant_cost: str | None}`

**Conceptual responsibilities (mapping formulas to concepts):**

1. **System 2 fatigue amplification** (cognitive_cost_t):
   - Formula: `cognitive_demand × (1 + FR) × (1 - cognitive_energy_t)`
   - Concept: Cognitive load depletes energy faster when already low (System 2 thinking is effortful)

2. **Fogg Ability model** (effort_cost_t):
   - Formula: `effort_demand × (1 - ET)`
   - Concept: Lower ability (effort tolerance) = higher perceived effort cost

3. **Prospect Theory / Loss Aversion** (risk_cost_t):
   - Formula: `risk_signal × LAM × (1 + irreversibility)`
   - Concept: Losses loom larger than gains (LAM amplifies), and irreversible actions amplify risk perception

4. **Temporal Discounting** (value_yield_t):
   - Formula: `explicit_value × exp(-DR × delay_to_value)`
   - Concept: Future value decays exponentially—higher discount rate (DR) = more impatient

5. **Control Need / Reassurance** (reassurance_yield_t):
   - Formula: `(reassurance_signal + authority_signal) × (1 - CN)`
   - Concept: Users with high control need (CN) benefit less from reassurance signals

**State update logic:**
- `cognitive_energy_{t+1} = max(0, cognitive_energy_t - cognitive_cost_t)`
- `perceived_risk_{t+1} = min(3.0, perceived_risk_t + risk_cost_t)`
- `perceived_effort_{t+1} = min(3.0, perceived_effort_t + effort_cost_t)`
- `perceived_value_{t+1} = min(3.0, perceived_value_t + value_yield_t)`
- `perceived_control_{t+1} = min(2.0, perceived_control_t + reassurance_yield_t)`

**Drop-off decision:**
- Left side: `(perceived_value_{t+1} × MS) + perceived_control_{t+1}`
- Right side: `perceived_risk_{t+1} + perceived_effort_{t+1}`
- Continue if Left > Right, else drop

**Dominant cost identification:**
- If drop occurs, compute cost percentages: `cognitive_pct = cognitive_cost / total_cost`, etc.
- If any cost ≥ 40% of total_cost, label it as primary
- Else label as "multi-factor failure"

---

#### `simulator`

**Implemented as:** `behavioral_engine.simulate_persona_trajectories()` and `fintech_demo.run_fintech_demo_simulation()`

**Responsibilities:**
- Orchestrates simulation across personas, state variants, and product steps
- Maintains per-step traces (state snapshots, costs, decisions)
- Identifies first failing step (or completion) for each persona × variant trajectory
- Handles deterministic state variant initialization

**Input:**
- List of personas: `[{name, raw_fields, compiled_priors}, ...]`
- List of state variants per persona: `[{variant_name, initial_state_formula}, ...]` (7–15 variants)
- Ordered product steps: `[{step_name, step_attributes}, ...]`

**Output:**
- For each persona × variant:
  - `{persona_name, variant_name, exit_step, failure_reason, journey: [{step, state, costs, decision}, ...]}`

**Pseudo-API signature:**
```python
def simulate_trajectory(
    persona_priors: Dict[str, float],
    state_variant: StateVariant,
    product_steps: List[ProductStep]
) -> Trajectory:
    """
    Simulates one persona × variant through product steps.
    Returns trajectory with per-step state, costs, and exit point.
    """
```

**CLI Usage:**
```bash
python dropsim_cli.py simulate --preset fintech
python dropsim_cli.py simulate --scenario-file examples/fintech_onboarding.json
```

**API Usage:**
```bash
curl -X POST http://localhost:8000/simulate \
  -H "Content-Type: application/json" \
  -d @examples/fintech_onboarding.json
```

**Key logic:**
- Initialize state M_0 from variant formula (e.g., `cognitive_energy_0 = 0.9 × CC`)
- For each step S_t:
  - Call `state_engine.update(M_t, S_t, Θ_persona)` → get M_{t+1}, costs, decision
  - Record trace: `{step: S_t.name, state: M_{t+1}, costs, decision}`
  - If decision = drop: set `exit_step = S_t.name`, `failure_reason = dominant_cost`, break
- If all steps completed: `exit_step = "Completed"`, `failure_reason = None`

---

#### `aggregator`

**Implemented as:** `behavioral_aggregator.format_failure_mode_report()`, `behavioral_aggregator.generate_full_report()`, `behavioral_aggregator.aggregate_failure_modes()`

**Responsibilities:**
- Aggregates all simulation traces to compute step-level failure rates
- Identifies primary and secondary costs per step
- Optionally computes confidence bands (hard drop / fragile / confident continuation) based on inequality margin
- Generates human-readable reports for PMs

**Input:**
- All simulation traces: `List[Trajectory]`

**Output:**
- Step summary: `{step_name, failure_rate, primary_cost, secondary_cost, confidence_bands?}`

**Failure rate calculation:**
- For each step t: `FailureRate(t) = (count of trajectories that exit at step t) / (total trajectories)`

**Primary/secondary cost identification:**
- For each step t, collect all `failure_reason` labels from trajectories that exit at step t
- Count occurrences: `{System 2 fatigue: 12, Loss aversion: 3, ...}`
- Primary = most common label if it represents ≥40% of failures
- Secondary = second-most common label if it represents ≥20% of failures
- Else label as "multi-factor failure"

**Confidence bands (optional):**
- For each trajectory that continues past step t, compute inequality margin:
  - `margin = (Left - Right) / Right`
  - If margin < -0.1: "hard drop" (would have dropped)
  - If -0.1 ≤ margin < 0.2: "fragile" (close to drop)
  - If margin ≥ 0.2: "confident continuation"
- Aggregate bands per step to show fragility distribution

**40% threshold rationale:**
- From spec: "Dominant cost must exceed 40% of total cost to be primary"
- Ensures we only label a cost as "primary" if it's truly dominant, not just slightly higher
- Prevents over-attribution when multiple costs are balanced

---

#### `vertical_presets`

**Implemented as:** `fintech_presets.get_default_fintech_scenario()`, `fintech_presets.DEFAULT_FINTECH_PERSONAS`, `fintech_presets.FINTECH_ONBOARDING_STEPS`

**Responsibilities:**
- Defines industry-specific personas, product steps, and state variants
- Provides "batteries-included" scenarios (fintech onboarding, edtech signup, commerce checkout)
- Allows PMs to start with presets and customize

**Structure:**
- Each preset is a `ScenarioConfig`:
  - `personas`: List of personas in raw field-space (e.g., "Gen Z UPI-native, metro, low risk aversion")
  - `product_steps`: Ordered list of steps with tuned attributes (e.g., fintech: Landing → Mobile+OTP → KYC → PAN/Bank → Consent → Transaction)
  - `state_variants`: Library of 7–15 deterministic variants (reusable across presets)

**Example: Fintech Onboarding Preset**
- Personas: 5 personas (Gen Z metro, Salaried Tier-2, Self-employed trader, Rural first-time, Urban professional)
- Steps: 6-step flow with calibrated risk signals (PAN/Bank step has `risk_signal=0.7`, `irreversibility=1`)
- State variants: 7 variants (fresh_motivated, tired_commuter, distrustful_arrival, browsing_casually, urgent_need, price_sensitive, tech_savvy_optimistic)

**Extension:**
- PMs can override any preset component (add personas, modify step attributes, add variants)
- Presets are just starting points—full customization is always available

---

### Data Model Sketch

#### `PersonaRaw`
```json
{
  "SEC": 0.6,                    // [0,1] Socio-economic class
  "UrbanRuralTier": 1.0,         // [0,1] 0=rural, 1=Tier-1 metro
  "DigitalLiteracy": 0.9,        // [0,1] 0=no digital skill, 1=power user
  "FamilyInfluence": 0.2,        // [0,1] 0=individualistic, 1=family-led
  "AspirationalLevel": 0.8,     // [0,1] 0=stability-only, 1=upwardly mobile
  "PriceSensitivity": 0.3,       // [0,1] 0=price insensitive, 1=deal-only
  "RegionalCulture": 0.4,       // [0,1] 0=low collectivism, 1=high
  "InfluencerTrust": 0.7,       // [0,1] 0=ignores influencers, 1=highly swayed
  "ProfessionalSector": 0.8,    // [0,1] 0=informal/agri, 1=formal/tech
  "EnglishProficiency": 0.9,    // [0,1] 0=vernacular only, 1=fluent
  "HobbyDiversity": 0.7,       // [0,1] 0=narrow, 1=broad
  "CareerAmbition": 0.8,        // [0,1] 0=status quo, 1=aggressive growth
  "AgeBucket": 1.0,            // [0,1] 0=60+, 1=Gen Z
  "GenderMarital": 0.7          // [0,1] 0=married female homemaker, 1=single male (proxy)
}
```

#### `PersonaPriors`
```json
{
  "CC": 0.88,      // [0.2, 0.9] Cognitive Capacity
  "FR": 0.1,       // [0.1, 0.8] Cognitive Fatigue Rate
  "RT": 0.71,      // [0.1, 0.9] Risk Tolerance
  "LAM": 1.24,     // [1.0, 2.5] Loss Aversion Multiplier
  "ET": 0.82,      // [0.2, 0.9] Effort Tolerance
  "TB": 0.85,      // [0.2, 0.9] Trust Baseline
  "DR": 0.31,      // [0.05, 0.9] Temporal Discount Rate
  "CN": 0.22,      // [0.2, 0.9] Control Need
  "MS": 0.84       // [0.3, 1.0] Motivation Strength
}
```

#### `StateVariant`
```json
{
  "name": "fresh_motivated",
  "description": "Fresh arrival, high energy, motivated",
  "initial_state": {
    "cognitive_energy_0": "0.9 × CC",           // Formula string (evaluated at runtime)
    "perceived_risk_0": 0.1,
    "perceived_effort_0": 0.0,
    "perceived_value_0": 0.8,
    "perceived_control_0": "TB",               // Can reference priors
    "commitment_level": "high"
  }
}
```

#### `ProductStep`
```json
{
  "name": "PAN + Bank Linking",
  "description": "Financial data linking (irreversible)",
  "cognitive_demand": 0.4,        // [0,1]
  "effort_demand": 0.6,          // [0,1]
  "risk_signal": 0.7,            // [0,1]
  "irreversibility": 1,          // 0 or 1
  "delay_to_value": 2,           // Steps until payoff (0-5)
  "explicit_value": 0.5,        // [0,1]
  "reassurance_signal": 0.7,     // [0,1]
  "authority_signal": 0.6        // [0,1]
}
```

#### `Trace`
```json
{
  "persona_name": "GenZ_UPI_Native_Metro",
  "variant": "fresh_motivated",
  "priors": { "CC": 0.88, "FR": 0.1, ... },
  "journey": [
    {
      "step": "Landing Page",
      "state": {
        "cognitive_energy": 0.792,
        "perceived_risk": 0.100,
        "perceived_effort": 0.100,
        "perceived_value": 0.672,
        "perceived_control": 0.595
      },
      "costs": {
        "cognitive_cost": 0.042,
        "effort_cost": 0.000,
        "risk_cost": 0.124,
        "value_yield": 0.200,
        "reassurance_yield": 0.195,
        "total_cost": 0.166
      },
      "decision": "continue",
      "inequality_margin": 0.85  // (Left - Right) / Right
    },
    {
      "step": "PAN + Bank Linking",
      "state": { ... },
      "costs": { ... },
      "decision": "drop",
      "failure_reason": "Loss aversion"
    }
  ],
  "exit_step": "PAN + Bank Linking",
  "failure_reason": "Loss aversion"
}
```

#### `StepSummary`
```json
{
  "step_name": "PAN + Bank Linking",
  "failure_rate": 0.40,              // 40% of trajectories drop here
  "primary_cost": "Loss aversion",    // Dominant cost (≥40% of failures)
  "primary_cost_pct": 100.0,          // % of failures with this cost
  "secondary_cost": null,             // Or second-most common
  "secondary_cost_pct": 0.0,
  "total_trajectories": 35,
  "failures": 14,
  "confidence_bands": {              // Optional
    "hard_drop": 2,                   // Would have dropped
    "fragile": 5,                     // Close to drop
    "confident": 14                   // Confident continuation
  }
}
```

#### `ScenarioSummary`
```json
{
  "scenario_name": "fintech_onboarding_demo",
  "personas": 5,
  "state_variants_per_persona": 7,
  "product_steps": 6,
  "total_trajectories": 35,
  "completed_trajectories": 2,
  "completion_rate": 0.057,
  "step_summaries": [
    { "step_name": "Landing Page", "failure_rate": 0.257, ... },
    { "step_name": "PAN + Bank Linking", "failure_rate": 0.40, ... }
  ],
  "persona_insights": [
    {
      "persona_name": "GenZ_UPI_Native_Metro",
      "dominant_exit_step": "PAN + Bank Linking",
      "dominant_failure_reason": "Loss aversion",
      "consistency_score": 1.0,      // % of variants that exit at same step
      "variants_completed": 0,
      "variants_total": 7
    }
  ]
}
```

---

## Simulation Methodology

### Separation: Persona vs State

**Persona = Fixed Constraints (Who They Are)**
- Θ_persona = {CC, FR, RT, LAM, ET, TB, DR, CN, MS} never changes across runs
- These represent identity, culture, and capacity:
  - Cognitive capacity (CC) and fatigue rate (FR) are stable traits
  - Risk tolerance (RT) and loss aversion (LAM) reflect cultural priors
  - Effort tolerance (ET) and trust baseline (TB) are demographic + experience-based
  - Temporal discount rate (DR) and control need (CN) are cultural + generational

**State = Arrival Conditions (How They Arrive)**
- M_0 = {cognitive_energy, perceived_value, perceived_risk, perceived_control, commitment_level} varies across runs
- These represent mood, context, and arrival condition:
  - Same person on different days: tired vs fresh, urgent vs browsing, burned before vs trusting
  - State variants are deterministic patterns, not random noise

**Why This Separation is Scientifically Correct:**
- Humans don't change their loss aversion, digital literacy, or cultural priors day-to-day
- They do change: energy level, urgency, patience, trust at arrival
- By simulating many state trajectories for one persona, we detect failure modes (structural vs intent-sensitive)

---

### Default 10 State Variants (Detailed Formulas)

Each variant defines precise initial state formulas, consistent with spec ranges:

#### 1. `fresh_motivated`
- `cognitive_energy_0 = 0.9 × CC` (high energy, bounded by capacity)
- `perceived_value_0 = 0.8` (high motivation)
- `perceived_risk_0 = 0.1` (low initial risk)
- `perceived_effort_0 = 0.0` (no accumulated effort)
- `perceived_control_0 = TB` (baseline trust)
- `commitment_level = "high"`

**Interpretation**: User arrives fresh, motivated, trusting. Best-case scenario for conversion.

---

#### 2. `tired_commuter`
- `cognitive_energy_0 = 0.5 × CC` (moderate-low energy)
- `perceived_value_0 = 0.6` (moderate motivation)
- `perceived_risk_0 = 0.2` (slightly elevated risk)
- `perceived_effort_0 = 0.0`
- `perceived_control_0 = TB`
- `commitment_level = "medium"`

**Interpretation**: User arrives after work/commute, lower energy. Tests fatigue sensitivity.

---

#### 3. `distrustful_arrival`
- `cognitive_energy_0 = 0.8 × CC` (good energy)
- `perceived_value_0 = 0.6` (moderate motivation)
- `perceived_risk_0 = 0.4` (elevated risk perception)
- `perceived_effort_0 = 0.0`
- `perceived_control_0 = 0.5 × TB` (reduced trust)
- `commitment_level = "medium"`

**Interpretation**: User arrives skeptical (maybe burned before, or low trust baseline). Tests risk sensitivity.

---

#### 4. `browsing_casually`
- `cognitive_energy_0 = 0.9 × CC` (high energy)
- `perceived_value_0 = 0.3` (low motivation—just browsing)
- `perceived_risk_0 = 0.1` (low risk)
- `perceived_effort_0 = 0.0`
- `perceived_control_0 = TB`
- `commitment_level = "low"`

**Interpretation**: User arrives with high energy but low intent. Tests value sensitivity.

---

#### 5. `urgent_need`
- `cognitive_energy_0 = 0.7 × CC` (moderate energy)
- `perceived_value_0 = 0.9` (very high motivation—urgent problem)
- `perceived_risk_0 = 0.2` (moderate risk, but value outweighs)
- `perceived_effort_0 = 0.0`
- `perceived_control_0 = TB`
- `commitment_level = "very_high"`

**Interpretation**: User has urgent problem, high motivation. Tests if high value can overcome barriers.

---

#### 6. `burned_before`
- `cognitive_energy_0 = 0.8 × CC` (good energy)
- `perceived_value_0 = 0.5` (moderate motivation)
- `perceived_risk_0 = 0.6` (high risk perception—past negative experience)
- `perceived_effort_0 = 0.2` (accumulated effort from past attempts)
- `perceived_control_0 = 0.3 × TB` (very low trust)
- `commitment_level = "low"`

**Interpretation**: User has been burned before (scam, bad UX, data breach). Tests if reassurance can overcome high risk.

---

#### 7. `price_sensitive`
- `cognitive_energy_0 = 0.8 × CC` (good energy)
- `perceived_value_0 = 0.4` (lower value—price-conscious)
- `perceived_risk_0 = 0.3` (moderate risk)
- `perceived_effort_0 = 0.0`
- `perceived_control_0 = TB`
- `commitment_level = "medium"`

**Interpretation**: User is price-sensitive (high PriceSensitivity in persona). Tests temporal discounting sensitivity.

---

#### 8. `tech_savvy_optimistic`
- `cognitive_energy_0 = 0.95 × CC` (very high energy)
- `perceived_value_0 = 0.7` (high motivation)
- `perceived_risk_0 = 0.05` (very low risk—tech-savvy, optimistic)
- `perceived_effort_0 = 0.0`
- `perceived_control_0 = 1.2 × TB` (enhanced trust—tech familiarity)
- `commitment_level = "high"`

**Interpretation**: User is tech-savvy, optimistic, high digital literacy. Best-case for low-friction flows.

---

#### 9. `family_pressure`
- `cognitive_energy_0 = 0.7 × CC` (moderate energy)
- `perceived_value_0 = 0.6` (moderate motivation)
- `perceived_risk_0 = 0.5` (high risk—family influence amplifies loss aversion)
- `perceived_effort_0 = 0.0`
- `perceived_control_0 = 0.6 × TB` (reduced control—family decision-making)
- `commitment_level = "medium"`

**Interpretation**: User is under family pressure (high FamilyInfluence). Tests loss aversion sensitivity.

---

#### 10. `low_energy_high_intent`
- `cognitive_energy_0 = 0.3 × CC` (very low energy)
- `perceived_value_0 = 0.9` (very high motivation)
- `perceived_risk_0 = 0.2` (low risk)
- `perceived_effort_0 = 0.0`
- `perceived_control_0 = TB`
- `commitment_level = "very_high"`

**Interpretation**: User has high intent but very low energy (maybe late night, exhausted). Tests if high value can overcome cognitive fatigue.

---

### Aggregation Logic Over Variants

**Pattern Detection Rules:**

1. **Structural Failure (≥70% consistency)**
   - If ≥70% of variants for a persona fail at the same step t, label it a "structural failure" for that persona
   - Interpretation: The product step has a fundamental flaw for this persona type (e.g., PAN step fails for all variants of a risk-averse persona)

2. **Fatigue-Sensitive Step**
   - If only low-energy variants (`tired_commuter`, `low_energy_high_intent`) fail at step t, but high-energy variants pass, mark step as "fatigue-sensitive"
   - Interpretation: The step requires high cognitive capacity—reduce cognitive_demand or add breaks

3. **Intent-Sensitive Step**
   - If only low-commitment variants (`browsing_casually`, `price_sensitive`) fail at step t, but high-commitment variants pass, mark step as "intent-sensitive"
   - Interpretation: The step requires high motivation—improve value proposition or reduce delay_to_value

4. **Risk-Sensitive Step**
   - If only high-risk variants (`distrustful_arrival`, `burned_before`, `family_pressure`) fail at step t, but low-risk variants pass, mark step as "risk-sensitive"
   - Interpretation: The step triggers loss aversion—increase reassurance_signal or reduce irreversibility

5. **Multi-Factor Failure**
   - If variants fail at different steps or for different reasons, label as "multi-factor failure"
   - Interpretation: The product has multiple issues—requires holistic redesign

**Implementation:**
- For each persona, compute `consistency_score = max(exit_step_counts) / total_variants`
- If consistency_score ≥ 0.7: structural failure
- Else: analyze which variant types fail (low-energy, low-commitment, high-risk) to label sensitivity

---

## Why Not Monte Carlo?

### Problems with Monte Carlo for Product Teams

1. **Opaque noise on noisy metrics**: Real funnels already have variance (seasonality, traffic quality, A/B tests). Adding random noise from Monte Carlo makes it impossible to separate signal (structural product flaws) from noise (random variation).

2. **Unreproducible results**: PMs run simulation Monday, see "40% drop at step 4." Run again Tuesday, see "38% drop at step 4." Which is correct? Can't explain the difference to stakeholders or VCs.

3. **Hard to debug**: If a step looks bad, you can't tell if it's due to randomness or structure. Did 10% of runs fail because of bad luck or because the step is fundamentally flawed? Requires many runs to converge, slowing iteration.

4. **Fuzzy attribution**: With randomness, risk vs effort vs fatigue costs are blurred. You can't say "this step fails due to loss aversion" with confidence—maybe it was just a bad random draw.

5. **A/B documentation risk**: If you're using simulation to justify a product change, and the simulation is non-deterministic, a VC or PM can challenge: "Run it again—does it still show improvement?" If results differ, you lose credibility.

6. **Calibration difficulty**: When calibrating coefficients from real data, you need deterministic outputs to compare against observed outcomes. Randomness adds variance that makes calibration noisy.

---

### Benefits of Deterministic State-Variant Simulation

1. **Same inputs → same outputs (critical for A/B docs and VC pitches)**: Run simulation with Persona A and Product Flow X, always get the same failure rates and cost labels. Reproducible, defensible, trustworthy.

2. **Each variant is interpretable and reusable**: "tired_commuter" means the same thing across all products. PMs can say "we tested the tired commuter scenario" and everyone understands. Variants become a shared language.

3. **Easier to calibrate coefficients from real data**: When you have real funnel data, you can fit coefficients (e.g., adjust the weight of FamilyInfluence in LAM) by comparing deterministic predictions to observed outcomes. No randomness to average out.

4. **Clear, causal narratives**: "Your PAN step fails when a user is low energy and moderate risk (tired_commuter variant), but passes when urgent and high value (urgent_need variant)." This is actionable—reduce cognitive demand or increase value signal.

5. **Structured uncertainty**: Instead of random noise, we model uncertainty through structured state variants. "We don't know if the user is tired or fresh, so we test both." This is scientific uncertainty (epistemic), not aleatoric noise.

6. **Debugging is straightforward**: If a step fails for all variants of a persona, it's a structural issue. If it only fails for low-energy variants, it's fatigue-sensitive. The pattern tells you exactly what to fix.

7. **VC-defensible**: VCs can audit the simulation, see the formulas, understand the logic. "Why did this step fail?" → "Because cognitive_cost exceeded cognitive_energy, and here's the exact formula." No black box.

---

## Why DropSim is Defensible

### Behavioral Grounding

DropSim is built on established behavioral science models, not ad-hoc heuristics:

- **System 2 Fatigue (Cognitive Cost)**: Based on Kahneman's dual-process theory—System 2 thinking is effortful and depletes mental energy. Our formula `cognitive_demand × (1 + FR) × (1 - cognitive_energy_t)` captures the amplification effect when energy is already low.

- **Fogg Ability Model (Effort Cost)**: Based on BJ Fogg's Behavior Model—ability (effort tolerance) inversely affects perceived effort. Our formula `effort_demand × (1 - ET)` directly implements this.

- **Prospect Theory / Loss Aversion (Risk Cost)**: Based on Kahneman & Tversky's Prospect Theory—losses loom larger than gains. Our LAM (Loss Aversion Multiplier) amplifies risk signals, and irreversibility further amplifies (sunk cost effect).

- **Temporal Discounting (Value Yield)**: Based on behavioral economics—future value decays exponentially. Our formula `explicit_value × exp(-DR × delay_to_value)` implements hyperbolic discounting.

- **Control Need (Reassurance Yield)**: Based on psychological research on autonomy and control—users with high control need benefit less from reassurance. Our formula `(reassurance_signal + authority_signal) × (1 - CN)` captures this.

**Moat**: While competitors use black-box ML or generic analytics, DropSim's equations are transparent, grounded in science, and explainable. PMs can point to the exact formula that caused a drop-off.

---

### Data Flywheel

Over time, DropSim becomes more accurate through a data flywheel:

1. **Client funnels + outcomes**: As clients use DropSim and launch products, we collect real funnel data (actual drop-off rates, A/B test results).

2. **Coefficient calibration**: We fit persona compiler coefficients (e.g., weight of FamilyInfluence in LAM) by comparing deterministic predictions to observed outcomes. More data → better calibration → more accurate predictions.

3. **Vertical-specific presets**: We learn that fintech onboarding has different risk signals than edtech signup. We build vertical-specific presets with tuned step attributes and persona libraries.

4. **Segment priors**: We learn that "Salaried Tier-2 Cautious" personas in India have different LAM values than similar personas in other markets. We build regional/segment-specific priors.

5. **State variant refinement**: We learn which state variants are most predictive (maybe "burned_before" is more common than "tech_savvy_optimistic"). We refine the variant library.

**Moat**: More clients → more data → better calibration → more accurate predictions → more clients. This is a classic data network effect.

---

### Explainability Moat

While others do black-box funnel ML or generic analytics, DropSim gives step-level *whys* tied directly to equations:

**Competitor (Generic Analytics)**: "Your funnel has a 40% drop at step 4."
- PM: "Why?"
- Competitor: "We don't know—maybe the step is too long?"

**Competitor (Black-Box ML)**: "Our model predicts 40% drop at step 4."
- PM: "Why?"
- Competitor: "The model learned it from data, but we can't explain the features."

**DropSim**: "Step 4 (PAN + Bank Linking) fails for 40% of state-variants. Primary cost: Loss aversion (100% of failures). Secondary cost: None."
- PM: "Why loss aversion?"
- DropSim: "Because `risk_cost_t = risk_signal × LAM × (1 + irreversibility)`. Your step has `risk_signal=0.7` and `irreversibility=1`, and personas with high FamilyInfluence have `LAM > 2.0`. The formula computes `risk_cost = 0.7 × 2.0 × 2.0 = 2.8`, which exceeds `perceived_value × MS + perceived_control`, so the inequality fails."
- PM: "How do I fix it?"
- DropSim: "Reduce `risk_signal` (simplify the step), increase `reassurance_signal` (add trust badges), or reduce `irreversibility` (make it reversible)."

**Moat**: PMs and VCs trust DropSim because it's explainable. They can audit the formulas, understand the logic, and make informed decisions. This builds trust and defensibility.

---

### Summary: Three-Layer Defensibility

1. **Behavioral grounding**: Science-backed formulas (System 2, Fogg, Prospect Theory) → transparent, explainable, defensible.
2. **Data flywheel**: More clients → more data → better calibration → more accurate → more clients.
3. **Explainability moat**: Step-level whys tied to equations → PMs trust it, VCs can audit it, competitors can't replicate the narrative.

**Result**: DropSim is not just a tool—it's a defensible product with a clear moat, grounded in science, improved by data, and differentiated by explainability.

---

## How to Run DropSim Locally

### Prerequisites

```bash
pip install -r requirements.txt
```

Required packages: `pandas`, `numpy`, `fastapi`, `uvicorn`, `pydantic`

### CLI Usage

#### Run Fintech Preset

```bash
python dropsim_cli.py simulate --preset fintech
```

**Output:**
- Step-level failure rates
- Primary/secondary costs (System 2 fatigue, Loss aversion, Temporal discounting, Low ability)
- Persona summaries with consistency scores

#### Run Custom Scenario

```bash
python dropsim_cli.py simulate --scenario-file examples/fintech_onboarding.json
python dropsim_cli.py simulate --scenario-file examples/edtech_onboarding.json
```

#### View Specific Persona × Variant Trace

```bash
python dropsim_cli.py simulate --preset fintech \
  --persona-name "Salaried_Tier2_Cautious" \
  --variant tired_commuter
```

**Output:**
- Step-by-step state evolution
- Cognitive energy, perceived risk/effort/value/control at each step
- Exact point of failure with labeled reason

#### Export to JSON

```bash
python dropsim_cli.py simulate --preset fintech --export fintech_traces.json
python dropsim_cli.py simulate --scenario-file examples/edtech_onboarding.json --export edtech_traces.json
```

**Exports:**
- Full trajectory traces
- Per-step state snapshots
- Cost breakdowns
- Machine-readable format for data science teams

### JSON API Usage

#### Start API Server

```bash
uvicorn dropsim_api:app --reload
```

Server runs at `http://localhost:8000`

#### Run Simulation via API

```bash
curl -X POST http://localhost:8000/simulate \
  -H "Content-Type: application/json" \
  -d @examples/fintech_onboarding.json
```

**Response:**
```json
{
  "scenario_summary": {
    "scenario_name": "fintech_onboarding_demo",
    "total_trajectories": 35,
    "completed_trajectories": 2,
    "completion_rate": 0.057,
    "step_summaries": [
      {
        "step_name": "PAN + Bank Linking",
        "failure_rate": 0.40,
        "primary_cost": "Loss aversion",
        "primary_cost_pct": 100.0,
        "secondary_cost": null,
        "total_trajectories": 35,
        "failures": 14
      }
    ],
    "persona_summaries": [...]
  }
}
```

#### Include Full Traces

```bash
curl -X POST "http://localhost:8000/simulate?include_traces=true" \
  -H "Content-Type: application/json" \
  -d @examples/fintech_onboarding.json
```

**Response includes:**
- `traces`: Full journey data for each persona × variant
- Per-step state and costs
- Exit points and failure reasons

#### Health Check

```bash
curl http://localhost:8000/health
```

### Scenario JSON Format

Create your own scenario by following the `ScenarioConfig` schema:

```json
{
  "scenario_name": "my_custom_scenario",
  "personas": [
    {
      "name": "Persona_Name",
      "description": "Description",
      "raw_fields": {
        "SEC": 0.6,
        "UrbanRuralTier": 1.0,
        "DigitalLiteracy": 0.9,
        ...
      }
    }
  ],
  "steps": [
    {
      "name": "Step Name",
      "description": "Step description",
      "cognitive_demand": 0.3,
      "effort_demand": 0.4,
      "risk_signal": 0.2,
      "irreversibility": 0,
      "delay_to_value": 2,
      "explicit_value": 0.5,
      "reassurance_signal": 0.4,
      "authority_signal": 0.3
    }
  ]
}
```

See `examples/fintech_onboarding.json` and `examples/edtech_onboarding.json` for complete examples.

### Output Language

All outputs use design doc language:
- **"System 2 fatigue"** (not "cognitive_cost")
- **"Loss aversion"** (not "risk_cost")
- **"Temporal discounting"** (not "value_decay")
- **"Low ability"** (not "effort_cost")

This ensures consistency between CLI, API, and documentation.

---

## Bringing Your Real Funnel into DropSim

### Calibration Overview

DropSim can compare its predictions to your actual funnel data, identify prediction errors, and suggest coefficient adjustments. This closes the loop between simulation and reality.

### Observed Funnel JSON Format

Create an `ObservedFunnel` JSON file with your real funnel data:

```json
{
  "total_users": 1000,
  "steps": [
    {
      "step_name": "Landing Page",
      "users_entered": 1000,
      "users_dropped": 280,
      "segment": "all"
    },
    {
      "step_name": "Mobile + OTP",
      "users_entered": 720,
      "users_dropped": 150,
      "segment": "all"
    }
  ]
}
```

**Fields:**
- `total_users`: Starting cohort size (optional)
- `steps`: Array of step observations
  - `step_name`: Must match step names in your scenario
  - `users_entered`: Number of users who reached this step
  - `users_dropped`: Number of users who dropped at this step
  - `segment`: Optional segment identifier (e.g., "new_to_digital", "high_risk")

### CLI Usage with Calibration

```bash
python dropsim_cli.py simulate \
  --preset fintech \
  --observed-funnel examples/fintech_observed_funnel.json \
  --export fintech_with_calibration.json
```

**Output includes:**
1. **Standard DropSim Report**: Predicted failure rates and cost labels
2. **Calibration Report**: Step-by-step comparison of predicted vs observed
3. **Model Tuning Suggestions**: Directional coefficient adjustments

### Sample Calibration Output

```
================================================================================
📊 CALIBRATION REPORT
   DropSim Predictions vs Observed Funnel Data
================================================================================

Overall Mean Absolute Error: 6.8 percentage points
Underestimates (>5pp): 2 steps
Overestimates (>5pp): 0 steps

Step-by-Step Comparison:
--------------------------------------------------------------------------------

Step: PAN + Bank Linking
  Predicted failure rate: 40.0%
  Observed failure rate: 44.9%
  Delta: -4.9 percentage points
  ✅ DropSim prediction is within 5pp of observed
  Dominant cost labels: Loss aversion

Step: Mobile + OTP
  Predicted failure rate: 14.3%
  Observed failure rate: 20.8%
  Delta: -6.5 percentage points
  ⚠️  DropSim UNDERESTIMATES drop-off by 6.5pp
  Dominant cost labels: Multi-factor failure, System 2 fatigue
  💡 Recommendation: DropSim predicts cognitive fatigue; observed drop is higher.
     Consider increasing cognitive_demand or FR (Fatigue Rate) for this segment.

================================================================================
🔧 MODEL TUNING SUGGESTIONS (v0)
   Directional adjustments based on prediction errors
================================================================================

1. LAM (FamilyInfluence)
   Current weight: 0.6
   Suggested weight: 0.65
   Change: +0.05
   Reason: High-risk steps (PAN + Bank Linking, etc.) systematically under-predict drop.
          Loss aversion is dominant, suggesting FamilyInfluence should have higher weight in LAM.
```

### Interpreting Calibration Results

**Underestimates (>5pp):**
- DropSim predicts lower drop-off than observed
- **Action**: Review step attributes (increase `risk_signal`, `cognitive_demand`, or `effort_demand`) or adjust persona priors

**Overestimates (>5pp):**
- DropSim predicts higher drop-off than observed
- **Action**: Step may be easier than modeled (decrease step attributes) or users are more motivated than predicted

**Within 5pp:**
- DropSim prediction is accurate
- **Action**: No immediate changes needed

### Model Tuning Suggestions

DropSim provides **directional suggestions** (not automated optimization):

1. **High-risk steps systematically under-predict**: Increase `LAM` (Loss Aversion Multiplier) weights
2. **High-cognitive steps under-predict**: Increase `FR` (Fatigue Rate) or decrease `CC` (Cognitive Capacity)
3. **High-effort steps under-predict**: Decrease `ET` (Effort Tolerance) weights
4. **High-delay steps over-predict**: Decrease `DR` (Discount Rate) sensitivity

**Apply incrementally**: Make suggested adjustments, re-run calibration, and iterate.

### Example: Fintech Onboarding Calibration

See `examples/fintech_observed_funnel.json` for a complete example matching the fintech preset.

**Key insights from calibration:**
- PAN + Bank Linking: DropSim predicts 40%, observed 45% → Close match, loss aversion confirmed
- Mobile + OTP: DropSim predicts 14%, observed 21% → Underestimate, may need higher cognitive/effort costs
- First Transaction: DropSim predicts 0%, observed 20% → Large underestimate, may need additional step attributes

---

## Running a DropSim Case Study in 30 Minutes

### Overview

This workflow demonstrates how to run a complete DropSim analysis, compare predictions to real data, export visualization-ready data, and generate insights—all in about 30 minutes.

### Step 1: Simulate with Calibration

```bash
python dropsim_cli.py simulate --preset fintech \
  --observed-funnel examples/fintech_observed_funnel.json \
  --export fintech_traces.json \
  --export-plot-data fintech_steps.csv \
  --trace-plot-data fintech_urban_prof_tired_commuter.csv \
  --persona-name Urban_Professional_Optimizer \
  --variant tired_commuter
```

**What this does:**
- Runs fintech preset simulation (5 personas × 7 variants = 35 trajectories)
- Compares predictions to observed funnel data
- Exports full traces to JSON
- Exports step-level data to CSV for plotting
- Exports one trajectory (Urban Professional × tired commuter) to CSV for state visualization

### Step 2: Inspect Console Output

**Key insights to look for:**

1. **Step with highest predicted failure:**
   - Example: "PAN + Bank Linking fails for 40% of state-variants"
   - **Why**: "Primary cost: Loss aversion (100% of failures)"
   - **Interpretation**: The irreversible financial data step triggers loss aversion across most personas

2. **Prediction vs observation:**
   - Example: "Predicted: 40.0% | Observed: 44.9%"
   - **Delta**: -4.9 percentage points (within 5pp = good match)
   - **Interpretation**: DropSim accurately predicts this step's failure rate

3. **Underestimates/overestimates:**
   - Example: "First Transaction: Predicted 0.0% | Observed 20.0%"
   - **Delta**: -20.0 percentage points (large underestimate)
   - **Interpretation**: Model may be missing behavioral costs at this step

4. **Behavioral "why":**
   - **System 2 fatigue**: Cognitive demand too high
   - **Loss aversion**: Risk signal or irreversibility too high
   - **Low ability**: Effort demand exceeds user capacity
   - **Temporal discounting**: Value too delayed

### Step 3: Visualize in Your Tool

#### Plot 1: Predicted vs Observed Failure Rate by Step

**Data source:** `fintech_steps.csv`

**Columns:**
- `step_index`, `step_name`
- `predicted_failure_rate`
- `observed_failure_rate` (if calibration provided)
- `delta`
- `primary_cost`, `secondary_cost`

**Visualization:**
- X-axis: Step index or step name
- Y-axis: Failure rate (0-1 or 0-100%)
- Two lines: Predicted (blue) and Observed (orange)
- Bars: Delta (green = overestimate, red = underestimate)
- Color-code by `primary_cost` to see behavioral patterns

**Insights to look for:**
- Steps where predicted and observed align → Model is accurate
- Steps with large deltas → Model needs tuning
- Steps with consistent primary cost → Clear behavioral driver

#### Plot 2: State Trajectory for One Persona × Variant

**Data source:** `fintech_urban_prof_tired_commuter.csv`

**Columns:**
- `step_index`, `step_name`
- `cognitive_energy`
- `perceived_value`
- `perceived_risk`
- `perceived_effort`
- `perceived_control`
- `continue_or_drop`
- `cognitive_cost`, `effort_cost`, `risk_cost`, `value_yield`

**Visualization:**
- X-axis: Step index
- Y-axis: State value (0-3 for risk/effort/value, 0-2 for control, 0-CC for energy)
- Multiple lines: One per state variable
- Vertical line: Drop point (where `continue_or_drop = 'drop'`)
- Shaded areas: Cost accumulation (risk + effort) vs value + control

**Insights to look for:**
- **Energy collapse**: Cognitive energy drops to near-zero before drop
- **Risk accumulation**: Perceived risk rises steadily, crosses threshold
- **Value decay**: Perceived value decreases (temporal discounting)
- **Control gap**: Perceived control insufficient to overcome risk/effort

### Step 4: Read the Narrative Summary

At the end of the run, DropSim generates a **Narrative Summary**—5-10 sentences of plain-language insights:

**Example:**
> "Most failures occur at the 'PAN + Bank Linking' step, with 40.0% of state-variants dropping off. This step is primarily driven by loss aversion, indicating that users are dropping due to this behavioral factor. Several personas show high consistency (≥70%) in their exit points, suggesting structural product flaws rather than intent-sensitive behavior. Observed funnel data shows that DropSim underestimates drop-off at 'First Transaction' by 20.0 percentage points, suggesting that the model may be under-weighting certain behavioral costs for this step."

**Use this:**
- Copy-paste into strategy docs
- Quote in investor decks
- Share with product team for alignment

### Step 5: Act on Insights

**If loss aversion is dominant:**
- Reduce `risk_signal` (simplify step, add reassurance)
- Reduce `irreversibility` (make step reversible)
- Increase `reassurance_signal` (trust badges, security messaging)

**If System 2 fatigue is dominant:**
- Reduce `cognitive_demand` (simplify UI, reduce choices)
- Add breaks between high-cognitive steps
- Increase `explicit_value` (show progress, immediate benefits)

**If temporal discounting is dominant:**
- Reduce `delay_to_value` (show value sooner)
- Increase `explicit_value` (make benefits clearer)
- Add intermediate value signals

**If low ability is dominant:**
- Reduce `effort_demand` (fewer fields, auto-fill)
- Increase `reassurance_signal` (help text, tooltips)
- Simplify step flow

### Tools for Visualization

**Google Sheets:**
1. Import CSV
2. Create line chart (predicted vs observed)
3. Add conditional formatting for deltas

**Tableau:**
1. Connect to CSV
2. Create dual-axis chart (predicted + observed)
3. Add filters for primary_cost

**Python/Jupyter:**
```python
import pandas as pd
import matplotlib.pyplot as plt

# Step-level data
df = pd.read_csv('fintech_steps.csv')
plt.plot(df['step_index'], df['predicted_failure_rate'], label='Predicted')
plt.plot(df['step_index'], df['observed_failure_rate'], label='Observed')
plt.xlabel('Step')
plt.ylabel('Failure Rate')
plt.legend()
plt.show()

# Trajectory data
traj = pd.read_csv('fintech_urban_prof_tired_commuter.csv')
plt.plot(traj['step_index'], traj['perceived_value'], label='Value')
plt.plot(traj['step_index'], traj['perceived_risk'], label='Risk')
plt.axvline(x=traj[traj['continue_or_drop']=='drop']['step_index'].values[0], 
            color='r', linestyle='--', label='Drop')
plt.xlabel('Step')
plt.ylabel('State Value')
plt.legend()
plt.show()
```

**Excel:**
1. Import CSV
2. Insert → Chart → Line Chart
3. Format axes and add data labels

### Time Breakdown

- **Simulation + calibration**: 2-3 minutes
- **Inspect console output**: 5 minutes
- **Import and plot data**: 10-15 minutes
- **Read narrative + act on insights**: 5-10 minutes

**Total: ~30 minutes** for a complete case study from simulation to actionable insights.

---

## Fast Start: Lite Input Mode (No Math Required)

### Overview

Lite Input Mode allows non-technical PMs to describe personas and steps using simple labels (low/medium/high) instead of raw numeric values. DropSim automatically maps these labels to the full behavioral engine.

### Lite Scenario Format

**Persona Labels:**
```json
{
  "name": "Rural Cautious",
  "sec": "low" | "mid" | "high",
  "urban_rural": "rural" | "tier2" | "metro",
  "digital_skill": "low" | "medium" | "high",
  "family_influence": "low" | "medium" | "high",
  "aspiration": "low" | "medium" | "high",
  "price_sensitivity": "low" | "medium" | "high",
  "risk_attitude": "risk_averse" | "balanced" | "risk_tolerant" (optional),
  "age_bucket": "senior" | "middle" | "young",
  "intent": "low" | "medium" | "high"
}
```

**Step Labels:**
```json
{
  "name": "Bank Account Linking",
  "type": "landing" | "signup" | "kyc" | "payment" | "consent" | "other",
  "mental_complexity": "low" | "medium" | "high",
  "effort": "low" | "medium" | "high",
  "risk": "low" | "medium" | "high",
  "irreversible": true | false,
  "value_visibility": "low" | "medium" | "high",
  "delay_to_value": "instant" | "soon" | "later",
  "reassurance": "low" | "medium" | "high",
  "authority": "low" | "medium" | "high"
}
```

### Usage

```bash
python dropsim_cli.py simulate-lite \
  --lite-scenario-file examples/fintech_lite_onboarding.json
```

**All standard flags work:**
```bash
python dropsim_cli.py simulate-lite \
  --lite-scenario-file examples/fintech_lite_onboarding.json \
  --observed-funnel examples/fintech_observed_funnel.json \
  --export-plot-data steps.csv \
  --persona-name "Rural Cautious" \
  --variant tired_commuter
```

### How Lite Labels Map to Behavioral Engine

**Persona Mappings:**
- `"low"` / `"medium"` / `"high"` → 0.2 / 0.5 / 0.8 (with context-specific adjustments)
- `"rural"` / `"tier2"` / `"metro"` → 0.0 / 0.4 / 1.0 (UrbanRuralTier)
- `"senior"` / `"middle"` / `"young"` → 0.1 / 0.5 / 0.9 (AgeBucket)
- `"low"` / `"medium"` / `"high"` intent → 0.4 / 0.6 / 0.85 (Motivation Strength)
- `"risk_averse"` / `"balanced"` / `"risk_tolerant"` → 0.2 / 0.5 / 0.8 (Risk Tolerance override)

**Step Mappings:**
- `"low"` / `"medium"` / `"high"` mental_complexity → 0.2 / 0.5 / 0.8 (cognitive_demand)
- `"low"` / `"medium"` / `"high"` effort → 0.2 / 0.5 / 0.8 (effort_demand)
- `"low"` / `"medium"` / `"high"` risk → 0.1 / 0.4 / 0.8 (risk_signal)
- `"instant"` / `"soon"` / `"later"` → 0 / 2 / 4 (delay_to_value)
- `"low"` / `"medium"` / `"high"` value_visibility → 0.2 / 0.5 / 0.8 (explicit_value)

**Type-Specific Adjustments:**
- `"payment"` type → Automatically increases risk_signal to ≥0.6, sets irreversibility=1
- `"kyc"` type → Automatically increases effort_demand to ≥0.6, authority_signal to ≥0.5
- `"landing"` type → Automatically caps risk_signal ≤0.2, effort_demand ≤0.2

### Example: Lite Scenario

See `examples/fintech_lite_onboarding.json` for a complete example with:
- 3 personas: "Rural Cautious", "Urban Young Risk-Taker", "Tier-2 Salaried Worker"
- 5 steps: Landing → Phone Verification → KYC → Bank Linking → First Transaction

**Key insight:** Even with simple labels, DropSim still produces the same behavioral insights:
- "high risk" + `"irreversible: true"` → Loss aversion dominant
- `"high mental_complexity"` → System 2 fatigue dominant
- `"high effort"` → Low ability dominant

### When to Use Lite vs Full Mode

**Use Lite Mode if:**
- You're a PM/founder describing your funnel for the first time
- You want to quickly test different persona/step combinations
- You don't need precise numeric control

**Use Full Mode if:**
- You're calibrating from real data and need exact values
- You're building vertical-specific presets
- You need to fine-tune specific coefficients

**Both modes use the same engine** - Lite is just a convenience layer on top.

---

## Target-Group Filtering (Don't Waste Simulation on Non-Users)

### Overview

Target-group filtering allows you to focus simulation on specific persona segments, reducing computation and noise while focusing on your actual target audience.

### Target Group JSON Format

```json
{
  "sec": ["low", "mid", "high"],
  "urban_rural": ["rural", "tier2", "metro"],
  "age_bucket": ["young", "middle", "senior"],
  "digital_skill": ["low", "medium", "high"],
  "risk_attitude": ["risk_averse", "balanced", "risk_tolerant"],
  "intent": ["low", "medium", "high"]
}
```

**All fields are optional** - only specified filters are applied. If a field is omitted, all values for that dimension are allowed.

### Usage

#### With Preset

```bash
python dropsim_cli.py simulate --preset fintech \
  --target-group examples/fintech_target_group_young_urban_risk_tolerant.json
```

#### With Lite Input

```bash
python dropsim_cli.py simulate-lite \
  --lite-scenario-file examples/fintech_lite_onboarding.json \
  --target-group examples/fintech_target_group_young_urban_risk_tolerant.json
```

#### With Custom Scenario

```bash
python dropsim_cli.py simulate --scenario-file examples/fintech_onboarding.json \
  --target-group examples/fintech_target_group_young_urban_risk_tolerant.json
```

### How It Works

1. **Persona Meta Tags**: Each persona has categorical meta tags (sec_band, urban_rural, age_bucket_label, etc.) extracted from raw fields or lite labels.

2. **Filtering**: Before simulation, DropSim filters personas using `persona_matches_target()`:
   - Checks each specified filter field
   - Persona must match ALL specified filters
   - If no filter specified for a field, all values allowed

3. **Simulation**: Only filtered personas are simulated, reducing computation:
   - Original: 5 personas × 7 variants = 35 trajectories
   - Filtered: 2 personas × 7 variants = 14 trajectories

4. **Output**: All outputs (narrative, calibration, exports) operate on filtered set only.

### Example: Young Urban Risk-Tolerant

**Target Group:**
```json
{
  "urban_rural": ["metro"],
  "age_bucket": ["young"],
  "risk_attitude": ["balanced", "risk_tolerant"],
  "intent": ["medium", "high"]
}
```

**Result:**
- Filters fintech preset from 5 personas → 2 personas (GenZ_UPI_Native_Metro, Urban_Professional_Optimizer)
- Reduces trajectories from 35 → 14
- Focuses insights on target segment

### When to Use

**Use target-group filtering when:**
- You have a specific target audience (e.g., "young metro users")
- You want to reduce computation time
- You want cleaner, segment-focused insights
- You're doing segment-specific calibration

**Don't use when:**
- You want to understand all personas
- You're exploring which segments to target
- You need full funnel coverage

---

## LLM-Assisted Fintech Ingestion (From Product Text to Simulation)

### Overview

DropSim can automatically extract personas, steps, and target groups from product descriptions using LLM, eliminating the need for manual scenario configuration.

### How It Works

1. **Input**: Product description text (website copy, OCR from screenshots, product spec)
2. **LLM Processing**: Structured extraction of LiteScenario + TargetGroup
3. **Validation**: Enum validation and normalization
4. **Simulation**: Automatic conversion to full scenario and simulation run

### LLM Input & Output Contract

**Input:**
- `product_text`: Product description, website copy, or OCR text
- `persona_notes`: Optional plain-language notes about target personas
- `target_group_notes`: Optional notes about target group filters

**Output JSON Schema:**
```json
{
  "lite_scenario": {
    "product_type": "fintech",
    "personas": [
      {
        "name": "Persona Name",
        "sec": "low" | "mid" | "high",
        "urban_rural": "rural" | "tier2" | "metro",
        "digital_skill": "low" | "medium" | "high",
        "family_influence": "low" | "medium" | "high",
        "aspiration": "low" | "medium" | "high",
        "price_sensitivity": "low" | "medium" | "high",
        "risk_attitude": "risk_averse" | "balanced" | "risk_tolerant" (optional),
        "age_bucket": "senior" | "middle" | "young",
        "intent": "low" | "medium" | "high"
      }
    ],
    "steps": [
      {
        "name": "Step Name",
        "type": "landing" | "signup" | "kyc" | "payment" | "consent" | "other",
        "mental_complexity": "low" | "medium" | "high",
        "effort": "low" | "medium" | "high",
        "risk": "low" | "medium" | "high",
        "irreversible": true | false,
        "value_visibility": "low" | "medium" | "high",
        "delay_to_value": "instant" | "soon" | "later",
        "reassurance": "low" | "medium" | "high",
        "authority": "low" | "medium" | "high"
      }
    ]
  },
  "target_group": {
    "sec": ["low", "mid", "high"] (optional),
    "urban_rural": ["rural", "tier2", "metro"] (optional),
    "age_bucket": ["young", "middle", "senior"] (optional),
    "digital_skill": ["low", "medium", "high"] (optional),
    "risk_attitude": ["risk_averse", "balanced", "risk_tolerant"] (optional),
    "intent": ["low", "medium", "high"] (optional)
  }
}
```

### Prompt Engineering

The LLM prompt is explicitly fintech-aware and instructs the model to:

**Persona Extraction:**
- Identify personas based on income/SEC hints, city/tier, digital comfort, family dynamics, risk preferences, age cues
- Map to LitePersona categorical values
- Use conservative defaults when uncertain

**Step Extraction:**
- Identify common fintech steps: Landing, Phone+OTP, KYC, Bank-linking, Consent, First transaction
- Map to LiteStep attributes:
  - `mental_complexity`: Thinking required (low = simple, high = complex forms)
  - `effort`: Physical/time effort (low = click, high = find documents, upload)
  - `risk`: Data/financial risk (low = browsing, high = sharing financial data)
  - `irreversible`: Can user undo? (true = bank linking, false = browsing)
  - `value_visibility`: Benefit clarity (low = vague, high = immediate)
  - `delay_to_value`: Steps until payoff (instant/soon/later)
  - `reassurance`: Trust signals (low = none, high = security badges)
  - `authority`: Official backing (low = none, high = bank/govt)

**Constraints:**
- Use only allowed categorical values (strict validation)
- Keep personas to 2-5, steps to 4-8
- Steps in chronological order
- Conservative defaults when uncertain

### Usage

```bash
# Basic ingestion
python dropsim_cli.py ingest-fintech \
  --product-text-file examples/sample_fintech_product_text.txt

# With persona/target notes
python dropsim_cli.py ingest-fintech \
  --product-text-file examples/sample_fintech_product_text.txt \
  --persona-notes-file persona_notes.txt \
  --target-notes-file target_notes.txt

# Export inferred scenario for editing
python dropsim_cli.py ingest-fintech \
  --product-text-file examples/sample_fintech_product_text.txt \
  --export-lite-scenario generated_scenario.json

# Full workflow with calibration
python dropsim_cli.py ingest-fintech \
  --product-text-file examples/sample_fintech_product_text.txt \
  --observed-funnel examples/fintech_observed_funnel.json \
  --export-plot-data steps.csv
```

### Validation & Guardrails

**Enum Validation:**
- All persona/step fields validated against allowed values
- Invalid values mapped to closest valid value or dropped with warning
- Missing optional fields use conservative defaults

**Error Handling:**
- JSON parsing errors → Clear error message with suggestions
- Invalid personas/steps → Dropped with warning, simulation continues if any valid
- LLM API failures → Clear error message with troubleshooting tips

**Debug Mode:**
- `--verbose` flag shows LLM prompt (first 500 chars) and response (first 500 chars)
- Useful for development and troubleshooting

### Example Flow

1. **PM provides product text:**
   ```
   "SavingsGoal - goal-based savings app for young professionals..."
   ```

2. **LLM extracts:**
   - 2-3 personas (e.g., "Young Metro Professional", "Tier-2 Salaried Worker")
   - 5-6 steps (Landing → Phone → KYC → Bank Linking → Goal Creation → First Transfer)
   - Target group: `{"age_bucket": ["young"], "urban_rural": ["metro"]}`

3. **DropSim runs:**
   - Converts to full scenario
   - Filters personas by target group
   - Runs simulation
   - Produces behavioral insights

4. **PM iterates:**
   - Exports lite scenario JSON
   - Edits personas/steps
   - Re-runs with `simulate-lite`

### LLM Client Interface

DropSim uses an abstract `LLMClient` interface:

```python
class LLMClient:
    def complete(self, prompt: str) -> str:
        """Complete prompt and return response text."""
        raise NotImplementedError
```

**Default Implementation:** `OpenAILLMClient` (uses OpenAI API)

**Extensibility:** Can implement other providers (Anthropic, local models, etc.)

### Fintech Archetype Support

DropSim's LLM ingestion recognizes and specializes for 6 common fintech archetypes:

1. **payments_wallet** - UPI, wallets, P2P transfers
2. **neo_bank** - Digital banking accounts, cards, deposits
3. **lending_bnpl** - Credit cards, BNPL, personal loans
4. **trading_investing** - Stock trading, mutual funds, crypto
5. **insurance** - Health, life, motor insurance
6. **personal_finance_manager** - PFM, spend analytics, goal-based savings

Each archetype has:
- **Archetype-specific step templates** (e.g., lending flows include credit approval steps)
- **Archetype-specific attribute biases** (e.g., trading has higher mental_complexity at instrument selection)
- **Archetype-specific normalization** (e.g., lending flows synthesize KYC if missing)

The LLM automatically classifies the product and applies appropriate biases when extracting steps.

### Multi-Persona Extraction

The LLM ingestion extracts **2-4 distinct personas** per product by default:

- **Deduplication**: Removes redundant personas (same SEC + age + urban_rural + digital_skill + intent)
- **Target group prioritization**: If target group is inferred, personas matching it are prioritized
- **Distinctness requirement**: Each persona must differ meaningfully (different SEC, age, digital skill, or risk attitude)

### Step Normalization

After LLM extraction, steps are normalized:

- **Ordering**: Steps ordered from first touch to first value (landing → signup → kyc → payment → value)
- **Noise removal**: Low-value steps (scrolling, browsing) are filtered out
- **Count clamping**: Steps clamped to 3-10 (synthesize missing core steps if too few, trim if too many)
- **Name cleaning**: Consistent formatting
- **Archetype-specific synthesis**: Missing core steps (e.g., KYC for lending) are synthesized if archetype demands it

### When to Use LLM Ingestion

**Use when:**
- You have product descriptions but not structured personas/steps
- You want to quickly prototype scenarios from product docs
- You're exploring multiple product concepts
- You have OCR text from screenshots
- **You're a fintech team starting with `ingest-fintech` (recommended primary entry point)**

**Don't use when:**
- You already have structured personas/steps (use `simulate-lite` directly)
- You need precise control over scenario details
- You're doing production calibration (use manual scenarios)

---

## Wizard Mode: From Product URL + Screenshots to Behavioral Insights

### Overview

Wizard Mode is the **easiest entry point** for PMs to use DropSim. Instead of preparing structured product text, PMs can provide:
- Product URL (for reference)
- Screenshot texts (OCR'd from key screens)
- Product copy/PRD snippets
- Free-form persona and target group notes

The wizard automatically consolidates all inputs, extracts the scenario via LLM, and runs simulation.

### Input Format

**WizardInput Schema:**
```python
@dataclass
class WizardInput:
    product_url: str | None              # Optional URL (for reference)
    product_text: str | None              # Product copy, PRD, notes
    screenshot_texts: list[str] | None    # OCR'd text from key screens
    persona_notes: str | None             # Free-form notes on users
    target_group_notes: str | None       # ICP description
```

### Screenshot Text Preparation

PMs should prepare screenshot text files with screens separated by `---` or blank lines:

```
SCREENSHOT 1: Landing Page
Welcome to QuickCredit
[Get Started] button
---

SCREENSHOT 2: Phone Verification
Enter your mobile number
[Continue] button
---
```

The LLM prompt is explicitly screenshot-aware:
- **Prioritizes SCREENSHOT sections** when inferring step order
- **Maps screenshot labels/buttons** to step names
- **Uses screenshot sequence** to determine chronological order

### Context Consolidation

The wizard consolidates all inputs into a structured context:
- `## PRODUCT_URL` - Reference URL
- `## PRODUCT_TEXT` - Main description
- `## SCREENSHOT_1`, `## SCREENSHOT_2`, etc. - Screenshot texts
- `## PERSONA_NOTES` - Persona descriptions
- `## TARGET_GROUP_NOTES` - Target group description

This structured context is passed to the LLM for extraction.

### Confidence Estimation

The wizard estimates confidence level (high/medium/low) based on:
- Input richness (product text, screenshots, notes)
- Extraction quality (number of personas/steps extracted)
- Target group inference

### Usage

```bash
python dropsim_cli.py wizard-fintech \
  --product-url https://example.com \
  --product-text-file my_product_copy.txt \
  --screenshot-text-file my_screens.txt \
  --persona-notes-file my_personas.txt \
  --target-notes-file my_target.txt \
  --export-lite-scenario my_product_lite.json \
  --export my_product_traces.json
```

### Fallback Behavior

If inputs are sparse or ambiguous:
- LLM infers reasonable generic fintech onboarding for the identified archetype
- Uses common step patterns for that archetype
- Keeps personas and steps interpretable and realistic
- Better to return a complete, usable scenario than incomplete data

### Next Steps

After wizard run:
1. Review the generated LiteScenario JSON
2. Edit if needed (adjust personas, steps, attributes)
3. Re-run with `simulate-lite` for calibration and iteration

---

### Recommended Workflow for Fintech Teams

**For most fintech products, start with `wizard-fintech` or `ingest-fintech`:**

1. Paste product copy into a text file
2. Run `ingest-fintech` to extract scenario
3. Review inferred personas and steps
4. (Optional) Edit exported lite scenario JSON
5. Re-run with `simulate-lite` for calibration and iteration

### Behavior

- **No filter**: All personas simulated (default behavior)
- **Filter matches personas**: Only matching personas simulated
- **Filter matches none**: Warning message, empty results returned
- **Deterministic**: Same filter → same filtered set (no randomness)

This ensures consistency between CLI, API, and documentation.


# Behavioral State-Based Simulation Engine - Complete Implementation

## ✅ **ALL SPEC REQUIREMENTS IMPLEMENTED**

This engine implements the complete behavioral simulation framework as specified.

---

## 🎯 What This Engine Does

**Deterministic behavioral simulator that:**
1. Takes normalized persona inputs → compiles **latent priors** (CC, FR, RT, LAM, ET, TB, DR, CN, MS)
2. Runs priors through product steps to evolve **internal state** (energy, risk, effort, value, control)
3. Uses single inequality per step to decide **continue vs drop**
4. Identifies **dominant cost** label for "why here, why now"

**Answers "WHY they dropped at step t" before "WHO"**

---

## 📁 Files

| File | Purpose |
|------|---------|
| `behavioral_engine.py` | Core engine (3 layers: compiler, state engine, aggregation) |
| `behavioral_aggregator.py` | Output formatting, drill-down, JSON export |
| `run_behavioral_simulation.py` | CLI runner with all options |
| `IMPLEMENTATION_VERIFICATION.md` | Complete spec compliance checklist |

---

## 🚀 Quick Start

### Basic Run
```bash
python run_behavioral_simulation.py --n 100 --seed 42
```

**Output:**
```
Step: Landing Page
  Fails for: 162 of 700 state-variants (23.1%)
  Primary cost: System 2 fatigue (93.2% of failures)
  Secondary cost: Loss aversion (6.8% of failures)
```

### View Persona Trace
```bash
python run_behavioral_simulation.py --n 100 --trace 5 --variant tired_commuter
```

**Shows:**
- Full journey with state variables at each step
- Costs (cognitive, effort, risk)
- Decision (continue/drop)
- Failure reason if dropped

### Export for Data Science
```bash
python run_behavioral_simulation.py --n 100 --export traces.json --export-all-variants
```

**Exports:**
- JSON with all persona × state traces
- Machine-readable format
- Full priors, journey, outcomes

---

## 🧠 Behavioral Models

### 1. Cognitive Fatigue (System 2)
- **Formula:** `cognitive_demand × (1 + FR) × (1 - cognitive_energy)`
- **Model:** System 2 thinking depletes energy faster when already low

### 2. Prospect Theory (Risk & Loss Aversion)
- **Formula:** `risk_signal × LAM × (1 + irreversibility)`
- **Model:** Losses loom larger than gains (LAM amplifies)

### 3. Temporal Discounting (Value Decay)
- **Formula:** `explicit_value × exp(-DR × delay_to_value)`
- **Model:** Future value decays exponentially

### 4. Fogg Ability (Effort Tolerance)
- **Formula:** `effort_demand × (1 - ET)`
- **Model:** Lower ability = higher effort cost

---

## 📊 Output Format (Spec-Compliant)

### Primary Output (First UI Surface)
```
Step: Landing Page
  Fails for: 162 of 700 state-variants (23.1%)
  Primary cost: System 2 fatigue (93.2% of failures)
  Secondary cost: Loss aversion (6.8% of failures)
```

### Drill-Down (Persona × State Trace)
```
👤 PERSONA: 19yo Male from Gujarat
🎭 STATE VARIANT: tired_commuter

📊 JOURNEY:
  Landing Page:
    State: energy=0.29, risk=0.20, effort=0.30, value=0.36, control=0.25
    Costs: cognitive=0.142, effort=0.102, risk=0.173
    Decision: CONTINUE
  
  Quiz Start:
    State: energy=0.15, risk=0.35, effort=0.40, value=0.38, control=0.30
    Costs: cognitive=0.198, effort=0.153, risk=0.260
    Decision: DROP
    ❌ FAILURE REASON: System 2 fatigue
```

---

## ✅ Spec Compliance Checklist

- ✅ **Persona Compiler**: Normalize inputs → 9 latent priors
- ✅ **State Engine**: 5 state variables, 8 step fields, all cost/yield functions
- ✅ **Aggregation**: Failure rates, primary/secondary costs
- ✅ **State Variants**: 7 deterministic variants per persona
- ✅ **Output Format**: "Step t fails for X of Y" with cost labels
- ✅ **Drill-Down**: Persona × state trace viewing
- ✅ **JSON Export**: Machine-readable traces
- ✅ **Decision Rule**: Exact inequality implementation
- ✅ **Failure Reasons**: 40% threshold + 4 labels

---

## 🎯 Key Insights from Credigo.club Simulation

### Failure Mode Analysis (20 personas, 140 trajectories)

| Step | Failure Rate | Primary Reason |
|------|--------------|----------------|
| Landing Page | 44.3% | System 2 fatigue (95%) |
| Quiz Start | 29.3% | System 2 fatigue (95%) |
| Quiz Progression | 20.0% | System 2 fatigue (93%) |
| Post-Results | 6.4% | System 2 fatigue (100%) |

**Finding:** Product is **cognitively demanding** for the sample. Most failures are cognitive exhaustion, not effort or risk.

### Consistency Analysis
- Avg consistency: 0.49 (moderate)
- High consistency (>0.7): 2 personas
- **Interpretation:** Mixed - some structural flaws, some intent-sensitive

---

## 🔧 Next Steps (Hardening)

1. **Calibration Defaults**: Fintech vs edtech vs commerce presets
2. **Coefficient Learning**: Fit weights from real funnel data
3. **Visualization**: State collapse charts over steps
4. **A/B Testing**: Predict impact of reducing cognitive demand

---

## 📚 References

- **Prospect Theory**: Risk cost calculation
- **Fogg Behavior Model**: Effort tolerance
- **System 2 Thinking**: Cognitive fatigue
- **Temporal Discounting**: Value decay

---

## ✅ **VERIFICATION COMPLETE**

**All spec requirements are implemented and tested.**

---

## 🏦 FINTECH ONBOARDING DEMO

A complete, opinionated fintech onboarding scenario with default personas, product flow, and PM-friendly output.

### Quick Start

```bash
# Run the demo
python run_behavioral_simulation.py --fintech-demo

# View specific persona × variant trace
python run_behavioral_simulation.py --fintech-demo \
  --persona-name "Salaried_Tier2_Cautious" \
  --variant tired_commuter

# Export to JSON
python run_behavioral_simulation.py --fintech-demo --export fintech_demo.json
```

### Default Personas

1. **GenZ_UPI_Native_Metro** - Gen Z UPI-native, metro, low risk aversion
2. **Salaried_Tier2_Cautious** - Salaried worker, Tier-2, high family influence, cautious
3. **Self_Employed_Trader_HighRisk** - Self-employed trader, high risk tolerance, impatient
4. **Rural_First_Time_User** - Rural user, first-time fintech, high trust concerns
5. **Urban_Professional_Optimizer** - Urban professional, high digital literacy, value optimizer

### Fintech Onboarding Flow

1. **Landing Page** - Product explanation, value proposition
2. **Mobile + OTP** - Phone verification step
3. **KYC Document Upload** - Identity verification via documents
4. **PAN + Bank Linking** - Financial data linking (irreversible)
5. **Consent + Terms** - Legal consent and terms acceptance
6. **First Transaction** - First transaction / test transfer (value delivery)

### Example Output

```
[Fintech Onboarding Demo]

Step: Landing Page
  Fails for: 9 of 35 state-variants (25.7%)
  Primary cost: System 2 fatigue (100.0% of failures)
  Secondary cost: Multi-factor or None

Step: PAN + Bank Linking
  Fails for: 14 of 35 state-variants (40.0%)
  Primary cost: Loss aversion (100.0% of failures)
  Secondary cost: Multi-factor or None
```

**Key Finding:** PAN + Bank Linking is the biggest drop-off point (40% failure rate) due to loss aversion - the irreversible financial data sharing step.

### Persona × Variant Trace Example

```
📋 FINTECH DEMO: Salaried_Tier2_Cautious × tired_commuter

👤 Salaried worker, Tier-2, high family influence, cautious
🎭 Tired, lower energy

📊 JOURNEY:
  Step 1: Landing Page ❌ DROP
    State: value=0.29, risk=0.38, effort=0.30, control=0.43, energy=0.03
    ❌ FAILURE: System 2 fatigue
    Costs: cognitive=0.220, effort=0.000, risk=0.176
```

### Fintech Onboarding Demo: JSON Schema

When exporting with `--export`, the JSON structure is:

```json
{
  "metadata": {
    "scenario": "fintech_onboarding_demo",
    "personas": 5,
    "state_variants": 7,
    "product_steps": 6,
    "total_trajectories": 35
  },
  "personas": [
    {
      "name": "GenZ_UPI_Native_Metro",
      "description": "...",
      "raw_fields": { "SEC": 0.6, "DigitalLiteracy": 0.9, ... },
      "compiled_priors": { "CC": 0.88, "FR": 0.1, ... }
    }
  ],
  "state_variants": { ... },
  "product_steps": { ... },
  "trajectories": [
    {
      "persona_name": "GenZ_UPI_Native_Metro",
      "variant": "fresh_motivated",
      "exit_step": "PAN + Bank Linking",
      "failure_reason": "Loss aversion",
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
            "total_cost": 0.166
          },
          "dropped": false
        }
      ]
    }
  ]
}
```

This schema is machine-readable for data science teams to analyze failure patterns, state trajectories, and cost breakdowns.

---

This is **no longer philosophy. This is the engine.** 🚀


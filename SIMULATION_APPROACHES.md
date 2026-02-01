# Credigo.club Audience Simulation - Three Approaches

## Overview

We've built **three complementary simulation engines** for predicting Indian audience reactions to Credigo.club:

1. **Rule-Based Engine** (Fast, Deterministic)
2. **LLM-Powered Engine** (Intelligent, Contextual)
3. **Behavioral State Engine** (Cognitive, Scientific)

---

## 1. Rule-Based Engine (`journey_simulator.py`)

### Approach
- Deterministic rules based on derived features
- Intent scores (0-100) calculated per step
- Fast: 1000 personas in ~16 seconds

### Strengths
- Fast iteration
- Reproducible (seed-based)
- Good for quick insights

### Limitations
- Less nuanced than LLM
- Doesn't model cognitive fatigue

### Usage
```bash
python run_simulation.py --n 1000 --seed 42
```

### Output
- Funnel tables (% reaching each step)
- Segment performance
- Top refusals
- Vivid reactions

---

## 2. LLM-Powered Engine (`llm_simulator.py`)

### Approach
- Uses GPT-4o-mini to generate contextual predictions
- Understands persona background and generates authentic Indian quotes
- ~$0.002 per persona

### Strengths
- Highly realistic reactions
- Authentic Hinglish quotes
- Discovers nuanced refusal patterns
- Context-aware

### Limitations
- Slower (API calls)
- Costs money
- Less deterministic

### Usage
```bash
export OPENAI_API_KEY="your-key"
python run_llm_simulation.py --n 20
```

### Output
- Intelligent journey predictions
- Culturally-authentic quotes
- LLM-generated segments
- Rich context

---

## 3. Behavioral State Engine (`behavioral_engine.py`) ⭐ **NEW**

### Approach
- **Cognitive state-based modeling**
- Tracks: cognitive energy, perceived risk/effort/value/control
- **One persona, multiple state trajectories** (not Monte Carlo)
- Deterministic, explainable
- Answers **"WHY they dropped"** before "WHO"

### Core Framework

#### Raw Inputs → Latent Priors
- **Cognitive Capacity (CC)**: Mental endurance
- **Fatigue Rate (FR)**: How fast energy drains
- **Risk Tolerance (RT)**: Financial/data risk comfort
- **Loss Aversion Multiplier (LAM)**: Amplifies perceived risk
- **Effort Tolerance (ET)**: Forms/OTPs tolerance
- **Trust Baseline (TB)**: Initial system trust
- **Temporal Discount Rate (DR)**: Future value decay
- **Control Need (CN)**: Need for reassurance

#### Internal State Variables
- `cognitive_energy`: 0 to CC
- `perceived_risk`: 0 to 3.0
- `perceived_effort`: 0 to 3.0
- `perceived_value`: 0 to 3.0
- `perceived_control`: 0 to 2.0

#### State Variants (Structured, Deterministic)
Each persona simulated across 7 variants:
- `fresh_motivated`: High energy, high value
- `tired_commuter`: Low energy, moderate value
- `distrustful_arrival`: High risk perception
- `browsing_casually`: Low urgency
- `urgent_need`: High motivation
- `price_sensitive`: Low value perception
- `tech_savvy_optimistic`: High digital comfort

#### Decision Rule
**CONTINUE if:**
```
(perceived_value × MS + perceived_control) > (perceived_risk + perceived_effort)
```

#### Failure Reasons
- **System 2 fatigue**: Cognitive overload
- **Low ability**: Effort too high
- **Loss aversion**: Risk too high
- **Temporal discounting**: Value too delayed

### Strengths
- ✅ **Scientifically grounded** (Prospect Theory, Fogg, System 2)
- ✅ **Deterministic** (no randomness)
- ✅ **Explainable** (shows WHY, not just percentages)
- ✅ **VC-defensible** (behavioral models)
- ✅ **Engineer-buildable** (clear equations)

### Usage
```bash
python run_behavioral_simulation.py --n 100 --seed 42
```

### Output
- **Failure Mode Analysis**: Why each step fails
- **Primary/Secondary Reasons**: Cognitive vs. effort vs. risk
- **Consistency Scores**: How many variants fail at same step
- **State Trajectories**: Full cognitive journey per variant

### Example Output
```
Step: Post-Results
Failure Rate: 6.6%
Primary Reason: System 2 fatigue (23 failures)
Secondary Reason: None

Interpretation: 
- Most variants complete the funnel
- When they fail, it's cognitive exhaustion
- Not effort or risk - the step is cognitively demanding
```

---

## When to Use Which

### Rule-Based
- ✅ Quick iteration
- ✅ Large samples (1000+)
- ✅ Initial exploration
- ✅ When cost/speed matters

### LLM-Powered
- ✅ Need authentic quotes
- ✅ Small samples (20-50)
- ✅ Founder presentations
- ✅ When context matters

### Behavioral State ⭐
- ✅ **Product optimization** (identify cognitive bottlenecks)
- ✅ **VC pitches** (scientifically grounded)
- ✅ **Engineering specs** (clear failure modes)
- ✅ **A/B testing** (predict which changes help)

---

## Key Insights from Behavioral Engine

### Failure Mode Analysis (50 personas, 350 trajectories)

| Step | Failure Rate | Primary Reason |
|------|--------------|----------------|
| Landing Page | 46.3% | System 2 fatigue |
| Quiz Start | 29.1% | System 2 fatigue |
| Quiz Progression | 16.3% | System 2 fatigue |
| Post-Results | 6.6% | System 2 fatigue |

**Finding**: The product is **cognitively demanding** for the sample (rural-heavy, low digital literacy). Most failures are cognitive exhaustion, not effort or risk.

### Consistency Analysis
- Avg consistency: 0.51 (moderate)
- High consistency (>0.7): 5 personas
- Low consistency (<0.4): 1 persona

**Interpretation**: 
- High consistency → Structural product flaw (same step fails across variants)
- Low consistency → Intent-sensitive (depends on arrival state)

---

## Next Steps

1. **Calibrate Product Steps**: Adjust `cognitive_demand` in `PRODUCT_STEPS` based on real data
2. **Add More Variants**: Expand state variants for edge cases
3. **Visualize State Collapse**: Show cognitive energy decay across steps
4. **A/B Testing**: Predict impact of reducing cognitive demand

---

## Files

- `behavioral_engine.py` - Core behavioral simulation
- `run_behavioral_simulation.py` - Runner script
- `journey_simulator.py` - Rule-based engine
- `llm_simulator.py` - LLM-powered engine
- `derive_features.py` - Feature derivation
- `load_dataset.py` - Data loading

---

## References

- **Prospect Theory**: Risk cost calculation
- **Fogg Behavior Model**: Effort tolerance
- **System 2 Thinking**: Cognitive fatigue
- **Temporal Discounting**: Value decay

This is **no longer philosophy. This is the engine.** 🚀


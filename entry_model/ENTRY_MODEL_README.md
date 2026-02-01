# Entry Model - Pre-Behavioral Entry Layer

## 🎯 Purpose

The entry model separates **entry probability** from **in-funnel behavioral completion**. This allows the system to correctly model the full funnel:

```
Total Conversion = P(entry) × P(completion | entry)
```

Where:
- **P(entry)** = Probability user enters the behavioral funnel (this module)
- **P(completion | entry)** = Probability user completes given they entered (behavioral engine)

## 📊 Why Separate Entry from Completion?

### The Problem
Traditional behavioral models only answer: "Of those who start, how many finish?"

But they don't answer: "Of everyone who could arrive, how many even start?"

### The Solution
By separating entry from completion, we can now answer:
- **Entry Model:** "Who starts?" (pre-behavioral decision)
- **Behavioral Engine:** "Who finishes?" (in-funnel behavior)
- **Full Funnel:** "Total conversion rate"

## 🏗️ Architecture

```
┌─────────────────┐
│  Traffic Source │
│  Intent Signals │  ──→  Entry Model  ──→  P(entry)
│  Landing Page   │
└─────────────────┘

┌─────────────────┐
│  User Enters    │  ──→  Behavioral Engine  ──→  P(completion | entry)
│  Funnel         │
└─────────────────┘

P(entry) × P(completion | entry) = Total Conversion
```

## 📦 Module Structure

```
entry_model/
├── entry_signals.py      # Extract entry-level signals
├── entry_model.py        # Compute P(entry | signals)
├── entry_calibration.py  # Calibrate model parameters
├── funnel_integration.py # Integrate with behavioral engine
└── test_entry_model.py   # Validation tests
```

## 🔧 Entry Model Inputs

The entry model uses **coarse, high-level signals** only:

### Required Signals
- **Traffic Source:** ads, SEO, referral, direct, social, email
- **Intent Strength:** high, medium, low (from intent inference)
- **Landing Page Promise Strength:** 0-1 (how strong is the value promise)

### Optional Signals
- **Brand Trust Proxy:** 0-1 (brand awareness/trust)
- **Device Type:** mobile, desktop, tablet
- **Platform:** web, app
- **Market Maturity:** early, mature, saturated

### ⚠️ Important Constraint
**This layer does NOT use behavioral signals** like:
- Cognitive load
- Friction
- Effort demand
- Risk signals

These are only relevant **after** entry.

## 📈 Entry Model Output

```python
{
  "entry_probability": 0.32,  # P(entry)
  "confidence": 0.78,          # Confidence in estimate
  "drivers": {
    "intent_match": 0.45,      # Contribution of intent
    "source_quality": 0.30,    # Contribution of traffic source
    "message_alignment": 0.25  # Contribution of landing page promise
  }
}
```

## 🚀 Usage

### Basic Usage

```python
from entry_model import estimate_entry_probability

# Estimate entry probability
result = estimate_entry_probability(
    referrer='direct',
    intent_frame={'commitment_threshold': 0.7, 'tolerance_for_effort': 0.6},
    landing_page_text='Find the Best Credit Card In 60 seconds - No PAN required',
    cta_text='Get Started Now'
)

print(f"Entry probability: {result.entry_probability:.2%}")
print(f"Confidence: {result.confidence:.2%}")
print(f"Primary driver: {max(result.drivers.items(), key=lambda x: x[1])[0]}")
```

### Full Funnel Integration

```python
from entry_model.funnel_integration import compute_full_funnel_prediction

# Entry signals
entry_signals = {
    'referrer': 'direct',
    'intent_frame': {'commitment_threshold': 0.7},
    'landing_page_text': 'Find the Best Credit Card In 60 seconds'
}

# Behavioral completion rate (from behavioral engine)
behavioral_completion_rate = 0.77

# Compute full funnel prediction
prediction = compute_full_funnel_prediction(
    entry_signals=entry_signals,
    behavioral_completion_rate=behavioral_completion_rate
)

print(f"Entry probability: {prediction.entry_probability:.2%}")
print(f"Completion probability: {prediction.completion_probability:.2%}")
print(f"Total conversion: {prediction.total_conversion:.2%}")
# Output: Entry: 55.50%, Completion: 77.00%, Total: 42.74%
```

### Export Results

```python
from entry_model.funnel_integration import (
    export_entry_probability,
    export_entry_diagnostics,
    export_full_funnel_prediction
)

# Export entry probability
export_entry_probability(result, 'entry_probability.json')

# Export diagnostics
export_entry_diagnostics(result, 'entry_diagnostics.json')

# Export full funnel prediction
export_full_funnel_prediction(prediction, 'full_funnel_prediction.json')
```

## 🎛️ Base Entry Probabilities

Default entry probabilities by traffic source:

- **Direct:** 50% (highest intent)
- **Referral:** 40% (high trust)
- **SEO:** 35% (organic search, good intent)
- **Email:** 30% (medium intent)
- **Ads:** 15% (lower intent, higher bounce)
- **Social:** 12% (low intent, exploratory)
- **Unknown:** 25% (default)

These are then adjusted by:
- Intent strength multiplier (high: +40%, low: -30%)
- Promise strength multiplier (strong: +30%, weak: -30%)
- Brand trust multiplier (high: +20%, low: -10%)

## ✅ Guardrails

1. **Probability Bounds:** Entry probability ∈ [0.01, 0.95]
2. **No Behavioral Signals:** Only uses pre-behavioral signals
3. **Explainable:** No black-box ML, all factors are interpretable
4. **Independent:** Entry model doesn't depend on downstream behavior

## 🧪 Validation Tests

Run tests to validate entry model:

```bash
python3 -m entry_model.test_entry_model
```

Tests validate:
- ✅ High-intent traffic → high entry probability
- ✅ Low-intent traffic → low entry probability
- ✅ Entry probabilities within bounds [0.01, 0.95]
- ✅ Full funnel integration: entry × completion = total conversion
- ✅ Traffic source ranking (direct > SEO > social)

## 📊 Calibration

Calibrate entry model with observed entry rates:

```python
from entry_model.entry_calibration import (
    ObservedEntryData,
    calibrate_entry_model
)

# Observed data
observed_data = [
    ObservedEntryData(
        traffic_source=TrafficSource.DIRECT,
        intent_strength=IntentStrength.HIGH,
        landing_page_promise_strength=0.8,
        observed_entry_rate=0.55,
        sample_size=1000
    ),
    # ... more data points
]

# Calibrate
calibration = calibrate_entry_model(observed_data)
print(f"Fit score: {calibration.fit_score:.4f}")
print(f"Calibrated weights: {calibration.calibrated_weights}")
```

## 📈 Output Artifacts

### `entry_probability.json`
Entry probability result with confidence and drivers.

### `entry_diagnostics.json`
Detailed diagnostics including signal interpretation and primary drivers.

### `full_funnel_prediction.json`
Complete funnel prediction combining entry and completion:
```json
{
  "entry_probability": 0.555,
  "completion_probability": 0.77,
  "total_conversion": 0.427,
  "breakdown": {
    "visitors": 1000,
    "entries": 555,
    "completions": 427
  }
}
```

## 🎯 Key Insights

### What Entry Model Answers
- "Of everyone who could arrive, how many do arrive?"
- "Which traffic sources have highest entry rates?"
- "How does landing page promise affect entry?"
- "What's the impact of intent strength on entry?"

### What Behavioral Engine Answers
- "Of those who enter, how many finish?"
- "Where do users drop off in the funnel?"
- "What causes drop-offs (fatigue, friction, risk)?"

### What Full Funnel Answers
- "Total conversion rate = entry × completion"
- "Full funnel optimization opportunities"
- "End-to-end user journey modeling"

## 💡 Example: Credigo Flow

```python
# High-intent direct traffic
entry_result = estimate_entry_probability(
    referrer='direct',
    intent_frame={'commitment_threshold': 0.7},
    landing_page_text='Find the Best Credit Card In 60 seconds - No PAN required'
)
# Entry probability: ~55%

# Behavioral completion (from engine)
completion_rate = 0.77  # 77% completion

# Total conversion
total_conversion = 0.55 * 0.77 = 0.4235  # 42.35%
```

This means: **Of 1000 visitors, 550 enter, and 424 complete** (42.4% total conversion).

## 🔄 Integration with Existing System

The entry model integrates seamlessly:

1. **Extract entry signals** from traffic/context
2. **Compute entry probability** using entry model
3. **Run behavioral simulation** (existing engine) to get completion rate
4. **Combine:** Total conversion = entry × completion
5. **Export** full funnel predictions

No changes to existing behavioral engine - entry model is additive.

---

**This transforms your engine from a behavior simulator into a full-funnel predictive system.**


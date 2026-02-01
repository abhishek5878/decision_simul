# Pre-Analytics Data Requirements & Sources

## 📋 Required Data Types

### 1. Product Steps Definition

**What:** Complete onboarding flow with step attributes

**Required Fields per Step:**
- `step_name`: Step identifier (e.g., "Welcome & Personalization")
- `description`: Detailed step description (UI elements, actions, context)
- `cognitive_demand`: 0.0-1.0 (mental load required)
- `effort_demand`: 0.0-1.0 (physical/time effort)
- `risk_signal`: 0.0-1.0 (perceived risk)
- `irreversibility`: 0.0-1.0 (commitment level)
- `delay_to_value`: Integer (steps until value shown)
- `explicit_value`: 0.0-1.0 (value clarity at this step)
- `reassurance_signal`: 0.0-1.0 (trust signals present)
- `authority_signal`: 0.0-1.0 (credibility signals)

**Sources:**
- Product screenshots (analyzed via LLM)
- Product documentation
- User flow diagrams
- Manual definition by PM/UX team

**Example:**
```python
{
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

### 2. Persona Database

**What:** Realistic user personas with behavioral attributes

**Required Fields:**
- Demographics: age, location, employment_type, education
- Behavioral: cognitive_capacity, risk_tolerance, effort_tolerance
- Psychographics: intent, urgency, digital_skill
- Derived: 9 latent priors (CC, FR, RT, LAM, ET, TB, DR, CN, MS)

**Sources:**
- **Primary:** NVIDIA Nemotron-Personas-India (3M personas)
  - Hugging Face: `nvidia/Nemotron-Personas-India`
  - Language: `en_IN` (English India)
  - 28 fields per persona
- **Fallback:** Generated personas (if database unavailable)

**Loading:**
```python
from load_dataset import load_and_sample

df, derived = load_and_sample(
    n=1000,
    seed=42,
    language="en_IN",
    use_huggingface=True
)
```

---

### 3. Target Group Filters

**What:** Criteria to filter personas for product target audience

**Required Fields:**
- `age_bucket`: ["young", "middle", "senior"]
- `urban_rural`: ["rural", "tier2", "metro"]
- `digital_skill`: ["low", "medium", "high"]
- `intent`: ["low", "medium", "high"]
- `sec`: ["low", "mid", "high"] (optional)
- `risk_attitude`: ["risk_averse", "balanced", "risk_tolerant"] (optional)

**Sources:**
- Product target persona definition
- Market research
- User interviews
- Product team input

**Example:**
```python
target_group = TargetGroup(
    age_bucket=["young", "middle"],  # 22-35
    urban_rural=["metro", "tier2"],  # Tier-1 cities
    digital_skill=["medium", "high"],
    intent=["medium", "high"]
)
```

---

### 4. Product Context (Optional but Recommended)

**What:** Additional product information for richer inferences

**Required Fields:**
- Company name, description
- Value proposition
- Target market
- Competitive landscape
- Product features

**Sources:**
- Product documentation
- Website/marketing materials
- Founder/product team input

**Example:**
```python
product_context = {
    "company": {
        "name": "CirclePe",
        "description": "Zero security deposit rental platform..."
    },
    "targetMarkets": {...},
    "competitiveLandscape": [...]
}
```

---

### 5. Intent Distribution (Optional)

**What:** User intent probabilities for intent-aware modeling

**Required Fields:**
- Intent IDs with probabilities (must sum to 1.0)

**Sources:**
- **Auto-inferred:** From product entry point text (via LLM)
- **Manual:** Product team definition
- **Default:** Generic distribution if unavailable

**Example:**
```python
intent_distribution = {
    'zero_deposit_rental': 0.4,
    'quick_move_in': 0.3,
    'cash_flow_relief': 0.2,
    'hassle_free_renting': 0.1
}
```

---

## 🔄 Data Flow

```
1. Product Steps
   └─> Defined manually or extracted from screenshots
   └─> Stored in: circlepe_steps.py, blink_money_steps.py

2. Persona Database
   └─> Loaded from NVIDIA database (Hugging Face)
   └─> Filtered by TargetGroup
   └─> Derived features computed

3. Target Group
   └─> Defined based on product target persona
   └─> Applied during persona loading

4. Product Context
   └─> Added to result generator
   └─> Enhances inferences and recommendations

5. Intent Distribution
   └─> Inferred from product entry point
   └─> Used in intent-aware simulation
```

---

## 📊 Minimum Required Data

**To run simulation, you need:**
1. ✅ Product steps definition (at least 3 steps)
2. ✅ Persona database access (or generated personas)
3. ✅ Target group filters (or use all personas)

**Optional but improves results:**
4. Product context
5. Intent distribution (auto-inferred if not provided)
6. Screenshots (for LLM-enhanced inferences)

---

## 🎯 Data Quality Requirements

### Product Steps
- **Completeness:** All steps in chronological order
- **Accuracy:** Attributes reflect actual user experience
- **Consistency:** Same scale (0.0-1.0) across all steps

### Personas
- **Diversity:** Representative of target audience
- **Volume:** Minimum 100 personas (recommended 1000+)
- **Quality:** Realistic behavioral attributes

### Target Group
- **Specificity:** Matches product target audience
- **Feasibility:** Filters should match available persona data

---

## 📁 Data Storage

**Product Steps:**
- Python files: `circlepe_steps.py`, `blink_money_steps.py`
- JSON files: `product_steps.json` (alternative)

**Personas:**
- Loaded on-demand from Hugging Face
- Cached locally in: `./nemotron_personas_india_data/data/`

**Results:**
- JSON: `{PRODUCT}_DECISION_AUTOPSY_RESULT.json`
- PDF: `{product}_context_graph.pdf`

---

## 🔧 Data Preparation Checklist

- [ ] Define product steps with all 9 attributes
- [ ] Verify step descriptions are detailed and accurate
- [ ] Set up NVIDIA database access (Hugging Face)
- [ ] Define target group filters
- [ ] (Optional) Add product context
- [ ] (Optional) Provide intent distribution or let it auto-infer
- [ ] (Optional) Prepare screenshots for LLM analysis

---

**Last Updated:** January 14, 2026

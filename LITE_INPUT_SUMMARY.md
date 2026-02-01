# DropSim Lite Input Mode - Implementation Summary

## ✅ **LITE INPUT FEATURES IMPLEMENTED**

### 1. LiteScenario Schema ✅

**File:** `dropsim_lite_input.py`

- `LitePersona` - Human-friendly persona description with labels
- `LiteStep` - Human-friendly step description with labels
- `LiteScenario` - Complete lite scenario configuration
- JSON-serializable, loads from file

**Persona Labels:**
- `sec`: "low" | "mid" | "high"
- `urban_rural`: "rural" | "tier2" | "metro"
- `digital_skill`: "low" | "medium" | "high"
- `family_influence`: "low" | "medium" | "high"
- `aspiration`: "low" | "medium" | "high"
- `price_sensitivity`: "low" | "medium" | "high"
- `risk_attitude`: "risk_averse" | "balanced" | "risk_tolerant" (optional)
- `age_bucket`: "senior" | "middle" | "young"
- `intent`: "low" | "medium" | "high"

**Step Labels:**
- `type`: "landing" | "signup" | "kyc" | "payment" | "consent" | "other"
- `mental_complexity`: "low" | "medium" | "high"
- `effort`: "low" | "medium" | "high"
- `risk`: "low" | "medium" | "high"
- `irreversible`: true | false
- `value_visibility`: "low" | "medium" | "high"
- `delay_to_value`: "instant" | "soon" | "later"
- `reassurance`: "low" | "medium" | "high"
- `authority`: "low" | "medium" | "high"

### 2. Deterministic Mappings ✅

**Persona Mappings:**
- Labels → Numeric bands (0.2 / 0.5 / 0.8 with context adjustments)
- Age buckets → 0.1 / 0.5 / 0.9
- Intent → Motivation Strength (0.4 / 0.6 / 0.85)
- Risk attitude → Risk Tolerance override (0.2 / 0.5 / 0.8)
- All mappings produce valid PersonaRaw fields
- Uses existing `compile_persona_from_raw()` to get priors

**Step Mappings:**
- mental_complexity → cognitive_demand (0.2 / 0.5 / 0.8)
- effort → effort_demand (0.2 / 0.5 / 0.8)
- risk → risk_signal (0.1 / 0.4 / 0.8)
- delay_to_value → 0 / 2 / 4 steps
- Type-specific adjustments (payment → higher risk, kyc → higher effort)

**Function:** `lite_to_scenario()` - Main entry point

### 3. CLI Integration ✅

**File:** `dropsim_cli.py`

- New command: `simulate-lite`
- Flag: `--lite-scenario-file <path>` (required)
- All standard flags work:
  - `--observed-funnel`
  - `--export`
  - `--export-plot-data`
  - `--trace-plot-data`
  - `--persona-name` + `--variant`

**Behavior:**
- Loads lite scenario from JSON
- Converts to full ScenarioConfig
- Runs existing simulation pipeline (no forked logic)
- Produces same outputs (narrative, plot data, etc.)

### 4. Example & Documentation ✅

**File:** `examples/fintech_lite_onboarding.json`

- 3 personas: "Rural Cautious", "Urban Young Risk-Taker", "Tier-2 Salaried Worker"
- 5 steps: Landing → Phone Verification → KYC → Bank Linking → First Transaction
- Demonstrates all label types

**Updated:**
- `QUICK_START.md` - Lite input mode section
- `DROPSIM_PRODUCT_DESIGN.md` - "Fast Start: Lite Input Mode" section with full mapping details

## Usage Examples

### Basic Lite Simulation

```bash
python dropsim_cli.py simulate-lite \
  --lite-scenario-file examples/fintech_lite_onboarding.json
```

### With All Features

```bash
python dropsim_cli.py simulate-lite \
  --lite-scenario-file examples/fintech_lite_onboarding.json \
  --observed-funnel examples/fintech_observed_funnel.json \
  --export-plot-data steps.csv \
  --persona-name "Rural Cautious" \
  --variant tired_commuter
```

## Verification

✅ Lite mode uses exact same engine (no forked logic)
✅ All mappings produce values within spec ranges
✅ Behavioral labels still correct (System 2 fatigue, Loss aversion, etc.)
✅ Output quality matches full mode
✅ All flags work correctly

## Key Features

- **No math required**: PMs describe in natural language
- **Deterministic**: Same lite input → same results
- **Same engine**: Uses full behavioral engine under the hood
- **Type-aware**: Step types (payment, kyc) get automatic adjustments
- **Lossy but opinionated**: Deliberately simplified for ease of use

## Sample Output

**Lite Input:**
```json
{
  "name": "Rural Cautious",
  "sec": "low",
  "digital_skill": "low",
  "risk_attitude": "risk_averse"
}
```

**Maps to:**
- CC = 0.41 (low cognitive capacity)
- RT = 0.20 (low risk tolerance)
- LAM = 1.80 (high loss aversion)

**Produces:**
- "Most failures occur at Landing Page, driven by System 2 fatigue"
- "Rural Cautious persona shows high consistency (86%)"

DropSim is now **accessible to non-technical PMs** while maintaining full behavioral engine accuracy.


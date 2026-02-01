# DropSim Quick Start

## Installation

```bash
pip install -r requirements.txt
```

## CLI Usage

### Run Fintech Preset

```bash
python dropsim_cli.py simulate --preset fintech
```

### Run Custom Scenario

```bash
python dropsim_cli.py simulate --scenario-file examples/fintech_onboarding.json
python dropsim_cli.py simulate --scenario-file examples/edtech_onboarding.json
```

### View Specific Trace

```bash
python dropsim_cli.py simulate --preset fintech \
  --persona-name "Salaried_Tier2_Cautious" \
  --variant tired_commuter
```

### Export to JSON

```bash
python dropsim_cli.py simulate --preset fintech --export traces.json
```

## API Usage

### Start Server

```bash
uvicorn dropsim_api:app --reload
```

### Run Simulation

```bash
curl -X POST http://localhost:8000/simulate \
  -H "Content-Type: application/json" \
  -d @examples/fintech_onboarding.json
```

### Include Traces

```bash
curl -X POST "http://localhost:8000/simulate?include_traces=true" \
  -H "Content-Type: application/json" \
  -d @examples/fintech_onboarding.json
```

## Output Language

All outputs use consistent design doc language:
- **System 2 fatigue** (cognitive cost)
- **Loss aversion** (risk cost)
- **Temporal discounting** (value decay)
- **Low ability** (effort cost)

## Calibration with Real Funnel Data

### Run with Observed Funnel

```bash
python dropsim_cli.py simulate --preset fintech \
  --observed-funnel examples/fintech_observed_funnel.json
```

**Output includes:**
- Step-by-step comparison (predicted vs observed)
- Underestimate/overestimate flags
- Model tuning suggestions

### Observed Funnel JSON Format

```json
{
  "total_users": 1000,
  "steps": [
    {
      "step_name": "Landing Page",
      "users_entered": 1000,
      "users_dropped": 280,
      "segment": "all"
    }
  ]
}
```

## Visualization Data Export

### Export Step-Level Data

```bash
python dropsim_cli.py simulate --preset fintech \
  --observed-funnel examples/fintech_observed_funnel.json \
  --export-plot-data fintech_steps.csv
```

**Output:** CSV/JSON with predicted/observed failure rates, costs, deltas

**Use for:** Plotting predicted vs observed by step, identifying calibration gaps

### Export Trajectory Data

```bash
python dropsim_cli.py simulate --preset fintech \
  --persona-name "Urban_Professional_Optimizer" \
  --variant tired_commuter \
  --trace-plot-data trajectory.csv
```

**Output:** CSV/JSON with state variables (energy, value, risk, effort, control) over steps

**Use for:** Plotting state evolution, identifying drop point, visualizing cost accumulation

## Lite Input Mode (No Math Required)

### Quick Start with Human-Friendly Labels

Instead of specifying raw numeric values, use simple labels (low/medium/high):

```bash
python dropsim_cli.py simulate-lite \
  --lite-scenario-file examples/fintech_lite_onboarding.json
```

**Lite Scenario Format:**
```json
{
  "product_type": "fintech",
  "personas": [
    {
      "name": "Rural Cautious",
      "sec": "low",
      "urban_rural": "rural",
      "digital_skill": "low",
      "family_influence": "high",
      "aspiration": "low",
      "price_sensitivity": "high",
      "risk_attitude": "risk_averse",
      "age_bucket": "middle",
      "intent": "low"
    }
  ],
  "steps": [
    {
      "name": "Landing Page",
      "type": "landing",
      "mental_complexity": "low",
      "effort": "low",
      "risk": "low",
      "irreversible": false,
      "value_visibility": "medium",
      "delay_to_value": "later",
      "reassurance": "medium",
      "authority": "low"
    }
  ]
}
```

**Labels automatically map to behavioral engine:**
- `"high risk"` → higher `risk_signal`, more loss aversion impact
- `"high mental_complexity"` → higher `cognitive_demand`, more System 2 fatigue
- `"high effort"` → higher `effort_demand`, more low ability failures
- `"irreversible: true"` → amplifies risk perception

See `DROPSIM_PRODUCT_DESIGN.md` for full mapping details.

## Target-Group Filtering

### Filter Personas by Target Group

Focus simulation on specific segments to reduce computation and noise:

```bash
python dropsim_cli.py simulate --preset fintech \
  --target-group examples/fintech_target_group_young_urban_risk_tolerant.json

python dropsim_cli.py simulate-lite \
  --lite-scenario-file examples/fintech_lite_onboarding.json \
  --target-group examples/fintech_target_group_young_urban_risk_tolerant.json
```

**Target Group JSON Format:**
```json
{
  "urban_rural": ["metro"],
  "age_bucket": ["young"],
  "risk_attitude": ["balanced", "risk_tolerant"],
  "intent": ["medium", "high"]
}
```

**All fields optional** - only specified filters are applied.

**Output:** DropSim only simulates personas matching the filters, reducing computation and focusing on your target audience.

## Wizard Mode: From Product URL + Screenshots to Behavioral Insights

**The easiest way to get started with DropSim - just provide your product info and get insights automatically.**

### Recommended Workflow

1. **Collect your inputs:**
   - 3-6 key screenshots (OCR'd into text)
   - A short product copy block or PRD snippet
   - A short paragraph describing your ICP (Ideal Customer Profile)

2. **Save them into text files:**
   - `my_product_copy.txt` - Product description
   - `my_screens.txt` - Screenshot texts (separated by `---` or blank lines)
   - `my_personas.txt` - Persona notes (optional but recommended)
   - `my_target.txt` - Target group notes (optional but recommended)

3. **Run the wizard:**
   ```bash
   python dropsim_cli.py wizard-fintech \
     --product-text-file my_product_copy.txt \
     --screenshot-text-file my_screens.txt \
     --persona-notes-file my_personas.txt \
     --target-notes-file my_target.txt \
     --export-lite-scenario my_product_lite.json \
     --export my_product_traces.json
   ```

4. **Read the results:**
   - Step-level failure rates and behavioral costs
   - Narrative summary with key insights
   - Generated LiteScenario JSON for editing/re-running

### Screenshot Text Format

When preparing screenshot text files, separate each screen with `---` or blank lines:

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

### What Happens Under the Hood

The wizard uses the same deterministic behavioral engine:
- Persona priors (CC, FR, RT, LAM, ET, TB, DR, CN, MS)
- Single inequality decision rule
- Behavioral cost labels (System 2 fatigue, Loss aversion, Low ability, Temporal discounting)

The wizard just makes it easier to get started - no schema knowledge required!

---

## Fast Start for Fintech Teams

**For most fintech products (payments, lending, trading, insurance, PFM), start with `wizard-fintech` or `ingest-fintech` instead of hand-writing scenarios.**

### Step 1: Prepare Product Description

Paste your product copy into a text file (or use `examples/sample_fintech_product_text.txt` as a template). Include:
- Product description and value proposition
- Target users (age, location, income, digital comfort)
- Onboarding flow steps (from landing to first value)

### Step 2: Run LLM Ingestion

```bash
export OPENAI_API_KEY=your_api_key_here

python dropsim_cli.py ingest-fintech \
  --product-text-file my_product_copy.txt \
  --export-lite-scenario my_product_lite_scenario.json \
  --export my_product_traces.json
```

**What happens:**
- LLM extracts 2-4 distinct personas
- LLM extracts 4-8 onboarding steps
- LLM identifies target group filters
- DropSim runs simulation automatically
- Results show step failure rates and behavioral costs

### Step 3: (Optional) Edit and Re-run

If you want to refine the inferred scenario:

1. Edit `my_product_lite_scenario.json` (adjust personas, steps, attributes)
2. Re-run with `simulate-lite`:

```bash
python dropsim_cli.py simulate-lite \
  --lite-scenario-file my_product_lite_scenario.json \
  --target-group my_target_group.json \
  --observed-funnel my_observed_funnel.json
```

### Step 4: Iterate with Calibration

Add your real funnel data to compare predictions:

```bash
python dropsim_cli.py ingest-fintech \
  --product-text-file my_product_copy.txt \
  --observed-funnel my_observed_funnel.json \
  --export-plot-data steps.csv
```

---

## LLM-Assisted Ingestion (From Product Text to Simulation)

### Extract Scenario from Product Description

Automatically generate a DropSim scenario from product text using LLM:

```bash
export OPENAI_API_KEY=your_api_key_here

python dropsim_cli.py ingest-fintech \
  --product-text-file examples/sample_fintech_product_text.txt \
  --export-lite-scenario examples/generated_fintech_lite_scenario.json
```

**What it does:**
- LLM extracts personas, steps, and target group from product description
- Converts to LiteScenario + TargetGroup
- Runs simulation automatically
- Optionally exports the inferred scenario for editing

**Optional flags:**
- `--persona-notes-file` - Additional persona context
- `--target-notes-file` - Additional target group context
- `--openai-api-key` - API key (or set OPENAI_API_KEY env var)
- `--llm-model` - Model name (default: gpt-4o-mini)
- `--export-lite-scenario` - Save inferred lite scenario
- `--export-scenario` - Save full scenario
- `--observed-funnel` - Add calibration
- `--export-plot-data` - Export visualization data
- `--dry-run` - Only extract scenario, do not run simulation (for debugging)
- `--verbose` - Show LLM prompt/response for debugging

**Output:**
- Inferred personas and steps summary
- Standard DropSim simulation results
- Narrative summary
- All exports work as usual

**Iteration workflow:**
1. Run `ingest-fintech` to generate initial scenario
2. Edit the exported `--export-lite-scenario` JSON
3. Run `simulate-lite` with edited scenario

## Examples

See `examples/` folder:
- `fintech_onboarding.json` - 5 personas, 6-step fintech flow (full format)
- `fintech_lite_onboarding.json` - 3 personas, 5-step fintech flow (lite format)
- `edtech_onboarding.json` - 3 personas, 4-step edtech flow
- `fintech_observed_funnel.json` - Real funnel data for calibration

## Documentation

Full product & system design: `DROPSIM_PRODUCT_DESIGN.md`


# Decision Simul

Decision simulation and autopsy engine for product onboarding flows. Simulates user journeys with persona-backed or synthetic traces, identifies belief-break points, and outputs founder-friendly Decision Autopsy JSON (verdict, one bet, evidence).

## Setup

```bash
pip install -r requirements.txt
```

Optional: set `OPENAI_API_KEY` (and `FIRECRAWL_API_KEY` if using URL ingestion) in the environment for LLM-backed inference.

## Quick start

- **Docs:** [docs/QUICK_START.md](docs/QUICK_START.md) — CLI and API usage  
- **Product runs:** Run a product simulation; outputs go to `output/`.

Examples:

```bash
# Novelty Wealth (default 1000 personas)
python3 run_novelty_wealth_simulation.py --n 70

# Currently (social app)
python3 run_currently_simulation.py

# Blink Money, Credigo, Bachatt, etc.
python3 run_blink_money_enhanced_inference.py
python3 run_bachatt_quick.py
```

## Repo layout

| Path | Purpose |
|------|--------|
| **docs/** | All markdown documentation (architecture, reports, guides) |
| **output/** | Generated Decision Autopsy JSON and related result files |
| **examples/** | Sample scenario JSON and target-group configs |
| **benchmark_flows/** | Benchmark product configs and runners |
| **calibration/** | Calibration and drift monitoring |
| **decision_*** | Decision graph, attribution, explainability, continuity |
| **sensitivity_engine/** | Sensitivity and perturbation analysis |
| **policy_registry/** | Policy versioning and resolution |
| **step_semantics/** | Step-level semantic and intent alignment |
| **\*_steps.py** | Product flow definitions (steps and signals) |
| **run_*.py** | Product-specific simulation runners (write to `output/`) |
| **blink_money/, credigo_ss/, novelty_wealth/, …** | Product screenshot assets (by product) |

## Products

Product flows are defined in `*_steps.py` and screenshots live in per-product folders. Runners (`run_*_simulation.py`, `run_*_quick.py`, etc.) use the intent-aware behavioral engine and (when configured) the Nemotron-Personas-India dataset; they write `*_DECISION_AUTOPSY_RESULT.json` into **output/**.

## License

See repository settings.

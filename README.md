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

Run from repo root so `output/` and `config/` paths resolve correctly:

```bash
# Novelty Wealth (default 1000 personas)
python3 scripts/run_novelty_wealth_simulation.py --n 70

# Currently (social app)
python3 scripts/run_currently_simulation.py

# Blink Money, Credigo, Bachatt, etc.
python3 scripts/run_blink_money_enhanced_inference.py
python3 scripts/run_bachatt_quick.py
```

## Repo layout

| Path | Purpose |
|------|--------|
| **config/** | Config and schema JSON (reference_signals, intent_profile, founder_output_schema, credigo_personas) |
| **docs/** | All markdown documentation (architecture, reports, guides) |
| **output/** | All generated artifacts: Decision Autopsy JSON, pipeline results, reports (PDF/HTML), analysis JSON, screenshot lists |
| **scripts/** | Entrypoint scripts: run_*, analyze_*, create_*, generate_*, test_* (run from repo root) |
| **examples/** | Sample scenario JSON and target-group configs |
| **benchmark_flows/** | Benchmark product configs and runners |
| **calibration/** | Calibration and drift monitoring |
| **decision_*** | Decision graph, attribution, explainability, continuity |
| **sensitivity_engine/** | Sensitivity and perturbation analysis |
| **policy_registry/** | Policy versioning and resolution |
| **step_semantics/** | Step-level semantic and intent alignment |
| **products/** | Product screenshot assets (bachatt, blink_money, credigo_ss, currently, keeper_ss, novelty_wealth, pluto_pe, trial1) |
| **\*_steps.py** | Product flow definitions at repo root (steps and signals) |

## Products

Product flows are defined in `*_steps.py` at repo root; screenshots live under **products/** (e.g. `products/blink_money/`, `products/novelty_wealth/`). Run simulations via **scripts/** (e.g. `python3 scripts/run_novelty_wealth_simulation.py`); they use the intent-aware behavioral engine and (when configured) the Nemotron-Personas-India dataset and write `*_DECISION_AUTOPSY_RESULT.json` into **output/**.

## License

See repository settings.

# Benchmark Flows - Implementation Status

## Phase 1: Benchmark Flow Definitions ✅

**Status:** Complete (3 products, expandable to 10)

**Created:**
- ✅ `zerodha.json` - 6 steps (trading)
- ✅ `groww.json` - 7 steps (wealth/investment)
- ✅ `cred.json` - 6 steps (credit rewards)

**Modules:**
- ✅ `benchmark_schema.md` - Schema documentation
- ✅ `benchmark_loader.py` - Load benchmark flows
- ✅ `benchmark_runner.py` - Run personas through benchmarks
- ✅ `comparative_analyzer.py` - Compare products

**Next:** Expand to 10 products (7 more: PhonePe, Paytm, Google Pay, Jupiter, Fi Money, Slice, OneCard)

---

## Phase 2: Benchmark Simulation ⏳

**Status:** Framework ready, needs integration

**Requires:**
- Integration with `sensitivity_engine.sensitivity_simulator`
- Unified ledger storage (`benchmark_decision_ledger.json`)
- Ensure identical personas across all products

**Deliverables:**
- Run 100 fixed personas through target + all benchmarks
- Capture full decision traces
- Store in unified ledger

---

## Phase 3: Comparative Sensitivity Analysis ⏳

**Status:** Analyzer created, needs testing

**Features:**
- Step-by-step comparisons (fragility ratios)
- Force dominance analysis
- Persona survival comparisons

**Output Examples:**
- "Cred's landing page is 2.8× more effort-sensitive than Groww's"
- "Zerodha delays risk until after value, improving low-energy retention"
- "Product X filters exploratory users earlier than benchmarks"

---

## Phase 4: Demo-Ready Outputs ⏳

**Status:** Not yet implemented

**Required:**
1. Benchmark Comparison Table
   - Rows: product steps
   - Columns: effort sensitivity, risk sensitivity, value leverage

2. Decision Sensitivity Curves
   - X-axis: perturbation magnitude
   - Y-axis: decision change rate
   - One curve per persona class

3. Founder-Readable Summary
   - "How Your Onboarding Compares to the Best Indian Fintech Products"
   - Structure: filtering points, trust demands, outperformance, recommendations

---

## Next Steps

1. **Complete Phase 2** - Test benchmark runner with 3 products
2. **Complete Phase 3** - Test comparative analyzer
3. **Implement Phase 4** - Create demo outputs
4. **Expand to 10 products** - Add remaining 7 benchmark flows


# Decision Attribution Layer: Improvement Roadmap

**Current Status:** Functional but can be improved  
**Goal:** Make attribution more accurate, actionable, and production-ready

---

## 1. Attribution Computation Quality

### Issue: Suspicious Normalization Patterns

**Current Problem:**
- Many steps show 100% attribution to a single force
- SHAP values are normalized to percentages, potentially masking signals
- Some forces get 0.0% attribution, which seems too extreme

**Improvements:**

#### A. Fix SHAP Value Normalization
```python
# Current: Normalizing to percentages might hide true contributions
drop_pct = {k: (v/total)*100 for k, v in drop_avg.items()}

# Better: Report raw SHAP values AND relative contributions
{
    "shap_values_raw": {...},  # Actual SHAP contributions
    "shap_values_relative": {...},  # Normalized percentages
    "total_contribution": 0.15  # Total absolute contribution
}
```

#### B. Improve Baseline Selection
```python
# Current: Fixed baseline (0.5 for all features)
baseline = {
    'cognitive_energy': 0.5,
    'intent_strength': 0.5,
    ...
}

# Better: Adaptive baseline based on step context
baseline = compute_step_adaptive_baseline(
    step_index, step_type, product_context
)
```

#### C. Validate Against Real Engine Logic
```python
# Add validation: Compare local function output with real engine
def validate_attribution_accuracy(traces, real_engine_results):
    """Compare local function predictions with actual engine outputs."""
    local_preds = [local_func.compute_probability(...) for trace in traces]
    real_preds = [trace['probability_before_sampling'] for trace in traces]
    
    mse = np.mean((np.array(local_preds) - np.array(real_preds))**2)
    assert mse < 0.01, f"Local function doesn't match engine (MSE: {mse})"
```

---

## 2. Analysis Depth & Sophistication

### Current Limitations:
- No persona-level analysis
- No sequential/temporal patterns
- No counterfactual analysis
- Limited cross-step comparisons

### Improvements:

#### A. Persona-Level Attribution
```python
def analyze_persona_sensitivity(traces):
    """Which persona types are most sensitive to which forces?"""
    # Group by persona characteristics
    # Analyze force sensitivity by persona class
    # Answer: "High-intent users drop due to effort, not intent mismatch"
```

#### B. Sequential Patterns
```python
def analyze_sequential_attribution(sequences):
    """How do forces compound across a user's journey?"""
    # Track force evolution within a single user's trajectory
    # Identify force accumulation patterns
    # Answer: "Users who experience trust deficit at Step 0 are 2x more likely to drop due to intent mismatch at Step 4"
```

#### C. Counterfactual Analysis
```python
def compute_counterfactual_attribution(trace, perturbations):
    """What if we changed one force? How would attribution change?"""
    # Recompute attribution with perturbed forces
    # Answer: "If we reduced effort by 20%, intent mismatch attribution drops from 91% to 65%"
```

#### D. Confidence Intervals
```python
def compute_attribution_confidence(traces, n_bootstrap=100):
    """Add confidence intervals to attribution estimates."""
    # Bootstrap sampling
    # Compute confidence intervals for each force
    # Answer: "Intent mismatch: 55.6% ± 2.1% (95% CI)"
```

---

## 3. Integration with Existing Systems

### Current Status:
- Attribution computed but not in Decision Ledger
- Attribution not in DIS outputs
- Attribution not in founder-facing reports

### Improvements:

#### A. Add to Decision Ledger
```python
# decision_graph/decision_ledger.py

@dataclass
class DecisionBoundaryAssertion:
    ...
    force_attribution: Optional[Dict[str, float]] = None  # NEW
    dominant_force: Optional[str] = None  # NEW
```

#### B. Add to DIS (Decision Intelligence Summary)
```markdown
## Decision Mechanics by Step

### Step 4: "Your top 2 spend categories?"

**Force Attribution (for REJECT decisions):**
- Intent mismatch: 91.1% of rejection pressure (95% CI: 89.2-93.0%)
- Trust deficit: 4.3% of rejection pressure
- Effort intolerance: 1.2% of rejection pressure

**Interpretation:** At this step, users who reject are primarily driven by intent mismatch...
```

#### C. Founder-Facing "Decision Mechanics" Section
```markdown
# Why Users Drop: Decision Mechanics

**The Core Truth:** Credigo has two phases:
1. Trust Filter (Step 0): Trust drives 49% of drops
2. Intent Filter (Steps 1+): Intent mismatch drives 84-100% of drops

[Visual: Force evolution chart]
[Actionable recommendations]
```

---

## 4. Performance Optimization

### Current Issue:
- Exact Shapley computation is O(2^n) for n features
- Computationally expensive for 11 features
- Runs on every decision (36K+ traces)

### Improvements:

#### A. Approximate Shapley Values
```python
# Use sampling-based approximation for large feature sets
def compute_shapley_approximate(func, features, baseline, n_samples=1000):
    """Monte Carlo sampling for Shapley values."""
    # Much faster than exact enumeration
    # Accuracy trade-off (but acceptable for production)
```

#### B. Caching
```python
# Cache attribution computations for similar states
@lru_cache(maxsize=10000)
def compute_attribution_cached(state_hash, step_context):
    """Cache attribution for identical states."""
    ...
```

#### C. Parallel Computation
```python
# Compute attribution in parallel batches
def compute_attribution_batch(traces, n_workers=4):
    """Parallel attribution computation."""
    with Pool(n_workers) as pool:
        attributions = pool.map(compute_attribution, traces)
```

---

## 5. Accuracy & Validation

### Current Gap:
- Local decision function might not perfectly match engine
- No validation that attribution is "correct"
- No comparison with actual behavioral logic

### Improvements:

#### A. Perfect Engine Mirror
```python
# Refactor to use actual engine functions (not surrogate)
def compute_attribution_from_engine(trace, engine_func):
    """Use actual engine logic, not surrogate."""
    # Reuse behavioral_engine_intent_aware functions directly
    # No approximation needed
```

#### B. Attribution Validation
```python
def validate_attribution_plausibility(attribution):
    """Check that attribution makes sense."""
    # SHAP values should sum to (final_prob - baseline_prob)
    # Forces should be bounded
    # Dominant forces should align with known step characteristics
```

#### C. Sensitivity Testing
```python
def test_attribution_sensitivity():
    """Test that small changes in features produce expected attribution changes."""
    # Perturb features slightly
    # Check attribution changes are reasonable
```

---

## 6. Output Quality & Usability

### Current Limitations:
- No visualizations
- Limited actionable recommendations
- No confidence metrics
- Hard to compare across products

### Improvements:

#### A. Visualizations
```python
# Generate charts:
# - Force evolution through funnel
# - Force co-occurrence heatmaps
# - Attribution comparison across steps
# - Persona sensitivity matrices
```

#### B. Actionable Recommendations
```python
def generate_attribution_recommendations(attribution_analysis):
    """Generate specific, testable recommendations."""
    # "Reduce intent mismatch at Step 4 by showing value preview"
    # "Strengthen trust signals at Step 0 (expected 10-15% drop reduction)"
    # "Break Step 3 into smaller chunks to reduce cognitive fatigue"
```

#### C. Comparison Framework
```python
def compare_attribution_across_products(product1_attr, product2_attr):
    """Compare attribution patterns across products."""
    # "Credigo is 2x more intent-sensitive than Groww"
    # "Trust matters more in Credigo (20.7%) vs Trial1 (5.2%)"
```

---

## 7. Advanced Features

### Future Enhancements:

#### A. Interactive Attribution Explorer
```python
# Web interface to explore attribution
# Filter by step, decision type, persona class
# Drill down into specific traces
```

#### B. Attribution-Based A/B Testing
```python
def design_ab_test_from_attribution(attribution_analysis):
    """Design A/B tests based on attribution insights."""
    # "Test: Reduce intent mismatch at Step 4"
    # "Expected impact: 20-30% reduction in Step 4 drops"
    # "Sample size needed: 500 users per variant"
```

#### C. Predictive Attribution
```python
def predict_attribution_for_new_step(new_step_config):
    """Predict what forces will dominate for a new step design."""
    # Use historical attribution patterns
    # Predict dominant forces before running simulation
```

---

## Priority Ranking

### High Priority (Do First):
1. ✅ Fix SHAP normalization (report raw + relative)
2. ✅ Add attribution to Decision Ledger
3. ✅ Validate local function matches engine
4. ✅ Add confidence intervals

### Medium Priority (Do Next):
5. Add attribution to DIS outputs
6. Persona-level analysis
7. Sequential pattern analysis
8. Performance optimization (caching/approximation)

### Low Priority (Future):
9. Counterfactual analysis
10. Visualizations
11. Interactive explorer
12. Predictive attribution

---

## Implementation Plan

### Phase 1: Accuracy (Week 1)
- Fix normalization issues
- Validate local function accuracy
- Add confidence intervals
- Improve baseline selection

### Phase 2: Integration (Week 2)
- Add to Decision Ledger
- Add to DIS outputs
- Create founder-facing "Decision Mechanics" section

### Phase 3: Depth (Week 3)
- Persona-level analysis
- Sequential patterns
- Counterfactual analysis

### Phase 4: Production (Week 4)
- Performance optimization
- Caching
- Approximate methods
- Monitoring & validation

---

**Next Step:** Start with Phase 1 (Accuracy improvements) to ensure attribution is mathematically sound before adding features.


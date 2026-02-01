# Attribution Improvements: Quick Wins (Do These First)

**Goal:** Fix the most critical issues quickly to improve attribution quality

---

## 1. Fix Normalization That Masks Signals

### Problem
Current code normalizes SHAP values to percentages, which can make it look like one force dominates 100% when actually multiple forces contribute.

### Fix
Report both raw SHAP values AND relative contributions:

```python
# In shap_attributor.py, compute_decision_attribution()

# Don't normalize - keep raw SHAP values
attribution = DecisionAttribution(
    ...
    shap_values_raw=aggregated_shap,  # Raw values
    shap_values_relative=normalized_shap,  # Percentages (for readability)
    total_contribution=sum(abs(v) for v in aggregated_shap.values())  # Total magnitude
)
```

**Impact:** See true force contributions, not just relative percentages

---

## 2. Validate Local Function Matches Engine

### Problem
Local decision function might not perfectly mirror behavioral engine logic.

### Fix
Add validation function:

```python
def validate_local_function_accuracy():
    """Compare local function output with actual engine."""
    # Sample 100 traces
    # Compute probability with local function
    # Compare with actual probability_before_sampling
    # Report MSE, max error
    # Fail if error > threshold
```

**Impact:** Ensure attribution is accurate, not just consistent

---

## 3. Improve Baseline Selection

### Problem
Fixed baseline (0.5 for all features) might not reflect step context.

### Fix
Use step-adaptive baseline:

```python
def get_step_adaptive_baseline(step_index, step_type):
    """Baseline that reflects step context."""
    # Early steps: higher baseline trust, lower baseline effort
    # Late steps: higher baseline commitment, lower baseline intent mismatch
    baseline = get_baseline_features()
    
    if step_index < 3:
        baseline['trust_baseline'] = 0.6  # Higher trust expected
    else:
        baseline['intent_mismatch'] = 0.1  # Lower mismatch expected
    
    return baseline
```

**Impact:** More accurate attribution relative to step context

---

## 4. Add Confidence Intervals

### Problem
No indication of attribution uncertainty/variance.

### Fix
Bootstrap confidence intervals:

```python
def compute_attribution_with_ci(traces, n_bootstrap=100):
    """Compute attribution with confidence intervals."""
    # Bootstrap sample traces
    # Compute attribution for each sample
    # Report mean ± CI
```

**Impact:** Know which attributions are reliable vs noisy

---

## 5. Fix 100% Attribution Cases

### Problem
Some steps show 100% attribution to single force, which seems suspicious.

### Fix
Investigate and fix:

```python
# In aggregation, check for extreme cases
if max(force_pct.values()) > 0.95:
    # Flag as potentially problematic
    # Check if normalization is correct
    # Consider reporting raw values instead
```

**Impact:** More realistic, multi-factor attributions

---

## Implementation Order

1. **Fix normalization** (30 min) - Report raw + relative
2. **Add validation** (1 hour) - Ensure accuracy
3. **Improve baseline** (1 hour) - Better context
4. **Add confidence intervals** (2 hours) - Reliability
5. **Fix 100% cases** (2 hours) - Realistic attributions

**Total: ~6 hours for all quick wins**

---

## Expected Improvements

After these fixes:
- ✅ More accurate attribution (validated against engine)
- ✅ Better signal visibility (raw + relative values)
- ✅ More realistic attributions (fewer 100% cases)
- ✅ Reliable insights (confidence intervals)
- ✅ Context-aware (adaptive baselines)

**This makes attribution production-ready for decision-making.**


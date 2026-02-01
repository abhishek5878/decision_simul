# Blink Money Variant Results: Realistic Assessment

**Analysis Date:** January 2025  
**Sample:** 1,000 personas × 7 variants = 7,000 total simulations

---

## The Results (What We Got)

| Variant | Completion Rate | Drop at Step 0 | Top Drop Force |
|---------|----------------|----------------|----------------|
| **Tech Savvy Optimistic** | **43.30%** | 19.3% | Trust (29.6%) |
| Fresh Motivated | 40.90% | 20.9% | Trust (29.5%) |
| Browsing Casually | 40.50% | 20.9% | Trust (30.3%) |
| Urgent Need | 40.40% | 19.8% | Trust (29.4%) |
| Tired Commuter | 40.20% | 21.4% | Trust (28.9%) |
| **Distrustful Arrival** | **39.90%** | 20.9% | Trust (30.5%) |
| **Price Sensitive** | **37.60%** | 21.5% | Trust (29.9%) |

---

## Realistic Assessment: What's Wrong?

### Issue 1: Variants Are Too Similar

**Problem:** Completion rates range from 37.6% to 43.3% - only a 5.7 percentage point spread.

**Expected Differences:**
- **Distrustful Arrival** (39.9%) should perform **significantly worse** than Fresh Motivated (40.9%)
  - Current gap: Only 1.0 percentage point
  - Expected gap: Should be 5-10 percentage points worse
  
- **Tired Commuter** (40.2%) should perform **worse** than Fresh Motivated (40.9%)
  - Current gap: Only 0.7 percentage points
  - Expected gap: Should be 3-5 percentage points worse
  
- **Tech Savvy Optimistic** (43.3%) should perform **much better** than others
  - Current gap: Only 2.4 percentage points above average
  - Expected gap: Should be 5-8 percentage points better

- **Price Sensitive** (37.6%) should perform **much worse** given the value proposition
  - Current gap: Only 3.3 percentage points below average
  - Expected gap: Should be 8-12 percentage points worse for credit products

---

### Issue 2: Distrustful Arrival Performs Too Well

**Finding:** Distrustful Arrival has 39.9% completion rate - only 1.0% worse than Fresh Motivated.

**Why This Is Unrealistic:**
- Users who arrive distrustful should drop more at Step 1 (Mobile Number) and Step 2 (PAN/DOB)
- Trust is the top drop force (30.5%), but the overall completion rate doesn't reflect this
- **Expected:** 30-35% completion rate for distrustful users

**Possible Causes:**
- Trust signals in the model might not be strong enough
- Trust penalty might not compound across steps
- Early drops might be balanced by later step performance

---

### Issue 3: Price Sensitive Doesn't Drop Enough

**Finding:** Price Sensitive has 37.6% completion - only 3.3% below average.

**Why This Is Unrealistic:**
- Blink Money is a credit product (9.99% p.a. interest)
- Price-sensitive users should care more about rates and terms
- Value clarity is a top drop force (27.2%), but completion is still relatively high
- **Expected:** 25-30% completion rate for price-sensitive users in credit products

**Possible Causes:**
- Value clarity signals might not be differentiated enough
- Price sensitivity might not be properly modeled for financial products
- The model might not penalize value perception enough

---

### Issue 4: Tech Savvy Optimistic Doesn't Perform Enough Better

**Finding:** Tech Savvy Optimistic has 43.3% completion - only 2.4% above average.

**Why This Is Unrealistic:**
- Tech-savvy users should have:
  - Lower risk perception (they understand digital security)
  - Lower effort perception (they're comfortable with forms)
  - Higher trust (they understand how fintech works)
- **Expected:** 50-55% completion rate for tech-savvy users

**Possible Causes:**
- Trust signals might not differentiate enough
- Risk perception might not be properly modeled
- The model might be too conservative

---

### Issue 5: Tired Commuter vs Fresh Motivated

**Finding:** Tired Commuter (40.2%) performs almost as well as Fresh Motivated (40.9%).

**Why This Is Unrealistic:**
- Cognitive energy difference (0.5× vs 0.9×) should create larger gaps
- Tired users should drop more at cognitively demanding steps
- **Expected:** 3-5 percentage point gap

**Possible Causes:**
- Cognitive fatigue might not compound enough across steps
- The model might reset cognitive energy too quickly
- Cognitive demand signals might not be strong enough

---

## What's Working (Realistic Patterns)

### Pattern 1: Early Filtering Is Consistent
- All variants drop 19-21% at Step 0 (landing page)
- This is realistic - landing page is the primary filter

### Pattern 2: Trust Is the Dominant Force
- All variants have Trust as top drop force (28.9% - 30.5%)
- This is realistic for financial products

### Pattern 3: Price Sensitive Is Worst
- Price Sensitive has the lowest completion (37.6%)
- This direction is correct, though the magnitude might be too small

### Pattern 4: Tech Savvy Is Best
- Tech Savvy Optimistic has the highest completion (43.3%)
- This direction is correct, though the magnitude might be too small

---

## Expected vs Actual Completion Rates

| Variant | Actual | Expected (Realistic) | Gap |
|---------|--------|---------------------|-----|
| Tech Savvy Optimistic | 43.3% | 50-55% | **-7 to -12 pp** |
| Fresh Motivated | 40.9% | 40-45% | ✓ Close |
| Browsing Casually | 40.5% | 35-40% | **+0.5 to +5 pp** |
| Urgent Need | 40.4% | 42-47% | **-1.6 to -6.6 pp** |
| Tired Commuter | 40.2% | 35-38% | **+2.2 to +5.2 pp** |
| Distrustful Arrival | 39.9% | 30-35% | **+4.9 to +9.9 pp** |
| Price Sensitive | 37.6% | 25-30% | **+7.6 to +12.6 pp** |

**Key Issues:**
- **Distrustful Arrival** performs **9.9 percentage points better** than expected
- **Price Sensitive** performs **12.6 percentage points better** than expected
- **Tech Savvy Optimistic** performs **12 percentage points worse** than expected
- **Tired Commuter** performs **5.2 percentage points better** than expected

---

## Root Causes (Hypothesis)

### 1. Trust Penalty Is Not Strong Enough
- Distrustful users should drop 10-15% more, but they only drop 1% more
- Trust signals might not compound across steps
- Trust baseline differences might not be large enough

### 2. Value Clarity Differentiation Is Weak
- Price-sensitive users should drop much more, but they only drop 3.3% more
- Value signals might not differentiate enough between variants
- Price sensitivity might not affect value perception enough

### 3. Cognitive Energy Impact Is Muted
- Tired users should perform worse, but they perform almost as well
- Cognitive fatigue might reset too quickly
- Cognitive demand signals might not be strong enough

### 4. Risk Perception Differentiation Is Weak
- Tech-savvy users (low risk) should perform much better
- Risk tolerance differences might not affect decisions enough
- Risk signals might not differentiate enough between variants

---

## Recommendations

### 1. Increase Trust Penalty for Distrustful Users
- Multiply trust penalties by 1.5-2× for distrustful variant
- Ensure trust compounds across steps (not just at entry)

### 2. Increase Value Clarity Penalty for Price-Sensitive Users
- Multiply value clarity penalties by 2-3× for price-sensitive variant
- Increase value signal differentiation in the model

### 3. Increase Cognitive Fatigue Impact
- Ensure cognitive energy differences persist across steps
- Increase cognitive demand signals at later steps

### 4. Increase Risk Perception Differentiation
- Amplify risk tolerance differences between variants
- Ensure tech-savvy users get larger risk reductions

### 5. Calibrate to Real-World Benchmarks
- Compare against real fintech completion rates by user segment
- Adjust variant multipliers to match observed patterns

---

## Conclusion

The variant results show **correct directional patterns** but **insufficient differentiation**. The model correctly identifies:
- Tech Savvy Optimistic as best performer
- Price Sensitive as worst performer
- Trust as dominant force

However, the **magnitude of differences is too small**. The model needs:
- Stronger variant-specific penalties/multipliers
- Better compounding of state differences across steps
- More realistic differentiation between user states

**Current State:** Model is conservative and doesn't differentiate enough between user states.  
**Expected State:** 10-15 percentage point spread between best and worst variants.


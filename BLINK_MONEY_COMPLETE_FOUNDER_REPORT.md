# Blink Money: Complete Product Analysis for Founders

**Analysis Date:** January 2025  
**Methodology:** Decision-first behavioral simulation with SHAP explainability  
**Purpose:** Understand what Blink Money actually does, not what it should do

---

## EXECUTIVE SUMMARY

**Blink Money converts 21.15% of users who start the flow.** The product has a 7-step onboarding flow for credit against mutual funds with strong completion rates. Unlike many fintech products, Blink Money has zero intent mismatch—the product is clear, and users either want it or don't.

**The Core Truth:**
- ✅ **Zero intent mismatch** - product is clear (credit against mutual funds)
- ⚠️ **Trust is the primary barrier** (30.5% of drops)
- ⚠️ **Value clarity matters early** (28.0% of drops, 42.9% at landing)
- ✅ **Early filtering pattern** (20.7% drop at landing, then progressive filtering)
- ✅ **Strong completion rate** (40.29% of those who enter complete all 7 steps)

---

## THE FUNNEL IN NUMBERS

```
Step 0 (Landing)           → 100 users start
                            ↓ 20.7% drop (21 users)
Step 1 (Mobile Number)     → 79 users continue
                            ↓ 18.0% drop (14 users)
Step 2 (PAN and DOB)       → 65 users continue
                            ↓ 14.1% drop (9 users)
Step 3 (OTP Verification)  → 56 users continue
                            ↓ 6.6% drop (4 users)
Step 4 (Bank Linking)      → 52 users continue
                            ↓ 8.2% drop (4 users)
Step 5 (Eligibility Results) → 48 users continue
                            ↓ 9.0% drop (4 users)
Step 6 (Final Confirmation) → 44 users continue
                            ↓ 7.5% drop (3 users)
Completion                  → 41 users complete (40.3% completion rate)
```

**Entry Rate:** 52.5% of traffic enters the flow  
**Completion Rate:** 40.3% of those who enter complete  
**Total Conversion:** 21.15% overall

**Key Insight:** The largest filtering happens at the landing page (20.7%). Once users commit past Step 2 (PAN/DOB), completion rates remain high (85-93% per step), indicating strong commitment from users who proceed.

---

## WHAT BLINK MONEY DECIDES ABOUT ITS USERS

### The Kind of User Blink Money is Built For

Blink Money is built for users who:

- **Have mutual funds and want credit**
  - They understand the value proposition (credit against mutual funds)
  - They're willing to share basic info (mobile, PAN, DOB) for eligibility check
  - They trust the "no credit score impact" promise

- **Value speed and clarity**
  - The 7-step flow is structured and straightforward
  - Value is shown at Step 5 (eligibility results)
  - Clear progression through verification steps

- **Are ready to check eligibility immediately**
  - They don't need extensive education
  - They understand credit products
  - They trust financial platforms with their data

### The Kind of User Blink Money Filters Out

**Step 0 Filter (20.7%):**
- Users who don't see clear value (42.9% of drops)
- Users who need more education about the product
- Users who don't have mutual funds or don't understand the concept
- Users with low trust who need reassurance before starting

**Step 1 Filter (18.0%):**
- Users with privacy concerns (31.0% of drops are trust-related)
- Users hesitant about data sharing
- Users who don't trust the platform with phone number

**Step 2 Filter (14.1%):**
- Users concerned about sharing PAN (26.7% of drops are value-related)
- Users who don't see clear value in proceeding
- Users who are risk-averse about financial data

**Later Steps (6.6-9.0% drops):**
- By this point, users are highly committed
- Drops are minimal and represent users who can't proceed for technical/logistical reasons

---

## THE DECISION GATES

### Decision Gate 1: Step 0 - Smart Credit against Mutual Funds

**Signal Demanded:** Initial commitment to check eligibility

**Who Passes (79.3%):**
- Users ready to check eligibility immediately
- Users who understand the value proposition
- Users who trust the "no credit score impact" promise

**Who Fails (20.7%):**
- Users uncertain about the product (value clarity: 42.9% of drops)
- Users who need more education
- Users who don't have mutual funds or don't understand the concept
- Users with low trust (33.3% of drops)

**Tradeoff:**
- **Gain:** Fast, efficient flow for committed users who understand the product
- **Loss:** Loses 20.7% who might convert with more education or clearer value communication

---

### Decision Gate 2: Step 1 - Check Your Eligibility (Mobile Number)

**Signal Demanded:** Mobile number for verification

**Who Passes (82.0%):**
- Users committed to checking eligibility
- Users who trust the platform with phone number
- Users ready to proceed with verification

**Who Fails (18.0%):**
- Users with privacy concerns (trust: 31.0% of drops)
- Users hesitant about data sharing
- Users who don't trust the platform
- Users who find the step too much effort (effort: 19.6% of drops)

**Tradeoff:**
- **Gain:** Progresses committed users quickly through verification
- **Loss:** Filters out privacy-conscious users who might convert with stronger trust signals

---

### Decision Gate 3: Step 2 - Check Limit (PAN and DOB)

**Signal Demanded:** PAN and date of birth (sensitive financial information)

**Who Passes (85.9%):**
- Users who trust the platform with sensitive data
- Users who see value in proceeding
- Users who are not risk-averse about financial data

**Who Fails (14.1%):**
- Users concerned about sharing PAN (value: 26.7% of drops, trust: 23.2% of drops)
- Users who don't see clear value in proceeding
- Users who are risk-averse about financial data (risk: 16.8% of drops)

**Tradeoff:**
- **Gain:** Progresses highly committed users to eligibility check
- **Loss:** Filters out users who might convert with stronger value/reassurance signals

---

### Decision Gate 4: Step 3 - OTP Verification

**Signal Demanded:** OTP code for phone verification

**Who Passes (93.4%):**
- Users who can access their phone
- Users who are committed to the process

**Who Fails (6.6%):**
- Users who can't access phone
- Users who find OTP step cumbersome

**Tradeoff:**
- **Gain:** Verifies phone ownership, maintains security
- **Loss:** Minimal - low drop rate at this step

---

### Decision Gate 5: Step 4 - Bank Account Linking

**Signal Demanded:** Bank account access (read-only)

**Who Passes (91.8%):**
- Users who trust the platform with bank access
- Users who are committed to getting credit
- Users who understand the "read-only" reassurance

**Who Fails (8.2%):**
- Users concerned about bank account security
- Users who are hesitant about financial account linking

**Tradeoff:**
- **Gain:** Enables loan disbursement process
- **Loss:** Filters out security-conscious users who might convert with stronger reassurance

---

### Decision Gate 6: Step 5 - Eligibility Results

**Signal Demanded:** Acceptance of eligibility results

**Who Passes (91.0%):**
- Users who are eligible and satisfied with results
- Users who want to proceed with loan application

**Who Fails (9.0%):**
- Users who are not eligible
- Users who don't meet expectations
- Users who are not satisfied with terms or credit limit

**Tradeoff:**
- **Gain:** Shows value (eligibility) to users - this is the FIRST VALUE moment
- **Loss:** Users drop if they don't meet eligibility or expectations

---

### Decision Gate 7: Step 6 - Final Confirmation

**Signal Demanded:** Commitment to proceed with loan application

**Who Passes (92.5%):**
- Users ready to commit to loan application
- Users who have completed all previous steps

**Who Fails (7.5%):**
- Users who need more time
- Users who want to compare options
- Users who are not ready to commit

**Tradeoff:**
- **Gain:** Committed users proceed to application
- **Loss:** Filters out users who need more time or comparison

---

## WHY USERS DROP: FORCE ATTRIBUTION

Across all drop decisions, here's what drives rejection:

1. **Trust: 30.5%** of rejection pressure
   - Users don't trust the platform with financial data
   - Privacy concerns about data sharing
   - Hesitation about platform security

2. **Value: 28.0%** of rejection pressure
   - Value proposition is unclear or insufficient
   - Users don't see clear benefits
   - Need more clarity on what they'll get

3. **Risk: 15.5%** of rejection pressure
   - Users are concerned about credit product risks
   - Financial data sharing concerns
   - Credit score impact worries

4. **Cognitive Energy: 11.0%** of rejection pressure
   - Users find the step mentally taxing
   - Process feels too complex

5. **Effort: 9.4%** of rejection pressure
   - Users find the step too much work
   - Friction in completing actions

6. **Risk Tolerance: 4.0%** of rejection pressure
7. **Effort Tolerance: 1.6%** of rejection pressure
8. **Intent: 0.0%** of rejection pressure
9. **Intent Mismatch: 0.0%** of rejection pressure

**Key Insight:** Unlike many products (including Credigo with 58.7% intent mismatch), Blink Money has **zero intent mismatch**. The product is clear (credit against mutual funds), and users either want it or don't. The barriers are trust, value clarity, and risk - not product-user fit.

---

## STEP-BY-STEP ANALYSIS

### Step 0: Smart Credit against Mutual Funds (Landing Page)

- **Reached by:** 700 users (100% of entry)
- **Drop rate:** 20.7% (145 users)
- **Continue:** 555 users (79.3%)
- **Dominant force (drops):** Value (42.9%), Trust (33.3%), Risk (12.9%)

**What Happens:** Largest single drop point. Users need clearer value communication and trust signals.

---

### Step 1: Check Your Eligibility - Mobile Number

- **Reached by:** 555 users
- **Drop rate:** 18.0% (100 users)
- **Continue:** 455 users (82.0%)
- **Dominant force (drops):** Trust (31.0%), Effort (19.6%), Risk (18.4%)

**What Happens:** Second-largest drop point. Trust and effort are the key barriers after initial commitment.

---

### Step 2: Check Limit - PAN and DOB

- **Reached by:** 455 users
- **Drop rate:** 14.1% (64 users)
- **Continue:** 391 users (85.9%)
- **Dominant force (drops):** Value (26.7%), Trust (23.2%), Risk (16.8%)

**What Happens:** Third-largest drop point. PAN is sensitive; users need stronger value/reassurance signals.

---

### Step 3: OTP Verification

- **Reached by:** 391 users
- **Drop rate:** 6.6% (26 users)
- **Continue:** 365 users (93.4%)

**What Happens:** Low drop rate - users who reach this step are committed.

---

### Step 4: Bank Account Linking

- **Reached by:** 365 users
- **Drop rate:** 8.2% (30 users)
- **Continue:** 335 users (91.8%)

**What Happens:** Moderate drop - bank linking is a trust/risk barrier, but users are invested by this point.

---

### Step 5: Eligibility Results

- **Reached by:** 335 users
- **Drop rate:** 9.0% (30 users)
- **Continue:** 305 users (91.0%)

**What Happens:** **FIRST VALUE** delivery point. Some users drop if they don't meet eligibility or expectations.

---

### Step 6: Final Confirmation

- **Reached by:** 305 users
- **Drop rate:** 7.5% (23 users)
- **Continue:** 282 users (92.5%)

**What Happens:** Lowest drop rate - users who reach final confirmation are highly committed.

---

## HOW BLINK MONEY COMPARES TO CREDIGO

| Metric | Blink Money | Credigo |
|--------|-------------|---------|
| **Steps** | 7 | 11 |
| **Entry Rate** | 52.5% | 55.5% |
| **Completion Rate** | **40.3%** | 21.9% |
| **Total Conversion** | **21.15%** | 12.15% |
| **Top Drop Driver** | Trust (30.5%) | Intent mismatch (58.7%) |
| **Intent Mismatch** | **0.0%** (clear product) | 58.7% (unclear fit) |
| **Drop Pattern** | Early filtering (20.7% at landing) | Consistent drops throughout |
| **Value Delivery** | Step 5 (eligibility results) | Step 10 (recommendations) |

**Key Differences:**
1. **Intent Clarity:** Blink Money has zero intent mismatch - product is clear. Credigo struggles with intent alignment.
2. **Completion Rate:** Blink Money achieves 1.8× higher completion despite similar step count (7 vs 11).
3. **Drop Pattern:** Blink Money filters early (20.7% at landing), then maintains high continuation rates. Credigo has consistent drops throughout.
4. **Primary Barrier:** Trust (Blink Money) vs Intent mismatch (Credigo).
5. **Value Timing:** Blink Money delivers value at Step 5 (of 7). Credigo delivers at Step 10 (of 11).

---

## STRATEGIC IMPLICATIONS

### What's Working

1. **Clear Product Value:** Zero intent mismatch means users understand what they're getting. No confusion about product fit.

2. **Strong Completion Rate:** 40.3% completion is excellent for a 7-step financial product flow. Once users commit past Step 2, they're highly likely to complete.

3. **Early Filtering:** Users who aren't a good fit drop early (20.7% at landing), saving resources and focusing efforts on committed users.

4. **Progressive Commitment:** Drop rates decrease as users progress, indicating strong commitment from those who continue.

### What Needs Improvement

1. **Trust Signals (Priority: HIGH)**
   - 30.5% of drops are trust-related
   - Strengthen security messaging, regulatory compliance, social proof
   - Add trust indicators at Steps 1-2 (mobile/PAN entry)
   - Show data encryption/privacy messaging

2. **Value Clarity at Landing (Priority: HIGH)**
   - 28.0% of drops are value-related, with 42.9% at landing page
   - Clarify benefits earlier and more prominently
   - Show use cases (wedding, emergency, etc.)
   - Highlight unique advantages more clearly

3. **Risk Reassurance (Priority: MEDIUM)**
   - 15.5% of drops are risk-related
   - Emphasize "no credit score impact" more prominently
   - Add reassurance at PAN/DOB step
   - Show security certifications

### The Unavoidable Decision Question

**Do you want to optimize for trust and convert more users, or accept the current trust barrier as a quality filter?**

- **Option A:** Strengthen trust signals → Higher conversion (potentially 30-40% completion), but may attract less-qualified users who drop later
- **Option B:** Keep current trust barrier → Lower conversion (40% completion), but users who complete are highly committed and qualified

**There's no right answer** - it depends on your business model, user acquisition costs, and whether you prioritize volume or quality.

---

## METHODOLOGY NOTES

- **Simulation:** 100 personas × 7 steps = 3,106 decision points
- **Attribution Method:** Shapley values (cooperative game theory)
- **Baseline:** Adaptive by step context
- **Coverage:** 100% of traces include attribution
- **Analysis Date:** January 2025
- **Product Steps:** 7-step onboarding flow for credit against mutual funds

---

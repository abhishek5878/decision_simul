# Intent Inference Improvements - Persona-Driven Granular Intent

## Problem Statement

**Current Limitation**: All users coming to a credit card landing page share the same high-level intent (get credit card recommendations), so the current intent inference doesn't capture nuanced differences in HOW they want to achieve that goal.

**Example**: 
- User A: Wants to compare 5 cards side-by-side before deciding (compare_options)
- User B: Already knows which card they want, just checking eligibility (eligibility_check)
- User C: New to credit cards, wants to learn basics first (learn_basics)
- User D: Needs a card urgently for a purchase (quick_decision)

All four want "credit card recommendations" but have different paths to get there.

---

## Solution: Persona-Driven Intent Inference

### Key Improvements

1. **Persona Behavioral Traits → Intent Mapping**
   - Use persona's cognitive capacity, risk tolerance, urgency, etc. to infer granular intent
   - High cognitive capacity + low risk tolerance → `validate_choice`
   - Low cognitive capacity + high urgency → `quick_decision`
   - High cognitive capacity + high openness → `compare_options`

2. **Entry Context Signals**
   - Search query analysis (if available)
   - Referral source (organic search → compare, direct → quick_decision)
   - Time of day / device (mobile late night → quick_decision)

3. **Persona-Level Intent Modifiers**
   - Each persona has a base intent distribution based on their traits
   - Product signals (CTA, copy) modify this base distribution
   - Result: More realistic, persona-specific intent inference

4. **Multi-Signal Fusion**
   - Combine: Persona traits + Product signals + Entry context
   - Weight persona traits more heavily (60%) than product signals (40%)
   - This ensures personas with different traits get different intents even on same landing page

---

## Implementation Plan

### Phase 1: Persona Trait → Intent Mapping

```python
def infer_intent_from_persona_traits(priors: Dict, persona_inputs: Dict) -> Dict[str, float]:
    """
    Infer base intent distribution from persona behavioral traits.
    
    Key Mappings:
    - High Cognitive Capacity + Low Risk Tolerance → validate_choice
    - Low Cognitive Capacity + High Urgency → quick_decision  
    - High Cognitive Capacity + High Openness → compare_options
    - Low Cognitive Capacity + Low Urgency → learn_basics
    - High Risk Tolerance + High Urgency → eligibility_check
    """
    intent_weights = {intent_id: 0.0 for intent_id in CANONICAL_INTENTS.keys()}
    
    # Extract persona traits
    cognitive_capacity = priors.get('cognitive_capacity', 0.5)
    risk_tolerance = priors.get('risk_tolerance', 0.5)
    urgency = persona_inputs.get('urgency', 0.5)
    openness = priors.get('openness', 0.5)
    financial_literacy = persona_inputs.get('financial_literacy', 0.5)
    
    # Rule 1: Cognitive Capacity + Risk Tolerance → Validation vs Quick Decision
    if cognitive_capacity > 0.7 and risk_tolerance < 0.4:
        # High capacity, risk-averse → wants to validate carefully
        intent_weights['validate_choice'] += 0.4
        intent_weights['compare_options'] += 0.3
    elif cognitive_capacity < 0.4 and urgency > 0.6:
        # Low capacity, high urgency → wants quick decision
        intent_weights['quick_decision'] += 0.5
        intent_weights['eligibility_check'] += 0.3
    
    # Rule 2: Openness + Cognitive Capacity → Comparison vs Learning
    if openness > 0.7 and cognitive_capacity > 0.6:
        # High openness, high capacity → wants to explore options
        intent_weights['compare_options'] += 0.4
        intent_weights['learn_basics'] += 0.2
    elif openness < 0.4 and cognitive_capacity < 0.5:
        # Low openness, low capacity → wants to learn basics first
        intent_weights['learn_basics'] += 0.5
        intent_weights['validate_choice'] += 0.2
    
    # Rule 3: Financial Literacy → Eligibility vs Learning
    if financial_literacy > 0.7:
        # High literacy → knows what they want, just checking eligibility
        intent_weights['eligibility_check'] += 0.4
        intent_weights['validate_choice'] += 0.3
    elif financial_literacy < 0.4:
        # Low literacy → needs to learn basics
        intent_weights['learn_basics'] += 0.5
        intent_weights['compare_options'] += 0.2
    
    # Rule 4: Urgency → Quick Decision vs Comparison
    if urgency > 0.7:
        # High urgency → wants quick decision
        intent_weights['quick_decision'] += 0.4
        intent_weights['eligibility_check'] += 0.3
    elif urgency < 0.3:
        # Low urgency → can take time to compare
        intent_weights['compare_options'] += 0.3
        intent_weights['learn_basics'] += 0.2
    
    # Normalize
    total = sum(intent_weights.values())
    if total > 0:
        intent_weights = {k: v / total for k, v in intent_weights.items()}
    else:
        # Default uniform if no signals
        intent_weights = {k: 1.0 / len(intent_weights) for k in intent_weights.keys()}
    
    return intent_weights
```

### Phase 2: Entry Context Signals

```python
def infer_intent_from_entry_context(
    entry_context: Optional[Dict] = None
) -> Dict[str, float]:
    """
    Infer intent from how user arrived at landing page.
    
    Signals:
    - Search query: "best credit card" → compare_options
    - Search query: "credit card eligibility" → eligibility_check
    - Referral: Direct → quick_decision (knows what they want)
    - Referral: Organic search → compare_options (exploring)
    - Device: Mobile late night → quick_decision (urgent)
    - Device: Desktop daytime → compare_options (research mode)
    """
    intent_modifiers = {intent_id: 1.0 for intent_id in CANONICAL_INTENTS.keys()}
    
    if not entry_context:
        return intent_modifiers
    
    # Search query analysis
    search_query = entry_context.get('search_query', '').lower()
    if search_query:
        if any(word in search_query for word in ['best', 'compare', 'top', 'vs']):
            intent_modifiers['compare_options'] *= 2.0
        elif any(word in search_query for word in ['eligibility', 'check', 'qualify']):
            intent_modifiers['eligibility_check'] *= 2.0
        elif any(word in search_query for word in ['learn', 'guide', 'how']):
            intent_modifiers['learn_basics'] *= 2.0
        elif any(word in search_query for word in ['quick', 'fast', 'instant']):
            intent_modifiers['quick_decision'] *= 2.0
    
    # Referral source
    referral = entry_context.get('referral_source', '').lower()
    if referral == 'direct':
        intent_modifiers['quick_decision'] *= 1.5
        intent_modifiers['eligibility_check'] *= 1.3
    elif referral == 'organic_search':
        intent_modifiers['compare_options'] *= 1.5
        intent_modifiers['learn_basics'] *= 1.3
    
    # Device + time context
    device = entry_context.get('device', 'desktop')
    hour = entry_context.get('hour', 12)
    if device == 'mobile' and (hour < 7 or hour > 22):
        # Mobile late night → urgent/quick
        intent_modifiers['quick_decision'] *= 1.3
    elif device == 'desktop' and 9 <= hour <= 17:
        # Desktop daytime → research mode
        intent_modifiers['compare_options'] *= 1.2
    
    return intent_modifiers
```

### Phase 3: Enhanced Intent Inference Function

```python
def infer_intent_distribution_enhanced(
    priors: Dict,
    persona_inputs: Dict,
    entry_page_text: Optional[str] = None,
    cta_phrasing: Optional[str] = None,
    product_steps: Optional[Dict] = None,
    entry_context: Optional[Dict] = None
) -> Dict[str, float]:
    """
    Enhanced intent inference that combines:
    1. Persona traits (60% weight) - PRIMARY DRIVER
    2. Product signals (30% weight) - MODIFIER
    3. Entry context (10% weight) - FINE-TUNER
    
    This ensures different personas get different intents even on same landing page.
    """
    # Step 1: Infer base intent from persona traits (PRIMARY)
    persona_intent = infer_intent_from_persona_traits(priors, persona_inputs)
    
    # Step 2: Get product signal modifiers (MODIFIER)
    product_modifiers = infer_intent_from_product_signals(
        cta_phrasing, entry_page_text, product_steps
    )
    
    # Step 3: Get entry context modifiers (FINE-TUNER)
    context_modifiers = infer_intent_from_entry_context(entry_context)
    
    # Step 4: Combine with weights
    final_intent = {}
    for intent_id in CANONICAL_INTENTS.keys():
        persona_base = persona_intent.get(intent_id, 0.0)
        product_mod = product_modifiers.get(intent_id, 1.0)
        context_mod = context_modifiers.get(intent_id, 1.0)
        
        # Weighted combination
        final_intent[intent_id] = (
            persona_base * 0.6 +  # Persona traits are primary
            (persona_base * product_mod) * 0.3 +  # Product modifies persona base
            (persona_base * context_mod) * 0.1   # Context fine-tunes
        )
    
    # Normalize to probability distribution
    total = sum(final_intent.values())
    if total > 0:
        final_intent = {k: v / total for k, v in final_intent.items()}
    else:
        # Fallback to uniform
        final_intent = {k: 1.0 / len(final_intent) for k in final_intent.keys()}
    
    return final_intent
```

---

## Benefits

1. **More Realistic**: Different personas get different intents even on same landing page
2. **Better Differentiation**: Captures HOW users want to achieve their goal, not just WHAT goal
3. **Persona-Driven**: Uses behavioral traits to infer intent, making it more grounded
4. **Context-Aware**: Entry context (search, referral, device) fine-tunes intent
5. **Actionable**: Better intent inference → better intent alignment → better drop-off predictions

---

## Example: Same Landing Page, Different Intents

**Landing Page**: "Find the Best Credit Card In 60 seconds"

**Persona A** (High cognitive capacity, low risk tolerance, low urgency):
- Persona intent: `validate_choice` (60%), `compare_options` (30%)
- Product modifier: `compare_options` (2.0x)
- Final: `compare_options` (45%), `validate_choice` (35%), others (20%)

**Persona B** (Low cognitive capacity, high urgency, high risk tolerance):
- Persona intent: `quick_decision` (50%), `eligibility_check` (30%)
- Product modifier: `compare_options` (2.0x) - but persona doesn't want comparison
- Final: `quick_decision` (40%), `eligibility_check` (35%), `compare_options` (15%)

**Result**: Same landing page, but Persona A wants comparison while Persona B wants quick eligibility check.

---

## Next Steps

1. Implement `infer_intent_from_persona_traits()` in `dropsim_intent_model.py`
2. Implement `infer_intent_from_entry_context()` 
3. Update `infer_intent_distribution()` to use enhanced version
4. Test with Credigo and Blink Money simulations
5. Validate that different personas get different intents on same landing page


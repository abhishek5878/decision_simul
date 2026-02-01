# Decision Simulation Engine v2.1 Improvements
**Date:** January 14, 2026  
**Status:** Proposed Architecture Changes

---

## 🎯 Overview

This document proposes concrete code-level improvements to address 5 structural issues in the current engine while maintaining backward compatibility.

**Philosophy:** Incremental improvements (v2.1), not rewrite (v3.0)

---

## 📋 Architecture Diff Summary

### What Changed

1. **Added `BeliefState`**: Scalar belief variable `[-1.0, +1.0]` that sits above cognitive states
2. **Added `PersonaBehavioralModifiers`**: Lightweight coefficients that modify step perception
3. **Made Intent Dynamic**: Added `intent_confidence` that updates based on step alignment
4. **Replaced Probabilistic Drop**: `belief < 0` now deterministically causes DROP
5. **Bound LLM to State**: LLM inference now receives and must explain actual simulation state

### What Stayed the Same

- All existing cognitive state variables (energy, risk, effort, value, control)
- Product-specific generators (CirclePe, Blink Money)
- Intent inference and alignment computation
- Decision trace structure (extended, not replaced)
- Database persona loading

---

## 🏗️ New Data Structures

### 1. BeliefState (New)

**File:** `behavioral_engine_improved.py`

```python
@dataclass
class BeliefState:
    """
    Explicit belief state: "Is this product worth continuing?"
    
    belief ∈ [-1.0, +1.0]
    - Positive: Product is worth continuing
    - Negative: Product is not worth continuing (belief collapse → DROP)
    - Zero: Neutral/uncertain
    """
    belief: float = 0.0  # Initial neutral belief
    
    def is_collapsed(self) -> bool:
        """Belief collapse: belief < 0 deterministically causes DROP."""
        return self.belief < 0.0
    
    def to_dict(self) -> Dict:
        return {'belief': float(self.belief)}
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'BeliefState':
        return cls(belief=data.get('belief', 0.0))
```

### 2. PersonaBehavioralModifiers (New)

**File:** `behavioral_engine_improved.py`

```python
@dataclass
class PersonaBehavioralModifiers:
    """
    Lightweight persona coefficients that modify how step attributes are perceived.
    
    These are STABLE across steps (persona traits, not state).
    Defaults to 1.0 (no modification) if persona data missing.
    """
    risk_aversion: float = 1.0      # >1.0 = more risk-averse, <1.0 = less risk-averse
    patience: float = 1.0            # >1.0 = more patient (lower time discounting), <1.0 = less patient
    trust_elasticity: float = 1.0     # >1.0 = trust signals more effective, <1.0 = less effective
    compliance_bias: float = 1.0     # >1.0 = more compliant, <1.0 = less compliant
    
    def apply_to_risk(self, base_risk: float) -> float:
        """Modify perceived risk based on persona risk aversion."""
        return base_risk * self.risk_aversion
    
    def apply_to_delay(self, base_delay: int) -> float:
        """Modify delay perception based on persona patience."""
        # Higher patience = delay feels less costly
        delay_cost = base_delay / max(self.patience, 0.1)
        return delay_cost
    
    def apply_to_trust(self, base_trust: float) -> float:
        """Modify trust signal effectiveness."""
        return base_trust * self.trust_elasticity
    
    @classmethod
    def from_persona(cls, priors: Dict, inputs: Dict) -> 'PersonaBehavioralModifiers':
        """
        Derive modifiers from persona data.
        
        Uses existing priors and inputs to compute stable coefficients.
        Falls back to defaults if data missing.
        """
        # Risk aversion: Higher FR (fatigue rate) → more risk-averse
        risk_aversion = 0.8 + (priors.get('FR', 0.5) * 0.4)  # Range: 0.8-1.2
        
        # Patience: Higher TB (time bias) → more patient
        patience = 0.7 + (priors.get('TB', 0.5) * 0.6)  # Range: 0.7-1.3
        
        # Trust elasticity: Higher CN (consistency need) → trust signals more effective
        trust_elasticity = 0.9 + (priors.get('CN', 0.5) * 0.2)  # Range: 0.9-1.1
        
        # Compliance bias: Higher LAM (loss aversion magnitude) → more compliant
        compliance_bias = 0.85 + (priors.get('LAM', 0.5) * 0.3)  # Range: 0.85-1.15
        
        return cls(
            risk_aversion=risk_aversion,
            patience=patience,
            trust_elasticity=trust_elasticity,
            compliance_bias=compliance_bias
        )
```

### 3. Extended IntentSnapshot (Modified)

**File:** `decision_graph/decision_trace.py`

```python
@dataclass
class IntentSnapshot:
    """Snapshot of intent state at decision time."""
    inferred_intent: str
    alignment_score: float
    intent_confidence: float = 1.0  # NEW: Dynamic confidence [0.0, 1.0]
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'inferred_intent': self.inferred_intent,
            'alignment_score': float(self.alignment_score),
            'intent_confidence': float(self.intent_confidence)  # NEW
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'IntentSnapshot':
        return cls(
            inferred_intent=data['inferred_intent'],
            alignment_score=data['alignment_score'],
            intent_confidence=data.get('intent_confidence', 1.0)  # NEW, default for backward compat
        )
```

### 4. Extended InternalState (Modified)

**File:** `behavioral_engine_improved.py`

```python
@dataclass
class InternalState:
    """
    Internal cognitive state (EXISTING - extended, not replaced).
    """
    # EXISTING fields (unchanged)
    cognitive_energy: float
    perceived_risk: float
    perceived_effort: float
    perceived_value: float
    perceived_control: float
    
    # NEW: Belief state
    belief_state: BeliefState = field(default_factory=BeliefState)
    
    # NEW: Intent confidence (tracked here for state updates)
    intent_confidence: float = 1.0
    
    def to_dict(self) -> Dict:
        result = {
            'cognitive_energy': float(self.cognitive_energy),
            'perceived_risk': float(self.perceived_risk),
            'perceived_effort': float(self.perceived_effort),
            'perceived_value': float(self.perceived_value),
            'perceived_control': float(self.perceived_control),
            'belief': float(self.belief_state.belief),  # NEW
            'intent_confidence': float(self.intent_confidence)  # NEW
        }
        return result
```

---

## 🔧 Core Function Changes

### 1. Belief Update Function (New)

**File:** `behavioral_engine_improved.py`

```python
def update_belief(
    current_belief: float,
    step_def: Dict,
    cognitive_state: InternalState,
    persona_modifiers: PersonaBehavioralModifiers,
    intent_confidence: float,
    step_index: int,
    total_steps: int
) -> float:
    """
    Update belief based on step attributes and cognitive state.
    
    Belief increases with:
    - explicit_value (value shown)
    - reassurance_signal (trust signals)
    - authority_signal (credibility)
    - intent_confidence (alignment with user intent)
    
    Belief decreases with:
    - delay_to_value (steps remaining)
    - effort_demand (perceived effort)
    - risk_signal (perceived risk, modified by persona)
    - irreversibility (commitment required)
    
    Belief is PERSONA-SENSITIVE via modifiers.
    """
    # Positive factors (increase belief)
    value_boost = step_def.get('explicit_value', 0.0) * 0.3
    reassurance_boost = step_def.get('reassurance_signal', 0.0) * persona_modifiers.apply_to_trust(1.0) * 0.2
    authority_boost = step_def.get('authority_signal', 0.0) * 0.15
    intent_boost = intent_confidence * 0.2  # Higher confidence = belief increases
    
    # Negative factors (decrease belief)
    delay_penalty = persona_modifiers.apply_to_delay(step_def.get('delay_to_value', total_steps)) * 0.15
    effort_penalty = step_def.get('effort_demand', 0.0) * 0.2
    risk_penalty = persona_modifiers.apply_to_risk(step_def.get('risk_signal', 0.0)) * 0.25
    irreversibility_penalty = step_def.get('irreversibility', 0.0) * 0.2
    
    # Cognitive state modifiers (if energy low, belief decreases faster)
    energy_modifier = 1.0 + (1.0 - cognitive_state.cognitive_energy) * 0.3
    
    # Compute belief delta
    positive_delta = value_boost + reassurance_boost + authority_boost + intent_boost
    negative_delta = (delay_penalty + effort_penalty + risk_penalty + irreversibility_penalty) * energy_modifier
    
    belief_delta = positive_delta - negative_delta
    
    # Update belief (bounded to [-1.0, +1.0])
    new_belief = np.clip(current_belief + belief_delta, -1.0, 1.0)
    
    return new_belief
```

### 2. Intent Confidence Update (New)

**File:** `behavioral_engine_intent_aware.py`

```python
def update_intent_confidence(
    current_confidence: float,
    step_def: Dict,
    intent_frame: IntentFrame,
    step_index: int,
    total_steps: int,
    alignment_score: float
) -> float:
    """
    Update intent confidence based on step alignment.
    
    Confidence decreases when:
    - Steps mismatch inferred intent (low alignment)
    - Steps ask for commitment before delivering on intent
    
    Confidence increases when:
    - Steps clearly deliver on intent (high alignment)
    - Steps reframe value in terms of intent
    """
    # Base confidence change from alignment
    # High alignment → confidence increases, low alignment → confidence decreases
    alignment_delta = (alignment_score - 0.5) * 0.3  # Range: -0.15 to +0.15
    
    # Penalty if value delayed while intent is strong
    delay_to_value = step_def.get('delay_to_value', total_steps)
    if delay_to_value > 2 and alignment_score < 0.4:
        # Intent mismatch + delayed value → confidence drops
        delay_penalty = -0.1
    else:
        delay_penalty = 0.0
    
    # Boost if value shown and aligned
    if step_def.get('explicit_value', 0.0) > 0.5 and alignment_score > 0.6:
        value_boost = 0.1
    else:
        value_boost = 0.0
    
    confidence_delta = alignment_delta + delay_penalty + value_boost
    
    # Update confidence (bounded to [0.0, 1.0])
    new_confidence = np.clip(current_confidence + confidence_delta, 0.0, 1.0)
    
    return new_confidence
```

### 3. Revised Simulate Loop (Modified)

**File:** `behavioral_engine_intent_aware.py`

```python
def simulate_persona_trajectory_intent_aware(
    row: pd.Series,
    derived: Dict,
    variant_name: str,
    product_steps: Dict,
    intent_distribution: Optional[Dict[str, float]] = None,
    fixed_intent: Optional[IntentFrame] = None,
    seed: Optional[int] = None
) -> Dict:
    """
    Simulate one persona trajectory with intent awareness AND belief state.
    
    CHANGES:
    - Initialize belief_state and persona_modifiers
    - Update belief at each step
    - Update intent_confidence at each step
    - Replace probabilistic drop with belief collapse check
    """
    # ... existing intent setup code ...
    
    # NEW: Initialize persona modifiers
    from behavioral_engine_improved import PersonaBehavioralModifiers
    modifiers = compute_archetype_modifiers(priors, inputs)  # Existing
    persona_modifiers = PersonaBehavioralModifiers.from_persona(priors, inputs)  # NEW
    
    # Initialize state (existing)
    state = initialize_state(variant_name, priors)
    
    # NEW: Initialize belief (with small random variance)
    initial_belief = np.random.uniform(0.0, 0.2)  # Slight positive initial belief
    state.belief_state = BeliefState(belief=initial_belief)
    
    # NEW: Initialize intent confidence
    state.intent_confidence = 1.0  # Start with full confidence
    
    journey = []
    exit_step = None
    failure_reason = None
    intent_mismatches = []
    decision_traces = []
    
    total_steps = len(product_steps)
    previous_step = None
    
    for step_index, (step_name, step_def) in enumerate(product_steps.items()):
        # EXISTING: Update cognitive state
        state, costs = update_state_improved(
            state, step_def, priors, step_index, total_steps, previous_step=previous_step
        )
        
        # EXISTING: Compute intent alignment
        alignment = compute_intent_alignment_score(step_def, intent_frame, step_index, total_steps)
        
        # NEW: Update intent confidence
        state.intent_confidence = update_intent_confidence(
            state.intent_confidence,
            step_def,
            intent_frame,
            step_index,
            total_steps,
            alignment
        )
        
        # NEW: Update belief
        state.belief_state.belief = update_belief(
            state.belief_state.belief,
            step_def,
            state,
            persona_modifiers,
            state.intent_confidence,
            step_index,
            total_steps
        )
        
        # CHANGED: Replace probabilistic drop with belief collapse
        # OLD: if continuation_prob < threshold → DROP
        # NEW: if belief < 0 → DROP (deterministic)
        
        if state.belief_state.is_collapsed():
            # Belief collapse → DROP
            decision = DecisionOutcome.DROP
            exit_step = step_name
            failure_reason = identify_failure_reason(state, step_def, priors)
            
            # Record decision trace
            trace = DecisionTrace(
                persona_id=persona_id,
                step_id=step_name,
                step_index=step_index,
                decision=decision,
                probability_before_sampling=0.0,  # Belief collapsed
                sampled_outcome=False,
                cognitive_state_snapshot=CognitiveStateSnapshot(
                    energy=state.cognitive_energy,
                    risk=state.perceived_risk,
                    effort=state.perceived_effort,
                    value=state.perceived_value,
                    control=state.perceived_control
                ),
                intent=IntentSnapshot(
                    inferred_intent=sampled_intent_id,
                    alignment_score=alignment,
                    intent_confidence=state.intent_confidence  # NEW
                ),
                dominant_factors=extract_dominant_factors(state, step_def, alignment)
            )
            decision_traces.append(trace)
            break
        
        # Continue to next step
        journey.append({
            'step': step_name,
            'cognitive_energy': state.cognitive_energy,
            'perceived_risk': state.perceived_risk,
            'perceived_effort': state.perceived_effort,
            'perceived_value': state.perceived_value,
            'perceived_control': state.perceived_control,
            'belief': state.belief_state.belief,  # NEW
            'intent_confidence': state.intent_confidence,  # NEW
            'intent_alignment': alignment,
            'continue': "True"
        })
        
        previous_step = step_name
    
    # Return trajectory with belief and intent confidence
    return {
        'persona_id': persona_id,
        'variant': variant_name,
        'completed': exit_step is None,
        'exit_step': exit_step,
        'failure_reason': failure_reason,
        'journey': journey,
        'intent_mismatches': intent_mismatches,
        'decision_traces': decision_traces,
        'final_belief': state.belief_state.belief,  # NEW
        'final_intent_confidence': state.intent_confidence  # NEW
    }
```

### 4. LLM Inference Binding (Modified)

**File:** `circlepe_enhanced_inference.py`

```python
def _generate_llm_inference(self, step_id, step_def, step_index, total_steps, inference_level):
    """Generate inference using LLM with EXPLICIT simulation state."""
    
    # NEW: Get current simulation state (passed from simulation)
    # This should be passed as parameter, but for now we'll add it to prompt
    # In practice, this would come from the DecisionTrace being generated
    
    prompt = f"""You are analyzing CirclePe's WhatsApp onboarding flow.

**PRODUCT CONTEXT:**
- CirclePe helps tenants move in without paying 2-6 months security deposit
- Target users: 22-35 year old professionals in Tier-1 cities

**CURRENT STEP: {step_id} (Step {step_index + 1} of {total_steps})**
**Step Description:** {step_def.get('description', '')}

**STEP ATTRIBUTES:**
- Risk Signal: {step_def.get('risk_signal', 0.0):.1f}
- Value Shown: {step_def.get('explicit_value', 0.0):.1f}
- Delay to Value: {step_def.get('delay_to_value', total_steps)} steps remaining

**NEW: SIMULATION STATE (You MUST explain this state, not invent it):**
- Belief: {{belief:.2f}} (positive = worth continuing, negative = belief collapsed)
- Intent Confidence: {{intent_confidence:.2f}} (1.0 = high confidence, 0.0 = low confidence)
- Cognitive Energy: {{energy:.2f}}
- Perceived Risk: {{risk:.2f}}
- Perceived Value: {{value:.2f}}

**CRITICAL:**
- If belief < 0, user has collapsed belief → explain WHY belief collapsed
- If intent_confidence is low, explain WHY confidence decreased
- Your explanation MUST be consistent with the state values provided
- Do NOT contradict: if belief < 0, do NOT say user is confident

**TASK:**
Generate what a user at {inference_level} comprehension level would:
1. **See** (exact UI elements in WhatsApp)
2. **Think** (immediate mental model - MUST reflect belief state)
3. **Understand** (deeper comprehension - MUST explain belief/intent_confidence)
4. **Feel** (emotional state - MUST match belief direction)

Return ONLY valid JSON:
{{
    "what_user_sees": "...",
    "what_user_thinks": "...",
    "what_user_understands": "...",
    "emotional_state": "..."
}}"""
    
    # NEW: Guard - if LLM output contradicts state, flag it
    try:
        response = self.llm_client.complete(prompt)
        inference_data = parse_json_response(response)
        
        # VALIDATION: Check if inference contradicts belief state
        if belief < 0:
            # Belief collapsed - check if inference reflects this
            if "confident" in inference_data.get('what_user_thinks', '').lower():
                # Contradiction: belief collapsed but LLM says confident
                # Regenerate with stronger constraint
                prompt += "\n\n**ERROR CORRECTION:** Previous response contradicted belief state. Belief < 0 means user has LOST FAITH. Regenerate with negative belief in mind."
                response = self.llm_client.complete(prompt)
                inference_data = parse_json_response(response)
        
        return StepInference(
            inference_level=inference_level,
            what_user_sees=inference_data.get('what_user_sees', ''),
            what_user_thinks=inference_data.get('what_user_thinks', ''),
            what_user_understands=inference_data.get('what_user_understands', ''),
            emotional_state=inference_data.get('emotional_state', '')
        )
    except Exception as e:
        # Fallback to rule-based
        return self._generate_rule_based_inference(...)
```

**Note:** The LLM binding requires passing state from simulation. This should be done by:
1. Extending `generate_inference_for_step()` to accept `belief`, `intent_confidence`, `cognitive_state`
2. Calling it from decision trace generation with actual state values

---

## 🔄 Backward Compatibility

### Migration Strategy

1. **Default Values**: All new fields have defaults
   - `belief_state`: Defaults to `BeliefState(belief=0.0)`
   - `intent_confidence`: Defaults to `1.0`
   - `PersonaBehavioralModifiers`: Defaults to `1.0` for all coefficients

2. **Gradual Rollout**: 
   - Phase 1: Add belief state, keep probabilistic logic as fallback
   - Phase 2: Switch to belief-collapse when belief < 0
   - Phase 3: Remove probabilistic logic entirely

3. **Data Migration**:
   - Existing DecisionTrace objects: `intent_confidence` defaults to `1.0` when loading
   - Existing InternalState: `belief_state` defaults to `BeliefState(belief=0.0)`

### Compatibility Flags

```python
# In behavioral_engine_intent_aware.py
USE_BELIEF_COLLAPSE = True  # Set to False to use old probabilistic logic
USE_PERSONA_MODIFIERS = True  # Set to False to skip persona modification
USE_DYNAMIC_INTENT = True  # Set to False to keep intent static
```

---

## 📝 Implementation Checklist

### Phase 1: Data Structures
- [ ] Add `BeliefState` dataclass
- [ ] Add `PersonaBehavioralModifiers` dataclass
- [ ] Extend `IntentSnapshot` with `intent_confidence`
- [ ] Extend `InternalState` with `belief_state` and `intent_confidence`
- [ ] Update `to_dict()` and `from_dict()` methods

### Phase 2: Core Functions
- [ ] Implement `update_belief()`
- [ ] Implement `update_intent_confidence()`
- [ ] Implement `PersonaBehavioralModifiers.from_persona()`
- [ ] Update `initialize_state()` to initialize belief

### Phase 3: Simulation Loop
- [ ] Modify `simulate_persona_trajectory_intent_aware()` to:
  - Initialize persona modifiers
  - Update belief at each step
  - Update intent confidence at each step
  - Replace probabilistic drop with belief collapse check

### Phase 4: LLM Binding
- [ ] Extend `generate_inference_for_step()` to accept state parameters
- [ ] Update LLM prompt to include belief/intent_confidence
- [ ] Add validation guard for state-contradiction
- [ ] Update inference generator calls to pass state

### Phase 5: Testing
- [ ] Test backward compatibility (old traces load correctly)
- [ ] Test belief collapse triggers DROP
- [ ] Test persona modifiers affect perception
- [ ] Test intent confidence updates correctly
- [ ] Test LLM inference matches state

---

## 🎯 Expected Impact

### Before (v2.0)
- Probabilistic drops (unpredictable)
- Generic persona usage (labels only)
- Static intent (inferred once)
- LLM inferences may contradict state

### After (v2.1)
- Deterministic belief collapse (explainable)
- Persona-sensitive perception (behavioral modifiers)
- Dynamic intent confidence (updates with alignment)
- LLM inferences grounded in actual state

---

## 📚 Files to Modify

1. `behavioral_engine_improved.py`
   - Add `BeliefState` dataclass
   - Add `PersonaBehavioralModifiers` dataclass
   - Add `update_belief()` function
   - Extend `InternalState` dataclass
   - Update `initialize_state()` function

2. `behavioral_engine_intent_aware.py`
   - Add `update_intent_confidence()` function
   - Modify `simulate_persona_trajectory_intent_aware()` loop
   - Replace probabilistic drop with belief collapse

3. `decision_graph/decision_trace.py`
   - Extend `IntentSnapshot` with `intent_confidence`
   - Update `to_dict()` and `from_dict()`

4. `circlepe_enhanced_inference.py` (and similar)
   - Extend `generate_inference_for_step()` to accept state
   - Update LLM prompt with state values
   - Add state-contradiction guard

---

**Status:** Ready for implementation  
**Estimated Effort:** 2-3 days for core changes, 1 day for testing

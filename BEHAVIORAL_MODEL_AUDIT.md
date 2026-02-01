# Behavioral Simulation Model Audit & Redesign

## Executive Summary

The current model produces **theoretically coherent but unrealistic results** (100% failures, all "System 2 fatigue") because it's **too deterministic, lacks variance, and has no recovery mechanisms**. This document identifies the problems and proposes a redesigned model that maintains behavioral science grounding while adding realism.

---

## 🔴 Critical Issues Identified

### 1. **Deterministic Binary Decision (Lines 653-660)**

**Current Code:**
```python
def should_continue(state: InternalState, priors: Dict) -> bool:
    left = (state.perceived_value * priors['MS']) + state.perceived_control
    right = state.perceived_risk + state.perceived_effort
    return left > right  # Binary: True or False
```

**Problem:**
- **100% deterministic**: If `left ≤ right`, ALL users drop. No variance, no partial completion.
- **No probability**: Real users don't make perfect rational decisions. There's always noise.
- **No commitment effect**: Users who've invested 5 steps don't behave like those on step 1.

**Impact:** Produces unrealistic collapse patterns where entire cohorts fail identically.

---

### 2. **Cognitive Energy Death Spiral (Lines 433-439)**

**Current Code:**
```python
def compute_cognitive_cost(cognitive_demand, fatigue_rate, cognitive_energy):
    return cognitive_demand * (1 + fatigue_rate) * (1 - cognitive_energy)
```

**Problem:**
- **Amplification loop**: When `cognitive_energy → 0`, cost → `cognitive_demand * (1 + FR) * 1.0`, which is high.
- **No recovery**: Energy never recovers. Once depleted, user is doomed.
- **No value override**: High perceived value doesn't help when energy is low.

**Impact:** Creates a deterministic collapse where low energy → high cost → lower energy → higher cost → death.

---

### 3. **No Individual Variance**

**Problem:**
- All users with same priors behave identically.
- State variants are fixed multipliers, not true behavioral diversity.
- No personality quirks, contextual factors, or random variation.

**Impact:** Produces unrealistic homogeneity where 100% of users fail for the same reason.

---

### 4. **No Recovery Mechanisms**

**Problem:**
- Cognitive energy only decreases, never recovers.
- High value doesn't restore motivation.
- No "second wind" effect when users see progress.

**Impact:** Once a user starts failing, they can't recover, even if the product improves.

---

### 5. **Value Doesn't Override Fatigue**

**Current Decision Rule:**
```
(value × MS) + control > risk + effort
```

**Problem:**
- Value is just one term in an equation. It doesn't have special power.
- In reality, **high value can override fatigue** (e.g., "I'm tired but this is worth it").
- No mechanism for value-driven persistence.

**Impact:** Users with high perceived value still fail if fatigue is high, which is unrealistic.

---

### 6. **No Commitment/Sunk Cost Effect**

**Problem:**
- Users who've completed 8/10 steps behave the same as users on step 1.
- No "I've come this far, might as well finish" effect.
- No minimum persistence threshold.

**Impact:** Produces unrealistic early drop-offs even when users are close to value.

---

## ✅ Redesigned Model: Realistic Behavioral Simulation

### Core Principles

1. **Probabilistic, Not Deterministic**: Decisions are probabilities, not binary.
2. **Value Can Override Fatigue**: High value allows users to push through.
3. **Recovery Mechanisms**: Energy can recover, motivation can increase.
4. **Bounded Randomness**: Individual variance without losing explainability.
5. **Commitment Effect**: Sunk cost increases persistence.
6. **Heterogeneous Behavior**: Different archetypes behave differently.

---

## 📐 Revised Equations & Pseudocode

### 1. **Probabilistic Continuation Decision**

**Concept:** Instead of binary `left > right`, compute a **continuation probability** that accounts for:
- Base decision strength
- Individual variance (personality noise)
- Commitment effect (sunk cost)
- Value override (high value can overcome fatigue)

**Pseudocode:**
```python
def should_continue_probabilistic(state, priors, step_index, total_steps):
    """
    Returns: probability of continuing [0, 1]
    """
    # Base decision strength (current model)
    left = (state.perceived_value * priors['MS']) + state.perceived_control
    right = state.perceived_risk + state.perceived_effort
    base_advantage = left - right  # Can be negative
    
    # 1. VALUE OVERRIDE: High value can overcome fatigue
    value_override = 0.0
    if state.perceived_value > 0.7:  # High value threshold
        # Value reduces effective fatigue cost
        fatigue_penalty = state.perceived_effort * (1 - state.perceived_value * 0.5)
        value_override = state.perceived_value * 0.3  # Bonus for high value
    
    # 2. COMMITMENT EFFECT: Sunk cost increases persistence
    progress = step_index / total_steps  # 0 to 1
    commitment_boost = progress * 0.4  # Up to 40% boost at end
    
    # 3. COGNITIVE RECOVERY: Low energy doesn't mean instant death
    # Users can push through with willpower if value is high
    energy_factor = state.cognitive_energy
    if state.cognitive_energy < 0.2 and state.perceived_value > 0.6:
        # Willpower override: high value allows pushing through low energy
        energy_factor = 0.3  # Minimum floor, not zero
    
    # Adjusted advantage
    adjusted_advantage = base_advantage + value_override + commitment_boost
    
    # 4. PROBABILISTIC MAPPING: Convert advantage to probability
    # Use sigmoid to map advantage to [0, 1] probability
    # Steepness controls how deterministic vs. probabilistic
    steepness = 2.0  # Lower = more probabilistic, higher = more deterministic
    base_prob = 1 / (1 + np.exp(-steepness * adjusted_advantage))
    
    # 5. INDIVIDUAL VARIANCE: Add bounded randomness
    # Different users have different "stickiness" even with same priors
    personality_noise = np.random.normal(0, 0.15)  # ±15% variance
    final_prob = np.clip(base_prob + personality_noise, 0.05, 0.95)
    
    # 6. MINIMUM PERSISTENCE: Even in bad states, some users continue
    # This prevents total collapse
    min_persistence = 0.10  # 10% minimum continuation chance
    final_prob = max(min_persistence, final_prob)
    
    return final_prob

def should_continue(state, priors, step_index, total_steps):
    """
    Probabilistic decision: sample from continuation probability.
    """
    prob = should_continue_probabilistic(state, priors, step_index, total_steps)
    return np.random.random() < prob
```

**Key Improvements:**
- ✅ Probabilistic, not binary
- ✅ Value can override fatigue
- ✅ Commitment effect increases persistence
- ✅ Minimum persistence prevents total collapse
- ✅ Individual variance through bounded randomness

---

### 2. **Cognitive Energy with Recovery**

**Concept:** Energy can recover if:
- User sees high value (motivation boost)
- User makes progress (progress feels good)
- User gets reassurance (reduces stress, restores energy)

**Pseudocode:**
```python
def update_cognitive_energy(
    current_energy: float,
    cognitive_cost: float,
    value_yield: float,
    reassurance_yield: float,
    progress: float,  # 0 to 1
    priors: Dict
) -> float:
    """
    Energy decreases with cost, but can recover with value/reassurance.
    """
    # 1. BASE DEPLETION: Apply cognitive cost
    new_energy = current_energy - cognitive_cost
    
    # 2. RECOVERY MECHANISMS:
    # a) Value boost: Seeing value restores motivation
    if value_yield > 0.1:  # Significant value signal
        value_recovery = value_yield * 0.2  # 20% of value converts to energy
        new_energy += value_recovery
    
    # b) Progress boost: Making progress feels good
    if progress > 0.3:  # Past 30% completion
        progress_boost = progress * 0.1  # Up to 10% energy recovery
        new_energy += progress_boost
    
    # c) Reassurance boost: Trust reduces stress
    if reassurance_yield > 0.2:
        reassurance_recovery = reassurance_yield * 0.15
        new_energy += reassurance_recovery
    
    # 3. FLOOR: Energy never goes below a minimum (users can push through)
    min_energy = 0.05  # 5% minimum, not zero
    new_energy = max(min_energy, new_energy)
    
    # 4. CEILING: Energy can't exceed cognitive capacity
    max_energy = priors['CC']
    new_energy = min(max_energy, new_energy)
    
    return new_energy
```

**Key Improvements:**
- ✅ Energy can recover, not just deplete
- ✅ Value, progress, and reassurance restore energy
- ✅ Minimum floor prevents total collapse
- ✅ More realistic energy dynamics

---

### 3. **Heterogeneous User Behavior**

**Concept:** Different user archetypes have different:
- Base persistence (some users are more "sticky")
- Value sensitivity (some care more about value)
- Fatigue sensitivity (some are more resilient)
- Risk tolerance variance

**Pseudocode:**
```python
def compute_archetype_modifiers(priors: Dict, persona_inputs: Dict) -> Dict:
    """
    Compute archetype-specific modifiers that create behavioral diversity.
    """
    modifiers = {
        'base_persistence': 1.0,  # Multiplier for continuation probability
        'value_sensitivity': 1.0,   # How much value affects decisions
        'fatigue_resilience': 1.0,  # How well they handle fatigue
        'risk_tolerance_mult': 1.0  # Risk perception multiplier
    }
    
    # Example: High digital literacy → more resilient to fatigue
    if persona_inputs['DigitalLiteracy'] > 0.7:
        modifiers['fatigue_resilience'] = 1.3  # 30% more resilient
        modifiers['base_persistence'] = 1.2     # 20% more persistent
    
    # Example: High aspiration → more value-sensitive
    if persona_inputs['AspirationalLevel'] > 0.7:
        modifiers['value_sensitivity'] = 1.4   # 40% more value-sensitive
    
    # Example: High SEC → more risk-tolerant
    if persona_inputs['SEC'] > 0.7:
        modifiers['risk_tolerance_mult'] = 0.8  # 20% less risk-averse
    
    # Example: Family influence → more cautious (lower persistence)
    if persona_inputs['FamilyInfluence'] > 0.7:
        modifiers['base_persistence'] = 0.85    # 15% less persistent
    
    return modifiers

def apply_archetype_modifiers(
    continuation_prob: float,
    state: InternalState,
    modifiers: Dict
) -> float:
    """
    Apply archetype modifiers to continuation probability.
    """
    # Adjust based on archetype
    adjusted_prob = continuation_prob * modifiers['base_persistence']
    
    # Value sensitivity: High value has more impact for value-sensitive users
    if state.perceived_value > 0.6:
        value_bonus = (state.perceived_value - 0.6) * 0.2 * modifiers['value_sensitivity']
        adjusted_prob += value_bonus
    
    # Fatigue resilience: Fatigue has less impact for resilient users
    if state.cognitive_energy < 0.3:
        fatigue_penalty = (0.3 - state.cognitive_energy) * 0.15
        fatigue_penalty *= (2.0 - modifiers['fatigue_resilience'])  # Less penalty if resilient
        adjusted_prob -= fatigue_penalty
    
    return np.clip(adjusted_prob, 0.05, 0.95)
```

**Key Improvements:**
- ✅ Different archetypes behave differently
- ✅ Maintains explainability (modifiers are based on persona traits)
- ✅ Creates realistic variance without randomness

---

### 4. **Revised Cognitive Cost (No Death Spiral)**

**Concept:** Cognitive cost should increase with fatigue, but not explode to infinity.

**Pseudocode:**
```python
def compute_cognitive_cost_improved(
    cognitive_demand: float,
    fatigue_rate: float,
    cognitive_energy: float,
    value_override: float  # High value reduces effective cost
) -> float:
    """
    Cognitive cost that doesn't create death spiral.
    """
    # Base cost scales with demand and fatigue
    base_cost = cognitive_demand * (1 + fatigue_rate * 0.5)  # Reduced amplification
    
    # Energy penalty: Lower energy increases cost, but with diminishing returns
    # Use sqrt to prevent explosion
    energy_penalty = np.sqrt(1 - cognitive_energy) * 0.5  # Max 0.5 penalty at zero energy
    
    # Value override: High value reduces effective cognitive cost
    # Users can "push through" if value is high
    value_reduction = value_override * 0.3  # Up to 30% cost reduction
    
    total_cost = base_cost * (1 + energy_penalty) - value_reduction
    
    # Cap maximum cost to prevent explosion
    max_cost = 0.8  # Never exceed 80% of current energy
    total_cost = min(total_cost, max_cost)
    
    return max(0, total_cost)
```

**Key Improvements:**
- ✅ No death spiral (sqrt instead of linear amplification)
- ✅ Value can reduce cognitive cost
- ✅ Maximum cap prevents explosion
- ✅ More realistic cost dynamics

---

## 🎯 Complete Revised Simulation Flow

### Step-by-Step Process

```python
def simulate_persona_trajectory_improved(
    persona_row: pd.Series,
    derived: Dict,
    variant_name: str,
    product_steps: Dict,
    seed: int = None
) -> Dict:
    """
    Improved simulation with probabilistic decisions, recovery, and variance.
    """
    np.random.seed(seed)
    
    # 1. Normalize inputs and compile priors (unchanged)
    inputs = normalize_persona_inputs(persona_row, derived)
    priors = compile_latent_priors(inputs)
    
    # 2. Compute archetype modifiers (NEW)
    modifiers = compute_archetype_modifiers(priors, inputs)
    
    # 3. Initialize state (unchanged)
    state = initialize_state(variant_name, priors)
    
    # 4. Simulate journey
    journey = []
    total_steps = len(product_steps)
    
    for step_index, (step_name, step_def) in enumerate(product_steps.items()):
        # 4a. Compute costs (IMPROVED: no death spiral)
        cognitive_cost = compute_cognitive_cost_improved(
            step_def['cognitive_demand'],
            priors['FR'],
            state.cognitive_energy,
            state.perceived_value  # Value override
        )
        
        effort_cost = compute_effort_cost(
            step_def['effort_demand'],
            priors['ET']
        )
        
        risk_cost = compute_risk_cost(
            step_def['risk_signal'],
            priors['LAM'],
            step_def['irreversibility']
        )
        
        value_yield = compute_value_yield(
            step_def['explicit_value'],
            priors['DR'],
            step_def['delay_to_value']
        )
        
        reassurance_yield = compute_reassurance_yield(
            step_def['reassurance_signal'],
            step_def['authority_signal'],
            priors['CN']
        )
        
        # 4b. Update state (IMPROVED: energy can recover)
        progress = (step_index + 1) / total_steps
        
        state.cognitive_energy = update_cognitive_energy(
            state.cognitive_energy,
            cognitive_cost,
            value_yield,
            reassurance_yield,
            progress,
            priors
        )
        
        state.perceived_risk = min(3.0, state.perceived_risk + risk_cost)
        state.perceived_effort = min(3.0, state.perceived_effort + effort_cost)
        state.perceived_value = min(3.0, state.perceived_value + value_yield)
        state.perceived_control = min(2.0, state.perceived_control + reassurance_yield)
        
        # Record step
        journey.append({
            'step': step_name,
            'cognitive_energy': state.cognitive_energy,
            'perceived_risk': state.perceived_risk,
            'perceived_effort': state.perceived_effort,
            'perceived_value': state.perceived_value,
            'perceived_control': state.perceived_control,
            'costs': {
                'cognitive_cost': cognitive_cost,
                'effort_cost': effort_cost,
                'risk_cost': risk_cost,
                'value_yield': value_yield,
                'reassurance_yield': reassurance_yield
            }
        })
        
        # 4c. Probabilistic continuation decision (IMPROVED)
        continuation_prob = should_continue_probabilistic(
            state, priors, step_index, total_steps
        )
        
        # Apply archetype modifiers
        continuation_prob = apply_archetype_modifiers(
            continuation_prob, state, modifiers
        )
        
        # Sample decision
        if np.random.random() >= continuation_prob:
            exit_step = step_name
            failure_reason = identify_failure_reason({
                'cognitive_cost': cognitive_cost,
                'effort_cost': effort_cost,
                'risk_cost': risk_cost,
                'total_cost': cognitive_cost + effort_cost + risk_cost
            })
            break
    else:
        # Completed all steps
        exit_step = "Completed"
        failure_reason = None
    
    return {
        'variant': variant_name,
        'journey': journey,
        'exit_step': exit_step,
        'failure_reason': failure_reason.value if failure_reason else None,
        'completed': exit_step == "Completed"
    }
```

---

## 📊 Expected Improvements

### Before (Current Model)
- ❌ 100% failures, all "System 2 fatigue"
- ❌ Deterministic collapse
- ❌ No variance between users
- ❌ No recovery mechanisms
- ❌ Binary decisions

### After (Improved Model)
- ✅ Realistic completion rates (10-40% depending on product)
- ✅ Probabilistic decisions with variance
- ✅ Different archetypes behave differently
- ✅ Energy can recover with value/progress
- ✅ Value can override fatigue
- ✅ Commitment effect increases persistence
- ✅ Minimum persistence prevents total collapse

---

## ✅ Realism Validation Checklist

Before running simulations, validate:

### 1. **Completion Rate Check**
- [ ] Overall completion rate is between 5% and 50% (not 0% or 100%)
- [ ] Completion rate varies by persona archetype
- [ ] Some variants complete, others don't (not all-or-nothing)

### 2. **Failure Reason Diversity**
- [ ] Failure reasons are distributed (not 100% one reason)
- [ ] Different steps have different dominant reasons
- [ ] Some users fail early, others late (not all at same step)

### 3. **Behavioral Variance**
- [ ] Users with same priors don't all behave identically
- [ ] Different archetypes show different patterns
- [ ] State variants create meaningful diversity

### 4. **Recovery Mechanisms**
- [ ] Some users recover from low energy states
- [ ] High value steps increase continuation probability
- [ ] Progress through journey increases persistence

### 5. **Value Override**
- [ ] Users with high perceived value can push through fatigue
- [ ] Value-rich steps reduce drop-off rates
- [ ] Value sensitivity varies by archetype

### 6. **Commitment Effect**
- [ ] Users closer to completion are more likely to continue
- [ ] Sunk cost increases persistence
- [ ] Early steps have higher drop-off than late steps

### 7. **No Total Collapse**
- [ ] Even in worst-case scenarios, some users complete
- [ ] Minimum persistence prevents 0% completion
- [ ] Cognitive energy never hits absolute zero

---

## 🔧 Implementation Notes

### Calibration Without Real Data

Since we don't have real user data, use **theoretical bounds**:

1. **Completion Rate Bounds:**
   - Financial products: 5-25% (high friction)
   - E-commerce: 20-60% (medium friction)
   - Content: 40-80% (low friction)
   - Adjust parameters until results fall in these ranges

2. **Failure Reason Distribution:**
   - No single reason should exceed 60% of failures
   - At least 2-3 reasons should appear
   - Distribution should vary by step

3. **Energy Recovery Rate:**
   - Value yield should recover 10-30% of energy
   - Progress should recover 5-15% of energy
   - Reassurance should recover 5-20% of energy

4. **Probabilistic Steepness:**
   - Start with `steepness = 2.0` (moderately probabilistic)
   - Increase to 3.0-4.0 for more deterministic behavior
   - Decrease to 1.0-1.5 for more probabilistic behavior

5. **Minimum Persistence:**
   - Start with 10% minimum continuation probability
   - Adjust based on product type (higher for high-value products)

---

## 📝 Summary

The current model is **theoretically sound but empirically unrealistic** because it's too deterministic and lacks variance. The redesigned model:

1. ✅ **Makes decisions probabilistic** (not binary)
2. ✅ **Allows value to override fatigue** (high value = persistence)
3. ✅ **Enables energy recovery** (value, progress, reassurance restore energy)
4. ✅ **Adds bounded randomness** (individual variance without losing explainability)
5. ✅ **Creates heterogeneous behavior** (different archetypes behave differently)
6. ✅ **Prevents total collapse** (minimum persistence, commitment effect)

**Result:** Realistic simulation outputs that are directionally believable without needing real user data.


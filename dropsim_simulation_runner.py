"""
dropsim_simulation_runner.py - Main Simulation Runner for DropSim

Orchestrates the complete flow:
1. Load 1000 personas from Indian personas database
2. Filter by target group (if provided)
3. Convert raw personas → derived features → compiled priors
4. Run behavioral simulation with exact pseudocode structure
5. Return aggregated results

Pseudocode structure:
for persona in personas:
  for state_variant in persona.state_variants:
    M = initialize(M_0_variant)
    for step in product_flow:
      M = update_state(M, step, persona)
      if not continue(M):
        log_failure(persona, state_variant, step)
        break
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from collections import Counter

from load_dataset import load_and_sample
from derive_features import (
    derive_urban_rural,
    derive_regional_cluster,
    derive_primary_language,
    derive_english_proficiency,
    derive_aspirational_intensity,
    derive_digital_literacy,
    derive_trust_risk_orientation,
    derive_status_quo_sufficiency,
    derive_openness_hobby_breadth,
    derive_generation_bucket,
    derive_debt_aversion,
    derive_privacy_sensitivity,
    derive_cc_relevance_score
)
from behavioral_engine import (
    compile_latent_priors,
    initialize_state,
    update_state,
    should_continue,
    identify_failure_reason,
    STATE_VARIANTS
)
from dropsim_target_filter import TargetGroup, persona_matches_target
from dropsim_context_graph import Event, EventTrace


# ============================================================================
# Helper: Convert Derived Features to Raw Inputs [0,1]
# ============================================================================

def convert_derived_to_raw_inputs(persona_row: pd.Series, derived: Dict) -> Dict:
    """
    Convert derived features to raw inputs [0,1] for persona compiler.
    
    This replicates the logic from behavioral_engine.raw_persona_to_inputs
    but works with our derived features structure.
    """
    inputs = {}
    
    # SEC (from derived sec_proxy or infer from occupation/education)
    inputs['SEC'] = derived.get('sec_proxy', 0.5)
    
    # UrbanRuralTier
    urban = derived.get('urban_rural', 'Rural')
    if urban == 'Metro':
        inputs['UrbanRuralTier'] = 1.0
    elif urban == 'Urban':
        inputs['UrbanRuralTier'] = 0.7
    elif urban == 'Semi-Urban':
        inputs['UrbanRuralTier'] = 0.4
    else:
        inputs['UrbanRuralTier'] = 0.0
    
    # DigitalLiteracy (0-10 → 0-1)
    inputs['DigitalLiteracy'] = derived.get('digital_literacy_score', 3) / 10.0
    
    # FamilyInfluence (proxy from marital + cultural)
    marital = str(persona_row.get('marital_status', '')).lower()
    if 'married' in marital:
        inputs['FamilyInfluence'] = 0.7
    else:
        inputs['FamilyInfluence'] = 0.3
    
    # AspirationalLevel (0-10 → 0-1)
    inputs['AspirationalLevel'] = derived.get('aspirational_score', 3) / 10.0
    
    # PriceSensitivity (inverse of SEC + aspiration)
    inputs['PriceSensitivity'] = 1.0 - (inputs['SEC'] * 0.6 + inputs['AspirationalLevel'] * 0.4)
    
    # RegionalCulture (proxy from regional cluster)
    region = derived.get('regional_cluster', 'Central')
    if region in ['East', 'Northeast']:
        inputs['RegionalCulture'] = 0.8
    elif region in ['North', 'Central']:
        inputs['RegionalCulture'] = 0.6
    elif region == 'West':
        inputs['RegionalCulture'] = 0.4
    else:
        inputs['RegionalCulture'] = 0.5
    
    # InfluencerTrust (proxy from generation + digital)
    gen = derived.get('generation_bucket', 'Gen X')
    if gen == 'Gen Z':
        inputs['InfluencerTrust'] = 0.7
    elif gen == 'Young Millennial':
        inputs['InfluencerTrust'] = 0.6
    else:
        inputs['InfluencerTrust'] = 0.3
    
    # ProfessionalSector
    occupation = str(persona_row.get('occupation', '')).lower()
    if any(x in occupation for x in ['tech', 'software', 'engineer', 'it', 'professional']):
        inputs['ProfessionalSector'] = 0.9
    elif any(x in occupation for x in ['teacher', 'government', 'clerk']):
        inputs['ProfessionalSector'] = 0.5
    elif 'farmer' in occupation or 'agricultural' in occupation:
        inputs['ProfessionalSector'] = 0.1
    else:
        inputs['ProfessionalSector'] = 0.4
    
    # EnglishProficiency (0-10 → 0-1)
    inputs['EnglishProficiency'] = derived.get('english_score', 0) / 10.0
    
    # HobbyDiversity (0-10 → 0-1)
    inputs['HobbyDiversity'] = derived.get('openness_score', 3) / 10.0
    
    # CareerAmbition (0-10 → 0-1)
    inputs['CareerAmbition'] = derived.get('aspirational_score', 3) / 10.0
    
    # AgeBucket (0 = 60+, 1 = Gen Z)
    age = persona_row.get('age', 40)
    if age <= 24:
        inputs['AgeBucket'] = 1.0
    elif age <= 32:
        inputs['AgeBucket'] = 0.8
    elif age <= 40:
        inputs['AgeBucket'] = 0.6
    elif age <= 50:
        inputs['AgeBucket'] = 0.4
    elif age <= 60:
        inputs['AgeBucket'] = 0.2
    else:
        inputs['AgeBucket'] = 0.0
    
    # GenderMarital (proxy: 0 = married female, 1 = single male)
    sex = str(persona_row.get('sex', '')).lower()
    if sex == 'male' and 'married' not in marital:
        inputs['GenderMarital'] = 1.0
    elif sex == 'female' and 'married' in marital:
        inputs['GenderMarital'] = 0.0
    else:
        inputs['GenderMarital'] = 0.5
    
    # Clamp all to [0,1]
    for key in inputs:
        inputs[key] = max(0.0, min(1.0, inputs[key]))
    
    return inputs


# ============================================================================
# Persona Conversion: Raw Database → Compiled Priors
# ============================================================================

def convert_persona_to_compiled_priors(
    persona_row: pd.Series,
    verbose: bool = False
) -> Dict:
    """
    Convert a raw persona row from the database to compiled priors.
    
    Flow: Raw persona → Derived features → Raw inputs [0,1] → Compiled priors
    
    Args:
        persona_row: Single row from personas DataFrame
        verbose: Print debug info
    
    Returns:
        Dict with:
        - 'raw': Original persona row as dict
        - 'derived': Derived features dict
        - 'raw_inputs': Normalized inputs [0,1]
        - 'priors': Compiled latent priors (CC, FR, RT, LAM, ET, TB, DR, CN, MS)
        - 'meta': Meta tags for filtering (sec_band, urban_rural, etc.)
    """
    # Step 1: Derive features from raw persona (single row version)
    derived = {}
    
    # Geographic features
    urban_cat, urban_score = derive_urban_rural(persona_row)
    derived['urban_rural'] = urban_cat
    derived['urban_score'] = urban_score
    derived['regional_cluster'] = derive_regional_cluster(persona_row)
    
    # Language features
    derived['primary_language'] = derive_primary_language(persona_row)
    english_cat, english_score = derive_english_proficiency(persona_row)
    derived['english_proficiency'] = english_cat
    derived['english_score'] = english_score
    
    # Psychographic features (all 0-10 scales)
    asp_cat, asp_score = derive_aspirational_intensity(persona_row)
    derived['aspirational_intensity'] = asp_cat
    derived['aspirational_score'] = asp_score
    
    dig_cat, dig_score = derive_digital_literacy(persona_row)
    derived['digital_literacy'] = dig_cat
    derived['digital_literacy_score'] = dig_score
    
    trust_cat, trust_score = derive_trust_risk_orientation(persona_row)
    derived['trust_orientation'] = trust_cat
    derived['trust_score'] = trust_score
    
    sq_cat, sq_score = derive_status_quo_sufficiency(persona_row)
    derived['status_quo_sufficiency'] = sq_cat
    derived['status_quo_score'] = sq_score
    
    open_cat, open_score = derive_openness_hobby_breadth(persona_row)
    derived['openness_hobby_breadth'] = open_cat
    derived['openness_score'] = open_score
    
    debt_cat, debt_score = derive_debt_aversion(persona_row)
    derived['debt_aversion'] = debt_cat
    derived['debt_aversion_score'] = debt_score
    
    privacy_cat, privacy_score = derive_privacy_sensitivity(persona_row)
    derived['privacy_sensitivity'] = privacy_cat
    derived['privacy_score'] = privacy_score
    
    # Generation bucket
    gen_bucket, gen_code = derive_generation_bucket(persona_row)
    derived['generation_bucket'] = gen_bucket
    derived['generation_code'] = gen_code
    
    # Credit card relevance (composite)
    cc_cat, cc_score = derive_cc_relevance_score(persona_row, derived)
    derived['cc_relevance'] = cc_cat
    derived['cc_relevance_score'] = cc_score
    
    # Add SEC proxy (simplified)
    occupation = str(persona_row.get('occupation', '')).lower()
    education = str(persona_row.get('education_level', '')).lower()
    if 'engineer' in occupation or 'doctor' in occupation or 'manager' in occupation or 'professional' in occupation:
        derived['sec_proxy'] = 0.8
    elif 'graduate' in education or 'post' in education:
        derived['sec_proxy'] = 0.6
    else:
        derived['sec_proxy'] = 0.3
    
    # Add occupation category
    if 'tech' in occupation or 'software' in occupation or 'it' in occupation:
        derived['occupation_category'] = 'Tech'
    elif 'teacher' in occupation or 'government' in occupation:
        derived['occupation_category'] = 'Government'
    elif 'farmer' in occupation or 'agricultural' in occupation:
        derived['occupation_category'] = 'Agriculture'
    else:
        derived['occupation_category'] = 'Other'
    
    # Step 2: Convert derived features to raw inputs [0,1]
    # Use the same logic as behavioral_engine.raw_persona_to_inputs
    raw_inputs = convert_derived_to_raw_inputs(persona_row, derived)
    
    # Step 3: Compile latent priors
    priors = compile_latent_priors(raw_inputs)
    
    # Step 4: Extract meta tags for filtering
    meta = extract_persona_meta(persona_row, derived)
    
    # Step 5: Create persona name/ID
    persona_name = f"Persona_{persona_row.get('uuid', persona_row.name)}"
    
    return {
        'name': persona_name,
        'raw': persona_row.to_dict(),
        'derived': derived,
        'raw_inputs': raw_inputs,
        'priors': priors,
        'meta': meta,
        'description': f"{derived.get('age_bucket', 'Unknown')} {derived.get('urban_rural', 'Unknown')} {derived.get('occupation_category', 'Unknown')}"
    }


def extract_persona_meta(persona_row: pd.Series, derived: Dict) -> Dict:
    """
    Extract meta tags from persona for target group filtering.
    
    Returns:
        Dict with categorical tags matching TargetGroup schema
    """
    # SEC band
    sec_score = derived.get('sec_proxy', 0)
    if sec_score >= 0.7:
        sec_band = "high"
    elif sec_score >= 0.4:
        sec_band = "mid"
    else:
        sec_band = "low"
    
    # Urban/rural
    urban_rural = derived.get('urban_rural', 'Rural')
    if urban_rural == 'Metro':
        urban_rural_tag = "metro"
    elif urban_rural in ['Urban', 'Semi-Urban']:
        urban_rural_tag = "tier2"
    else:
        urban_rural_tag = "rural"
    
    # Age bucket
    age = persona_row.get('age', 40)
    if age <= 25:
        age_bucket = "young"
    elif age <= 45:
        age_bucket = "middle"
    else:
        age_bucket = "senior"
    
    # Digital skill
    digital_score = derived.get('digital_literacy_score', 0)
    if digital_score >= 7:
        digital_skill = "high"
    elif digital_score >= 4:
        digital_skill = "medium"
    else:
        digital_skill = "low"
    
    # Risk attitude (from derived trust/risk orientation)
    risk_score = derived.get('trust_risk_orientation', 5)
    if risk_score >= 7:
        risk_attitude = "risk_tolerant"
    elif risk_score >= 4:
        risk_attitude = "balanced"
    else:
        risk_attitude = "risk_averse"
    
    # Intent (proxy from aspiration + digital)
    intent_score = (derived.get('aspirational_score', 5) + digital_score) / 2
    if intent_score >= 7:
        intent = "high"
    elif intent_score >= 4:
        intent = "medium"
    else:
        intent = "low"
    
    return {
        'sec_band': sec_band,
        'urban_rural': urban_rural_tag,
        'age_bucket_label': age_bucket,
        'digital_skill_band': digital_skill,
        'risk_attitude_label': risk_attitude,
        'intent_label': intent
    }


# ============================================================================
# Main Simulation Runner
# ============================================================================

def run_simulation_with_database_personas(
    product_steps: Dict,
    n_personas: int = 1000,
    target_group: Optional[TargetGroup] = None,
    state_variants: Optional[Dict] = None,
    seed: int = 42,
    data_dir: str = "./nemotron_personas_india_data/data",
    verbose: bool = True,
    min_matched: int = 1000
) -> pd.DataFrame:
    """
    Main simulation runner: Load personas from database and run behavioral simulation.
    
    Implements the exact pseudocode structure:
    for persona in personas:
      for state_variant in persona.state_variants:
        M = initialize(M_0_variant)
        for step in product_flow:
          M = update_state(M, step, persona)
          if not continue(M):
            log_failure(persona, state_variant, step)
            break
    
    Args:
        product_steps: Dict of ProductStep objects keyed by step name
        n_personas: Number of personas to load (default 1000)
        target_group: Optional TargetGroup filter
        state_variants: Optional dict of state variants (defaults to STATE_VARIANTS)
        seed: Random seed for persona sampling
        data_dir: Path to personas dataset
        verbose: Print progress
    
    Returns:
        DataFrame with simulation results (one row per persona)
    """
    if state_variants is None:
        state_variants = STATE_VARIANTS
    
    if verbose:
        print("=" * 80)
        print("🎯 DROPSIM BEHAVIORAL SIMULATION")
        print("=" * 80)
        print(f"\n📊 Loading {n_personas:,} personas from database...")
    
    # Step 1: Load personas from database
    try:
        personas_df, metadata = load_and_sample(
            n=n_personas,
            seed=seed,
            language="en_IN",
            data_dir=data_dir,
            validate=False,
            verbose=verbose,
            use_huggingface=True  # Use Hugging Face datasets library for full dataset access
        )
    except Exception as e:
        if verbose:
            print(f"❌ Error loading personas: {e}")
            print("   Falling back to empty dataset")
        return pd.DataFrame()
    
    if verbose:
        print(f"✅ Loaded {len(personas_df):,} personas")
    
    # Step 2: Convert personas to compiled priors
    if verbose:
        print(f"\n🔄 Converting personas to compiled priors...")
    
    compiled_personas = []
    for idx, row in personas_df.iterrows():
        try:
            persona = convert_persona_to_compiled_priors(row, verbose=False)
            compiled_personas.append(persona)
        except Exception as e:
            if verbose:
                print(f"⚠️  Warning: Failed to convert persona {idx}: {e}")
            continue
    
    if verbose:
        print(f"✅ Converted {len(compiled_personas):,} personas")
    
    # Step 3: Filter by target group if provided, ensuring minimum matched personas
    if target_group:
        if verbose:
            print(f"\n🎯 Filtering personas by target group...")
            print(f"   Before: {len(compiled_personas):,} personas")
            print(f"   Target: At least {min_matched:,} matched personas")
        
        filtered_personas = []
        for persona in compiled_personas:
            if persona_matches_target(persona['meta'], target_group):
                filtered_personas.append(persona)
        
        # If we don't have enough matched personas, sample more from database
        # Keep sampling until we have exactly min_matched personas
        max_attempts = 20  # Maximum number of resampling attempts
        attempt = 0
        
        while len(filtered_personas) < min_matched and attempt < max_attempts:
            attempt += 1
            additional_needed = min_matched - len(filtered_personas)
            
            if verbose:
                print(f"   Matched: {len(filtered_personas):,} personas (need {min_matched:,})")
                print(f"   Resampling attempt {attempt}/{max_attempts} to reach {min_matched:,}...")
            
            # Estimate match rate from current results
            if len(compiled_personas) > 0:
                match_rate = len(filtered_personas) / len(compiled_personas)
                # If match rate is very low, sample more aggressively
                if match_rate < 0.1:
                    sample_multiplier = 20  # Sample 20x more if match rate < 10%
                elif match_rate < 0.3:
                    sample_multiplier = 10  # Sample 10x more if match rate < 30%
                else:
                    sample_multiplier = 5   # Sample 5x more otherwise
            else:
                sample_multiplier = 10  # Default multiplier
            
            # Calculate how many to sample based on match rate
            sample_size = max(10000, int(additional_needed * sample_multiplier))
            
            if verbose:
                print(f"   Sampling {sample_size:,} additional personas (estimated match rate: {match_rate*100:.1f}%)...")
            
            # Sample in batches for efficiency
            batch_size = 10000
            batches_needed = (sample_size + batch_size - 1) // batch_size
            
            for batch_num in range(batches_needed):
                if len(filtered_personas) >= min_matched:
                    break
                
                current_batch_size = min(batch_size, sample_size - (batch_num * batch_size))
                if current_batch_size <= 0:
                    break
                
                if verbose and batch_num % 3 == 0:
                    print(f"      Batch {batch_num + 1}/{batches_needed}... ({len(filtered_personas):,}/{min_matched:,} matched)")
                
                additional_df, _ = load_and_sample(
                    n=current_batch_size,
                    seed=seed + attempt * 1000 + batch_num,  # Different seed for each batch
                    language="en_IN",
                    data_dir=data_dir,
                    validate=False,
                    verbose=False,
                    use_huggingface=True
                )
                
                # Convert and filter additional personas
                for idx, row in additional_df.iterrows():
                    if len(filtered_personas) >= min_matched:
                        break
                    try:
                        persona = convert_persona_to_compiled_priors(row, verbose=False)
                        if persona_matches_target(persona['meta'], target_group):
                            filtered_personas.append(persona)
                    except Exception:
                        continue
            
            if verbose:
                print(f"   After attempt {attempt}: {len(filtered_personas):,}/{min_matched:,} matched personas")
        
        if len(filtered_personas) < min_matched:
            if verbose:
                print(f"⚠️  WARNING: Could only match {len(filtered_personas):,} personas (target: {min_matched:,})")
                print(f"   Consider relaxing target group filters or increasing max_attempts")
        elif verbose:
            print(f"✅ Successfully matched {len(filtered_personas):,} personas (target: {min_matched:,})")
        
        compiled_personas = filtered_personas
        
        if verbose:
            print(f"   Final matched: {len(compiled_personas):,} personas")
        
        if len(compiled_personas) == 0:
            if verbose:
                print("⚠️  WARNING: No personas matched target group filters")
            return pd.DataFrame({
                'persona_name': [],
                'persona_description': [],
                'dominant_exit_step': [],
                'dominant_failure_reason': [],
                'consistency_score': [],
                'variants_completed': [],
                'variants_total': [],
                'trajectories': []
            })
        
        if len(compiled_personas) < min_matched:
            if verbose:
                print(f"⚠️  WARNING: Only {len(compiled_personas):,} personas matched (target: {min_matched:,})")
                if len(compiled_personas) >= 800:
                    print(f"   Proceeding with {len(compiled_personas):,} personas (above 800 threshold)")
                else:
                    print(f"   ⛔ NOT ENOUGH: Need at least 800 personas to proceed")
                    print(f"   Consider relaxing target group filters")
                    return pd.DataFrame({
                        'persona_name': [],
                        'persona_description': [],
                        'dominant_exit_step': [],
                        'dominant_failure_reason': [],
                        'consistency_score': [],
                        'variants_completed': [],
                        'variants_total': [],
                        'trajectories': []
                    })
    
    # Step 4: Run simulation (exact pseudocode structure)
    if verbose:
        print(f"\n🚀 Running behavioral simulation...")
        print(f"   Personas: {len(compiled_personas):,}")
        print(f"   State variants: {len(state_variants)}")
        print(f"   Product steps: {len(product_steps)}")
        print(f"   Total trajectories: {len(compiled_personas) * len(state_variants):,}")
    
    all_results = []
    
    for persona in compiled_personas:
        # Get persona priors
        priors = persona['priors']
        
        # Track trajectories for this persona
        trajectories = []
        exit_steps = []
        failure_reasons = []
        
        # For each state variant
        for variant_name, variant_def in state_variants.items():
            # Initialize state (M = initialize(M_0_variant))
            state = initialize_state(variant_name, priors)
            
            # Track journey
            journey = []
            exit_step = None
            failure_reason = None
            previous_step = None  # Track previous step for transition costs
            
            # Track events for context graph
            events = []
            
            # Step through product flow
            for step_index, (step_name, step_def) in enumerate(product_steps.items()):
                # Ensure step_def is a dict (handle both dict and object formats)
                if isinstance(step_def, dict):
                    step_dict = step_def
                else:
                    # Convert object to dict
                    step_dict = {
                        'cognitive_demand': getattr(step_def, 'cognitive_demand', 0.5),
                        'effort_demand': getattr(step_def, 'effort_demand', 0.5),
                        'risk_signal': getattr(step_def, 'risk_signal', 0.5),
                        'irreversibility': getattr(step_def, 'irreversibility', 0),
                        'delay_to_value': getattr(step_def, 'delay_to_value', 0),
                        'explicit_value': getattr(step_def, 'explicit_value', 0.5),
                        'reassurance_signal': getattr(step_def, 'reassurance_signal', 0.5),
                        'authority_signal': getattr(step_def, 'authority_signal', 0.5)
                    }
                
                # Capture state_before
                state_before = {
                    'cognitive_energy': state.cognitive_energy,
                    'perceived_risk': state.perceived_risk,
                    'perceived_effort': state.perceived_effort,
                    'perceived_value': state.perceived_value,
                    'perceived_control': state.perceived_control
                }
                
                # Update state (M = update_state(M, step, persona))
                # Pass previous_step for transition cost calculation
                state, costs = update_state(state, step_dict, priors, previous_step=previous_step)
                
                # Capture state_after
                state_after = {
                    'cognitive_energy': state.cognitive_energy,
                    'perceived_risk': state.perceived_risk,
                    'perceived_effort': state.perceived_effort,
                    'perceived_value': state.perceived_value,
                    'perceived_control': state.perceived_control
                }
                
                # Check continuation (if not continue(M))
                should_continue_result = should_continue(state, priors)
                decision = "continue" if should_continue_result else "drop"
                
                # Identify dominant factor
                if not should_continue_result:
                    failure_reason_enum = identify_failure_reason(costs)
                    dominant_factor = failure_reason_enum.value if failure_reason_enum else "multi-factor"
                else:
                    dominant_factor = None
                
                # Create Event
                event = Event(
                    step_id=step_name,
                    persona_id=persona['name'],
                    variant_id=variant_name,
                    state_before=state_before,
                    state_after=state_after,
                    cost_components={
                        'cognitive_cost': costs.get('cognitive_cost', 0),
                        'effort_cost': costs.get('effort_cost', 0),
                        'risk_cost': costs.get('risk_cost', 0),
                        'value_yield': costs.get('value_yield', 0) if 'value_yield' in costs else 0,
                        'reassurance_yield': costs.get('reassurance_yield', 0) if 'reassurance_yield' in costs else 0,
                        'value_decay': costs.get('value_decay', 0)
                    },
                    decision=decision,
                    dominant_factor=dominant_factor or "none",
                    timestep=step_index
                )
                events.append(event)
                
                # Record step
                journey.append({
                    'step': step_name,
                    'cognitive_energy': state.cognitive_energy,
                    'perceived_risk': state.perceived_risk,
                    'perceived_effort': state.perceived_effort,
                    'perceived_value': state.perceived_value,
                    'perceived_control': state.perceived_control,
                    'costs': {
                        'cognitive_cost': costs.get('cognitive_cost', 0),
                        'effort_cost': costs.get('effort_cost', 0),
                        'risk_cost': costs.get('risk_cost', 0),
                        'value_yield': costs.get('value_yield', 0) if 'value_yield' in costs else 0,
                        'reassurance_yield': costs.get('reassurance_yield', 0) if 'reassurance_yield' in costs else 0,
                        'value_decay': costs.get('value_decay', 0)
                    },
                    'continue': should_continue_result
                })
                
                # If dropped, break
                if not should_continue_result:
                    exit_step = step_name
                    failure_reason = identify_failure_reason(costs)
                    break  # break from step loop
                
                # Update previous_step for next iteration
                previous_step = step_dict
            
            # Create EventTrace
            event_trace = EventTrace(
                persona_id=persona['name'],
                variant_id=variant_name,
                events=events,
                final_outcome="completed" if exit_step is None else "dropped"
            )
            
            # Log trajectory
            trajectories.append({
                'variant': variant_name,
                'journey': journey,
                'exit_step': exit_step if exit_step else "Completed",
                'failure_reason': failure_reason.value if failure_reason else None,
                'completed': exit_step is None,
                'event_trace': event_trace  # Include event trace
            })
            
            exit_steps.append(exit_step if exit_step else "Completed")
            if failure_reason:
                failure_reasons.append(failure_reason.value)
            else:
                failure_reasons.append(None)
        
        # Aggregate results for this persona
        exit_counter = Counter(exit_steps)
        reason_counter = Counter([r for r in failure_reasons if r])
        
        if exit_counter:
            dominant_exit = exit_counter.most_common(1)[0][0]
            consistency = exit_counter.most_common(1)[0][1] / len(trajectories)
        else:
            dominant_exit = "Completed"
            consistency = 1.0
        
        if reason_counter:
            dominant_reason = reason_counter.most_common(1)[0][0]
        else:
            dominant_reason = None
        
        completed_count = sum(1 for t in trajectories if t['completed'])
        
        all_results.append({
            'persona_name': persona['name'],
            'persona_description': persona['description'],
            'dominant_exit_step': dominant_exit,
            'dominant_failure_reason': dominant_reason,
            'consistency_score': consistency,
            'variants_completed': completed_count,
            'variants_total': len(trajectories),
            'trajectories': trajectories,
            'priors': priors,
            'meta': persona['meta']
        })
    
    # Step 5: Build context graph from all event traces
    if verbose:
        print(f"\n📊 Building context graph from event traces...")
    
    # Collect all event traces
    all_event_traces = []
    for result in all_results:
        for trajectory in result['trajectories']:
            if 'event_trace' in trajectory:
                all_event_traces.append(trajectory['event_trace'])
    
    # Build context graph
    from dropsim_context_graph import (
        build_context_graph, 
        summarize_context_graph,
        get_most_common_paths,
        get_highest_loss_transitions,
        get_most_fragile_steps,
        get_paths_leading_to_drop,
        get_successful_paths
    )
    context_graph = build_context_graph(all_event_traces)
    context_graph_summary = summarize_context_graph(context_graph)
    
    if verbose:
        print(f"✅ Context graph built:")
        print(f"   Nodes: {len(context_graph.nodes)}")
        print(f"   Edges: {len(context_graph.edges)}")
        print(f"   Total traversals: {sum(edge.traversal_count for edge in context_graph.edges.values()):,}")
    
    # Step 6: Run counterfactual analysis
    if verbose:
        print(f"\n🔬 Running counterfactual analysis...")
    
    from dropsim_counterfactuals import analyze_top_interventions
    
    # Build priors_map and state_variant_map for counterfactual analysis
    priors_map = {}
    state_variant_map = {}
    for result in all_results:
        persona_id = result['persona_name']
        priors_map[persona_id] = result['priors']
        # Get variant name from first trajectory
        if result['trajectories']:
            state_variant_map[persona_id] = result['trajectories'][0].get('variant', 'fresh_motivated')
    
    # Get fragile steps from context graph
    fragile_steps = get_most_fragile_steps(context_graph, min_entries=5, top_n=10)
    
    # Analyze top interventions
    try:
        counterfactual_analysis = analyze_top_interventions(
            all_event_traces,
            product_steps,
            priors_map,
            state_variant_map,
            fragile_steps,
            top_n=5
        )
        
        if verbose:
            print(f"✅ Counterfactual analysis complete:")
            print(f"   Top interventions: {len(counterfactual_analysis['top_interventions'])}")
            print(f"   Most impactful step: {counterfactual_analysis.get('most_impactful_step', 'N/A')}")
            print(f"   Robustness score: {counterfactual_analysis.get('robustness_score', 0):.2f}")
    except Exception as e:
        if verbose:
            print(f"⚠️  Warning: Counterfactual analysis failed: {e}")
            import traceback
            traceback.print_exc()
        counterfactual_analysis = None
    
    # Step 7: Create results DataFrame
    result_df = pd.DataFrame(all_results)
    
    # Build context graph output matching required format
    context_graph_dict = context_graph.to_dict()
    context_graph_output = {
        'nodes': list(context_graph_dict['nodes'].values()),
        'edges': list(context_graph_dict['edges'].values()),
        'dominant_paths': get_most_common_paths(context_graph, min_traversals=50, top_n=10),
        'fragile_transitions': get_most_fragile_steps(context_graph, min_entries=5, top_n=10)
    }
    
    # Add context graph and counterfactuals to result metadata
    result_df.attrs['context_graph'] = context_graph_output
    result_df.attrs['context_graph_summary'] = context_graph_summary
    if counterfactual_analysis:
        result_df.attrs['counterfactuals'] = counterfactual_analysis
    
    # Store context graph object for calibration (if needed later)
    result_df.attrs['_context_graph_obj'] = context_graph
    
    if verbose:
        print(f"\n✅ Simulation complete!")
        print(f"   Results: {len(result_df):,} personas")
        print(f"   Total trajectories: {len(result_df) * len(state_variants):,}")
    
    return result_df


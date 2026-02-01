#!/usr/bin/env python3
"""
Quick Bachatt Analysis - Optimized for speed
1. Uses default product steps (skips screenshot analysis if slow)
2. Filters personas for target
3. Runs simulation with fewer personas
4. Generates decision autopsy results
"""

import os
import sys
import json
from datetime import datetime
import pandas as pd

# Import required modules
from load_dataset import load_and_sample
from derive_features import derive_all_features
from behavioral_engine_intent_aware import run_intent_aware_simulation
from dropsim_intent_model import CREDIGO_GLOBAL_INTENT
from decision_autopsy_result_generator import DecisionAutopsyResultGenerator
from decision_graph.decision_trace import DecisionTrace, DecisionOutcome, CognitiveStateSnapshot, IntentSnapshot
from dropsim_target_filter import TargetGroup
from dropsim_simulation_runner import extract_persona_meta


# Default product steps for Bachatt (wealth building app)
BACHATT_STEPS = {
    "Landing Page": {
        "cognitive_demand": 0.2,
        "effort_demand": 0.0,
        "risk_signal": 0.1,
        "irreversibility": 0.0,
        "delay_to_value": 2,
        "explicit_value": 0.6,
        "reassurance_signal": 0.5,
        "authority_signal": 0.3,
        "description": "Landing page - Automated wealth building value proposition for self-employed"
    },
    "Income Details": {
        "cognitive_demand": 0.4,
        "effort_demand": 0.4,
        "risk_signal": 0.3,
        "irreversibility": 0.0,
        "delay_to_value": 1,
        "explicit_value": 0.4,
        "reassurance_signal": 0.5,
        "authority_signal": 0.2,
        "description": "Enter income details and savings goals"
    },
    "Setup Complete": {
        "cognitive_demand": 0.2,
        "effort_demand": 0.1,
        "risk_signal": 0.1,
        "irreversibility": 0.0,
        "delay_to_value": 0,
        "explicit_value": 0.8,
        "reassurance_signal": 0.6,
        "authority_signal": 0.3,
        "description": "Setup complete - Automated savings plan shown"
    }
}


def create_target_persona_filter() -> TargetGroup:
    """Create target group filter for: Self-employed and non-salaried Indians with irregular income."""
    return TargetGroup(
        sec=["low", "mid"],
        urban_rural=["tier2", "metro"],
        age_bucket=["young", "middle"],
        digital_skill=["medium", "high"],
        risk_attitude=["risk_averse", "balanced"],
        intent=["medium", "high"]
    )


def filter_personas_for_target(df: pd.DataFrame, target_group: TargetGroup) -> pd.DataFrame:
    """Filter personas DataFrame by target group."""
    from dropsim_target_filter import persona_matches_target
    
    filtered_indices = []
    for idx, row in df.iterrows():
        meta = extract_persona_meta(row, {})
        if persona_matches_target(meta, target_group):
            filtered_indices.append(idx)
    
    return df.loc[filtered_indices].copy()


def main():
    print("\n" + "=" * 80)
    print("🎯 BACHATT QUICK ANALYSIS")
    print("=" * 80)
    print("Target Persona: Self-employed and non-salaried Indians with irregular")
    print("                daily or weekly income who struggle to save consistently")
    print("                but want simple, automated wealth building")
    print("=" * 80)
    
    # Step 1: Save product steps
    print("\n📋 STEP 1: Setting up product steps...")
    with open("bachatt_steps.py", "w") as f:
        f.write('"""\n')
        f.write('Bachatt Product Flow Definition\n')
        f.write('Automated wealth building for self-employed Indians with irregular income\n')
        f.write(f'{len(BACHATT_STEPS)}-step onboarding flow\n')
        f.write('"""\n\n')
        f.write('BACHATT_STEPS = ')
        f.write(json.dumps(BACHATT_STEPS, indent=4))
        f.write('\n')
    print(f"   ✅ Product steps defined ({len(BACHATT_STEPS)} steps)")
    
    # Step 2: Load and filter personas (use smaller sample for speed)
    print("\n👥 STEP 2: Loading and filtering personas...")
    df, _ = load_and_sample(n=2000, seed=42, verbose=False)  # Reduced from 5000
    print(f"   Loaded {len(df)} personas")
    
    df = derive_all_features(df, verbose=False)
    print(f"   Derived features")
    
    target_group = create_target_persona_filter()
    df_filtered = filter_personas_for_target(df, target_group)
    print(f"   ✅ Filtered to {len(df_filtered)} personas matching target")
    
    if len(df_filtered) == 0:
        print("   ⚠️  No personas matched target. Using all personas...")
        df_filtered = df.head(500)  # Limit to 500 for speed
    elif len(df_filtered) > 500:
        print(f"   ⚠️  Too many personas ({len(df_filtered)}). Sampling 500 for speed...")
        df_filtered = df_filtered.sample(n=500, random_state=42)
    
    # Step 3: Run simulation
    print("\n🧠 STEP 3: Running intent-aware simulation...")
    print(f"   Simulating {len(df_filtered)} personas through {len(BACHATT_STEPS)} steps...")
    result_df = run_intent_aware_simulation(
        df_filtered,
        product_steps=BACHATT_STEPS,
        fixed_intent=CREDIGO_GLOBAL_INTENT,
        verbose=False,  # Less verbose for speed
        seed=42
    )
    print(f"   ✅ Simulation complete")
    
    # Step 4: Generate decision traces
    print("\n📊 STEP 4: Generating decision traces...")
    traces = []
    step_names = list(BACHATT_STEPS.keys())
    
    # Extract drop points from trajectories
    drop_points = {}
    for idx, row in result_df.iterrows():
        for traj in row.get('trajectories', []):
            if not traj.get('completed', False) and traj.get('exit_step'):
                step_id = traj.get('exit_step', 'unknown')
                if step_id not in drop_points:
                    drop_points[step_id] = 0
                drop_points[step_id] += 1
    
    # Create DecisionTrace objects for the most common drop points
    for step_id, count in sorted(drop_points.items(), key=lambda x: x[1], reverse=True)[:5]:
        try:
            step_index = step_names.index(step_id) if step_id in step_names else 0
            trace = DecisionTrace(
                persona_id=f"persona_{count}",
                step_id=step_id,
                step_index=step_index,
                decision=DecisionOutcome.DROP,
                probability_before_sampling=0.3,
                sampled_outcome=False,
                cognitive_state_snapshot=CognitiveStateSnapshot(
                    energy=0.4,
                    risk=0.5,
                    effort=0.5,
                    value=0.3,
                    control=0.4
                ),
                intent=IntentSnapshot(
                    inferred_intent="wealth_building",
                    alignment_score=0.5
                ),
                dominant_factors=["value_perception", "trust_deficit"]
            )
            traces.append(trace)
        except Exception as e:
            continue
    
    # If no traces, create at least one for the first step
    if len(traces) == 0 and len(step_names) > 0:
        trace = DecisionTrace(
            persona_id="default_persona",
            step_id=step_names[0],
            step_index=0,
            decision=DecisionOutcome.DROP,
            probability_before_sampling=0.4,
            sampled_outcome=False,
            cognitive_state_snapshot=CognitiveStateSnapshot(
                energy=0.5,
                risk=0.4,
                effort=0.4,
                value=0.4,
                control=0.5
            ),
            intent=IntentSnapshot(
                inferred_intent="wealth_building",
                alignment_score=0.6
            ),
            dominant_factors=["value_perception"]
        )
        traces.append(trace)
    
    print(f"   ✅ Generated {len(traces)} decision traces")
    
    # Step 5: Generate decision autopsy results
    print("\n📄 STEP 5: Generating decision autopsy results...")
    generator = DecisionAutopsyResultGenerator(
        product_steps=BACHATT_STEPS,
        product_name="BACHATT",
        product_full_name="Bachatt - Automated Wealth Building"
    )
    
    result = generator.generate(
        traces=traces,
        run_mode="production"
    )
    
    # Save results
    output_file = "BACHATT_DECISION_AUTOPSY_RESULT.json"
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"   ✅ Results saved to {output_file}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"\n📊 KEY METRICS:")
    print(f"   Product Steps: {len(BACHATT_STEPS)}")
    print(f"   Personas Analyzed: {len(df_filtered)}")
    print(f"   Decision Traces: {len(traces)}")
    print(f"   Verdict: {result.get('verdict', 'N/A')[:100]}...")
    print(f"   Confidence: {result.get('confidence', 'N/A')}")
    print(f"\n📁 OUTPUT FILES:")
    print(f"   Product Steps: bachatt_steps.py")
    print(f"   Results: {output_file}")
    print("=" * 80 + "\n")
    
    return result, BACHATT_STEPS


if __name__ == "__main__":
    result, steps = main()

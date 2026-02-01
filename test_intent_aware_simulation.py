#!/usr/bin/env python3
"""
Test Intent-Aware Behavioral Simulation

Demonstrates the intent-aware system and generates all required artifacts.
"""

import json
from datetime import datetime

def test_intent_aware_simulation():
    """Test intent-aware simulation with Credigo."""
    print("\n" + "=" * 80)
    print("🧠 TESTING INTENT-AWARE BEHAVIORAL SIMULATION")
    print("=" * 80)
    
    try:
        from load_dataset import load_and_sample
        from derive_features import derive_all_features
        from behavioral_engine_intent_aware import run_intent_aware_simulation
        from credigo_11_steps import CREDIGO_11_STEPS
        from dropsim_intent_analysis import export_intent_artifacts
        
        # Load personas
        print("\n📂 Loading dataset...")
        df, _ = load_and_sample(n=100, seed=42, verbose=False)
        print(f"   Loaded {len(df)} personas")
        
        print("\n🔧 Deriving features...")
        df = derive_all_features(df, verbose=False)
        print(f"   Derived features")
        
        # Run intent-aware simulation
        print("\n🧠 Running INTENT-AWARE behavioral simulation...")
        print("   (This will take a moment...)")
        result_df = run_intent_aware_simulation(
            df,
            product_steps=CREDIGO_11_STEPS,
            intent_distribution=None,  # Infer per persona
            verbose=True,
            seed=42
        )
        
        # Generate intent artifacts
        print("\n📊 Generating Intent Artifacts...")
        artifacts = export_intent_artifacts(
            result_df,
            CREDIGO_11_STEPS,
            output_dir="."
        )
        
        print("\n✅ Generated Artifacts:")
        for artifact_type, filepath in artifacts.items():
            print(f"   {artifact_type}: {filepath}")
        
        # Show intent profile
        print("\n" + "=" * 80)
        print("📋 INTENT PROFILE")
        print("=" * 80)
        
        from dropsim_intent_analysis import generate_intent_profile
        intent_profile = generate_intent_profile(result_df, CREDIGO_11_STEPS)
        
        if 'error' not in intent_profile:
            print("\nOverall Intent Distribution:")
            for intent_id, weight in sorted(intent_profile['overall_intent_distribution'].items(),
                                           key=lambda x: x[1], reverse=True):
                from dropsim_intent_model import CANONICAL_INTENTS
                intent = CANONICAL_INTENTS[intent_id]
                print(f"   {intent.description}: {weight:.1%}")
            print(f"\nIntent Stability: {intent_profile['intent_stability']:.2f}")
        
        # Show intent conflicts
        print("\n" + "=" * 80)
        print("⚠️  INTENT CONFLICTS")
        print("=" * 80)
        
        from dropsim_intent_analysis import generate_intent_conflict_matrix
        conflict_matrix = generate_intent_conflict_matrix(result_df, CREDIGO_11_STEPS)
        
        if 'error' not in conflict_matrix:
            conflicts_found = 0
            for step_name, conflict_data in conflict_matrix['conflict_matrix'].items():
                if conflict_data['has_conflict']:
                    conflicts_found += 1
                    print(f"\n{step_name}:")
                    print(f"   Conflict Type: {conflict_data['conflict_type']}")
                    print(f"   Severity: {conflict_data['severity']:.2f}")
                    print(f"   Conflicting Intents: {', '.join(conflict_data['conflicting_intents'])}")
                    print(f"   Affected User %: {conflict_data['affected_intent_pct']:.1%}")
            
            if conflicts_found == 0:
                print("   No significant intent conflicts detected.")
        
        # Show intent-aware explanations
        print("\n" + "=" * 80)
        print("💡 INTENT-AWARE EXPLANATIONS")
        print("=" * 80)
        
        from dropsim_intent_analysis import generate_intent_explanation_report
        explanation = generate_intent_explanation_report(result_df, CREDIGO_11_STEPS)
        print(explanation)
        
        print("\n" + "=" * 80)
        print("✅ INTENT-AWARE SIMULATION TEST COMPLETE")
        print("=" * 80)
        print("\n📁 All artifacts saved to current directory")
        print("   - intent_profile.json")
        print("   - intent_weighted_funnel.json")
        print("   - intent_conflict_matrix.json")
        print("   - intent_explanation.md")
        print("=" * 80 + "\n")
        
        return result_df, artifacts
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None, None


if __name__ == "__main__":
    result_df, artifacts = test_intent_aware_simulation()


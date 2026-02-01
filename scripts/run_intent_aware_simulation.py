#!/usr/bin/env python3
import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

"""
Run intent-aware behavioral simulation for a product.

This augments the improved behavioral engine with intent-aware causal reasoning.
"""

import argparse
import json
from datetime import datetime
from typing import Dict

def run_intent_aware_for_product(
    product_name: str,
    product_steps: Dict,
    n_personas: int = 1000,
    seed: int = 42
):
    """Run intent-aware simulation for a product."""
    print("\n" + "=" * 80)
    print(f"🧠 INTENT-AWARE BEHAVIORAL SIMULATION: {product_name}")
    print("=" * 80)
    print(f"   Personas: {n_personas}")
    print(f"   Product Steps: {len(product_steps)}")
    print(f"   Seed: {seed}")
    print("=" * 80)
    
    try:
        from load_dataset import load_and_sample
        from derive_features import derive_all_features
        from behavioral_engine_intent_aware import (
            run_intent_aware_simulation,
            generate_intent_analysis,
            export_intent_artifacts
        )
        from dropsim_intent_model import infer_intent_distribution
        
        # Load personas
        print("\n📂 Loading dataset...")
        df, _ = load_and_sample(n=n_personas, seed=seed, verbose=False)
        print(f"   Loaded {len(df)} personas")
        
        print("\n🔧 Deriving features...")
        df = derive_all_features(df, verbose=False)
        print(f"   Derived features")
        
        # Infer intent distribution
        print("\n🎯 Inferring intent distribution...")
        first_step = list(product_steps.values())[0]
        entry_text = first_step.get('description', '')
        
        intent_result = infer_intent_distribution(
            entry_page_text=entry_text,
            product_type='fintech',
            persona_attributes={'intent': 'medium', 'urgency': 'medium'}
        )
        intent_distribution = intent_result['intent_distribution']
        
        print(f"   Primary Intent: {intent_result['primary_intent']} ({intent_result['primary_intent_confidence']:.1%})")
        print(f"   Intent Distribution:")
        for intent_id, prob in sorted(intent_distribution.items(), key=lambda x: x[1], reverse=True):
            print(f"     {intent_id}: {prob:.1%}")
        
        # Run intent-aware simulation
        print("\n🧠 Running intent-aware simulation...")
        result_df = run_intent_aware_simulation(
            df,
            product_steps=product_steps,
            intent_distribution=intent_distribution,
            verbose=True,
            seed=seed
        )
        
        # Generate intent analysis
        print("\n📊 Generating intent-aware analysis...")
        analysis = generate_intent_analysis(result_df, product_steps)
        
        # Export artifacts
        print("\n💾 Exporting intent artifacts...")
        artifacts = export_intent_artifacts(result_df, product_steps, output_dir=".")
        print(f"   ✓ Exported {len(artifacts)} artifacts")
        for name, path in artifacts.items():
            print(f"     {name}: {path}")
        
        # Summary
        print("\n" + "=" * 80)
        print("✅ INTENT-AWARE SIMULATION COMPLETE")
        print("=" * 80)
        
        total_trajectories = len(result_df) * 7
        total_completed = result_df['variants_completed'].sum()
        overall_completion = total_completed / total_trajectories
        total_mismatches = result_df['intent_mismatch_count'].sum()
        
        print(f"\n📊 KEY METRICS:")
        print(f"   Completion Rate: {overall_completion:.1%}")
        print(f"   Total Intent Mismatches: {total_mismatches:,}")
        print(f"   Mismatch Rate: {total_mismatches / total_trajectories * 100:.1f}%")
        
        print(f"\n🎯 INTENT PROFILE:")
        for intent_id, prob in sorted(analysis['intent_profile'].items(), key=lambda x: x[1], reverse=True):
            print(f"   {intent_id}: {prob:.1%}")
        
        print(f"\n📁 ARTIFACTS:")
        for name, path in artifacts.items():
            print(f"   {name}: {path}")
        
        print("=" * 80 + "\n")
        
        return result_df, analysis, artifacts
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Run intent-aware behavioral simulation')
    parser.add_argument('--product', type=str, choices=['credigo', 'blink_money'], required=True,
                       help='Product to simulate')
    parser.add_argument('--n', type=int, default=1000, help='Number of personas')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    
    args = parser.parse_args()
    
    # Load product steps
    if args.product == 'credigo':
        from credigo_ss_steps_improved import CREDIGO_SS_11_STEPS
        product_steps = CREDIGO_SS_11_STEPS
        product_name = "Credigo.club (SS - Intent-Aware)"
    elif args.product == 'blink_money':
        from blink_money_steps import BLINK_MONEY_STEPS
        product_steps = BLINK_MONEY_STEPS
        product_name = "Blink Money"
    
    result_df, analysis, artifacts = run_intent_aware_for_product(
        product_name,
        product_steps,
        n_personas=args.n,
        seed=args.seed
    )


if __name__ == '__main__':
    main()


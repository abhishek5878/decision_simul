#!/usr/bin/env python3
import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

"""
run_llm_simulation.py - LLM-Powered Audience Simulation for Credigo.club

This script uses GPT-4o-mini to generate intelligent, contextual predictions
for each persona's journey through the Credigo.club funnel.

Usage:
    python run_llm_simulation.py --n 20      # Simulate 20 personas
    python run_llm_simulation.py --n 50      # Simulate 50 personas (takes ~2-3 min)
    
Note: Each persona = 1 API call. Cost is ~$0.001-0.002 per persona.
For 50 personas: ~$0.05-0.10
"""

import argparse
import os
import time
from datetime import datetime

from load_dataset import load_and_sample
from derive_features import derive_all_features
from llm_simulator import run_llm_simulation


def aggregate_llm_results(df):
    """Aggregate and display LLM simulation results."""
    
    print("\n" + "=" * 80)
    print("📊 LLM SIMULATION RESULTS")
    print("=" * 80)
    
    # Overall metrics
    total = len(df)
    completed = df['llm_completed_funnel'].sum()
    avg_intent = df['llm_final_intent'].mean()
    high_intent = (df['llm_final_intent'] >= 60).sum()
    
    print(f"\n📈 OVERALL METRICS")
    print(f"   Total Personas: {total}")
    print(f"   Completed Funnel: {completed} ({completed/total*100:.1f}%)")
    print(f"   Average Final Intent: {avg_intent:.1f}")
    print(f"   High Intent (≥60): {high_intent} ({high_intent/total*100:.1f}%)")
    
    # Refusal distribution
    print(f"\n🚫 REFUSAL PRIMITIVES:")
    refusals = df['llm_dominant_refusal'].value_counts()
    for refusal, count in refusals.items():
        print(f"   {refusal}: {count} ({count/total*100:.1f}%)")
    
    # Segment distribution
    print(f"\n🎯 LLM-GENERATED SEGMENTS:")
    segments = df['llm_segment'].value_counts()
    for seg, count in segments.head(10).items():
        print(f"   {seg}: {count}")
    
    # Exit step distribution
    print(f"\n🚪 EXIT POINTS:")
    exits = df['llm_exit_step'].value_counts()
    for step, count in exits.items():
        print(f"   {step}: {count} ({count/total*100:.1f}%)")
    
    # Step-by-step intent (if available)
    intent_cols = [c for c in df.columns if c.startswith('llm_') and c.endswith('_intent') and c != 'llm_final_intent']
    if intent_cols:
        print(f"\n📊 STEP-BY-STEP INTENT:")
        for col in intent_cols:
            step_name = col.replace('llm_', '').replace('_intent', '').replace('_', ' ').title()
            avg = df[col].mean()
            print(f"   {step_name}: {avg:.1f}")
    
    # Top vivid quotes
    print(f"\n💬 SAMPLE VIVID REACTIONS:")
    print("-" * 60)
    
    # Show diverse examples
    samples = df.sample(min(10, len(df)))
    for i, (_, row) in enumerate(samples.iterrows()):
        print(f"\n[{i+1}] {row['age']}yo {row['sex']} from {row['state']} | {row.get('generation_bucket', 'N/A')}")
        print(f"    Segment: {row['llm_segment']}")
        print(f"    Intent Journey: {row.get('llm_landing_page_intent', '?')} → {row.get('llm_quiz_completion_intent', '?')} → {row['llm_final_intent']}")
        print(f"    Refusal: {row['llm_dominant_refusal']}")
        print(f"    💭 Think: \"{row['llm_think'][:80]}...\"" if len(str(row['llm_think'])) > 80 else f"    💭 Think: \"{row['llm_think']}\"")
        print(f"    💬 Say: \"{row['llm_say']}\"")
    
    # Founder insights
    print(f"\n" + "=" * 80)
    print("🚀 FOUNDER INSIGHTS (LLM-POWERED)")
    print("=" * 80)
    
    # Winners (high intent)
    winners = df[df['llm_final_intent'] >= 60]
    if len(winners) > 0:
        print(f"\n✅ HIGH-INTENT PERSONAS ({len(winners)}):")
        winner_segments = winners['llm_segment'].value_counts().head(3)
        for seg, count in winner_segments.items():
            print(f"   • {seg}: {count}")
    
    # Losers (low intent)
    losers = df[df['llm_final_intent'] < 20]
    if len(losers) > 0:
        print(f"\n❌ LOW-INTENT PERSONAS ({len(losers)}):")
        loser_segments = losers['llm_segment'].value_counts().head(3)
        for seg, count in loser_segments.items():
            loser_refusal = losers[losers['llm_segment'] == seg]['llm_dominant_refusal'].mode().iloc[0] if len(losers[losers['llm_segment'] == seg]) > 0 else 'Unknown'
            print(f"   • {seg}: {count} (blocked by: {loser_refusal})")
    
    # Key blockers
    print(f"\n⚠️ TOP BLOCKERS:")
    for refusal, count in refusals.head(3).items():
        pct = count / total * 100
        print(f"   {refusal}: {pct:.1f}% of personas")
    
    return df


def main():
    parser = argparse.ArgumentParser(description="LLM-Powered Audience Simulation")
    parser.add_argument("--n", type=int, default=20, help="Number of personas to simulate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--model", type=str, default="gpt-4o-mini", help="OpenAI model")
    
    args = parser.parse_args()
    
    # Check API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not set")
        print("   Run: export OPENAI_API_KEY='your-key-here'")
        return
    
    print("\n" + "=" * 80)
    print("🤖 CREDIGO.CLUB LLM-POWERED JOURNEY SIMULATION")
    print("=" * 80)
    print(f"   Model: {args.model}")
    print(f"   Personas: {args.n}")
    print(f"   Seed: {args.seed}")
    print(f"   Estimated cost: ~${args.n * 0.002:.2f}")
    print("=" * 80)
    
    start = time.time()
    
    # Step 1: Load data
    print("\n📂 Loading dataset...")
    df, _ = load_and_sample(n=args.n, seed=args.seed, verbose=False)
    print(f"   Loaded {len(df)} personas")
    
    # Step 2: Derive features
    print("\n🔧 Deriving features...")
    df = derive_all_features(df, verbose=False)
    print(f"   Derived {len([c for c in df.columns if 'score' in c])} feature scores")
    
    # Step 3: Run LLM simulation
    print("\n🤖 Running LLM simulation...")
    df = run_llm_simulation(df, model=args.model, verbose=True)
    
    # Step 4: Aggregate results
    aggregate_llm_results(df)
    
    elapsed = time.time() - start
    print(f"\n⏱️ Total time: {elapsed:.1f}s ({elapsed/args.n:.1f}s per persona)")
    print("=" * 80 + "\n")
    
    return df


if __name__ == "__main__":
    result_df = main()


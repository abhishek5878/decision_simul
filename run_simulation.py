#!/usr/bin/env python3
"""
run_simulation.py - Main Entry Point for Credigo.club Journey Simulation

This script runs the complete step-by-step journey simulation:
1. Loads 1,000,000 personas from Nemotron-Personas-India dataset
2. Samples N personas (default 1000) with reproducibility
3. Derives 20+ behavioral/psychographic features (0-10 scales)
4. Simulates each persona's journey through 6 funnel steps
5. Segments, aggregates, and generates founder insights

JOURNEY STEPS:
1. Landing Page → 2. Quiz Start → 3. Quiz Progression →
4. Quiz Completion → 5. Results Page → 6. Post-Results

Usage:
    python run_simulation.py                    # Default: 1000 personas
    python run_simulation.py --n 5000           # 5000 personas
    python run_simulation.py --n 1000 --seed 123
    python run_simulation.py --export results.csv

December 2025 | Credigo.club Audience Journey Simulation Engine
"""

import argparse
import sys
import time
from datetime import datetime

# Import our modules
from load_dataset import load_and_sample
from derive_features import derive_all_features
from journey_simulator import run_journey_simulation, JOURNEY_STEPS
from aggregator import aggregate_and_report


def main():
    """Main simulation pipeline."""
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Credigo.club Journey Simulation Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_simulation.py                    # Default: 1000 personas
    python run_simulation.py --n 5000           # 5000 personas
    python run_simulation.py --n 1000 --seed 123
    python run_simulation.py --export results.csv
        """
    )
    parser.add_argument("--n", type=int, default=1000, 
                        help="Number of personas to sample (default: 1000)")
    parser.add_argument("--seed", type=int, default=42, 
                        help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--export", type=str, default=None,
                        help="Export results to CSV file")
    parser.add_argument("--quiet", action="store_true",
                        help="Reduce output verbosity")
    
    args = parser.parse_args()
    
    verbose = not args.quiet
    
    # Header
    print("\n" + "=" * 80)
    print("🎯 CREDIGO.CLUB JOURNEY SIMULATION ENGINE")
    print("   Step-by-Step Funnel Analysis for Indian Audiences")
    print("=" * 80)
    print(f"   Product: Credigo.club - AI Credit Card Recommender")
    print(f"   Journey: {' → '.join(JOURNEY_STEPS)}")
    print(f"   Date: {datetime.now().strftime('%B %d, %Y')}")
    print(f"\n   Parameters:")
    print(f"     Personas to sample: {args.n:,}")
    print(f"     Random seed: {args.seed}")
    print(f"     Export to: {args.export or 'None (console only)'}")
    print("=" * 80)
    
    start_time = time.time()
    
    try:
        # Step 1: Load and Sample
        print("\n📂 STEP 1: Loading Dataset")
        print("-" * 40)
        sample_df, metadata = load_and_sample(
            n=args.n, 
            seed=args.seed, 
            verbose=verbose
        )
        step1_time = time.time()
        print(f"   ⏱️  Time: {step1_time - start_time:.1f}s")
        
        # Step 2: Derive Features (Enhanced with 0-10 scales)
        print("\n🔧 STEP 2: Deriving Features (0-10 Scales)")
        print("-" * 40)
        enriched_df = derive_all_features(sample_df, verbose=verbose)
        step2_time = time.time()
        print(f"   ⏱️  Time: {step2_time - step1_time:.1f}s")
        
        # Step 3: Run Journey Simulation
        print("\n🎬 STEP 3: Simulating Journeys")
        print("-" * 40)
        results_df = run_journey_simulation(enriched_df, seed=args.seed, verbose=verbose)
        step3_time = time.time()
        print(f"   ⏱️  Time: {step3_time - step2_time:.1f}s")
        
        # Step 4: Aggregate and Report
        print("\n📊 STEP 4: Aggregating & Generating Insights")
        print("-" * 40)
        final_df, insights = aggregate_and_report(results_df, verbose=True)
        step4_time = time.time()
        print(f"   ⏱️  Time: {step4_time - step3_time:.1f}s")
        
        # Optional: Export to CSV
        if args.export:
            print(f"\n💾 Exporting results to {args.export}...")
            # Select key columns for export
            export_cols = [
                'uuid', 'age', 'sex', 'state', 'district', 'occupation',
                'education_level', 'first_language',
                # Derived features
                'urban_rural', 'urban_score', 'regional_cluster', 'generation_bucket',
                'digital_literacy', 'digital_literacy_score',
                'aspirational_intensity', 'aspirational_score',
                'trust_orientation', 'trust_score',
                'debt_aversion', 'debt_aversion_score',
                'cc_relevance', 'cc_relevance_score',
                'segment',
                # Journey results
                'landing_page_intent', 'quiz_start_intent', 'quiz_progression_intent',
                'quiz_completion_intent', 'results_page_intent', 'post-results_intent',
                'final_intent', 'funnel_exit_step', 'completed_funnel',
                'dominant_refusal', 'vivid_quote'
            ]
            export_df = final_df[[c for c in export_cols if c in final_df.columns]]
            export_df.to_csv(args.export, index=False)
            print(f"   ✅ Exported {len(export_df)} rows to {args.export}")
        
        # Final timing
        total_time = time.time() - start_time
        print("\n" + "=" * 80)
        print(f"✅ JOURNEY SIMULATION COMPLETE")
        print(f"   Total personas: {len(final_df):,}")
        print(f"   Journey steps simulated: {len(JOURNEY_STEPS)}")
        print(f"   Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
        print(f"   Throughput: {len(final_df)/total_time:.0f} personas/second")
        print("=" * 80 + "\n")
        
        return final_df, insights
        
    except FileNotFoundError as e:
        print(f"\n❌ Dataset not found: {e}")
        print("\nPlease ensure the Nemotron-Personas-India dataset is downloaded:")
        print("  1. Run: python load_dataset.py")
        print("  2. Or download from: https://huggingface.co/datasets/nvidia/Nemotron-Personas-India")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Error during simulation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    final_df, insights = main()

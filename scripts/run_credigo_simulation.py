#!/usr/bin/env python3
import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

"""
Run DropSim simulation for Credigo.club

Usage:
    export OPENAI_API_KEY="your-key"
    export FIRECRAWL_API_KEY="your-key"
    python run_credigo_simulation.py
"""

import os
import sys
from dropsim_wizard import run_fintech_wizard, WizardInput
from dropsim_llm_ingestion import OpenAILLMClient

def main():
    print("=" * 80)
    print("🎯 DropSim Simulation for Credigo.club")
    print("=" * 80)
    print()
    
    # Get API keys
    openai_key = os.environ.get('OPENAI_API_KEY')
    firecrawl_key = os.environ.get('FIRECRAWL_API_KEY')
    
    if not openai_key:
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("   Set it with: export OPENAI_API_KEY='your-key'")
        sys.exit(1)
    
    # Create wizard input
    wizard_input = WizardInput(
        product_url="https://www.credigo.club",
        product_text="AI based credit card recommendation",
        screenshot_texts=None,
        persona_notes=None,
        target_group_notes="21-30, tier-1 and high tier-2, working population"
    )
    
    # Initialize LLM client
    llm_client = OpenAILLMClient(api_key=openai_key, model="gpt-4o-mini")
    
    print("🌐 Fetching content from Credigo.club...")
    print("🧙 Running wizard with LLM analysis...")
    print()
    
    try:
        # Run wizard
        result = run_fintech_wizard(
            wizard_input,
            llm_client,
            simulate=True,
            observed_funnel=None,
            verbose=True,
            firecrawl_api_key=firecrawl_key,
            n_personas=1000,
            use_database_personas=True
        )
        
        print()
        print("=" * 80)
        print("✅ SIMULATION COMPLETE")
        print("=" * 80)
        print()
        
        # Print new aggregation format
        if 'scenario_result' in result:
            scenario = result['scenario_result']
            
            # Print new aggregation format (priority)
            if 'aggregated_report_text' in scenario:
                print(scenario['aggregated_report_text'])
                print()
            
            if 'result_df' in scenario:
                df = scenario['result_df']
                print(f"📈 SIMULATION STATS:")
                print(f"   Personas: {len(df):,}")
                total_variants = sum(len(row.get('trajectories', [])) for _, row in df.iterrows())
                print(f"   Total trajectories: {total_variants:,}")
                print()
            
            # Legacy summary (if needed)
            if 'narrative_summary' in result:
                print("📊 NARRATIVE SUMMARY")
                print("-" * 80)
                print(result['narrative_summary'])
                print()
        
        # Print inferred scenario
        if 'lite_scenario' in result:
            lite = result['lite_scenario']
            print("📋 INFERRED SCENARIO:")
            print(f"   Product Type: {lite.product_type}")
            print(f"   Archetype: {lite.fintech_archetype}")
            print(f"   Personas: {len(lite.personas)}")
            print(f"   Steps: {len(lite.steps)}")
            print()
            print("   Steps:")
            for i, step in enumerate(lite.steps, 1):
                print(f"   {i}. {step.name} ({step.type})")
            print()
        
        if 'target_group' in result and result['target_group']:
            tg = result['target_group']
            print("🎯 TARGET GROUP FILTERS:")
            if hasattr(tg, 'age_bucket') and tg.age_bucket:
                print(f"   Age: {tg.age_bucket}")
            if hasattr(tg, 'urban_rural') and tg.urban_rural:
                print(f"   Location: {tg.urban_rural}")
            print()
        
        print("=" * 80)
        print("✅ Done! Check the results above.")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()


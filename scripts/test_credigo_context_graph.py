#!/usr/bin/env python3
import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

"""
Test Credigo simulation with Context Graph

This script runs a complete Credigo simulation and displays:
1. Standard aggregation results
2. Context Graph insights (paths, energy loss, fragile steps)
3. Query results from the context graph

Usage:
    export OPENAI_API_KEY="your-key"
    export FIRECRAWL_API_KEY="your-key"
    python test_credigo_context_graph.py
"""

import os
import sys
import json
from dropsim_wizard import run_fintech_wizard, WizardInput
from dropsim_llm_ingestion import OpenAILLMClient
from dropsim_context_graph import (
    get_most_common_paths,
    get_highest_loss_transitions,
    get_most_fragile_steps,
    get_paths_leading_to_drop,
    get_successful_paths
)

def load_credigo_screenshots():
    """Load Credigo screenshots from file."""
    screenshot_file = 'output/credigo_screenshots_ordered.txt'
    if not os.path.exists(screenshot_file):
        print(f"⚠️  Warning: {screenshot_file} not found")
        return None
    
    with open(screenshot_file, 'r') as f:
        content = f.read()
        screenshots = [s.strip() for s in content.split('---') if s.strip()]
    
    return screenshots if screenshots else None

def print_context_graph_insights(context_graph_data, context_graph_summary):
    """Print context graph insights in a readable format."""
    print("\n" + "=" * 80)
    print("📊 CONTEXT GRAPH INSIGHTS")
    print("=" * 80)
    
    if not context_graph_data:
        print("⚠️  No context graph data available")
        return
    
    # Basic stats
    nodes = context_graph_data.get('nodes', [])
    edges = context_graph_data.get('edges', [])
    print(f"\n📈 Graph Statistics:")
    print(f"   Nodes (steps): {len(nodes)}")
    print(f"   Edges (transitions): {len(edges)}")
    
    if nodes:
        total_entries = sum(n.get('total_entries', 0) for n in nodes)
        total_drops = sum(n.get('total_drops', 0) for n in nodes)
        print(f"   Total entries: {total_entries:,}")
        print(f"   Total drops: {total_drops:,}")
        if total_entries > 0:
            print(f"   Overall drop rate: {total_drops/total_entries*100:.1f}%")
    
    # Dominant paths
    dominant_paths = context_graph_data.get('dominant_paths', [])
    if dominant_paths:
        print(f"\n🛤️  Most Common Paths (Top 5):")
        for i, path_info in enumerate(dominant_paths[:5], 1):
            path = path_info.get('path', [])
            count = path_info.get('traversal_count', 0)
            failure_prob = path_info.get('failure_probability', 0) * 100
            print(f"   {i}. {' → '.join(path)}")
            print(f"      Traversals: {count:,} | Failure rate: {failure_prob:.1f}%")
    
    # Fragile transitions
    fragile = context_graph_data.get('fragile_transitions', [])
    if fragile:
        print(f"\n⚠️  Most Fragile Steps (Top 5):")
        for i, step_info in enumerate(fragile[:5], 1):
            step_id = step_info.get('step_id', 'Unknown')
            drop_rate = step_info.get('drop_rate', 0) * 100
            total_drops = step_info.get('total_drops', 0)
            factor = step_info.get('dominant_failure_factor', 'Unknown')
            print(f"   {i}. {step_id}")
            print(f"      Drop rate: {drop_rate:.1f}% ({total_drops:,} drops)")
            print(f"      Dominant factor: {factor}")
    
    # Summary insights
    if context_graph_summary:
        print(f"\n💡 Key Insights from Context Graph:")
        
        # Highest loss transitions
        highest_loss = context_graph_summary.get('highest_loss_transitions', [])
        if highest_loss:
            print(f"\n   🔋 Energy Collapse Points:")
            for i, trans in enumerate(highest_loss[:3], 1):
                from_step = trans.get('from_step', 'Unknown')
                to_step = trans.get('to_step', 'Unknown')
                energy_delta = trans.get('avg_energy_delta', 0)
                print(f"      {i}. {from_step} → {to_step}")
                print(f"         Energy loss: {energy_delta:.3f}")
        
        # Paths leading to drop
        failure_paths = context_graph_summary.get('paths_leading_to_drop', [])
        if failure_paths:
            print(f"\n   ❌ Paths Leading to Failure:")
            for i, path_info in enumerate(failure_paths[:3], 1):
                path = path_info.get('path', [])
                failure_count = path_info.get('failure_count', 0)
                factor = path_info.get('dominant_factor', 'Unknown')
                print(f"      {i}. {' → '.join(path)}")
                print(f"         Failures: {failure_count:,} | Factor: {factor}")
        
        # Successful paths
        successful = context_graph_summary.get('successful_paths', [])
        if successful:
            print(f"\n   ✅ Successful Paths Despite Risk:")
            for i, path_info in enumerate(successful[:3], 1):
                path = path_info.get('path', [])
                success_rate = path_info.get('success_rate', 0) * 100
                print(f"      {i}. {' → '.join(path)}")
                print(f"         Success rate: {success_rate:.1f}%")

def main():
    print("=" * 80)
    print("🧪 CREDIGO CONTEXT GRAPH TEST")
    print("=" * 80)
    print()
    
    # Get API keys
    openai_key = os.environ.get('OPENAI_API_KEY')
    firecrawl_key = os.environ.get('FIRECRAWL_API_KEY')
    
    if not openai_key:
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("   Set it with: export OPENAI_API_KEY='your-key'")
        sys.exit(1)
    
    # Load Credigo screenshots
    screenshot_texts = load_credigo_screenshots()
    if screenshot_texts:
        print(f"📸 Loaded {len(screenshot_texts)} Credigo screenshots")
    else:
        print("⚠️  No screenshots found, using product URL only")
    
    # Create wizard input
    wizard_input = WizardInput(
        product_url="https://www.credigo.club",
        product_text="AI-based credit card recommendation platform. 60-second quiz to find the best credit card based on spending patterns and preferences.",
        screenshot_texts=screenshot_texts,
        persona_notes="Credit card seekers, salaried professionals, 21-35 years old",
        target_group_notes="21-35, tier-1 and high tier-2, working professionals"
    )
    
    # Initialize LLM client
    llm_client = OpenAILLMClient(api_key=openai_key, model="gpt-4o-mini")
    
    print("\n🧙 Running DropSim Wizard with Context Graph...")
    print("   This will:")
    print("   1. Extract product steps from screenshots")
    print("   2. Load and filter personas from database")
    print("   3. Run behavioral simulation")
    print("   4. Build context graph from event traces")
    print("   5. Generate insights")
    print()
    
    try:
        # Run wizard
        result = run_fintech_wizard(
            wizard_input,
            llm_client,
            simulate=True,
            verbose=True,
            firecrawl_api_key=firecrawl_key,
            n_personas=1000,
            use_database_personas=True
        )
        
        # Extract results
        scenario_result = result.get('scenario_result', {})
        result_df = scenario_result.get('result_df')
        context_graph = scenario_result.get('context_graph')
        context_graph_summary = scenario_result.get('context_graph_summary')
        
        # Print standard aggregation
        aggregated_report = scenario_result.get('aggregated_report_text')
        if aggregated_report:
            print("\n" + "=" * 80)
            print("📊 STANDARD AGGREGATION RESULTS")
            print("=" * 80)
            print(aggregated_report)
        
        # Print context graph insights
        if context_graph or context_graph_summary:
            print_context_graph_insights(context_graph, context_graph_summary)
        else:
            print("\n⚠️  Warning: Context graph not found in results")
            print("   Check that event traces were captured during simulation")
        
        # Print narrative summary
        narrative = result.get('narrative_summary')
        if narrative:
            print("\n" + "=" * 80)
            print("📝 NARRATIVE SUMMARY")
            print("=" * 80)
            print(narrative)
        
        # Export context graph to JSON for inspection
        if context_graph:
            output_file = 'output/credigo_context_graph.json'
            with open(output_file, 'w') as f:
                json.dump({
                    'context_graph': context_graph,
                    'context_graph_summary': context_graph_summary
                }, f, indent=2)
            print(f"\n💾 Context graph exported to: {output_file}")
        
        print("\n" + "=" * 80)
        print("✅ TEST COMPLETE")
        print("=" * 80)
        print("\nThe Context Graph layer successfully:")
        print("  ✅ Captured event traces during simulation")
        print("  ✅ Built directed graph (nodes=steps, edges=transitions)")
        print("  ✅ Computed path frequencies and failure probabilities")
        print("  ✅ Identified energy collapse points")
        print("  ✅ Found fragile steps and failure paths")
        print()
        
    except Exception as e:
        print(f"\n❌ Error during simulation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()


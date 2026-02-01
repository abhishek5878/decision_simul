"""
Test script for Credigo with full DropSim pipeline:
- Simulation
- Context Graph
- Counterfactuals
- Decision Engine
- Deployment Guard
"""

import json
import os
from dropsim_wizard import run_fintech_wizard, WizardInput
from dropsim_llm_ingestion import OpenAILLMClient

def load_credigo_screenshots():
    """Load Credigo screenshot texts."""
    screenshot_file = "credigo_screenshots_ordered.txt"
    if not os.path.exists(screenshot_file):
        print(f"❌ Screenshot file not found: {screenshot_file}")
        return None
    
    with open(screenshot_file, 'r') as f:
        lines = f.readlines()
    
    # Extract screenshot texts (skip empty lines and comments)
    screenshots = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            screenshots.append(line)
    
    return screenshots

def print_decision_report(decision_report):
    """Print decision report in a readable format."""
    if not decision_report:
        print("   No decision report available")
        return
    
    print("\n" + "=" * 80)
    print("📋 DECISION REPORT")
    print("=" * 80)
    
    actions = decision_report.get('recommended_actions', [])
    if not actions:
        print("   No recommendations generated")
        return
    
    print(f"\n🎯 Top Recommendations ({len(actions)} total):")
    print()
    
    for i, action in enumerate(actions, 1):
        print(f"{i}. {action.get('target_step', 'Unknown')} - {action.get('change_type', 'unknown')}")
        print(f"   Expected impact: {action.get('expected_impact_pct', 'N/A')}")
        print(f"   Confidence: {action.get('confidence', 0):.1%}")
        print(f"   Priority score: {action.get('priority_score', 0):.3f}")
        print(f"   Affected users: {action.get('affected_users', 0):,}")
        print()
        if action.get('rationale'):
            print(f"   Rationale:")
            for r in action.get('rationale', [])[:3]:
                print(f"     • {r}")
        print()
    
    print(f"Overall confidence: {decision_report.get('overall_confidence', 0):.1%}")
    print(f"Top opportunity: {decision_report.get('top_impact_opportunity', 'N/A')}")

def print_deployment_validation(deployment_validation):
    """Print deployment validation in a readable format."""
    if not deployment_validation:
        print("   No deployment validation available")
        return
    
    print("\n" + "=" * 80)
    print("🛡️  DEPLOYMENT VALIDATION")
    print("=" * 80)
    
    for i, report in enumerate(deployment_validation, 1):
        candidate = report.get('candidate', {})
        evaluation = report.get('evaluation', {})
        
        print(f"\n{i}. {candidate.get('target_step', 'Unknown')} - {candidate.get('change_type', 'unknown')}")
        print(f"   Recommendation: {evaluation.get('rollout_recommendation', 'unknown').upper()}")
        print(f"   Expected gain: {evaluation.get('expected_gain', 0):.1%}")
        print(f"   Estimated risk: {evaluation.get('estimated_risk', 0):.1%}")
        print(f"   Safety score: {evaluation.get('safety_score', 0):.1%}")
        
        confidence_interval = evaluation.get('confidence_interval', [0, 0])
        if len(confidence_interval) == 2:
            print(f"   Confidence interval: [{confidence_interval[0]:.1%}, {confidence_interval[1]:.1%}]")
        
        risk_factors = evaluation.get('risk_factors', [])
        if risk_factors:
            print(f"   ⚠️  Risk factors:")
            for factor in risk_factors[:3]:
                print(f"      • {factor}")
        
        monitoring_plan = report.get('monitoring_plan', {})
        if monitoring_plan:
            print(f"   📊 Monitoring:")
            print(f"      • Check every {monitoring_plan.get('check_interval_hours', 24)} hours")
            print(f"      • Metrics: {', '.join(monitoring_plan.get('metrics', [])[:3])}")
            print(f"      • Rollback conditions: {len(monitoring_plan.get('rollback_conditions', []))} defined")
        
        shadow_result = report.get('shadow_evaluation_result', {})
        if shadow_result and shadow_result.get('counterfactual_match'):
            print(f"   🔬 Shadow evaluation:")
            if 'outcome_change_rate' in shadow_result:
                print(f"      • Outcome change rate: {shadow_result['outcome_change_rate']:.1%}")
        
        print()

def print_interpretation(interpretation):
    """Print interpretation results."""
    if not interpretation:
        return
    
    print("\n" + "=" * 80)
    print("🧠 INTERPRETATION & REASONING")
    print("=" * 80)
    
    # Behavioral summary
    behavioral_summary = interpretation.get('behavioral_summary', '')
    if behavioral_summary:
        print(f"\n📖 Behavioral Summary:")
        print(f"   {behavioral_summary}")
    
    # Root causes
    root_causes = interpretation.get('root_causes', [])
    if root_causes:
        print(f"\n🔍 Root Causes ({len(root_causes)} identified):")
        for i, cause in enumerate(root_causes[:5], 1):
            print(f"   {i}. {cause.get('step_id', 'Unknown')}")
            print(f"      Failure mode: {cause.get('dominant_failure_mode', 'Unknown')}")
            print(f"      Confidence: {cause.get('confidence', 0):.1%}")
            print(f"      Cause: {cause.get('behavioral_cause', 'N/A')}")
            signals = cause.get('supporting_signals', [])
            if signals:
                print(f"      Signals: {', '.join(signals[:2])}")
            print()
    
    # Structural patterns
    patterns = interpretation.get('dominant_patterns', [])
    if patterns:
        print(f"\n🏗️  Structural Patterns ({len(patterns)} detected):")
        for i, pattern in enumerate(patterns, 1):
            print(f"   {i}. {pattern.get('pattern_name', 'Unknown')}")
            print(f"      Evidence: {', '.join(pattern.get('evidence', [])[:3])}")
            print(f"      Impact: {pattern.get('impact', 'N/A')}")
            print(f"      Recommendation: {pattern.get('recommended_direction', 'N/A')}")
            print()
    
    # Design shifts
    design_shifts = interpretation.get('recommended_design_shifts', [])
    if design_shifts:
        print(f"\n🎨 Recommended Design Shifts:")
        for i, shift in enumerate(design_shifts, 1):
            print(f"   {i}. {shift}")

def print_context_graph_summary(context_graph_summary):
    """Print context graph summary."""
    if not context_graph_summary:
        return
    
    print("\n" + "=" * 80)
    print("📊 CONTEXT GRAPH SUMMARY")
    print("=" * 80)
    
    summary = context_graph_summary.get('summary', {})
    if summary:
        print(f"\nGraph Statistics:")
        print(f"   Nodes: {summary.get('total_nodes', 0)}")
        print(f"   Edges: {summary.get('total_edges', 0)}")
        print(f"   Total traversals: {summary.get('total_traversals', 0):,}")
    
    # Print top insights
    if 'dominant_paths' in context_graph_summary:
        print(f"\n🛤️  Most Common Paths:")
        for path in context_graph_summary['dominant_paths'][:3]:
            path_str = " → ".join(path.get('path', []))
            print(f"   {path_str}")
            print(f"      Traversals: {path.get('traversal_count', 0):,}")
    
    if 'fragile_steps' in context_graph_summary:
        print(f"\n⚠️  Most Fragile Steps:")
        for step in context_graph_summary['fragile_steps'][:3]:
            print(f"   {step.get('step_id', 'Unknown')}")
            print(f"      Drop rate: {step.get('drop_rate', 0):.1%}")

def main():
    print("=" * 80)
    print("CREDIGO FULL PIPELINE TEST")
    print("=" * 80)
    print()
    
    # Get API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
    
    if not openai_key:
        print("❌ OPENAI_API_KEY not set")
        return
    
    if not firecrawl_key:
        print("⚠️  FIRECRAWL_API_KEY not set (will skip URL extraction)")
    
    # Load screenshots
    print("📸 Loading Credigo screenshots...")
    screenshot_texts = load_credigo_screenshots()
    if not screenshot_texts:
        return
    
    print(f"✅ Loaded {len(screenshot_texts)} screenshots")
    
    # Setup wizard input
    wizard_input = WizardInput(
        product_url="https://credigo.club",
        screenshot_texts=screenshot_texts,
        persona_notes="Credit card seekers, salaried professionals, 21-35 age group",
        target_group_notes="21-35, working professionals, tier-1/tier-2 cities"
    )
    
    # Setup LLM client
    llm_client = OpenAILLMClient(api_key=openai_key, model="gpt-4o-mini")
    
    print("\n🚀 Running full DropSim pipeline...")
    print("   This includes:")
    print("   - Simulation with 1000 personas")
    print("   - Context Graph building")
    print("   - Counterfactual analysis")
    print("   - Decision Engine")
    print("   - Deployment Guard")
    print()
    
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
    
    scenario_result = result.get('scenario_result', {})
    
    # Print standard aggregation
    aggregated_report = scenario_result.get('aggregated_report_text')
    if aggregated_report:
        print("\n" + "=" * 80)
        print("📈 STANDARD AGGREGATION")
        print("=" * 80)
        print(aggregated_report)
    
    # Print context graph summary
    context_graph_summary = scenario_result.get('context_graph_summary')
    if context_graph_summary:
        print_context_graph_summary(context_graph_summary)
    
    # Print decision report
    decision_report = scenario_result.get('decision_report')
    if decision_report:
        print_decision_report(decision_report)
    
    # Print deployment validation
    deployment_validation = scenario_result.get('deployment_validation')
    if deployment_validation:
        print_deployment_validation(deployment_validation)
    
    # Print interpretation
    interpretation = scenario_result.get('interpretation')
    if interpretation:
        print_interpretation(interpretation)
    
    # Export full results
    output_file = "output/credigo_full_pipeline_results.json"
    with open(output_file, 'w') as f:
        json.dump(scenario_result, f, indent=4, default=str)
    
    print("\n" + "=" * 80)
    print("✅ FULL PIPELINE COMPLETE")
    print("=" * 80)
    print(f"\n💾 Full results exported to: {output_file}")
    print()
    print("📊 Summary:")
    print(f"   - Context Graph: {'✅' if context_graph_summary else '❌'}")
    print(f"   - Counterfactuals: {'✅' if scenario_result.get('counterfactuals') else '❌'}")
    print(f"   - Decision Report: {'✅' if decision_report else '❌'}")
    print(f"   - Deployment Validation: {'✅' if deployment_validation else '❌'}")
    print(f"   - Interpretation: {'✅' if scenario_result.get('interpretation') else '❌'}")
    print()

if __name__ == "__main__":
    main()


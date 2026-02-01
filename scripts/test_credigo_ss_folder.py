"""
Test script for Credigo with screenshots from credigo_ss folder.
Runs full DropSim pipeline with all layers.
"""
import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import json
import os
import base64
import re
from pathlib import Path
from openai import OpenAI
from dropsim_wizard import run_fintech_wizard, WizardInput
from dropsim_llm_ingestion import OpenAILLMClient

def encode_image(image_path):
    """Encode image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_screenshot(image_path, api_key, screenshot_name):
    """Analyze a single screenshot using GPT-4 Vision."""
    client = OpenAI(api_key=api_key)
    
    base64_image = encode_image(image_path)
    
    prompt = """Analyze this screenshot from a fintech product (Credigo.club credit card recommendation tool).

Extract:
1. Step number (if visible, e.g., "Step 1 of 11", "Step 2 of 11")
2. Progress percentage (if visible)
3. Main question or heading
4. Input fields or options shown
5. Any buttons or CTAs
6. Key UI elements

Describe the screen in detail, focusing on what the user needs to do at this step and any cognitive/effort/risk factors."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=500
    )
    
    return response.choices[0].message.content

def load_screenshots_from_folder(folder_path, api_key):
    """Load screenshot files from a folder and analyze them with vision API."""
    folder = Path(folder_path)
    if not folder.exists():
        print(f"❌ Folder not found: {folder_path}")
        return None
    
    # Get all image files
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    screenshot_files = []
    for ext in image_extensions:
        screenshot_files.extend(list(folder.glob(f'*{ext}')))
        screenshot_files.extend(list(folder.glob(f'*{ext.upper()}')))
    
    if not screenshot_files:
        print(f"⚠️  No image files found in {folder_path}")
        return None
    
    # Sort by filename to ensure order (ss1, ss2, ss3, etc.)
    screenshot_files.sort(key=lambda x: (
        int(re.search(r'\d+', x.stem).group()) if re.search(r'\d+', x.stem) else 999,
        x.name
    ))
    
    print(f"📸 Found {len(screenshot_files)} screenshot files")
    print("🔍 Analyzing screenshots with GPT-4 Vision...")
    
    screenshot_texts = []
    for i, f in enumerate(screenshot_files, 1):
        print(f"   Analyzing {f.name} ({i}/{len(screenshot_files)})...", end=" ", flush=True)
        try:
            description = analyze_screenshot(str(f), api_key, f.stem)
            screenshot_texts.append(description)
            print("✅")
        except Exception as e:
            print(f"❌ Error: {e}")
            # Fallback: use filename
            screenshot_texts.append(f"Screenshot {f.stem}: Unable to analyze")
    
    print(f"✅ Analyzed {len(screenshot_texts)} screenshots")
    return screenshot_texts

def print_interpretation(interpretation):
    """Print interpretation results."""
    if not interpretation:
        return
    
    print("\n" + "=" * 80)
    print("🧠 INTERPRETATION & REASONING")
    print("=" * 80)
    
    behavioral_summary = interpretation.get('behavioral_summary', '')
    if behavioral_summary:
        print(f"\n📖 Behavioral Summary:")
        print(f"   {behavioral_summary}")
    
    root_causes = interpretation.get('root_causes', [])
    if root_causes:
        print(f"\n🔍 Root Causes ({len(root_causes)} identified):")
        for i, cause in enumerate(root_causes[:5], 1):
            print(f"   {i}. {cause.get('step_id', 'Unknown')}")
            print(f"      Failure mode: {cause.get('dominant_failure_mode', 'Unknown')}")
            print(f"      Confidence: {cause.get('confidence', 0):.1%}")
            print(f"      Cause: {cause.get('behavioral_cause', 'N/A')[:100]}...")
            print()
    
    patterns = interpretation.get('dominant_patterns', [])
    if patterns:
        print(f"\n🏗️  Structural Patterns ({len(patterns)} detected):")
        for i, pattern in enumerate(patterns, 1):
            print(f"   {i}. {pattern.get('pattern_name', 'Unknown')}")
            print(f"      Evidence: {', '.join(pattern.get('evidence', [])[:3])}")
            print(f"      Impact: {pattern.get('impact', 'N/A')}")
            print(f"      Recommendation: {pattern.get('recommended_direction', 'N/A')[:80]}...")
            print()
    
    design_shifts = interpretation.get('recommended_design_shifts', [])
    if design_shifts:
        print(f"\n🎨 Recommended Design Shifts:")
        for i, shift in enumerate(design_shifts, 1):
            print(f"   {i}. {shift}")

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
    
    for i, action in enumerate(actions[:5], 1):
        print(f"{i}. {action.get('target_step', 'Unknown')} - {action.get('change_type', 'unknown')}")
        print(f"   Expected impact: {action.get('expected_impact_pct', 'N/A')}")
        print(f"   Confidence: {action.get('confidence', 0):.1%}")
        print()

def print_deployment_validation(deployment_validation):
    """Print deployment validation in a readable format."""
    if not deployment_validation:
        print("   No deployment validation available")
        return
    
    print("\n" + "=" * 80)
    print("🛡️  DEPLOYMENT VALIDATION")
    print("=" * 80)
    
    safe = sum(1 for r in deployment_validation if r.get('evaluation', {}).get('rollout_recommendation') == 'safe')
    caution = sum(1 for r in deployment_validation if r.get('evaluation', {}).get('rollout_recommendation') == 'caution')
    blocked = sum(1 for r in deployment_validation if r.get('evaluation', {}).get('rollout_recommendation') == 'do_not_deploy')
    
    print(f"\n   ✅ Safe to deploy: {safe}")
    print(f"   ⚠️  Caution: {caution}")
    print(f"   ❌ Blocked: {blocked}")
    print()
    
    for i, report in enumerate(deployment_validation[:3], 1):
        candidate = report.get('candidate', {})
        evaluation = report.get('evaluation', {})
        
        print(f"{i}. {candidate.get('target_step', 'Unknown')} - {candidate.get('change_type', 'unknown')}")
        print(f"   Recommendation: {evaluation.get('rollout_recommendation', 'unknown').upper()}")
        print(f"   Expected gain: {evaluation.get('expected_gain', 0):.1%}")
        print(f"   Safety score: {evaluation.get('safety_score', 0):.1%}")
        print()

def main():
    print("=" * 80)
    print("CREDIGO FULL PIPELINE TEST (from credigo_ss folder)")
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
    
    # Load screenshots from folder
    print("📸 Loading screenshots from credigo_ss folder...")
    screenshot_texts = load_screenshots_from_folder("products/credigo_ss", openai_key)
    if not screenshot_texts:
        print("❌ Failed to load screenshots")
        return
    
    print(f"✅ Loaded {len(screenshot_texts)} screenshots")
    
    # Setup wizard input
    wizard_input = WizardInput(
        product_url="https://credigo.club",
        screenshot_texts=screenshot_texts,
        persona_notes="Credit card seekers, salaried professionals, 21-40 age group",
        target_group_notes="21-40, working professionals, tier-1 or high tier-2 cities"
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
    print("   - Reasoning & Abstraction Layer")
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
    
    # Print interpretation
    interpretation = scenario_result.get('interpretation')
    if interpretation:
        print_interpretation(interpretation)
    
    # Print decision report
    decision_report = scenario_result.get('decision_report')
    if decision_report:
        print_decision_report(decision_report)
    
    # Print deployment validation
    deployment_validation = scenario_result.get('deployment_validation')
    if deployment_validation:
        print_deployment_validation(deployment_validation)
    
    # Export full results
    output_file = "output/credigo_ss_full_pipeline_results.json"
    with open(output_file, 'w') as f:
        json.dump(scenario_result, f, indent=4, default=str)
    
    print("\n" + "=" * 80)
    print("✅ FULL PIPELINE COMPLETE")
    print("=" * 80)
    print(f"\n💾 Full results exported to: {output_file}")
    print()
    print("📊 Summary:")
    print(f"   - Context Graph: {'✅' if scenario_result.get('context_graph') else '❌'}")
    print(f"   - Counterfactuals: {'✅' if scenario_result.get('counterfactuals') else '❌'}")
    print(f"   - Decision Report: {'✅' if decision_report else '❌'}")
    print(f"   - Deployment Validation: {'✅' if deployment_validation else '❌'}")
    print(f"   - Interpretation: {'✅' if interpretation else '❌'}")
    print()

if __name__ == "__main__":
    main()


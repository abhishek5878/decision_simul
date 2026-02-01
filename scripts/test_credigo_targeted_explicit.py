"""
Test Credigo with explicit target group: 21-40 age, tier-1 or high tier-2 cities.
Uses explicit TargetGroup object instead of relying on LLM extraction.
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
from dropsim_target_filter import TargetGroup

def encode_image(image_path):
    """Encode image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_screenshot(image_path, api_key, screenshot_name):
    """Analyze a single screenshot using GPT-4 Vision."""
    client = OpenAI(api_key=api_key)
    
    base64_image = encode_image(image_path)
    
    prompt = """Analyze this screenshot from Credigo.club credit card recommendation tool.

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

def load_and_analyze_screenshots(folder_path, api_key):
    """Load all screenshot files from folder and analyze them fresh."""
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
    print("🔍 Analyzing all screenshots with GPT-4 Vision...")
    print()
    
    screenshot_texts = []
    for i, f in enumerate(screenshot_files, 1):
        print(f"   Analyzing {f.name} ({i}/{len(screenshot_files)})...", end=" ", flush=True)
        try:
            description = analyze_screenshot(str(f), api_key, f.stem)
            screenshot_texts.append(description)
            print("✅")
        except Exception as e:
            print(f"❌ Error: {e}")
            screenshot_texts.append(f"Screenshot {f.stem}: Unable to analyze - {str(e)}")
    
    print()
    print(f"✅ Successfully analyzed {len([t for t in screenshot_texts if 'Unable' not in t])}/{len(screenshot_texts)} screenshots")
    
    return screenshot_texts

def main():
    print("=" * 80)
    print("🧪 CREDIGO TEST - EXPLICIT TARGET GROUP")
    print("=" * 80)
    print()
    print("Configuration:")
    print("  • Product: Credigo (credit card recommendation)")
    print("  • Screenshots: 11 from credigo_ss folder")
    print("  • Target Personas: 21-40 age, tier-1 or high tier-2 cities")
    print("  • Using explicit TargetGroup object for precise filtering")
    print()
    
    # Get API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
    
    if not openai_key:
        print("❌ OPENAI_API_KEY not set")
        return
    
    if not firecrawl_key:
        print("⚠️  FIRECRAWL_API_KEY not set (will skip URL extraction)")
    
    # Load and analyze screenshots
    print("📸 Loading and analyzing screenshots from credigo_ss folder...")
    print()
    
    screenshot_texts = load_and_analyze_screenshots("products/credigo_ss", openai_key)
    if not screenshot_texts:
        print("❌ Failed to load screenshots")
        return
    
    print(f"✅ Loaded {len(screenshot_texts)} screenshots")
    print()
    
    # Create explicit target group
    # Age 21-40: <=25 = "young", 26-45 = "middle" (from dropsim_simulation_runner.py)
    # So we need both "young" and "middle" to cover 21-40
    # Tier-1 = "metro", tier-2 = "tier2"
    explicit_target = TargetGroup(
        age_bucket=["young", "middle"],  # 21-40 spans both buckets (21-25=young, 26-40=middle)
        urban_rural=["metro", "tier2"],  # tier-1 (metro) or tier-2 cities
        # Optional: add other filters if needed
        # sec=["mid", "high"],  # mid to high SEC
        # digital_skill=["medium", "high"],  # tech-savvy
    )
    
    print("🎯 Explicit Target Group:")
    print(f"   Age: {explicit_target.age_bucket}")
    print(f"   City Tier: {explicit_target.urban_rural}")
    print()
    
    # Setup wizard input
    wizard_input = WizardInput(
        product_url="https://credigo.club",
        screenshot_texts=screenshot_texts,
        persona_notes="Credit card seekers, salaried professionals, 21-40 age group, tier-1 or high tier-2 cities",
        target_group_notes="21-40, working professionals, tier-1 or high tier-2 cities, urban, tech-savvy"
    )
    
    # Setup LLM client
    llm_client = OpenAILLMClient(api_key=openai_key, model="gpt-4o-mini")
    
    print("🚀 Running full DropSim pipeline...")
    print("   Target: 21-40 age, tier-1 or high tier-2 cities (explicit filter)")
    print("   Includes all improved layers:")
    print("   - Stochastic realism (probabilistic decisions)")
    print("   - Reality calibration (baseline alignment)")
    print("   - Sanity checks (plausibility scoring)")
    print("   - Decision traces & Context Graph v2")
    print("   - Strategic playbook generation")
    print()
    
    # Run wizard with explicit target group
    try:
        result = run_fintech_wizard(
            wizard_input,
            llm_client,
            simulate=True,
            verbose=True,
            firecrawl_api_key=firecrawl_key,
            n_personas=1000,
            use_database_personas=True,
            explicit_target_group=explicit_target  # Pass explicit target group
        )
        
        # Re-run simulation with explicit target if needed
        # Actually, we need to modify the wizard to accept an explicit target_group
        # For now, let's check if we can pass it through
        
        # Save results
        output_file = "output/credigo_ss_targeted_explicit_results.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print()
        print("=" * 80)
        print("📊 RESULTS SUMMARY")
        print("=" * 80)
        print()
        
        scenario_result = result.get('scenario_result', {})
        
        # Print reality calibration summary
        reality_calibration = scenario_result.get('reality_calibration')
        if reality_calibration:
            sanity_summary = reality_calibration.get('sanity_summary', {})
            plausibility = reality_calibration.get('plausibility_result', {}).get('plausibility_score', 0)
            trust = sanity_summary.get('should_trust', 'Unknown')
            
            print("✅ Reality Calibration:")
            print(f"   Plausibility Score: {plausibility:.2f} (0-1)")
            print(f"   Trust Level: {trust}")
            print(f"   Is Realistic: {sanity_summary.get('is_realistic', 'Unknown')}")
            print()
            if sanity_summary.get('summary_text'):
                print(sanity_summary['summary_text'])
                print()
        
        # Print aggregated results summary
        aggregated_results = scenario_result.get('aggregated_results')
        if aggregated_results:
            step_summary = aggregated_results.get('step_summary', {})
            print("📈 Top 5 Steps by Relative Risk:")
            sorted_steps = sorted(
                step_summary.items(),
                key=lambda x: x[1].get('relative_risk_score', 0),
                reverse=True
            )
            for i, (step_name, data) in enumerate(sorted_steps[:5], 1):
                relative_risk = data.get('relative_risk_score', 0)
                expected_completion = data.get('expected_completion_rate', 0)
                print(f"   {i}. {step_name[:50]}")
                print(f"      Relative Risk: {relative_risk:.1%}")
                print(f"      Expected Completion: {expected_completion:.1%}")
                print()
        
        # Print decision report summary
        decision_report = scenario_result.get('decision_report')
        if decision_report:
            actions = decision_report.get('recommended_actions', [])
            if actions:
                print("🎯 Top 3 Recommendations:")
                for i, action in enumerate(actions[:3], 1):
                    target = action.get('target_step', 'Unknown')
                    impact = action.get('expected_impact_pct', '')
                    confidence = action.get('confidence', 0)
                    change_type = action.get('change_type', 'improve')
                    print(f"   {i}. {change_type.replace('_', ' ').title()} at '{target}'")
                    print(f"      Impact: {impact}")
                    print(f"      Confidence: {confidence:.1%}")
                    print()
        
        print(f"💾 Full results saved to: {output_file}")
        print()
        print("=" * 80)
        
        return result
    except Exception as e:
        print(f"❌ Error running pipeline: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()


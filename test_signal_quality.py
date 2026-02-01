"""
Test script for signal quality evaluation.
Runs comparative scenarios to assess discriminative power.
"""

import json
import os
from dropsim_wizard import run_fintech_wizard, WizardInput
from dropsim_llm_ingestion import OpenAILLMClient
from dropsim_signal_quality import evaluate_signal_quality, compute_signal_strength

def load_screenshots_from_folder(folder_path, api_key):
    """Load and analyze screenshots from folder."""
    from pathlib import Path
    import base64
    import re
    from openai import OpenAI
    
    folder = Path(folder_path)
    image_extensions = ['.jpg', '.jpeg', '.png']
    screenshot_files = []
    for ext in image_extensions:
        screenshot_files.extend(list(folder.glob(f'*{ext}')))
        screenshot_files.extend(list(folder.glob(f'*{ext.upper()}')))
    
    screenshot_files.sort(key=lambda x: (
        int(re.search(r'\d+', x.stem).group()) if re.search(r'\d+', x.stem) else 999,
        x.name
    ))
    
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def analyze_screenshot(image_path, api_key):
        client = OpenAI(api_key=api_key)
        base64_image = encode_image(image_path)
        prompt = """Analyze this screenshot from a fintech product (Credigo.club credit card recommendation tool).

Extract:
1. Step number (if visible)
2. Main question or heading
3. Input fields or options shown
4. Key UI elements

Describe the screen in detail."""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }],
            max_tokens=500
        )
        return response.choices[0].message.content
    
    screenshot_texts = []
    for f in screenshot_files:
        try:
            description = analyze_screenshot(str(f), api_key)
            screenshot_texts.append(description)
        except Exception as e:
            screenshot_texts.append(f"Screenshot {f.stem}: Unable to analyze")
    
    return screenshot_texts

def run_scenario(name, persona_notes, target_group_notes, api_key, firecrawl_key):
    """Run a single scenario."""
    print(f"\n{'='*80}")
    print(f"Running Scenario: {name}")
    print(f"{'='*80}")
    
    screenshot_texts = load_screenshots_from_folder("credigo_ss", api_key)
    
    wizard_input = WizardInput(
        product_url="https://credigo.club",
        screenshot_texts=screenshot_texts,
        persona_notes=persona_notes,
        target_group_notes=target_group_notes
    )
    
    llm_client = OpenAILLMClient(api_key=api_key, model="gpt-4o-mini")
    
    result = run_fintech_wizard(
        wizard_input,
        llm_client,
        simulate=True,
        verbose=False,
        firecrawl_api_key=firecrawl_key,
        n_personas=500,  # Smaller for faster testing
        use_database_personas=True
    )
    
    return result.get('scenario_result', {})

def main():
    print("=" * 80)
    print("SIGNAL QUALITY EVALUATION - Comparative Scenarios")
    print("=" * 80)
    
    api_key = os.getenv("OPENAI_API_KEY")
    firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
    
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return
    
    # Scenario 1: Baseline (21-40, tier-1/high tier-2)
    print("\n📊 Scenario 1: Baseline")
    baseline = run_scenario(
        "Baseline",
        "Credit card seekers, salaried professionals, 21-40 age group",
        "21-40, working professionals, tier-1 or high tier-2 cities",
        api_key,
        firecrawl_key
    )
    
    # Scenario 2: Different persona (older, different location)
    print("\n📊 Scenario 2: Different Persona")
    different_persona = run_scenario(
        "Different Persona",
        "Credit card seekers, salaried professionals, 35-50 age group",
        "35-50, working professionals, tier-2 or tier-3 cities",
        api_key,
        firecrawl_key
    )
    
    # Evaluate signal quality
    print("\n" + "=" * 80)
    print("SIGNAL QUALITY EVALUATION")
    print("=" * 80)
    
    # Evaluate baseline
    print("\n📊 Evaluating Baseline Scenario...")
    baseline_eval = evaluate_signal_quality(
        baseline,
        comparison_results=None,  # Could add multiple runs
        perturbed_result=different_persona
    )
    
    print(f"\nSignal Strength: {baseline_eval['signal_strength']['score']:.1%}")
    print(f"Classification: {baseline_eval['judgment']['classification']}")
    print(f"Confidence Band: [{baseline_eval['signal_strength']['confidence_band'][0]:.1%}, {baseline_eval['signal_strength']['confidence_band'][1]:.1%}]")
    
    if baseline_eval['false_certainty_warnings']:
        print(f"\n⚠️  False Certainty Warnings:")
        for warning in baseline_eval['false_certainty_warnings']:
            print(f"   • {warning}")
    
    print(f"\n✅ Trustworthy Conclusions:")
    for conclusion in baseline_eval['judgment']['trustworthy_conclusions']:
        print(f"   • {conclusion}")
    
    print(f"\n⚠️  Uncertain Conclusions:")
    for conclusion in baseline_eval['judgment']['uncertain_conclusions']:
        print(f"   • {conclusion}")
    
    # Compare scenarios
    print("\n" + "=" * 80)
    print("COMPARATIVE ANALYSIS")
    print("=" * 80)
    
    # Check if outputs are meaningfully different
    baseline_top = None
    different_top = None
    
    if baseline.get('decision_report') and baseline['decision_report'].get('recommended_actions'):
        baseline_top = baseline['decision_report']['recommended_actions'][0].get('target_step')
    
    if different_persona.get('decision_report') and different_persona['decision_report'].get('recommended_actions'):
        different_top = different_persona['decision_report']['recommended_actions'][0].get('target_step')
    
    print(f"\nTop Recommendations:")
    print(f"   Baseline: {baseline_top}")
    print(f"   Different Persona: {different_top}")
    
    if baseline_top != different_top:
        print(f"   ✅ System detected meaningful difference (discriminative)")
    else:
        print(f"   ⚠️  System produced same recommendation (may be insensitive)")
    
    # Compare root causes
    baseline_causes = set()
    different_causes = set()
    
    if baseline.get('interpretation') and baseline['interpretation'].get('root_causes'):
        baseline_causes = set(c.get('step_id') for c in baseline['interpretation']['root_causes'][:3])
    
    if different_persona.get('interpretation') and different_persona['interpretation'].get('root_causes'):
        different_causes = set(c.get('step_id') for c in different_persona['interpretation']['root_causes'][:3])
    
    print(f"\nRoot Causes (top 3):")
    print(f"   Baseline: {baseline_causes}")
    print(f"   Different Persona: {different_causes}")
    
    overlap = len(baseline_causes & different_causes)
    if overlap < len(baseline_causes):
        print(f"   ✅ Different root causes identified (discriminative)")
    else:
        print(f"   ⚠️  Same root causes (may not be persona-sensitive)")
    
    # Save results
    output = {
        'baseline': baseline,
        'different_persona': different_persona,
        'baseline_evaluation': baseline_eval,
        'comparative_analysis': {
            'top_recommendation_changed': baseline_top != different_top,
            'root_causes_overlap': overlap,
            'discriminative': baseline_top != different_top and overlap < len(baseline_causes)
        }
    }
    
    with open('signal_quality_evaluation.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: signal_quality_evaluation.json")
    
    # Generate report
    print("\n" + "=" * 80)
    print("EVALUATION REPORT SUMMARY")
    print("=" * 80)
    print(f"\nSignal Quality: {baseline_eval['judgment']['classification'].upper()}")
    print(f"Overall Score: {baseline_eval['signal_strength']['score']:.1%}")
    print(f"\nExplanation: {baseline_eval['judgment']['explanation']}")
    print(f"\nImprovement Suggestions:")
    for suggestion in baseline_eval['judgment']['improvement_suggestions']:
        print(f"   • {suggestion}")

if __name__ == "__main__":
    main()


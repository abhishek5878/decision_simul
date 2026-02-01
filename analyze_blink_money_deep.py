#!/usr/bin/env python3
"""
Deep Analysis of Blink Money Screenshots - Enhanced Inference
Analyzes screenshots in much more detail to extract rich context
"""

import os
import base64
import json
from openai import OpenAI

def encode_image(image_path):
    """Encode image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_screenshot_deep(image_path, api_key, screenshot_name, step_number, total_steps):
    """Deep analysis of a single screenshot with rich context extraction."""
    client = OpenAI(api_key=api_key)
    
    base64_image = encode_image(image_path)
    
    prompt = f"""You are analyzing screenshot {step_number} of {total_steps} from Blink Money, a fintech product offering credit against mutual funds.

**CRITICAL: Analyze this screenshot in EXTREME detail. Extract everything visible.**

## DETAILED EXTRACTION REQUIRED:

1. **Screen Purpose & Context:**
   - What is the primary purpose of this screen?
   - What step number is shown (if visible)?
   - What progress indicator is shown (percentage, step X of Y)?
   - What is the user being asked to do?

2. **Exact Text Content:**
   - All headings, titles, labels
   - All button text (exact wording)
   - All form field labels
   - All helper text, disclaimers, fine print
   - Any value propositions, benefits, or promises shown
   - Any warnings, reassurances, or trust signals

3. **User Actions Required:**
   - What specific input is required?
   - What buttons/actions are available?
   - What happens if user clicks each button?
   - Is there a back button? Cancel option?

4. **Value & Benefits Shown:**
   - Is credit limit/eligibility shown? (exact numbers if visible)
   - Are interest rates shown? (exact percentages)
   - Are any benefits highlighted? (speed, cost savings, etc.)
   - Is there any comparison to alternatives?

5. **Risk & Trust Signals:**
   - Security badges, encryption mentions
   - "No credit score impact" messaging
   - Privacy policy links
   - Terms & conditions mentions
   - Any warnings or disclaimers

6. **Cognitive Load Indicators:**
   - How many form fields?
   - How complex are the inputs?
   - Is there educational content?
   - Are there multiple options/choices?

7. **Emotional Triggers:**
   - Urgency signals ("Limited time", "Act now")
   - Reassurance signals ("Secure", "Trusted")
   - Value signals ("Save ₹X", "Get up to ₹Y")
   - Social proof (testimonials, user count)

8. **Visual Elements:**
   - Icons, images, graphics
   - Color schemes (trust colors vs warning colors)
   - Layout complexity
   - Information density

9. **User Journey Context:**
   - Where is user coming from (previous step)?
   - Where are they going next (next step)?
   - What commitment level is this step?
   - Can they go back? Can they skip?

10. **Specific to Credit Products:**
    - Loan amount shown? Interest rate? Tenure?
    - EMI calculator? Comparison to alternatives?
    - Eligibility criteria visible?
    - Mutual fund details required?

**OUTPUT FORMAT:**
Provide a comprehensive analysis covering all 10 points above. Be extremely detailed and specific. Quote exact text when possible."""

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
        max_tokens=1000
    )
    
    return response.choices[0].message.content

def extract_enhanced_steps(screenshots, api_key):
    """Extract product steps with enhanced detail from deep screenshot analysis."""
    client = OpenAI(api_key=api_key)
    
    # Combine all detailed screenshot analyses
    screenshots_text = "\n\n".join([
        f"## SCREENSHOT {i+1} ({s['filename']})\n{s['deep_analysis']}"
        for i, s in enumerate(screenshots)
    ])
    
    prompt = f"""You are analyzing detailed screenshots from Blink Money. Based on the comprehensive analysis below, extract product steps with accurate attributes.

## DETAILED SCREENSHOT ANALYSES
{screenshots_text}

## TASK
For each screenshot, create a step definition with PRECISE attributes based on what's actually visible:

- step_name: Exact name from screenshot (button text, heading, or screen purpose)
- cognitive_demand: 0.0-1.0 (based on actual form complexity, choices, educational content)
- effort_demand: 0.0-1.0 (based on actual inputs required - slider vs form fields vs just clicking)
- risk_signal: 0.0-1.0 (based on actual data requested - phone number vs PAN vs bank linking)
- irreversibility: 0.0-1.0 (can user go back? Is this a commitment point?)
- delay_to_value: number of steps until credit eligibility/limit is shown (count from current step to value step)
- explicit_value: 0.0-1.0 (is credit limit/rate/eligibility actually shown on this screen? How clearly?)
- reassurance_signal: 0.0-1.0 (are trust signals visible? "No credit impact", security badges, etc.)
- authority_signal: 0.0-1.0 (bank partnerships, regulatory mentions, etc.)
- description: Detailed description of what user sees and does, including exact text/numbers if visible

**IMPORTANT:**
- If credit limit/eligibility is shown on a screen, delay_to_value should be 0 for that step
- If interest rate is shown, explicit_value should be higher
- If "no credit score impact" is visible, reassurance_signal should be higher
- Count steps accurately - if value appears at step 4, step 1 has delay_to_value = 3

Output ONLY a JSON object with this structure:
{{
  "Step Name 1": {{
    "cognitive_demand": 0.2,
    "effort_demand": 0.3,
    "risk_signal": 0.15,
    "irreversibility": 0.0,
    "delay_to_value": 2,
    "explicit_value": 0.5,
    "reassurance_signal": 0.6,
    "authority_signal": 0.3,
    "description": "Detailed description with exact text visible"
  }},
  ...
}}

Extract EXACTLY {len(screenshots)} steps."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={"type": "json_object"},
        max_tokens=2500
    )
    
    steps = json.loads(response.choices[0].message.content)
    return steps

def main():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set")
        return
    
    screenshot_dir = "products/blink_money"
    screenshot_files = sorted([f for f in os.listdir(screenshot_dir) if f.endswith(('.jpeg', '.jpg', '.png'))])
    total_steps = len(screenshot_files)
    
    print(f"\n🔍 DEEP ANALYSIS: Analyzing {total_steps} screenshots from {screenshot_dir}...")
    print("   This will extract detailed information from each screenshot...\n")
    
    screenshots = []
    for i, filename in enumerate(screenshot_files, 1):
        image_path = os.path.join(screenshot_dir, filename)
        print(f"   📸 Analyzing {filename} (Step {i}/{total_steps})...")
        try:
            deep_analysis = analyze_screenshot_deep(image_path, api_key, filename, i, total_steps)
            screenshots.append({
                'filename': filename,
                'step_number': i,
                'deep_analysis': deep_analysis
            })
            print(f"   ✅ {filename} analyzed in detail")
        except Exception as e:
            print(f"   ❌ Error analyzing {filename}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n📋 Extracting enhanced product steps from detailed analysis...")
    try:
        product_steps = extract_enhanced_steps(screenshots, api_key)
        print(f"   ✅ Extracted {len(product_steps)} product steps with enhanced detail")
        
        # Save to file
        with open("blink_money_steps.py", "w") as f:
            f.write('"""\n')
            f.write('Blink Money Product Flow Definition\n')
            f.write('Credit against Mutual Funds - Deep analysis from latest screenshots\n')
            f.write(f'{len(product_steps)}-step onboarding flow\n')
            f.write('Enhanced with detailed screenshot analysis\n')
            f.write('"""\n\n')
            f.write('BLINK_MONEY_STEPS = ')
            f.write(json.dumps(product_steps, indent=4))
            f.write('\n')
        
        print(f"\n✅ Enhanced product steps saved to blink_money_steps.py")
        print(f"\n📊 Steps extracted with enhanced detail:")
        for i, (step_name, step_def) in enumerate(product_steps.items(), 1):
            print(f"\n   {i}. {step_name}")
            print(f"      Description: {step_def.get('description', 'N/A')[:100]}...")
            print(f"      Value: {step_def.get('explicit_value', 0):.1f}, Delay: {step_def.get('delay_to_value', 0)} steps")
            print(f"      Risk: {step_def.get('risk_signal', 0):.1f}, Effort: {step_def.get('effort_demand', 0):.1f}")
        
        # Also save detailed analysis for reference
        with open("output/blink_money_screenshots_deep_analysis.json", "w") as f:
            json.dump(screenshots, f, indent=2)
        print(f"\n✅ Detailed screenshot analysis saved to blink_money_screenshots_deep_analysis.json")
        
        return product_steps
        
    except Exception as e:
        print(f"   ❌ Error extracting steps: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()

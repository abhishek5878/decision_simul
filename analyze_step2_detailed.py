#!/usr/bin/env python3
"""
Detailed re-analysis of Step 2 - Focus on phone number input and primary action
"""

import os
import base64
import json
from openai import OpenAI

def encode_image(image_path):
    """Encode image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_step2_focused(image_path, api_key):
    """Focused analysis on step 2 - identify primary action vs context."""
    client = OpenAI(api_key=api_key)
    
    base64_image = encode_image(image_path)
    
    prompt = """You are analyzing screenshot 2 of 5 from Blink Money's credit against mutual funds flow.

**CRITICAL: Identify the PRIMARY ACTION that moves the user to the next step vs CONTEXTUAL INFORMATION.**

## FOCUS AREAS:

1. **PRIMARY ACTION (What user must do to proceed):**
   - What is the MAIN input field that moves to next step?
   - Is there a phone number input field? (Look carefully - mobile number, phone number field)
   - Is there a number input for mutual fund amount?
   - What is the PRIMARY button that submits and moves forward?
   - What happens when user fills the primary field and clicks the button?

2. **CONTEXTUAL INFORMATION (Below the fold, for reference only):**
   - Benefits listed (these are informational, not actions)
   - Testimonials (social proof, not actions)
   - FAQs (help content, not actions)
   - Partner logos (trust signals, not actions)
   - "Why BlinkMoney?" section (marketing content, not actions)

3. **EXACT LAYOUT:**
   - What appears ABOVE the fold (primary action area)?
   - What appears BELOW the fold (contextual information)?
   - Is there a form with multiple fields, or one primary field?

4. **STEP FLOW:**
   - What is the exact sequence: User enters [what] → Clicks [what button] → Goes to step 3?
   - Is the phone number input the PRIMARY field that triggers next step?
   - Or is it the mutual fund amount that triggers next step?

**OUTPUT FORMAT:**
Provide a JSON object with this structure:
{
  "primary_action": {
    "main_input_field": {
      "type": "phone number input / number input / text input",
      "label": "exact label text",
      "placeholder": "placeholder if visible",
      "description": "what user must enter here"
    },
    "secondary_input_fields": [
      {
        "type": "...",
        "label": "...",
        "description": "..."
      }
    ],
    "primary_button": {
      "text": "exact button text",
      "action": "what happens when clicked"
    },
    "step_flow": "User enters [field] → Clicks [button] → Goes to step 3"
  },
  "contextual_information": {
    "above_fold": ["list of elements visible without scrolling"],
    "below_fold": ["list of elements that require scrolling"],
    "benefits_section": ["benefit 1", "benefit 2"],
    "testimonials": true/false,
    "faqs": true/false,
    "partner_logos": true/false
  },
  "complete_understanding": "Detailed explanation of what user sees, what they must do, and what is just context"
}

**IMPORTANT:**
- If there's a phone number field, it's likely the PRIMARY action
- If there's a mutual fund amount field, clarify if it's required or optional
- Distinguish between ACTION REQUIRED vs INFORMATION PROVIDED"""

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
        response_format={"type": "json_object"},
        max_tokens=1500
    )
    
    return json.loads(response.choices[0].message.content)

def main():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set")
        return
    
    screenshot_path = "blink_money/ss2.jpeg"
    
    print("\n🔍 DETAILED RE-ANALYSIS: Step 2 - Identifying Primary Action vs Context\n")
    
    try:
        analysis = analyze_step2_focused(screenshot_path, api_key)
        
        print("✅ Primary Action Identified:")
        primary = analysis.get('primary_action', {})
        main_input = primary.get('main_input_field', {})
        print(f"   Main Input: {main_input.get('type', 'N/A')} - {main_input.get('label', 'N/A')}")
        print(f"   Primary Button: {primary.get('primary_button', {}).get('text', 'N/A')}")
        print(f"   Step Flow: {primary.get('step_flow', 'N/A')}")
        
        if primary.get('secondary_input_fields'):
            print(f"\n   Secondary Inputs:")
            for field in primary.get('secondary_input_fields', []):
                print(f"      - {field.get('type', 'N/A')}: {field.get('label', 'N/A')}")
        
        print(f"\n✅ Contextual Information:")
        context = analysis.get('contextual_information', {})
        print(f"   Benefits: {len(context.get('benefits_section', []))} items")
        print(f"   Testimonials: {context.get('testimonials', False)}")
        print(f"   FAQs: {context.get('faqs', False)}")
        print(f"   Partner Logos: {context.get('partner_logos', False)}")
        
        # Save detailed analysis
        with open("step2_detailed_analysis.json", "w") as f:
            json.dump(analysis, f, indent=2)
        
        print(f"\n✅ Detailed analysis saved to step2_detailed_analysis.json")
        print(f"\n📝 Complete Understanding:")
        print(f"   {analysis.get('complete_understanding', 'N/A')[:200]}...")
        
        return analysis
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()

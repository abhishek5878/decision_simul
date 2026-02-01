#!/usr/bin/env python3
"""
Re-analyze Step 2 - Focus specifically on phone number input field
"""

import os
import base64
import json
from openai import OpenAI

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_for_phone_number(image_path, api_key):
    """Look specifically for phone number input field."""
    client = OpenAI(api_key=api_key)
    base64_image = encode_image(image_path)
    
    prompt = """Analyze this screenshot from Blink Money step 2. 

**CRITICAL: Look for a PHONE NUMBER or MOBILE NUMBER input field.**

The user says there is a phone number input field in step 2 that takes users to the next step.

**QUESTIONS TO ANSWER:**
1. Is there a phone number/mobile number input field visible? (Look for labels like "Mobile Number", "Phone Number", "Enter Mobile", etc.)
2. What is the exact label text for this field?
3. Is there a placeholder text? (e.g., "Enter 10-digit mobile number", "+91", etc.)
4. Is this field ABOVE or BELOW the mutual fund amount field?
5. What is the PRIMARY action: Enter phone number → Click button → Next step?
6. Is the mutual fund amount field also visible? Where is it relative to the phone field?

**OUTPUT:**
Provide a JSON object:
{
  "phone_number_field": {
    "exists": true/false,
    "label": "exact label text",
    "placeholder": "placeholder if visible",
    "position": "above/below mutual fund field",
    "is_primary_action": true/false
  },
  "mutual_fund_field": {
    "exists": true/false,
    "label": "exact label text",
    "position": "above/below phone field"
  },
  "primary_action_flow": "User enters [what] → Clicks [button] → Next step",
  "all_input_fields": [
    {"type": "phone/mobile/number/text", "label": "...", "order": 1},
    {"type": "...", "label": "...", "order": 2}
  ],
  "button_text": "exact button text",
  "layout_description": "Describe the layout: what's at the top (primary action), what's below (context)"
}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        response_format={"type": "json_object"},
        max_tokens=1000
    )
    
    return json.loads(response.choices[0].message.content)

if __name__ == "__main__":
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set")
        exit(1)
    
    print("\n🔍 RE-ANALYZING STEP 2: Looking for Phone Number Input Field\n")
    
    result = analyze_for_phone_number("blink_money/ss2.jpeg", api_key)
    
    print("✅ Phone Number Field Analysis:")
    phone_field = result.get('phone_number_field', {})
    if phone_field.get('exists'):
        print(f"   ✅ FOUND: {phone_field.get('label', 'N/A')}")
        print(f"   Placeholder: {phone_field.get('placeholder', 'N/A')}")
        print(f"   Position: {phone_field.get('position', 'N/A')}")
        print(f"   Is Primary Action: {phone_field.get('is_primary_action', False)}")
    else:
        print("   ❌ Phone number field not detected")
    
    print(f"\n✅ Mutual Fund Field:")
    mf_field = result.get('mutual_fund_field', {})
    if mf_field.get('exists'):
        print(f"   Label: {mf_field.get('label', 'N/A')}")
        print(f"   Position: {mf_field.get('position', 'N/A')}")
    
    print(f"\n✅ Primary Action Flow:")
    print(f"   {result.get('primary_action_flow', 'N/A')}")
    
    print(f"\n✅ All Input Fields (in order):")
    for field in result.get('all_input_fields', []):
        print(f"   {field.get('order', '?')}. {field.get('type', 'N/A')}: {field.get('label', 'N/A')}")
    
    print(f"\n✅ Button: {result.get('button_text', 'N/A')}")
    print(f"\n📝 Layout: {result.get('layout_description', 'N/A')[:200]}...")
    
    with open("step2_phone_analysis.json", "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n✅ Saved to step2_phone_analysis.json")

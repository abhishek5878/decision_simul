#!/usr/bin/env python3
import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

"""
Complete Analysis of Blink Money Screenshots - Capture EVERYTHING
Ensures no detail is missed, especially input fields, numbers, buttons, etc.
"""

import os
import base64
import json
from openai import OpenAI

def encode_image(image_path):
    """Encode image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_screenshot_complete(image_path, api_key, screenshot_name, step_number, total_steps):
    """Complete analysis - capture EVERY visible element."""
    client = OpenAI(api_key=api_key)
    
    base64_image = encode_image(image_path)
    
    prompt = f"""You are analyzing screenshot {step_number} of {total_steps} from Blink Money. 

**CRITICAL: Extract EVERY SINGLE ELEMENT visible on screen. Do not miss ANYTHING.**

## MANDATORY EXTRACTION - BE EXHAUSTIVE:

1. **ALL TEXT CONTENT (Quote exactly):**
   - Every heading, title, label (word-for-word)
   - Every button text (exact wording)
   - Every form field label (exact wording)
   - Every placeholder text in input fields
   - Every helper text, tooltip, hint
   - Every disclaimer, fine print, legal text
   - Every number, amount, percentage visible
   - Every icon label or alt text

2. **ALL INPUT FIELDS (Be specific):**
   - Field type (text input, number input, dropdown, date picker, slider, toggle, etc.)
   - Field label (exact text)
   - Placeholder text (if visible)
   - Default value (if any)
   - Input format expected (e.g., "6 digits", "PAN format", "currency amount")
   - Whether field is required or optional
   - Any validation hints visible

3. **ALL BUTTONS AND ACTIONS:**
   - Primary button text (exact)
   - Secondary button text (exact)
   - Back button (if visible)
   - Cancel/Close button (if visible)
   - Link text (if any)
   - Icon buttons and their purpose

4. **ALL NUMBERS AND AMOUNTS:**
   - Any currency amounts (₹X, $X, etc.)
   - Percentages (X% p.a., X% interest, etc.)
   - Step numbers (Step X of Y)
   - Progress percentages (X%)
   - Countdown timers (if any)
   - Any numeric values visible

5. **ALL VISUAL ELEMENTS:**
   - Icons and their meanings
   - Images and graphics
   - Progress bars or indicators
   - Checkmarks, badges, status indicators
   - Color coding (if meaningful)

6. **ALL VALUE PROPOSITIONS:**
   - Benefits listed (exact text)
   - Features highlighted (exact text)
   - Promises made (exact text)
   - Comparisons shown (if any)

7. **ALL TRUST SIGNALS:**
   - Security badges
   - Partner logos
   - Regulatory mentions
   - Testimonials (exact text)
   - User counts or statistics

8. **ALL WARNINGS/REASSURANCES:**
   - Privacy policy mentions
   - Terms & conditions mentions
   - "No credit score impact" messaging
   - Security assurances
   - Any disclaimers

9. **PROGRESS INDICATORS:**
   - Step number (Step X of Y)
   - Progress percentage (X%)
   - Progress bar (if visible)
   - Completion status

10. **LAYOUT AND STRUCTURE:**
    - Number of sections visible
    - Form fields count
    - Buttons count
    - Information density (high/medium/low)

**OUTPUT FORMAT:**
Provide a comprehensive JSON object with ALL extracted information. Be exhaustive - if you see it, include it.

Example structure:
{{
  "step_number": {step_number},
  "screenshot_file": "{screenshot_name}",
  "all_text_content": {{
    "headings": ["exact text 1", "exact text 2"],
    "buttons": ["exact button text 1", "exact button text 2"],
    "form_field_labels": ["exact label 1", "exact label 2"],
    "placeholders": ["placeholder text if visible"],
    "helper_text": ["helper text 1", "helper text 2"],
    "disclaimers": ["disclaimer text"],
    "value_propositions": ["benefit 1", "benefit 2"]
  }},
  "input_fields": [
    {{
      "type": "number input",
      "label": "How much is your fund?",
      "placeholder": "Enter amount",
      "format": "currency/numeric",
      "required": true,
      "description": "User must enter a numeric value representing their mutual fund amount"
    }}
  ],
  "numbers_and_amounts": [
    {{"type": "currency", "value": "₹10,000", "context": "Earn from ₹10,000"}},
    {{"type": "percentage", "value": "9.99%", "context": "interest rate"}}
  ],
  "buttons": [
    {{"text": "Check Eligibility", "type": "primary", "action": "submits form"}},
    {{"text": "Back", "type": "secondary", "action": "returns to previous step"}}
  ],
  "progress_indicator": {{
    "step_number": "Step 2 of 5",
    "percentage": "40%",
    "visible": true
  }},
  "trust_signals": ["No credit score impact", "Partner logos visible"],
  "visual_elements": ["Icons for benefits", "Progress bar"],
  "complete_description": "Detailed paragraph describing everything visible"
}}

**IMPORTANT:**
- If there's a number input field, describe it in detail (type, label, format, placeholder)
- If there's a slider, describe its range and current value
- If there's a toggle, describe what it does
- Quote ALL text exactly as it appears
- Include ALL numbers, amounts, percentages visible
- Do not summarize - be exhaustive"""

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
        max_tokens=2000
    )
    
    return response.choices[0].message.content

def main():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set")
        return
    
    screenshot_dir = "products/blink_money"
    screenshot_files = sorted([f for f in os.listdir(screenshot_dir) if f.endswith(('.jpeg', '.jpg', '.png'))])
    total_steps = len(screenshot_files)
    
    print(f"\n🔍 COMPLETE ANALYSIS: Analyzing {total_steps} screenshots...")
    print("   Capturing EVERY visible element - no detail will be missed...\n")
    
    all_analyses = []
    for i, filename in enumerate(screenshot_files, 1):
        image_path = os.path.join(screenshot_dir, filename)
        print(f"   📸 Analyzing {filename} (Step {i}/{total_steps})...")
        try:
            complete_analysis = analyze_screenshot_complete(image_path, api_key, filename, i, total_steps)
            analysis_data = json.loads(complete_analysis)
            all_analyses.append(analysis_data)
            print(f"   ✅ {filename} - Complete analysis extracted")
            
            # Show key findings
            if 'input_fields' in analysis_data:
                print(f"      Input fields found: {len(analysis_data['input_fields'])}")
                for field in analysis_data['input_fields']:
                    print(f"        - {field.get('type', 'N/A')}: {field.get('label', 'N/A')}")
            if 'numbers_and_amounts' in analysis_data:
                print(f"      Numbers/amounts found: {len(analysis_data['numbers_and_amounts'])}")
        except Exception as e:
            print(f"   ❌ Error analyzing {filename}: {e}")
            import traceback
            traceback.print_exc()
    
    # Save complete analysis
    import os
    os.makedirs("output", exist_ok=True)
    output_file = "output/blink_money_complete_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(all_analyses, f, indent=2)
    
    print(f"\n✅ Complete analysis saved to {output_file}")
    
    # Update step definitions with complete information
    print(f"\n📋 Updating step definitions with complete information...")
    update_steps_with_complete_analysis(all_analyses)
    
    print(f"\n✅ Complete analysis finished!\n")


def update_steps_with_complete_analysis(analyses):
    """Update blink_money_steps.py with complete information from analyses."""
    from blink_money_steps import BLINK_MONEY_STEPS
    
    step_names = list(BLINK_MONEY_STEPS.keys())
    updated_steps = {}
    
    for i, analysis in enumerate(analyses):
        if i < len(step_names):
            step_name = step_names[i]
            step_def = BLINK_MONEY_STEPS[step_name].copy()
            
            # Enhance description with complete information
            input_fields = analysis.get('input_fields', [])
            all_text = analysis.get('all_text_content', {})
            numbers = analysis.get('numbers_and_amounts', [])
            
            # Build comprehensive description
            desc_parts = [step_def.get('description', '')]
            
            # Add input field details
            if input_fields:
                for field in input_fields:
                    field_desc = f"Users must fill in a {field.get('type', 'input')} field labeled '{field.get('label', 'N/A')}'"
                    if field.get('format'):
                        field_desc += f" (format: {field.get('format')})"
                    if field.get('placeholder'):
                        field_desc += f" with placeholder '{field.get('placeholder')}'"
                    desc_parts.append(field_desc)
            
            # Add button details
            buttons = analysis.get('buttons', [])
            if buttons:
                button_texts = [b.get('text', '') for b in buttons if b.get('text')]
                if button_texts:
                    desc_parts.append(f"Available actions: {', '.join(button_texts)}")
            
            # Add numbers/amounts visible
            if numbers:
                number_strs = [f"{n.get('value', '')} ({n.get('context', '')})" for n in numbers]
                desc_parts.append(f"Visible numbers/amounts: {', '.join(number_strs)}")
            
            step_def['description'] = '. '.join(desc_parts) + '.'
            
            updated_steps[step_name] = step_def
    
    # Write updated steps
    with open("blink_money_steps.py", "w") as f:
        f.write('"""\n')
        f.write('Blink Money Product Flow Definition\n')
        f.write('Credit against Mutual Funds - COMPLETE analysis from screenshots\n')
        f.write(f'{len(updated_steps)}-step onboarding flow\n')
        f.write('Every visible element captured - no detail missed\n')
        f.write('"""\n\n')
        f.write('BLINK_MONEY_STEPS = ')
        f.write(json.dumps(updated_steps, indent=4))
        f.write('\n')
    
    print(f"   ✅ Updated blink_money_steps.py with complete information")


if __name__ == "__main__":
    main()

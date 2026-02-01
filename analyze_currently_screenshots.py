#!/usr/bin/env python3
"""
Analyze Currently screenshots to extract product steps
"""

import os
import base64
import json
from openai import OpenAI

def encode_image(image_path):
    """Encode image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_screenshot(image_path, api_key, screenshot_name):
    """Analyze a single screenshot using GPT-4 Vision."""
    client = OpenAI(api_key=api_key)
    
    base64_image = encode_image(image_path)
    
    prompt = """Analyze this screenshot from Currently, a social app for young Millennials who want real-time, authentic updates from friends rather than curated feeds. The app focuses on socially active, urban users who like spontaneous meetups and seeing where friends are on a live map.

Extract:
1. Step number (if visible, e.g., "Step 1 of 6", "Step 2 of 6")
2. Progress percentage (if visible)
3. Main question, heading, or screen purpose
4. Input fields, options, or actions required
5. Any buttons or CTAs
6. Key UI elements and what the user needs to do
7. Risk indicators (data sharing, location sharing, privacy concerns, etc.)
8. Effort indicators (form complexity, number of fields, etc.)
9. Cognitive complexity (simple choice vs complex decision)
10. Value proposition shown (if any - seeing friends, live map, real-time updates, etc.)

Describe the screen in detail, focusing on what the user needs to do at this step."""

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
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=500
    )
    
    return response.choices[0].message.content

def extract_product_steps_from_analysis(screenshots, api_key):
    """Extract product steps from screenshot analysis using LLM."""
    client = OpenAI(api_key=api_key)
    
    # Combine all screenshot descriptions
    screenshots_text = "\n\n".join([
        f"## SCREENSHOT {i+1} ({s['filename']})\n{s['description']}"
        for i, s in enumerate(screenshots)
    ])
    
    prompt = f"""You are analyzing screenshots from Currently, a social app for young Millennials who are heavy social app users and want real-time, authentic updates from friends rather than curated feeds. It focuses on socially active, urban users who like spontaneous meetups and seeing where friends are on a live map.

## SCREENSHOTS (in order)
{screenshots_text}

## TASK
Extract product steps from these screenshots. For each screenshot, create a step definition with these attributes:
- step_name: Clear name of the step (use exact text from screenshot if available)
- cognitive_demand: 0.0-1.0 (how much thinking required)
- effort_demand: 0.0-1.0 (physical/time effort)
- risk_signal: 0.0-1.0 (data/location/privacy risk perception)
- irreversibility: 0.0-1.0 (can user undo this?)
- delay_to_value: number of steps until user sees value (0 = instant, higher = later)
- explicit_value: 0.0-1.0 (how clear is the benefit shown? - seeing friends, live map, real-time updates, etc.)
- reassurance_signal: 0.0-1.0 (trust signals present - privacy controls, security badges, etc.)
- authority_signal: 0.0-1.0 (official backing)
- description: Brief description of what happens at this step

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
    "description": "Step description"
  }},
  "Step Name 2": {{ ... }},
  ...
}}

Extract EXACTLY {len(screenshots)} steps, one per screenshot. Use the exact step names/headings from the screenshots."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={"type": "json_object"},
        max_tokens=2000
    )
    
    steps = json.loads(response.choices[0].message.content)
    return steps

def main():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set")
        return
    
    screenshot_dir = "products/currently"
    screenshot_files = sorted([f for f in os.listdir(screenshot_dir) if f.endswith(('.jpeg', '.jpg', '.png', '.PNG'))])
    
    print(f"\n🔍 Analyzing {len(screenshot_files)} screenshots from {screenshot_dir}...")
    
    screenshots = []
    for i, filename in enumerate(screenshot_files, 1):
        image_path = os.path.join(screenshot_dir, filename)
        print(f"   Analyzing {filename}...")
        try:
            description = analyze_screenshot(image_path, api_key, filename)
            screenshots.append({
                'filename': filename,
                'step_number': i,
                'description': description
            })
            print(f"   ✅ {filename} analyzed")
        except Exception as e:
            print(f"   ❌ Error analyzing {filename}: {e}")
    
    print(f"\n📋 Extracting product steps...")
    try:
        product_steps = extract_product_steps_from_analysis(screenshots, api_key)
        print(f"   ✅ Extracted {len(product_steps)} product steps")
        
        # Save to file
        with open("currently_steps.py", "w") as f:
            f.write('"""\n')
            f.write('Currently Product Flow Definition\n')
            f.write('Social app for real-time, authentic updates from friends\n')
            f.write(f'{len(product_steps)}-step onboarding flow\n')
            f.write('"""\n\n')
            f.write('CURRENTLY_STEPS = ')
            f.write(json.dumps(product_steps, indent=4))
            f.write('\n')
        
        print(f"\n✅ Product steps saved to currently_steps.py")
        print(f"\n📊 Steps extracted:")
        for i, (step_name, step_def) in enumerate(product_steps.items(), 1):
            print(f"   {i}. {step_name}")
            print(f"      Description: {step_def.get('description', 'N/A')}")
        
        return product_steps
        
    except Exception as e:
        print(f"   ❌ Error extracting steps: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()

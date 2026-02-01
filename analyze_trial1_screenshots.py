#!/usr/bin/env python3
"""
Analyze trial1 screenshots using OpenAI Vision API and extract product flow.
AI tool for indie founders and small SaaS teams.
"""

import os
import base64
from openai import OpenAI

def encode_image(image_path):
    """Encode image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_screenshot(image_path, api_key, screenshot_name):
    """Analyze a single screenshot using GPT-4 Vision."""
    client = OpenAI(api_key=api_key)
    
    base64_image = encode_image(image_path)
    
    prompt = """Analyze this screenshot from an AI tool onboarding flow targeting indie founders and small SaaS teams.

Extract:
1. Step number (if visible, e.g., "Step 1 of 5", "Step 2 of 5")
2. Progress percentage (if visible)
3. Main question, heading, or screen purpose
4. Input fields, options, or actions required
5. Any buttons or CTAs
6. Key UI elements and what the user needs to do
7. What value is being delivered or promised

Describe the screen in detail, focusing on what the user needs to do at this step and any cognitive/effort/risk factors. Pay special attention to:
- What AI capability is being demonstrated
- What data/input is being requested
- What value/output is being shown
- Any trust signals or reassurance elements"""

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
        max_tokens=800
    )
    
    return response.choices[0].message.content

if __name__ == "__main__":
    import sys
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set")
        sys.exit(1)
    
    # Screenshots to analyze (ss1 to ss5)
    screenshots = [f"ss{i}" for i in range(1, 6)]
    base_dir = "/Users/abhishekvyas/Desktop/inertia_labs/trial1"
    
    print("🔍 Analyzing trial1 screenshots (AI tool for indie founders/SaaS teams)...\n")
    
    descriptions = []
    for ss_name in screenshots:
        image_path = os.path.join(base_dir, f"{ss_name}.png")
        
        if not os.path.exists(image_path):
            print(f"⚠️  Warning: {ss_name}.png not found, skipping")
            continue
        
        print(f"Analyzing {ss_name}...")
        try:
            description = analyze_screenshot(image_path, api_key, ss_name)
            descriptions.append(f"Screenshot {ss_name}: {description}")
            print(f"✅ {ss_name} analyzed\n")
        except Exception as e:
            print(f"❌ Error analyzing {ss_name}: {e}\n")
    
    # Write to file
    output_file = "trial1_screenshots_analyzed.txt"
    with open(output_file, "w") as f:
        f.write("\n---\n".join(descriptions))
    
    print(f"✅ Saved descriptions to {output_file}")
    print(f"\n📋 Total screenshots analyzed: {len(descriptions)}")


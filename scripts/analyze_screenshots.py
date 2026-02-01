#!/usr/bin/env python3
import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

"""
Analyze screenshots using OpenAI Vision API and extract product flow.
"""

import os
import base64
from openai import OpenAI

def encode_image(image_path):
    """Encode image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_screenshot(image_path, api_key):
    """Analyze a single screenshot using GPT-4 Vision."""
    client = OpenAI(api_key=api_key)
    
    base64_image = encode_image(image_path)
    
    prompt = """Analyze this screenshot from a fintech product (Credigo.club credit card recommendation tool).

Extract:
1. Step number (if visible, e.g., "Step 1 of 7", "Step 2 of 7")
2. Progress percentage (if visible)
3. Main question or heading
4. Input fields or options shown
5. Any buttons or CTAs
6. Key UI elements

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
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=500
    )
    
    return response.choices[0].message.content

if __name__ == "__main__":
    import sys
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set")
        sys.exit(1)
    
    # Screenshots to analyze (in order)
    screenshots = ["ss1", "ss2", "ss3", "ss4", "ss5", "ss10", "ss11"]
    base_dir = "/Users/abhishekvyas/Desktop/inertia_labs/credigo_ss"
    
    print("🔍 Analyzing screenshots...\n")
    
    descriptions = []
    for ss_name in screenshots:
        image_path = os.path.join(base_dir, f"{ss_name}.jpeg")
        if not os.path.exists(image_path):
            print(f"⚠️  Warning: {image_path} not found, skipping")
            continue
        
        print(f"Analyzing {ss_name}...")
        try:
            description = analyze_screenshot(image_path, api_key)
            descriptions.append(f"Screenshot {ss_name}: {description}")
            print(f"✅ {ss_name} analyzed\n")
        except Exception as e:
            print(f"❌ Error analyzing {ss_name}: {e}\n")
    
    # Write to file
    output_file = "credigo_screenshots_analyzed.txt"
    with open(output_file, "w") as f:
        f.write("\n---\n".join(descriptions))
    
    print(f"✅ Saved descriptions to {output_file}")
    print(f"\n📋 Total screenshots analyzed: {len(descriptions)}")


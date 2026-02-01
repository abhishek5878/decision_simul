import json
import re

# Load the JSON file
with open('BLINK_MONEY_DECISION_AUTOPSY_RESULT.json', 'r') as f:
    data = json.load(f)

# Target persona keywords
persona_keywords = [
    "self-employed",
    "non-salaried",
    "irregular.*income",
    "daily.*weekly.*income",
    "struggle.*save",
    "automated.*wealth",
    "wealth building"
]

def search_recursive(obj, path="", results=None, search_terms=None):
    """Recursively search through JSON structure"""
    if results is None:
        results = []
    if search_terms is None:
        search_terms = []
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            current_path = f"{path}.{key}" if path else key
            search_recursive(value, current_path, results, search_terms)
            
            # Check if key or value contains our search terms
            key_str = str(key).lower()
            value_str = str(value).lower() if isinstance(value, (str, int, float)) else ""
            full_text = f"{key_str} {value_str}"
            
            # Search for bachatt (various spellings)
            if any(term in full_text for term in ['bachatt', 'bachat', 'bachattt', 'bhatt']):
                results.append({
                    'type': 'bachatt_match',
                    'path': current_path,
                    'key': key,
                    'value': value if not isinstance(value, (dict, list)) else f"[{type(value).__name__}]"
                })
            
            # Search for persona keywords
            for keyword in persona_keywords:
                if re.search(keyword, full_text, re.IGNORECASE):
                    results.append({
                        'type': 'persona_match',
                        'path': current_path,
                        'key': key,
                        'value': str(value)[:500] if not isinstance(value, (dict, list)) else f"[{type(value).__name__}]",
                        'matched_keyword': keyword
                    })
    
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            current_path = f"{path}[{i}]"
            search_recursive(item, current_path, results, search_terms)
            
            # Check list items
            item_str = str(item).lower() if isinstance(item, (str, int, float)) else ""
            if any(term in item_str for term in ['bachatt', 'bachat', 'bachattt', 'bhatt']):
                results.append({
                    'type': 'bachatt_match',
                    'path': current_path,
                    'value': item if not isinstance(item, (dict, list)) else f"[{type(item).__name__}]"
                })
            for keyword in persona_keywords:
                if re.search(keyword, item_str, re.IGNORECASE):
                    results.append({
                        'type': 'persona_match',
                        'path': current_path,
                        'value': str(item)[:500] if not isinstance(item, (dict, list)) else f"[{type(item).__name__}]",
                        'matched_keyword': keyword
                    })
    
    return results

# Search through the data
print("=" * 80)
print("SEARCHING FOR 'BACHATT' AND TARGET PERSONA")
print("=" * 80)
results = search_recursive(data)

bachatt_results = [r for r in results if r['type'] == 'bachatt_match']
persona_results = [r for r in results if r['type'] == 'persona_match']

print(f"\nFound {len(bachatt_results)} matches for 'bachatt' (various spellings):")
for r in bachatt_results[:20]:
    print(f"  Path: {r['path']}")
    print(f"  Key: {r.get('key', 'N/A')}")
    print(f"  Value: {str(r['value'])[:200]}")
    print()

print(f"\nFound {len(persona_results)} matches for persona keywords:")
for r in persona_results[:20]:
    print(f"  Path: {r['path']}")
    print(f"  Key: {r.get('key', 'N/A')}")
    print(f"  Matched keyword: {r.get('matched_keyword', 'N/A')}")
    print(f"  Value: {str(r['value'])[:300]}")
    print()

# Extract product steps
print("\n" + "=" * 80)
print("EXTRACTING PRODUCT STEPS")
print("=" * 80)

def extract_steps(obj, path=""):
    """Extract product steps from the structure"""
    steps = []
    
    if isinstance(obj, dict):
        # Check for common step-related keys
        if 'steps' in obj:
            steps.append({
                'path': f"{path}.steps" if path else "steps",
                'data': obj['steps']
            })
        if 'productSteps' in obj:
            steps.append({
                'path': f"{path}.productSteps" if path else "productSteps",
                'data': obj['productSteps']
            })
        if 'decisionSimulation' in obj and isinstance(obj['decisionSimulation'], dict):
            if 'steps' in obj['decisionSimulation']:
                steps.append({
                    'path': f"{path}.decisionSimulation.steps" if path else "decisionSimulation.steps",
                    'data': obj['decisionSimulation']['steps']
                })
        
        # Recursively search
        for key, value in obj.items():
            if isinstance(value, (dict, list)):
                steps.extend(extract_steps(value, f"{path}.{key}" if path else key))
    
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, (dict, list)):
                steps.extend(extract_steps(item, f"{path}[{i}]" if path else f"[{i}]"))
    
    return steps

all_steps = extract_steps(data)
print(f"\nFound {len(all_steps)} step structures:")
for step_info in all_steps:
    print(f"\n  Path: {step_info['path']}")
    step_data = step_info['data']
    if isinstance(step_data, list):
        print(f"  Number of steps: {len(step_data)}")
        if len(step_data) > 0:
            print(f"  First step keys: {list(step_data[0].keys()) if isinstance(step_data[0], dict) else 'N/A'}")
            print(f"  Sample step:")
            if isinstance(step_data[0], dict):
                for k, v in list(step_data[0].items())[:5]:
                    print(f"    {k}: {str(v)[:100]}")
    elif isinstance(step_data, dict):
        print(f"  Step dict keys: {list(step_data.keys())}")
    print()

# Now filter for bachatt and persona in the steps
print("\n" + "=" * 80)
print("FILTERING STEPS FOR BACHATT AND TARGET PERSONA")
print("=" * 80)

filtered_results = {
    'bachatt_steps': [],
    'persona_steps': [],
    'all_steps_with_context': []
}

# Get the main steps structure
main_steps = None
if 'decisionSimulation' in data and 'steps' in data['decisionSimulation']:
    main_steps = data['decisionSimulation']['steps']
    
    print(f"\nProcessing {len(main_steps)} product steps...")
    
    for i, step in enumerate(main_steps):
        step_str = json.dumps(step, indent=2).lower()
        
        # Check for bachatt
        if any(term in step_str for term in ['bachatt', 'bachat', 'bachattt', 'bhatt']):
            filtered_results['bachatt_steps'].append({
                'step_index': i,
                'step': step
            })
        
        # Check for persona
        persona_found = False
        matched_keywords = []
        for keyword in persona_keywords:
            if re.search(keyword, step_str, re.IGNORECASE):
                persona_found = True
                matched_keywords.append(keyword)
        
        if persona_found:
            filtered_results['persona_steps'].append({
                'step_index': i,
                'step': step,
                'matched_keywords': matched_keywords
            })
        
        # Store all steps with their context
        filtered_results['all_steps_with_context'].append({
            'step_index': i,
            'step': step
        })

print(f"\nSteps containing 'bachatt': {len(filtered_results['bachatt_steps'])}")
for item in filtered_results['bachatt_steps']:
    print(f"\n  Step {item['step_index']}:")
    print(json.dumps(item['step'], indent=4)[:500])

print(f"\nSteps containing persona keywords: {len(filtered_results['persona_steps'])}")
for item in filtered_results['persona_steps']:
    print(f"\n  Step {item['step_index']} (matched: {', '.join(item['matched_keywords'])})")
    print(json.dumps(item['step'], indent=4)[:500])

# Save filtered results
output_file = 'filtered_bachatt_persona_results.json'
with open(output_file, 'w') as f:
    json.dump(filtered_results, f, indent=2)

print(f"\n\nResults saved to: {output_file}")
print(f"Total steps analyzed: {len(filtered_results['all_steps_with_context'])}")

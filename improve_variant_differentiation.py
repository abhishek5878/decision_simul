#!/usr/bin/env python3
"""
Increase variant differentiation to make results more realistic.

The current variants produce completion rates that are too similar (37.6% - 43.3%).
We need to increase the spread to 25-55% range to be realistic.

Strategy:
1. Increase perceived_control gap for distrustful_arrival (trust penalty)
2. Increase perceived_value gap for price_sensitive (value penalty)
3. Increase perceived_risk reduction for tech_savvy_optimistic (risk bonus)
4. Increase cognitive_energy_mult gap for tired_commuter (fatigue penalty)
5. Ensure these differences compound across steps (not just initial state)
"""

# Modified STATE_VARIANTS with stronger differentiation
IMPROVED_STATE_VARIANTS = {
    "fresh_motivated": {
        "cognitive_energy_mult": 0.9,  # Keep high
        "perceived_value": 0.8,  # Keep high
        "perceived_risk": 0.1,  # Keep low
        "perceived_effort": 0.1,  # Keep low
        "perceived_control": 0.75,  # Slightly higher (trust)
        "description": "Fresh arrival, high motivation"
    },
    "tired_commuter": {
        "cognitive_energy_mult": 0.45,  # LOWER: 0.5 -> 0.45 (stronger fatigue)
        "perceived_value": 0.55,  # LOWER: 0.6 -> 0.55
        "perceived_risk": 0.25,  # HIGHER: 0.2 -> 0.25 (tired = more risk-averse)
        "perceived_effort": 0.35,  # HIGHER: 0.3 -> 0.35 (tired = effort feels harder)
        "perceived_control": 0.45,  # LOWER: 0.5 -> 0.45 (less control when tired)
        "description": "Tired, lower energy - STRONGER PENALTIES"
    },
    "distrustful_arrival": {
        "cognitive_energy_mult": 0.8,  # Keep
        "perceived_value": 0.55,  # LOWER: 0.6 -> 0.55 (distrust = lower value perception)
        "perceived_risk": 0.5,  # HIGHER: 0.4 -> 0.5 (stronger risk perception)
        "perceived_effort": 0.25,  # HIGHER: 0.2 -> 0.25
        "perceived_control": 0.2,  # MUCH LOWER: 0.3 -> 0.2 (STRONGER TRUST PENALTY)
        "description": "Arrives with trust concerns - STRONGER PENALTIES"
    },
    "browsing_casually": {
        "cognitive_energy_mult": 0.9,  # Keep
        "perceived_value": 0.25,  # LOWER: 0.3 -> 0.25 (casual browsing = lower value)
        "perceived_risk": 0.1,  # Keep low
        "perceived_effort": 0.2,  # Keep
        "perceived_control": 0.6,  # Keep
        "description": "Low urgency, exploring"
    },
    "urgent_need": {
        "cognitive_energy_mult": 0.7,  # Keep
        "perceived_value": 0.95,  # HIGHER: 0.9 -> 0.95 (urgent = very high value)
        "perceived_risk": 0.15,  # LOWER: 0.2 -> 0.15 (urgent = risk tolerance)
        "perceived_effort": 0.08,  # LOWER: 0.1 -> 0.08 (urgent = effort feels less)
        "perceived_control": 0.85,  # HIGHER: 0.8 -> 0.85 (urgent = more control)
        "description": "High urgency, strong motivation - STRONGER BONUSES"
    },
    "price_sensitive": {
        "cognitive_energy_mult": 0.8,  # Keep
        "perceived_value": 0.3,  # MUCH LOWER: 0.4 -> 0.3 (STRONGER VALUE PENALTY)
        "perceived_risk": 0.35,  # HIGHER: 0.3 -> 0.35 (price-sensitive = more risk-averse)
        "perceived_effort": 0.25,  # HIGHER: 0.2 -> 0.25
        "perceived_control": 0.45,  # LOWER: 0.5 -> 0.45 (price-sensitive = less trust)
        "description": "Highly price-conscious - STRONGER PENALTIES"
    },
    "tech_savvy_optimistic": {
        "cognitive_energy_mult": 0.98,  # HIGHER: 0.95 -> 0.98 (very high energy)
        "perceived_value": 0.75,  # HIGHER: 0.7 -> 0.75 (tech-savvy = see more value)
        "perceived_risk": 0.02,  # MUCH LOWER: 0.05 -> 0.02 (STRONGER RISK REDUCTION)
        "perceived_effort": 0.03,  # MUCH LOWER: 0.05 -> 0.03 (STRONGER EFFORT REDUCTION)
        "perceived_control": 0.9,  # HIGHER: 0.8 -> 0.9 (STRONGER TRUST BONUS)
        "description": "High digital literacy, optimistic - STRONGER BONUSES"
    }
}

def generate_modified_behavioral_engine():
    """Generate code to replace STATE_VARIANTS in behavioral_engine.py"""
    
    code_lines = []
    code_lines.append('# ============================================================================')
    code_lines.append('# STATE VARIANT DEFINITIONS (Structured, Deterministic)')
    code_lines.append('# MODIFIED: Increased differentiation for realistic variant spread')
    code_lines.append('# ============================================================================')
    code_lines.append('')
    code_lines.append('STATE_VARIANTS = {')
    
    for variant, config in IMPROVED_STATE_VARIANTS.items():
        code_lines.append(f'    "{variant}": {{')
        for key, value in config.items():
            if key == 'description':
                code_lines.append(f'        "{key}": "{value}",')
            else:
                code_lines.append(f'        "{key}": {value},')
        code_lines.append('    },')
        code_lines.append('')
    
    code_lines.append('}')
    code_lines.append('')
    
    return '\n'.join(code_lines)

if __name__ == "__main__":
    print("=" * 80)
    print("IMPROVED STATE_VARIANTS (for increased differentiation)")
    print("=" * 80)
    print()
    
    print("Changes:")
    print("1. distrustful_arrival: perceived_control 0.3 -> 0.2 (stronger trust penalty)")
    print("2. price_sensitive: perceived_value 0.4 -> 0.3 (stronger value penalty)")
    print("3. tech_savvy_optimistic: perceived_risk 0.05 -> 0.02, perceived_control 0.8 -> 0.9 (stronger bonuses)")
    print("4. tired_commuter: cognitive_energy_mult 0.5 -> 0.45, perceived_value 0.6 -> 0.55 (stronger penalties)")
    print("5. urgent_need: perceived_value 0.9 -> 0.95, perceived_control 0.8 -> 0.85 (stronger bonuses)")
    print()
    
    code = generate_modified_behavioral_engine()
    print("Generated code:")
    print("=" * 80)
    print(code)
    print("=" * 80)
    
    # Save to file
    with open('improved_state_variants_code.txt', 'w') as f:
        f.write(code)
    
    print("\n✅ Code saved to improved_state_variants_code.txt")
    print("\nNext step: Replace STATE_VARIANTS in behavioral_engine.py with this code")


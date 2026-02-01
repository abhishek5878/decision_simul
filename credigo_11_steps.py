"""
Credigo 11-Step Product Flow Definition
Based on actual Credigo.club screenshots and flow
"""

CREDIGO_11_STEPS = {
    "Find the Best Credit Card In 60 seconds": {
        "cognitive_demand": 0.2,
        "effort_demand": 0.0,
        "risk_signal": 0.1,
        "irreversibility": 0,
        "delay_to_value": 10,  # 11 steps total
        "explicit_value": 0.3,
        "reassurance_signal": 0.6,  # "No PAN, no data" is strong
        "authority_signal": 0.2,
        "description": "Landing page - 60 second promise, privacy claims"
    },
    "What kind of perks excite you the most?": {
        "cognitive_demand": 0.3,
        "effort_demand": 0.2,
        "risk_signal": 0.15,
        "irreversibility": 0,
        "delay_to_value": 9,
        "explicit_value": 0.2,
        "reassurance_signal": 0.4,
        "authority_signal": 0.1,
        "description": "First question - perks preference"
    },
    "Any preference on annual fee?": {
        "cognitive_demand": 0.3,
        "effort_demand": 0.2,
        "risk_signal": 0.15,
        "irreversibility": 0,
        "delay_to_value": 8,
        "explicit_value": 0.2,
        "reassurance_signal": 0.4,
        "authority_signal": 0.1,
        "description": "Annual fee preference question"
    },
    "straightforward + options are clearly defined": {
        "cognitive_demand": 0.25,
        "effort_demand": 0.15,
        "risk_signal": 0.1,
        "irreversibility": 0,
        "delay_to_value": 7,
        "explicit_value": 0.25,
        "reassurance_signal": 0.4,
        "authority_signal": 0.1,
        "description": "Clarification step - options defined"
    },
    "Your top 2 spend categories?": {
        "cognitive_demand": 0.4,
        "effort_demand": 0.3,
        "risk_signal": 0.2,
        "irreversibility": 0,
        "delay_to_value": 6,
        "explicit_value": 0.25,
        "reassurance_signal": 0.3,
        "authority_signal": 0.1,
        "description": "Spend categories question - requires thinking"
    },
    "Do you track your monthly spending?": {
        "cognitive_demand": 0.35,
        "effort_demand": 0.25,
        "risk_signal": 0.2,
        "irreversibility": 0,
        "delay_to_value": 5,
        "explicit_value": 0.25,
        "reassurance_signal": 0.3,
        "authority_signal": 0.1,
        "description": "Spending tracking question"
    },
    "How much do you spend monthly?": {
        "cognitive_demand": 0.4,
        "effort_demand": 0.3,
        "risk_signal": 0.25,  # Financial info feels risky
        "irreversibility": 0,
        "delay_to_value": 4,
        "explicit_value": 0.25,
        "reassurance_signal": 0.3,
        "authority_signal": 0.1,
        "description": "Monthly spending amount - sensitive question"
    },
    "Do you have any existing credit cards?": {
        "cognitive_demand": 0.3,
        "effort_demand": 0.2,
        "risk_signal": 0.2,
        "irreversibility": 0,
        "delay_to_value": 3,
        "explicit_value": 0.3,
        "reassurance_signal": 0.35,
        "authority_signal": 0.1,
        "description": "Existing cards question"
    },
    "Help us personalise your card matches": {
        "cognitive_demand": 0.35,
        "effort_demand": 0.25,
        "risk_signal": 0.2,
        "irreversibility": 0,
        "delay_to_value": 2,
        "explicit_value": 0.35,  # Getting closer to value
        "reassurance_signal": 0.4,
        "authority_signal": 0.15,
        "description": "Personalization step - building anticipation"
    },
    "Step 1 of 11": {
        "cognitive_demand": 0.2,
        "effort_demand": 0.1,
        "risk_signal": 0.1,
        "irreversibility": 0,
        "delay_to_value": 1,
        "explicit_value": 0.5,  # Progress indicator - feels good
        "reassurance_signal": 0.5,
        "authority_signal": 0.2,
        "description": "Progress indicator - almost done"
    },
    "Best Deals for You – Apply Now": {
        "cognitive_demand": 0.3,
        "effort_demand": 0.1,
        "risk_signal": 0.15,
        "irreversibility": 0,
        "delay_to_value": 0.5,
        "explicit_value": 0.7,  # Value delivered!
        "reassurance_signal": 0.4,
        "authority_signal": 0.3,
        "description": "Results page - recommendations shown, apply CTA"
    }
}


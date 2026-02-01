"""
Trial1 Product Flow Definition
AI tool for indie founders and small SaaS teams
Based on 5 screenshots - typical AI tool onboarding flow
"""

TRIAL1_STEPS = {
    "Landing Page - AI Tool Value Proposition": {
        "cognitive_demand": 0.2,
        "effort_demand": 0.0,
        "risk_signal": 0.1,
        "irreversibility": 0,
        "delay_to_value": 4,  # 5 steps total
        "explicit_value": 0.5,  # AI tool value prop shown
        "reassurance_signal": 0.5,
        "authority_signal": 0.3,
        "intent_signals": {
            "try_ai_tool": 0.8,  # High alignment - this is what they want
        },
        "comparison_available": False,
        "description": "Landing page - AI tool value proposition, features, benefits for indie founders/SaaS teams"
    },
    "Sign Up / Email Entry": {
        "cognitive_demand": 0.2,
        "effort_demand": 0.2,  # Enter email
        "risk_signal": 0.15,  # Sharing email
        "irreversibility": 0,
        "delay_to_value": 3,
        "explicit_value": 0.3,  # Getting closer to trying the tool
        "reassurance_signal": 0.4,
        "authority_signal": 0.2,
        "intent_signals": {
            "try_ai_tool": 0.7,
        },
        "comparison_available": False,
        "description": "Email entry - sign up to try the AI tool"
    },
    "Onboarding - Use Case Selection": {
        "cognitive_demand": 0.4,
        "effort_demand": 0.3,  # Select use case/describe needs
        "risk_signal": 0.15,
        "irreversibility": 0,
        "delay_to_value": 2,
        "explicit_value": 0.3,  # Personalization for their use case
        "reassurance_signal": 0.4,
        "authority_signal": 0.2,
        "intent_signals": {
            "try_ai_tool": 0.6,
        },
        "comparison_available": False,
        "description": "Select use case or describe what they want to do with the AI tool"
    },
    "Setup / Configuration": {
        "cognitive_demand": 0.5,
        "effort_demand": 0.4,  # Configure tool settings
        "risk_signal": 0.2,  # May need to connect integrations
        "irreversibility": 0,
        "delay_to_value": 1,
        "explicit_value": 0.4,  # Getting close to using the tool
        "reassurance_signal": 0.5,
        "authority_signal": 0.3,
        "intent_signals": {
            "try_ai_tool": 0.7,
        },
        "comparison_available": False,
        "description": "Configure tool settings, connect integrations if needed"
    },
    "First Use / Value Delivery": {
        "cognitive_demand": 0.3,
        "effort_demand": 0.2,  # Try the AI tool
        "risk_signal": 0.1,
        "irreversibility": 0,
        "delay_to_value": 0,  # Value delivered: AI tool working
        "explicit_value": 0.9,  # High value: AI tool delivers results
        "reassurance_signal": 0.6,
        "authority_signal": 0.4,
        "intent_signals": {
            "try_ai_tool": 0.9,  # Perfect alignment - they're using it
        },
        "comparison_available": False,
        "description": "First use - AI tool delivers value, user sees results"
    }
}


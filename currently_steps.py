"""
Currently Product Flow Definition
Social app for real-time, authentic updates from friends
6-step onboarding flow
Based on typical social app onboarding patterns for location-based social apps
"""

CURRENTLY_STEPS = {
    "Welcome & Value Proposition": {
        "cognitive_demand": 0.1,
        "effort_demand": 0.0,
        "risk_signal": 0.0,
        "irreversibility": 0.0,
        "delay_to_value": 5,
        "explicit_value": 0.4,
        "reassurance_signal": 0.3,
        "authority_signal": 0.2,
        "description": "Welcome screen showing value proposition: real-time updates from friends, live map, spontaneous meetups. User sees what the app offers before committing."
    },
    "Phone Number Entry": {
        "cognitive_demand": 0.2,
        "effort_demand": 0.3,
        "risk_signal": 0.2,
        "irreversibility": 0.0,
        "delay_to_value": 4,
        "explicit_value": 0.2,
        "reassurance_signal": 0.4,
        "authority_signal": 0.2,
        "description": "User enters phone number to sign up. First data collection point. Privacy-conscious users may hesitate here."
    },
    "OTP Verification": {
        "cognitive_demand": 0.2,
        "effort_demand": 0.3,
        "risk_signal": 0.15,
        "irreversibility": 0.0,
        "delay_to_value": 3,
        "explicit_value": 0.2,
        "reassurance_signal": 0.5,
        "authority_signal": 0.3,
        "description": "User enters OTP received via SMS to verify phone number. Standard verification step."
    },
    "Profile Setup": {
        "cognitive_demand": 0.3,
        "effort_demand": 0.4,
        "risk_signal": 0.2,
        "irreversibility": 0.1,
        "delay_to_value": 2,
        "explicit_value": 0.3,
        "reassurance_signal": 0.4,
        "authority_signal": 0.2,
        "description": "User sets up profile: name, photo, bio. Personal information sharing. Some users may skip or provide minimal info."
    },
    "Location Permission": {
        "cognitive_demand": 0.4,
        "effort_demand": 0.2,
        "risk_signal": 0.6,
        "irreversibility": 0.3,
        "delay_to_value": 1,
        "explicit_value": 0.5,
        "reassurance_signal": 0.5,
        "authority_signal": 0.3,
        "description": "App requests location permission to show live map and friend locations. High privacy concern for many users. Critical for app functionality."
    },
    "Friend Discovery & Main Feed": {
        "cognitive_demand": 0.2,
        "effort_demand": 0.3,
        "risk_signal": 0.3,
        "irreversibility": 0.2,
        "delay_to_value": 0,
        "explicit_value": 1.0,
        "reassurance_signal": 0.6,
        "authority_signal": 0.4,
        "description": "User sees main feed with real-time updates from friends, live map showing friend locations, and can discover/connect with friends. Value delivery point - user finally sees what they came for."
    }
}

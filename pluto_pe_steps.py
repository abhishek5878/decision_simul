"""
Pluto PE Product Flow Definition
Crypto/Web3 fintech for crypto-native individuals in India
8-step onboarding flow
Extracted from actual screenshots
"""

PLUTO_PE_STEPS = {
    "Wallet Setup": {
        "cognitive_demand": 0.1,
        "effort_demand": 0.2,
        "risk_signal": 0.1,
        "irreversibility": 0.0,
        "delay_to_value": 6,
        "explicit_value": 0.4,
        "reassurance_signal": 0.5,
        "authority_signal": 0.2,
        "description": "User chooses to create a new wallet or import an existing one with a secret phrase."
    },
    "Legal": {
        "cognitive_demand": 0.3,
        "effort_demand": 0.4,
        "risk_signal": 0.2,
        "irreversibility": 0.0,
        "delay_to_value": 5,
        "explicit_value": 0.6,
        "reassurance_signal": 0.5,
        "authority_signal": 0.4,
        "description": "User reviews and accepts the Terms of Services and Privacy Policy before proceeding."
    },
    "Create Passcode": {
        "cognitive_demand": 0.2,
        "effort_demand": 0.2,
        "risk_signal": 0.1,
        "irreversibility": 0.5,
        "delay_to_value": 4,
        "explicit_value": 0.5,
        "reassurance_signal": 0.6,
        "authority_signal": 0.3,
        "description": "User sets up a 6-digit passcode for wallet security."
    },
    "Secret Phrase Backup": {
        "cognitive_demand": 0.3,
        "effort_demand": 0.1,
        "risk_signal": 0.5,
        "irreversibility": 0.0,
        "delay_to_value": 3,
        "explicit_value": 0.7,
        "reassurance_signal": 0.4,
        "authority_signal": 0.3,
        "description": "User is prompted to back up their secret phrase, essential for accessing their wallet."
    },
    "Select Phrase": {
        "cognitive_demand": 0.2,
        "effort_demand": 0.1,
        "risk_signal": 0.4,
        "irreversibility": 0.5,
        "delay_to_value": 2,
        "explicit_value": 0.6,
        "reassurance_signal": 0.5,
        "authority_signal": 0.3,
        "description": "User selects the correct phrase from a list as part of security setup."
    },
    "Spend Anywhere": {
        "cognitive_demand": 0.1,
        "effort_demand": 0.1,
        "risk_signal": 0.0,
        "irreversibility": 0.0,
        "delay_to_value": 1,
        "explicit_value": 0.5,
        "reassurance_signal": 0.6,
        "authority_signal": 0.2,
        "description": "User is introduced to the feature of spending cryptocurrency globally."
    },
    "One Wallet & Unlimited Possibilities": {
        "cognitive_demand": 0.1,
        "effort_demand": 0.1,
        "risk_signal": 0.0,
        "irreversibility": 0.0,
        "delay_to_value": 1,
        "explicit_value": 0.7,
        "reassurance_signal": 0.5,
        "authority_signal": 0.3,
        "description": "User is informed about the advantages of using one wallet for various functions."
    },
    "Wallet Balance": {
        "cognitive_demand": 0.2,
        "effort_demand": 0.2,
        "risk_signal": 0.2,
        "irreversibility": 0.0,
        "delay_to_value": 0,
        "explicit_value": 0.8,
        "reassurance_signal": 0.4,
        "authority_signal": 0.3,
        "description": "User views their wallet balance and options to receive, send, buy, swap, or sell cryptocurrency."
    }
}

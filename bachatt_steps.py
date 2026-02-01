"""
Bachatt Product Flow Definition
Automated wealth building for self-employed Indians with irregular income
3-step onboarding flow
Extracted from actual screenshots: ss1.jpeg, ss2.jpeg, ss3.jpeg
"""

BACHATT_STEPS = {
    "Enter your mobile number": {
        "cognitive_demand": 0.1,
        "effort_demand": 0.2,
        "risk_signal": 0.2,
        "irreversibility": 0.0,
        "delay_to_value": 2,
        "explicit_value": 0.4,
        "reassurance_signal": 0.5,
        "authority_signal": 0.2,
        "description": "Users are prompted to enter their Aadhaar-linked mobile number for OTP verification, with a focus on data consent for identity confirmation."
    },
    "Enter OTP": {
        "cognitive_demand": 0.2,
        "effort_demand": 0.2,
        "risk_signal": 0.25,
        "irreversibility": 0.0,
        "delay_to_value": 1,
        "explicit_value": 0.3,
        "reassurance_signal": 0.5,
        "authority_signal": 0.3,
        "description": "Users must input the OTP sent to their registered mobile number to verify their identity and continue the registration process."
    },
    "Save ₹101 daily": {
        "cognitive_demand": 0.3,
        "effort_demand": 0.3,
        "risk_signal": 0.1,
        "irreversibility": 0.0,
        "delay_to_value": 0,
        "explicit_value": 0.6,
        "reassurance_signal": 0.4,
        "authority_signal": 0.0,
        "description": "Users are prompted to select their saving frequency and amount, emphasizing potential long-term wealth growth to encourage regular saving habits."
    }
}

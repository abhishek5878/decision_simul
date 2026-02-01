"""
Blink Money Product Flow Definition (Improved - Intent-Aware)
Based on screenshots: Credit against Mutual Funds product
"""

BLINK_MONEY_STEPS_IMPROVED = {
    "Smart Credit against Mutual Funds": {
        # Behavioral attributes
        "cognitive_demand": 0.2,
        "effort_demand": 0.0,
        "risk_signal": 0.15,  # Credit product - moderate risk
        "irreversibility": 0,
        "delay_to_value": 3,  # 3 steps total
        "explicit_value": 0.5,  # Strong value prop: 9.99% p.a., up to ₹1 Crore, 2 hours approval
        "reassurance_signal": 0.6,  # Interest only EMI, clear terms
        "authority_signal": 0.3,
        
        # Intent-aware attributes
        "cta_phrasing": "Check Eligibility In 10s",
        "value_proposition": "Credit against mutual funds, wedding loan, eligibility check",
        "commitment_gate": False,
        "comparison_available": False,
        "personal_info_required": False,
        "intent_signals": {
            "compare_options": 0.2,  # Low - not about comparison
            "quick_decision": 0.8,   # HIGH - "10s" promise
            "learn_basics": 0.3,
            "eligibility_check": 0.9,  # VERY HIGH - "Check Eligibility"
            "price_check": 0.4,     # Moderate - shows rates
            "validate_choice": 0.3
        },
        "description": "Landing page - Credit against mutual funds, wedding loan, eligibility check promise"
    },
    "Check Your Eligibility - Mobile Number": {
        "cognitive_demand": 0.3,
        "effort_demand": 0.3,  # Enter mobile number
        "risk_signal": 0.25,  # Sharing phone number, bureau checks mentioned
        "irreversibility": 0,
        "delay_to_value": 2,
        "explicit_value": 0.4,  # Free flight vouchers up to ₹1,000 mentioned
        "reassurance_signal": 0.5,  # Terms and privacy policy
        "authority_signal": 0.2,
        
        # Intent-aware
        "cta_phrasing": "Continue",
        "value_proposition": "Mobile number entry for eligibility check",
        "commitment_gate": False,  # Just phone number
        "comparison_available": False,
        "personal_info_required": True,  # Phone number
        "intent_signals": {
            "compare_options": 0.2,
            "quick_decision": 0.6,   # Still fast
            "learn_basics": 0.3,
            "eligibility_check": 0.8,  # HIGH - checking eligibility
            "price_check": 0.3,
            "validate_choice": 0.3
        },
        "description": "Mobile number entry - linked to mutual funds, referral code option"
    },
    "Check Limit - PAN and DOB": {
        "cognitive_demand": 0.4,
        "effort_demand": 0.4,  # Enter PAN and DOB
        "risk_signal": 0.4,  # PAN is sensitive financial info
        "irreversibility": 0,
        "delay_to_value": 1,
        "explicit_value": 0.5,  # "Check eligible loan limit without impact on credit score"
        "reassurance_signal": 0.6,  # No credit score impact, secure verification
        "authority_signal": 0.4,
        
        # Intent-aware - HIGH COMMITMENT GATE
        "cta_phrasing": "Verify",
        "value_proposition": "PAN and DOB verification for credit limit check",
        "commitment_gate": True,  # PAN = high commitment
        "comparison_available": False,
        "personal_info_required": True,  # Very sensitive - PAN
        "intent_signals": {
            "compare_options": 0.2,
            "quick_decision": 0.5,   # Getting slower
            "learn_basics": 0.2,
            "eligibility_check": 0.7,  # HIGH - checking eligibility/limit
            "price_check": 0.3,
            "validate_choice": 0.4
        },
        "description": "PAN and date of birth verification - credit limit check"
    }
}

"""
Credigo SS 11-Step Product Flow Definition (Improved)
Based on actual Credigo.club screenshots with intent-aware architecture integration

This version is optimized for:
- Intent inference (CTA phrasing, value signals, commitment gates)
- Intent-step alignment scoring
- Behavioral simulation coherence
"""

CREDIGO_SS_11_STEPS = {
    "Find the Best Credit Card In 60 seconds": {
        # Behavioral attributes
        "cognitive_demand": 0.2,
        "effort_demand": 0.0,
        "risk_signal": 0.1,
        "irreversibility": 0,
        "delay_to_value": 10,  # 11 steps total
        "explicit_value": 0.3,
        "reassurance_signal": 0.6,  # "No PAN, no data" is strong
        "authority_signal": 0.2,
        
        # Intent-aware attributes
        "cta_phrasing": "Find the Best Credit Card In 60 seconds",  # Speed + comparison signal
        "value_proposition": "Quick credit card comparison and recommendation",
        "commitment_gate": False,  # No commitment required
        "comparison_available": False,  # No comparison shown yet
        "personal_info_required": False,
        "intent_signals": {
            "compare_options": 0.7,  # "Find the Best" = comparison intent
            "quick_decision": 0.8,   # "60 seconds" = speed intent
            "learn_basics": 0.3,     # Low - not educational
            "eligibility_check": 0.2,  # Low - not about eligibility
            "price_check": 0.4,     # Moderate - might want to see prices
            "validate_choice": 0.3   # Low - no choice to validate yet
        },
        "description": "Landing page - 60 second promise, privacy claims, 'Find the Best' CTA"
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
        
        # Intent-aware
        "cta_phrasing": "Continue",  # Generic continuation
        "value_proposition": "Personalization question - no value yet",
        "commitment_gate": False,
        "comparison_available": False,  # Still no comparison
        "personal_info_required": False,  # Just preference
        "intent_signals": {
            "compare_options": 0.3,  # Low - no comparison shown
            "quick_decision": 0.4,   # Moderate - still early
            "learn_basics": 0.5,     # Moderate - learning about product
            "eligibility_check": 0.2,
            "price_check": 0.2,
            "validate_choice": 0.3
        },
        "description": "First question - perks preference, no comparison yet"
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
        
        # Intent-aware
        "cta_phrasing": "Continue",
        "value_proposition": "Price-related question but no prices shown",
        "commitment_gate": False,
        "comparison_available": False,
        "personal_info_required": False,
        "intent_signals": {
            "compare_options": 0.3,  # Still no comparison
            "quick_decision": 0.3,   # Getting slower
            "learn_basics": 0.4,
            "eligibility_check": 0.2,
            "price_check": 0.6,     # Price-related question
            "validate_choice": 0.3
        },
        "description": "Annual fee preference question - price signal but no prices"
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
        
        # Intent-aware
        "cta_phrasing": "Continue",
        "value_proposition": "Reassurance about simplicity",
        "commitment_gate": False,
        "comparison_available": False,
        "personal_info_required": False,
        "intent_signals": {
            "compare_options": 0.4,  # "Options" mentioned but not shown
            "quick_decision": 0.5,   # "Straightforward" = speed signal
            "learn_basics": 0.6,     # Educational reassurance
            "eligibility_check": 0.2,
            "price_check": 0.3,
            "validate_choice": 0.4
        },
        "description": "Clarification step - options defined but not shown"
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
        
        # Intent-aware - HIGH COMMITMENT GATE
        "cta_phrasing": "Continue",
        "value_proposition": "Personal spending info required",
        "commitment_gate": True,  # Personal financial info = commitment
        "comparison_available": False,  # Still no comparison!
        "personal_info_required": True,  # Spending categories = personal
        "intent_signals": {
            "compare_options": 0.2,  # Very low - asked for info before showing options
            "quick_decision": 0.2,   # Low - slowing down
            "learn_basics": 0.3,
            "eligibility_check": 0.3,
            "price_check": 0.2,
            "validate_choice": 0.2
        },
        "description": "Spend categories question - PERSONAL INFO BEFORE COMPARISON (intent mismatch risk)"
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
        
        # Intent-aware
        "cta_phrasing": "Continue",
        "value_proposition": "More personal financial questions",
        "commitment_gate": True,
        "comparison_available": False,
        "personal_info_required": True,
        "intent_signals": {
            "compare_options": 0.2,  # Still no comparison
            "quick_decision": 0.2,
            "learn_basics": 0.3,
            "eligibility_check": 0.4,  # Spending tracking = eligibility signal
            "price_check": 0.2,
            "validate_choice": 0.2
        },
        "description": "Spending tracking question - more personal info"
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
        
        # Intent-aware - HIGH RISK COMMITMENT GATE
        "cta_phrasing": "Continue",
        "value_proposition": "Sensitive financial information",
        "commitment_gate": True,
        "comparison_available": False,
        "personal_info_required": True,  # Very sensitive
        "intent_signals": {
            "compare_options": 0.1,  # Very low - major mismatch
            "quick_decision": 0.1,   # Very low - too slow
            "learn_basics": 0.2,
            "eligibility_check": 0.5,  # Spending amount = eligibility
            "price_check": 0.3,
            "validate_choice": 0.2
        },
        "description": "Monthly spending amount - SENSITIVE INFO BEFORE VALUE (major intent mismatch)"
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
        
        # Intent-aware
        "cta_phrasing": "Continue",
        "value_proposition": "Context about existing cards",
        "commitment_gate": False,  # Less sensitive
        "comparison_available": False,
        "personal_info_required": False,  # Just yes/no
        "intent_signals": {
            "compare_options": 0.3,
            "quick_decision": 0.4,   # Getting closer
            "learn_basics": 0.3,
            "eligibility_check": 0.4,
            "price_check": 0.3,
            "validate_choice": 0.5   # Validating existing choice
        },
        "description": "Existing cards question - less sensitive"
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
        
        # Intent-aware - ANTICIPATION BUILDING
        "cta_phrasing": "Continue",
        "value_proposition": "Personalization - value coming soon",
        "commitment_gate": False,
        "comparison_available": False,  # Still not shown!
        "personal_info_required": False,
        "intent_signals": {
            "compare_options": 0.5,  # "Matches" = comparison coming
            "quick_decision": 0.6,   # Getting close
            "learn_basics": 0.4,
            "eligibility_check": 0.5,
            "price_check": 0.4,
            "validate_choice": 0.6   # "Matches" = validation coming
        },
        "description": "Personalization step - building anticipation, value soon"
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
        
        # Intent-aware - PROGRESS SIGNAL
        "cta_phrasing": "Continue",
        "value_proposition": "Progress indicator - almost done",
        "commitment_gate": False,
        "comparison_available": False,  # Still waiting!
        "personal_info_required": False,
        "intent_signals": {
            "compare_options": 0.6,  # Almost there
            "quick_decision": 0.7,   # Very close
            "learn_basics": 0.5,
            "eligibility_check": 0.6,
            "price_check": 0.5,
            "validate_choice": 0.7   # Almost at validation
        },
        "description": "Progress indicator - almost done, value imminent"
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
        
        # Intent-aware - VALUE DELIVERED
        "cta_phrasing": "Apply Now",  # Action CTA
        "value_proposition": "Personalized card recommendations shown",
        "commitment_gate": False,  # Value shown first
        "comparison_available": True,  # FINALLY - comparison shown!
        "personal_info_required": False,
        "intent_signals": {
            "compare_options": 0.9,  # HIGH - comparison finally shown
            "quick_decision": 0.8,   # HIGH - can decide now
            "learn_basics": 0.6,
            "eligibility_check": 0.7,  # Eligibility implied
            "price_check": 0.8,     # HIGH - prices/deals shown
            "validate_choice": 0.8   # HIGH - can validate now
        },
        "description": "Results page - recommendations shown, comparison available, apply CTA"
    }
}


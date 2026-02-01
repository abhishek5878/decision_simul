"""
Keeper SS Product Flow Definition
Based on screenshots: Leave Liability Calculator / HR Analytics product
10 steps total
"""

KEEPER_SS_STEPS = {
    "Check Paid Leave Balance": {
        "cognitive_demand": 0.2,
        "effort_demand": 0.0,
        "risk_signal": 0.1,
        "irreversibility": 0,
        "delay_to_value": 9,  # 10 steps total
        "explicit_value": 0.4,  # Value prop: unlock value of paid leaves
        "reassurance_signal": 0.5,
        "authority_signal": 0.3,
        "intent_signals": {
            "calculate_leave_liability": 0.8,  # High alignment - this is exactly what they want
        },
        "comparison_available": False,
        "description": "Landing page - Check paid leave balance, book demo"
    },
    "What is the average leave balance of your employees?": {
        "cognitive_demand": 0.4,
        "effort_demand": 0.3,  # Need to recall/calculate average leave balance
        "risk_signal": 0.15,  # Sharing employee data
        "irreversibility": 0,
        "delay_to_value": 8,
        "explicit_value": 0.2,  # "Every unused leave hits your books harder"
        "reassurance_signal": 0.4,
        "authority_signal": 0.2,
        "intent_signals": {
            "compare_credit_cards": 0.2,  # Very low alignment
        },
        "comparison_available": False,
        "description": "Input: Average leave balance in days"
    },
    "What is the max leave encashment at your organization?": {
        "cognitive_demand": 0.3,
        "effort_demand": 0.2,  # Select from options (30, 35, 40, 45 days or custom)
        "risk_signal": 0.15,
        "irreversibility": 0,
        "delay_to_value": 7,
        "explicit_value": 0.2,
        "reassurance_signal": 0.4,
        "authority_signal": 0.2,
        "intent_signals": {
            "compare_credit_cards": 0.2,
        },
        "comparison_available": False,
        "description": "Select max leave encashment policy"
    },
    "What is the average annual employee growth rate (%) in your organization?": {
        "cognitive_demand": 0.4,
        "effort_demand": 0.3,  # Need to recall/calculate growth rate
        "risk_signal": 0.2,  # Sharing organizational metrics
        "irreversibility": 0,
        "delay_to_value": 6,
        "explicit_value": 0.2,
        "reassurance_signal": 0.4,
        "authority_signal": 0.2,
        "intent_signals": {
            "compare_credit_cards": 0.2,
        },
        "comparison_available": False,
        "description": "Input: Average annual employee growth rate percentage"
    },
    "What is your attrition rate?": {
        "cognitive_demand": 0.4,
        "effort_demand": 0.3,  # Need to recall/calculate attrition rate
        "risk_signal": 0.25,  # Sensitive organizational metric
        "irreversibility": 0,
        "delay_to_value": 5,
        "explicit_value": 0.2,
        "reassurance_signal": 0.4,
        "authority_signal": 0.2,
        "intent_signals": {
            "compare_credit_cards": 0.2,
        },
        "comparison_available": False,
        "description": "Input: Attrition rate percentage"
    },
    "What is your total monthly payout (salaries) to full-time employees? (in Crores)": {
        "cognitive_demand": 0.5,
        "effort_demand": 0.4,  # Need to calculate total monthly payout
        "risk_signal": 0.4,  # Sensitive financial data
        "irreversibility": 0,
        "delay_to_value": 4,
        "explicit_value": 0.3,  # Financial impact calculation
        "reassurance_signal": 0.5,
        "authority_signal": 0.3,
        "intent_signals": {
            "compare_credit_cards": 0.2,
        },
        "comparison_available": False,
        "description": "Input: Total monthly salary payout in Crores"
    },
    "What is the total no of employees in your organization?": {
        "cognitive_demand": 0.3,
        "effort_demand": 0.2,  # Simple number input
        "risk_signal": 0.2,
        "irreversibility": 0,
        "delay_to_value": 3,
        "explicit_value": 0.2,
        "reassurance_signal": 0.4,
        "authority_signal": 0.2,
        "intent_signals": {
            "compare_credit_cards": 0.2,
        },
        "comparison_available": False,
        "description": "Input: Total number of employees"
    },
    "What is the average Salary Hike % in your organisation?": {
        "cognitive_demand": 0.4,
        "effort_demand": 0.3,  # Need to recall/calculate salary hike %
        "risk_signal": 0.3,  # Sensitive compensation data
        "irreversibility": 0,
        "delay_to_value": 2,
        "explicit_value": 0.2,
        "reassurance_signal": 0.4,
        "authority_signal": 0.2,
        "intent_signals": {
            "compare_credit_cards": 0.2,
        },
        "comparison_available": False,
        "description": "Input: Average salary hike percentage"
    },
    "What is your work email?": {
        "cognitive_demand": 0.2,
        "effort_demand": 0.2,  # Simple email input
        "risk_signal": 0.15,  # Sharing work email
        "irreversibility": 0,
        "delay_to_value": 1,
        "explicit_value": 0.3,  # Getting closer to results
        "reassurance_signal": 0.5,
        "authority_signal": 0.3,
        "intent_signals": {
            "compare_credit_cards": 0.2,
        },
        "comparison_available": False,
        "description": "Input: Work email address"
    },
    "Step 1 of 10": {
        "cognitive_demand": 0.3,
        "effort_demand": 0.1,  # View results/calculations
        "risk_signal": 0.1,
        "irreversibility": 0,
        "delay_to_value": 0,  # Value delivered: Leave liability report
        "explicit_value": 0.8,  # High value: See calculations, financial impact visualization
        "reassurance_signal": 0.6,
        "authority_signal": 0.4,
        "intent_signals": {
            "compare_credit_cards": 0.2,
        },
        "comparison_available": False,
        "description": "Results page - See calculations, leave liability report (₹1.97 Cr shown)"
    }
}


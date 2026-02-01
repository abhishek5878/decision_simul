"""
Novelty Wealth Product Flow Definition

Wealth / investing product with a 6-step onboarding / decision flow.
This file defines abstract step characteristics so the decision engine
can reason about cognitive load, effort, risk and value timing.

The steps are ordered to match the screenshot sequence in the
`novelty_wealth/` folder:
  ss1.png -> ss2.PNG -> ss3.PNG -> ss4.PNG -> ss5.PNG -> ss6.PNG
"""

NOVELTY_WEALTH_STEPS = {
    # 1. Landing page — users arrive here from ad / link
    "Landing & Promise (ss1)": {
        "cognitive_demand": 0.15,
        "effort_demand": 0.05,
        "risk_signal": 0.05,
        "irreversibility": 0.0,
        # User is still many steps away from seeing concrete value (portfolio, returns, plan)
        "delay_to_value": 5,
        "explicit_value": 0.4,
        "reassurance_signal": 0.4,
        "authority_signal": 0.3,
        "description": "Initial landing screen from ss1.png that introduces the Novelty Wealth proposition and promise, before any data or commitment is requested."
    },
    # 2. Light intro / high-level framing (if present in ss2)
    "Framing & What You Get (ss2)": {
        "cognitive_demand": 0.2,
        "effort_demand": 0.15,
        "risk_signal": 0.1,
        "irreversibility": 0.0,
        # Still multiple steps away from the final wealth plan / investment view
        "delay_to_value": 4,
        "explicit_value": 0.5,
        "reassurance_signal": 0.5,
        "authority_signal": 0.35,
        "description": "Framing screen from ss2.PNG that explains how Novelty Wealth works and what kind of plan or portfolio the user will see if they continue."
    },
    # 3. Goals / profile capture
    "Profile & Goals (ss3)": {
        "cognitive_demand": 0.3,
        "effort_demand": 0.3,
        "risk_signal": 0.15,
        "irreversibility": 0.05,
        # User is now a few steps away from seeing a draft plan
        "delay_to_value": 3,
        "explicit_value": 0.5,
        "reassurance_signal": 0.5,
        "authority_signal": 0.35,
        "description": "Questionnaire screen from ss3.PNG where users share basic profile and financial goals so the product can tailor a plan."
    },
    # 4. Income / contributions capture
    "Income & Contributions (ss4)": {
        "cognitive_demand": 0.35,
        "effort_demand": 0.4,
        "risk_signal": 0.35,
        "irreversibility": 0.15,
        # User is getting close to seeing the actual portfolio or projections
        "delay_to_value": 2,
        "explicit_value": 0.6,
        "reassurance_signal": 0.55,
        "authority_signal": 0.4,
        "description": "Data entry screen from ss4.PNG where users provide income / contribution details so the engine can generate a concrete wealth plan."
    },
    # 5. Plan / options preview
    "Plan / Options Preview (ss5)": {
        "cognitive_demand": 0.3,
        "effort_demand": 0.25,
        "risk_signal": 0.25,
        "irreversibility": 0.2,
        # User effectively sees value here (proposed plan / portfolio), so delay becomes small
        "delay_to_value": 1,
        "explicit_value": 0.85,
        "reassurance_signal": 0.65,
        "authority_signal": 0.45,
        "description": "Preview screen from ss5.PNG showing a proposed plan or investment options so users can see what they might get."
    },
    # 6. Account / KYC / funding commitment
    "Account / KYC Commitment (ss6)": {
        "cognitive_demand": 0.35,
        "effort_demand": 0.35,
        "risk_signal": 0.6,
        "irreversibility": 0.5,
        # This is the value delivery / activation step, so delay_to_value is 0
        "delay_to_value": 0,
        "explicit_value": 1.0,
        "reassurance_signal": 0.7,
        "authority_signal": 0.5,
        "description": "Final screen from ss6.PNG where users are asked to commit (e.g., complete KYC, link money, or activate their Novelty Wealth plan)."
    }
}


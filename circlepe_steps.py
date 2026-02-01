"""
CirclePe WhatsApp Onboarding Flow - Product Steps
Based on WhatsApp Business bot flow for zero security deposit rental platform
"""

CIRCLEPE_STEPS = {
    "Entry": {
        "step_number": 0,
        "step_name": "Entry",
        "description": "User clicks wa.me link or messages CirclePe directly. Bot triggers immediately with welcome message.",
        "cognitive_demand": 0.1,
        "effort": 0.1,
        "risk": 0.0,
        "value": 0.2,
        "irreversible": 0.0,
        "explicit_value": False,
        "delay_to_value": 5
    },
    "Welcome & Personalization": {
        "step_number": 1,
        "step_name": "Welcome & Personalization",
        "description": "Greeting with user name, welcome message 'Welcome to CirclePe Club (An IIT-IIM Venture) 🎉', full-screen image/carousel showing 'You are just ONE STEP AWAY to unlock the ZERO Security Deposit' with trust logos (Paytm, BharatPe, OYO, Uni). Buttons: Services (Tenant/Landlord) or Got a query?",
        "cognitive_demand": 0.2,
        "effort": 0.1,
        "risk": 0.1,
        "value": 0.3,
        "irreversible": 0.0,
        "explicit_value": False,
        "delay_to_value": 4
    },
    "User Type Selection": {
        "step_number": 2,
        "step_name": "User Type Selection",
        "description": "Branch point: User selects Tenant or Landlord from Services list. This determines the path forward.",
        "cognitive_demand": 0.3,
        "effort": 0.2,
        "risk": 0.1,
        "value": 0.2,
        "irreversible": 0.1,
        "explicit_value": False,
        "delay_to_value": 3
    },
    "Tenant Path - Eligibility Check": {
        "step_number": 3,
        "step_name": "Tenant Path - Eligibility Check",
        "description": "For Tenant: Prompt 'Have you checked your eligibility on CirclePe?' with Yes/No options. If No, shows 3-step process card: Check eligibility ✅, Share property & rent details 🏠, Expert will call ☎️. Big button: 'Check My Eligibility' redirects to CirclePe Android app (no in-chat form).",
        "cognitive_demand": 0.4,
        "effort": 0.3,
        "risk": 0.2,
        "value": 0.4,
        "irreversible": 0.2,
        "explicit_value": False,
        "delay_to_value": 2
    },
    "Landlord Path - Benefits or Property": {
        "step_number": 3,
        "step_name": "Landlord Path - Benefits or Property",
        "description": "For Landlord: Shows benefits (Advance Rent Payout 8-10 months, Additional Security Deposit, Vetted Tenants). Options: Calculate Adv Rent (redirects to app), Rent My Property (asks for city input), Talk to Expert (agent handover).",
        "cognitive_demand": 0.4,
        "effort": 0.3,
        "risk": 0.2,
        "value": 0.5,
        "irreversible": 0.2,
        "explicit_value": True,
        "delay_to_value": 1
    },
    "App Redirect or Agent Handover": {
        "step_number": 4,
        "step_name": "App Redirect or Agent Handover",
        "description": "Final step: User is redirected to CirclePe app for eligibility check/advance rent calculation, OR live agent takes over via chat/call. Bot does not handle docs upload, payments, agreements - all in app + agent coordination.",
        "cognitive_demand": 0.5,
        "effort": 0.4,
        "risk": 0.3,
        "value": 0.7,
        "irreversible": 0.3,
        "explicit_value": True,
        "delay_to_value": 0
    }
}

# Simplified flow for simulation (combining tenant/landlord paths)
CIRCLEPE_STEPS_SIMPLIFIED = {
    "Entry": {
        "cognitive_demand": 0.1,
        "effort_demand": 0.1,
        "risk_signal": 0.0,
        "irreversibility": 0.0,
        "delay_to_value": 4,
        "explicit_value": 0.0,
        "reassurance_signal": 0.3,
        "authority_signal": 0.2,
        "description": "User clicks wa.me link or messages CirclePe directly. Bot triggers immediately with welcome message. Low friction entry point via familiar WhatsApp interface."
    },
    "Welcome & Personalization": {
        "cognitive_demand": 0.2,
        "effort_demand": 0.1,
        "risk_signal": 0.1,
        "irreversibility": 0.0,
        "delay_to_value": 3,
        "explicit_value": 0.0,
        "reassurance_signal": 0.6,
        "authority_signal": 0.7,
        "description": "Greeting with user name, welcome message 'Welcome to CirclePe Club (An IIT-IIM Venture) 🎉', full-screen image/carousel showing 'You are just ONE STEP AWAY to unlock the ZERO Security Deposit' with trust logos (Paytm, BharatPe, OYO, Uni). Buttons: Services (Tenant/Landlord) or Got a query?. Strong authority signals from IIT-IIM branding and partner logos."
    },
    "User Type Selection": {
        "cognitive_demand": 0.3,
        "effort_demand": 0.2,
        "risk_signal": 0.1,
        "irreversibility": 0.1,
        "delay_to_value": 2,
        "explicit_value": 0.0,
        "reassurance_signal": 0.4,
        "authority_signal": 0.5,
        "description": "Branch point: User selects Tenant or Landlord from Services list. This determines the path forward. Simple choice but commits user to a specific flow path."
    },
    "Path-Specific Interaction": {
        "cognitive_demand": 0.4,
        "effort_demand": 0.3,
        "risk_signal": 0.2,
        "irreversibility": 0.2,
        "delay_to_value": 1,
        "explicit_value": 0.5,
        "reassurance_signal": 0.5,
        "authority_signal": 0.4,
        "description": "Tenant: Eligibility check prompt with app redirect button. Landlord: Benefits display with advance rent calculator or property listing prompt. Both paths show value proposition (zero deposit for tenants, advance rent for landlords) but require app redirect or agent handover. Value becomes clearer here."
    },
    "App Redirect or Agent Handover": {
        "cognitive_demand": 0.5,
        "effort_demand": 0.4,
        "risk_signal": 0.3,
        "irreversibility": 0.3,
        "delay_to_value": 0,
        "explicit_value": 0.8,
        "reassurance_signal": 0.6,
        "authority_signal": 0.5,
        "description": "Final step: User is redirected to CirclePe app for eligibility check/advance rent calculation, OR live agent takes over via chat/call. Bot does not handle docs upload, payments, agreements - all in app + agent coordination. Highest value moment but also highest friction (app download/install or waiting for agent)."
    }
}

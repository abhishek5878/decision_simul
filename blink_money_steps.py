"""
Blink Money Product Flow Definition
Credit against Mutual Funds - COMPLETE analysis from screenshots
5-step onboarding flow
Every visible element captured - no detail missed
"""

BLINK_MONEY_STEPS = {
    "Smart Credit Exploration": {
        "cognitive_demand": 0.2,
        "effort_demand": 0.2,
        "risk_signal": 0.1,
        "irreversibility": 0.0,
        "delay_to_value": 4,
        "explicit_value": 0.0,
        "reassurance_signal": 0.5,
        "authority_signal": 0.4,
        "description": "Users are prompted to explore credit options with the title 'Smart Credit against Mutual Funds for your dream Career'. The button 'Know Your Limit' invites users to check their credit limit, emphasizing the financial benefit of saving interest with BlinkMoney.. Available actions: Check Eligibility, Get Started, Let\u2019s Go. Visible numbers/amounts: \u20b912,001 (Save in interest), 4 (steps to avail loan)."
    },
    "Eligibility Check for Credit": {
        "cognitive_demand": 0.3,
        "effort_demand": 0.5,
        "risk_signal": 0.2,
        "irreversibility": 0.0,
        "delay_to_value": 3,
        "explicit_value": 0.0,
        "reassurance_signal": 0.6,
        "authority_signal": 0.3,
        "description": "PRIMARY ACTION: Users must fill in a PHONE NUMBER INPUT FIELD (mobile number) to proceed to the next step. This is the main action that moves the user forward. SECONDARY: There is also a NUMBER INPUT FIELD labeled 'How much is your fund?' to enter mutual fund amount (format: currency/numeric, e.g., \u20b910,000, \u20b91,00,000, \u20b910,00,000). There is a toggle option labeled 'I have current funds'. The button 'Check Eligibility' submits the form and takes user to step 3. CONTEXT (below fold, informational only): Benefits section includes 'No selling of funds', 'Instant credit in just 2 hours', 'Pay only interest', 'Completely digital process', and 'No credit score impact'. Testimonials, FAQs, partner logos, and 'Why BlinkMoney?' section provide context but are not required actions. Progress indicator shows 'Step 2 of 5' (40% complete). Visible numbers/amounts: \u20b910,000 (minimum credit amount), \u20b91,00,000 (loan amount option), \u20b910,00,000 (maximum loan amount), 12 months (loan tenure option)."
    },
    "PAN & DOB Input": {
        "cognitive_demand": 0.2,
        "effort_demand": 0.5,
        "risk_signal": 0.7,
        "irreversibility": 0.0,
        "delay_to_value": 2,
        "explicit_value": 0.0,
        "reassurance_signal": 0.6,
        "authority_signal": 0.2,
        "description": "Users are asked to enter their PAN and date of birth in the fields labeled 'Enter PAN' and 'Date of Birth'. The button 'Verify' checks their eligibility. A disclaimer mentions acceptance of T&Cs and indicates that checking does not impact the credit score.. Users must fill in a text input field labeled 'Enter PAN' (format: 10 characters) with placeholder 'PAN ID'. Users must fill in a dropdown field labeled 'Date of Birth' with placeholder 'Select date'. Available actions: Verify."
    },
    "OTP Verification": {
        "cognitive_demand": 0.1,
        "effort_demand": 0.2,
        "risk_signal": 0.6,
        "irreversibility": 0.0,
        "delay_to_value": 1,
        "explicit_value": 0.0,
        "reassurance_signal": 0.0,
        "authority_signal": 0.0,
        "description": "Users must input a 6-digit OTP sent to their registered phone number to verify their identity. The screen features a timer indicating time left to enter the OTP and options to 'Verify' or 'Resend OTP'. There are no visible trust signals or explicit benefits.. Users must fill in a text input field labeled '6-digit OTP' (format: 6 digits). Available actions: Verify, Resend OTP. Visible numbers/amounts: 00:25 (countdown timer for OTP)."
    },
    "Eligibility Confirmation": {
        "cognitive_demand": 0.2,
        "effort_demand": 0.1,
        "risk_signal": 0.0,
        "irreversibility": 0.0,
        "delay_to_value": 0,
        "explicit_value": 1.0,
        "reassurance_signal": 0.5,
        "authority_signal": 0.3,
        "description": "Users see their eligibility confirmed with the message 'You\u2019re eligible for upto \u20b9 1,59,300'. The 'Proceed' button allows users to continue to the next step, and there's an option to learn more about how the credit amount is calculated. The screen suggests empowerment with phrases like 'Unlock your bold dreams with smart credit'.. Users must fill in a number input field labeled 'Loan Amount' (format: currency/numeric) with placeholder '\u20b9 25,600'. Users must fill in a date picker field labeled 'Loan Tenure' (format: numeric/duration) with placeholder '1 years - 5 years'. Available actions: Proceed. Visible numbers/amounts: \u20b91,59,300 (Eligible amount), \u20b925,600 (Loan Amount), 1 years (Minimum Loan Tenure), 5 years (Maximum Loan Tenure), \u20b924,000 (Personal Loan cost), \u20b918,923 (Selling Mutual Fund opportunity cost)."
    }
}

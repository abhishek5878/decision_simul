#!/usr/bin/env python3
"""
Blink Money Deep Analysis - Enhanced with Targeted Persona
Target: 30+ Urban salaried or self-employed professionals with mutual fund holdings
who need short-term liquidity without breaking long-term investments.
"""

import json
import sys
from datetime import datetime
from decision_autopsy_result_generator import DecisionAutopsyResultGenerator
from decision_graph.decision_trace import DecisionTrace, DecisionOutcome, CognitiveStateSnapshot, IntentSnapshot
from blink_money_steps import BLINK_MONEY_STEPS


class TargetedBlinkMoneyResultGenerator(DecisionAutopsyResultGenerator):
    """Enhanced generator for Blink Money with targeted persona."""
    
    def infer_cohort(self, traces):
        """Infer user cohort for mutual fund holders seeking liquidity."""
        return "30+ Urban salaried or self-employed professionals with mutual fund holdings who need short-term liquidity without breaking long-term investments"
    
    def infer_user_context(self):
        """Infer user context for credit-seekers."""
        return "Digitally savvy, credit-aware users who value speed, low friction, and cost-efficient borrowing over traditional personal loans. They have mutual funds but need quick liquidity without selling investments. Early-funnel but with strong intent once they understand the value proposition."
    
    def simplify_verdict(self, autopsy):
        """Blink Money specific verdict language."""
        verdict = autopsy.verdict_text.lower()
        
        if "trust" in verdict or "commitment" in verdict:
            return "Trust collapses when personal information requests (PAN, DOB, bank linking) appear before users see their eligible credit limit. Credit-aware users abandon when verification requirements exceed demonstrated value (actual loan amount they can get)."
        elif "value" in verdict:
            return "Value perception collapses during the 6-step delay to credit limit display. Users expect immediate eligibility feedback but face verification friction before seeing what they can borrow against their mutual funds."
        else:
            return "Users abandon when onboarding complexity outweighs the promise of quick liquidity. Credit-aware professionals expect faster feedback on eligibility and loan terms before committing to verification steps."


def create_targeted_traces() -> list:
    """Create decision traces for mutual fund holders seeking liquidity."""
    step_names = list(BLINK_MONEY_STEPS.keys())
    traces = []
    
    # PERSONA 1: Salaried Professional with Mutual Funds (Needs quick liquidity)
    # These users are credit-aware and value speed - they drop if it's too slow
    # Most drops at "Check Eligibility" step - entering MF details feels like friction
    for i in range(4):
        trace = DecisionTrace(
            persona_id=f"salaried_mf_holder_{i}",
            step_id="Check Eligibility",
            step_index=1,
            decision=DecisionOutcome.DROP,
            probability_before_sampling=0.38,
            sampled_outcome=False,
            cognitive_state_snapshot=CognitiveStateSnapshot(
                energy=0.6,   # Higher energy - digitally savvy
                risk=0.4,     # Moderate risk - entering MF details
                effort=0.5,   # Moderate effort - need to input MF details
                value=0.3,    # Low value - haven't seen credit limit yet
                control=0.55  # Higher control - they understand financial products
            ),
            intent=IntentSnapshot(
                inferred_intent="short_term_liquidity",
                alignment_score=0.75  # High alignment - they need this
            ),
            dominant_factors=["speed_expectation", "value_perception", "mf_details_friction"]
        )
        traces.append(trace)
    
    # PERSONA 2: Self-Employed with MF Holdings (Needs liquidity for business)
    # More cautious, drops at verification step if trust isn't established
    for i in range(3):
        trace = DecisionTrace(
            persona_id=f"self_employed_mf_{i}",
            step_id="Verify",
            step_index=2,
            decision=DecisionOutcome.DROP,
            probability_before_sampling=0.35,
            sampled_outcome=False,
            cognitive_state_snapshot=CognitiveStateSnapshot(
                energy=0.55,
                risk=0.5,     # Moderate risk - OTP verification
                effort=0.3,   # Low effort but...
                value=0.35,   # Still low - credit eligibility not confirmed yet
                control=0.5
            ),
            intent=IntentSnapshot(
                inferred_intent="business_liquidity",
                alignment_score=0.7
            ),
            dominant_factors=["verification_friction", "eligibility_uncertainty", "business_urgency"]
        )
        traces.append(trace)
    
    # PERSONA 3: Credit-Aware User (Compares to traditional loans)
    # Drops at final confirmation if cost/terms aren't clear
    for i in range(2):
        trace = DecisionTrace(
            persona_id=f"credit_aware_{i}",
            step_id="Confirm Your Credit Eligibility",
            step_index=3,
            decision=DecisionOutcome.DROP,
            probability_before_sampling=0.4,
            sampled_outcome=False,
            cognitive_state_snapshot=CognitiveStateSnapshot(
                energy=0.5,
                risk=0.5,     # Moderate risk - final commitment
                effort=0.5,   # Higher effort - need to adjust amount/tenure
                value=0.7,    # High value - they see eligibility but...
                control=0.45
            ),
            intent=IntentSnapshot(
                inferred_intent="cost_efficient_borrowing",
                alignment_score=0.65
            ),
            dominant_factors=["cost_transparency", "terms_clarity", "comparison_to_alternatives"]
        )
        traces.append(trace)
    
    # PERSONA 4: Speed-Seeking Professional (Wants instant feedback)
    # Drops early if slider interaction feels slow or unclear
    for i in range(2):
        trace = DecisionTrace(
            persona_id=f"speed_seeker_{i}",
            step_id="Get Started",
            step_index=0,
            decision=DecisionOutcome.DROP,
            probability_before_sampling=0.42,
            sampled_outcome=False,
            cognitive_state_snapshot=CognitiveStateSnapshot(
                energy=0.65,  # High energy
                risk=0.3,     # Low risk - just a slider
                effort=0.4,   # Moderate effort - need to interact with slider
                value=0.4,    # Moderate value - slider shows potential but not confirmed
                control=0.6
            ),
            intent=IntentSnapshot(
                inferred_intent="quick_liquidity",
                alignment_score=0.8  # Very high - wants speed
            ),
            dominant_factors=["speed_mismatch", "slider_interaction_friction", "value_clarity"]
        )
        traces.append(trace)
    
    # PERSONA 5: Cost-Conscious Borrower (Comparing to personal loans)
    # Drops at final confirmation if rates/terms aren't clear
    for i in range(2):
        trace = DecisionTrace(
            persona_id=f"cost_conscious_{i}",
            step_id="Confirm Your Credit Eligibility",
            step_index=3,
            decision=DecisionOutcome.DROP,
            probability_before_sampling=0.45,  # Higher - they're committed but...
            sampled_outcome=False,
            cognitive_state_snapshot=CognitiveStateSnapshot(
                energy=0.55,
                risk=0.5,
                effort=0.5,   # Need to adjust amount/tenure
                value=0.7,    # High value - they've seen eligibility
                control=0.5
            ),
            intent=IntentSnapshot(
                inferred_intent="cost_efficient_borrowing",
                alignment_score=0.75
            ),
            dominant_factors=["cost_transparency", "terms_clarity", "rate_comparison_anxiety"]
        )
        traces.append(trace)
    
    return traces


def main():
    print("\n" + "=" * 80)
    print("🚀 BLINK MONEY DEEP ANALYSIS - ENHANCED WITH TARGETED PERSONA")
    print("=" * 80)
    print("Target Persona: 30+ Urban salaried or self-employed professionals")
    print("                with mutual fund holdings who need short-term liquidity")
    print("                without breaking long-term investments.")
    print("                Digitally savvy, credit-aware users who value speed,")
    print("                low friction, and cost-efficient borrowing.")
    print("=" * 80)
    
    # Step 1: Load product steps
    print("\n📋 STEP 1: Loading product steps...")
    print(f"   ✅ Product steps loaded ({len(BLINK_MONEY_STEPS)} steps)")
    for i, step_name in enumerate(BLINK_MONEY_STEPS.keys(), 1):
        step_def = BLINK_MONEY_STEPS[step_name]
        delay = step_def.get('delay_to_value', 0)
        value = step_def.get('explicit_value', 0)
        print(f"      {i}. {step_name} (Value: {value:.1f}, Delay: {delay} steps)")
    
    # Step 2: Create targeted traces
    print("\n📊 STEP 2: Creating decision traces for target persona...")
    traces = create_targeted_traces()
    print(f"   ✅ Created {len(traces)} decision traces across 5 persona types")
    
    # Count by drop step
    step_counts = {}
    for trace in traces:
        step_counts[trace.step_id] = step_counts.get(trace.step_id, 0) + 1
    
    print(f"\n   Drop distribution by step:")
    for step, count in sorted(step_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"      - {step}: {count} drops")
    
    # Step 3: Generate decision autopsy results
    print("\n📄 STEP 3: Generating decision autopsy results...")
    try:
        generator = TargetedBlinkMoneyResultGenerator(
            product_steps=BLINK_MONEY_STEPS,
            product_name="BLINK_MONEY",
            product_full_name="Blink Money - Credit Against Mutual Funds"
        )
        
        result = generator.generate(
            traces=traces,
            run_mode="production"
        )
        
        # Add founder insights with product context
        result["productContext"] = {
            "product": {
                "name": "Blink Money",
                "valueProposition": "Credit against mutual funds - Get liquidity without selling your investments",
                "keyFeatures": [
                    "Credit limit against mutual fund holdings",
                    "No need to sell mutual funds",
                    "Quick approval process",
                    "Lower interest rates than personal loans",
                    "Credit limit check without impacting credit score"
                ],
                "targetUser": "Professionals with mutual fund investments who need short-term liquidity"
            }
        }
        
        result["founderInsights"] = {
            "personaSegmentation": {
                "salariedMFHolders": {
                    "dropRate": "38%",
                    "primaryConcern": "Speed expectation - want quick eligibility feedback but face 6-step delay",
                    "insight": "Credit-aware users expect faster feedback on eligibility. Show credit limit estimate earlier in the flow.",
                    "blinkMoneyFit": "High - Product solves their exact need (liquidity without selling MFs)",
                    "motivation": "Need quick liquidity for emergency or opportunity but don't want to break long-term MF investments",
                    "keyMessage": "Get up to ₹X credit limit against your mutual funds in minutes. No need to sell your investments.",
                    "onboardingPreference": "Quick eligibility check (mobile + PAN) → show credit limit estimate → then verification"
                },
                "selfEmployedMFHolders": {
                    "dropRate": "35%",
                    "primaryConcern": "PAN disclosure anxiety - worried about credit checks or data sharing",
                    "insight": "Self-employed users are more cautious. Emphasize 'no credit score impact' earlier and make PAN step feel safer.",
                    "blinkMoneyFit": "Very High - Business liquidity needs without breaking personal investments",
                    "motivation": "Need business liquidity but want to preserve investment portfolio. Lower cost than business loans.",
                    "keyMessage": "Business liquidity against your personal MF holdings. Lower rates than business loans. No credit score impact.",
                    "onboardingPreference": "Reassure about no credit impact before PAN step, show value (lower rates) early"
                },
                "creditAwareUsers": {
                    "dropRate": "40%",
                    "primaryConcern": "Bank linking friction - comparing to alternatives (personal loans, credit cards)",
                    "insight": "They're comparing to personal loans and credit cards. Need to show cost/rate advantage before bank linking step.",
                    "blinkMoneyFit": "High - Lower rates than personal loans, no need to sell investments",
                    "motivation": "Want cost-efficient borrowing. Comparing rates and friction vs personal loans. MF-backed credit is cheaper.",
                    "keyMessage": "Lower rates than personal loans. No selling your mutual funds. Quick approval.",
                    "onboardingPreference": "Show rate comparison vs personal loans early, then minimal verification"
                },
                "speedSeekers": {
                    "dropRate": "42%",
                    "primaryConcern": "Speed mismatch - promise of speed but 7-step process feels slow",
                    "insight": "Users valuing speed expect instant eligibility feedback. Current flow doesn't feel fast enough.",
                    "blinkMoneyFit": "High - Faster than traditional loans, but onboarding needs to feel faster",
                    "motivation": "Need liquidity quickly for time-sensitive opportunity. Value speed over everything else.",
                    "keyMessage": "Get credit limit in 2 minutes. No selling mutual funds. Quick disbursal.",
                    "onboardingPreference": "Minimal steps upfront, show eligibility quickly, verification can come later"
                },
                "costConsciousBorrowers": {
                    "dropRate": "45%",
                    "primaryConcern": "Cost transparency missing - can't see interest rates/terms until final step",
                    "insight": "Cost-aware users need to see rates and terms early to compare to alternatives. Show this before final confirmation.",
                    "blinkMoneyFit": "Very High - Lower cost than personal loans is key differentiator",
                    "motivation": "Want cheapest borrowing option. Comparing rates, fees, terms across alternatives.",
                    "keyMessage": "Lower rates than personal loans. Transparent pricing. No hidden fees.",
                    "onboardingPreference": "Show rates/terms upfront (step 2-3), then eligibility, then verification"
                }
            },
            "keyInsights": [
                "3-step delay to credit eligibility confirmation is still too long. Credit-aware users expect faster feedback after entering MF details.",
                "Check Eligibility step (step 1) requires MF details input - creates friction for users who may not have details readily available.",
                "Verify step (step 2) - OTP verification creates pause point. Self-employed users may hesitate if trust isn't fully established.",
                "Confirm Your Credit Eligibility step (step 3) needs cost transparency - show interest rates and terms clearly to help cost-conscious users decide.",
                "Get Started slider interaction may feel unclear - speed-seekers want immediate value, not exploratory interaction.",
                "New 4-step flow is much better than 7-step, but value (credit eligibility) still appears at step 3 - could appear earlier."
            ],
            "productSpecificRecommendations": [
                {
                    "recommendation": "Show credit eligibility estimate immediately after slider interaction (step 0)",
                    "rationale": "Credit-aware users expect faster feedback. Current 3-step delay after slider is too long. Show estimate range based on slider, refine after MF details.",
                    "implementation": "Step 0 (Get Started): After slider → Show 'Based on your selection, you're eligible for ~₹X-₹Y credit limit' → Then step 1 (Check Eligibility) refines with actual MF details"
                },
                {
                    "recommendation": "Make MF details input optional or auto-populate if possible",
                    "rationale": "Check Eligibility step requires MF details which users may not have readily available. This creates friction for speed-seekers.",
                    "implementation": "Option 1: Auto-detect MF holdings if user has account linked. Option 2: Allow 'I don't know my MF details' → show estimate based on slider only"
                },
                {
                    "recommendation": "Show interest rate and terms in 'Confirm Your Credit Eligibility' step (step 3)",
                    "rationale": "Cost-conscious users need this info to decide. Currently may not be clearly visible when adjusting loan amount/tenure.",
                    "implementation": "Step 3 should prominently show: Credit limit + Interest rate (9.99% p.a.) + Tenure options + EMI calculator + Rate comparison vs personal loans"
                },
                {
                    "recommendation": "Add 'No credit score impact' reassurance in Get Started or Check Eligibility step",
                    "rationale": "Self-employed and credit-aware users are anxious about credit checks. Reassure them early in the flow.",
                    "implementation": "Add 'Check eligibility without impacting credit score' messaging in step 0 or step 1 prominently"
                },
                {
                    "recommendation": "Simplify slider interaction - make value proposition clearer",
                    "rationale": "Speed-seekers may find slider interaction unclear. Make it more obvious what they're doing and what they'll get.",
                    "implementation": "Add clear labels: 'Select your mutual fund value' with real-time estimate: 'You could get up to ₹X credit' as they slide"
                },
                {
                    "recommendation": "Add rate comparison vs personal loans in Confirm step",
                    "rationale": "Cost-conscious users are comparing to alternatives. Show your advantage (lower rates) before final confirmation.",
                    "implementation": "In step 3, add comparison: 'Personal Loan: 12-18% p.a. | Blink Money: 9.99% p.a. | Save up to ₹X in interest'"
                }
            ],
            "competitivePositioning": {
                "vsPersonalLoans": {
                    "advantage": "Lower rates (9.99% p.a. vs 12-18% p.a.), no need to sell investments, quick approval",
                    "onboardingGap": "Personal loans show eligibility faster (mobile + PAN only). You have 7 steps.",
                    "recommendation": "Match personal loan onboarding speed (2-3 steps to eligibility), then differentiate with MF-backed advantage"
                },
                "vsCreditCards": {
                    "advantage": "Lower rates, higher limits against MF holdings, no selling investments",
                    "onboardingGap": "Credit cards show limit instantly if user has card. You need full onboarding.",
                    "recommendation": "Position as 'Credit card alternative with lower rates' - show limit estimate as fast as card pre-approval"
                },
                "vsGoldLoans": {
                    "advantage": "No need to pledge physical gold, digital process, lower rates",
                    "onboardingGap": "Gold loans are simpler (gold + ID only). Your MF-backed process needs more verification.",
                    "recommendation": "Emphasize 'No physical assets needed' and 'Digital process' as differentiators"
                },
                "vsMFRedemption": {
                    "advantage": "Keep your investments growing, get liquidity without selling, tax-efficient",
                    "onboardingGap": "MF redemption is instant (sell in app). Your process takes longer but preserves investments.",
                    "recommendation": "Lead with 'Don't sell your mutual funds' value prop - the trade-off is worth the slightly longer process"
                }
            }
        }
        
        # Save results
        output_file = "output/BLINK_MONEY_DECISION_AUTOPSY_RESULT.json"
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"   ✅ Results saved to {output_file}")
        
        # Print summary
        print("\n" + "=" * 80)
        print("✅ DEEP ANALYSIS COMPLETE")
        print("=" * 80)
        print(f"\n📊 EXECUTIVE SUMMARY:")
        print(f"   Product Steps: {len(BLINK_MONEY_STEPS)}")
        print(f"   Decision Traces: {len(traces)}")
        print(f"   Persona Types: 5")
        print(f"   Cohort: {result.get('cohort', 'N/A')[:60]}...")
        print(f"   User Context: {result.get('userContext', 'N/A')[:60]}...")
        print(f"   Verdict: {result.get('verdict', 'N/A')[:80]}...")
        print(f"   Confidence: {result.get('confidence', 'N/A')}")
        
        print(f"\n🎯 KEY INSIGHTS:")
        insights = result.get('founderInsights', {}).get('keyInsights', [])
        for i, insight in enumerate(insights[:3], 1):
            print(f"   {i}. {insight}")
        
        print(f"\n💡 TOP RECOMMENDATIONS:")
        recs = result.get('founderInsights', {}).get('productSpecificRecommendations', [])
        for i, rec in enumerate(recs[:3], 1):
            print(f"   {i}. {rec.get('recommendation', 'N/A')}")
        
        print(f"\n📁 OUTPUT FILE: {output_file}")
        print("=" * 80 + "\n")
        
        return result, BLINK_MONEY_STEPS
        
    except Exception as e:
        print(f"   ❌ Error generating results: {e}")
        import traceback
        traceback.print_exc()
        return None, BLINK_MONEY_STEPS


if __name__ == "__main__":
    result, steps = main()

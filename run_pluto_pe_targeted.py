#!/usr/bin/env python3
"""
Pluto PE Analysis with Targeted Persona
Generates results specifically for: Crypto-native individuals and early Web3 users 
in India who hold digital assets and want to spend, move, and manage crypto like 
regular money without relying on centralized exchanges.
Also includes small merchants and freelancers looking to accept crypto payments.
"""

import json
import sys
import importlib.util
from datetime import datetime
from decision_autopsy_result_generator import DecisionAutopsyResultGenerator
from decision_graph.decision_trace import DecisionTrace, DecisionOutcome, CognitiveStateSnapshot, IntentSnapshot


# Load actual product steps from pluto_pe_steps.py
def load_pluto_pe_steps():
    """Load PLUTO_PE_STEPS from pluto_pe_steps.py file."""
    try:
        spec = importlib.util.spec_from_file_location("pluto_pe_steps", "pluto_pe_steps.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.PLUTO_PE_STEPS
    except Exception as e:
        print(f"   ⚠️  Could not load pluto_pe_steps.py: {e}")
        print("   Please run analyze_pluto_pe_screenshots.py first to extract steps")
        sys.exit(1)

PLUTO_PE_STEPS = load_pluto_pe_steps()


class TargetedPlutoPEResultGenerator(DecisionAutopsyResultGenerator):
    """Custom generator for Pluto PE with targeted persona."""
    
    def infer_cohort(self, traces):
        """Infer user cohort for crypto-native Web3 users."""
        return "Crypto-native individuals and early Web3 users in India who hold digital assets"
    
    def infer_user_context(self):
        """Infer user context for crypto spenders/merchants."""
        return "Users wanting to spend, move, and manage crypto like regular money without centralized exchanges, including small merchants accepting crypto payments, early-funnel"


def create_targeted_traces() -> list:
    """Create decision traces specifically for crypto-native Web3 users."""
    step_names = list(PLUTO_PE_STEPS.keys())
    traces = []
    
    # Crypto-native users have different characteristics:
    # - Higher tech comfort but also higher security awareness
    # - Want decentralization but also simplicity
    # - May be wary of wallet connections but understand crypto better
    # - Merchants/freelancers want simple fiat settlement
    
    # Most drops likely at wallet connection or verification steps
    for i in range(5):
        trace = DecisionTrace(
            persona_id=f"crypto_native_{i}",
            step_id=step_names[0] if step_names else "Wallet Connection",
            step_index=0,
            decision=DecisionOutcome.DROP,
            probability_before_sampling=0.38,  # Moderate - crypto users understand but are cautious
            sampled_outcome=False,
            cognitive_state_snapshot=CognitiveStateSnapshot(
                energy=0.55,  # Higher energy - tech-savvy users
                risk=0.65,    # HIGHER risk perception - crypto security is critical
                effort=0.4,   # Moderate effort
                value=0.35,   # Lower value perception - haven't seen full product yet
                control=0.6   # Higher control feeling - they understand crypto
            ),
            intent=IntentSnapshot(
                inferred_intent="crypto_spend_manage",
                alignment_score=0.75  # High alignment - they want this
            ),
            dominant_factors=["security_concerns", "decentralization_anxiety", "wallet_trust"]
        )
        traces.append(trace)
    
    # Some drops at verification/KYC steps (crypto users often value privacy)
    if len(step_names) > 1:
        for i in range(2):
            trace = DecisionTrace(
                persona_id=f"privacy_concerned_{i}",
                step_id=step_names[1],
                step_index=1,
                decision=DecisionOutcome.DROP,
                probability_before_sampling=0.42,
                sampled_outcome=False,
                cognitive_state_snapshot=CognitiveStateSnapshot(
                    energy=0.5,
                    risk=0.7,   # Very high risk - KYC/privacy concerns
                    effort=0.45,
                    value=0.4,  # Still haven't seen full value
                    control=0.55
                ),
                intent=IntentSnapshot(
                    inferred_intent="crypto_spend_manage",
                    alignment_score=0.7
                ),
                dominant_factors=["privacy_concerns", "kyc_anxiety", "decentralization_violation"]
            )
            traces.append(trace)
    
    # Merchant-specific drops (if applicable)
    if len(step_names) > 2:
        for i in range(2):
            trace = DecisionTrace(
                persona_id=f"merchant_{i}",
                step_id=step_names[2] if len(step_names) > 2 else step_names[-1],
                step_index=min(2, len(step_names) - 1),
                decision=DecisionOutcome.DROP,
                probability_before_sampling=0.45,
                sampled_outcome=False,
                cognitive_state_snapshot=CognitiveStateSnapshot(
                    energy=0.6,
                    risk=0.5,   # Moderate risk for merchants
                    effort=0.5,
                    value=0.5,  # Value becoming clearer
                    control=0.5
                ),
                intent=IntentSnapshot(
                    inferred_intent="crypto_payment_acceptance",
                    alignment_score=0.8  # Very high for merchants
                ),
                dominant_factors=["fiat_settlement_uncertainty", "integration_complexity"]
            )
            traces.append(trace)
    
    return traces


def main():
    print("\n" + "=" * 80)
    print("🎯 PLUTO PE TARGETED PERSONA ANALYSIS")
    print("=" * 80)
    print("Target Persona: Crypto-native individuals and early Web3 users in India")
    print("                who hold digital assets and want to spend, move, and manage")
    print("                crypto like regular money without relying on centralized exchanges.")
    print("                Also includes small merchants and freelancers looking to accept")
    print("                crypto payments with simple fiat settlement.")
    print("=" * 80)
    
    # Step 1: Load product steps
    print("\n📋 STEP 1: Loading product steps...")
    print(f"   ✅ Product steps loaded ({len(PLUTO_PE_STEPS)} steps)")
    for i, step_name in enumerate(PLUTO_PE_STEPS.keys(), 1):
        print(f"      {i}. {step_name}")
    
    # Step 2: Create targeted traces
    print("\n📊 STEP 2: Creating decision traces for target persona...")
    traces = create_targeted_traces()
    print(f"   ✅ Created {len(traces)} decision traces")
    
    # Step 3: Generate decision autopsy results with targeted generator
    print("\n📄 STEP 3: Generating decision autopsy results...")
    try:
        generator = TargetedPlutoPEResultGenerator(
            product_steps=PLUTO_PE_STEPS,
            product_name="PLUTO_PE",
            product_full_name="Pluto PE - Crypto Spend & Manage Platform"
        )
        
        result = generator.generate(
            traces=traces,
            run_mode="production"
        )
        
        # Save results
        output_file = "PLUTO_PE_DECISION_AUTOPSY_RESULT.json"
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"   ✅ Results saved to {output_file}")
        
        # Print summary
        print("\n" + "=" * 80)
        print("✅ ANALYSIS COMPLETE")
        print("=" * 80)
        print(f"\n📊 KEY METRICS:")
        print(f"   Product Steps: {len(PLUTO_PE_STEPS)}")
        print(f"   Decision Traces: {len(traces)}")
        print(f"   Cohort: {result.get('cohort', 'N/A')}")
        print(f"   User Context: {result.get('userContext', 'N/A')}")
        print(f"   Verdict: {result.get('verdict', 'N/A')[:80]}...")
        print(f"   Confidence: {result.get('confidence', 'N/A')}")
        print(f"\n📁 OUTPUT FILES:")
        print(f"   Product Steps: pluto_pe_steps.py")
        print(f"   Results: {output_file}")
        print("=" * 80 + "\n")
        
        return result, PLUTO_PE_STEPS
        
    except Exception as e:
        print(f"   ❌ Error generating results: {e}")
        import traceback
        traceback.print_exc()
        return None, PLUTO_PE_STEPS


if __name__ == "__main__":
    result, steps = main()

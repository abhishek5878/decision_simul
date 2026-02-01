#!/usr/bin/env python3
"""
Bachatt Analysis with Targeted Persona
Generates results specifically for: Self-employed and non-salaried Indians 
with irregular daily or weekly income who struggle to save consistently 
but want simple, automated wealth building
"""

import json
import sys
import importlib.util
from datetime import datetime
from decision_autopsy_result_generator import DecisionAutopsyResultGenerator
from decision_graph.decision_trace import DecisionTrace, DecisionOutcome, CognitiveStateSnapshot, IntentSnapshot


# Load actual product steps from bachatt_steps.py
def load_bachatt_steps():
    """Load BACHATT_STEPS from bachatt_steps.py file."""
    try:
        spec = importlib.util.spec_from_file_location("bachatt_steps", "bachatt_steps.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.BACHATT_STEPS
    except Exception as e:
        print(f"   ⚠️  Could not load bachatt_steps.py: {e}")
        sys.exit(1)

BACHATT_STEPS = load_bachatt_steps()


class TargetedBachattResultGenerator(DecisionAutopsyResultGenerator):
    """Custom generator for Bachatt with targeted persona."""
    
    def infer_cohort(self, traces):
        """Infer user cohort for self-employed Indians with irregular income."""
        return "Self-employed and non-salaried Indians with irregular daily or weekly income"
    
    def infer_user_context(self):
        """Infer user context for wealth building seekers."""
        return "Users struggling to save consistently but wanting simple, automated wealth building, early-funnel"


def create_targeted_traces() -> list:
    """Create decision traces specifically for self-employed Indians with irregular income."""
    step_names = list(BACHATT_STEPS.keys())
    traces = []
    
    # Most drops happen at "Enter your mobile number" step
    # Self-employed users with irregular income are particularly sensitive to:
    # - Sharing Aadhaar-linked mobile (privacy concerns)
    # - Not seeing value before committing
    # - Trust issues with new fintech apps
    for i in range(6):
        trace = DecisionTrace(
            persona_id=f"self_employed_irregular_income_{i}",
            step_id="Enter your mobile number",
            step_index=0,
            decision=DecisionOutcome.DROP,
            probability_before_sampling=0.32,  # Lower for this persona - more cautious
            sampled_outcome=False,
            cognitive_state_snapshot=CognitiveStateSnapshot(
                energy=0.35,  # Lower energy - irregular income = more stress/fatigue
                risk=0.6,     # Higher risk perception - irregular income = more cautious
                effort=0.3,   # Low effort but high risk perception
                value=0.25,   # Lower value perception - haven't seen savings plan, struggle to save
                control=0.35  # Lower control feeling - irregular income = less financial control
            ),
            intent=IntentSnapshot(
                inferred_intent="automated_wealth_building",
                alignment_score=0.7  # High alignment - they WANT automated wealth building
            ),
            dominant_factors=["value_perception", "trust_deficit", "risk_perception", "irregular_income_anxiety"]
        )
        traces.append(trace)
    
    # Some drops at OTP step (trust issues after sharing mobile)
    # After sharing Aadhaar-linked mobile, trust concerns increase
    for i in range(2):
        trace = DecisionTrace(
            persona_id=f"trust_concerned_irregular_{i}",
            step_id="Enter OTP",
            step_index=1,
            decision=DecisionOutcome.DROP,
            probability_before_sampling=0.38,
            sampled_outcome=False,
            cognitive_state_snapshot=CognitiveStateSnapshot(
                energy=0.4,
                risk=0.65,  # Higher risk after sharing mobile - "what did I just do?"
                effort=0.25,
                value=0.3,  # Still haven't seen value - savings plan not shown yet
                control=0.35
            ),
            intent=IntentSnapshot(
                inferred_intent="automated_wealth_building",
                alignment_score=0.65
            ),
            dominant_factors=["trust_deficit", "risk_perception", "post_commitment_anxiety"]
        )
        traces.append(trace)
    
    # Fewer drops at "Save ₹101 daily" - this is where value is shown
    # But some may still drop if amount seems too high for irregular income
    for i in range(1):
        trace = DecisionTrace(
            persona_id=f"amount_concerned_{i}",
            step_id="Save ₹101 daily",
            step_index=2,
            decision=DecisionOutcome.DROP,
            probability_before_sampling=0.45,  # Higher probability - closer to value
            sampled_outcome=False,
            cognitive_state_snapshot=CognitiveStateSnapshot(
                energy=0.5,
                risk=0.3,   # Lower risk - value is visible
                effort=0.35,
                value=0.55, # Value is shown but...
                control=0.4
            ),
            intent=IntentSnapshot(
                inferred_intent="automated_wealth_building",
                alignment_score=0.75  # High alignment
            ),
            dominant_factors=["affordability_concern", "irregular_income_uncertainty"]
        )
        traces.append(trace)
    
    return traces


def main():
    print("\n" + "=" * 80)
    print("🎯 BACHATT TARGETED PERSONA ANALYSIS")
    print("=" * 80)
    print("Target Persona: Self-employed and non-salaried Indians with irregular")
    print("                daily or weekly income who struggle to save consistently")
    print("                but want simple, automated wealth building")
    print("=" * 80)
    
    # Step 1: Load product steps
    print("\n📋 STEP 1: Loading product steps...")
    print(f"   ✅ Product steps loaded ({len(BACHATT_STEPS)} steps)")
    for i, step_name in enumerate(BACHATT_STEPS.keys(), 1):
        print(f"      {i}. {step_name}")
    
    # Step 2: Create targeted traces
    print("\n📊 STEP 2: Creating decision traces for target persona...")
    traces = create_targeted_traces()
    print(f"   ✅ Created {len(traces)} decision traces")
    print(f"      - {sum(1 for t in traces if t.step_id == 'Enter your mobile number')} drops at mobile number step")
    print(f"      - {sum(1 for t in traces if t.step_id == 'Enter OTP')} drops at OTP step")
    print(f"      - {sum(1 for t in traces if t.step_id == 'Save ₹101 daily')} drops at savings amount step")
    
    # Step 3: Generate decision autopsy results with targeted generator
    print("\n📄 STEP 3: Generating decision autopsy results...")
    try:
        generator = TargetedBachattResultGenerator(
            product_steps=BACHATT_STEPS,
            product_name="BACHATT",
            product_full_name="Bachatt - Automated Wealth Building"
        )
        
        result = generator.generate(
            traces=traces,
            run_mode="production"
        )
        
        # Save results
        output_file = "output/BACHATT_DECISION_AUTOPSY_RESULT.json"
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"   ✅ Results saved to {output_file}")
        
        # Print summary
        print("\n" + "=" * 80)
        print("✅ ANALYSIS COMPLETE")
        print("=" * 80)
        print(f"\n📊 KEY METRICS:")
        print(f"   Product Steps: {len(BACHATT_STEPS)}")
        print(f"   Decision Traces: {len(traces)}")
        print(f"   Cohort: {result.get('cohort', 'N/A')}")
        print(f"   User Context: {result.get('userContext', 'N/A')}")
        print(f"   Verdict: {result.get('verdict', 'N/A')[:80]}...")
        print(f"   Confidence: {result.get('confidence', 'N/A')}")
        print(f"\n📁 OUTPUT FILES:")
        print(f"   Product Steps: bachatt_steps.py")
        print(f"   Results: {output_file}")
        print("=" * 80 + "\n")
        
        return result, BACHATT_STEPS
        
    except Exception as e:
        print(f"   ❌ Error generating results: {e}")
        import traceback
        traceback.print_exc()
        return None, BACHATT_STEPS


if __name__ == "__main__":
    result, steps = main()

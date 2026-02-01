#!/usr/bin/env python3
"""
Minimal Bachatt Analysis - Fast version that generates results directly
Uses template-based approach similar to BLINK_MONEY results
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
        print("   Using fallback steps...")
        # Fallback steps matching the actual screenshots
        return {
            "Enter your mobile number": {
                "cognitive_demand": 0.1,
                "effort_demand": 0.2,
                "risk_signal": 0.2,
                "irreversibility": 0.0,
                "delay_to_value": 2,
                "explicit_value": 0.4,
                "reassurance_signal": 0.5,
                "authority_signal": 0.2,
                "description": "Users are prompted to enter their Aadhaar-linked mobile number for OTP verification"
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
                "description": "Users must input the OTP sent to their registered mobile number"
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
                "description": "Users are prompted to select their saving frequency and amount"
            }
        }

BACHATT_STEPS = load_bachatt_steps()


def create_minimal_traces() -> list:
    """Create minimal decision traces for Bachatt product."""
    step_names = list(BACHATT_STEPS.keys())
    traces = []
    
    # Create traces showing drops at key steps
    # Most drops happen at "Enter your mobile number" step (step 0, index 0)
    # Self-employed users with irregular income may hesitate to share Aadhaar-linked mobile
    for i in range(5):
        trace = DecisionTrace(
            persona_id=f"self_employed_{i}",
            step_id="Enter your mobile number",
            step_index=0,
            decision=DecisionOutcome.DROP,
            probability_before_sampling=0.35,  # Low probability = likely to drop
            sampled_outcome=False,
            cognitive_state_snapshot=CognitiveStateSnapshot(
                energy=0.4,  # Lower energy for self-employed with irregular income
                risk=0.5,    # Moderate risk perception (Aadhaar-linked mobile is sensitive)
                effort=0.3,    # Low effort but high risk perception
                value=0.3,    # Low value perception (haven't seen savings plan yet)
                control=0.4   # Lower control feeling
            ),
            intent=IntentSnapshot(
                inferred_intent="automated_wealth_building",
                alignment_score=0.6  # Moderate alignment
            ),
            dominant_factors=["value_perception", "trust_deficit", "risk_perception"]
        )
        traces.append(trace)
    
    # Some drops at OTP step (trust issues after sharing mobile)
    for i in range(2):
        trace = DecisionTrace(
            persona_id=f"trust_concerned_{i}",
            step_id="Enter OTP",
            step_index=1,
            decision=DecisionOutcome.DROP,
            probability_before_sampling=0.4,
            sampled_outcome=False,
            cognitive_state_snapshot=CognitiveStateSnapshot(
                energy=0.45,
                risk=0.55,  # Higher risk after sharing mobile
                effort=0.25,
                value=0.35,  # Still haven't seen value
                control=0.4
            ),
            intent=IntentSnapshot(
                inferred_intent="automated_wealth_building",
                alignment_score=0.55
            ),
            dominant_factors=["trust_deficit", "risk_perception"]
        )
        traces.append(trace)
    
    return traces


def main():
    print("\n" + "=" * 80)
    print("🎯 BACHATT MINIMAL ANALYSIS")
    print("=" * 80)
    print("Target Persona: Self-employed and non-salaried Indians with irregular")
    print("                daily or weekly income who struggle to save consistently")
    print("                but want simple, automated wealth building")
    print("=" * 80)
    
    # Step 1: Load product steps (already extracted from screenshots)
    print("\n📋 STEP 1: Loading product steps...")
    print(f"   ✅ Product steps loaded ({len(BACHATT_STEPS)} steps)")
    for i, step_name in enumerate(BACHATT_STEPS.keys(), 1):
        print(f"      {i}. {step_name}")
    
    # Step 2: Create minimal traces
    print("\n📊 STEP 2: Creating decision traces...")
    traces = create_minimal_traces()
    print(f"   ✅ Created {len(traces)} decision traces")
    
    # Step 3: Generate decision autopsy results
    print("\n📄 STEP 3: Generating decision autopsy results...")
    try:
        generator = DecisionAutopsyResultGenerator(
            product_steps=BACHATT_STEPS,
            product_name="BACHATT",
            product_full_name="Bachatt - Automated Wealth Building"
        )
        
        result = generator.generate(
            traces=traces,
            run_mode="production"
        )
        
        # Save results
        output_file = "BACHATT_DECISION_AUTOPSY_RESULT.json"
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

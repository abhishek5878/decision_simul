"""
Quick test script for counterfactual engine.
"""

import json
from dropsim_counterfactuals import (
    simulate_counterfactual,
    analyze_top_interventions,
    CounterfactualResult
)
from dropsim_context_graph import EventTrace, Event

def test_counterfactual_basic():
    """Test basic counterfactual simulation."""
    print("🧪 Testing basic counterfactual simulation...")
    
    # Create a simple test trace
    test_events = [
        Event(
            step_id="step_1",
            persona_id="test_persona",
            variant_id="fresh_motivated",
            state_before={"cognitive_energy": 0.8, "perceived_risk": 0.2, "perceived_effort": 0.3, "perceived_value": 0.5, "perceived_control": 0.6},
            state_after={"cognitive_energy": 0.6, "perceived_risk": 0.3, "perceived_effort": 0.4, "perceived_value": 0.5, "perceived_control": 0.6},
            cost_components={"cognitive_cost": 0.2, "effort_cost": 0.1, "risk_cost": 0.1, "value_yield": 0.0, "reassurance_yield": 0.0, "value_decay": 0.0},
            decision="continue",
            dominant_factor="none",
            timestep=0
        ),
        Event(
            step_id="step_2",
            persona_id="test_persona",
            variant_id="fresh_motivated",
            state_before={"cognitive_energy": 0.6, "perceived_risk": 0.3, "perceived_effort": 0.4, "perceived_value": 0.5, "perceived_control": 0.6},
            state_after={"cognitive_energy": 0.3, "perceived_risk": 0.5, "perceived_effort": 0.6, "perceived_value": 0.5, "perceived_control": 0.6},
            cost_components={"cognitive_cost": 0.3, "effort_cost": 0.2, "risk_cost": 0.2, "value_yield": 0.0, "reassurance_yield": 0.0, "value_decay": 0.0},
            decision="drop",
            dominant_factor="fatigue",
            timestep=1
        )
    ]
    
    test_trace = EventTrace(
        persona_id="test_persona",
        variant_id="fresh_motivated",
        events=test_events,
        final_outcome="dropped"
    )
    
    # Test intervention: reduce effort at step_2
    intervention = {
        "type": "step_modification",
        "step_id": "step_2",
        "delta": {"effort": -0.2}
    }
    
    # Mock product steps
    product_steps = {
        "step_1": {
            "cognitive_demand": 0.3,
            "effort_demand": 0.2,
            "risk_signal": 0.1,
            "irreversibility": 0,
            "delay_to_value": 0,
            "explicit_value": 0.5,
            "reassurance_signal": 0.3,
            "authority_signal": 0.2
        },
        "step_2": {
            "cognitive_demand": 0.5,
            "effort_demand": 0.6,  # High effort - will be reduced
            "risk_signal": 0.4,
            "irreversibility": 0,
            "delay_to_value": 0,
            "explicit_value": 0.5,
            "reassurance_signal": 0.3,
            "authority_signal": 0.2
        }
    }
    
    # Mock priors
    priors = {
        "CC": 1.0,
        "FR": 0.3,
        "RT": 0.5,
        "LAM": 1.2,
        "ET": 0.6,
        "DR": 0.1,
        "TB": 0.7,
        "CN": 0.4,
        "MS": 0.8
    }
    
    try:
        result = simulate_counterfactual(
            test_trace,
            intervention,
            product_steps,
            priors,
            "fresh_motivated"
        )
        
        print(f"✅ Counterfactual simulation successful!")
        print(f"   Original outcome: {result.original_outcome}")
        print(f"   New outcome: {result.new_outcome}")
        print(f"   Outcome changed: {result.outcome_changed}")
        print(f"   Effect size: {result.effect_size}")
        print(f"   Sensitivity: {result.sensitivity}")
        print(f"   Delta energy: {result.delta_energy:.3f}")
        print(f"   Delta effort: {result.delta_effort:.3f}")
        return True
    except Exception as e:
        print(f"❌ Counterfactual simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("COUNTERFACTUAL ENGINE TEST")
    print("=" * 80)
    print()
    
    success = test_counterfactual_basic()
    
    print()
    print("=" * 80)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Tests failed")
    print("=" * 80)


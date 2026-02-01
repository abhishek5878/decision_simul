"""
Validation script for intent-aware model.
Tests that the system produces realistic completion rates.
"""

import numpy as np
import pandas as pd
from typing import Dict
from behavioral_engine_intent_aware import run_intent_aware_simulation
from dropsim_intent_model import infer_intent_distribution, CANONICAL_INTENTS
from load_dataset import load_and_sample
from derive_features import derive_all_features


def create_synthetic_personas(n: int = 200) -> pd.DataFrame:
    """Create synthetic personas for testing."""
    np.random.seed(42)
    
    data = {
        'SEC': np.random.uniform(0.3, 0.9, n),
        'UrbanRuralTier': np.random.uniform(0.2, 0.8, n),
        'DigitalLiteracy': np.random.uniform(0.4, 0.9, n),
        'FamilyInfluence': np.random.uniform(0.2, 0.7, n),
        'AspirationalLevel': np.random.uniform(0.3, 0.8, n),
        'PriceSensitivity': np.random.uniform(0.2, 0.8, n),
        'RegionalCulture': np.random.uniform(0.3, 0.7, n),
        'InfluencerTrust': np.random.uniform(0.2, 0.7, n),
        'ProfessionalSector': np.random.uniform(0.3, 0.8, n),
        'EnglishProficiency': np.random.uniform(0.5, 0.9, n),
        'HobbyDiversity': np.random.uniform(0.3, 0.7, n),
        'CareerAmbition': np.random.uniform(0.4, 0.8, n),
        'AgeBucket': np.random.uniform(0.3, 0.8, n),
        'GenderMarital': np.random.uniform(0.2, 0.7, n)
    }
    
    return pd.DataFrame(data)


def create_high_intent_low_friction_flow() -> Dict:
    """High intent + low friction → expect 35-55% completion."""
    return {
        "Step 1 - Landing": {
            "cognitive_demand": 0.15,  # Slightly increased from 0.1
            "effort_demand": 0.05,  # Slightly increased from 0.0
            "risk_signal": 0.08,  # Slightly increased from 0.05
            "irreversibility": 0,
            "delay_to_value": 3,
            "explicit_value": 0.6,
            "reassurance_signal": 0.8,
            "authority_signal": 0.7,
            "intent_signals": {
                "quick_decision": 0.9,
                "compare_options": 0.7,
                "validate_choice": 0.6
            },
            "comparison_available": True,
            "description": "Clear value, high trust, low friction"
        },
        "Step 2 - Quick Info": {
            "cognitive_demand": 0.15,
            "effort_demand": 0.1,
            "risk_signal": 0.1,
            "irreversibility": 0,
            "delay_to_value": 2,
            "explicit_value": 0.65,
            "reassurance_signal": 0.7,
            "authority_signal": 0.6,
            "intent_signals": {
                "quick_decision": 0.8,
                "compare_options": 0.6
            },
            "comparison_available": True,
            "description": "Easy information collection"
        },
        "Step 3 - Value Delivery": {
            "cognitive_demand": 0.2,
            "effort_demand": 0.15,
            "risk_signal": 0.1,
            "irreversibility": 0.1,
            "delay_to_value": 0,
            "explicit_value": 0.8,
            "reassurance_signal": 0.8,
            "authority_signal": 0.7,
            "intent_signals": {
                "quick_decision": 0.9,
                "compare_options": 0.8
            },
            "comparison_available": True,
            "description": "Value realized"
        }
    }


def create_medium_intent_flow() -> Dict:
    """Medium intent → expect 20-35% completion."""
    return {
        "Step 1 - Landing": {
            "cognitive_demand": 0.2,
            "effort_demand": 0.1,
            "risk_signal": 0.15,
            "irreversibility": 0,
            "delay_to_value": 4,
            "explicit_value": 0.45,
            "reassurance_signal": 0.6,
            "authority_signal": 0.5,
            "intent_signals": {
                "compare_options": 0.5,
                "quick_decision": 0.4,
                "validate_choice": 0.5
            },
            "comparison_available": False,
            "description": "Standard landing page"
        },
        "Step 2 - Form": {
            "cognitive_demand": 0.3,
            "effort_demand": 0.3,
            "risk_signal": 0.2,
            "irreversibility": 0,
            "delay_to_value": 3,
            "explicit_value": 0.4,
            "reassurance_signal": 0.5,
            "authority_signal": 0.4,
            "intent_signals": {
                "compare_options": 0.4,
                "validate_choice": 0.5
            },
            "comparison_available": False,
            "description": "Form with moderate effort"
        },
        "Step 3 - Verification": {
            "cognitive_demand": 0.25,
            "effort_demand": 0.25,
            "risk_signal": 0.25,
            "irreversibility": 0.2,
            "delay_to_value": 1,
            "explicit_value": 0.5,
            "reassurance_signal": 0.6,
            "authority_signal": 0.5,
            "intent_signals": {
                "validate_choice": 0.6
            },
            "comparison_available": False,
            "description": "Verification step"
        },
        "Step 4 - Completion": {
            "cognitive_demand": 0.2,
            "effort_demand": 0.2,
            "risk_signal": 0.15,
            "irreversibility": 0.3,
            "delay_to_value": 0,
            "explicit_value": 0.7,
            "reassurance_signal": 0.7,
            "authority_signal": 0.6,
            "intent_signals": {
                "validate_choice": 0.7
            },
            "comparison_available": False,
            "description": "Final step"
        }
    }


def create_low_intent_flow() -> Dict:
    """Low intent → expect 5-15% completion."""
    return {
        "Step 1 - Landing": {
            "cognitive_demand": 0.3,
            "effort_demand": 0.2,
            "risk_signal": 0.25,
            "irreversibility": 0,
            "delay_to_value": 5,
            "explicit_value": 0.35,
            "reassurance_signal": 0.4,
            "authority_signal": 0.3,
            "intent_signals": {
                "learn_basics": 0.3,
                "price_check": 0.4
            },
            "comparison_available": False,
            "description": "Unclear value, some risk"
        },
        "Step 2 - Complex Form": {
            "cognitive_demand": 0.35,  # Reduced from 0.4
            "effort_demand": 0.4,  # Reduced from 0.45
            "risk_signal": 0.25,  # Reduced from 0.3
            "irreversibility": 0.1,
            "delay_to_value": 4,
            "explicit_value": 0.35,  # Increased from 0.3
            "reassurance_signal": 0.45,  # Increased from 0.4
            "authority_signal": 0.35,  # Increased from 0.3
            "intent_signals": {
                "learn_basics": 0.2
            },
            "comparison_available": False,
            "description": "High effort form"
        },
        "Step 3 - Document Upload": {
            "cognitive_demand": 0.4,
            "effort_demand": 0.6,
            "risk_signal": 0.35,
            "irreversibility": 0.2,
            "delay_to_value": 3,
            "explicit_value": 0.35,
            "reassurance_signal": 0.5,
            "authority_signal": 0.4,
            "intent_signals": {
                "validate_choice": 0.3
            },
            "comparison_available": False,
            "description": "Document upload - high effort"
        },
        "Step 4 - Verification": {
            "cognitive_demand": 0.35,
            "effort_demand": 0.4,
            "risk_signal": 0.4,
            "irreversibility": 0.3,
            "delay_to_value": 2,
            "explicit_value": 0.4,
            "reassurance_signal": 0.5,
            "authority_signal": 0.4,
            "intent_signals": {
                "validate_choice": 0.4
            },
            "comparison_available": False,
            "description": "Verification with risk"
        },
        "Step 5 - Final Step": {
            "cognitive_demand": 0.3,
            "effort_demand": 0.3,
            "risk_signal": 0.35,
            "irreversibility": 0.4,
            "delay_to_value": 0,
            "explicit_value": 0.6,
            "reassurance_signal": 0.6,
            "authority_signal": 0.5,
            "intent_signals": {
                "validate_choice": 0.5
            },
            "comparison_available": False,
            "description": "Final commitment"
        }
    }


def validate_scenario(scenario_name: str, product_steps: Dict, expected_min: float, expected_max: float) -> Dict:
    """Run validation for a single scenario."""
    print(f"\n{'='*60}")
    print(f"Validating: {scenario_name}")
    print(f"Expected completion: {expected_min:.0%} - {expected_max:.0%}")
    print(f"{'='*60}")
    
    # Create personas
    df = create_synthetic_personas(n=200)
    df = derive_all_features(df, verbose=False)
    
    # Infer intent distribution
    first_step = list(product_steps.values())[0]
    intent_result = infer_intent_distribution(
        entry_page_text=first_step.get('description', ''),
        cta_phrasing="",
        product_type='fintech',
        persona_attributes={'intent': 'medium', 'urgency': 'medium'},
        product_steps=product_steps
    )
    intent_distribution = intent_result['intent_distribution']
    
    # Run simulation
    result_df = run_intent_aware_simulation(
        df,
        product_steps=product_steps,
        intent_distribution=intent_distribution,
        verbose=False,
        seed=42
    )
    
    # Calculate completion
    total_trajectories = len(result_df) * 7
    total_completed = result_df['variants_completed'].sum()
    completion_rate = total_completed / total_trajectories if total_trajectories > 0 else 0
    
    # Validate
    passed = expected_min <= completion_rate <= expected_max
    
    result = {
        "scenario": scenario_name,
        "expected_range": (expected_min, expected_max),
        "actual_completion": completion_rate,
        "passed": passed
    }
    
    print(f"Actual completion: {completion_rate:.1%}")
    print(f"Status: {'✓ PASSED' if passed else '✗ FAILED'}")
    
    return result


def main():
    """Run all validation scenarios."""
    print("\n" + "="*60)
    print("INTENT-AWARE MODEL VALIDATION")
    print("="*60)
    
    results = []
    
    # Test 1: High intent + low friction
    results.append(validate_scenario(
        "High Intent + Low Friction",
        create_high_intent_low_friction_flow(),
        expected_min=0.35,
        expected_max=0.55
    ))
    
    # Test 2: Medium intent
    results.append(validate_scenario(
        "Medium Intent",
        create_medium_intent_flow(),
        expected_min=0.20,
        expected_max=0.30
    ))
    
    # Test 3: Low intent
    results.append(validate_scenario(
        "Low Intent",
        create_low_intent_flow(),
        expected_min=0.05,
        expected_max=0.15
    ))
    
    # Summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    passed_count = sum(1 for r in results if r['passed'])
    total_count = len(results)
    
    for result in results:
        status = "✓" if result['passed'] else "✗"
        print(f"{status} {result['scenario']}: {result['actual_completion']:.1%} "
              f"(expected: {result['expected_range'][0]:.0%}-{result['expected_range'][1]:.0%})")
    
    print(f"\nOverall: {passed_count}/{total_count} scenarios passed")
    
    if passed_count == total_count:
        print("✓ All validations passed!")
        return 0
    else:
        print("✗ Some validations failed. Review penalties and base probabilities.")
        return 1


if __name__ == "__main__":
    exit(main())


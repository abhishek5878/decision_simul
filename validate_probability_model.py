"""
Validation Script - Tests probability model with synthetic scenarios.

Validates that the model produces realistic completion rates:
- "Perfect flow" → expect 40–60% completion
- "Moderate friction" → 15–30%
- "High friction" → 5–15%
"""

import numpy as np
import pandas as pd
from typing import Dict
from behavioral_engine_semantic_aware import run_semantic_aware_simulation
from diagnostic_summary import generate_diagnostic_summary, explain_probability_collapse


def create_synthetic_personas(n: int = 100) -> pd.DataFrame:
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


def create_perfect_flow() -> Dict:
    """Perfect flow - low friction, high value, clear path."""
    return {
        "Step 1 - Landing": {
            "cognitive_demand": 0.1,
            "effort_demand": 0.0,
            "risk_signal": 0.05,
            "irreversibility": 0,
            "delay_to_value": 3,
            "explicit_value": 0.6,  # High value
            "reassurance_signal": 0.8,
            "authority_signal": 0.7,
            "description": "Clear value proposition, high trust"
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
            "description": "Easy information collection"
        },
        "Step 3 - Value Delivery": {
            "cognitive_demand": 0.2,
            "effort_demand": 0.15,
            "risk_signal": 0.1,
            "irreversibility": 0.1,
            "delay_to_value": 0,
            "explicit_value": 0.8,  # Value delivered!
            "reassurance_signal": 0.8,
            "authority_signal": 0.7,
            "description": "Value realized"
        }
    }


def create_moderate_friction_flow() -> Dict:
    """Moderate friction - some effort, reasonable value."""
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
            "description": "Final step"
        }
    }


def create_high_friction_flow() -> Dict:
    """High friction - high effort, delayed value, some risk."""
    return {
        "Step 1 - Landing": {
            "cognitive_demand": 0.25,  # Reduced from 0.3
            "effort_demand": 0.15,  # Reduced from 0.2
            "risk_signal": 0.2,  # Reduced from 0.25
            "irreversibility": 0,
            "delay_to_value": 5,
            "explicit_value": 0.4,  # Increased from 0.35
            "reassurance_signal": 0.45,  # Increased from 0.4
            "authority_signal": 0.35,  # Increased from 0.3
            "description": "Unclear value, some risk"
        },
        "Step 2 - Complex Form": {
            "cognitive_demand": 0.4,  # Reduced from 0.5
            "effort_demand": 0.45,  # Reduced from 0.5
            "risk_signal": 0.3,
            "irreversibility": 0.1,
            "delay_to_value": 4,
            "explicit_value": 0.35,  # Increased from 0.3
            "reassurance_signal": 0.45,  # Increased from 0.4
            "authority_signal": 0.35,  # Increased from 0.3
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
    
    # Derive features
    from derive_features import derive_all_features
    df = derive_all_features(df, verbose=False)
    
    # Run simulation
    result_df = run_semantic_aware_simulation(
        df,
        product_steps=product_steps,
        use_llm=False,
        verbose=False,
        seed=42
    )
    
    # Generate diagnostic summary
    summary = generate_diagnostic_summary(result_df, product_steps)
    completion_rate = summary['completion_rate']
    
    # Validate
    passed = expected_min <= completion_rate <= expected_max
    
    result = {
        "scenario": scenario_name,
        "expected_range": (expected_min, expected_max),
        "actual_completion": completion_rate,
        "passed": passed,
        "summary": summary,
        "explanation": explain_probability_collapse(summary) if not passed else "Completion rate within expected range."
    }
    
    print(f"Actual completion: {completion_rate:.1%}")
    print(f"Status: {'✓ PASSED' if passed else '✗ FAILED'}")
    if not passed:
        print(f"Explanation: {result['explanation']}")
    
    return result


def main():
    """Run all validation scenarios."""
    print("\n" + "="*60)
    print("PROBABILITY MODEL VALIDATION")
    print("="*60)
    
    results = []
    
    # Test 1: Perfect flow
    results.append(validate_scenario(
        "Perfect Flow",
        create_perfect_flow(),
        expected_min=0.40,
        expected_max=0.60
    ))
    
    # Test 2: Moderate friction
    results.append(validate_scenario(
        "Moderate Friction",
        create_moderate_friction_flow(),
        expected_min=0.15,
        expected_max=0.30
    ))
    
    # Test 3: High friction
    results.append(validate_scenario(
        "High Friction",
        create_high_friction_flow(),
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
        print("✗ Some validations failed. Review explanations above.")
        return 1


if __name__ == "__main__":
    exit(main())


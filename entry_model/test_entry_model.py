"""
test_entry_model.py - Tests for Entry Model

Validates entry model behavior and integration.
"""

import numpy as np
from entry_model import (
    estimate_entry_probability,
    TrafficSource,
    IntentStrength
)
from entry_model.funnel_integration import compute_full_funnel_prediction


def test_high_intent_traffic():
    """Test that high-intent traffic produces high entry probability."""
    print("Testing high-intent traffic...")
    
    # High intent: direct traffic, high intent strength, strong promise
    result = estimate_entry_probability(
        referrer='direct',
        intent_frame={'commitment_threshold': 0.8, 'tolerance_for_effort': 0.7},
        landing_page_text='Find the Best Credit Card In 60 seconds - No PAN required',
        cta_text='Get Started Now'
    )
    
    assert result.entry_probability > 0.4, f"High intent should have entry prob > 0.4, got {result.entry_probability}"
    assert result.signals.traffic_source == TrafficSource.DIRECT
    assert result.signals.intent_strength == IntentStrength.HIGH
    
    print(f"  ✓ High intent entry probability: {result.entry_probability:.2%}")
    print(f"  ✓ Traffic source: {result.signals.traffic_source.value}")
    print(f"  ✓ Intent strength: {result.signals.intent_strength.value}")
    return True


def test_low_intent_traffic():
    """Test that low-intent traffic produces low entry probability."""
    print("Testing low-intent traffic...")
    
    # Low intent: social traffic, low intent strength, weak promise
    result = estimate_entry_probability(
        referrer='https://facebook.com',
        intent_frame={'commitment_threshold': 0.2, 'tolerance_for_effort': 0.3},
        landing_page_text='Explore credit card options',
        cta_text='Learn More'
    )
    
    assert result.entry_probability < 0.3, f"Low intent should have entry prob < 0.3, got {result.entry_probability}"
    assert result.signals.traffic_source == TrafficSource.SOCIAL
    assert result.signals.intent_strength == IntentStrength.LOW
    
    print(f"  ✓ Low intent entry probability: {result.entry_probability:.2%}")
    print(f"  ✓ Traffic source: {result.signals.traffic_source.value}")
    print(f"  ✓ Intent strength: {result.signals.intent_strength.value}")
    return True


def test_entry_probability_bounds():
    """Test that entry probabilities are within valid bounds [0.01, 0.95]."""
    print("Testing entry probability bounds...")
    
    # Test various scenarios
    scenarios = [
        {'referrer': 'direct', 'intent_frame': {'commitment_threshold': 0.9}},
        {'referrer': 'https://google.com', 'utm_medium': 'cpc'},
        {'referrer': 'https://facebook.com'},
        {'referrer': None, 'utm_source': 'unknown'}
    ]
    
    for i, scenario in enumerate(scenarios):
        result = estimate_entry_probability(**scenario)
        assert 0.01 <= result.entry_probability <= 0.95, \
            f"Scenario {i+1}: Entry prob {result.entry_probability} not in [0.01, 0.95]"
    
    print(f"  ✓ All {len(scenarios)} scenarios within bounds [0.01, 0.95]")
    return True


def test_full_funnel_integration():
    """Test that entry × completion ≈ observed funnel data."""
    print("Testing full funnel integration...")
    
    # Simulate: 1000 visitors, 30% entry, 77% completion
    entry_signals = {
        'referrer': 'direct',
        'intent_frame': {'commitment_threshold': 0.7, 'tolerance_for_effort': 0.6},
        'landing_page_text': 'Find the Best Credit Card In 60 seconds'
    }
    
    behavioral_completion_rate = 0.77  # From behavioral engine
    
    prediction = compute_full_funnel_prediction(
        entry_signals=entry_signals,
        behavioral_completion_rate=behavioral_completion_rate
    )
    
    # Check that total conversion = entry × completion
    expected_total = prediction.entry_probability * prediction.completion_probability
    assert abs(prediction.total_conversion - expected_total) < 0.001, \
        f"Total conversion should equal entry × completion"
    
    # Check that entry prob is reasonable
    assert 0.01 <= prediction.entry_probability <= 0.95, \
        f"Entry probability {prediction.entry_probability} not in valid range"
    
    print(f"  ✓ Entry probability: {prediction.entry_probability:.2%}")
    print(f"  ✓ Completion probability: {prediction.completion_probability:.2%}")
    print(f"  ✓ Total conversion: {prediction.total_conversion:.2%}")
    print(f"  ✓ Integration correct: {prediction.entry_probability:.2%} × {prediction.completion_probability:.2%} = {prediction.total_conversion:.2%}")
    
    return True


def test_traffic_source_ranking():
    """Test that traffic sources are ranked correctly by entry probability."""
    print("Testing traffic source ranking...")
    
    sources = [
        ('direct', TrafficSource.DIRECT),
        ('https://google.com', TrafficSource.SEO),
        ('https://facebook.com', TrafficSource.SOCIAL),
        ('https://unknown-site.com', TrafficSource.REFERRAL)  # Unknown referrer = referral
    ]
    
    entry_probs = []
    for referrer, expected_source in sources:
        result = estimate_entry_probability(referrer=referrer)
        entry_probs.append((result.entry_probability, result.signals.traffic_source))
        print(f"    {referrer}: {result.signals.traffic_source.value} = {result.entry_probability:.2%}")
    
    # Direct should have highest entry prob
    direct_prob = next(p for p, s in entry_probs if s == TrafficSource.DIRECT)
    social_prob = next(p for p, s in entry_probs if s == TrafficSource.SOCIAL)
    
    assert direct_prob > social_prob, \
        f"Direct traffic ({direct_prob:.2%}) should have higher entry prob than social ({social_prob:.2%})"
    
    print(f"  ✓ Traffic source ranking correct")
    print(f"    Direct: {direct_prob:.2%} > Social: {social_prob:.2%}")
    return True


def run_all_tests():
    """Run all entry model tests."""
    print("=" * 80)
    print("ENTRY MODEL TESTS")
    print("=" * 80)
    
    tests = [
        test_high_intent_traffic,
        test_low_intent_traffic,
        test_entry_probability_bounds,
        test_full_funnel_integration,
        test_traffic_source_ranking
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  ❌ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"  ❌ Test error: {e}")
            failed += 1
        print()
    
    print("=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 80)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)


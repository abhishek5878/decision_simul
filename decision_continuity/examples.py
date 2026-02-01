"""
Example flows demonstrating Decision Continuity & Precedent Engine usage.
"""

from decision_continuity import (
    ContinuityEngine,
    DecisionEvent,
    BeliefState,
    DecisionEventType
)
from decision_graph.decision_trace import DecisionTrace, DecisionOutcome
from decision_graph.decision_trace import CognitiveStateSnapshot, IntentSnapshot


def example_1_record_event_during_simulation():
    """
    Example 1: Recording a DecisionEvent during simulation execution.
    
    This shows how to capture decisions DURING execution, not post-hoc.
    """
    print("=" * 60)
    print("Example 1: Recording DecisionEvent During Simulation")
    print("=" * 60)
    
    # Initialize engine
    engine = ContinuityEngine(storage_path="./continuity_data")
    
    # Simulate a decision point during execution
    belief_before = BeliefState(
        trust_level=0.6,
        value_perception=0.3,
        commitment_level=0.2,
        cognitive_energy=0.7,
        risk_perception=0.4,
        intent_strength=0.8
    )
    
    # User decides to continue
    belief_after = BeliefState(
        trust_level=0.65,  # Trust increased slightly
        value_perception=0.3,
        commitment_level=0.4,  # Commitment increased
        cognitive_energy=0.6,  # Energy decreased
        risk_perception=0.4,
        intent_strength=0.8
    )
    
    event = DecisionEvent(
        event_id="evt_001",
        entity_id="product_credigo",
        entity_type="product",
        step_id="Step 3: PAN Entry",
        step_index=2,
        event_type=DecisionEventType.CONTINUATION,
        belief_state_before=belief_before,
        belief_state_after=belief_after,
        action_considered="Continue to next step",
        action_taken="Continue to next step",
        alternatives_rejected=["Drop", "Skip step", "Go back"],
        outcome_observed="User continued to Step 4",
        confidence_level=0.75
    )
    
    # Record the event
    engine.record_event(event)
    
    print(f"✅ Recorded event: {event.event_id}")
    print(f"   Action: {event.action_taken}")
    print(f"   Outcome: {event.outcome_observed}")
    print(f"   Trust delta: {event.get_belief_delta()['trust_delta']:.2f}")
    
    # Check continuity state
    continuity = engine.get_continuity_state("product_credigo", "product")
    if continuity:
        print(f"\n📊 Continuity State:")
        print(f"   Cumulative Trust: {continuity.cumulative_trust:.2f}")
        print(f"   Total Events: {continuity.total_events}")
    
    return engine


def example_2_convert_trace_to_event():
    """
    Example 2: Converting existing DecisionTrace to DecisionEvent.
    
    This bridges the existing DecisionTrace system with DecisionEvent system.
    """
    print("\n" + "=" * 60)
    print("Example 2: Converting DecisionTrace to DecisionEvent")
    print("=" * 60)
    
    engine = ContinuityEngine()
    
    # Create a sample DecisionTrace (from existing system)
    trace = DecisionTrace(
        persona_id="persona_001",
        step_id="Step 3: PAN Entry",
        step_index=2,
        decision=DecisionOutcome.DROP,
        probability_before_sampling=0.35,
        sampled_outcome=False,
        cognitive_state_snapshot=CognitiveStateSnapshot(
            energy=0.3,
            risk=0.7,
            effort=0.6,
            value=0.2,
            control=0.4
        ),
        intent=IntentSnapshot(
            inferred_intent="explore",
            alignment_score=0.4
        ),
        dominant_factors=["risk_spike", "cognitive_fatigue", "value_delay"]
    )
    
    # Convert to DecisionEvent
    event = engine.record_event_from_trace(
        trace=trace,
        entity_id="product_credigo",
        entity_type="product",
        action_considered="Continue to next step",
        action_taken="Drop",
        alternatives_rejected=["Continue", "Skip step"],
        outcome_observed="User dropped at Step 3",
        confidence_level=0.65,
        context={"dominant_factors": trace.dominant_factors}
    )
    
    print(f"✅ Converted trace to event: {event.event_id}")
    print(f"   Event Type: {event.event_type.value}")
    print(f"   Action Taken: {event.action_taken}")
    print(f"   Trust Before: {event.belief_state_before.trust_level:.2f}")
    print(f"   Trust After: {event.belief_state_after.trust_level:.2f}")
    
    return engine


def example_3_query_precedents():
    """
    Example 3: Querying precedents for guidance.
    
    This shows how to query "What usually works in similar situations?"
    """
    print("\n" + "=" * 60)
    print("Example 3: Querying Precedents")
    print("=" * 60)
    
    engine = ContinuityEngine(storage_path="./continuity_data")
    
    # First, record some events to build precedents
    # (In real usage, these would come from historical simulations)
    events = [
        DecisionEvent(
            event_id=f"evt_{i}",
            entity_id="product_credigo",
            entity_type="product",
            step_id="Step 3",
            step_index=2,
            event_type=DecisionEventType.CONTINUATION if i % 2 == 0 else DecisionEventType.DROP,
            belief_state_before=BeliefState(
                trust_level=0.5 + (i * 0.05),
                value_perception=0.2,
                commitment_level=0.3,
                cognitive_energy=0.6,
                risk_perception=0.5,
                intent_strength=0.7
            ),
            belief_state_after=BeliefState(
                trust_level=0.55 + (i * 0.05),
                value_perception=0.2,
                commitment_level=0.4,
                cognitive_energy=0.5,
                risk_perception=0.5,
                intent_strength=0.7
            ),
            action_considered="Continue",
            action_taken="Show value before commitment" if i % 2 == 0 else "Ask for commitment",
            alternatives_rejected=["Drop"],
            outcome_observed="Continued" if i % 2 == 0 else "Dropped",
            confidence_level=0.7,
            context={"dominant_factors": ["value_delay"]}
        )
        for i in range(10)
    ]
    
    for event in events:
        engine.record_event(event)
    
    # Query: "What usually works when belief collapses due to delayed value?"
    results = engine.query_what_usually_works(
        condition_description="belief collapses due to delayed value",
        step_id="Step 3"
    )
    
    print(f"\n📊 Query Results: What usually works?")
    print(f"   Found {len(results)} precedent matches\n")
    
    for i, result in enumerate(results[:5], 1):
        print(f"   {i}. Action: {result['action']}")
        print(f"      Success Rate: {result['success_rate']:.2%}")
        print(f"      Occurrences: {result['total_occurrences']}")
        print(f"      Confidence: {result['average_confidence']:.2f}")
        print()
    
    return engine


def example_4_continuity_across_runs():
    """
    Example 4: Continuity state persists across simulation runs.
    
    This shows how belief state accumulates over time.
    """
    print("\n" + "=" * 60)
    print("Example 4: Continuity Across Runs")
    print("=" * 60)
    
    engine = ContinuityEngine(storage_path="./continuity_data")
    
    entity_id = "product_credigo"
    entity_type = "product"
    
    # Run 1: Initial events
    print("Run 1: Recording initial events...")
    for i in range(3):
        event = DecisionEvent(
            event_id=f"run1_evt_{i}",
            entity_id=entity_id,
            entity_type=entity_type,
            step_id=f"Step {i+1}",
            step_index=i,
            event_type=DecisionEventType.CONTINUATION,
            belief_state_before=BeliefState(
                trust_level=0.5 + (i * 0.1),
                value_perception=0.2,
                commitment_level=0.2,
                cognitive_energy=0.7,
                risk_perception=0.4,
                intent_strength=0.8
            ),
            belief_state_after=BeliefState(
                trust_level=0.55 + (i * 0.1),
                value_perception=0.2,
                commitment_level=0.3,
                cognitive_energy=0.6,
                risk_perception=0.4,
                intent_strength=0.8
            ),
            action_considered="Continue",
            action_taken="Continue",
            alternatives_rejected=["Drop"],
            confidence_level=0.7
        )
        engine.record_event(event)
    
    continuity = engine.get_continuity_state(entity_id, entity_type)
    print(f"   Cumulative Trust: {continuity.cumulative_trust:.2f}")
    print(f"   Total Events: {continuity.total_events}")
    
    # Run 2: More events (simulating a new simulation run)
    print("\nRun 2: Recording more events...")
    for i in range(2):
        event = DecisionEvent(
            event_id=f"run2_evt_{i}",
            entity_id=entity_id,
            entity_type=entity_type,
            step_id=f"Step {i+1}",
            step_index=i,
            event_type=DecisionEventType.CONTINUATION,
            belief_state_before=BeliefState(
                trust_level=continuity.cumulative_trust,  # Start from accumulated state
                value_perception=0.3,
                commitment_level=continuity.cumulative_commitment,
                cognitive_energy=0.7,
                risk_perception=0.4,
                intent_strength=0.8
            ),
            belief_state_after=BeliefState(
                trust_level=continuity.cumulative_trust + 0.1,
                value_perception=0.3,
                commitment_level=continuity.cumulative_commitment + 0.1,
                cognitive_energy=0.6,
                risk_perception=0.4,
                intent_strength=0.8
            ),
            action_considered="Continue",
            action_taken="Continue",
            alternatives_rejected=["Drop"],
            confidence_level=0.7
        )
        engine.record_event(event)
    
    continuity = engine.get_continuity_state(entity_id, entity_type)
    print(f"   Cumulative Trust: {continuity.cumulative_trust:.2f}")
    print(f"   Total Events: {continuity.total_events}")
    print(f"   Total Runs: {continuity.total_runs}")
    
    print("\n✅ Continuity state persists across runs!")


def example_5_query_what_works():
    """
    Example 5: Query "What usually works when belief collapses due to delayed value?"
    
    This is the example query from the requirements.
    """
    print("\n" + "=" * 60)
    print("Example 5: Query - What works when belief collapses?")
    print("=" * 60)
    
    engine = ContinuityEngine(storage_path="./continuity_data")
    
    # Query
    results = engine.query_what_usually_works(
        condition_description="belief collapses due to delayed value",
        step_id="Step 3"
    )
    
    print(f"\nQuery: 'What usually works when belief collapses due to delayed value?'")
    print(f"Results: {len(results)} precedent matches\n")
    
    if results:
        print("Top recommendations:")
        for i, result in enumerate(results[:3], 1):
            print(f"\n{i}. {result['action']}")
            print(f"   Success Rate: {result['success_rate']:.1%}")
            print(f"   Based on {result['total_occurrences']} historical occurrences")
            print(f"   Average Confidence: {result['average_confidence']:.2f}")
    else:
        print("No precedents found. Record more events to build precedents.")
    
    return engine


if __name__ == "__main__":
    # Run all examples
    example_1_record_event_during_simulation()
    example_2_convert_trace_to_event()
    example_3_query_precedents()
    example_4_continuity_across_runs()
    example_5_query_what_works()
    
    print("\n" + "=" * 60)
    print("✅ All examples completed!")
    print("=" * 60)


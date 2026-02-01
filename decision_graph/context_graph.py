"""
context_graph.py - Context Graph from Decision Traces

The context graph is built FROM traces, not inferred by ML.
This is the thing that becomes your moat.

Nodes: Persona archetypes, Steps, Intents, Failure modes
Edges: Decision outcomes, Repeated precedents, Dominant causal paths
"""

from typing import Dict, List, Set, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from decision_graph.decision_trace import DecisionTrace, DecisionOutcome, DecisionSequence


@dataclass
class ContextGraphNode:
    """Node in context graph."""
    node_id: str
    node_type: str  # "persona", "step", "intent", "failure_mode"
    attributes: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'node_id': self.node_id,
            'node_type': self.node_type,
            'attributes': self.attributes
        }


@dataclass
class ContextGraphEdge:
    """Edge in context graph."""
    source_id: str
    target_id: str
    edge_type: str  # "decision", "precedent", "causal_path"
    weight: float = 1.0
    attributes: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'source_id': self.source_id,
            'target_id': self.target_id,
            'edge_type': self.edge_type,
            'weight': float(self.weight),
            'attributes': self.attributes
        }


@dataclass
class ContextGraph:
    """
    Context Graph - Built from decision traces.
    
    This graph captures:
    - Which persona types reach which steps
    - Which steps filter which persona types
    - Repeated precedents (persona → step → outcome patterns)
    - Dominant causal paths (why personas drop)
    """
    nodes: Dict[str, ContextGraphNode] = field(default_factory=dict)
    edges: List[ContextGraphEdge] = field(default_factory=list)
    
    # Derived insights
    dominant_failure_paths: List[Dict] = field(default_factory=list)
    persona_step_rejection_map: Dict[str, List[str]] = field(default_factory=dict)  # persona_id -> rejected_step_ids
    repeated_precedents: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'nodes': {k: v.to_dict() for k, v in self.nodes.items()},
            'edges': [e.to_dict() for e in self.edges],
            'dominant_failure_paths': self.dominant_failure_paths,
            'persona_step_rejection_map': self.persona_step_rejection_map,
            'repeated_precedents': self.repeated_precedents
        }


def build_context_graph_from_traces(
    sequences: List[DecisionSequence],
    product_steps: Dict
) -> ContextGraph:
    """
    Build context graph from decision traces.
    
    This is the core function - it builds the graph FROM traces,
    not by inference or ML.
    
    Args:
        sequences: List of decision sequences (one per persona trajectory)
        product_steps: Product step definitions
    
    Returns:
        ContextGraph built from traces
    """
    graph = ContextGraph()
    
    # Track which personas were rejected at which steps
    persona_rejections = defaultdict(set)  # persona_id -> set of rejected step_ids
    step_rejections = defaultdict(set)  # step_id -> set of rejected persona_ids
    
    # Track dominant failure paths
    failure_paths = []  # List of (persona_id, step_id, dominant_factors)
    
    # Track repeated precedents (persona → step → outcome patterns)
    precedents = defaultdict(int)  # (persona_pattern, step_id, outcome) -> count
    
    # Process each sequence
    for sequence in sequences:
        persona_id = sequence.persona_id
        
        # Add persona node if not exists
        if persona_id not in graph.nodes:
            graph.nodes[persona_id] = ContextGraphNode(
                node_id=persona_id,
                node_type="persona"
            )
        
        # Process each trace in sequence
        for trace in sequence.traces:
            step_id = trace.step_id
            
            # Add step node if not exists
            if step_id not in graph.nodes:
                graph.nodes[step_id] = ContextGraphNode(
                    node_id=step_id,
                    node_type="step",
                    attributes={'step_index': trace.step_index}
                )
            
            # Add intent node if not exists
            intent_id = trace.intent.inferred_intent
            if intent_id not in graph.nodes:
                graph.nodes[intent_id] = ContextGraphNode(
                    node_id=intent_id,
                    node_type="intent"
                )
            
            # Add edges
            # Persona -> Step (decision edge)
            graph.edges.append(ContextGraphEdge(
                source_id=persona_id,
                target_id=step_id,
                edge_type="decision",
                weight=1.0,
                attributes={
                    'decision': trace.decision.value,
                    'probability': trace.probability_before_sampling
                }
            ))
            
            # Step -> Intent (alignment edge)
            graph.edges.append(ContextGraphEdge(
                source_id=step_id,
                target_id=intent_id,
                edge_type="alignment",
                weight=trace.intent.alignment_score,
                attributes={'alignment_score': trace.intent.alignment_score}
            ))
            
            # Track rejections
            if trace.decision == DecisionOutcome.DROP:
                persona_rejections[persona_id].add(step_id)
                step_rejections[step_id].add(persona_id)
                
                # Record failure path
                failure_paths.append({
                    'persona_id': persona_id,
                    'step_id': step_id,
                    'step_index': trace.step_index,
                    'dominant_factors': trace.dominant_factors,
                    'intent': intent_id,
                    'alignment_score': trace.intent.alignment_score
                })
                
                # Add failure mode nodes and edges
                for factor in trace.dominant_factors:
                    failure_mode_id = f"{step_id}:{factor}"
                    if failure_mode_id not in graph.nodes:
                        graph.nodes[failure_mode_id] = ContextGraphNode(
                            node_id=failure_mode_id,
                            node_type="failure_mode",
                            attributes={'step_id': step_id, 'factor': factor}
                        )
                    
                    # Step -> Failure mode edge
                    graph.edges.append(ContextGraphEdge(
                        source_id=step_id,
                        target_id=failure_mode_id,
                        edge_type="causes",
                        weight=1.0
                    ))
            
            # Track precedents (simplified - persona pattern based on cognitive state)
            persona_pattern = _derive_persona_pattern(trace.cognitive_state_snapshot)
            precedent_key = (persona_pattern, step_id, trace.decision.value)
            precedents[precedent_key] += 1
    
    # Build rejection map
    graph.persona_step_rejection_map = {
        persona_id: list(rejected_steps)
        for persona_id, rejected_steps in persona_rejections.items()
    }
    
    # Build dominant failure paths (top N by frequency)
    failure_path_counts = Counter(
        (fp['step_id'], tuple(sorted(fp['dominant_factors'])))
        for fp in failure_paths
    )
    
    graph.dominant_failure_paths = [
        {
            'step_id': step_id,
            'dominant_factors': list(factors),
            'count': count,
            'percentage': count / len(sequences) * 100 if sequences else 0
        }
        for (step_id, factors), count in failure_path_counts.most_common(10)
    ]
    
    # Build repeated precedents (patterns that appear multiple times)
    graph.repeated_precedents = [
        {
            'persona_pattern': pattern,
            'step_id': step_id,
            'outcome': outcome,
            'count': count
        }
        for (pattern, step_id, outcome), count in precedents.items()
        if count > 1
    ]
    
    return graph


def _derive_persona_pattern(cognitive_state) -> str:
    """
    Derive a persona pattern from cognitive state snapshot.
    
    This is a simplified pattern - in practice, you might use
    persona attributes or more sophisticated clustering.
    """
    # Simple pattern based on cognitive state thresholds
    if cognitive_state.energy > 0.6:
        energy_level = "high_energy"
    elif cognitive_state.energy > 0.3:
        energy_level = "medium_energy"
    else:
        energy_level = "low_energy"
    
    if cognitive_state.risk > 0.6:
        risk_level = "high_risk"
    elif cognitive_state.risk > 0.3:
        risk_level = "medium_risk"
    else:
        risk_level = "low_risk"
    
    return f"{energy_level}_{risk_level}"


@dataclass
class ContextGraphSummary:
    """Summary of context graph for PipelineResult."""
    dominant_failure_paths: List[Dict]
    persona_step_rejection_map: Dict[str, List[str]]
    repeated_precedents: List[Dict]
    total_nodes: int
    total_edges: int
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'dominant_failure_paths': self.dominant_failure_paths,
            'persona_step_rejection_map': self.persona_step_rejection_map,
            'repeated_precedents': self.repeated_precedents,
            'total_nodes': self.total_nodes,
            'total_edges': self.total_edges
        }


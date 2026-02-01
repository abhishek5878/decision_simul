"""
dropsim_context_graph.py - Context Graph Layer for DropSim

Records event-level behavioral traces during simulation runs, enabling:
- Causal inspection
- Path-based reasoning
- "Why did this happen?" explanations
- Future extensibility into counterfactual simulation

This is structured logging + reasoning over the existing engine, not a new model.
"""

from typing import Dict, List, Optional, Tuple, Literal
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import json


# ============================================================================
# Event Abstraction
# ============================================================================

@dataclass
class Event:
    """Single behavioral transition event."""
    step_id: str
    persona_id: str
    variant_id: str
    state_before: Dict[str, float]  # cognitive_energy, perceived_risk, etc.
    state_after: Dict[str, float]
    cost_components: Dict[str, float]  # cognitive_cost, effort_cost, risk_cost, etc.
    decision: Literal["continue", "drop"]
    dominant_factor: str  # e.g., "fatigue", "risk", "effort", "multi-factor"
    timestep: int  # monotonic step index (0-based)
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'step_id': self.step_id,
            'persona_id': self.persona_id,
            'variant_id': self.variant_id,
            'state_before': self.state_before,
            'state_after': self.state_after,
            'cost_components': self.cost_components,
            'decision': self.decision,
            'dominant_factor': self.dominant_factor,
            'timestep': self.timestep
        }


# ============================================================================
# Event Trace
# ============================================================================

@dataclass
class EventTrace:
    """Complete event trace for one persona × state-variant simulation."""
    persona_id: str
    variant_id: str
    events: List[Event]
    final_outcome: Literal["completed", "dropped"]
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'persona_id': self.persona_id,
            'variant_id': self.variant_id,
            'events': [e.to_dict() for e in self.events],
            'final_outcome': self.final_outcome
        }


# ============================================================================
# Context Graph Nodes and Edges
# ============================================================================

@dataclass
class StepNode:
    """Node in context graph representing a product step."""
    step_id: str
    total_entries: int  # How many times this step was reached
    total_exits: int  # How many times users left from this step
    total_drops: int  # How many times users dropped at this step
    avg_cognitive_energy: float
    avg_perceived_risk: float
    avg_perceived_effort: float
    avg_perceived_value: float
    avg_perceived_control: float
    dominant_failure_factor: Optional[str]  # Most common failure reason at this step
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'step_id': self.step_id,
            'total_entries': self.total_entries,
            'total_exits': self.total_exits,
            'total_drops': self.total_drops,
            'drop_rate': self.total_drops / self.total_entries if self.total_entries > 0 else 0.0,
            'avg_cognitive_energy': self.avg_cognitive_energy,
            'avg_perceived_risk': self.avg_perceived_risk,
            'avg_perceived_effort': self.avg_perceived_effort,
            'avg_perceived_value': self.avg_perceived_value,
            'avg_perceived_control': self.avg_perceived_control,
            'dominant_failure_factor': self.dominant_failure_factor
        }


@dataclass
class EdgeStats:
    """Edge statistics for transitions between steps."""
    from_step: str
    to_step: str
    traversal_count: int  # How many times this transition occurred
    avg_energy_delta: float  # Average change in cognitive_energy
    avg_risk_delta: float  # Average change in perceived_risk
    avg_effort_delta: float  # Average change in perceived_effort
    avg_value_delta: float  # Average change in perceived_value
    avg_control_delta: float  # Average change in perceived_control
    dominant_failure_factor: Optional[str]  # Most common failure reason on this edge
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'from_step': self.from_step,
            'to_step': self.to_step,
            'traversal_count': self.traversal_count,
            'avg_energy_delta': self.avg_energy_delta,
            'avg_risk_delta': self.avg_risk_delta,
            'avg_effort_delta': self.avg_effort_delta,
            'avg_value_delta': self.avg_value_delta,
            'avg_control_delta': self.avg_control_delta,
            'dominant_failure_factor': self.dominant_failure_factor
        }


# ============================================================================
# Context Graph
# ============================================================================

@dataclass
class ContextGraph:
    """Aggregated context graph from event traces."""
    nodes: Dict[str, StepNode]  # step_id -> StepNode
    edges: Dict[Tuple[str, str], EdgeStats]  # (from_step, to_step) -> EdgeStats
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'nodes': {step_id: node.to_dict() for step_id, node in self.nodes.items()},
            'edges': {
                f"{from_step}->{to_step}": edge.to_dict()
                for (from_step, to_step), edge in self.edges.items()
            }
        }


# ============================================================================
# Context Graph Builder
# ============================================================================

def build_context_graph(event_traces: List[EventTrace]) -> ContextGraph:
    """
    Build a context graph from a list of event traces.
    
    Args:
        event_traces: List of EventTrace objects from a simulation run
    
    Returns:
        ContextGraph with aggregated nodes and edges
    """
    # Initialize aggregators
    node_data = defaultdict(lambda: {
        'entries': 0,
        'exits': 0,
        'drops': 0,
        'cognitive_energy_sum': 0.0,
        'perceived_risk_sum': 0.0,
        'perceived_effort_sum': 0.0,
        'perceived_value_sum': 0.0,
        'perceived_control_sum': 0.0,
        'failure_factors': Counter()
    })
    
    edge_data = defaultdict(lambda: {
        'traversals': 0,
        'energy_deltas': [],
        'risk_deltas': [],
        'effort_deltas': [],
        'value_deltas': [],
        'control_deltas': [],
        'failure_factors': Counter()
    })
    
    # Process each trace
    for trace in event_traces:
        if not trace.events:
            continue
        
        # Process events in sequence
        for i, event in enumerate(trace.events):
            step_id = event.step_id
            
            # Node: entry
            node_data[step_id]['entries'] += 1
            node_data[step_id]['cognitive_energy_sum'] += event.state_before.get('cognitive_energy', 0)
            node_data[step_id]['perceived_risk_sum'] += event.state_before.get('perceived_risk', 0)
            node_data[step_id]['perceived_effort_sum'] += event.state_before.get('perceived_effort', 0)
            node_data[step_id]['perceived_value_sum'] += event.state_before.get('perceived_value', 0)
            node_data[step_id]['perceived_control_sum'] += event.state_before.get('perceived_control', 0)
            
            # Node: exit (if not last event or if dropped)
            if event.decision == "drop" or i == len(trace.events) - 1:
                node_data[step_id]['exits'] += 1
                if event.decision == "drop":
                    node_data[step_id]['drops'] += 1
                    if event.dominant_factor:
                        node_data[step_id]['failure_factors'][event.dominant_factor] += 1
            
            # Edge: transition to next step (if exists)
            if i < len(trace.events) - 1:
                next_event = trace.events[i + 1]
                from_step = step_id
                to_step = next_event.step_id
                edge_key = (from_step, to_step)
                
                edge_data[edge_key]['traversals'] += 1
                
                # Compute deltas
                energy_delta = next_event.state_before.get('cognitive_energy', 0) - event.state_after.get('cognitive_energy', 0)
                risk_delta = next_event.state_before.get('perceived_risk', 0) - event.state_after.get('perceived_risk', 0)
                effort_delta = next_event.state_before.get('perceived_effort', 0) - event.state_after.get('perceived_effort', 0)
                value_delta = next_event.state_before.get('perceived_value', 0) - event.state_after.get('perceived_value', 0)
                control_delta = next_event.state_before.get('perceived_control', 0) - event.state_after.get('perceived_control', 0)
                
                edge_data[edge_key]['energy_deltas'].append(energy_delta)
                edge_data[edge_key]['risk_deltas'].append(risk_delta)
                edge_data[edge_key]['effort_deltas'].append(effort_delta)
                edge_data[edge_key]['value_deltas'].append(value_delta)
                edge_data[edge_key]['control_deltas'].append(control_delta)
                
                # If next event is a drop, record failure factor
                if next_event.decision == "drop" and next_event.dominant_factor:
                    edge_data[edge_key]['failure_factors'][next_event.dominant_factor] += 1
    
    # Build nodes
    nodes = {}
    for step_id, data in node_data.items():
        entries = data['entries']
        nodes[step_id] = StepNode(
            step_id=step_id,
            total_entries=entries,
            total_exits=data['exits'],
            total_drops=data['drops'],
            avg_cognitive_energy=data['cognitive_energy_sum'] / entries if entries > 0 else 0.0,
            avg_perceived_risk=data['perceived_risk_sum'] / entries if entries > 0 else 0.0,
            avg_perceived_effort=data['perceived_effort_sum'] / entries if entries > 0 else 0.0,
            avg_perceived_value=data['perceived_value_sum'] / entries if entries > 0 else 0.0,
            avg_perceived_control=data['perceived_control_sum'] / entries if entries > 0 else 0.0,
            dominant_failure_factor=data['failure_factors'].most_common(1)[0][0] if data['failure_factors'] else None
        )
    
    # Build edges
    edges = {}
    for (from_step, to_step), data in edge_data.items():
        traversals = data['traversals']
        edges[(from_step, to_step)] = EdgeStats(
            from_step=from_step,
            to_step=to_step,
            traversal_count=traversals,
            avg_energy_delta=sum(data['energy_deltas']) / traversals if traversals > 0 else 0.0,
            avg_risk_delta=sum(data['risk_deltas']) / traversals if traversals > 0 else 0.0,
            avg_effort_delta=sum(data['effort_deltas']) / traversals if traversals > 0 else 0.0,
            avg_value_delta=sum(data['value_deltas']) / traversals if traversals > 0 else 0.0,
            avg_control_delta=sum(data['control_deltas']) / traversals if traversals > 0 else 0.0,
            dominant_failure_factor=data['failure_factors'].most_common(1)[0][0] if data['failure_factors'] else None
        )
    
    return ContextGraph(nodes=nodes, edges=edges)


# ============================================================================
# Query Functions (Must-Have)
# ============================================================================

def get_most_common_paths(context_graph: ContextGraph, min_traversals: int = 50, top_n: int = 10) -> List[Dict]:
    """
    Get the most common paths through the product.
    
    Returns:
        List of dicts with path info sorted by frequency
    """
    # Build path frequency from edges
    path_freq = []
    
    for edge in context_graph.edges.values():
        if edge.traversal_count >= min_traversals:
            path_freq.append({
                'path': [edge.from_step, edge.to_step],
                'traversal_count': edge.traversal_count,
                'avg_energy_delta': edge.avg_energy_delta,
                'avg_risk_delta': edge.avg_risk_delta,
                'avg_value_delta': edge.avg_value_delta,
                'failure_probability': 0.0  # Will compute if edge leads to failure
            })
    
    # Sort by traversal count
    path_freq.sort(key=lambda x: x['traversal_count'], reverse=True)
    
    # Compute failure probability for paths that lead to drops
    for path_info in path_freq:
        from_step, to_step = path_info['path']
        to_node = context_graph.nodes.get(to_step)
        if to_node and to_node.total_entries > 0:
            path_info['failure_probability'] = to_node.total_drops / to_node.total_entries
    
    return path_freq[:top_n]


def get_highest_loss_transitions(context_graph: ContextGraph, top_n: int = 10) -> List[Dict]:
    """
    Get transitions with highest cognitive energy loss.
    
    Returns:
        List of dicts with transition info sorted by energy loss
    """
    transitions = []
    for edge in context_graph.edges.values():
        if edge.traversal_count > 0:
            transitions.append({
                'from_step': edge.from_step,
                'to_step': edge.to_step,
                'avg_energy_delta': edge.avg_energy_delta,
                'traversal_count': edge.traversal_count,
                'avg_risk_delta': edge.avg_risk_delta,
                'avg_effort_delta': edge.avg_effort_delta,
                'avg_value_delta': edge.avg_value_delta
            })
    
    # Sort by energy loss (most negative = highest loss)
    transitions.sort(key=lambda x: x['avg_energy_delta'])
    
    return transitions[:top_n]


def get_most_fragile_steps(context_graph: ContextGraph, min_entries: int = 5, top_n: int = 10) -> List[Dict]:
    """
    Get steps that are most fragile (high drop rate).
    
    Returns:
        List of dicts with fragile step info
    """
    fragile = []
    
    for step_id, node in context_graph.nodes.items():
        if node.total_entries >= min_entries:
            drop_rate = node.total_drops / node.total_entries if node.total_entries > 0 else 0.0
            fragile.append({
                'step_id': step_id,
                'drop_rate': drop_rate,
                'total_entries': node.total_entries,
                'total_drops': node.total_drops,
                'dominant_failure_factor': node.dominant_failure_factor,
                'avg_cognitive_energy': node.avg_cognitive_energy,
                'avg_perceived_risk': node.avg_perceived_risk,
                'avg_perceived_effort': node.avg_perceived_effort
            })
    
    # Sort by drop rate (highest first)
    fragile.sort(key=lambda x: x['drop_rate'], reverse=True)
    
    return fragile[:top_n]


def get_paths_leading_to_drop(context_graph: ContextGraph, min_failures: int = 10, top_n: int = 10) -> List[Dict]:
    """
    Get paths that most often lead to failure.
    
    Returns:
        List of dicts with path info leading to drops
    """
    # Find edges that lead to steps with drops
    failure_paths = []
    
    for edge in context_graph.edges.values():
        to_node = context_graph.nodes.get(edge.to_step)
        if to_node and to_node.total_drops >= min_failures:
            failure_count = to_node.total_drops
            failure_paths.append({
                'path': [edge.from_step, edge.to_step],
                'failure_count': failure_count,
                'failure_rate': failure_count / edge.traversal_count if edge.traversal_count > 0 else 0.0,
                'dominant_factor': edge.dominant_failure_factor or to_node.dominant_failure_factor,
                'avg_energy_delta': edge.avg_energy_delta,
                'traversal_count': edge.traversal_count
            })
    
    # Sort by failure count (most common failure paths)
    failure_paths.sort(key=lambda x: x['failure_count'], reverse=True)
    
    return failure_paths[:top_n]


def get_successful_paths(context_graph: ContextGraph, min_traversals: int = 10, top_n: int = 10) -> List[Dict]:
    """
    Get paths that succeed despite high risk/effort.
    
    Returns:
        List of dicts with successful path info
    """
    successful_paths = []
    
    for edge in context_graph.edges.values():
        if edge.traversal_count >= min_traversals:
            # Check if this edge doesn't lead to high failure
            to_node = context_graph.nodes.get(edge.to_step)
            if to_node:
                success_rate = 1.0 - (to_node.total_drops / to_node.total_entries) if to_node.total_entries > 0 else 1.0
                
                # High risk/effort but still successful
                if (edge.avg_risk_delta > 0.2 or edge.avg_effort_delta > 0.2) and success_rate > 0.5:
                    successful_paths.append({
                        'path': [edge.from_step, edge.to_step],
                        'traversal_count': edge.traversal_count,
                        'success_rate': success_rate,
                        'avg_risk_delta': edge.avg_risk_delta,
                        'avg_effort_delta': edge.avg_effort_delta,
                        'avg_value_delta': edge.avg_value_delta,
                        'avg_energy_delta': edge.avg_energy_delta
                    })
    
    # Sort by success rate
    successful_paths.sort(key=lambda x: x['success_rate'], reverse=True)
    
    return successful_paths[:top_n]


# Legacy query functions (for backward compatibility)
def query_paths_to_failure(context_graph: ContextGraph, min_failures: int = 10) -> List[Dict]:
    """
    Find paths that most often lead to failure.
    
    Returns:
        List of dicts with path info: {'path': [...], 'failure_count': N, 'failure_rate': ...}
    """
    # Find edges with failures
    failure_edges = [
        (edge.from_step, edge.to_step, edge.traversal_count)
        for edge in context_graph.edges.values()
        if edge.dominant_failure_factor is not None
    ]
    
    # Sort by traversal count (most common failure paths)
    failure_edges.sort(key=lambda x: x[2], reverse=True)
    
    results = []
    for from_step, to_step, count in failure_edges[:20]:  # Top 20
        if count >= min_failures:
            edge = context_graph.edges[(from_step, to_step)]
            results.append({
                'path': [from_step, to_step],
                'failure_count': count,
                'failure_rate': 1.0,  # All traversals on this edge lead to failure
                'dominant_factor': edge.dominant_failure_factor,
                'avg_energy_delta': edge.avg_energy_delta
            })
    
    return results


def query_high_energy_loss_transitions(context_graph: ContextGraph, top_n: int = 10) -> List[Dict]:
    """
    Find transitions with highest cognitive energy loss.
    
    Returns:
        List of dicts with transition info sorted by energy loss
    """
    transitions = []
    for edge in context_graph.edges.values():
        if edge.traversal_count > 0:
            transitions.append({
                'from_step': edge.from_step,
                'to_step': edge.to_step,
                'avg_energy_delta': edge.avg_energy_delta,
                'traversal_count': edge.traversal_count,
                'avg_risk_delta': edge.avg_risk_delta,
                'avg_effort_delta': edge.avg_effort_delta
            })
    
    # Sort by energy loss (most negative = highest loss)
    transitions.sort(key=lambda x: x['avg_energy_delta'])
    
    return transitions[:top_n]


def query_fragile_transitions(context_graph: ContextGraph, min_traversals: int = 5) -> List[Dict]:
    """
    Find transitions that are fragile (high drop rate, low traversal count).
    
    Returns:
        List of dicts with fragile transition info
    """
    fragile = []
    
    for step_id, node in context_graph.nodes.items():
        if node.total_entries >= min_traversals:
            drop_rate = node.total_drops / node.total_entries if node.total_entries > 0 else 0.0
            if drop_rate > 0.1:  # More than 10% drop rate
                fragile.append({
                    'step_id': step_id,
                    'drop_rate': drop_rate,
                    'total_entries': node.total_entries,
                    'total_drops': node.total_drops,
                    'dominant_failure_factor': node.dominant_failure_factor,
                    'avg_cognitive_energy': node.avg_cognitive_energy
                })
    
    # Sort by drop rate (highest first)
    fragile.sort(key=lambda x: x['drop_rate'], reverse=True)
    
    return fragile


def query_successful_paths_despite_risk(context_graph: ContextGraph, min_traversals: int = 10) -> List[Dict]:
    """
    Find paths that succeed despite high risk/effort.
    
    Returns:
        List of dicts with successful path info
    """
    successful_paths = []
    
    for edge in context_graph.edges.values():
        if edge.traversal_count >= min_traversals:
            # High risk/effort but still traversed (successful)
            if edge.avg_risk_delta > 0.2 or edge.avg_effort_delta > 0.2:
                # Check if this edge doesn't lead to failure
                to_node = context_graph.nodes.get(edge.to_step)
                if to_node and to_node.total_drops < to_node.total_entries * 0.5:  # Less than 50% drop
                    successful_paths.append({
                        'from_step': edge.from_step,
                        'to_step': edge.to_step,
                        'traversal_count': edge.traversal_count,
                        'avg_risk_delta': edge.avg_risk_delta,
                        'avg_effort_delta': edge.avg_effort_delta,
                        'avg_value_delta': edge.avg_value_delta,
                        'success_rate': 1.0 - (to_node.total_drops / to_node.total_entries) if to_node.total_entries > 0 else 0.0
                    })
    
    # Sort by success rate
    successful_paths.sort(key=lambda x: x['success_rate'], reverse=True)
    
    return successful_paths


def query_dominant_paths(context_graph: ContextGraph, min_traversals: int = 50) -> List[Dict]:
    """
    Find the most common paths through the product.
    
    Returns:
        List of dicts with path info sorted by frequency
    """
    # Build path frequency from edges
    path_freq = Counter()
    
    # Simple heuristic: count consecutive edge traversals
    for edge in context_graph.edges.values():
        if edge.traversal_count >= min_traversals:
            path_freq[(edge.from_step, edge.to_step)] = edge.traversal_count
    
    # Convert to list of dicts
    results = []
    for (from_step, to_step), count in path_freq.most_common(20):
        edge = context_graph.edges.get((from_step, to_step))
        if edge:
            results.append({
                'path': [from_step, to_step],
                'traversal_count': count,
                'avg_energy_delta': edge.avg_energy_delta,
                'avg_risk_delta': edge.avg_risk_delta,
                'avg_value_delta': edge.avg_value_delta
            })
    
    return results


# ============================================================================
# Context Graph Summary
# ============================================================================

def summarize_context_graph(context_graph: ContextGraph) -> Dict:
    """
    Generate a summary of the context graph with key insights.
    
    Returns:
        Dict with summary statistics and insights matching required output format
    """
    # Use the required query function names
    dominant_paths = get_most_common_paths(context_graph, min_traversals=50, top_n=10)
    energy_loss = get_highest_loss_transitions(context_graph, top_n=10)
    fragile_steps = get_most_fragile_steps(context_graph, min_entries=5, top_n=10)
    failure_paths = get_paths_leading_to_drop(context_graph, min_failures=10, top_n=10)
    successful_paths = get_successful_paths(context_graph, min_traversals=10, top_n=10)
    
    return {
        'summary': {
            'total_nodes': len(context_graph.nodes),
            'total_edges': len(context_graph.edges),
            'total_traversals': sum(edge.traversal_count for edge in context_graph.edges.values())
        },
        'dominant_paths': dominant_paths,
        'highest_loss_transitions': energy_loss,
        'fragile_steps': fragile_steps,
        'paths_leading_to_drop': failure_paths,
        'successful_paths': successful_paths
    }


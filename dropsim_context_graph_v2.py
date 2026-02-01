"""
dropsim_context_graph_v2.py - Context Graph v2

A graph that records actual decisions, states, entities, and policies.
Grows over time and is queryable.

Nodes:
- Decisions
- States
- Entities (users, accounts, steps)
- Policies / rules

Edges:
- "was influenced by"
- "was justified by"
- "led to"
- "overrode"
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import json
import os


@dataclass
class GraphNode:
    """A node in the context graph."""
    node_id: str
    node_type: str  # "decision", "state", "entity", "policy"
    properties: Dict
    timestamp: str
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'node_id': self.node_id,
            'node_type': self.node_type,
            'properties': self.properties,
            'timestamp': self.timestamp
        }


@dataclass
class GraphEdge:
    """An edge in the context graph."""
    edge_id: str
    from_node: str
    to_node: str
    edge_type: str  # "was_influenced_by", "was_justified_by", "led_to", "overrode"
    properties: Dict
    timestamp: str
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'edge_id': self.edge_id,
            'from_node': self.from_node,
            'to_node': self.to_node,
            'edge_type': self.edge_type,
            'properties': self.properties,
            'timestamp': self.timestamp
        }


class ContextGraphV2:
    """Context Graph v2 - records actual decisions and relationships."""
    
    def __init__(self, store_path: str = "context_graph_v2.json"):
        self.store_path = store_path
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: Dict[str, GraphEdge] = {}
        self._load()
    
    def _load(self):
        """Load graph from disk."""
        if os.path.exists(self.store_path):
            try:
                with open(self.store_path, 'r') as f:
                    data = json.load(f)
                    
                    # Load nodes
                    for node_data in data.get('nodes', []):
                        node = GraphNode(
                            node_id=node_data['node_id'],
                            node_type=node_data['node_type'],
                            properties=node_data['properties'],
                            timestamp=node_data.get('timestamp', datetime.now().isoformat())
                        )
                        self.nodes[node.node_id] = node
                    
                    # Load edges
                    for edge_data in data.get('edges', []):
                        edge = GraphEdge(
                            edge_id=edge_data['edge_id'],
                            from_node=edge_data['from_node'],
                            to_node=edge_data['to_node'],
                            edge_type=edge_data['edge_type'],
                            properties=edge_data['properties'],
                            timestamp=edge_data.get('timestamp', datetime.now().isoformat())
                        )
                        self.edges[edge.edge_id] = edge
            except Exception:
                pass
    
    def _save(self):
        """Save graph to disk."""
        data = {
            'nodes': [n.to_dict() for n in self.nodes.values()],
            'edges': [e.to_dict() for e in self.edges.values()],
            'last_updated': datetime.now().isoformat()
        }
        with open(self.store_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def add_node(
        self,
        node_id: str,
        node_type: str,
        properties: Dict
    ):
        """Add a node to the graph."""
        node = GraphNode(
            node_id=node_id,
            node_type=node_type,
            properties=properties,
            timestamp=datetime.now().isoformat()
        )
        self.nodes[node_id] = node
        self._save()
    
    def add_edge(
        self,
        from_node: str,
        to_node: str,
        edge_type: str,
        properties: Dict = None
    ):
        """Add an edge to the graph."""
        edge_id = f"edge_{from_node}_{to_node}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        edge = GraphEdge(
            edge_id=edge_id,
            from_node=from_node,
            to_node=to_node,
            edge_type=edge_type,
            properties=properties or {},
            timestamp=datetime.now().isoformat()
        )
        self.edges[edge_id] = edge
        self._save()
    
    def add_decision_trace(self, trace):
        """Add a decision trace to the graph."""
        from dropsim_decision_traces import DecisionTrace
        
        # Add decision node
        decision_node_id = f"decision_{trace.decision_id}"
        self.add_node(
            decision_node_id,
            "decision",
            {
                'decision_id': trace.decision_id,
                'actor_type': trace.actor_type,
                'chosen_action': trace.chosen_action,
                'rationale': trace.rationale,
                'confidence': trace.confidence
            }
        )
        
        # Add state node (context snapshot)
        state_node_id = f"state_{trace.decision_id}"
        self.add_node(
            state_node_id,
            "state",
            trace.context_snapshot
        )
        
        # Add edge: decision was influenced by state
        self.add_edge(
            state_node_id,
            decision_node_id,
            "was_influenced_by",
            {'timestamp': trace.timestamp}
        )
        
        # Add edges to precedent decisions
        for precedent_id in trace.precedent_ids:
            precedent_node_id = f"decision_{precedent_id}"
            if precedent_node_id in self.nodes:
                self.add_edge(
                    precedent_node_id,
                    decision_node_id,
                    "was_justified_by",
                    {'precedent': True}
                )
        
        # Add entity nodes if present
        if 'step_id' in trace.context_snapshot:
            entity_node_id = f"entity_step_{trace.context_snapshot['step_id']}"
            self.add_node(
                entity_node_id,
                "entity",
                {
                    'entity_type': 'step',
                    'step_id': trace.context_snapshot['step_id']
                }
            )
            self.add_edge(
                entity_node_id,
                decision_node_id,
                "led_to",
                {}
            )
    
    def get_decisions_influenced_by(self, node_id: str) -> List[str]:
        """Get all decisions influenced by a given node."""
        decisions = []
        for edge in self.edges.values():
            if edge.from_node == node_id and edge.edge_type == "was_influenced_by":
                decisions.append(edge.to_node)
        return decisions
    
    def get_precedents_for(self, decision_id: str) -> List[str]:
        """Get precedent decisions for a given decision."""
        decision_node_id = f"decision_{decision_id}"
        precedents = []
        for edge in self.edges.values():
            if edge.to_node == decision_node_id and edge.edge_type == "was_justified_by":
                precedents.append(edge.from_node.replace("decision_", ""))
        return precedents
    
    def get_graph_delta(self, since_timestamp: str) -> Dict:
        """Get changes to the graph since a timestamp."""
        new_nodes = [
            n.to_dict() for n in self.nodes.values()
            if n.timestamp > since_timestamp
        ]
        new_edges = [
            e.to_dict() for e in self.edges.values()
            if e.timestamp > since_timestamp
        ]
        
        return {
            'nodes': new_nodes,
            'edges': new_edges,
            'since': since_timestamp
        }
    
    def query_similar_decisions(
        self,
        context_snapshot: Dict,
        action_type: str
    ) -> List[Dict]:
        """
        Query: Show me all past decisions similar to this one.
        
        Returns decisions with their outcomes.
        """
        similar_decisions = []
        
        # Find decision nodes with similar context
        for node in self.nodes.values():
            if node.node_type == "decision":
                props = node.properties
                
                # Check if similar
                if props.get('chosen_action', {}).get('action_type') == action_type:
                    # Find associated state
                    state_node = None
                    for edge in self.edges.values():
                        if edge.to_node == node.node_id and edge.edge_type == "was_influenced_by":
                            state_node = self.nodes.get(edge.from_node)
                            break
                    
                    if state_node:
                        similar_decisions.append({
                            'decision_id': props.get('decision_id'),
                            'chosen_action': props.get('chosen_action'),
                            'rationale': props.get('rationale'),
                            'confidence': props.get('confidence'),
                            'context': state_node.properties,
                            'timestamp': node.timestamp
                        })
        
        return similar_decisions


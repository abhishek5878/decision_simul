#!/usr/bin/env python3
"""
Visualize Context Graph for Decision Intelligence

Creates a network visualization of the decision graph showing:
- Persona classes as nodes
- Steps as layers/stages
- Decision outcomes (ACCEPT/REJECT) as edge colors
- Dominant factors as edge labels
"""

import json
import sys
import os
from typing import Dict, List, Set
from collections import defaultdict

try:
    import networkx as nx
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import FancyBboxPatch
except ImportError:
    print("Installing required packages...")
    os.system("pip install networkx matplotlib -q")
    import networkx as nx
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import FancyBboxPatch


def load_decision_ledger(ledger_file: str) -> Dict:
    """Load decision ledger JSON file."""
    with open(ledger_file, 'r') as f:
        return json.load(f)


def build_graph_from_ledger(ledger_data: Dict) -> nx.DiGraph:
    """
    Build a directed graph from decision ledger.
    
    Nodes: (step_id, persona_class)
    Edges: Decision outcomes with weights
    """
    G = nx.DiGraph()
    
    boundaries = ledger_data.get('decision_boundaries', [])
    
    # Group boundaries by step to understand flow
    boundaries_by_step = defaultdict(list)
    for boundary in boundaries:
        step_id = boundary['step_id']
        step_index = boundary['step_index']
        boundaries_by_step[step_index].append(boundary)
    
    # Create nodes and edges
    step_order = sorted(boundaries_by_step.keys())
    
    for step_idx in step_order:
        step_boundaries = boundaries_by_step[step_idx]
        step_id = step_boundaries[0]['step_id']  # Get step_id from first boundary
        
        for boundary in step_boundaries:
            persona_class = boundary['persona_class']
            node_id = f"{step_id}::{persona_class}"
            
            # Add node with attributes
            G.add_node(node_id, 
                      step_id=step_id,
                      step_index=step_idx,
                      persona_class=persona_class,
                      accepted_count=boundary.get('accepted_count', 0),
                      rejected_count=boundary.get('rejected_count', 0),
                      supporting_trace_count=boundary.get('supporting_trace_count', 0))
            
            # Add edges to next step (if persona continues)
            if step_idx < max(step_order):
                next_step_idx = step_idx + 1
                if next_step_idx in boundaries_by_step:
                    # Find if this persona continues to next step
                    next_boundaries = boundaries_by_step[next_step_idx]
                    for next_boundary in next_boundaries:
                        if next_boundary['persona_class'] == persona_class:
                            next_step_id = next_boundary['step_id']
                            next_node_id = f"{next_step_id}::{persona_class}"
                            if G.has_node(next_node_id):
                                # Edge weight based on continuation rate
                                continuation_rate = boundary.get('accepted_count', 0) / max(boundary.get('supporting_trace_count', 1), 1)
                                G.add_edge(node_id, next_node_id,
                                          weight=continuation_rate,
                                          outcome='CONTINUE')
    
    return G, step_order, boundaries_by_step


def create_visualization(ledger_file: str, output_file: str = 'context_graph_visualization.png'):
    """Create and save context graph visualization."""
    
    print(f"Loading ledger: {ledger_file}")
    ledger_data = load_decision_ledger(ledger_file)
    
    print("Building graph...")
    G, step_order, boundaries_by_step = build_graph_from_ledger(ledger_data)
    
    if len(G.nodes()) == 0:
        print("No nodes found in graph. Cannot create visualization.")
        return
    
    print(f"Graph has {len(G.nodes())} nodes and {len(G.edges())} edges")
    
    # Create figure
    fig, ax = plt.subplots(figsize=(20, 12))
    
    # Use hierarchical layout (steps as layers)
    pos = {}
    step_x_positions = {}
    
    # Calculate x positions for each step
    for i, step_idx in enumerate(step_order):
        step_x_positions[step_idx] = i * 3
    
    # Calculate y positions for nodes (group by step, stack by persona)
    for step_idx in step_order:
        step_boundaries = boundaries_by_step[step_idx]
        step_id = step_boundaries[0]['step_id']
        
        nodes_in_step = [f"{step_id}::{b['persona_class']}" for b in step_boundaries]
        nodes_in_step = [n for n in nodes_in_step if G.has_node(n)]
        
        y_spacing = 2.0 / max(len(nodes_in_step), 1)
        y_start = 1.0 - (y_spacing * (len(nodes_in_step) - 1)) / 2
        
        for j, node_id in enumerate(nodes_in_step):
            x = step_x_positions[step_idx]
            y = y_start - (j * y_spacing)
            pos[node_id] = (x, y)
    
    # Draw edges
    edge_colors = []
    edge_widths = []
    for u, v in G.edges():
        weight = G[u][v].get('weight', 0.5)
        edge_colors.append('green' if weight > 0.5 else 'orange' if weight > 0.2 else 'red')
        edge_widths.append(weight * 3)
    
    nx.draw_networkx_edges(G, pos, 
                          edge_color=edge_colors,
                          width=edge_widths,
                          alpha=0.6,
                          arrows=True,
                          arrowsize=20,
                          arrowstyle='->',
                          ax=ax)
    
    # Draw nodes
    node_colors = []
    node_sizes = []
    for node_id in G.nodes():
        node_data = G.nodes[node_id]
        accepted = node_data.get('accepted_count', 0)
        rejected = node_data.get('rejected_count', 0)
        total = node_data.get('supporting_trace_count', 1)
        
        # Color by acceptance rate
        if total > 0:
            acceptance_rate = accepted / total
            if acceptance_rate > 0.7:
                node_colors.append('#2ecc71')  # Green (high acceptance)
            elif acceptance_rate > 0.4:
                node_colors.append('#f39c12')  # Orange (medium)
            else:
                node_colors.append('#e74c3c')  # Red (low acceptance)
        else:
            node_colors.append('#95a5a6')  # Gray
        
        # Size by trace count
        node_sizes.append(node_data.get('supporting_trace_count', 100) / 10)
    
    nx.draw_networkx_nodes(G, pos,
                          node_color=node_colors,
                          node_size=node_sizes,
                          alpha=0.8,
                          ax=ax)
    
    # Draw labels (persona classes only, step info in title)
    labels = {}
    for node_id in G.nodes():
        persona_class = G.nodes[node_id]['persona_class']
        # Simplify persona class name for display
        short_name = persona_class.replace('_', ' ').title()
        # Truncate if too long
        if len(short_name) > 30:
            short_name = short_name[:27] + '...'
        labels[node_id] = short_name
    
    nx.draw_networkx_labels(G, pos, labels,
                           font_size=8,
                           font_weight='bold',
                           ax=ax)
    
    # Add step labels at top
    for step_idx in step_order:
        step_boundaries = boundaries_by_step[step_idx]
        step_id = step_boundaries[0]['step_id']
        x_pos = step_x_positions[step_idx]
        
        # Truncate step name if too long
        step_label = step_id[:40] + '...' if len(step_id) > 40 else step_id
        
        ax.text(x_pos, 1.15, step_label,
               ha='center', va='bottom',
               fontsize=10, fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.7))
    
    # Add legend
    legend_elements = [
        mpatches.Patch(color='#2ecc71', label='High Acceptance (>70%)'),
        mpatches.Patch(color='#f39c12', label='Medium Acceptance (40-70%)'),
        mpatches.Patch(color='#e74c3c', label='Low Acceptance (<40%)'),
        plt.Line2D([0], [0], color='green', linewidth=3, label='High Continuation'),
        plt.Line2D([0], [0], color='orange', linewidth=3, label='Medium Continuation'),
        plt.Line2D([0], [0], color='red', linewidth=3, label='Low Continuation'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=10)
    
    ax.set_title('Credigo Decision Context Graph\nPersona Classes Across Product Steps', 
                fontsize=16, fontweight='bold', pad=20)
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n✓ Visualization saved to: {output_file}")
    
    # Also create a simplified text summary
    print("\nGraph Summary:")
    print(f"  Total nodes: {len(G.nodes())}")
    print(f"  Total edges: {len(G.edges())}")
    print(f"  Steps: {len(step_order)}")
    print(f"  Persona classes: {len(set(G.nodes[n]['persona_class'] for n in G.nodes()))}")


if __name__ == '__main__':
    ledger_file = sys.argv[1] if len(sys.argv) > 1 else 'credigo_ss_decision_ledger.json'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'credigo_context_graph.png'
    
    create_visualization(ledger_file, output_file)


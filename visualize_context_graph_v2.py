#!/usr/bin/env python3
"""
Improved Context Graph Visualization

Creates a clear, easy-to-understand funnel-style visualization showing:
- Steps as horizontal layers (funnel stages)
- Persona classes as colored bars/segments
- Clear labels and readable text
- Simple color coding
"""

import json
import sys
import os
from typing import Dict, List, Set
from collections import defaultdict

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import Rectangle, FancyBboxPatch
    import numpy as np
except ImportError:
    print("Installing required packages...")
    os.system("pip install matplotlib numpy -q")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import Rectangle, FancyBboxPatch
    import numpy as np


def load_decision_ledger(ledger_file: str) -> Dict:
    """Load decision ledger JSON file."""
    with open(ledger_file, 'r') as f:
        return json.load(f)


def create_funnel_visualization(ledger_file: str, output_file: str = 'credigo_context_graph_v2.png'):
    """Create a clear funnel-style visualization."""
    
    print(f"Loading ledger: {ledger_file}")
    ledger_data = load_decision_ledger(ledger_file)
    
    boundaries = ledger_data.get('decision_boundaries', [])
    
    # Group boundaries by step
    boundaries_by_step = defaultdict(list)
    for boundary in boundaries:
        step_index = boundary['step_index']
        boundaries_by_step[step_index].append(boundary)
    
    step_order = sorted(boundaries_by_step.keys())
    
    # Get step names (use first boundary's step_id for each step)
    step_names = {}
    for step_idx in step_order:
        step_names[step_idx] = boundaries_by_step[step_idx][0]['step_id']
    
    print(f"Visualizing {len(step_order)} steps with {len(boundaries)} persona-step combinations")
    
    # Create figure with better sizing
    fig, ax = plt.subplots(figsize=(16, 10))
    
    # Color palette - distinct colors for different persona types
    colors = plt.cm.Set3(np.linspace(0, 1, 20))
    
    # Track all persona classes and assign colors
    all_personas = set()
    for boundary in boundaries:
        all_personas.add(boundary['persona_class'])
    
    persona_colors = {}
    for i, persona in enumerate(sorted(all_personas)):
        persona_colors[persona] = colors[i % len(colors)]
    
    # Funnel parameters
    step_height = 0.12
    step_spacing = 0.15
    left_margin = 0.35
    right_margin = 0.05
    top_margin = 0.05
    bottom_margin = 0.1
    
    # Calculate positions
    y_positions = {}
    y_start = 1.0 - top_margin
    
    for i, step_idx in enumerate(step_order):
        y_pos = y_start - (i * (step_height + step_spacing))
        y_positions[step_idx] = y_pos
    
    # Draw each step as a horizontal bar
    for step_idx in step_order:
        step_boundaries = boundaries_by_step[step_idx]
        step_name = step_names[step_idx]
        y_pos = y_positions[step_idx]
        
        # Calculate total width for this step
        total_traces = sum(b['supporting_trace_count'] for b in step_boundaries)
        max_traces = max((b['supporting_trace_count'] for b in boundaries), default=1)
        
        # Sort by trace count (largest first)
        step_boundaries_sorted = sorted(step_boundaries, 
                                       key=lambda b: b['supporting_trace_count'], 
                                       reverse=True)
        
        # Draw segments for each persona class
        x_start = left_margin
        width_scale = (1.0 - left_margin - right_margin) / max_traces
        
        for boundary in step_boundaries_sorted:
            persona_class = boundary['persona_class']
            trace_count = boundary['supporting_trace_count']
            accepted = boundary.get('accepted_count', 0)
            rejected = boundary.get('rejected_count', 0)
            total = boundary.get('supporting_trace_count', 1)
            
            # Width proportional to trace count
            width = trace_count * width_scale
            
            # Color based on acceptance rate
            if total > 0:
                acceptance_rate = accepted / total
                if acceptance_rate > 0.7:
                    color = '#2ecc71'  # Green
                    alpha = 0.8
                elif acceptance_rate > 0.4:
                    color = '#f39c12'  # Orange
                    alpha = 0.7
                else:
                    color = '#e74c3c'  # Red
                    alpha = 0.6
            else:
                color = '#95a5a6'
                alpha = 0.5
            
            # Draw rectangle
            rect = Rectangle((x_start, y_pos - step_height/2), width, step_height,
                           facecolor=color, edgecolor='white', linewidth=1.5,
                           alpha=alpha)
            ax.add_patch(rect)
            
            # Add label if segment is wide enough
            if width > 0.02:  # Only label if segment is large enough
                # Simplify persona name
                short_name = persona_class.replace('_', ' ').title()
                if len(short_name) > 25:
                    # Create abbreviation
                    parts = persona_class.split('_')
                    short_name = ''.join(p[0].upper() for p in parts if p)
                
                # Add text in center of segment
                mid_x = x_start + width/2
                ax.text(mid_x, y_pos, short_name,
                       ha='center', va='center',
                       fontsize=8, fontweight='bold',
                       color='white' if acceptance_rate < 0.5 else 'black',
                       bbox=dict(boxstyle='round,pad=0.3', 
                               facecolor='black' if acceptance_rate < 0.5 else 'white',
                               alpha=0.7 if acceptance_rate < 0.5 else 0.5,
                               edgecolor='none'))
                
                # Add count below
                ax.text(mid_x, y_pos - step_height/2 - 0.01, f'{trace_count}',
                       ha='center', va='top',
                       fontsize=7, color='gray')
            
            x_start += width
        
        # Add step label on the left
        step_label = step_name[:50] + '...' if len(step_name) > 50 else step_name
        ax.text(left_margin - 0.02, y_pos, f"Step {step_idx + 1}",
               ha='right', va='center',
               fontsize=10, fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.8))
        
        # Add step name below
        ax.text(left_margin - 0.02, y_pos - step_height/2 - 0.02, step_label,
               ha='right', va='top',
               fontsize=8, color='gray',
               style='italic')
        
        # Add total count on the right
        ax.text(1.0 - right_margin + 0.01, y_pos, f'{total_traces}',
               ha='left', va='center',
               fontsize=9, fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgray', alpha=0.7))
    
    # Add title
    ax.text(0.5, 1.0 - top_margin/2, 
           'Credigo Decision Funnel: Persona Classes Across Steps',
           ha='center', va='center',
           fontsize=16, fontweight='bold',
           bbox=dict(boxstyle='round,pad=0.8', facecolor='white', alpha=0.9, edgecolor='black'))
    
    # Add legend
    legend_elements = [
        mpatches.Patch(color='#2ecc71', label='High Acceptance (70%+)'),
        mpatches.Patch(color='#f39c12', label='Medium Acceptance (40-70%)'),
        mpatches.Patch(color='#e74c3c', label='Low Acceptance (<40%)'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=10, framealpha=0.9)
    
    # Add explanation text
    explanation = "Each bar segment = Persona class | Width = Number of traces | Color = Acceptance rate"
    ax.text(0.5, bottom_margin/2, explanation,
           ha='center', va='center',
           fontsize=9, style='italic', color='gray')
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"\n✓ Improved visualization saved to: {output_file}")
    
    return output_file


if __name__ == '__main__':
    ledger_file = sys.argv[1] if len(sys.argv) > 1 else 'credigo_ss_decision_ledger.json'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'credigo_context_graph_v2.png'
    
    create_funnel_visualization(ledger_file, output_file)


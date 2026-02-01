#!/usr/bin/env python3
"""
Clean, Professional Context Graph Visualization

Creates a clear, easy-to-read visualization optimized for:
- Fast comprehension
- Clean design
- Professional appearance
- Clear data hierarchy
"""

import json
import sys
import os
from typing import Dict, List
from collections import defaultdict

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import Rectangle
    import numpy as np
except ImportError:
    os.system("pip install matplotlib numpy -q")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import Rectangle
    import numpy as np


def load_decision_ledger(ledger_file: str) -> Dict:
    """Load decision ledger JSON file."""
    with open(ledger_file, 'r') as f:
        return json.load(f)


def simplify_persona_name(persona_class: str) -> str:
    """Convert persona class to readable name."""
    parts = persona_class.split('_')
    
    # Map common abbreviations
    mapping = {
        'low': 'Low',
        'medium': 'Med',
        'high': 'High',
        'energy': 'E',
        'risk': 'R',
        'effort': 'Eff'
    }
    
    # Create abbreviation
    abbrev = ''.join(mapping.get(p.lower(), p.capitalize()[0]) for p in parts if p)
    return abbrev


def create_clean_visualization(ledger_file: str, output_file: str = 'credigo_context_graph.png'):
    """Create a clean, professional visualization."""
    
    print(f"Loading ledger: {ledger_file}")
    ledger_data = load_decision_ledger(ledger_file)
    
    boundaries = ledger_data.get('decision_boundaries', [])
    termination_points = ledger_data.get('decision_termination_points', [])
    
    # Group boundaries by step
    boundaries_by_step = defaultdict(list)
    step_names = {}
    
    for boundary in boundaries:
        step_index = boundary['step_index']
        boundaries_by_step[step_index].append(boundary)
    
    for tp in termination_points:
        step_names[tp['step_index']] = tp['step_id']
    
    step_order = sorted(boundaries_by_step.keys())
    
    print(f"Creating visualization for {len(step_order)} steps")
    
    # Create figure with professional styling
    fig = plt.figure(figsize=(18, 12), facecolor='white')
    ax = fig.add_subplot(111)
    
    # Clean color palette
    high_color = '#27AE60'  # Green
    medium_color = '#F39C12'  # Orange
    low_color = '#E74C3C'  # Red
    
    # Layout parameters
    step_height = 1.2
    step_spacing = 1.5
    left_margin = 4.5
    chart_width = 12
    top_start = len(step_order) * (step_height + step_spacing)
    
    # Calculate max traces for scaling
    max_traces = max((b['supporting_trace_count'] for b in boundaries), default=1)
    
    # Draw each step
    for step_idx_pos, step_idx in enumerate(step_order):
        step_boundaries = boundaries_by_step[step_idx]
        step_name = step_names.get(step_idx, f"Step {step_idx}")
        
        # Y position (top to bottom)
        y_center = top_start - (step_idx_pos * (step_height + step_spacing))
        y_bottom = y_center - step_height / 2
        y_top = y_center + step_height / 2
        
        # Sort by trace count
        step_boundaries_sorted = sorted(step_boundaries, 
                                       key=lambda b: b['supporting_trace_count'], 
                                       reverse=True)
        
        # Draw step background
        bg_rect = Rectangle((0, y_bottom), left_margin + chart_width, step_height,
                          facecolor='#F8F9FA', edgecolor='#DEE2E6', linewidth=1,
                          zorder=0)
        ax.add_patch(bg_rect)
        
        # Step number and name
        ax.text(0.3, y_center, f"STEP {step_idx + 1}",
               ha='left', va='center',
               fontsize=14, fontweight='bold', color='#495057',
               zorder=2)
        
        # Step name (truncate if too long)
        step_label = step_name if len(step_name) <= 60 else step_name[:57] + '...'
        ax.text(0.3, y_center - 0.4, step_label,
               ha='left', va='center',
               fontsize=10, color='#6C757D', style='italic',
               zorder=2)
        
        # Draw persona segments
        x_start = left_margin
        total_traces_step = sum(b['supporting_trace_count'] for b in step_boundaries_sorted)
        
        for boundary in step_boundaries_sorted:
            trace_count = boundary['supporting_trace_count']
            accepted = boundary.get('accepted_count', 0)
            rejected = boundary.get('rejected_count', 0)
            total = boundary.get('supporting_trace_count', 1)
            
            acceptance_rate = accepted / total if total > 0 else 0
            
            # Calculate width
            width = (trace_count / max_traces) * chart_width
            
            # Choose color
            if acceptance_rate > 0.7:
                color = high_color
                text_color = 'white'
            elif acceptance_rate > 0.4:
                color = medium_color
                text_color = 'white'
            else:
                color = low_color
                text_color = 'white'
            
            # Draw segment
            rect = Rectangle((x_start, y_bottom), width, step_height,
                           facecolor=color, edgecolor='white', linewidth=2,
                           alpha=0.85, zorder=1)
            ax.add_patch(rect)
            
            # Add label if wide enough
            if width > 0.8:  # Only label if segment is reasonably wide
                mid_x = x_start + width / 2
                
                # Persona abbreviation
                persona_abbrev = simplify_persona_name(boundary['persona_class'])
                ax.text(mid_x, y_center + 0.25, persona_abbrev,
                       ha='center', va='center',
                       fontsize=11, fontweight='bold', color=text_color,
                       zorder=3)
                
                # Count and percentage
                count_text = f"{trace_count:,}"
                pct_text = f"{acceptance_rate*100:.0f}%"
                ax.text(mid_x, y_center - 0.25, f"{count_text} ({pct_text})",
                       ha='center', va='center',
                       fontsize=9, color=text_color,
                       zorder=3)
            
            x_start += width
        
        # Total count on the right
        ax.text(left_margin + chart_width + 0.3, y_center, f"{total_traces_step:,}",
               ha='left', va='center',
               fontsize=12, fontweight='bold', color='#495057',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='white', 
                        edgecolor='#DEE2E6', linewidth=1),
               zorder=2)
    
    # Title
    ax.text((left_margin + chart_width) / 2, top_start + 1.5,
           'Credigo Decision Funnel',
           ha='center', va='bottom',
           fontsize=20, fontweight='bold', color='#212529')
    
    ax.text((left_margin + chart_width) / 2, top_start + 0.5,
           'Persona Classes Across Product Steps',
           ha='center', va='bottom',
           fontsize=14, color='#6C757D', style='italic')
    
    # Legend (top right)
    legend_x = left_margin + chart_width - 2.5
    legend_y = top_start + 0.8
    
    legend_items = [
        (high_color, 'High Acceptance (70%+)'),
        (medium_color, 'Medium (40-70%)'),
        (low_color, 'Low (<40%)')
    ]
    
    for i, (color, label) in enumerate(legend_items):
        y_pos = legend_y - i * 0.4
        # Color box
        rect = Rectangle((legend_x, y_pos - 0.15), 0.3, 0.3,
                        facecolor=color, edgecolor='white', linewidth=1.5)
        ax.add_patch(rect)
        # Label
        ax.text(legend_x + 0.4, y_pos, label,
               ha='left', va='center',
               fontsize=10, color='#495057')
    
    # Footer note
    ax.text((left_margin + chart_width) / 2, -1.5,
           'Segment width = Number of traces | Color = Acceptance rate',
           ha='center', va='top',
           fontsize=9, color='#6C757D', style='italic')
    
    # Set limits
    ax.set_xlim(-0.5, left_margin + chart_width + 2)
    ax.set_ylim(-2, top_start + 2.5)
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    print(f"\n✓ Clean visualization saved to: {output_file}")
    
    return output_file


if __name__ == '__main__':
    ledger_file = sys.argv[1] if len(sys.argv) > 1 else 'credigo_ss_decision_ledger.json'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'credigo_context_graph.png'
    
    create_clean_visualization(ledger_file, output_file)


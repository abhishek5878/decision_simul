#!/usr/bin/env python3
"""
Create a clean funnel visualization for the founder summary
"""

import json
import sys
import os

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    import numpy as np
except ImportError:
    os.system("pip install matplotlib numpy -q")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    import numpy as np


def load_decision_ledger(ledger_file: str) -> dict:
    """Load decision ledger JSON file."""
    with open(ledger_file, 'r') as f:
        return json.load(f)


def create_funnel_chart(ledger_file: str, output_file: str = 'output/credigo_funnel_chart.png'):
    """Create a clean funnel visualization."""
    
    print(f"Loading ledger: {ledger_file}")
    ledger_data = load_decision_ledger(ledger_file)
    
    termination_points = ledger_data.get('decision_termination_points', [])
    total_sequences = ledger_data.get('total_sequences', 7000)
    
    # Sort by step index
    termination_points_sorted = sorted(termination_points, key=lambda tp: tp['step_index'])
    
    # Calculate cumulative users at each step
    steps_data = []
    current_users = total_sequences
    
    for tp in termination_points_sorted:
        rejections = tp.get('rejection_decision_count', 0)
        steps_data.append({
            'step_id': tp['step_id'],
            'step_index': tp['step_index'],
            'users_at_step': current_users,
            'rejections': rejections,
            'users_after': current_users - rejections
        })
        current_users -= rejections
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 12), facecolor='white')
    
    # Funnel parameters
    top_width = 8
    bottom_width = 2
    funnel_height = 10
    step_height = funnel_height / len(steps_data)
    
    # Color scheme
    bg_color = '#F8F9FA'
    primary_color = '#2563EB'
    drop_color = '#EF4444'
    text_color = '#1F2937'
    
    # Draw funnel
    y_start = 0.5
    y_pos = y_start + funnel_height
    
    # Key steps to highlight (first 3)
    key_steps = steps_data[:3]
    other_steps = steps_data[3:]
    
    # Draw key steps
    for i, step in enumerate(key_steps):
        users_at = step['users_at_step']
        users_after = step['users_after']
        rejections = step['rejections']
        
        # Calculate widths
        width_top = top_width - (i * (top_width - bottom_width) / len(steps_data))
        width_bottom = top_width - ((i + 1) * (top_width - bottom_width) / len(steps_data))
        
        # Draw step box
        y_bottom = y_pos - step_height
        
        # Background box
        box = FancyBboxPatch((10 - width_top/2, y_bottom), width_top, step_height,
                           boxstyle="round,pad=0.1",
                           facecolor=bg_color, edgecolor='#E5E7EB', linewidth=1.5,
                           zorder=1)
        ax.add_patch(box)
        
        # Users count
        ax.text(10, y_pos - step_height/2, f"{users_at:,}",
               ha='center', va='center',
               fontsize=16, fontweight='bold', color=text_color,
               zorder=2)
        
        # Step label (shortened)
        step_label = step['step_id']
        if len(step_label) > 50:
            step_label = step_label[:47] + '...'
        
        ax.text(10, y_bottom - 0.15, f"Step {step['step_index'] + 1}",
               ha='center', va='top',
               fontsize=10, fontweight='bold', color='#6B7280',
               zorder=2)
        
        ax.text(10, y_bottom - 0.4, step_label,
               ha='center', va='top',
               fontsize=8, color='#9CA3AF', style='italic',
               zorder=2)
        
        # Drop count
        if rejections > 0:
            drop_pct = (rejections / users_at) * 100
            ax.text(10 + width_top/2 + 0.3, y_pos - step_height/2,
                   f"-{rejections:,}\n({drop_pct:.0f}%)",
                   ha='left', va='center',
                   fontsize=11, fontweight='bold', color=drop_color,
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='#FEE2E2', 
                           edgecolor=drop_color, linewidth=1.5),
                   zorder=2)
        
        # Arrow to next step
        if i < len(key_steps) - 1:
            arrow = FancyArrowPatch((10, y_bottom), (10, y_bottom - 0.3),
                                   arrowstyle='->', lw=2, color='#9CA3AF',
                                   zorder=2)
            ax.add_patch(arrow)
        
        y_pos = y_bottom - 0.5
    
    # Draw "Other steps" summary
    if other_steps:
        total_other_drops = sum(s['rejections'] for s in other_steps)
        users_after_key = key_steps[-1]['users_after']
        
        width = bottom_width * 0.8
        y_bottom = y_pos - step_height * 2
        
        # Box
        box = FancyBboxPatch((10 - width/2, y_bottom), width, step_height * 2,
                           boxstyle="round,pad=0.1",
                           facecolor=bg_color, edgecolor='#E5E7EB', linewidth=1.5,
                           zorder=1)
        ax.add_patch(box)
        
        ax.text(10, y_pos - step_height, f"{users_after_key:,}",
               ha='center', va='center',
               fontsize=14, fontweight='bold', color=text_color,
               zorder=2)
        
        ax.text(10, y_pos - step_height * 1.5, f"Steps 4-11",
               ha='center', va='center',
               fontsize=10, fontweight='bold', color='#6B7280',
               zorder=2)
        
        if total_other_drops > 0:
            ax.text(10 + width/2 + 0.3, y_pos - step_height,
                   f"-{total_other_drops:,}",
                   ha='left', va='center',
                   fontsize=10, fontweight='bold', color=drop_color,
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='#FEE2E2', 
                           edgecolor=drop_color, linewidth=1.5),
                   zorder=2)
        
        y_pos = y_bottom - 0.3
    
    # Final completion count
    final_count = steps_data[-1]['users_after']
    completion_pct = (final_count / total_sequences) * 100
    
    width = bottom_width
    y_bottom = y_pos - step_height * 1.5
    
    # Highlight box for completion
    box = FancyBboxPatch((10 - width/2, y_bottom), width, step_height * 1.5,
                       boxstyle="round,pad=0.15",
                       facecolor='#D1FAE5', edgecolor='#10B981', linewidth=2.5,
                       zorder=1)
    ax.add_patch(box)
    
    ax.text(10, y_pos - step_height * 0.75, f"{final_count:,}",
           ha='center', va='center',
           fontsize=18, fontweight='bold', color='#065F46',
           zorder=2)
    
    ax.text(10, y_bottom + 0.2, "COMPLETE",
           ha='center', va='bottom',
           fontsize=12, fontweight='bold', color='#059669',
           zorder=2)
    
    ax.text(10, y_bottom - 0.1, f"{completion_pct:.1f}% of arrivals",
           ha='center', va='top',
           fontsize=10, color='#047857',
           zorder=2)
    
    # Title
    ax.text(10, y_start + funnel_height + 0.5,
           'Credigo User Funnel',
           ha='center', va='bottom',
           fontsize=20, fontweight='bold', color=text_color)
    
    ax.text(10, y_start + funnel_height + 0.2,
           f'{total_sequences:,} users arrive',
           ha='center', va='bottom',
           fontsize=14, color='#6B7280', style='italic')
    
    # Key insight box
    key_insight = "62% of all drop-offs occur in Steps 1-3"
    early_drops = sum(s['rejections'] for s in key_steps)
    total_drops = sum(s['rejections'] for s in steps_data)
    early_pct = (early_drops / total_drops) * 100 if total_drops > 0 else 0
    
    insight_box = FancyBboxPatch((1, y_start + funnel_height - 1), 5.5, 1.2,
                                boxstyle="round,pad=0.4",
                                facecolor='#FEF3C7', edgecolor='#F59E0B', linewidth=2,
                                zorder=3)
    ax.add_patch(insight_box)
    
    ax.text(3.75, y_start + funnel_height - 0.3, "KEY INSIGHT",
           ha='center', va='center',
           fontsize=11, fontweight='bold', color='#92400E',
           zorder=4)
    
    ax.text(3.75, y_start + funnel_height - 0.7, f"{early_pct:.0f}% of drops in first 3 steps",
           ha='center', va='center',
           fontsize=10, color='#78350F',
           zorder=4)
    
    # Set limits
    ax.set_xlim(0, 20)
    ax.set_ylim(y_bottom - 0.5, y_start + funnel_height + 1)
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    print(f"\n✓ Funnel chart saved to: {output_file}")
    
    return output_file


if __name__ == '__main__':
    ledger_file = sys.argv[1] if len(sys.argv) > 1 else 'credigo_ss_decision_ledger.json'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'output/credigo_funnel_chart.png'
    
    create_funnel_chart(ledger_file, output_file)


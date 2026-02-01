"""
Report generation for SHAP explainability analysis.

Generates human-readable markdown reports from SHAP aggregations.
"""

from typing import Dict, List
from collections import defaultdict


def generate_feature_importance_report(
    step_importance: Dict[str, Dict],
    output_file: str = "decision_feature_importance.md"
) -> str:
    """
    Generate feature importance report across all steps.
    
    Args:
        step_importance: Dict mapping step_id to importance dict from aggregate_step_importance
        output_file: Output file path
    
    Returns:
        Markdown string
    """
    lines = []
    
    lines.append("# Decision Feature Importance Analysis")
    lines.append("")
    lines.append("**Generated from:** SHAP value aggregation over decision traces")
    lines.append("**Purpose:** Identify which features drive decisions at each step")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Sort steps by step_index if available, otherwise by step_id
    steps_sorted = sorted(step_importance.items(), key=lambda x: x[0])
    
    for step_id, importance_data in steps_sorted:
        lines.append(f"## Step: {step_id}")
        lines.append("")
        
        total = importance_data.get('total_decisions', 0)
        continue_count = importance_data.get('continue_count', 0)
        drop_count = importance_data.get('drop_count', 0)
        
        lines.append(f"**Total Decisions:** {total} (CONTINUE: {continue_count}, DROP: {drop_count})")
        lines.append("")
        
        feature_rank = importance_data.get('feature_rank', [])
        if feature_rank:
            lines.append("| Feature | Mean Absolute SHAP | Importance Rank |")
            lines.append("|---------|-------------------|-----------------|")
            
            for rank, (feature, importance) in enumerate(feature_rank, 1):
                lines.append(f"| {feature} | {importance:.4f} | {rank} |")
            
            lines.append("")
            
            # Highlight top 3 features
            if len(feature_rank) >= 3:
                lines.append("**Top 3 Features by Importance:**")
                for rank, (feature, importance) in enumerate(feature_rank[:3], 1):
                    lines.append(f"{rank}. {feature} (SHAP: {importance:.4f})")
                lines.append("")
        else:
            lines.append("*No feature importance data available.*")
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    markdown = "\n".join(lines)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(markdown)
    
    return markdown


def generate_step_fragility_report(
    step_importance: Dict[str, Dict],
    drop_trigger_analysis: Dict,
    output_file: str = "step_fragility_shap.md"
) -> str:
    """
    Generate step fragility report focusing on drop triggers.
    
    Args:
        step_importance: Dict mapping step_id to importance dict
        drop_trigger_analysis: Dict from aggregate_drop_trigger_analysis (can be per-step)
        output_file: Output file path
    
    Returns:
        Markdown string
    """
    lines = []
    
    lines.append("# Step Fragility Analysis (SHAP)")
    lines.append("")
    lines.append("**Generated from:** SHAP value analysis of DROP decisions")
    lines.append("**Purpose:** Identify which features cause users to drop at each step")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Analyze drop triggers
    if drop_trigger_analysis:
        top_triggers = drop_trigger_analysis.get('top_drop_triggers', [])
        drop_count = drop_trigger_analysis.get('drop_count', 0)
        
        lines.append("## Overall Drop Trigger Analysis")
        lines.append("")
        lines.append(f"**Total DROP Decisions Analyzed:** {drop_count}")
        lines.append("")
        
        if top_triggers:
            lines.append("### Features Most Strongly Causing Drops")
            lines.append("")
            lines.append("| Feature | Mean Negative SHAP | Impact |")
            lines.append("|---------|-------------------|--------|")
            
            for feature, shap_value in top_triggers[:10]:  # Top 10
                impact_desc = "High" if abs(shap_value) > 0.1 else "Medium" if abs(shap_value) > 0.05 else "Low"
                lines.append(f"| {feature} | {shap_value:.4f} | {impact_desc} |")
            
            lines.append("")
            
            lines.append("**Note:** Negative SHAP values indicate features that push decisions toward DROP.")
            lines.append("")
    
    # Per-step drop analysis
    lines.append("---")
    lines.append("")
    lines.append("## Per-Step Drop Analysis")
    lines.append("")
    
    steps_sorted = sorted(step_importance.items(), key=lambda x: x[0])
    
    for step_id, importance_data in steps_sorted:
        drop_count = importance_data.get('drop_count', 0)
        total = importance_data.get('total_decisions', 0)
        drop_rate = drop_count / total if total > 0 else 0.0
        
        lines.append(f"### {step_id}")
        lines.append("")
        lines.append(f"**Drop Rate:** {drop_rate:.1%} ({drop_count} / {total})")
        lines.append("")
        
        # Features ranked by importance (most important = most likely to cause drops)
        feature_rank = importance_data.get('feature_rank', [])
        if feature_rank:
            lines.append("**Features Ranked by Decision Influence:**")
            lines.append("")
            for rank, (feature, importance) in enumerate(feature_rank[:5], 1):  # Top 5
                lines.append(f"{rank}. {feature} (SHAP: {importance:.4f})")
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    markdown = "\n".join(lines)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(markdown)
    
    return markdown


def generate_persona_sensitivity_report(
    persona_sensitivity: Dict,
    output_file: str = "persona_sensitivity_shap.md"
) -> str:
    """
    Generate persona sensitivity report.
    
    Args:
        persona_sensitivity: Dict from aggregate_persona_sensitivity
        output_file: Output file path
    
    Returns:
        Markdown string
    """
    lines = []
    
    lines.append("# Persona Sensitivity Analysis (SHAP)")
    lines.append("")
    lines.append("**Generated from:** SHAP value comparison across persona classes")
    lines.append("**Purpose:** Identify which features matter for different user types")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    persona_classes = persona_sensitivity.get('persona_classes', {})
    feature_sensitivity_by_class = persona_sensitivity.get('feature_sensitivity_by_class', {})
    
    if not persona_classes:
        lines.append("*No persona class data available.*")
        markdown = "\n".join(lines)
        if output_file:
            with open(output_file, 'w') as f:
                f.write(markdown)
        return markdown
    
    # Per-persona-class analysis
    lines.append("## Feature Importance by Persona Class")
    lines.append("")
    
    for class_name, class_importance in persona_classes.items():
        lines.append(f"### {class_name}")
        lines.append("")
        
        # Sort features by importance
        sorted_features = sorted(class_importance.items(), key=lambda x: x[1], reverse=True)
        
        if sorted_features:
            lines.append("| Feature | Mean Absolute SHAP | Rank |")
            lines.append("|---------|-------------------|------|")
            
            for rank, (feature, importance) in enumerate(sorted_features, 1):
                lines.append(f"| {feature} | {importance:.4f} | {rank} |")
            
            lines.append("")
        else:
            lines.append("*No data available.*")
            lines.append("")
    
    # Cross-feature comparison
    lines.append("---")
    lines.append("")
    lines.append("## Cross-Persona Feature Sensitivity")
    lines.append("")
    lines.append("Comparison of how feature importance varies across persona classes:")
    lines.append("")
    
    # Build comparison table for top features
    all_features = set()
    for class_importance in persona_classes.values():
        all_features.update(class_importance.keys())
    
    # Get top features overall
    feature_total_importance = defaultdict(float)
    for class_importance in persona_classes.values():
        for feature, importance in class_importance.items():
            feature_total_importance[feature] += importance
    
    top_features = sorted(feature_total_importance.items(), key=lambda x: x[1], reverse=True)[:10]
    
    if top_features:
        # Header
        class_names = list(persona_classes.keys())
        header = "| Feature | " + " | ".join(class_names) + " |"
        separator = "|---------|" + "|".join(["---" for _ in class_names]) + "|"
        
        lines.append(header)
        lines.append(separator)
        
        for feature, _ in top_features:
            row = f"| {feature} |"
            for class_name in class_names:
                importance = persona_classes[class_name].get(feature, 0.0)
                row += f" {importance:.4f} |"
            lines.append(row)
        
        lines.append("")
    
    markdown = "\n".join(lines)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(markdown)
    
    return markdown


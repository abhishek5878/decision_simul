"""
aggregator.py - Funnel Analysis, Segmentation & Insights for Credigo.club

This module aggregates journey simulation results and provides:
1. Funnel Table - % reaching each step + average intent per step
2. Segment Clustering - 8-12 audience segments with rule-based clustering
3. Per-Segment Metrics - Funnel metrics, top refusals, winner/loser flags
4. Happy Flow Beacon - Top 5% ideal journeys showcased
5. Diverse Vivid Reactions - 20 sample quotes across segments
6. Founder GTM Insights - Actionable recommendations

Output: Markdown tables + text insights for founder decision-making.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from collections import Counter


# ============================================================================
# JOURNEY STEP DEFINITIONS
# ============================================================================

JOURNEY_STEPS = [
    "Landing Page",
    "Quiz Start",
    "Quiz Progression",
    "Quiz Completion",
    "Results Page",
    "Post-Results"
]


# ============================================================================
# SEGMENT DEFINITIONS (8-12 segments)
# ============================================================================

SEGMENTS = [
    {
        "name": "Metro Tech Trailblazer",
        "emoji": "🚀",
        "description": "Young metro professionals in tech, high digital literacy, aspirational",
        "filter": lambda r: (
            r['generation_bucket'] in ['Gen Z', 'Young Millennial'] and
            r['urban_rural'] == 'Metro' and
            r['digital_literacy'] == 'High' and
            r['aspirational_intensity'] in ['High', 'Medium']
        )
    },
    {
        "name": "Urban Young Professional",
        "emoji": "💼",
        "description": "Millennials in urban areas, moderate-high digital, career-focused",
        "filter": lambda r: (
            r['generation_bucket'] in ['Young Millennial', 'Core Millennial'] and
            r['urban_rural'] in ['Metro', 'Urban'] and
            r['digital_literacy'] in ['High', 'Medium']
        )
    },
    {
        "name": "Tier-2 Rising Star",
        "emoji": "🌟",
        "description": "Aspirational youth in semi-urban areas, growth mindset",
        "filter": lambda r: (
            r['generation_bucket'] in ['Gen Z', 'Young Millennial'] and
            r['urban_rural'] in ['Urban', 'Semi-Urban'] and
            r['aspirational_intensity'] in ['High', 'Medium']
        )
    },
    {
        "name": "Gen Z Digital Native",
        "emoji": "📱",
        "description": "Gen Z with high digital comfort but often debt-cautious",
        "filter": lambda r: (
            r['generation_bucket'] == 'Gen Z' and
            r['digital_literacy'] in ['High', 'Medium']
        )
    },
    {
        "name": "South Tech Corridor",
        "emoji": "🏢",
        "description": "Professionals from Bangalore/Hyderabad/Chennai tech hubs",
        "filter": lambda r: (
            r['regional_cluster'] == 'South' and
            r['urban_rural'] in ['Metro', 'Urban'] and
            r['digital_literacy'] in ['High', 'Medium']
        )
    },
    {
        "name": "North Urban Family",
        "emoji": "👨‍👩‍👧",
        "description": "North Indian urban families, moderate digital, family-oriented",
        "filter": lambda r: (
            r['regional_cluster'] in ['North', 'Central'] and
            r['urban_rural'] in ['Metro', 'Urban', 'Semi-Urban'] and
            r['generation_bucket'] in ['Core Millennial', 'Gen X']
        )
    },
    {
        "name": "West Business Pragmatist",
        "emoji": "📈",
        "description": "Western India entrepreneurial mindset, pragmatic about finance",
        "filter": lambda r: (
            r['regional_cluster'] == 'West' and
            r['aspirational_intensity'] in ['High', 'Medium']
        )
    },
    {
        "name": "East Emerging Middle",
        "emoji": "🌅",
        "description": "Eastern India emerging middle class, mixed digital comfort",
        "filter": lambda r: (
            r['regional_cluster'] == 'East' and
            r['urban_rural'] in ['Urban', 'Semi-Urban']
        )
    },
    {
        "name": "Cautious Gen Z",
        "emoji": "🤔",
        "description": "Gen Z who are debt-averse despite digital savvy",
        "filter": lambda r: (
            r['generation_bucket'] == 'Gen Z' and
            r['debt_aversion'] in ['High', 'Medium'] and
            r['trust_orientation'] == 'Conservative'
        )
    },
    {
        "name": "Stability-Seeking Gen X",
        "emoji": "🏦",
        "description": "Gen X with stable jobs, conservative outlook, trust-sensitive",
        "filter": lambda r: (
            r['generation_bucket'] == 'Gen X' and
            r['trust_orientation'] == 'Conservative'
        )
    },
    {
        "name": "Rural UPI Loyalist",
        "emoji": "🌾",
        "description": "Rural population satisfied with UPI, low credit awareness",
        "filter": lambda r: (
            r['urban_rural'] == 'Rural' and
            r['status_quo_sufficiency'] in ['High', 'Medium']
        )
    },
    {
        "name": "Traditional Boomer",
        "emoji": "👴",
        "description": "Older generation with traditional financial habits",
        "filter": lambda r: (
            r['generation_bucket'] == 'Boomer' or
            (r['generation_bucket'] == 'Gen X' and r['digital_literacy'] == 'Low')
        )
    },
    {
        "name": "Unclassified",
        "emoji": "🔄",
        "description": "Personas not fitting clearly into other segments",
        "filter": lambda r: True  # Catch-all
    }
]


# ============================================================================
# SEGMENTATION FUNCTIONS
# ============================================================================

def assign_segment(row: pd.Series) -> Tuple[str, str]:
    """Assign persona to first matching segment."""
    for segment in SEGMENTS:
        try:
            if segment["filter"](row):
                return (segment["name"], segment["emoji"])
        except Exception:
            continue
    return ("Unclassified", "🔄")


def segment_personas(df: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    """Assign segments to all personas."""
    if verbose:
        print("📊 Segmenting personas into audience clusters...")
    
    segments = []
    emojis = []
    
    for _, row in df.iterrows():
        seg_name, seg_emoji = assign_segment(row)
        segments.append(seg_name)
        emojis.append(seg_emoji)
    
    df = df.copy()
    df['segment'] = segments
    df['segment_emoji'] = emojis
    
    if verbose:
        seg_counts = df['segment'].value_counts()
        print(f"✅ Created {len(seg_counts)} segments:")
        for seg, count in seg_counts.items():
            pct = count / len(df) * 100
            emoji = df[df['segment'] == seg]['segment_emoji'].iloc[0]
            print(f"   {emoji} {seg}: {count} ({pct:.1f}%)")
    
    return df


# ============================================================================
# FUNNEL TABLE
# ============================================================================

def compute_funnel_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute funnel metrics per step.
    
    Returns DataFrame with:
    - Step name
    - % reached this step (didn't exit before)
    - Average intent at this step
    - % bounced at this step
    """
    funnel_data = []
    total = len(df)
    
    for step in JOURNEY_STEPS:
        step_key = step.replace(" ", "_").lower()
        intent_col = f'{step_key}_intent'
        
        if intent_col not in df.columns:
            continue
        
        # Get intents (non-zero means they reached this step)
        intents = df[intent_col]
        reached = (intents > 0).sum()
        
        # Calculate bounced at this step
        exit_at_step = (df['funnel_exit_step'] == step).sum()
        
        funnel_data.append({
            "Step": step,
            "Reached": reached,
            "% Reached": round(reached / total * 100, 1),
            "Avg Intent": round(intents[intents > 0].mean(), 1) if reached > 0 else 0,
            "Bounced Here": exit_at_step,
            "% Bounced": round(exit_at_step / total * 100, 1)
        })
    
    return pd.DataFrame(funnel_data)


def compute_step_by_step_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute detailed step-by-step intent changes."""
    metrics = []
    
    prev_col = None
    for step in JOURNEY_STEPS:
        step_key = step.replace(" ", "_").lower()
        intent_col = f'{step_key}_intent'
        
        if intent_col not in df.columns:
            continue
        
        avg_intent = df[intent_col].mean()
        median_intent = df[intent_col].median()
        
        # Calculate drop from previous step
        if prev_col:
            drop = df[prev_col].mean() - avg_intent
            drop_pct = drop / df[prev_col].mean() * 100 if df[prev_col].mean() > 0 else 0
        else:
            drop = 100 - avg_intent  # Initial drop from 100
            drop_pct = drop
        
        metrics.append({
            "Step": step,
            "Avg Intent": round(avg_intent, 1),
            "Median Intent": round(median_intent, 1),
            "Δ from Prev": round(-drop, 1),
            "% Drop": round(drop_pct, 1)
        })
        
        prev_col = intent_col
    
    return pd.DataFrame(metrics)


# ============================================================================
# SEGMENT ANALYSIS
# ============================================================================

def compute_segment_funnel(df: pd.DataFrame) -> pd.DataFrame:
    """Compute funnel metrics per segment."""
    metrics = []
    
    for segment_name in df['segment'].unique():
        seg_df = df[df['segment'] == segment_name]
        emoji = seg_df['segment_emoji'].iloc[0] if len(seg_df) > 0 else ""
        
        # Landing page intent (entry point)
        landing_intent = seg_df['landing_page_intent'].mean() if 'landing_page_intent' in seg_df.columns else 0
        
        # Final intent
        final_intent = seg_df['final_intent'].mean()
        
        # Funnel completion rate
        completed = seg_df['completed_funnel'].sum()
        completion_rate = completed / len(seg_df) * 100
        
        # Top refusal
        refusals = seg_df['dominant_refusal'].value_counts()
        top_refusal = refusals.index[0] if len(refusals) > 0 else "None"
        
        # Conversion score (weighted)
        conv_score = (landing_intent * 0.2 + final_intent * 0.5 + completion_rate * 0.3)
        
        # Winner/Loser status
        if conv_score >= 50:
            status = "🏆 WINNER"
        elif conv_score >= 30:
            status = "⚖️ NEUTRAL"
        else:
            status = "❌ LOSER"
        
        metrics.append({
            "Segment": f"{emoji} {segment_name}",
            "Count": len(seg_df),
            "% Total": round(len(seg_df) / len(df) * 100, 1),
            "Entry Intent": round(landing_intent, 1),
            "Exit Intent": round(final_intent, 1),
            "Completed %": round(completion_rate, 1),
            "Conv Score": round(conv_score, 1),
            "Top Refusal": top_refusal,
            "Status": status
        })
    
    return pd.DataFrame(metrics).sort_values("Conv Score", ascending=False).reset_index(drop=True)


def compute_segment_refusals(df: pd.DataFrame) -> pd.DataFrame:
    """Get refusal breakdown by segment."""
    refusal_data = []
    
    for segment in df['segment'].unique():
        seg_df = df[df['segment'] == segment]
        refusal_counts = seg_df['dominant_refusal'].value_counts()
        
        for refusal, count in refusal_counts.head(3).items():
            refusal_data.append({
                "Segment": segment,
                "Refusal": refusal,
                "Count": count,
                "% of Segment": round(count / len(seg_df) * 100, 1)
            })
    
    return pd.DataFrame(refusal_data)


# ============================================================================
# HAPPY FLOW BEACON
# ============================================================================

def identify_happy_flow(df: pd.DataFrame, top_pct: float = 5.0) -> pd.DataFrame:
    """
    Identify top 5% personas with highest final intent (Happy Flow).
    
    These are the ideal customer journeys - personas who would definitely convert.
    """
    # Sort by final intent descending
    sorted_df = df.sort_values('final_intent', ascending=False)
    
    # Get top X%
    top_n = max(1, int(len(df) * top_pct / 100))
    happy_flow_df = sorted_df.head(top_n).copy()
    
    return happy_flow_df


def format_happy_flow_showcase(df: pd.DataFrame) -> str:
    """
    Format a detailed showcase of the Happy Flow Beacon.
    
    Shows one ideal journey in full detail.
    """
    if len(df) == 0:
        return "No happy flow personas found."
    
    # Pick the best one
    best = df.iloc[0]
    
    output = []
    output.append("=" * 80)
    output.append("🌟 HAPPY FLOW BEACON - THE IDEAL CUSTOMER JOURNEY 🌟")
    output.append("=" * 80)
    output.append("")
    output.append("PERSONA PROFILE:")
    output.append(f"  📍 {best['age']}yo {best['sex']} from {best['state']} ({best.get('district', 'N/A')})")
    output.append(f"  💼 {best.get('occupation', 'N/A')[:50]}...")
    output.append(f"  🎓 {best.get('education_level', 'N/A')}")
    output.append(f"  🗣️  {best.get('first_language', 'N/A')} | English: {best.get('english_proficiency', 'N/A')}")
    output.append("")
    output.append("DERIVED ATTRIBUTES:")
    output.append(f"  📊 {best.get('urban_rural', 'N/A')} | {best.get('regional_cluster', 'N/A')} | {best.get('generation_bucket', 'N/A')}")
    output.append(f"  💻 Digital Literacy: {best.get('digital_literacy', 'N/A')} (Score: {best.get('digital_literacy_score', 'N/A')})")
    output.append(f"  🚀 Aspirational: {best.get('aspirational_intensity', 'N/A')} (Score: {best.get('aspirational_score', 'N/A')})")
    output.append(f"  🔒 Trust: {best.get('trust_orientation', 'N/A')} | Debt Aversion: {best.get('debt_aversion', 'N/A')}")
    output.append(f"  💳 CC Relevance: {best.get('cc_relevance', 'N/A')} (Score: {best.get('cc_relevance_score', 'N/A')})")
    output.append("")
    output.append("JOURNEY WALKTHROUGH:")
    output.append("-" * 60)
    
    for step in JOURNEY_STEPS:
        step_key = step.replace(" ", "_").lower()
        intent = best.get(f'{step_key}_intent', 'N/A')
        emotion = best.get(f'{step_key}_emotion', 'N/A')
        action = best.get(f'{step_key}_action', 'N/A')
        
        output.append(f"  📍 {step}")
        output.append(f"     Intent: {intent} | Emotion: {emotion}")
        output.append(f"     Action: {action}")
    
    output.append("-" * 60)
    output.append("")
    output.append("FINAL OUTCOME:")
    output.append(f"  🎯 Final Intent: {best['final_intent']}")
    output.append(f"  ✅ Completed Funnel: {best['completed_funnel']}")
    output.append(f"  🚫 Dominant Refusal: {best['dominant_refusal']}")
    output.append("")
    output.append("VIVID REACTION:")
    output.append(f"  💭 Think: \"{best.get('vivid_think', 'N/A')}\"")
    output.append(f"  💬 Say: \"{best.get('vivid_say', 'N/A')}\"")
    output.append("")
    output.append("WHY THIS IS THE HAPPY FLOW:")
    output.append("  • High digital literacy enables smooth quiz completion")
    output.append("  • Aspirational mindset values reward optimization")
    output.append("  • Metro/Urban location aligns with CC ecosystem")
    output.append("  • Low debt aversion means credit seen as tool, not trap")
    output.append("  • Privacy claims addressed core concerns upfront")
    output.append("=" * 80)
    
    return "\n".join(output)


# ============================================================================
# DIVERSE REACTIONS SELECTION
# ============================================================================

def get_diverse_reactions(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    """Select N diverse vivid reactions across different segments."""
    reactions = []
    
    # Group by segment and sample
    segments = df['segment'].unique()
    per_segment = max(1, n // len(segments))
    
    for segment in segments:
        seg_df = df[df['segment'] == segment]
        
        # Sample diverse intents within segment
        high_intent = seg_df[seg_df['final_intent'] >= 60].sample(min(1, len(seg_df[seg_df['final_intent'] >= 60])))
        low_intent = seg_df[seg_df['final_intent'] < 30].sample(min(1, len(seg_df[seg_df['final_intent'] < 30])))
        
        for sample_df in [high_intent, low_intent]:
            for _, row in sample_df.iterrows():
                reactions.append({
                    "Segment": f"{row['segment_emoji']} {row['segment']}",
                    "Persona": f"{row['age']}yo {row['sex']}, {row['state']}",
                    "Generation": row.get('generation_bucket', 'N/A'),
                    "Entry Intent": row.get('landing_page_intent', 'N/A'),
                    "Exit Intent": row['final_intent'],
                    "Completed": "✅" if row['completed_funnel'] else "❌",
                    "Refusal": row.get('dominant_refusal', 'None')[:15],
                    "Think": row.get('vivid_think', 'N/A')[:50] + "...",
                    "Say": row.get('vivid_say', 'N/A')[:40] + "..."
                })
                
                if len(reactions) >= n:
                    break
        
        if len(reactions) >= n:
            break
    
    # Fill remaining slots if needed
    if len(reactions) < n:
        remaining = df.sample(min(n - len(reactions), len(df)))
        for _, row in remaining.iterrows():
            reactions.append({
                "Segment": f"{row['segment_emoji']} {row['segment']}",
                "Persona": f"{row['age']}yo {row['sex']}, {row['state']}",
                "Generation": row.get('generation_bucket', 'N/A'),
                "Entry Intent": row.get('landing_page_intent', 'N/A'),
                "Exit Intent": row['final_intent'],
                "Completed": "✅" if row['completed_funnel'] else "❌",
                "Refusal": row.get('dominant_refusal', 'None')[:15],
                "Think": row.get('vivid_think', 'N/A')[:50] + "...",
                "Say": row.get('vivid_say', 'N/A')[:40] + "..."
            })
    
    return pd.DataFrame(reactions[:n])


# ============================================================================
# FOUNDER INSIGHTS
# ============================================================================

def generate_founder_insights(df: pd.DataFrame, segment_metrics: pd.DataFrame, funnel: pd.DataFrame) -> Dict:
    """Generate actionable founder insights from simulation results."""
    insights = {
        "winning_segments": [],
        "losing_segments": [],
        "gtm_recommendations": [],
        "product_redirects": [],
        "messaging_insights": [],
        "regional_insights": [],
        "funnel_insights": []
    }
    
    # === WINNERS AND LOSERS ===
    for _, row in segment_metrics.iterrows():
        segment_name = row['Segment']
        if "WINNER" in row['Status']:
            insights["winning_segments"].append({
                "segment": segment_name,
                "count": row['Count'],
                "pct": row['% Total'],
                "exit_intent": row['Exit Intent'],
                "completion": row['Completed %']
            })
        elif "LOSER" in row['Status']:
            insights["losing_segments"].append({
                "segment": segment_name,
                "count": row['Count'],
                "pct": row['% Total'],
                "exit_intent": row['Exit Intent'],
                "top_refusal": row['Top Refusal']
            })
    
    # === GTM RECOMMENDATIONS ===
    
    # Check winning segment patterns
    winner_names = [s['segment'] for s in insights['winning_segments']]
    
    if any("Tech" in s or "Digital" in s for s in winner_names):
        insights["gtm_recommendations"].append({
            "channel": "LinkedIn + Twitter/X + Tech Podcasts",
            "reason": "Tech professionals show highest conversion - target where they are",
            "priority": "HIGH"
        })
    
    if any("Tier-2" in s or "Rising" in s for s in winner_names):
        insights["gtm_recommendations"].append({
            "channel": "Instagram Reels + YouTube Shorts (Hindi/Regional)",
            "reason": "Tier-2 aspirational youth highly engaged - use vernacular content",
            "priority": "HIGH"
        })
    
    if any("South" in s for s in winner_names):
        insights["gtm_recommendations"].append({
            "channel": "Bangalore/Hyderabad Tech Meetups + Corporate Tie-ups",
            "reason": "South tech corridor shows strong conversion",
            "priority": "MEDIUM"
        })
    
    if any("Gen Z" in s for s in winner_names):
        insights["gtm_recommendations"].append({
            "channel": "Discord Communities + College Fests + Influencer Collabs",
            "reason": "Gen Z digital natives respond to peer influence",
            "priority": "MEDIUM"
        })
    
    # === PRODUCT REDIRECTS (to protect happy flow) ===
    
    # Check funnel drops
    if 'Post-Results' in funnel['Step'].values:
        post_results_drop = funnel[funnel['Step'] == 'Post-Results']['% Bounced'].values[0]
        if post_results_drop > 10:
            insights["product_redirects"].append({
                "issue": "No Direct Apply Button",
                "impact": f"{post_results_drop}% bounce at Post-Results",
                "redirect": "Add one-click apply links to bank pages OR embed pre-fill forms",
                "priority": "CRITICAL"
            })
    
    # Check refusal patterns
    refusal_counts = df['dominant_refusal'].value_counts()
    
    if "Trust Threshold Not Met" in refusal_counts.index and refusal_counts["Trust Threshold Not Met"] > len(df) * 0.15:
        insights["product_redirects"].append({
            "issue": "Trust Deficit",
            "impact": f"{refusal_counts['Trust Threshold Not Met']} personas blocked",
            "redirect": "Add testimonials, security badges, RBI compliance mentions",
            "priority": "HIGH"
        })
    
    if "Status Quo Sufficiency" in refusal_counts.index and refusal_counts["Status Quo Sufficiency"] > len(df) * 0.25:
        insights["product_redirects"].append({
            "issue": "UPI Satisfaction",
            "impact": f"{refusal_counts['Status Quo Sufficiency']} personas blocked",
            "redirect": "Show concrete ₹/year savings calculator on landing page",
            "priority": "HIGH"
        })
    
    if "Responsibility Avoidance" in refusal_counts.index and refusal_counts["Responsibility Avoidance"] > len(df) * 0.15:
        insights["product_redirects"].append({
            "issue": "Debt Fear",
            "impact": f"{refusal_counts['Responsibility Avoidance']} personas blocked",
            "redirect": "Rebrand as 'Smart Rewards Tool' not credit product. Add 'no EMI trap' messaging",
            "priority": "HIGH"
        })
    
    # === MESSAGING INSIGHTS ===
    
    insights["messaging_insights"].append(
        "Privacy-first messaging works for digital-savvy. Lead with 'No PAN, No Data, No Check'"
    )
    insights["messaging_insights"].append(
        "For debt-averse segments, emphasize 'rewards optimization' over 'credit access'"
    )
    insights["messaging_insights"].append(
        "Show tangible value upfront: '₹12,000/year in rewards you're missing'"
    )
    
    # === REGIONAL INSIGHTS ===
    
    regional_intents = df.groupby('regional_cluster')['final_intent'].agg(['mean', 'count'])
    regional_intents = regional_intents.sort_values('mean', ascending=False)
    
    top_regions = regional_intents.head(2)
    bottom_regions = regional_intents.tail(2)
    
    for region, row in top_regions.iterrows():
        insights["regional_insights"].append({
            "region": region,
            "avg_intent": round(row['mean'], 1),
            "count": int(row['count']),
            "status": "STRONG"
        })
    
    for region, row in bottom_regions.iterrows():
        insights["regional_insights"].append({
            "region": region,
            "avg_intent": round(row['mean'], 1),
            "count": int(row['count']),
            "status": "WEAK"
        })
    
    # === FUNNEL INSIGHTS ===
    
    # Biggest drop points (based on bounce rates)
    step_drops = []
    for _, row in funnel.iterrows():
        step_drops.append((row['Step'], row['% Bounced']))
    
    step_drops.sort(key=lambda x: x[1], reverse=True)
    
    for step, bounced in step_drops[:3]:
        if bounced > 5:
            insights["funnel_insights"].append({
                "step": step,
                "bounced": bounced,
                "action": f"Investigate {step} friction - {bounced}% bounce rate"
            })
    
    # === SUMMARY ESTIMATES ===
    
    avg_landing = df['landing_page_intent'].mean() if 'landing_page_intent' in df.columns else 0
    avg_final = df['final_intent'].mean()
    completed_pct = df['completed_funnel'].sum() / len(df) * 100
    high_intent_pct = (df['final_intent'] >= 60).sum() / len(df) * 100
    
    insights["summary"] = {
        "total_simulated": len(df),
        "avg_entry_intent": round(avg_landing, 1),
        "avg_exit_intent": round(avg_final, 1),
        "funnel_completion_rate": round(completed_pct, 1),
        "high_intent_rate": round(high_intent_pct, 1),
        "primary_blocker": refusal_counts.index[0] if len(refusal_counts) > 0 else "None",
        "estimated_conversions_per_1000": int(high_intent_pct * 10)
    }
    
    return insights


# ============================================================================
# MAIN AGGREGATION PIPELINE
# ============================================================================

def aggregate_and_report(df: pd.DataFrame, verbose: bool = True) -> Tuple[pd.DataFrame, Dict]:
    """
    Main entry point: Full aggregation and reporting pipeline.
    
    Args:
        df: DataFrame with journey simulation results
        verbose: Print reports
    
    Returns:
        Tuple of (segmented_df, insights_dict)
    """
    print("\n" + "=" * 80)
    print("📊 CREDIGO.CLUB JOURNEY SIMULATION REPORT")
    print("=" * 80)
    
    # 1. Segment personas
    df = segment_personas(df, verbose=True)
    
    # 2. Funnel Table
    print("\n" + "-" * 80)
    print("📈 FUNNEL ANALYSIS")
    print("-" * 80)
    
    funnel = compute_funnel_table(df)
    print("\nFunnel Progression:")
    print(funnel.to_string(index=False))
    
    step_metrics = compute_step_by_step_metrics(df)
    print("\nStep-by-Step Intent:")
    print(step_metrics.to_string(index=False))
    
    # 3. Overall metrics
    print("\n" + "-" * 80)
    print("📊 OVERALL METRICS")
    print("-" * 80)
    
    total = len(df)
    completed = df['completed_funnel'].sum()
    avg_final = df['final_intent'].mean()
    
    print(f"   Total Personas Simulated: {total:,}")
    print(f"   Completed Full Funnel: {completed} ({completed/total*100:.1f}%)")
    print(f"   Average Final Intent: {avg_final:.1f}")
    print(f"   High Intent (≥60): {(df['final_intent'] >= 60).sum()} ({(df['final_intent'] >= 60).sum()/total*100:.1f}%)")
    print(f"   Warm Intent (40-59): {((df['final_intent'] >= 40) & (df['final_intent'] < 60)).sum()}")
    print(f"   Low Intent (<40): {(df['final_intent'] < 40).sum()}")
    
    refusals = df['dominant_refusal'].value_counts()
    print("\n   Top Refusal Primitives:")
    for refusal, count in refusals.head(5).items():
        pct = count / total * 100
        print(f"     {refusal}: {count} ({pct:.1f}%)")
    
    # 4. Segment Analysis
    print("\n" + "-" * 80)
    print("🎯 SEGMENT PERFORMANCE")
    print("-" * 80)
    
    segment_metrics = compute_segment_funnel(df)
    print(segment_metrics.to_string(index=False))
    
    # 5. Happy Flow Beacon
    print("\n" + "-" * 80)
    happy_flow_df = identify_happy_flow(df, top_pct=5.0)
    print(format_happy_flow_showcase(happy_flow_df))
    
    # 6. Diverse Reactions
    print("\n" + "-" * 80)
    print("💬 DIVERSE VIVID REACTIONS (20 samples)")
    print("-" * 80)
    
    reactions = get_diverse_reactions(df, n=20)
    for i, row in reactions.iterrows():
        print(f"\n[{i+1}] {row['Segment']}")
        print(f"    {row['Persona']} | {row['Generation']}")
        print(f"    Entry: {row['Entry Intent']} → Exit: {row['Exit Intent']} | {row['Completed']}")
        print(f"    💭 {row['Think']}")
        print(f"    💬 \"{row['Say']}\"")
    
    # 7. Founder Insights
    insights = generate_founder_insights(df, segment_metrics, funnel)
    
    print("\n" + "-" * 80)
    print("🚀 FOUNDER INSIGHTS & GTM RECOMMENDATIONS")
    print("-" * 80)
    
    print("\n✅ WINNING SEGMENTS (Double Down):")
    for seg in insights['winning_segments'][:5]:
        print(f"   • {seg['segment']}")
        print(f"     {seg['count']} personas ({seg['pct']}%) | Exit Intent: {seg['exit_intent']} | Completion: {seg['completion']}%")
    
    print("\n❌ LOSING SEGMENTS (Back Off):")
    for seg in insights['losing_segments'][:5]:
        print(f"   • {seg['segment']}")
        print(f"     Blocked by: {seg['top_refusal']}")
    
    print("\n🎯 GTM RECOMMENDATIONS:")
    for rec in insights['gtm_recommendations']:
        print(f"   [{rec['priority']}] {rec['channel']}")
        print(f"         → {rec['reason']}")
    
    print("\n⚠️ PRODUCT REDIRECTS (Protect Happy Flow):")
    for redirect in insights['product_redirects']:
        print(f"   [{redirect['priority']}] {redirect['issue']}")
        print(f"         Impact: {redirect['impact']}")
        print(f"         Fix: {redirect['redirect']}")
    
    print("\n💡 MESSAGING INSIGHTS:")
    for msg in insights['messaging_insights']:
        print(f"   • {msg}")
    
    print("\n🗺️ REGIONAL PERFORMANCE:")
    for region in insights['regional_insights']:
        status_emoji = "🏆" if region['status'] == 'STRONG' else "📉"
        print(f"   {status_emoji} {region['region']}: {region['avg_intent']} avg intent ({region['count']} personas)")
    
    print("\n📊 QUICK ESTIMATES (per 1,000 impressions):")
    summary = insights['summary']
    print(f"   Entry Intent: {summary['avg_entry_intent']}")
    print(f"   Exit Intent: {summary['avg_exit_intent']}")
    print(f"   Funnel Completion: {summary['funnel_completion_rate']}%")
    print(f"   High Intent Rate: {summary['high_intent_rate']}%")
    print(f"   Estimated Conversions: ~{summary['estimated_conversions_per_1000']}")
    print(f"   Primary Blocker: {summary['primary_blocker']}")
    
    print("\n" + "=" * 80)
    
    return df, insights


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("\n🧪 Running aggregator.py test...\n")
    
    try:
        from load_dataset import load_and_sample
        from derive_features import derive_all_features
        from journey_simulator import run_journey_simulation
        
        # Load sample
        sample_df, meta = load_and_sample(n=100, seed=42, verbose=True)
        
        # Derive features
        enriched_df = derive_all_features(sample_df, verbose=True)
        
        # Run journey simulation
        results_df = run_journey_simulation(enriched_df, seed=42, verbose=True)
        
        # Aggregate and report
        final_df, insights = aggregate_and_report(results_df, verbose=True)
        
        print("\n✅ Aggregator test complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

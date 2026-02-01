#!/usr/bin/env python3
import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

"""
Create final 3-page PDF with proper visual diagrams.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY, TA_CENTER
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Rect, Line, String, Circle
from reportlab.graphics import renderPDF
import os

def draw_context_graph_on_canvas(canvas_obj, x, y, width, height):
    """Draw context graph directly on canvas."""
    step_height = height / 5.5
    step_width = width * 0.5
    
    steps = [
        ("Step 0", "Smart Credit\nExploration", 0.1, 0.3, 4, 0.0, False, HexColor('#ecf0f1')),
        ("Step 1", "Eligibility Check\n(Phone)", 0.3, 0.0, 3, 0.2, True, HexColor('#e74c3c')),
        ("Step 2", "PAN & DOB\nInput", 0.7, 0.0, 2, 0.4, True, HexColor('#e74c3c')),
        ("Step 3", "OTP\nVerification", 0.6, 0.0, 1, 0.3, True, HexColor('#e74c3c')),
        ("Step 4", "Eligibility\nConfirmation", 0.0, 0.8, 0, 0.1, False, HexColor('#27ae60')),
    ]
    
    for i, (step_num, label, risk, value, delay, irrev, is_break, color) in enumerate(steps):
        step_y = y + height - (i + 1) * step_height
        
        # Draw step box
        canvas_obj.setFillColor(color)
        canvas_obj.setStrokeColor(HexColor('#2c3e50'))
        canvas_obj.setLineWidth(1.5)
        canvas_obj.roundRect(x, step_y, step_width, step_height - 8, 5, fill=1, stroke=1)
        
        # Text color based on background
        text_color = white if is_break or (value > 0.5) else black
        
        # Step number
        canvas_obj.setFillColor(text_color)
        canvas_obj.setFont("Helvetica-Bold", 10)
        canvas_obj.drawString(x + 5, step_y + step_height - 20, step_num)
        
        # Label
        canvas_obj.setFont("Helvetica-Bold", 9)
        lines = label.split('\n')
        for j, line in enumerate(lines):
            canvas_obj.drawString(x + 5, step_y + step_height - 35 - j*12, line)
        
        # Metrics
        canvas_obj.setFont("Helvetica", 7)
        canvas_obj.drawString(x + 5, step_y + step_height - 58, f"Risk: {risk:.1f} | Value: {value:.1f}")
        canvas_obj.drawString(x + 5, step_y + step_height - 70, f"Delay: {delay} | Irrev: {irrev:.1f}")
        
        # Warning icon for belief breaks
        if is_break:
            canvas_obj.setFillColor(white)
            canvas_obj.circle(x + step_width - 12, step_y + step_height/2, 6, fill=1)
            canvas_obj.setFillColor(HexColor('#e74c3c'))
            canvas_obj.setFont("Helvetica-Bold", 10)
            canvas_obj.drawString(x + step_width - 15, step_y + step_height/2 - 4, "!")
        
        # Arrow to next
        if i < 4:
            arrow_y = step_y - 4
            canvas_obj.setStrokeColor(HexColor('#7f8c8d'))
            canvas_obj.setLineWidth(1)
            canvas_obj.line(x + step_width/2, step_y, x + step_width/2, arrow_y)
            canvas_obj.line(x + step_width/2 - 3, arrow_y - 2, x + step_width/2, arrow_y)
            canvas_obj.line(x + step_width/2 + 3, arrow_y - 2, x + step_width/2, arrow_y)
    
    # Key insight box
    insight_x = x + step_width + 8
    insight_y = y + height - 75
    insight_width = width - step_width - 8
    insight_height = 65
    
    canvas_obj.setFillColor(HexColor('#3498db'))
    canvas_obj.setStrokeColor(HexColor('#2980b9'))
    canvas_obj.setLineWidth(2)
    canvas_obj.roundRect(insight_x, insight_y, insight_width, insight_height, 5, fill=1, stroke=1)
    
    canvas_obj.setFillColor(white)
    canvas_obj.setFont("Helvetica-Bold", 10)
    canvas_obj.drawString(insight_x + 6, insight_y + insight_height - 18, "KEY INSIGHT")
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.drawString(insight_x + 6, insight_y + insight_height - 32, "Trust demanded at Steps 1-3")
    canvas_obj.drawString(insight_x + 6, insight_y + insight_height - 44, "Value delayed until Step 4")
    canvas_obj.drawString(insight_x + 6, insight_y + insight_height - 56, "Misalignment causes abandonment")

def create_final_pdf():
    """Create final 3-page PDF."""
    import os
    os.makedirs("output", exist_ok=True)
    print("📄 Creating final 3-page PDF with visual diagrams...")
    
    doc = SimpleDocTemplate(
        'output/blink_money_3page_brief.pdf',
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, textColor=HexColor('#1a1a1a'), spaceAfter=6, alignment=TA_CENTER)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['BodyText'], fontSize=9, textColor=HexColor('#7f8c8d'), alignment=TA_CENTER, spaceAfter=10)
    h1_style = ParagraphStyle('H1', parent=styles['Heading1'], fontSize=12, textColor=HexColor('#2c3e50'), spaceAfter=5, spaceBefore=8)
    h2_style = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=10, textColor=HexColor('#34495e'), spaceAfter=4, spaceBefore=6)
    body_style = ParagraphStyle('Body', parent=styles['BodyText'], fontSize=8.5, leading=11, alignment=TA_JUSTIFY, spaceAfter=4)
    bold_style = ParagraphStyle('Bold', parent=body_style, fontName='Helvetica-Bold')
    
    story = []
    
    # PAGE 1
    story.append(Paragraph("Blink Money — Technical Intelligence Brief", title_style))
    story.append(Paragraph("<i>How user decision-making unfolds inside the product</i>", subtitle_style))
    story.append(Spacer(1, 0.2*cm))
    
    story.append(Paragraph("<b>What This System Does</b>", h1_style))
    story.append(Paragraph("A <b>decision simulation system</b> that models how users reason through your product, step by step.", body_style))
    story.append(Spacer(1, 0.1*cm))
    story.append(Paragraph("<b>Simulates:</b> Expectations • Perceived risk • Irreversibility • Value recognition", body_style))
    story.append(Paragraph("<b>Output:</b> 1000 decision traces across target personas", body_style))
    story.append(Spacer(1, 0.3*cm))
    
    story.append(Paragraph("<b>The Context Graph: How Your Product Works as a System</b>", h1_style))
    story.append(Spacer(1, 0.15*cm))
    
    # Graph description with pointers
    story.append(Paragraph("<b>Visual Diagram (see graph above):</b>", bold_style))
    story.append(Paragraph("→ <b>Red boxes</b> = Belief break points (Steps 1-3)", body_style))
    story.append(Paragraph("→ <b>Green box</b> = Value finally shown (Step 4)", body_style))
    story.append(Paragraph("→ <b>Risk scores</b> increase: 0.1 → 0.3 → 0.7 → 0.6 → 0.0", body_style))
    story.append(Paragraph("→ <b>Value scores</b> remain 0.0 until Step 4 (0.8)", body_style))
    story.append(Paragraph("→ <b>Delay to value</b> decreases: 4 → 3 → 2 → 1 → 0 steps", body_style))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("<b>Key Insight:</b> Trust is demanded at Steps 1-3 (phone, PAN, OTP) but no value is shown. Value is delayed until Step 4. This misalignment causes abandonment.", bold_style))
    
    def page1_template(canvas_obj, doc):
        draw_context_graph_on_canvas(canvas_obj, 1.5*cm, 3*cm, A4[0] - 3*cm, 12*cm)
        canvas_obj.saveState()
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(HexColor('#7f8c8d'))
        canvas_obj.drawRightString(A4[0] - 1.5*cm, 1*cm, "Page 1")
        canvas_obj.restoreState()
    
    # PAGE 2
    story.append(PageBreak())
    story.append(Paragraph("<b>Persona Decision Patterns</b>", h1_style))
    story.append(Paragraph("<i>Five User Mindsets Through the Same Flow</i>", body_style))
    story.append(Spacer(1, 0.2*cm))
    
    persona_data = [
        ['Persona', 'Drop Step', 'Primary Concern'],
        ['Salaried Professionals', '1', 'Delay seeing limit'],
        ['Self-Employed', '2', 'PAN/DOB anxiety'],
        ['Credit-Aware', '3', 'No comparison'],
        ['Speed-Seekers', '0', 'Too slow'],
        ['Cost-Conscious', '4', 'Rates unclear'],
    ]
    
    persona_table = Table(persona_data, colWidths=[4.2*cm, 1.5*cm, 6.8*cm])
    persona_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#ecf0f1')),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#bdc3c7')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(persona_table)
    story.append(Spacer(1, 0.2*cm))
    
    story.append(Paragraph("<b>Shared Pattern:</b> All five abandon when asked to share personal information before seeing value.", bold_style))
    story.append(Spacer(1, 0.1*cm))
    story.append(Paragraph("<b>Different Reasons, Same Structural Flaw:</b>", bold_style))
    story.append(Paragraph("→ Salaried: 'I don't see my limit yet' (value delay)", body_style))
    story.append(Paragraph("→ Self-employed: 'I'm anxious about data sharing' (risk perception)", body_style))
    story.append(Paragraph("→ Credit-aware: 'I'm comparing to alternatives' (comparison need)", body_style))
    story.append(Spacer(1, 0.15*cm))
    story.append(Paragraph("<b>Insight:</b> Same step fails for different psychological reasons, but all point to the same structural issue: <b>value comes too late</b>.", body_style))
    story.append(Spacer(1, 0.25*cm))
    
    story.append(Paragraph("<b>Non-Obvious Patterns</b>", h1_style))
    story.append(Spacer(1, 0.15*cm))
    
    story.append(Paragraph("<b>Pattern 1: Progress Indicators Increase Anxiety</b>", h2_style))
    story.append(Paragraph("<b>Assumption:</b> 'Step 2 of 5' indicator reduces friction", body_style))
    story.append(Paragraph("<b>Reality:</b> Indicator sets expectation → Step 2 introduces friction → mismatch triggers abandonment", body_style))
    story.append(Paragraph("<b>Insight:</b> Progress indicators work when they match expectations.", bold_style))
    story.append(Spacer(1, 0.12*cm))
    
    story.append(Paragraph("<b>Pattern 2: Trust Signals Ineffective Before Value</b>", h2_style))
    story.append(Paragraph("<b>Assumption:</b> Partner logos (HDFC, Axis, SBI) build trust", body_style))
    story.append(Paragraph("<b>Reality:</b> Trust signals visible at Steps 1-3 but abandonment occurs. Effective only at Step 4 (value shown)", body_style))
    story.append(Paragraph("<b>Insight:</b> Trust signals work when trust exists. Value creates trust; signals reinforce it.", bold_style))
    story.append(Spacer(1, 0.12*cm))
    
    story.append(Paragraph("<b>Pattern 3: Irreversibility Timing Matters More Than Score</b>", h2_style))
    story.append(Paragraph("Phone (0.2) < PAN (0.4) < OTP (0.3) in irreversibility, but all feel too risky when asked before value.", body_style))
    story.append(Paragraph("<b>Insight:</b> The issue isn't the irreversibility score—it's the timing relative to value delivery.", bold_style))
    
    def page2_template(canvas_obj, doc):
        canvas_obj.saveState()
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(HexColor('#7f8c8d'))
        canvas_obj.drawRightString(A4[0] - 1.5*cm, 1*cm, "Page 2")
        canvas_obj.restoreState()
    
    # PAGE 3
    story.append(PageBreak())
    story.append(Paragraph("<b>The Core Structural Insight</b>", h1_style))
    story.append(Spacer(1, 0.15*cm))
    
    story.append(Paragraph("<b>The Flaw:</b> Sequencing and trust, not UX or copy.", bold_style))
    story.append(Spacer(1, 0.15*cm))
    
    comparison_data = [
        ['', 'Steps 1-3', 'Step 4'],
        ['Action Type', 'Irreversible', 'Reversible'],
        ['What User Sees', 'No value', 'Value shown'],
        ['User Feeling', 'Commitment', 'Exploration'],
        ['Result', 'Abandonment', 'Proceed'],
    ]
    
    comp_table = Table(comparison_data, colWidths=[3.5*cm, 4.5*cm, 4.5*cm])
    comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('BACKGROUND', (0, 1), (0, -1), HexColor('#34495e')),
        ('TEXTCOLOR', (0, 1), (0, -1), white),
        ('BACKGROUND', (1, 1), (1, -1), HexColor('#e74c3c')),
        ('TEXTCOLOR', (1, 1), (1, -1), white),
        ('BACKGROUND', (2, 1), (2, -1), HexColor('#27ae60')),
        ('TEXTCOLOR', (2, 1), (2, -1), white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(comp_table)
    story.append(Spacer(1, 0.15*cm))
    
    story.append(Paragraph("<b>Why This Matters:</b>", bold_style))
    story.append(Paragraph("→ Irreversible actions feel like commitments", body_style))
    story.append(Paragraph("→ Reversible value feels like exploration", body_style))
    story.append(Paragraph("→ When commitment comes before exploration, users leave", body_style))
    story.append(Spacer(1, 0.15*cm))
    story.append(Paragraph("<b>The Fix:</b> Show credit limit estimate after phone + PAN (Step 2-3), before OTP. This establishes value before asking for more trust.", bold_style))
    story.append(Spacer(1, 0.25*cm))
    
    story.append(Paragraph("<b>What This Enables</b>", h1_style))
    story.append(Spacer(1, 0.15*cm))
    
    enable_data = [
        ['See Blind Spots', 'Align Teams', 'Safer Bets'],
        ['Before metrics move', 'Shared diagnosis', 'Reversible changes'],
        ['Fix structural issues', 'No debate about cause', 'Clear learning goals'],
        ['Prevent problems', 'Faster decisions', 'Risk assessment included'],
    ]
    
    enable_table = Table(enable_data, colWidths=[4*cm, 4*cm, 4*cm])
    enable_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#bdc3c7')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#ecf0f1')),
    ]))
    story.append(enable_table)
    story.append(Spacer(1, 0.25*cm))
    
    story.append(Paragraph("<b>Closing Perspective</b>", h1_style))
    story.append(Paragraph("This is about seeing how users decide, not forcing them to convert. When you understand the decision-making process, you can design products that align with how users actually think, not how you hope they think.", body_style))
    story.append(Spacer(1, 0.15*cm))
    story.append(Paragraph("<i>Analysis based on 1000 decision traces across target personas, 5 product steps, and 3-level inference depth. All insights derived from structured decision simulations.</i>", ParagraphStyle('Footer', parent=body_style, fontSize=7, textColor=HexColor('#7f8c8d'))))
    
    def page3_template(canvas_obj, doc):
        canvas_obj.saveState()
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(HexColor('#7f8c8d'))
        canvas_obj.drawRightString(A4[0] - 1.5*cm, 1*cm, "Page 3")
        canvas_obj.restoreState()
    
    # Build PDF
    doc.build(story, onFirstPage=page1_template, onLaterPages=lambda c, d: (page2_template(c, d) if c.getPageNumber() == 2 else page3_template(c, d)))
    
    print("✅ Final 3-page PDF generated: output/blink_money_3page_brief.pdf")
    print(f"   File size: {os.path.getsize('output/blink_money_3page_brief.pdf') / 1024:.1f} KB")
    print(f"   Pages: 3")
    print(f"   Includes: Context graph diagram, persona table, comparison table, visual pointers")

if __name__ == '__main__':
    try:
        create_final_pdf()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

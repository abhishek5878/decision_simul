#!/usr/bin/env python3
"""
Create a beautiful 3-page PDF with visual diagrams and pointers.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, KeepTogether
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY, TA_CENTER
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Rect, Line, String, Circle, Group
from reportlab.graphics import renderPDF
from reportlab.lib.utils import ImageReader
import os

class PDFCanvas:
    """Custom canvas for drawing diagrams."""
    def __init__(self, canvas_obj):
        self.canvas = canvas_obj
    
    def draw_context_graph(self, x, y, width, height):
        """Draw the context graph with visual elements."""
        step_height = height / 5.5
        step_width = width * 0.45
        
        steps = [
            ("Step 0", "Smart Credit\nExploration", 0.1, 0.3, 4, 0.0, False),
            ("Step 1", "Eligibility Check\n(Phone Number)", 0.3, 0.0, 3, 0.2, True),
            ("Step 2", "PAN & DOB\nInput", 0.7, 0.0, 2, 0.4, True),
            ("Step 3", "OTP\nVerification", 0.6, 0.0, 1, 0.3, True),
            ("Step 4", "Eligibility\nConfirmation", 0.0, 0.8, 0, 0.1, False),
        ]
        
        for i, (step_num, label, risk, value, delay, irrev, is_break) in enumerate(steps):
            step_y = y + height - (i + 1) * step_height + 5
            
            # Draw step box with color coding
            if is_break:
                fill_color = HexColor('#e74c3c')  # Red for belief break
                text_color = white
            elif value > 0.5:
                fill_color = HexColor('#27ae60')  # Green for value shown
                text_color = white
            else:
                fill_color = HexColor('#ecf0f1')  # Gray for neutral
                text_color = black
            
            self.canvas.setFillColor(fill_color)
            self.canvas.setStrokeColor(HexColor('#2c3e50'))
            self.canvas.setLineWidth(1.5)
            self.canvas.roundRect(x, step_y, step_width, step_height - 8, 5, fill=1, stroke=1)
            
            # Add step number
            self.canvas.setFillColor(text_color)
            self.canvas.setFont("Helvetica-Bold", 10)
            self.canvas.drawString(x + 5, step_y + step_height - 20, step_num)
            
            # Add label
            self.canvas.setFont("Helvetica-Bold", 9)
            lines = label.split('\n')
            for j, line in enumerate(lines):
                self.canvas.drawString(x + 5, step_y + step_height - 35 - j*12, line)
            
            # Add metrics
            self.canvas.setFont("Helvetica", 7)
            self.canvas.drawString(x + 5, step_y + step_height - 60, f"Risk: {risk:.1f} | Value: {value:.1f}")
            self.canvas.drawString(x + 5, step_y + step_height - 72, f"Delay: {delay} steps | Irrev: {irrev:.1f}")
            
            # Mark belief break with warning icon
            if is_break:
                self.canvas.setFillColor(white)
                self.canvas.circle(x + step_width - 12, step_y + step_height/2, 6, fill=1)
                self.canvas.setFillColor(HexColor('#e74c3c'))
                self.canvas.setFont("Helvetica-Bold", 10)
                self.canvas.drawString(x + step_width - 15, step_y + step_height/2 - 4, "!")
            
            # Draw arrow to next step
            if i < 4:
                arrow_y = step_y - 4
                self.canvas.setStrokeColor(HexColor('#7f8c8d'))
                self.canvas.setLineWidth(1)
                self.canvas.line(x + step_width/2, step_y, x + step_width/2, arrow_y)
                # Arrow head
                self.canvas.line(x + step_width/2 - 3, arrow_y - 2, x + step_width/2, arrow_y)
                self.canvas.line(x + step_width/2 + 3, arrow_y - 2, x + step_width/2, arrow_y)
        
        # Add key insight box on the right
        insight_x = x + step_width + 10
        insight_y = y + height - 80
        insight_width = width - step_width - 10
        insight_height = 70
        
        self.canvas.setFillColor(HexColor('#3498db'))
        self.canvas.setStrokeColor(HexColor('#2980b9'))
        self.canvas.setLineWidth(2)
        self.canvas.roundRect(insight_x, insight_y, insight_width, insight_height, 5, fill=1, stroke=1)
        
        self.canvas.setFillColor(white)
        self.canvas.setFont("Helvetica-Bold", 11)
        self.canvas.drawString(insight_x + 8, insight_y + insight_height - 20, "KEY INSIGHT")
        self.canvas.setFont("Helvetica", 9)
        self.canvas.drawString(insight_x + 8, insight_y + insight_height - 35, "Trust demanded at Steps 1-3")
        self.canvas.drawString(insight_x + 8, insight_y + insight_height - 48, "Value delayed until Step 4")
        self.canvas.drawString(insight_x + 8, insight_y + insight_height - 61, "Misalignment causes abandonment")

def add_page_number(canvas_obj, page_num):
    """Add page number."""
    canvas_obj.saveState()
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(HexColor('#7f8c8d'))
    canvas_obj.drawRightString(A4[0] - 1.5*cm, 1*cm, f"Page {page_num}")
    canvas_obj.restoreState()

def create_3page_pdf():
    """Create enhanced 3-page PDF."""
    import os
    os.makedirs("output", exist_ok=True)
    print("📄 Creating enhanced 3-page PDF with visual diagrams...")
    
    doc = SimpleDocTemplate(
        'output/blink_money_3page_brief.pdf',
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=HexColor('#1a1a1a'),
        spaceAfter=6,
        alignment=TA_CENTER
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['BodyText'],
        fontSize=9,
        textColor=HexColor('#7f8c8d'),
        alignment=TA_CENTER,
        spaceAfter=12
    )
    
    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Heading1'],
        fontSize=13,
        textColor=HexColor('#2c3e50'),
        spaceAfter=6,
        spaceBefore=10
    )
    
    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Heading2'],
        fontSize=10,
        textColor=HexColor('#34495e'),
        spaceAfter=4,
        spaceBefore=6
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['BodyText'],
        fontSize=8.5,
        leading=11,
        alignment=TA_JUSTIFY,
        spaceAfter=4
    )
    
    bold_style = ParagraphStyle(
        'Bold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=body_style,
        leftIndent=10,
        bulletIndent=5
    )
    
    # Build story
    story = []
    
    # PAGE 1: Overview and Context Graph
    story.append(Paragraph("Blink Money — Technical Intelligence Brief", title_style))
    story.append(Paragraph("<i>How user decision-making unfolds inside the product</i>", subtitle_style))
    story.append(Spacer(1, 0.3*cm))
    
    story.append(Paragraph("<b>What This System Does</b>", h1_style))
    story.append(Paragraph("This is a <b>decision simulation system</b> that models how users reason through your product, step by step.", body_style))
    story.append(Spacer(1, 0.15*cm))
    story.append(Paragraph("<b>Instead of tracking clicks, we simulate:</b>", bold_style))
    story.append(Paragraph("• What users expect to see", body_style))
    story.append(Paragraph("• How risky each action feels", body_style))
    story.append(Paragraph("• Which actions feel irreversible", body_style))
    story.append(Paragraph("• When value becomes visible", body_style))
    story.append(Paragraph("<b>Output:</b> 13 decision traces across 5 personas, revealing where belief breaks and why.", body_style))
    story.append(Spacer(1, 0.3*cm))
    
    story.append(Paragraph("<b>The Context Graph: How Your Product Works as a System</b>", h1_style))
    story.append(Spacer(1, 0.2*cm))
    
    # Context graph will be drawn on canvas
    # Add placeholder text
    graph_desc = """
    <b>Visual Diagram (see graph above):</b><br/>
    The flow shows 5 steps with risk scores, value scores, and delay to value. 
    Steps 1-3 (phone, PAN, OTP) demand trust but show no value. Step 4 finally shows value (eligibility), 
    but users have already abandoned at earlier steps.
    """
    story.append(Paragraph(graph_desc, body_style))
    story.append(Spacer(1, 0.2*cm))
    
    # Add pointer callouts
    story.append(Paragraph("<b>Key Pointers:</b>", bold_style))
    story.append(Paragraph("→ <b>Red boxes</b> indicate belief break points (Steps 1-3)", body_style))
    story.append(Paragraph("→ <b>Green box</b> shows where value finally appears (Step 4)", body_style))
    story.append(Paragraph("→ <b>Risk scores</b> increase from 0.1 to 0.7 as users progress", body_style))
    story.append(Paragraph("→ <b>Value score</b> remains 0.0 until Step 4 (0.8)", body_style))
    story.append(Paragraph("→ <b>Delay to value</b> decreases: 4 → 3 → 2 → 1 → 0 steps", body_style))
    
    # Custom page template for Page 1 with graph
    def page1_template(canvas_obj, doc):
        pdf_canvas = PDFCanvas(canvas_obj)
        # Draw context graph
        graph_x = 1.5*cm
        graph_y = 3*cm
        graph_width = A4[0] - 3*cm
        graph_height = 12*cm
        pdf_canvas.draw_context_graph(graph_x, graph_y, graph_width, graph_height)
        add_page_number(canvas_obj, 1)
    
    # PAGE 2: Persona Patterns
    story.append(PageBreak())
    story.append(Paragraph("<b>Persona Decision Patterns</b>", h1_style))
    story.append(Paragraph("<i>Five User Mindsets Through the Same Flow</i>", body_style))
    story.append(Spacer(1, 0.2*cm))
    
    # Compact persona table
    persona_data = [
        ['Persona', 'Drop', 'Step', 'Concern'],
        ['Salaried Professionals', '38%', '1', 'Delay seeing limit'],
        ['Self-Employed', '35%', '2', 'PAN/DOB anxiety'],
        ['Credit-Aware', '40%', '3', 'No comparison shown'],
        ['Speed-Seekers', '42%', '0', 'Process too slow'],
        ['Cost-Conscious', '45%', '4', 'Rates unclear'],
    ]
    
    persona_table = Table(persona_data, colWidths=[4.5*cm, 1.5*cm, 1.2*cm, 4.8*cm])
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
    story.append(Spacer(1, 0.25*cm))
    
    story.append(Paragraph("<b>Shared Pattern:</b> All five abandon when asked to share personal information before seeing value.", bold_style))
    story.append(Spacer(1, 0.15*cm))
    story.append(Paragraph("<b>Different Reasons, Same Structural Flaw:</b>", bold_style))
    story.append(Paragraph("→ Salaried: 'I don't see my limit yet' (value delay)", body_style))
    story.append(Paragraph("→ Self-employed: 'I'm anxious about data sharing' (risk perception)", body_style))
    story.append(Paragraph("→ Credit-aware: 'I'm comparing to alternatives' (comparison need)", body_style))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("<b>The Insight:</b> Same step fails for different psychological reasons, but all point to the same structural issue: <b>value comes too late</b>.", body_style))
    story.append(Spacer(1, 0.3*cm))
    
    story.append(Paragraph("<b>Non-Obvious Patterns</b>", h1_style))
    story.append(Spacer(1, 0.15*cm))
    
    story.append(Paragraph("<b>Pattern 1: Progress Indicators Increase Anxiety</b>", h2_style))
    story.append(Paragraph("<b>Assumption:</b> 'Step 2 of 5' indicator reduces friction", body_style))
    story.append(Paragraph("<b>Reality:</b> Indicator sets expectation of smooth progress → Step 2 introduces new friction → mismatch triggers abandonment", body_style))
    story.append(Paragraph("<b>Insight:</b> Progress indicators work when they match expectations. They fail when they don't.", bold_style))
    story.append(Spacer(1, 0.15*cm))
    
    story.append(Paragraph("<b>Pattern 2: Trust Signals Ineffective Before Value</b>", h2_style))
    story.append(Paragraph("<b>Assumption:</b> Partner logos (HDFC, Axis, SBI) build trust", body_style))
    story.append(Paragraph("<b>Reality:</b> Trust signals visible at Steps 1-3 but abandonment still occurs. Effective only at Step 4 (when value shown)", body_style))
    story.append(Paragraph("<b>Insight:</b> Trust signals work when trust exists. They don't create it. Value creates trust; signals reinforce it.", bold_style))
    story.append(Spacer(1, 0.15*cm))
    
    story.append(Paragraph("<b>Pattern 3: Irreversibility Perception Varies</b>", h2_style))
    story.append(Paragraph("Phone (0.2) < PAN (0.4) < OTP (0.3) in irreversibility, but all feel too risky when asked before value.", body_style))
    story.append(Paragraph("<b>Insight:</b> The issue isn't the irreversibility score—it's the timing relative to value delivery.", bold_style))
    
    def page2_template(canvas_obj, doc):
        add_page_number(canvas_obj, 2)
    
    # PAGE 3: Core Insight and What This Enables
    story.append(PageBreak())
    story.append(Paragraph("<b>The Core Structural Insight</b>", h1_style))
    story.append(Spacer(1, 0.2*cm))
    
    story.append(Paragraph("<b>The Flaw:</b> Sequencing and trust, not UX or copy.", bold_style))
    story.append(Spacer(1, 0.15*cm))
    
    # Visual comparison box
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
    story.append(Spacer(1, 0.2*cm))
    
    story.append(Paragraph("<b>Why This Matters:</b>", bold_style))
    story.append(Paragraph("→ Irreversible actions feel like commitments", body_style))
    story.append(Paragraph("→ Reversible value feels like exploration", body_style))
    story.append(Paragraph("→ When commitment comes before exploration, users leave", body_style))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("<b>The Fix:</b> Show credit limit estimate after phone + PAN (Step 2-3), before OTP. This establishes value before asking for more trust.", bold_style))
    story.append(Spacer(1, 0.3*cm))
    
    story.append(Paragraph("<b>What This Enables</b>", h1_style))
    story.append(Spacer(1, 0.15*cm))
    
    # Three-column layout for "What This Enables"
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
    story.append(Spacer(1, 0.3*cm))
    
    story.append(Paragraph("<b>Closing Perspective</b>", h1_style))
    story.append(Paragraph("This is about seeing how users decide, not forcing them to convert. When you understand the decision-making process, you can design products that align with how users actually think, not how you hope they think.", body_style))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("<i>Analysis based on 13 decision traces across 5 personas, 5 product steps, and 3-level inference depth. All insights derived from structured decision simulations.</i>", ParagraphStyle('Footer', parent=body_style, fontSize=7, textColor=HexColor('#7f8c8d'))))
    
    def page3_template(canvas_obj, doc):
        add_page_number(canvas_obj, 3)
    
    # Build PDF with custom page templates
    doc.build(story, onFirstPage=page1_template, onLaterPages=lambda c, d: add_page_number(c, 2 if c.getPageNumber() == 2 else 3))
    
    print("✅ Enhanced 3-page PDF generated: output/blink_money_3page_brief.pdf")
    print(f"   File size: {os.path.getsize('output/blink_money_3page_brief.pdf') / 1024:.1f} KB")
    print(f"   Pages: 3")

if __name__ == '__main__':
    try:
        create_3page_pdf()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

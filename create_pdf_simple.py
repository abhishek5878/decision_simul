#!/usr/bin/env python3
"""
Simple PDF generator using available libraries.
Falls back to HTML export if PDF libraries not available.
"""

import os
import sys

def try_weasyprint():
    """Try generating PDF with WeasyPrint."""
    try:
        from markdown import markdown
        from weasyprint import HTML, CSS
        
        print("📄 Reading markdown file...")
        with open('blink_money_technical_brief_enhanced.md', 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        print("🔄 Converting markdown to HTML...")
        html_content = markdown(md_content, extensions=['extra', 'codehilite', 'tables'])
        
        css = """
        @page {
            size: A4;
            margin: 2cm;
        }
        body {
            font-family: Georgia, serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #333;
        }
        h1 {
            font-size: 24pt;
            color: #1a1a1a;
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 0.3em;
            margin-top: 0;
        }
        h2 {
            font-size: 18pt;
            color: #2c3e50;
            border-bottom: 1px solid #e0e0e0;
            padding-bottom: 0.2em;
            margin-top: 1.5em;
        }
        h3 {
            font-size: 14pt;
            color: #34495e;
            margin-top: 1em;
        }
        code {
            background: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
        pre {
            background: #f8f8f8;
            border: 1px solid #e0e0e0;
            padding: 1em;
            border-radius: 4px;
            overflow-x: auto;
        }
        """
        
        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>{css}</style>
</head>
<body>
{html_content}
</body>
</html>"""
        
        print("📄 Generating PDF...")
        HTML(string=full_html).write_pdf('blink_money_technical_brief.pdf')
        print("✅ PDF generated: blink_money_technical_brief.pdf")
        return True
        
    except ImportError:
        return False
    except Exception as e:
        print(f"❌ Error with WeasyPrint: {e}")
        return False

def create_html_version():
    """Create an HTML version that can be printed to PDF from browser."""
    try:
        from markdown import markdown
        
        print("📄 Creating HTML version...")
        with open('blink_money_technical_brief_enhanced.md', 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        html_content = markdown(md_content, extensions=['extra', 'codehilite', 'tables'])
        
        css = """
        <style>
        @media print {
            @page { size: A4; margin: 2cm; }
        }
        body {
            font-family: Georgia, serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 2em;
        }
        h1 {
            font-size: 24pt;
            color: #1a1a1a;
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 0.3em;
        }
        h2 {
            font-size: 18pt;
            color: #2c3e50;
            border-bottom: 1px solid #e0e0e0;
            padding-bottom: 0.2em;
            margin-top: 1.5em;
        }
        h3 {
            font-size: 14pt;
            color: #34495e;
            margin-top: 1em;
        }
        code {
            background: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
        pre {
            background: #f8f8f8;
            border: 1px solid #e0e0e0;
            padding: 1em;
            border-radius: 4px;
            overflow-x: auto;
        }
        </style>
        """
        
        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Blink Money - Technical Intelligence Brief</title>
    {css}
</head>
<body>
{html_content}
</body>
</html>"""
        
        with open('blink_money_technical_brief.html', 'w', encoding='utf-8') as f:
            f.write(full_html)
        
        print("✅ HTML version created: blink_money_technical_brief.html")
        print("   Open in browser and use 'Print to PDF' for best results")
        return True
        
    except Exception as e:
        print(f"❌ Error creating HTML: {e}")
        return False

def main():
    print("=" * 70)
    print("PDF Generation for Blink Money Technical Brief")
    print("=" * 70)
    print()
    
    # Try WeasyPrint first
    if try_weasyprint():
        return
    
    # Fallback to HTML
    print("\n⚠️  WeasyPrint not available. Creating HTML version instead...")
    if create_html_version():
        print("\n💡 To create PDF:")
        print("   1. Open blink_money_technical_brief.html in your browser")
        print("   2. Press Cmd+P (Mac) or Ctrl+P (Windows/Linux)")
        print("   3. Select 'Save as PDF'")
        print("\n   Or install WeasyPrint: pip3 install weasyprint markdown")
        return
    
    print("\n❌ Could not generate PDF or HTML")
    print("   Please install: pip3 install weasyprint markdown")

if __name__ == '__main__':
    main()

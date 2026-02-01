"""
Test script for executive brief generator.
"""
import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import json
import os
from dropsim_executive_brief import generate_executive_brief

def main():
    print("=" * 80)
    print("EXECUTIVE BRIEF GENERATOR TEST")
    print("=" * 80)
    print()
    
    # Load result
    result_file = "output/credigo_ss_full_pipeline_results.json"
    if not os.path.exists(result_file):
        print(f"❌ Result file not found: {result_file}")
        print("   Please run a full pipeline test first.")
        return
    
    print(f"📊 Loading result from: {result_file}")
    with open(result_file, 'r') as f:
        result = json.load(f)
    
    print("✅ Result loaded")
    print()
    
    # Generate executive brief
    print("📝 Generating executive brief...")
    print()
    
    brief = generate_executive_brief(result)
    
    # Print brief
    print(brief)
    print()
    
    # Save to file
    output_file = "executive_brief_credigo.md"
    with open(output_file, 'w') as f:
        f.write(brief)
    
    print(f"💾 Executive brief saved to: {output_file}")
    print()
    
    # Print summary
    print("=" * 80)
    print("BRIEF SUMMARY")
    print("=" * 80)
    print()
    print("✅ Executive brief generated successfully!")
    print()
    print("The brief includes:")
    print("   • Executive summary with confidence level")
    print("   • Key insight (single most important finding)")
    print("   • Recommended actions (primary + secondary)")
    print("   • Evidence snapshot (3-5 supporting facts)")
    print("   • What we don't know (uncertainties)")
    print()
    print("📄 Ready for leadership review!")

if __name__ == "__main__":
    main()


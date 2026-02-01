#!/usr/bin/env python3
"""
Generate Decision Intelligence Summary from Decision Ledger.

Usage:
    python generate_dis.py <ledger_file> <product_name> [output_file] [--json-sidecar]
"""

import sys
import json
import argparse
from pathlib import Path
from dis_generator import generate_dis, LanguageSafetyError, SchemaValidationError, ConsistencyInvariantError


def main():
    parser = argparse.ArgumentParser(
        description='Generate Decision Intelligence Summary from Decision Ledger'
    )
    parser.add_argument('ledger_file', help='Path to Decision Ledger JSON file')
    parser.add_argument('product_name', help='Product name for the summary')
    parser.add_argument('output_file', nargs='?', help='Output file path (default: <product>_DIS.md)')
    parser.add_argument('--json-sidecar', action='store_true', help='Generate JSON sidecar file')
    parser.add_argument('--version', default='1.0.0', help='Generator version (default: 1.0.0)')
    
    args = parser.parse_args()
    
    # Validate ledger file exists
    if not Path(args.ledger_file).exists():
        print(f"❌ Error: Ledger file not found: {args.ledger_file}", file=sys.stderr)
        return 1
    
    # Determine output file
    if args.output_file:
        output_file = args.output_file
    else:
        # Generate output filename from product name
        safe_name = args.product_name.lower().replace(' ', '_').replace('/', '_')
        output_file = f"{safe_name}_decision_intelligence_summary.md"
    
    try:
        print(f"Generating Decision Intelligence Summary...")
        print(f"  Ledger: {args.ledger_file}")
        print(f"  Product: {args.product_name}")
        print(f"  Output: {output_file}")
        
        # Generate DIS
        markdown_content, metadata_dict = generate_dis(
            ledger_file=args.ledger_file,
            product_name=args.product_name,
            generator_version=args.version
        )
        
        # Write markdown
        with open(output_file, 'w') as f:
            f.write(markdown_content)
        print(f"✓ Generated: {output_file}")
        
        # Write JSON sidecar if requested
        if args.json_sidecar:
            json_file = output_file.replace('.md', '_metadata.json')
            with open(json_file, 'w') as f:
                json.dump(metadata_dict, f, indent=2)
            print(f"✓ Generated JSON sidecar: {json_file}")
        
        print("\n✅ Decision Intelligence Summary generated successfully")
        print("   All validation checks passed")
        return 0
        
    except LanguageSafetyError as e:
        print(f"❌ Language Safety Error: {e}", file=sys.stderr)
        return 1
    except SchemaValidationError as e:
        print(f"❌ Schema Validation Error: {e}", file=sys.stderr)
        return 1
    except ConsistencyInvariantError as e:
        print(f"❌ Consistency Invariant Error: {e}", file=sys.stderr)
        print("\nThis indicates the ledger data has internal inconsistencies.", file=sys.stderr)
        print("The DIS cannot be generated until these are resolved.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())


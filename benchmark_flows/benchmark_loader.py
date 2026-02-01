"""
Benchmark Flow Loader

Loads benchmark onboarding flows from JSON files.
"""

import json
import os
from typing import Dict, List
from pathlib import Path


def get_benchmark_metadata(product_name: str, benchmark_dir: str = "benchmark_flows") -> Dict:
    """
    Get metadata for a benchmark product.
    
    Returns:
        Dictionary with product_name, category, description
    """
    product_name_lower = product_name.lower().replace(" ", "_")
    filepath = os.path.join(benchmark_dir, f"{product_name_lower}.json")
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Benchmark flow not found: {product_name}")
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    return {
        'product_name': data.get('product_name', product_name),
        'category': data.get('category', 'unknown'),
        'description': data.get('description', '')
    }


def load_benchmark_flow(product_name: str, benchmark_dir: str = "benchmark_flows") -> Dict:
    """
    Load a benchmark flow from JSON file.
    
    Args:
        product_name: Product name (e.g., "zerodha", "groww")
        benchmark_dir: Directory containing benchmark JSON files
    
    Returns:
        Dictionary with product steps
    """
    # Normalize product name (lowercase, handle variations)
    product_name_lower = product_name.lower().replace(" ", "_")
    
    # Try exact match first
    filepath = os.path.join(benchmark_dir, f"{product_name_lower}.json")
    
    if not os.path.exists(filepath):
        # Try common variations
        variations = {
            "cred": "cred",
            "groww": "groww",
            "zerodha": "zerodha",
            "paytm": "paytm",
            "phonepe": "phonepe",
            "google_pay": "google_pay",
            "jupiter": "jupiter",
            "fi_money": "fi_money",
            "slice": "slice",
            "onecard": "onecard"
        }
        
        if product_name_lower in variations:
            filepath = os.path.join(benchmark_dir, f"{variations[product_name_lower]}.json")
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Benchmark flow not found: {product_name} (tried {filepath})")
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Extract steps as a dictionary (compatible with existing step format)
    steps = {}
    for step_key, step_data in data.get('steps', {}).items():
        steps[step_key] = step_data
    
    return steps


def list_available_benchmarks(benchmark_dir: str = "benchmark_flows") -> List[str]:
    """
    List all available benchmark products.
    
    Returns:
        List of product names
    """
    if not os.path.exists(benchmark_dir):
        return []
    
    products = []
    for filename in os.listdir(benchmark_dir):
        if filename.endswith('.json') and filename != 'benchmark_schema.md':
            product_name = filename.replace('.json', '')
            products.append(product_name)
    
    return sorted(products)


def get_benchmark_metadata(product_name: str, benchmark_dir: str = "benchmark_flows") -> Dict:
    """
    Get metadata for a benchmark product.
    
    Returns:
        Dictionary with product_name, category, description
    """
    product_name_lower = product_name.lower().replace(" ", "_")
    filepath = os.path.join(benchmark_dir, f"{product_name_lower}.json")
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Benchmark flow not found: {product_name}")
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    return {
        'product_name': data.get('product_name', product_name),
        'category': data.get('category', 'unknown'),
        'description': data.get('description', '')
    }


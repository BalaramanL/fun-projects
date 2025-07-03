#!/usr/bin/env python
"""
Wrapper script to run example scripts with proper Python path setup.

This script ensures that the project root is added to sys.path before running
any example scripts, allowing them to import modules correctly.

Usage:
    python scripts/run_example.py reporting_demo
    python scripts/run_example.py simulation_demo
    python scripts/run_example.py integration_demo
    python scripts/run_example.py run_complete_workflow
"""

import os
import sys
import importlib.util
from pathlib import Path

# Add the project root to sys.path
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

def run_example(example_name):
    """Run an example script by name."""
    example_path = BASE_DIR / "src" / "examples" / f"{example_name}.py"
    
    if not example_path.exists():
        print(f"Error: Example script {example_name}.py not found at {example_path}")
        return 1
    
    print(f"Running example: {example_name}")
    
    # Load the module
    spec = importlib.util.spec_from_file_location(example_name, example_path)
    module = importlib.util.module_from_spec(spec)
    
    # Execute the module
    try:
        spec.loader.exec_module(module)
        print(f"Example {example_name} completed successfully")
        return 0
    except Exception as e:
        print(f"Error running example {example_name}: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_example.py <example_name>")
        print("Available examples: reporting_demo, simulation_demo, integration_demo, run_complete_workflow")
        sys.exit(1)
    
    example_name = sys.argv[1]
    sys.exit(run_example(example_name))

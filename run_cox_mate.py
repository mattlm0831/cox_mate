#!/usr/bin/env python3
"""
Quick runner script for COX Mate processing
Usage: python run_cox_mate.py /path/to/screenshots
"""

import sys
import os
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from main import COXMateProcessor

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_cox_mate.py <screenshot_directory>")
        print("Example: python run_cox_mate.py /Users/username/Downloads/screenshots")
        sys.exit(1)
    
    directory = sys.argv[1]
    
    if not os.path.exists(directory):
        print(f"Error: Directory does not exist: {directory}")
        sys.exit(1)
    
    processor = COXMateProcessor()
    stats = processor.process_screenshots(directory)
    
    if "error" in stats:
        sys.exit(1)
    elif "cancelled" in stats:
        print("Processing cancelled.")
        sys.exit(0)
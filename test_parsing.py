"""
Test script for filename parsing logic
"""

import sys
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from main import COXMateProcessor

def test_filename_parsing():
    """Test the filename parsing logic with example filenames"""
    processor = COXMateProcessor()
    
    test_files = [
        "Chambers of Xeric(125) 2024-02-15_14-30-45.png",
        "Chambers of Xeric Challenge Mode(67) 2024-02-16_09-15-22.png",
        "Chambers of Xeric(200) 2024-02-17_21-45-33.png",
        "Invalid_filename.png",
        "Chambers of Xeric 2024-02-15_14-30-45.png",  # Missing kill count
    ]
    
    print("Testing filename parsing:")
    print("-" * 60)
    
    for filename in test_files:
        result = processor.parse_chambers_filename(filename)
        if result:
            raid_type, kill_count, date_completed = result
            print(f"✅ {filename}")
            print(f"   Type: {raid_type}, Kill Count: {kill_count}, Date: {date_completed}")
        else:
            print(f"❌ {filename}")
            print(f"   Failed to parse")
        print()

if __name__ == "__main__":
    test_filename_parsing()
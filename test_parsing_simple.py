"""
Simple test for filename parsing logic without dependencies
"""

import re
from datetime import datetime
from typing import Optional, Tuple

def parse_chambers_filename(filename: str) -> Optional[Tuple[str, int, datetime]]:
    """
    Parse chambers filename to extract metadata
    
    Format: "Chambers of Xeric(kill_count) YYYY-MM-DD_HH-mm-ss.png"
    Format: "Chambers of Xeric Challenge Mode(kill_count) YYYY-MM-DD_HH-mm-ss.png"
    
    Args:
        filename: The filename to parse
        
    Returns:
        Tuple of (raid_type, kill_count, date_completed) or None if parsing fails
    """
    try:
        # Check if it's challenge mode
        if "Challenge Mode" in filename:
            pattern = r"Chambers of Xeric Challenge Mode\((\d+)\) (\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\.png"
            raid_type = "cm"
        else:
            pattern = r"Chambers of Xeric\((\d+)\) (\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\.png"
            raid_type = "regular"
        
        match = re.match(pattern, filename)
        if not match:
            print(f"Could not parse filename: {filename}")
            return None
        
        kill_count = int(match.group(1))
        date_str = match.group(2)
        
        # Parse the date
        date_completed = datetime.strptime(date_str, "%Y-%m-%d_%H-%M-%S")
        
        return raid_type, kill_count, date_completed
        
    except Exception as e:
        print(f"Error parsing filename {filename}: {e}")
        return None

def test_filename_parsing():
    """Test the filename parsing logic with example filenames"""
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
        result = parse_chambers_filename(filename)
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
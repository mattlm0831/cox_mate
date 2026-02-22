"""
Tests for filename parsing functionality
"""

import pytest
from datetime import datetime

from main import COXMateProcessor


class TestFilenameParser:
    """Test filename parsing logic"""
    
    def test_regular_chambers_parsing(self):
        """Test parsing regular Chambers filenames"""
        processor = COXMateProcessor()
        
        filename = "Chambers of Xeric(125) 2024-02-15_14-30-45.png"
        result = processor.parse_chambers_filename(filename)
        
        assert result is not None
        raid_type, kill_count, date_completed = result
        
        assert raid_type == "regular"
        assert kill_count == 125
        assert date_completed == datetime(2024, 2, 15, 14, 30, 45)
    
    def test_challenge_mode_parsing(self):
        """Test parsing Challenge Mode filenames"""
        processor = COXMateProcessor()
        
        filename = "Chambers of Xeric Challenge Mode(67) 2024-02-16_09-15-22.png"
        result = processor.parse_chambers_filename(filename)
        
        assert result is not None
        raid_type, kill_count, date_completed = result
        
        assert raid_type == "cm"
        assert kill_count == 67
        assert date_completed == datetime(2024, 2, 16, 9, 15, 22)
    
    def test_invalid_filenames(self):
        """Test that invalid filenames return None"""
        processor = COXMateProcessor()
        
        invalid_files = [
            "invalid_file.png",
            "Chambers of Xeric 2024-02-15_14-30-45.png",  # Missing kill count
            "Chambers of Xeric(125) invalid_date.png",     # Invalid date format
            "Chambers of Xeric(abc) 2024-02-15_14-30-45.png",  # Non-numeric kill count
        ]
        
        for filename in invalid_files:
            result = processor.parse_chambers_filename(filename)
            assert result is None, f"Should fail to parse: {filename}"
    
    def test_edge_cases(self):
        """Test edge cases in filename parsing"""
        processor = COXMateProcessor()
        
        # Very high kill count
        result = processor.parse_chambers_filename("Chambers of Xeric(99999) 2024-12-31_23-59-59.png")
        assert result is not None
        assert result[1] == 99999
        
        # Zero kill count (should still parse)
        result = processor.parse_chambers_filename("Chambers of Xeric(0) 2024-01-01_00-00-00.png")
        assert result is not None
        assert result[1] == 0

"""
Tests for file processing functionality
"""

import pytest
from datetime import datetime
from pathlib import Path

from main import COXMateProcessor


class TestFileProcessing:
    """Test file discovery and processing logic"""
    
    def test_get_chambers_files(self, sample_screenshot_files, temp_dir):
        """Test discovery of Chambers files"""
        processor = COXMateProcessor()
        
        files = processor.get_chambers_files(str(temp_dir))
        
        # Should find 3 Chambers files (excluding invalid_file.png)
        assert len(files) == 3
        
        # Check that all found files have Chambers in the name
        for file in files:
            assert "Chambers of Xeric" in Path(file).name
            assert file.endswith('.png')
    
    def test_filter_files_by_date(self, sample_screenshot_files, temp_dir):
        """Test date-based file filtering"""
        processor = COXMateProcessor()
        
        files = processor.get_chambers_files(str(temp_dir))
        
        # Test with no cutoff date (should include all)
        filtered = processor.filter_files_by_date(files, None)
        assert len(filtered) == 3
        
        # Test with cutoff before all files
        cutoff = datetime(2024, 2, 1)
        filtered = processor.filter_files_by_date(files, cutoff)
        assert len(filtered) == 3
        
        # Test with cutoff after some files
        cutoff = datetime(2024, 2, 16, 12, 0, 0)  # Between second and third file
        filtered = processor.filter_files_by_date(files, cutoff)
        assert len(filtered) == 1  # Should exclude the 2024-02-15 and 2024-02-16 files
        
        # Test with cutoff after all files
        cutoff = datetime(2024, 2, 20)
        filtered = processor.filter_files_by_date(files, cutoff) 
        assert len(filtered) == 0
    
    def test_nonexistent_directory(self):
        """Test handling of nonexistent directory"""
        processor = COXMateProcessor()
        
        with pytest.raises(ValueError, match="Directory does not exist"):
            processor.get_chambers_files("/nonexistent/directory")
    
    def test_empty_directory(self, temp_dir):
        """Test handling of empty directory"""
        processor = COXMateProcessor()
        
        files = processor.get_chambers_files(str(temp_dir))
        assert len(files) == 0

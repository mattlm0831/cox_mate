"""
Integration tests for COX Mate
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from cox_mate.cox_tracker import COXDropTracker
from main import COXMateProcessor


class TestIntegration:
    """Integration tests combining multiple components"""
    
    @pytest.mark.integration
    def test_full_processing_workflow_mock(self, test_db, sample_screenshot_files, temp_dir):
        """Test the complete processing workflow with mocked VLM"""
        processor = COXMateProcessor(test_db.db_path)
        
        # Mock the VLM analysis to avoid requiring actual model
        mock_drops = {
            "drops": [
                {"item": "Dragon claws", "quantity": 1, "confidence": "high"}
            ]
        }
        
        mock_points = {
            "points": 28500,
            "confidence": "high"
        }
        
        with patch.object(processor.tracker, 'analyze_drop_screenshot', return_value=mock_drops), \
             patch.object(processor.tracker, 'analyze_points_screenshot', return_value=mock_points):
            
            # Get files to process
            chambers_files = processor.get_chambers_files(str(temp_dir))
            filtered_files = processor.filter_files_by_date(chambers_files, None)
            
            assert len(filtered_files) == 3
            
            # Process first file
            file_path, raid_type, kill_count, date_completed = filtered_files[0]
            
            raid_id = processor.tracker.record_raid(
                screenshot_path=file_path,
                raid_type=raid_type,
                date_completed=date_completed
            )
            
            # Update with correct metadata
            test_db.update_raid(raid_id, completion_count=kill_count)
            
            # Verify the raid was recorded correctly
            raid = test_db.get_raid(raid_id)
            assert raid is not None
            assert raid.raid_type == raid_type
            assert raid.completion_count == kill_count
            assert raid.points == 28500
            assert len(raid.item_list) == 1
            assert raid.item_list[0]['item'] == 'Dragon claws'
    
    @pytest.mark.integration
    def test_database_persistence(self, test_db):
        """Test that database operations persist correctly"""
        # Add multiple raids
        raid1 = test_db.add_raid(
            raid_type="regular",
            points=25000,
            completion_count=100,
            is_purple=False
        )
        
        raid2 = test_db.add_raid(
            raid_type="cm", 
            points=35000,
            completion_count=50,
            is_purple=True,
            item_list=[
                {"item": "Twisted bow", "quantity": 1}
            ]
        )
        
        # Verify both raids exist
        all_raids = test_db.get_all_raids()
        assert len(all_raids) == 2
        
        # Verify stats
        stats = test_db.get_raid_stats()
        assert stats['total_raids'] == 2
        assert stats['regular_raids'] == 1
        assert stats['cm_raids'] == 1
        assert stats['purple_raids'] == 1
        
        # Verify item stats
        item_stats = test_db.get_item_statistics()
        assert 'Twisted bow' in item_stats
        assert item_stats['Twisted bow'] == 1

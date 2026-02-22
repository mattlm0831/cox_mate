"""
Tests for database operations
"""

import pytest
from datetime import datetime

from cox_mate.database import DatabaseManager, COXRaid


class TestDatabaseManager:
    """Test database operations"""
    
    def test_create_database(self, test_db):
        """Test database creation"""
        assert test_db is not None
        # Test that tables exist
        session = test_db.get_session()
        try:
            count = session.query(COXRaid).count()
            assert count == 0
        finally:
            session.close()
    
    def test_add_raid(self, test_db):
        """Test adding a raid"""
        raid = test_db.add_raid(
            raid_type="regular",
            points=25000,
            completion_count=125,
            is_purple=True,
            item_list=[
                {"item": "Twisted bow", "quantity": 1, "confidence": "high"}
            ]
        )
        
        assert raid.id is not None
        assert raid.raid_type == "regular"
        assert raid.points == 25000
        assert raid.completion_count == 125
        assert raid.is_purple is True
        assert len(raid.item_list) == 1
    
    def test_get_raid(self, test_db):
        """Test retrieving a raid"""
        # Add a raid
        raid = test_db.add_raid(
            raid_type="cm",
            points=35000,
            completion_count=67
        )
        
        # Retrieve it
        retrieved = test_db.get_raid(raid.id)
        assert retrieved is not None
        assert retrieved.raid_type == "cm"
        assert retrieved.points == 35000
        assert retrieved.completion_count == 67
    
    def test_get_raid_stats(self, test_db):
        """Test raid statistics"""
        # Add some test raids
        test_db.add_raid(raid_type="regular", points=25000, is_purple=False)
        test_db.add_raid(raid_type="cm", points=35000, is_purple=True)
        test_db.add_raid(raid_type="regular", points=20000, is_purple=False)
        
        stats = test_db.get_raid_stats()
        
        assert stats['total_raids'] == 3
        assert stats['regular_raids'] == 2
        assert stats['cm_raids'] == 1
        assert stats['purple_raids'] == 1
        assert stats['purple_rate'] == 1/3
        assert stats['total_points'] == 80000
        assert stats['average_points'] == round(80000 / 3, 2)
    
    def test_raid_to_dict(self, test_db):
        """Test raid serialization"""
        raid = test_db.add_raid(
            raid_type="regular",
            points=25000,
            item_list=[
                {"item": "Dragon claws", "quantity": 1}
            ]
        )
        
        raid_dict = raid.to_dict()
        
        assert raid_dict['id'] == raid.id
        assert raid_dict['raid_type'] == "regular"
        assert raid_dict['points'] == 25000
        assert len(raid_dict['item_list']) == 1
        assert 'date_completed' in raid_dict
        assert 'date_observed' in raid_dict

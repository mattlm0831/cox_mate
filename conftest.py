"""
Pytest configuration and shared fixtures
"""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime
from PIL import Image

from cox_mate.database import DatabaseManager
from cox_mate.cox_tracker import COXDropTracker


@pytest.fixture
def temp_dir():
    """Provide a temporary directory that gets cleaned up"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_db():
    """Provide a temporary test database"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db = DatabaseManager(db_path)
        yield db
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.fixture
def cox_tracker(test_db):
    """Provide a COXDropTracker with test database"""
    tracker = COXDropTracker(test_db.db_path)
    return tracker


@pytest.fixture
def sample_screenshot_files(temp_dir):
    """Create sample screenshot files with proper naming"""
    files = [
        "Chambers of Xeric(125) 2024-02-15_14-30-45.png",
        "Chambers of Xeric Challenge Mode(67) 2024-02-16_09-15-22.png",
        "Chambers of Xeric(200) 2024-02-17_21-45-33.png",
        "invalid_file.png"
    ]
    
    created_files = []
    for filename in files:
        file_path = temp_dir / filename
        # Create a minimal PNG file
        img = Image.new('RGB', (100, 100), color='red')
        img.save(file_path)
        created_files.append(str(file_path))
    
    return created_files


@pytest.fixture
def validation_data():
    """Sample validation data for DSPy testing"""
    return [
        {
            "image_path": "validation_images/cox_drop_1.png",
            "expected_drops": [
                {"item": "Twisted bow", "quantity": 1, "confidence": "high"}
            ],
            "expected_points": 35000
        },
        {
            "image_path": "validation_images/cox_drop_2.png", 
            "expected_drops": [
                {"item": "Dragon claws", "quantity": 1, "confidence": "high"},
                {"item": "Teak plank", "quantity": 15, "confidence": "high"}
            ],
            "expected_points": 28500
        }
    ]

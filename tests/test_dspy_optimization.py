"""
Tests for DSPy optimization functionality
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

try:
    from optimize_prompt import COXPromptOptimizer, COXDropSignature, COXDropAnalyzer
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False


@pytest.mark.skipif(not DSPY_AVAILABLE, reason="DSPy not available")
class TestDSPyOptimization:
    """Test DSPy prompt optimization"""
    
    def test_validation_data_loading(self, temp_dir):
        """Test loading validation data from JSON"""
        # Create test validation file
        validation_data = [
            {
                "image_path": "test.png",
                "expected_drops": [{"item": "Test item", "quantity": 1}],
                "expected_points": 25000
            }
        ]
        
        validation_file = temp_dir / "test_validation.json"
        with open(validation_file, 'w') as f:
            json.dump(validation_data, f)
        
        optimizer = COXPromptOptimizer(str(validation_file))
        
        assert len(optimizer.validation_data) == 1
        assert optimizer.validation_data[0]["expected_points"] == 25000
    
    def test_default_validation_creation(self, temp_dir):
        """Test creation of default validation file"""
        validation_file = temp_dir / "new_validation.json"
        
        optimizer = COXPromptOptimizer(str(validation_file))
        
        assert validation_file.exists()
        
        with open(validation_file, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data, list)
        assert len(data) > 0
        assert all('image_path' in item for item in data)
        assert all('expected_drops' in item for item in data)
    
    @patch('optimize_prompt.example_vision_language_inference')
    @patch('optimize_prompt.download_qwen25_vl')
    def test_prompt_evaluation(self, mock_download, mock_inference, temp_dir):
        """Test prompt evaluation functionality"""
        # Mock VLM responses
        mock_download.return_value = (MagicMock(), MagicMock())
        mock_inference.return_value = json.dumps({
            "drops": [{"item": "Twisted bow", "quantity": 1, "confidence": "high"}],
            "points": 35000
        })
        
        # Create validation data with matching expected results
        validation_data = [
            {
                "image_path": "validation_images/test.png",
                "expected_drops": [{"item": "Twisted bow", "quantity": 1}],
                "expected_points": 35000
            }
        ]
        
        validation_file = temp_dir / "test_validation.json"
        with open(validation_file, 'w') as f:
            json.dump(validation_data, f)
        
        # Create a dummy image file
        test_image = Path("validation_images/test.png")
        test_image.parent.mkdir(parents=True, exist_ok=True)
        test_image.touch()
        
        try:
            optimizer = COXPromptOptimizer(str(validation_file))
            
            test_prompt = "Test prompt for COX analysis"
            scores = optimizer.evaluate_prompt(test_prompt, validation_data)
            
            assert "accuracy" in scores
            assert "item_f1" in scores
            assert "points_mae" in scores
            assert scores["total_evaluated"] > 0
            
        finally:
            # Cleanup
            if test_image.exists():
                test_image.unlink()
            if test_image.parent.exists():
                test_image.parent.rmdir()
    
    def test_cox_drop_signature(self):
        """Test the COXDropSignature DSPy signature"""
        signature = COXDropSignature
        
        # Check that required fields exist
        assert hasattr(signature, 'image_description')
        assert hasattr(signature, 'system_prompt')
        assert hasattr(signature, 'drops_analysis')
        assert hasattr(signature, 'points_analysis')
    
    def test_cox_drop_analyzer(self):
        """Test the COXDropAnalyzer module"""
        analyzer = COXDropAnalyzer()
        
        # Should have the analyze attribute
        assert hasattr(analyzer, 'analyze')
        assert hasattr(analyzer, 'forward')


class TestItemIconsIntegration:
    """Test item icons functionality"""
    
    def test_icon_manager_creation(self, temp_dir):
        """Test creating an ItemIconManager"""
        from cox_mate.item_icons import ItemIconManager
        
        icons_dir = temp_dir / "test_icons"
        manager = ItemIconManager(str(icons_dir))
        
        assert manager.icons_dir == icons_dir
        assert isinstance(manager.icon_mapping, dict)
    
    def test_icon_mapping_creation(self, temp_dir):
        """Test default icon mapping creation"""
        from cox_mate.item_icons import ItemIconManager
        
        icons_dir = temp_dir / "test_icons"
        manager = ItemIconManager(str(icons_dir))
        
        # Should create default mapping
        assert len(manager.icon_mapping) > 0
        assert "twisted_bow.png" in manager.icon_mapping
        assert manager.icon_mapping["twisted_bow.png"] == "Twisted bow"
        
        # Should save the mapping file
        mapping_file = icons_dir / "icon_mapping.json"
        assert mapping_file.exists()
    
    def test_icon_validation(self, temp_dir):
        """Test icon validation functionality"""
        from cox_mate.item_icons import ItemIconManager
        
        icons_dir = temp_dir / "test_icons"
        icons_dir.mkdir(parents=True, exist_ok=True)
        
        # Create some test icon files
        (icons_dir / "twisted_bow.png").touch()
        (icons_dir / "dragon_claws.png").touch()
        (icons_dir / "unmapped_item.png").touch()
        
        manager = ItemIconManager(str(icons_dir))
        validation_result = manager.validate_icons()
        
        assert "valid_mappings" in validation_result
        assert "missing_files" in validation_result
        assert "unmapped_files" in validation_result
        
        # Should find the valid mappings
        assert "twisted_bow.png" in validation_result["valid_mappings"]
        assert "dragon_claws.png" in validation_result["valid_mappings"]
        
        # Should find unmapped files
        assert "unmapped_item.png" in validation_result["unmapped_files"]

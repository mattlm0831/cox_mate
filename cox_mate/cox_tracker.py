"""
COX Drop Recognition System
Handles image analysis and database storage for Chambers of Xeric drops
"""

import json
from datetime import datetime
from typing import List, Dict, Any
from PIL import Image

from cox_mate.models.qwen_vl_setup import download_qwen25_vl, example_vision_language_inference
from cox_mate.prompts import chambers_score_prompt, create_item_reference_list
from cox_mate.visual_recognition import VisualItemRecognizer
from cox_mate.database import DatabaseManager

class COXDropTracker:
    def __init__(self, db_path: str = "cox_tracker.db", reference_images_dir: str = None):
        self.db = DatabaseManager(db_path)
        self.model = None
        self.processor = None
        self.visual_recognizer = VisualItemRecognizer()
        
        # Load reference images if directory provided
        if reference_images_dir:
            self.visual_recognizer.load_item_references(reference_images_dir)
    

    
    def load_model(self):
        """Load the Qwen VL model (cached after first load)"""
        if self.model is None:
            print("Loading Qwen 2.5 VL model...")
            self.model, self.processor = download_qwen25_vl()
            print("Model loaded and ready!")
    
    def analyze_drop_screenshot(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze a screenshot for COX drops using visual icon recognition
        
        Args:
            image_path: Path to the screenshot
            
        Returns:
            Dict with drop information
        """
        return self.visual_recognizer.analyze_with_references(image_path, use_reference_images=True)
    
    def analyze_points_screenshot(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze a screenshot for COX points
        
        Args:
            image_path: Path to the screenshot
            
        Returns:
            Dict with points information
        """
        self.load_model()
        
        response = example_vision_language_inference(
            self.model, self.processor, image_path, chambers_score_prompt
        )
        
        try:
            points_data = json.loads(response)
            return points_data
        except json.JSONDecodeError:
            print(f"Failed to parse VLM response: {response}")
            return {"points": 0, "confidence": "low", "points_text_found": ""}
    
    def record_raid(self, 
                   screenshot_path: str, 
                   raid_type: str = "regular",
                   analyze_drops: bool = True, 
                   analyze_points: bool = True,
                   date_completed: datetime = None) -> int:
        """
        Record a complete raid with drops and points
        
        Args:
            screenshot_path: Path to the raid screenshot
            raid_type: 'cm' or 'regular'
            analyze_drops: Whether to analyze for drops
            analyze_points: Whether to analyze for points
            date_completed: When the raid was completed (defaults to now)
            
        Returns:
            raid_id of the recorded raid
        """
        # Analyze the screenshot
        drops_data = self.analyze_drop_screenshot(screenshot_path) if analyze_drops else None
        points_data = self.analyze_points_screenshot(screenshot_path) if analyze_points else None
        
        # Process drops data - focus on purple detection
        item_list = []
        is_purple = False
        if drops_data and drops_data.get("drops"):
            from cox_mate.prompts import COX_ITEMS
            
            for drop in drops_data["drops"]:
                item_name = drop["item"]
                
                # Check if VLM identified it as purple (preferred method)
                drop_is_purple = drop.get("is_purple", False)
                
                # Fallback: check our item database
                if not drop_is_purple:
                    drop_is_purple = COX_ITEMS.get(item_name, {}).get("is_purple", False)
                
                item_info = {
                    "item": item_name,
                    "quantity": drop.get("quantity", 1),
                    "confidence": drop.get("confidence", "medium"),
                    "is_purple": drop_is_purple
                }
                item_list.append(item_info)
                
                # Mark raid as purple if any purple drop found
                if drop_is_purple:
                    is_purple = True
        
        # Create raid record
        raid = self.db.add_raid(
            raid_type=raid_type,
            points=points_data.get("points", 0) if points_data else 0,
            completion_count=1,  # Assuming each screenshot represents one completion
            date_completed=date_completed or datetime.now(),
            is_purple=is_purple,
            item_list=item_list
        )
        
        print(f"Recorded {raid_type} raid {raid.id} with {len(item_list)} drops (purple: {is_purple})")
        return raid.id
    
    def get_raid_summary(self, raid_id: int = None) -> Dict[str, Any]:
        """Get summary of raids and drops"""
        if raid_id:
            # Specific raid
            raid = self.db.get_raid(raid_id)
            if raid:
                return raid.to_dict()
            return None
        else:
            # All raids summary
            stats = self.db.get_raid_stats()
            item_stats = self.db.get_item_statistics()
            
            return {
                **stats,
                'top_items': list(item_stats.items())[:10]  # Top 10 most common items
            }

    def get_all_raids(self, raid_type: str = None) -> List[Dict[str, Any]]:
        """Get all raids, optionally filtered by type"""
        raids = self.db.get_all_raids(raid_type)
        return [raid.to_dict() for raid in raids]
    
    def get_purple_drops(self) -> List[Dict[str, Any]]:
        """Get all raids with purple drops"""
        session = self.db.get_session()
        try:
            from cox_mate.database import COXRaid
            purple_raids = session.query(COXRaid).filter(
                COXRaid.is_purple == True
            ).order_by(COXRaid.date_completed.desc()).all()
            return [raid.to_dict() for raid in purple_raids]
        finally:
            session.close()
    
    def update_raid_type(self, raid_id: int, raid_type: str) -> bool:
        """Update the type of a raid (e.g., change regular to cm)"""
        raid = self.db.update_raid(raid_id, raid_type=raid_type)
        return raid is not None

# Usage example
if __name__ == "__main__":
    tracker = COXDropTracker()
    
    # Example usage:
    # raid_id = tracker.record_raid("path/to/screenshot.png")
    # summary = tracker.get_raid_summary()
    # print(f"Total raids: {summary['total_raids']}, Total points: {summary['total_points']}")
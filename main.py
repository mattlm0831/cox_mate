"""
Main driver for COX Mate - Chambers of Xeric screenshot processing
"""

import os
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional
import argparse

from cox_mate.cox_tracker import COXDropTracker
from cox_mate.database import DatabaseManager, COXRaid

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cox_mate.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class COXMateProcessor:
    def __init__(self, db_path: str = "cox_tracker.db"):
        self.tracker = COXDropTracker(db_path)
        self.db = DatabaseManager(db_path)
        
    def parse_chambers_filename(self, filename: str) -> Optional[Tuple[str, int, datetime]]:
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
                logger.warning(f"Could not parse filename: {filename}")
                return None
            
            kill_count = int(match.group(1))
            date_str = match.group(2)
            
            # Parse the date
            date_completed = datetime.strptime(date_str, "%Y-%m-%d_%H-%M-%S")
            
            return raid_type, kill_count, date_completed
            
        except Exception as e:
            logger.error(f"Error parsing filename {filename}: {e}")
            return None
    
    def get_chambers_files(self, directory_path: str) -> List[str]:
        """
        Get all PNG files containing "Chambers" in the directory
        
        Args:
            directory_path: Path to directory containing screenshots
            
        Returns:
            List of absolute file paths
        """
        directory = Path(directory_path)
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Directory does not exist: {directory_path}")
        
        chambers_files = []
        for file_path in directory.iterdir():
            if (file_path.suffix.lower() == '.png' and 
                'Chambers' in file_path.name and
                ('Chambers of Xeric' in file_path.name)):
                chambers_files.append(str(file_path))
        
        logger.info(f"Found {len(chambers_files)} Chambers files in {directory_path}")
        return sorted(chambers_files)
    
    def get_most_recent_processed_date(self) -> Optional[datetime]:
        """
        Get the most recent date_completed from the database
        
        Returns:
            Most recent date_completed or None if no raids exist
        """
        session = self.db.get_session()
        try:
            most_recent = session.query(COXRaid).filter(
                COXRaid.date_completed.isnot(None)
            ).order_by(COXRaid.date_completed.desc()).first()
            
            return most_recent.date_completed if most_recent else None
        finally:
            session.close()
    
    def filter_files_by_date(self, files: List[str], cutoff_date: Optional[datetime]) -> List[Tuple[str, str, int, datetime]]:
        """
        Filter files to only include those after the cutoff date
        
        Args:
            files: List of file paths
            cutoff_date: Only include files after this date (None means include all)
            
        Returns:
            List of tuples (file_path, raid_type, kill_count, date_completed)
        """
        valid_files = []
        
        for file_path in files:
            filename = Path(file_path).name
            parsed = self.parse_chambers_filename(filename)
            
            if parsed is None:
                continue
                
            raid_type, kill_count, date_completed = parsed
            
            # Check if this file is after the cutoff date
            if cutoff_date is None or date_completed > cutoff_date:
                valid_files.append((file_path, raid_type, kill_count, date_completed))
                
        return sorted(valid_files, key=lambda x: x[3])  # Sort by date
    
    def process_screenshots(self, directory_path: str, force: bool = False) -> dict:
        """
        Process all Chambers screenshots in a directory
        
        Args:
            directory_path: Path to directory containing screenshots
            force: Skip date filtering and process all files
            
        Returns:
            Dictionary with processing statistics
        """
        logger.info(f"Starting COX Mate processing for directory: {directory_path}")
        
        # Get all chambers files
        chambers_files = self.get_chambers_files(directory_path)
        if not chambers_files:
            logger.warning("No Chambers files found!")
            return {"error": "No Chambers files found"}
        
        # Get most recent processed date unless forced
        cutoff_date = None if force else self.get_most_recent_processed_date()
        
        if cutoff_date:
            logger.info(f"Most recent processed entry: {cutoff_date}")
        else:
            logger.info("No previous entries found, will process all files")
        
        # Filter files by date
        files_to_process = self.filter_files_by_date(chambers_files, cutoff_date)
        
        if not files_to_process:
            logger.info("No new files to process")
            return {
                "total_files_found": len(chambers_files),
                "files_processed": 0,
                "message": "No new files to process"
            }
        
        # Show confirmation prompt
        print(f"\n{'='*60}")
        print(f"COX MATE PROCESSING SUMMARY")
        print(f"{'='*60}")
        print(f"Directory: {directory_path}")
        print(f"Total Chambers files found: {len(chambers_files)}")
        print(f"Files to process: {len(files_to_process)}")
        if cutoff_date:
            print(f"Most recent processed: {cutoff_date}")
        print(f"Date range: {files_to_process[0][3]} to {files_to_process[-1][3]}")
        print(f"{'='*60}")
        
        if not force:
            response = input("Continue with processing? (y/N): ")
            if response.lower() not in ['y', 'yes']:
                logger.info("Processing cancelled by user")
                return {"cancelled": True}
        
        # Process each file
        stats = {
            "total_files_found": len(chambers_files),
            "files_processed": 0,
            "successful": 0,
            "failed": 0,
            "purple_drops": 0,
            "cm_raids": 0,
            "regular_raids": 0,
            "total_points": 0,
            "errors": []
        }
        
        logger.info(f"Processing {len(files_to_process)} files...")
        
        for i, (file_path, raid_type, kill_count, date_completed) in enumerate(files_to_process, 1):
            try:
                logger.info(f"Processing {i}/{len(files_to_process)}: {Path(file_path).name}")
                
                # Record the raid with the parsed date
                raid_id = self.tracker.record_raid(
                    screenshot_path=file_path,
                    raid_type=raid_type,
                    analyze_drops=True,
                    analyze_points=True
                )
                
                # Update the raid with the correct date_completed and completion_count
                self.db.update_raid(
                    raid_id, 
                    date_completed=date_completed,
                    completion_count=kill_count
                )
                
                # Get raid info for stats
                raid = self.db.get_raid(raid_id)
                if raid:
                    stats["successful"] += 1
                    stats["total_points"] += raid.points
                    
                    if raid.raid_type == "cm":
                        stats["cm_raids"] += 1
                    else:
                        stats["regular_raids"] += 1
                    
                    if raid.is_purple:
                        stats["purple_drops"] += 1
                        logger.info(f"  🟣 Purple drop detected! Items: {raid.item_list}")
                    
                    logger.info(f"  ✅ Recorded raid {raid_id}: {raid.points} points, {len(raid.item_list)} items")
                
                stats["files_processed"] += 1
                
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                stats["failed"] += 1
                stats["errors"].append(f"{Path(file_path).name}: {str(e)}")
        
        # Show final statistics
        self.show_execution_statistics(stats)
        
        return stats
    
    def show_execution_statistics(self, stats: dict):
        """Show detailed execution statistics"""
        print(f"\n{'='*60}")
        print(f"PROCESSING COMPLETE")
        print(f"{'='*60}")
        print(f"Files found: {stats['total_files_found']}")
        print(f"Files processed: {stats['files_processed']}")
        print(f"Successful: {stats['successful']}")
        print(f"Failed: {stats['failed']}")
        
        if stats['successful'] > 0:
            print(f"\n📊 RAID STATISTICS:")
            print(f"  Regular raids: {stats['regular_raids']}")
            print(f"  Challenge Mode raids: {stats['cm_raids']}")
            print(f"  Purple drops: {stats['purple_drops']} ({stats['purple_drops']/stats['successful']*100:.1f}%)")
            print(f"  Total points: {stats['total_points']:,}")
            print(f"  Average points: {stats['total_points']/stats['successful']:.0f}")
        
        if stats['errors']:
            print(f"\n❌ ERRORS:")
            for error in stats['errors']:
                print(f"  {error}")
        
        print(f"{'='*60}")

def main():
    parser = argparse.ArgumentParser(description="COX Mate - Process Chambers of Xeric screenshots")
    parser.add_argument("directory", help="Directory containing screenshot files")
    parser.add_argument("--db", default="cox_tracker.db", help="Database file path")
    parser.add_argument("--force", action="store_true", 
                        help="Process all files, ignoring the most recent processed date")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                        default="INFO", help="Set logging level")
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    try:
        processor = COXMateProcessor(args.db)
        stats = processor.process_screenshots(args.directory, args.force)
        
        if "error" in stats:
            return 1
        elif "cancelled" in stats:
            return 0
        else:
            return 0 if stats["failed"] == 0 else 1
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
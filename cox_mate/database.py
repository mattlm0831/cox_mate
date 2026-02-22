"""
Database models for COX tracker using SQLAlchemy
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.types import TypeDecorator, VARCHAR

Base = declarative_base()

class JSONField(TypeDecorator):
    """Custom SQLAlchemy type for storing JSON data"""
    impl = VARCHAR
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return value
    
    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value

class COXRaid(Base):
    __tablename__ = 'cox_raids'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    raid_type = Column(String(10), nullable=False)  # 'cm' or 'regular'
    completion_count = Column(Integer, default=0)
    date_completed = Column(DateTime, nullable=True)
    date_observed = Column(DateTime, default=datetime.utcnow)
    points = Column(Integer, default=0)
    is_purple = Column(Boolean, default=False)
    item_list = Column(JSONField, default=list)  # JSON array of dropped items
    
    def __repr__(self):
        return f"<COXRaid(id={self.id}, type={self.raid_type}, points={self.points}, purple={self.is_purple})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert raid record to dictionary"""
        return {
            'id': self.id,
            'raid_type': self.raid_type,
            'completion_count': self.completion_count,
            'date_completed': self.date_completed.isoformat() if self.date_completed else None,
            'date_observed': self.date_observed.isoformat() if self.date_observed else None,
            'points': self.points,
            'is_purple': self.is_purple,
            'item_list': self.item_list or []
        }

class DatabaseManager:
    """Manages database connection and operations"""
    
    def __init__(self, db_path: str = "cox_tracker.db"):
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.create_tables()
    
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get a database session"""
        return self.SessionLocal()
    
    def add_raid(self, 
                raid_type: str,
                points: int = 0,
                completion_count: int = 0,
                date_completed: Optional[datetime] = None,
                is_purple: bool = False,
                item_list: List[Dict[str, Any]] = None) -> COXRaid:
        """
        Add a new raid record to the database
        
        Args:
            raid_type: 'cm' or 'regular'
            points: Points earned in the raid
            completion_count: Number of completions 
            date_completed: When the raid was completed
            is_purple: Whether any purple (rare) items dropped
            item_list: List of items that dropped
            
        Returns:
            The created COXRaid object
        """
        session = self.get_session()
        try:
            raid = COXRaid(
                raid_type=raid_type,
                points=points,
                completion_count=completion_count,
                date_completed=date_completed or datetime.utcnow(),
                is_purple=is_purple,
                item_list=item_list or []
            )
            session.add(raid)
            session.commit()
            session.refresh(raid)
            return raid
        finally:
            session.close()
    
    def get_raid(self, raid_id: int) -> Optional[COXRaid]:
        """Get a specific raid by ID"""
        session = self.get_session()
        try:
            return session.query(COXRaid).filter(COXRaid.id == raid_id).first()
        finally:
            session.close()
    
    def get_all_raids(self, raid_type: Optional[str] = None) -> List[COXRaid]:
        """Get all raids, optionally filtered by type"""
        session = self.get_session()
        try:
            query = session.query(COXRaid)
            if raid_type:
                query = query.filter(COXRaid.raid_type == raid_type)
            return query.order_by(COXRaid.date_observed.desc()).all()
        finally:
            session.close()
    
    def get_raid_stats(self) -> Dict[str, Any]:
        """Get comprehensive raid statistics"""
        session = self.get_session()
        try:
            # Total raids
            total_raids = session.query(COXRaid).count()
            cm_raids = session.query(COXRaid).filter(COXRaid.raid_type == 'cm').count()
            regular_raids = session.query(COXRaid).filter(COXRaid.raid_type == 'regular').count()
            
            # Purple drops
            purple_raids = session.query(COXRaid).filter(COXRaid.is_purple == True).count()
            
            # Total points
            total_points = session.query(COXRaid).with_entities(
                COXRaid.points
            ).all()
            total_points_sum = sum(raid.points for raid in total_points if raid.points)
            
            # Average points
            avg_points = total_points_sum / total_raids if total_raids > 0 else 0
            
            return {
                'total_raids': total_raids,
                'cm_raids': cm_raids,
                'regular_raids': regular_raids,
                'purple_raids': purple_raids,
                'purple_rate': purple_raids / total_raids if total_raids > 0 else 0,
                'total_points': total_points_sum,
                'average_points': round(avg_points, 2)
            }
        finally:
            session.close()
    
    def get_item_statistics(self) -> Dict[str, int]:
        """Get statistics on item drops"""
        session = self.get_session()
        try:
            raids = session.query(COXRaid).filter(COXRaid.item_list.isnot(None)).all()
            item_counts = {}
            
            for raid in raids:
                if raid.item_list:
                    for item in raid.item_list:
                        item_name = item.get('item', 'Unknown')
                        quantity = item.get('quantity', 1)
                        item_counts[item_name] = item_counts.get(item_name, 0) + quantity
            
            # Sort by count descending
            return dict(sorted(item_counts.items(), key=lambda x: x[1], reverse=True))
        finally:
            session.close()
    
    def update_raid(self, raid_id: int, **kwargs) -> Optional[COXRaid]:
        """Update a raid record"""
        session = self.get_session()
        try:
            raid = session.query(COXRaid).filter(COXRaid.id == raid_id).first()
            if raid:
                for key, value in kwargs.items():
                    if hasattr(raid, key):
                        setattr(raid, key, value)
                session.commit()
                session.refresh(raid)
            return raid
        finally:
            session.close()
    
    def delete_raid(self, raid_id: int) -> bool:
        """Delete a raid record"""
        session = self.get_session()
        try:
            raid = session.query(COXRaid).filter(COXRaid.id == raid_id).first()
            if raid:
                session.delete(raid)
                session.commit()
                return True
            return False
        finally:
            session.close()

# Usage example
if __name__ == "__main__":
    # Initialize database
    db = DatabaseManager()
    
    # Add a sample raid
    raid = db.add_raid(
        raid_type="regular",
        points=25000,
        completion_count=1,
        is_purple=True,
        item_list=[
            {"item": "Twisted bow", "quantity": 1, "confidence": "high"},
            {"item": "Teak plank", "quantity": 15, "confidence": "high"}
        ]
    )
    
    print(f"Added raid: {raid}")
    
    # Get stats
    stats = db.get_raid_stats()
    print(f"Raid stats: {stats}")
    
    # Get item stats
    item_stats = db.get_item_statistics()
    print(f"Item stats: {item_stats}")
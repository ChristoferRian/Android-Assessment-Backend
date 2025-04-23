import aiosqlite
import json
from typing import Dict, Any, List, Optional
import os
import datetime

class DBRepository:
    """Repository for asynchronous database operations."""
    
    def __init__(self, db_path: str = "database/scans.db"):
        """
        Initialize the database repository.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        
    async def initialize(self) -> None:
        """Initialize the database and create required tables if they don't exist."""
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    brand TEXT NOT NULL,
                    model TEXT NOT NULL,
                    scan_type TEXT NOT NULL,
                    scan_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await db.commit()
    
    async def save_scan_result(self, 
                              device_id: str, 
                              brand: str, 
                              model: str, 
                              scan_type: str, 
                              scan_data: Dict[str, Any]) -> int:
        """
        Save scan result to the database.
        
        Args:
            device_id: The device identifier
            brand: The device brand
            model: The device model
            scan_type: The type of scan (fast/full)
            scan_data: The scan data as a dictionary
            
        Returns:
            The ID of the inserted record
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                '''
                INSERT INTO scans (device_id, brand, model, scan_type, scan_data)
                VALUES (?, ?, ?, ?, ?)
                ''',
                (device_id, brand, model, scan_type, json.dumps(scan_data))
            )
            await db.commit()
            return cursor.lastrowid
    
    async def get_scan_by_id(self, scan_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a scan result by its ID.
        
        Args:
            scan_id: The scan ID
            
        Returns:
            The scan record as a dictionary, or None if not found
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                'SELECT * FROM scans WHERE id = ?',
                (scan_id,)
            )
            row = await cursor.fetchone()
            
            if not row:
                return None
                
            return {
                "id": row["id"],
                "device_id": row["device_id"],
                "brand": row["brand"],
                "model": row["model"],
                "scan_type": row["scan_type"],
                "scan_data": json.loads(row["scan_data"]),
                "created_at": row["created_at"]
            }
    
    async def get_scans_by_device_id(self, device_id: str) -> List[Dict[str, Any]]:
        """
        Get all scan results for a specific device.
        
        Args:
            device_id: The device identifier
            
        Returns:
            List of scan records
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                'SELECT * FROM scans WHERE device_id = ? ORDER BY created_at DESC',
                (device_id,)
            )
            rows = await cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    "id": row["id"],
                    "device_id": row["device_id"],
                    "brand": row["brand"],
                    "model": row["model"],
                    "scan_type": row["scan_type"],
                    "scan_data": json.loads(row["scan_data"]),
                    "created_at": row["created_at"]
                })
                
            return results
    
    async def get_all_scans(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all scan results with optional limit.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of scan records
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                'SELECT * FROM scans ORDER BY created_at DESC LIMIT ?',
                (limit,)
            )
            rows = await cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    "id": row["id"],
                    "device_id": row["device_id"],
                    "brand": row["brand"],
                    "model": row["model"],
                    "scan_type": row["scan_type"],
                    "scan_data": json.loads(row["scan_data"]),
                    "created_at": row["created_at"]
                })
                
            return results
    
    async def delete_scan(self, scan_id: int) -> bool:
        """
        Delete a scan result by its ID.
        
        Args:
            scan_id: The scan ID
            
        Returns:
            True if deleted successfully, False if not found
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                'DELETE FROM scans WHERE id = ?',
                (scan_id,)
            )
            await db.commit()
            
            return cursor.rowcount > 0

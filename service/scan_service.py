import asyncio
import json
from typing import Dict, Any, List, Optional, Callable
import datetime
import time

from repositories.adb_repository import ADBRepository
from repositories.db_repository import DBRepository
from repositories.brand.brand_factory import BrandFactory
from repositories.brand.base_brand import BaseBrand

class ScanService:
    """Service for performing device scans and managing scan results."""
    
    def __init__(self, 
                 adb_repo: ADBRepository, 
                 db_repo: DBRepository,
                 brand_factory: BrandFactory,
                 websocket_manager = None):
        """
        Initialize the scan service.
        
        Args:
            adb_repo: ADB repository for executing commands
            db_repo: Database repository for storing results
            brand_factory: Factory for creating brand-specific implementations
            websocket_manager: Websocket manager for real-time updates
        """
        self.adb_repo = adb_repo
        self.db_repo = db_repo
        self.brand_factory = brand_factory
        self.websocket_manager = websocket_manager
    
    async def _send_status_update(self, message: str) -> None:
        """
        Send a status update via websocket.
        
        Args:
            message: The status message
        """
        if self.websocket_manager:
            await self.websocket_manager.broadcast(
                json.dumps({
                    "type": "status_update",
                    "message": message,
                    "timestamp": datetime.datetime.now().isoformat()
                })
            )
    
    async def fast_scan(self, device_id: str) -> Dict[str, Any]:
        """
        Perform a fast scan of the device.
        
        Args:
            device_id: The device identifier
            
        Returns:
            Scan results as a dictionary
        """
        # Send status update
        await self._send_status_update(f"Starting fast scan for device {device_id}")
        
        # Ensure device is connected
        if not await self.adb_repo.is_device_connected(device_id):
            raise Exception(f"Device {device_id} is not connected")
        
        # Detect and create brand implementation
        await self._send_status_update("Detecting device brand")
        brand_impl = await self.brand_factory.create_brand_implementation(device_id)
        
        # Get basic device information
        await self._send_status_update("Gathering basic device information")
        device_info = await brand_impl.get_device_info(device_id)
        
        # Save scan results to database
        await self._send_status_update("Saving scan results")
        scan_id = await self.db_repo.save_scan_result(
            device_id=device_id,
            brand=device_info.get("brand", "Unknown"),
            model=device_info.get("model", "Unknown"),
            scan_type="fast",
            scan_data=device_info
        )
        
        # Add scan ID to results
        device_info["scan_id"] = scan_id
        device_info["scan_type"] = "fast"
        device_info["timestamp"] = datetime.datetime.now().isoformat()
        
        await self._send_status_update("Fast scan completed successfully")
        return device_info
    
    async def full_scan(self, device_id: str) -> Dict[str, Any]:
        """
        Perform a full scan of the device with detailed information.
        
        Args:
            device_id: The device identifier
            
        Returns:
            Scan results as a dictionary
        """
        # Send status update
        await self._send_status_update(f"Starting full scan for device {device_id}")
        
        # Ensure device is connected
        if not await self.adb_repo.is_device_connected(device_id):
            raise Exception(f"Device {device_id} is not connected")
        
        # Detect and create brand implementation
        await self._send_status_update("Detecting device brand")
        brand_impl = await self.brand_factory.create_brand_implementation(device_id)
        
        # Get basic device information
        await self._send_status_update("Gathering device information")
        device_info = await brand_impl.get_device_info(device_id)
        
        # Get additional information for full scan
        await self._send_status_update("Gathering installed applications")
        installed_apps = await brand_impl.get_installed_apps(device_id)
        
        # Add additional information to results
        device_info["installed_apps"] = installed_apps
        
        # Additional detailed information can be added here
        # For example, system settings, network configuration, etc.
        
        # Save scan results to database
        await self._send_status_update("Saving scan results")
        scan_id = await self.db_repo.save_scan_result(
            device_id=device_id,
            brand=device_info.get("brand", "Unknown"),
            model=device_info.get("model", "Unknown"),
            scan_type="full",
            scan_data=device_info
        )
        
        # Add scan ID to results
        device_info["scan_id"] = scan_id
        device_info["scan_type"] = "full"
        device_info["timestamp"] = datetime.datetime.now().isoformat()
        
        await self._send_status_update("Full scan completed successfully")
        return device_info
    
    async def get_scan_by_id(self, scan_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a scan result by its ID.
        
        Args:
            scan_id: The scan ID
            
        Returns:
            The scan record or None if not found
        """
        return await self.db_repo.get_scan_by_id(scan_id)
    
    async def get_scans_by_device_id(self, device_id: str) -> List[Dict[str, Any]]:
        """
        Get all scan results for a specific device.
        
        Args:
            device_id: The device identifier
            
        Returns:
            List of scan records
        """
        return await self.db_repo.get_scans_by_device_id(device_id)
    
    async def get_all_scans(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all scan results with optional limit.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of scan records
        """
        return await self.db_repo.get_all_scans(limit)
    
    async def delete_scan(self, scan_id: int) -> bool:
        """
        Delete a scan result by its ID.
        
        Args:
            scan_id: The scan ID
            
        Returns:
            True if deleted successfully, False if not found
        """
        return await self.db_repo.delete_scan(scan_id)

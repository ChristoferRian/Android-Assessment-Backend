import asyncio
import json
from typing import Dict, Any, List, Optional, Callable
import datetime

from repositories.adb_repository import ADBRepository
from repositories.brand.brand_factory import BrandFactory

class DeviceService:
    """Service for managing device connections and detection."""
    
    def __init__(self, 
                 adb_repo: ADBRepository, 
                 brand_factory: BrandFactory,
                 websocket_manager = None,
                 polling_interval: int = 5):
        """
        Initialize the device service.
        
        Args:
            adb_repo: ADB repository for executing commands
            brand_factory: Factory for creating brand-specific implementations
            websocket_manager: Websocket manager for real-time updates
            polling_interval: Interval (in seconds) for polling connected devices
        """
        self.adb_repo = adb_repo
        self.brand_factory = brand_factory
        self.websocket_manager = websocket_manager
        self.polling_interval = polling_interval
        self.connected_devices = {}  # Store connected devices with metadata
        self._polling_task = None
    
    async def _send_device_update(self, device_data: Dict[str, Any]) -> None:
        """
        Send a device update via websocket.
        
        Args:
            device_data: The device data to send
        """
        if self.websocket_manager:
            await self.websocket_manager.broadcast(
                json.dumps({
                    "type": "device_update",
                    "data": device_data,
                    "timestamp": datetime.datetime.now().isoformat()
                })
            )
    
    async def start_device_polling(self) -> None:
        """Start polling for connected devices."""
        # Start ADB server if not already running
        await self.adb_repo.start_adb_server()
        
        # Cancel existing polling task if it exists
        if self._polling_task and not self._polling_task.done():
            self._polling_task.cancel()
            
        # Create a new polling task
        self._polling_task = asyncio.create_task(self._poll_devices())
    
    async def stop_device_polling(self) -> None:
        """Stop polling for connected devices."""
        if self._polling_task and not self._polling_task.done():
            self._polling_task.cancel()
            self._polling_task = None
    
    async def _poll_devices(self) -> None:
        """Poll for connected devices and update status."""
        try:
            while True:
                # Get list of connected devices
                devices = await self.adb_repo.get_connected_devices()
                
                # Track new and disconnected devices
                current_ids = set(devices)
                previous_ids = set(self.connected_devices.keys())
                
                # Handle new devices
                for device_id in current_ids - previous_ids:
                    await self._handle_new_device(device_id)
                
                # Handle disconnected devices
                for device_id in previous_ids - current_ids:
                    await self._handle_disconnected_device(device_id)
                
                # Wait for next polling interval
                await asyncio.sleep(self.polling_interval)
        except asyncio.CancelledError:
            # Task was cancelled, exit gracefully
            pass
        except Exception as e:
            # Log the error and restart polling
            print(f"Error in device polling: {str(e)}")
            await asyncio.sleep(5)
            await self.start_device_polling()
    
    async def _handle_new_device(self, device_id: str) -> None:
        """
        Handle a newly connected device.
        
        Args:
            device_id: The device identifier
        """
        try:
            # Attempt to authorize the device if needed
            authorized = await self.adb_repo.authorize_device(device_id)
            
            if not authorized:
                # Send notification to approve USB debugging on the device
                await self._send_device_update({
                    "device_id": device_id,
                    "status": "pending_authorization",
                    "message": "Please approve USB debugging on your device"
                })
                return
            
            # Detect brand
            brand = await self.brand_factory.detect_brand(device_id)
            
            # Create brand implementation
            brand_impl = await self.brand_factory.create_brand_implementation(device_id)
            
            # Get basic device info
            model = await brand_impl.get_device_model(device_id)
            android_version = await brand_impl.get_android_version(device_id)
            
            # Store device information
            device_info = {
                "device_id": device_id,
                "brand": brand,
                "model": model,
                "android_version": android_version,
                "status": "connected",
                "connected_at": datetime.datetime.now().isoformat()
            }
            
            self.connected_devices[device_id] = device_info
            
            # Send notification about new device
            await self._send_device_update(device_info)
            
        except Exception as e:
            # Send error notification
            await self._send_device_update({
                "device_id": device_id,
                "status": "error",
                "message": f"Error detecting device: {str(e)}"
            })
    
    async def _handle_disconnected_device(self, device_id: str) -> None:
        """
        Handle a disconnected device.
        
        Args:
            device_id: The device identifier
        """
        # Get device info before removing
        device_info = self.connected_devices.get(device_id, {"device_id": device_id})
        
        # Remove from connected devices
        if device_id in self.connected_devices:
            del self.connected_devices[device_id]
        
        # Send notification about disconnected device
        device_info["status"] = "disconnected"
        device_info["disconnected_at"] = datetime.datetime.now().isoformat()
        await self._send_device_update(device_info)
    
    async def get_connected_devices(self) -> List[Dict[str, Any]]:
        """
        Get a list of currently connected devices.
        
        Returns:
            List of connected device information
        """
        return list(self.connected_devices.values())
    
    async def get_device_info(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific device.
        
        Args:
            device_id: The device identifier
            
        Returns:
            Device information or None if not connected
        """
        return self.connected_devices.get(device_id)
    
    async def wait_for_device(self, timeout: int = 30) -> Optional[str]:
        """
        Wait for any device to be connected within the timeout period.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            The device ID if one is found, None if timeout
        """
        return await self.adb_repo.wait_for_device(timeout)

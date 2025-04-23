from fastapi import APIRouter, Depends, HTTPException, WebSocket, BackgroundTasks, Request
from typing import List, Dict, Any
import json

from service.device_service import DeviceService
from repositories.adb_repository import ADBRepository
from repositories.brand.brand_factory import BrandFactory

# Create router
router = APIRouter()

# Dependency to get the shared DeviceService instance
def get_device_service(request: Request) -> DeviceService:
    """Get the shared DeviceService instance from app.state"""
    return request.app.state.device_service

@router.get("/connected")
async def get_connected_devices(
    device_service: DeviceService = Depends(get_device_service)
) -> List[Dict[str, Any]]:
    """Get all connected devices."""
    return await device_service.get_connected_devices()

@router.get("/{device_id}")
async def get_device_info(
    device_id: str,
    device_service: DeviceService = Depends(get_device_service)
) -> Dict[str, Any]:
    """Get information about a specific device."""
    device_info = await device_service.get_device_info(device_id)
    if not device_info:
        raise HTTPException(status_code=404, detail="Device not found")
    return device_info

@router.post("/start-polling")
async def start_device_polling(
    background_tasks: BackgroundTasks,
    device_service: DeviceService = Depends(get_device_service)
) -> Dict[str, Any]:
    """Start polling for connected devices."""
    background_tasks.add_task(device_service.start_device_polling)
    return {"status": "Device polling started"}

@router.post("/stop-polling")
async def stop_device_polling(
    device_service: DeviceService = Depends(get_device_service)
) -> Dict[str, Any]:
    """Stop polling for connected devices."""
    await device_service.stop_device_polling()
    return {"status": "Device polling stopped"}

@router.post("/wait")
async def wait_for_device(
    timeout: int = 30,
    device_service: DeviceService = Depends(get_device_service)
) -> Dict[str, Any]:
    """Wait for a device to be connected."""
    device_id = await device_service.wait_for_device(timeout)
    if not device_id:
        return {"status": "timeout", "message": "No device connected within timeout period"}
    
    return {
        "status": "connected",
        "device_id": device_id
    }

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any
import json

from service.scan_service import ScanService
from service.device_service import DeviceService
from repositories.adb_repository import ADBRepository
from repositories.db_repository import DBRepository
from repositories.brand.brand_factory import BrandFactory

# Create router
router = APIRouter()

# Dependencies
def get_adb_repository():
    return ADBRepository()

def get_db_repository():
    db_repo = DBRepository()
    return db_repo

def get_brand_factory(adb_repo: ADBRepository = Depends(get_adb_repository)):
    return BrandFactory(adb_repo)

def get_device_service(
    adb_repo: ADBRepository = Depends(get_adb_repository),
    brand_factory: BrandFactory = Depends(get_brand_factory)
):
    # Note: In main.py, we'll pass the WebSocket manager to this service
    return DeviceService(adb_repo, brand_factory)

def get_scan_service(
    adb_repo: ADBRepository = Depends(get_adb_repository),
    db_repo: DBRepository = Depends(get_db_repository),
    brand_factory: BrandFactory = Depends(get_brand_factory)
):
    # Note: In main.py, we'll pass the WebSocket manager to this service
    return ScanService(adb_repo, db_repo, brand_factory)

@router.post("/{device_id}")
async def perform_fast_scan(
    device_id: str,
    background_tasks: BackgroundTasks,
    scan_service: ScanService = Depends(get_scan_service),
    device_service: DeviceService = Depends(get_device_service)
) -> Dict[str, Any]:
    """
    Perform a fast scan on the specified device.
    
    This will collect basic device information quickly.
    """
    # Check if device is connected
    device_info = await device_service.get_device_info(device_id)
    if not device_info:
        raise HTTPException(
            status_code=404, 
            detail=f"Device {device_id} not connected or not authorized"
        )
    
    # Perform scan in background to not block the response
    background_tasks.add_task(scan_service.fast_scan, device_id)
    
    return {
        "status": "Scan started",
        "device_id": device_id,
        "scan_type": "fast",
        "message": "Fast scan initiated. Progress will be sent via WebSocket."
    }

@router.get("/{device_id}/last")
async def get_last_fast_scan(
    device_id: str,
    scan_service: ScanService = Depends(get_scan_service)
) -> Dict[str, Any]:
    """Get the most recent fast scan result for a device."""
    scans = await scan_service.get_scans_by_device_id(device_id)
    
    # Filter for fast scans and get the latest
    fast_scans = [scan for scan in scans if scan["scan_type"] == "fast"]
    
    if not fast_scans:
        raise HTTPException(
            status_code=404,
            detail=f"No fast scan results found for device {device_id}"
        )
    
    return fast_scans[0]  # Return the most recent scan

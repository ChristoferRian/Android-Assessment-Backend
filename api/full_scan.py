from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from typing import Dict, Any
import json

from service.scan_service import ScanService
from service.device_service import DeviceService

# Create router
router = APIRouter()

# Dependencies to get shared service instances
def get_scan_service(request: Request) -> ScanService:
    """Get the shared ScanService instance from app.state"""
    return request.app.state.scan_service

def get_device_service(request: Request) -> DeviceService:
    """Get the shared DeviceService instance from app.state"""
    return request.app.state.device_service

@router.post("/{device_id}")
async def perform_full_scan(
    device_id: str,
    background_tasks: BackgroundTasks,
    scan_service: ScanService = Depends(get_scan_service),
    device_service: DeviceService = Depends(get_device_service)
) -> Dict[str, Any]:
    """
    Perform a full scan on the specified device.
    
    This will collect detailed device information including installed apps.
    """
    # Check if device is connected
    device_info = await device_service.get_device_info(device_id)
    if not device_info:
        raise HTTPException(
            status_code=404, 
            detail=f"Device {device_id} not connected or not authorized"
        )
    
    # Perform scan in background to not block the response
    background_tasks.add_task(scan_service.full_scan, device_id)
    
    return {
        "status": "Scan started",
        "device_id": device_id,
        "scan_type": "full",
        "message": "Full scan initiated. Progress will be sent via WebSocket."
    }

@router.get("/{device_id}/last")
async def get_last_full_scan(
    device_id: str,
    scan_service: ScanService = Depends(get_scan_service)
) -> Dict[str, Any]:
    """Get the most recent full scan result for a device."""
    scans = await scan_service.get_scans_by_device_id(device_id)
    
    # Filter for full scans and get the latest
    full_scans = [scan for scan in scans if scan["scan_type"] == "full"]
    
    if not full_scans:
        raise HTTPException(
            status_code=404,
            detail=f"No full scan results found for device {device_id}"
        )
    
    return full_scans[0]  # Return the most recent scan

@router.get("/{device_id}/compare/{scan_id_1}/{scan_id_2}")
async def compare_full_scans(
    device_id: str,
    scan_id_1: int,
    scan_id_2: int,
    scan_service: ScanService = Depends(get_scan_service)
) -> Dict[str, Any]:
    """Compare two full scan results."""
    # Get the scan results
    scan1 = await scan_service.get_scan_by_id(scan_id_1)
    scan2 = await scan_service.get_scan_by_id(scan_id_2)
    
    if not scan1 or not scan2:
        raise HTTPException(
            status_code=404,
            detail="One or both scan IDs not found"
        )
    
    if scan1["device_id"] != device_id or scan2["device_id"] != device_id:
        raise HTTPException(
            status_code=400,
            detail="Both scans must be for the specified device"
        )
    
    # Calculate differences between the scans
    differences = {}
    scan1_data = scan1["scan_data"]
    scan2_data = scan2["scan_data"]
    
    # Check basic device info differences
    for key in ["android_version", "security_patch", "kernel_version", 
                "baseband_version", "bootloader_locked"]:
        if key in scan1_data and key in scan2_data and scan1_data[key] != scan2_data[key]:
            differences[key] = {
                "scan1": scan1_data[key],
                "scan2": scan2_data[key]
            }
    
    # Check storage differences
    if "storage" in scan1_data and "storage" in scan2_data:
        storage_diff = {}
        for key in ["total", "available"]:
            if key in scan1_data["storage"] and key in scan2_data["storage"] and \
               scan1_data["storage"][key] != scan2_data["storage"][key]:
                storage_diff[key] = {
                    "scan1": scan1_data["storage"][key],
                    "scan2": scan2_data["storage"][key]
                }
        if storage_diff:
            differences["storage"] = storage_diff
    
    # Check app differences if available
    if "installed_apps" in scan1_data and "installed_apps" in scan2_data:
        apps1 = set(scan1_data["installed_apps"])
        apps2 = set(scan2_data["installed_apps"])
        
        newly_installed = list(apps2 - apps1)
        removed = list(apps1 - apps2)
        
        if newly_installed or removed:
            differences["installed_apps"] = {
                "newly_installed": newly_installed,
                "removed": removed
            }
    
    return {
        "device_id": device_id,
        "scan1": {
            "id": scan_id_1,
            "timestamp": scan1["created_at"]
        },
        "scan2": {
            "id": scan_id_2,
            "timestamp": scan2["created_at"]
        },
        "differences": differences
    }

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from typing import Dict, Any
import json

from service.scan_service import ScanService

# Create router
router = APIRouter()

# Dependency to get shared ScanService
def get_scan_service(request: Request) -> ScanService:
    return request.app.state.scan_service

@router.post("/{device_id}")
async def perform_fast_scan(
    device_id: str,
    background_tasks: BackgroundTasks,
    scan_service: ScanService = Depends(get_scan_service)
) -> Dict[str, Any]:
    """Initiate a fast scan (basic device info) in background."""
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

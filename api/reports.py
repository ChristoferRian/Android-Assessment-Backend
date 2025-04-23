from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.responses import JSONResponse, FileResponse
from typing import Dict, Any, List
import json
import tempfile
import os
from datetime import datetime

from service.scan_service import ScanService

# Create router
router = APIRouter()

# Dependency to get shared service instance
def get_scan_service(request: Request) -> ScanService:
    """Get the shared ScanService instance from app.state"""
    return request.app.state.scan_service

@router.get("/")
async def get_all_reports(
    limit: int = 50,
    scan_service: ScanService = Depends(get_scan_service)
) -> List[Dict[str, Any]]:
    """Get all scan reports with optional limit."""
    return await scan_service.get_all_scans(limit)

@router.get("/{scan_id}")
async def get_report_by_id(
    scan_id: int,
    scan_service: ScanService = Depends(get_scan_service)
) -> Dict[str, Any]:
    """Get a specific scan report by ID."""
    report = await scan_service.get_scan_by_id(scan_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report with ID {scan_id} not found")
    return report

@router.get("/device/{device_id}")
async def get_reports_by_device(
    device_id: str,
    scan_service: ScanService = Depends(get_scan_service)
) -> List[Dict[str, Any]]:
    """Get all scan reports for a specific device."""
    return await scan_service.get_scans_by_device_id(device_id)

@router.get("/{scan_id}/download")
async def download_report(
    scan_id: int,
    format: str = "json",
    scan_service: ScanService = Depends(get_scan_service)
) -> Response:
    """
    Download a scan report in the specified format.
    
    Currently supported formats: json
    """
    report = await scan_service.get_scan_by_id(scan_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report with ID {scan_id} not found")
    
    if format.lower() == "json":
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_file:
            temp_file.write(json.dumps(report, indent=2).encode('utf-8'))
            temp_path = temp_file.name
        
        # Generate filename based on device info and scan date
        device_model = report.get("model", "unknown")
        device_id = report.get("device_id", "unknown")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scan_{device_model}_{device_id}_{timestamp}.json"
        
        # Return the file for download
        return FileResponse(
            path=temp_path,
            filename=filename,
            media_type="application/json",
            background=tempfile.TemporaryFile  # Clean up the file after sending
        )
    else:
        raise HTTPException(status_code=400, detail=f"Format '{format}' not supported")

@router.delete("/{scan_id}")
async def delete_report(
    scan_id: int,
    scan_service: ScanService = Depends(get_scan_service)
) -> Dict[str, Any]:
    """Delete a specific scan report."""
    success = await scan_service.delete_scan(scan_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Report with ID {scan_id} not found")
    
    return {"status": "success", "message": f"Report {scan_id} deleted successfully"}

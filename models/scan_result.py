from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from models.device_info import DeviceInfo

class ScanBase(BaseModel):
    """Base model for scan operations."""
    device_id: str = Field(..., description="ADB device identifier")
    scan_type: str = Field(..., description="Type of scan (fast/full)")
    
class ScanResult(ScanBase):
    """Model for a completed scan result."""
    id: int = Field(..., description="Scan ID in the database")
    brand: str = Field(..., description="Device brand")
    model: str = Field(..., description="Device model")
    scan_data: Dict[str, Any] = Field(..., description="Complete scan data")
    created_at: datetime = Field(..., description="Timestamp when scan was performed")
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "device_id": "ABCD1234",
                "brand": "Xiaomi",
                "model": "Redmi Note 10 Pro",
                "scan_type": "full",
                "scan_data": {
                    "brand": "Xiaomi",
                    "model": "Redmi Note 10 Pro",
                    "android_version": "11",
                    "security_patch": "2023-03-01",
                    "kernel_version": "Linux version 4.19.157-perf+",
                    "baseband_version": "M52DXXXXX",
                    "bootloader_locked": True,
                    "user_name": "user@example.com",
                    "storage": {
                        "total": "128G",
                        "used": "64G",
                        "available": "64G",
                        "use_percentage": "50%"
                    },
                    "installed_apps": [
                        "com.android.chrome",
                        "com.whatsapp",
                        "com.instagram.android"
                    ]
                },
                "created_at": "2023-09-15T14:30:00"
            }
        }

class ScanRequest(ScanBase):
    """Model for a scan request."""
    pass

class ScanResponse(BaseModel):
    """Model for response to a scan request."""
    status: str = Field(..., description="Status of the scan request")
    device_id: str = Field(..., description="ADB device identifier")
    scan_type: str = Field(..., description="Type of scan (fast/full)")
    message: str = Field(..., description="Status message")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "Scan started",
                "device_id": "ABCD1234",
                "scan_type": "full",
                "message": "Full scan initiated. Progress will be sent via WebSocket."
            }
        }

class ScanStatus(BaseModel):
    """Model for scan status updates via WebSocket."""
    type: str = Field("status_update", description="Type of WebSocket message")
    message: str = Field(..., description="Status message")
    timestamp: datetime = Field(..., description="Timestamp of the status update")
    progress: Optional[float] = Field(None, description="Scan progress percentage if available")
    
    class Config:
        schema_extra = {
            "example": {
                "type": "status_update",
                "message": "Gathering device information",
                "timestamp": "2023-09-15T14:30:05",
                "progress": 50.0
            }
        }

class ScanComparison(BaseModel):
    """Model for comparing two scan results."""
    device_id: str = Field(..., description="ADB device identifier")
    scan1: Dict[str, Any] = Field(..., description="First scan summary")
    scan2: Dict[str, Any] = Field(..., description="Second scan summary")
    differences: Dict[str, Any] = Field(..., description="Differences between scans")
    
    class Config:
        schema_extra = {
            "example": {
                "device_id": "ABCD1234",
                "scan1": {
                    "id": 1,
                    "timestamp": "2023-09-01T10:00:00"
                },
                "scan2": {
                    "id": 2,
                    "timestamp": "2023-09-15T14:30:00"
                },
                "differences": {
                    "android_version": {
                        "scan1": "10",
                        "scan2": "11"
                    },
                    "security_patch": {
                        "scan1": "2023-01-01",
                        "scan2": "2023-03-01"
                    },
                    "installed_apps": {
                        "newly_installed": ["com.instagram.android"],
                        "removed": ["com.facebook.katana"]
                    }
                }
            }
        }

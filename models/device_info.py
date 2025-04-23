from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

class StorageInfo(BaseModel):
    """Model for device storage information."""
    total: str = Field(..., description="Total storage capacity")
    used: Optional[str] = Field(None, description="Used storage")
    available: str = Field(..., description="Available storage space")
    use_percentage: Optional[str] = Field(None, description="Percentage of storage used")

class DeviceInfo(BaseModel):
    """Model for basic device information."""
    device_id: str = Field(..., description="ADB device identifier")
    brand: str = Field(..., description="Device brand (e.g., Xiaomi, Infinix)")
    model: str = Field(..., description="Device model name")
    android_version: str = Field(..., description="Android OS version")
    security_patch: str = Field(..., description="Security patch level")
    kernel_version: str = Field(..., description="Kernel version")
    baseband_version: str = Field(..., description="Baseband version")
    bootloader_locked: bool = Field(..., description="Bootloader lock status (True if locked)")
    user_name: Optional[str] = Field(None, description="Device user name if available")
    storage: StorageInfo = Field(..., description="Storage information")
    
    class Config:
        schema_extra = {
            "example": {
                "device_id": "ABCD1234",
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
                }
            }
        }

class DeviceConnection(BaseModel):
    """Model for device connection status."""
    device_id: str = Field(..., description="ADB device identifier")
    brand: Optional[str] = Field(None, description="Device brand if detected")
    model: Optional[str] = Field(None, description="Device model if detected")
    android_version: Optional[str] = Field(None, description="Android OS version if detected")
    status: str = Field(..., description="Connection status (connected, disconnected, pending_authorization, error)")
    connected_at: Optional[datetime] = Field(None, description="Timestamp when device was connected")
    disconnected_at: Optional[datetime] = Field(None, description="Timestamp when device was disconnected")
    message: Optional[str] = Field(None, description="Additional status message")
    
    class Config:
        schema_extra = {
            "example": {
                "device_id": "ABCD1234",
                "brand": "Xiaomi",
                "model": "Redmi Note 10 Pro",
                "android_version": "11",
                "status": "connected",
                "connected_at": "2023-09-15T14:30:00",
                "disconnected_at": None,
                "message": None
            }
        }

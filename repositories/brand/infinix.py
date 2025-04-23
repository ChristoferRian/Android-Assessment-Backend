from typing import Dict, Any, List
import json

from repositories.brand.base_brand import BaseBrand
from repositories.adb_repository import ADBRepository

class InfinixBrand(BaseBrand):
    """Implementation of BaseBrand for Infinix devices."""
    
    def __init__(self, adb_repo: ADBRepository):
        self.adb_repo = adb_repo
        
    async def get_device_model(self, device_id: str) -> str:
        """Get the commercial name/model of the device using Infinix-specific command."""
        # Infinix-specific command for device model
        result = await self.adb_repo.execute_command(
            device_id, 
            "getprop persist.trans.sys.trans.device.name"
        )
        return result.strip()
    
    async def get_android_version(self, device_id: str) -> str:
        """Get the Android version of the device."""
        result = await self.adb_repo.execute_command(
            device_id, 
            "getprop ro.build.version.release"
        )
        return result.strip()
    
    async def get_security_patch(self, device_id: str) -> str:
        """Get the security patch level of the device."""
        result = await self.adb_repo.execute_command(
            device_id, 
            "getprop ro.build.version.security_patch"
        )
        return result.strip()
    
    async def get_kernel_version(self, device_id: str) -> str:
        """Get the kernel version of the device."""
        result = await self.adb_repo.execute_command(
            device_id, 
            "cat /proc/version"
        )
        return result.strip()
    
    async def get_baseband_version(self, device_id: str) -> str:
        """Get the baseband version of the device."""
        # Infinix might use a different property for baseband
        result = await self.adb_repo.execute_command(
            device_id, 
            "getprop gsm.version.baseband"
        )
        if not result.strip():
            # Fallback to alternative property
            result = await self.adb_repo.execute_command(
                device_id,
                "getprop ro.build.display.id"
            )
        return result.strip()
    
    async def get_bootloader_status(self, device_id: str) -> bool:
        """Get bootloader locked status (True if locked, False if unlocked)."""
        result = await self.adb_repo.execute_command(
            device_id, 
            "getprop ro.boot.verifiedbootstate"
        )
        # For Infinix, "green" typically means locked, "orange" means unlocked
        return result.strip().lower() == "green"
    
    async def get_user_name(self, device_id: str) -> str:
        """Get the user name from the device."""
        # Infinix might store user information differently
        result = await self.adb_repo.execute_command(
            device_id, 
            "dumpsys account | grep name"
        )
        # Parse the output to extract the username
        if "name=" in result:
            return result.split("name=")[1].split(",")[0].strip()
        return ""
    
    async def get_storage_info(self, device_id: str) -> Dict[str, Any]:
        """Get storage information including total and available."""
        result = await self.adb_repo.execute_command(
            device_id, 
            "df -h /data"
        )
        # Parse the output to extract storage information
        lines = result.strip().split('\n')
        if len(lines) > 1:
            # Split by whitespace and take the relevant columns
            parts = lines[1].split()
            if len(parts) >= 4:
                return {
                    "total": parts[1],
                    "used": parts[2],
                    "available": parts[3],
                    "use_percentage": parts[4] if len(parts) > 4 else None
                }
        return {"total": "Unknown", "available": "Unknown"}
    
    async def get_installed_apps(self, device_id: str) -> List[str]:
        """Get list of installed applications."""
        result = await self.adb_repo.execute_command(
            device_id, 
            "pm list packages -3"  # List third-party packages
        )
        # Parse the output to extract package names
        packages = []
        for line in result.strip().split('\n'):
            if line.startswith('package:'):
                packages.append(line[8:])  # Remove 'package:' prefix
        return packages
    
    async def get_device_info(self, device_id: str) -> Dict[str, Any]:
        """Get all device information in a single call."""
        device_model = await self.get_device_model(device_id)
        android_version = await self.get_android_version(device_id)
        security_patch = await self.get_security_patch(device_id)
        kernel_version = await self.get_kernel_version(device_id)
        baseband_version = await self.get_baseband_version(device_id)
        bootloader_status = await self.get_bootloader_status(device_id)
        user_name = await self.get_user_name(device_id)
        storage_info = await self.get_storage_info(device_id)
        
        return {
            "brand": "Infinix",
            "model": device_model,
            "android_version": android_version,
            "security_patch": security_patch,
            "kernel_version": kernel_version,
            "baseband_version": baseband_version,
            "bootloader_locked": bootloader_status,
            "user_name": user_name,
            "storage": storage_info
        }

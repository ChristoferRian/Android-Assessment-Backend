from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseBrand(ABC):
    """Base abstract class for all Android device brands.
    
    Each brand implementation should inherit from this class and implement
    all the required methods with brand-specific ADB commands.
    """
    
    @abstractmethod
    async def get_device_model(self, device_id: str) -> str:
        """Get the commercial name/model of the device."""
        pass
    
    @abstractmethod
    async def get_android_version(self, device_id: str) -> str:
        """Get the Android version of the device."""
        pass
    
    @abstractmethod
    async def get_security_patch(self, device_id: str) -> str:
        """Get the security patch level of the device."""
        pass
    
    @abstractmethod
    async def get_kernel_version(self, device_id: str) -> str:
        """Get the kernel version of the device."""
        pass
    
    @abstractmethod
    async def get_baseband_version(self, device_id: str) -> str:
        """Get the baseband version of the device."""
        pass
    
    @abstractmethod
    async def get_bootloader_status(self, device_id: str) -> bool:
        """Get bootloader locked status (True if locked, False if unlocked)."""
        pass
    
    @abstractmethod
    async def get_user_name(self, device_id: str) -> str:
        """Get the user name from the device."""
        pass
    
    @abstractmethod
    async def get_storage_info(self, device_id: str) -> Dict[str, Any]:
        """Get storage information including total and available."""
        pass
    
    @abstractmethod
    async def get_installed_apps(self, device_id: str) -> List[str]:
        """Get list of installed applications."""
        pass
    
    @abstractmethod
    async def get_device_info(self, device_id: str) -> Dict[str, Any]:
        """Get all device information in a single call."""
        pass

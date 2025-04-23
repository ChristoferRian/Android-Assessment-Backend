from typing import Dict, Any, List, Optional

from repositories.brand.base_brand import BaseBrand
from repositories.brand.xiaomi import XiaomiBrand
from repositories.brand.infinix import InfinixBrand
from repositories.adb_repository import ADBRepository

class BrandFactory:
    """Factory for creating brand-specific implementations based on device detection."""
    
    def __init__(self, adb_repo: ADBRepository):
        self.adb_repo = adb_repo
        # Register available brand implementations
        self.brands = {
            "xiaomi": XiaomiBrand,
            "infinix": InfinixBrand,
            # Add more brands as needed
        }
        
    async def detect_brand(self, device_id: str) -> str:
        """
        Detect the brand of the connected Android device.
        
        Args:
            device_id: The ADB device ID
            
        Returns:
            Brand name in lowercase (e.g., 'xiaomi', 'infinix')
        """
        # Try different properties to detect brand
        brand_properties = [
            "ro.product.brand",
            "ro.product.manufacturer",
            "ro.product.vendor.brand",
            "ro.product.system.brand"
        ]
        
        for prop in brand_properties:
            result = await self.adb_repo.execute_command(
                device_id, 
                f"getprop {prop}"
            )
            
            if result and result.strip():
                brand = result.strip().lower()
                # Return the brand if we have an implementation for it
                if brand in self.brands:
                    return brand
                
                # Check for partial matches (e.g., if device returns "xiaomi_global")
                for known_brand in self.brands.keys():
                    if known_brand in brand:
                        return known_brand
        
        # Return generic if brand couldn't be detected
        return "generic"
    
    async def create_brand_implementation(self, device_id: str) -> BaseBrand:
        """
        Create and return the appropriate brand implementation for the device.
        
        Args:
            device_id: The ADB device ID
            
        Returns:
            An implementation of BaseBrand appropriate for the device's brand
        """
        brand = await self.detect_brand(device_id)
        
        # Create the specific brand implementation if available
        if brand in self.brands:
            return self.brands[brand](self.adb_repo)
        
        # If brand is not supported, use a generic implementation
        # This can be extended later with a GenericBrand class
        return self.brands["xiaomi"](self.adb_repo)  # Default to Xiaomi for now

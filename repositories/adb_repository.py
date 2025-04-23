import asyncio
import re
from typing import List, Dict, Any, Optional

class ADBRepository:
    """Repository for executing ADB commands asynchronously."""
    
    def __init__(self, adb_path: str = "adb"):
        """
        Initialize the ADB repository.
        
        Args:
            adb_path: Path to the ADB executable (default: assumes 'adb' is in PATH)
        """
        self.adb_path = adb_path
        
    async def execute_command(self, device_id: str, command: str) -> str:
        """
        Execute an ADB shell command on the specified device.
        
        Args:
            device_id: The device identifier
            command: The shell command to execute
            
        Returns:
            The command output as a string
        """
        full_command = f"{self.adb_path} -s {device_id} shell {command}"
        try:
            process = await asyncio.create_subprocess_shell(
                full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        except FileNotFoundError:
            raise Exception(
                "ADB executable not found. Install Android platform-tools and ensure 'adb' is in PATH."
            )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error = stderr.decode('utf-8', errors='replace')
            raise Exception(f"ADB command failed: {error}")
        
        return stdout.decode('utf-8', errors='replace')
    
    async def get_connected_devices(self) -> List[str]:
        """
        Get a list of connected device IDs.
        
        Returns:
            List of device IDs
        """
        try:
            process = await asyncio.create_subprocess_shell(
                f"{self.adb_path} devices",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        except FileNotFoundError:
            raise Exception(
                "ADB executable not found. Install Android platform-tools and ensure 'adb' is in PATH."
            )
        
        stdout, _ = await process.communicate()
        output = stdout.decode('utf-8')
        
        # Parse the output to extract device IDs
        device_ids = []
        for line in output.strip().split('\n')[1:]:  # Skip the first line (header)
            if line.strip():
                parts = re.split(r'\s+', line.strip(), 1)
                if len(parts) >= 1 and 'offline' not in line:
                    device_ids.append(parts[0])
        
        return device_ids
    
    async def authorize_device(self, device_id: str) -> bool:
        """
        Request USB debugging authorization for the device.
        
        Args:
            device_id: The device identifier
            
        Returns:
            True if authorization was successful, False otherwise
        """
        # Check if the device is already authorized
        devices = await self.get_connected_devices()
        if device_id in devices:
            return True
        
        # Request authorization (this will prompt on the device)
        process = await asyncio.create_subprocess_shell(
            f"{self.adb_path} -s {device_id} shell echo 'Authorization requested'",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        await process.communicate()
        
        # Check again if the device is now authorized
        devices = await self.get_connected_devices()
        return device_id in devices
    
    async def is_device_connected(self, device_id: str) -> bool:
        """
        Check if a specific device is connected.
        
        Args:
            device_id: The device identifier
            
        Returns:
            True if the device is connected, False otherwise
        """
        devices = await self.get_connected_devices()
        return device_id in devices
        
    async def start_adb_server(self) -> None:
        """Start the ADB server if it's not already running."""
        process = await asyncio.create_subprocess_shell(
            f"{self.adb_path} start-server",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        await process.communicate()
        
    async def wait_for_device(self, timeout: int = 30) -> Optional[str]:
        """
        Wait for any device to be connected within the timeout period.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            The device ID if one is found, None if timeout
        """
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            devices = await self.get_connected_devices()
            if devices:
                return devices[0]
            
            await asyncio.sleep(1)
            
        return None

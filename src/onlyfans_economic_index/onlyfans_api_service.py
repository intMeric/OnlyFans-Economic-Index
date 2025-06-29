"""Service for OnlyFans API requests."""

import os
from typing import Dict, Any, Optional
import httpx
from dotenv import load_dotenv


class OnlyFansAPIService:
    """Service for interacting with OnlyFans API."""
    
    def __init__(self):
        """Initialize the service with API configuration."""
        load_dotenv()
        self.api_key = os.getenv("OF_API")
        if not self.api_key:
            raise ValueError("OF_API not found in environment variables")
        
        self.base_url = "https://app.onlyfansapi.com/api"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def get_profile_details(self, username: str) -> Dict[str, Any]:
        """Get OnlyFans profile details.
        
        Args:
            username: The profile username
            
        Returns:
            Dict containing profile details
            
        Raises:
            httpx.HTTPError: For HTTP errors
            ValueError: If username is empty
        """
        if not username or not username.strip():
            raise ValueError("Username cannot be empty")
        
        url = f"{self.base_url}/profiles/{username.strip()}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
    
    def get_profile_details_sync(self, username: str) -> Dict[str, Any]:
        """Synchronous version of get_profile_details.
        
        Args:
            username: The profile username
            
        Returns:
            Dict containing profile details
            
        Raises:
            httpx.HTTPError: For HTTP errors
            ValueError: If username is empty
        """
        if not username or not username.strip():
            raise ValueError("Username cannot be empty")
        
        url = f"{self.base_url}/profiles/{username.strip()}"
        
        with httpx.Client() as client:
            response = client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
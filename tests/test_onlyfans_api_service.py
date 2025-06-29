"""Tests for OnlyFans API service."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import httpx
from onlyfans_economic_index.onlyfans_api_service import OnlyFansAPIService

pytestmark = pytest.mark.asyncio


class TestOnlyFansAPIService:
    """Test cases for OnlyFansAPIService."""
    
    @patch.dict('os.environ', {'ONLYFANS_API_KEY': 'test_api_key'})
    def test_init_with_api_key(self):
        """Test service initialization with API key."""
        service = OnlyFansAPIService()
        assert service.api_key == 'test_api_key'
        assert service.base_url == 'https://app.onlyfansapi.com/api'
        assert service.headers['Authorization'] == 'Bearer test_api_key'
    
    @patch.dict('os.environ', {}, clear=True)
    def test_init_without_api_key(self):
        """Test service initialization without API key raises error."""
        with pytest.raises(ValueError, match="ONLYFANS_API_KEY not found"):
            OnlyFansAPIService()
    
    @patch.dict('os.environ', {'ONLYFANS_API_KEY': 'test_api_key'})
    @patch('httpx.AsyncClient')
    async def test_get_profile_details_success(self, mock_client):
        """Test successful profile details retrieval."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"username": "testuser"}}
        mock_response.raise_for_status.return_value = None
        
        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        service = OnlyFansAPIService()
        result = await service.get_profile_details("testuser")
        
        assert result == {"data": {"username": "testuser"}}
        mock_client_instance.get.assert_called_once_with(
            "https://app.onlyfansapi.com/api/profiles/testuser",
            headers=service.headers
        )
    
    @patch.dict('os.environ', {'ONLYFANS_API_KEY': 'test_api_key'})
    async def test_get_profile_details_empty_username(self):
        """Test profile details with empty username."""
        service = OnlyFansAPIService()
        
        with pytest.raises(ValueError, match="Username cannot be empty"):
            await service.get_profile_details("")
        
        with pytest.raises(ValueError, match="Username cannot be empty"):
            await service.get_profile_details("   ")
    
    @patch.dict('os.environ', {'ONLYFANS_API_KEY': 'test_api_key'})
    @patch('httpx.Client')
    def test_get_profile_details_sync_success(self, mock_client):
        """Test successful synchronous profile details retrieval."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"username": "testuser"}}
        mock_response.raise_for_status.return_value = None
        
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        service = OnlyFansAPIService()
        result = service.get_profile_details_sync("testuser")
        
        assert result == {"data": {"username": "testuser"}}
        mock_client_instance.get.assert_called_once_with(
            "https://app.onlyfansapi.com/api/profiles/testuser",
            headers=service.headers
        )
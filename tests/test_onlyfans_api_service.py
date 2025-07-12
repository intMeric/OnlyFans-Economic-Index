"""Tests for OnlyFans API service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from onlyfans_economic_index.onlyfans_api_service import OnlyFansAPIService

pytestmark = pytest.mark.asyncio


class TestOnlyFansAPIService:
    """Test cases for OnlyFansAPIService."""

    def test_init_default(self):
        """Test service initialization with default values."""
        service = OnlyFansAPIService()
        assert service.base_url == "https://onlyfans.com"
        assert service.api_base == "https://onlyfans.com/api2/v2"
        assert service.config["app_token"] == "33d57ade8c02dbc5a333db99ff9ae26a"
        assert service.config["x_bc"] is None

    def test_init_with_custom_user_agent(self):
        """Test service initialization with custom user agent."""
        custom_ua = "Custom User Agent"
        service = OnlyFansAPIService(user_agent=custom_ua)
        assert service.default_headers["User-Agent"] == custom_ua

    @patch("httpx.AsyncClient")
    async def test_get_init_config_success(self, mock_client):
        """Test successful config retrieval."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status.return_value = None

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        service = OnlyFansAPIService()
        result = await service.get_init_config()

        assert result == {"status": "success"}
        mock_client_instance.get.assert_called_once_with(
            "https://texts.onlyfans.com/init.json",
            headers={"origin": "https://onlyfans.com", "referer": "https://onlyfans.com/"},
        )

    @patch("httpx.Client")
    def test_get_init_config_sync_success(self, mock_client):
        """Test successful synchronous config retrieval."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status.return_value = None

        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance

        service = OnlyFansAPIService()
        result = service.get_init_config_sync()

        assert result == {"status": "success"}
        mock_client_instance.get.assert_called_once_with(
            "https://texts.onlyfans.com/init.json",
            headers={"origin": "https://onlyfans.com", "referer": "https://onlyfans.com/"},
        )

    async def test_get_profile_details_success(self):
        """Test successful profile details retrieval with mock browser."""
        service = OnlyFansAPIService(use_browser=True, use_mock=True)
        service.start_browser_session()  # Start the session explicitly
        result = await service.get_profile_details("testuser")

        expected_format = {
            "username": "testuser",
            "name": "Test User",
            "followers": "1K",
            "posts": "10",
            "bio": "Test profile",
            "avatar": "https://example.com/test.jpg",
            "is_verified": False
        }
        assert result == expected_format

    async def test_get_profile_details_empty_username(self):
        """Test profile details with empty username."""
        service = OnlyFansAPIService()

        with pytest.raises(ValueError, match="Username cannot be empty"):
            await service.get_profile_details("")

        with pytest.raises(ValueError, match="Username cannot be empty"):
            await service.get_profile_details("   ")

    @patch("httpx.Client")
    def test_get_profile_details_sync_success(self, mock_client):
        """Test successful synchronous profile details retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 123, "username": "testuser"}

        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance

        service = OnlyFansAPIService()
        result = service.get_profile_details_sync("testuser")

        assert result == {"id": 123, "username": "testuser"}
        mock_client_instance.get.assert_called_once()

    def test_set_authentication_tokens(self):
        """Test setting authentication tokens."""
        service = OnlyFansAPIService()

        service.set_authentication_tokens("test_bc", "test_sign", "test_hash")

        assert service.config["x_bc"] == "test_bc"
        assert service.config["sign"] == "test_sign"
        assert service.config["x_hash"] == "test_hash"

    def test_generate_timestamp(self):
        """Test timestamp generation."""
        service = OnlyFansAPIService()
        timestamp = service._generate_timestamp()

        assert isinstance(timestamp, str)
        assert len(timestamp) >= 13  # Unix timestamp in milliseconds
        assert timestamp.isdigit()

    def test_build_auth_headers(self):
        """Test authentication headers building."""
        service = OnlyFansAPIService()
        service.set_authentication_tokens("test_bc", "test_sign", "test_hash")

        headers = service._build_auth_headers("GET", "/test/path")

        assert headers["x-of-rev"] == service.config["x_of_rev"]
        assert headers["app-token"] == service.config["app_token"]
        assert headers["x-bc"] == "test_bc"
        assert headers["sign"] == "test_sign"
        assert headers["x-hash"] == "test_hash"
        assert "time" in headers

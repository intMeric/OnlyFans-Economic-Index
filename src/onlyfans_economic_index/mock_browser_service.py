"""Mock browser service for testing without actual browser."""

from typing import Any


class MockOnlyFansBrowserService:
    """Mock browser service for testing purposes."""

    def __init__(self, headless: bool = True):
        """Initialize mock browser service."""
        self.headless = headless
        self.session_started = False
        self.tokens = {
            "x_bc": "mock_x_bc_token",
            "sign": "mock_sign_token",
            "x_hash": "mock_x_hash_token"
        }

    def start_session(self) -> bool:
        """Mock start session."""
        self.session_started = True
        return True

    def close_session(self):
        """Mock close session."""
        self.session_started = False

    async def get_profile_data(self, username: str) -> dict[str, Any] | None:
        """Mock get profile data."""
        if not self.session_started:
            return None

        mock_profiles = {
            "iggyazalea": {
                "username": "iggyazalea",
                "name": "Iggy Azalea",
                "followers": "1.2M",
                "posts": "156",
                "bio": "Australian rapper and songwriter",
                "avatar": "https://example.com/avatar.jpg",
                "is_verified": True
            },
            "testuser": {
                "username": "testuser",
                "name": "Test User",
                "followers": "1K",
                "posts": "10",
                "bio": "Test profile",
                "avatar": "https://example.com/test.jpg",
                "is_verified": False
            }
        }

        return mock_profiles.get(username.lower())

    def get_tokens(self) -> dict[str, str]:
        """Get mock tokens."""
        return self.tokens.copy()

    async def refresh_tokens(self) -> bool:
        """Mock refresh tokens."""
        return True

    def are_tokens_valid(self) -> bool:
        """Mock token validation."""
        return True

    def __enter__(self):
        """Context manager entry."""
        self.start_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        del exc_type, exc_val, exc_tb  # Unused parameters
        self.close_session()

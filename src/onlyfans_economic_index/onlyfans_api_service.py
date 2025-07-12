"""Service for OnlyFans API requests."""

import time
from typing import Any

import httpx

from .browser_service import OnlyFansBrowserService
from .mock_browser_service import MockOnlyFansBrowserService


class OnlyFansAPIService:
    """
    Service for interacting with OnlyFans API.

    WARNING: This class is provided for educational purposes only.
    Make sure to comply with OnlyFans terms of service and applicable laws.
    """

    def __init__(self, user_agent: str = None, use_browser: bool = True, use_mock: bool = False):
        """
        Initialize the API service.

        Args:
            user_agent: User-Agent to use for requests
            use_browser: Whether to use browser service for token management
            use_mock: Whether to use mock browser service for testing
        """
        self.base_url = "https://onlyfans.com"
        self.api_base = f"{self.base_url}/api2/v2"
        self.use_browser = use_browser
        self.use_mock = use_mock
        self.browser_service: OnlyFansBrowserService | None = None

        self.default_headers = {
            "User-Agent": user_agent or "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "fr-FR,fr;q=0.8",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Brave";v="138"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Linux"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-gpc": "1",
            "Content-Type": "application/json"
        }

        self.config = {
            "x_of_rev": "202507041642-6716789133",
            "app_token": "33d57ade8c02dbc5a333db99ff9ae26a",
            "x_bc": None,
            "sign": None,
            "x_hash": None
        }

        if self.use_browser:
            if self.use_mock:
                self.browser_service = MockOnlyFansBrowserService(headless=True)
            else:
                self.browser_service = OnlyFansBrowserService(headless=True)

    async def get_init_config(self) -> dict[str, Any] | None:
        """
        Get initial configuration from texts.onlyfans.com/init.json

        Returns:
            JSON configuration or None on error
        """
        try:
            url = "https://texts.onlyfans.com/init.json"
            headers = {
                "origin": "https://onlyfans.com",
                "referer": "https://onlyfans.com/",
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()

        except httpx.RequestError as e:
            print(f"Error getting configuration: {e}")
            return None

    def get_init_config_sync(self) -> dict[str, Any] | None:
        """
        Synchronous version of get_init_config.

        Returns:
            JSON configuration or None on error
        """
        try:
            url = "https://texts.onlyfans.com/init.json"
            headers = {
                "origin": "https://onlyfans.com",
                "referer": "https://onlyfans.com/",
            }

            with httpx.Client() as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()

        except httpx.RequestError as e:
            print(f"Error getting configuration: {e}")
            return None

    def _generate_timestamp(self) -> str:
        """Generate timestamp in milliseconds."""
        return str(int(time.time() * 1000))

    def _build_auth_headers(
        self, method: str, path: str, body: str = ""
    ) -> dict[str, str]:
        """
        Build authentication headers.

        WARNING: This method is incomplete as OnlyFans exact signing
        algorithm is not public.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path
            body: Request body for POST/PUT

        Returns:
            Authentication headers
        """
        del method, path, body  # Unused parameters
        timestamp = self._generate_timestamp()

        auth_headers = {
            "x-of-rev": self.config["x_of_rev"],
            "app-token": self.config["app_token"],
            "time": timestamp,
        }

        if self.config.get("x_bc"):
            auth_headers["x-bc"] = self.config["x_bc"]
        if self.config.get("sign"):
            auth_headers["sign"] = self.config["sign"]
        if self.config.get("x_hash"):
            auth_headers["x-hash"] = self.config["x_hash"]

        return auth_headers

    async def get_profile_details(self, username: str) -> dict[str, Any] | None:
        """
        Get user profile details.

        Args:
            username: OnlyFans username

        Returns:
            Profile data or None on error
        """
        if not username or not username.strip():
            raise ValueError("Username cannot be empty")

        if self.use_browser and self.browser_service:
            return await self._get_profile_with_browser(username)
        else:
            return await self._get_profile_with_api(username)

    async def _get_profile_with_browser(self, username: str) -> dict[str, Any] | None:
        """
        Get profile details using browser service.

        Args:
            username: OnlyFans username

        Returns:
            Profile data or None on error
        """
        if not self.browser_service:
            return None

        try:
            profile_data = self.browser_service.get_profile_data(username)
            return profile_data
        except Exception as e:
            print(f"Browser error: {e}")
            return None

    async def _get_profile_with_api(self, username: str) -> dict[str, Any] | None:
        """
        Get profile details using API (fallback method).

        Args:
            username: OnlyFans username

        Returns:
            Profile data or None on error
        """
        if not self._are_tokens_valid():
            if self.use_browser and self.browser_service:
                if not self._refresh_tokens_from_browser():
                    print("Could not refresh tokens from browser")
                    return None
            else:
                print("No valid tokens available")
                return None

        try:
            url = f"{self.api_base}/users/{username.strip()}"

            auth_headers = self._build_auth_headers(
                "GET", f"/api2/v2/users/{username.strip()}"
            )
            auth_headers["Referer"] = f"{self.base_url}/{username.strip()}"

            headers = {**self.default_headers, **auth_headers}

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"HTTP Error {response.status_code}: {response.text}")
                    if response.status_code == 401 and self.use_browser:
                        if self._refresh_tokens_from_browser():
                            return await self._get_profile_with_api(username)
                    return None

        except httpx.RequestError as e:
            print(f"Request error: {e}")
            return None

    def get_profile_details_sync(self, username: str) -> dict[str, Any] | None:
        """
        Synchronous version of get_profile_details.

        Args:
            username: OnlyFans username

        Returns:
            Profile data or None on error
        """
        if not username or not username.strip():
            raise ValueError("Username cannot be empty")

        try:
            url = f"{self.api_base}/users/{username.strip()}"

            auth_headers = self._build_auth_headers(
                "GET", f"/api2/v2/users/{username.strip()}"
            )
            auth_headers["Referer"] = f"{self.base_url}/{username.strip()}"

            headers = {**self.default_headers, **auth_headers}

            with httpx.Client() as client:
                response = client.get(url, headers=headers)

                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"HTTP Error {response.status_code}: {response.text}")
                    return None

        except httpx.RequestError as e:
            print(f"Request error: {e}")
            return None


    def set_authentication_tokens(self, x_bc: str, sign: str, x_hash: str):
        """
        Set authentication tokens.

        These tokens must be obtained through legal authentication
        on the OnlyFans platform.

        Args:
            x_bc: x-bc token
            sign: Signature
            x_hash: x-hash token
        """
        self.config["x_bc"] = x_bc
        self.config["sign"] = sign
        self.config["x_hash"] = x_hash

    def _are_tokens_valid(self) -> bool:
        """
        Check if current tokens are valid.

        Returns:
            True if tokens exist and are not empty, False otherwise
        """
        required_tokens = ['x_bc', 'sign', 'x_hash']
        return all(self.config.get(token) for token in required_tokens)

    def _refresh_tokens_from_browser(self) -> bool:
        """
        Refresh tokens using browser service.

        Returns:
            True if tokens were refreshed successfully, False otherwise
        """
        if not self.browser_service:
            return False

        try:
            if self.browser_service.refresh_tokens():
                tokens = self.browser_service.get_tokens()
                if tokens:
                    self.config["x_bc"] = tokens.get("x_bc")
                    self.config["sign"] = tokens.get("sign")
                    self.config["x_hash"] = tokens.get("x_hash")
                    return True
            return False
        except Exception as e:
            print(f"Error refreshing tokens: {e}")
            return False

    def start_browser_session(self) -> bool:
        """
        Start browser session for token management.

        Returns:
            True if session started successfully, False otherwise
        """
        if not self.browser_service:
            return False

        return self.browser_service.start_session()

    def close_browser_session(self):
        """Close browser session."""
        if self.browser_service:
            self.browser_service.close_session()

    def __enter__(self):
        """Context manager entry."""
        if self.use_browser:
            self.start_browser_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        del exc_type, exc_val, exc_tb  # Unused parameters
        if self.use_browser:
            self.close_browser_session()


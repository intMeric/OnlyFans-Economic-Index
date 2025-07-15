"""Browser service for OnlyFans data retrieval using Selenium."""

import asyncio
import json
from typing import Any

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


class OnlyFansBrowserService:
    """Service for retrieving OnlyFans data using headless browser."""

    def __init__(self, headless: bool = True):
        """
        Initialize the browser service.

        Args:
            headless: Whether to run browser in headless mode
        """
        self.headless = headless
        self.driver: webdriver.Chrome | None = None
        self.tokens: dict[str, str] = {}
        self.session_started = False

    def _setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome driver with appropriate options."""
        options = Options()

        if self.headless:
            options.add_argument("--headless")

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # Enable performance logging to capture network requests
        options.add_experimental_option('perfLoggingPrefs', {
            'enableNetwork': True,
            'enablePage': False
        })
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

        user_agent = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        )
        options.add_argument(f"--user-agent={user_agent}")

        try:
            # Try to get latest ChromeDriver
            service = Service(ChromeDriverManager(chrome_type="chromium").install())
        except Exception as e:
            print(f"Error installing ChromeDriver for Chromium: {e}")
            try:
                # Fallback to regular Chrome driver
                service = Service(ChromeDriverManager().install())
            except Exception as e2:
                print(f"Error installing ChromeDriver fallback: {e2}")
                return None

        try:
            driver = webdriver.Chrome(service=service, options=options)
            script = ("Object.defineProperty(navigator, 'webdriver', "
                     "{get: () => undefined})")
            driver.execute_script(script)
            return driver
        except Exception as e:
            print(f"Error creating Chrome driver: {e}")
            try:
                options.binary_location = "/snap/bin/chromium"
                driver = webdriver.Chrome(service=service, options=options)
                script = ("Object.defineProperty(navigator, 'webdriver', "
                     "{get: () => undefined})")
                driver.execute_script(script)
                return driver
            except Exception as e2:
                print(f"Error with Chromium snap: {e2}")
                try:
                    flatpak_path = (
                        "/var/lib/flatpak/app/org.chromium.Chromium/"
                        "current/active/export/bin/org.chromium.Chromium"
                    )
                    options.binary_location = flatpak_path
                    driver = webdriver.Chrome(service=service, options=options)
                    script = ("Object.defineProperty(navigator, 'webdriver', "
                     "{get: () => undefined})")
                    driver.execute_script(script)
                    return driver
                except Exception as e3:
                    print(f"Error with Chromium flatpak: {e3}")
                    return None

    def start_session(self) -> bool:
        """
        Start browser session.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.driver = self._setup_driver()
            self.session_started = self.driver is not None

            if self.session_started:
                # Enable network domain for CDP to capture requests
                try:
                    self.driver.execute_cdp_cmd('Network.enable', {})
                    self.driver.execute_cdp_cmd('Runtime.enable', {})
                    print("✓ Network and Runtime domains enabled for request "
                         "interception")
                except Exception as e:
                    print(f"Warning: Could not enable CDP domains: {e}")

            return self.session_started
        except WebDriverException as e:
            print(f"Error starting browser session: {e}")
            self.session_started = False
            return False

    def close_session(self):
        """Close browser session."""
        if self.driver:
            self.driver.quit()
            self.driver = None
        self.session_started = False

    def _extract_tokens_from_network(self) -> dict[str, str]:
        """
        Extract authentication tokens from network requests.

        Returns:
            Dictionary containing tokens
        """
        tokens = {}

        if not self.driver:
            return tokens

        try:
            logs = self.driver.get_log('performance')

            for log in logs:
                try:
                    # Performance logs have nested JSON structure
                    outer_message = json.loads(log['message'])
                    inner_message = outer_message.get('message', {})

                    if inner_message.get('method') == 'Network.requestWillBeSent':
                        params = inner_message.get('params', {})
                        request = params.get('request', {})
                        headers = request.get('headers', {})

                        if 'x-bc' in headers:
                            tokens['x_bc'] = headers['x-bc']
                        if 'sign' in headers:
                            tokens['sign'] = headers['sign']
                        if 'x-hash' in headers:
                            tokens['x_hash'] = headers['x-hash']
                except json.JSONDecodeError:
                    continue
                except Exception:
                    continue

        except Exception as e:
            print(f"Error extracting tokens: {e}")

        return tokens

    def navigate_to_profile(self, username: str) -> bool:
        """
        Navigate to user profile page.

        Args:
            username: OnlyFans username

        Returns:
            True if successful, False otherwise
        """
        if not self.driver:
            print("Browser session not started")
            return False

        try:
            url = f"https://onlyfans.com/{username}"
            self.driver.get(url)

            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            return True

        except TimeoutException:
            print(f"Timeout while loading profile: {username}")
            return False
        except WebDriverException as e:
            print(f"Error navigating to profile: {e}")
            return False

    async def get_profile_data(self, username: str) -> dict[str, Any] | None:
        """
        Get profile data by navigating to profile page and intercepting API calls.

        Args:
            username: OnlyFans username

        Returns:
            Profile data or None if failed
        """
        try:
            # Set up network interception BEFORE navigation
            api_data = await self._setup_and_capture_api(username)
            if api_data:
                print(f"✅ Intercepted API data for {username}")
                return self._format_api_data(api_data, username)

            # Fallback to DOM scraping
            print(f"⚠ No API data intercepted for {username}, using DOM extraction")
            return self._extract_dom_data(username)

        except Exception as e:
            print(f"Error extracting profile data: {e}")
            return None

    async def _setup_and_capture_api(self, username: str) -> dict[str, Any] | None:
        """
        Set up network interception and navigate to capture API response.

        Args:
            username: OnlyFans username

        Returns:
            API response data or None if not captured
        """
        try:
            print(f"🔧 Setting up API interception for {username}")

            # Clear any existing logs before starting
            self.driver.get_log('performance')

            # Navigate to the profile page to trigger API calls
            if not self.navigate_to_profile(username):
                return None

            # Wait actively for the specific API request with multiple checks
            return await self._wait_for_api_request(username)

        except Exception as e:
            print(f"❌ Error in setup_and_capture_api: {e}")
            return None

    async def _wait_for_api_request(self, username: str) -> dict[str, Any] | None:
        """
        Actively wait for the specific API request to appear in logs.

        Args:
            username: OnlyFans username

        Returns:
            API response data or None if not found
        """
        try:
            target_url_pattern = f"api2/v2/users/{username}"
            print(f"⏳ Waiting for API request: {target_url_pattern}")

            max_wait_time = 30  # 30 seconds max wait
            check_interval = 1  # Check every 1 second
            checks_done = 0
            max_checks = max_wait_time // check_interval

            while checks_done < max_checks:
                checks_done += 1
                print(
                    f"🔍 Check {checks_done}/{max_checks} - Looking for API request..."
                )

                # Get fresh performance logs
                logs = self.driver.get_log('performance')

                if logs:
                    api_data = self._search_logs_for_api_response(
                        logs, username, target_url_pattern
                    )
                    if api_data:
                        return api_data

                # Wait before next check
                await asyncio.sleep(check_interval)

                # Show progress every 5 checks
                if checks_done % 5 == 0:
                    print(
                        f"⏰ Still waiting... ({checks_done * check_interval}s elapsed)"
                    )

            print(f"⏰ Timeout reached after {max_wait_time}s - No API request found")
            return None

        except Exception as e:
            print(f"❌ Error waiting for API request: {e}")
            return None

    def _search_logs_for_api_response(
        self, logs: list, username: str, target_pattern: str
    ) -> dict[str, Any] | None:
        """
        Search through performance logs for the target API response.

        Args:
            logs: Performance logs to search
            username: Username to look for
            target_pattern: URL pattern to match

        Returns:
            API response data or None if not found
        """
        try:
            for log in logs:
                try:
                    # Performance logs have nested JSON structure:
                    # {"message": {"method": ..., "params": ...}}
                    outer_message = json.loads(log['message'])
                    inner_message = outer_message.get('message', {})
                    method = inner_message.get('method')

                    if method == 'Network.responseReceived':
                        params = inner_message.get('params', {})
                        response = params.get('response', {})
                        url = response.get('url', '')
                        status = response.get('status')

                        # Check if this is our target API endpoint
                        if target_pattern in url and status == 200:
                            print(f"🎯 Found target API request: {url}")

                            request_id = params.get('requestId')
                            if request_id:
                                try:
                                    # Get the response body
                                    response_body = self.driver.execute_cdp_cmd(
                                        'Network.getResponseBody', {
                                        'requestId': request_id
                                    })

                                    if response_body and 'body' in response_body:
                                        body_text = response_body['body']

                                        # Handle base64 encoding if necessary
                                        if response_body.get('base64Encoded'):
                                            import base64
                                            body_text = base64.b64decode(
                                                body_text
                                            ).decode('utf-8')

                                        # Parse and validate the JSON data
                                        api_data = json.loads(body_text)

                                        # Verify this is actually user data
                                        # for our target
                                        if (
                                            isinstance(api_data, dict)
                                            and api_data.get('username') == username
                                        ):
                                            print(
                                                f"✅ Successfully captured API data for "
                                                f"{username}!"
                                            )
                                            print(
                                                f"   📊 Posts: {api_data.get('postsCount', 0)}"
                                            )
                                            print(
                                                f"   📷 Photos: {api_data.get('photosCount', 0)}"
                                            )
                                            print(
                                                f"   🎥 Videos: {api_data.get('videosCount', 0)}"
                                            )
                                            print(
                                                f"   💰 Price: ${api_data.get('subscribePrice', 0)}"
                                            )
                                            return api_data
                                        else:
                                            print(
                                                "⚠ API response doesn't match expected user data"
                                            )

                                except Exception as e:
                                    print(f"❌ Error processing response body: {e}")
                                    continue

                except json.JSONDecodeError:
                    continue
                except Exception:
                    continue

            return None

        except Exception as e:
            print(f"❌ Error searching logs: {e}")
            return None


    def _format_api_data(self, api_data: dict, username: str) -> dict[str, Any]:
        """
        Format API response data into our standard format.

        Args:
            api_data: Raw API response data
            username: Username

        Returns:
            Formatted profile data
        """
        return {
            'username': username,
            'name': api_data.get('name', username),
            'is_verified': api_data.get('isVerified', False),
            'avatar': api_data.get('avatar', ''),
            'header': api_data.get('header', ''),
            'about': api_data.get('about', ''),
            'posts_count': api_data.get('postsCount', 0),
            'photos_count': api_data.get('photosCount', 0),
            'videos_count': api_data.get('videosCount', 0),
            'subscribe_price': api_data.get('subscribePrice', 0),
            'join_date': api_data.get('joinDate', ''),
            'last_seen': api_data.get('lastSeen', ''),
            'favorites_count': api_data.get('favoritesCount', 0),
            'favorited_count': api_data.get('favoritedCount', 0),
            'can_earn': api_data.get('canEarn', False),
            'tips_enabled': api_data.get('tipsEnabled', False),
            'tips_min': api_data.get('tipsMin', 0),
            'tips_max': api_data.get('tipsMax', 0),
            'subscriber_data': {
                'subscribed_by': api_data.get('subscribedBy', False),
                'subscribed_on': api_data.get('subscribedOn', False),
                'can_chat': api_data.get('canChat', False),
            },
            'media_counts': {
                'posts': api_data.get('postsCount', 0),
                'archived_posts': api_data.get('archivedPostsCount', 0),
                'photos': api_data.get('photosCount', 0),
                'videos': api_data.get('videosCount', 0),
                'audios': api_data.get('audiosCount', 0),
            },
            'raw_api_data': api_data  # Keep original data for debugging
        }

    def _extract_dom_data(self, username: str) -> dict[str, Any] | None:
        """
        Extract profile data from DOM elements (fallback method).

        Args:
            username: OnlyFans username

        Returns:
            Profile data from DOM or None if failed
        """
        try:
            profile_data = {
                'username': username,
                'name': username,
                'is_verified': False,
                'avatar': '',
                'about': '',
                'posts_count': 0,
                'photos_count': 0,
                'videos_count': 0,
                'subscribe_price': 0,
            }

            # Try to extract JSON data from page source
            try:
                page_source = self.driver.page_source
                # Look for JSON data in script tags or window objects
                json_data = self._extract_json_from_source(page_source, username)
                if json_data:
                    print("✓ Found JSON data in page source!")
                    return self._format_api_data(json_data, username)
            except Exception as e:
                print(f"DEBUG: Could not analyze page source: {e}")

            # Try to find profile name with multiple selectors
            name_selectors = [
                'h1',
                'h2',
                'h3',
                '.profile-name',
                '[data-testid="profile-name"]',
                '.m-username',
                '.profile-title',
                '.user-name',
                'title'
            ]

            for selector in name_selectors:
                try:
                    name_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    text = name_element.text.strip()
                    if text and text != username:
                        profile_data['name'] = text
                        break
                except Exception:
                    continue

            # Try to find avatar with expanded selectors
            avatar_selectors = [
                'img[src*="avatar"]',
                'img[alt*="avatar"]',
                '.profile-avatar img',
                '.avatar img',
                '[data-testid="profile-avatar"] img',
                '.m-avatar img',
                '.user-avatar img',
                'img[src*="profile"]'
            ]

            for selector in avatar_selectors:
                try:
                    avatar = self.driver.find_element(By.CSS_SELECTOR, selector)
                    src = avatar.get_attribute('src')
                    if src:
                        profile_data['avatar'] = src
                        break
                except Exception:
                    continue

            # Check verification status with expanded selectors
            verification_selectors = [
                '.verified-badge',
                '.m-verified',
                '[data-testid="verified-badge"]',
                '.icon-verified',
                '.verified',
                'svg[aria-label*="verified"]',
                'svg[aria-label*="Verified"]',
                '[title*="verified"]',
                '[title*="Verified"]'
            ]

            for selector in verification_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    profile_data['is_verified'] = True
                    break
                except Exception:
                    continue

            # Try to find post/media counts
            count_selectors = [
                '[data-testid*="count"]',
                '.count',
                '.media-count',
                '.posts-count',
                '.stat-value',
                '.number'
            ]

            for selector in count_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text.isdigit():
                            # Could be posts, followers, etc.
                            pass
                except Exception:
                    continue

            return profile_data

        except Exception as e:
            print(f"Error extracting DOM data: {e}")
            return None

    def _extract_json_from_source(self, page_source: str, username: str) -> dict[str, Any] | None:
        """
        Extract JSON data from page source.

        Args:
            page_source: HTML source of the page
            username: Username to look for

        Returns:
            JSON data if found, None otherwise
        """
        import re

        try:
            # Common patterns where user data might be stored
            patterns = [
                # Look for window.__INITIAL_STATE__ or similar
                r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
                r'window\.__NUXT__\s*=\s*({.+?});',
                r'window\.__APP_STATE__\s*=\s*({.+?});',

                # Look for user data in script tags
                r'"username"\s*:\s*"' + re.escape(username) + r'"[^}]+}[^}]*}',
                r'"name"\s*:\s*"[^"]*"[^}]*"username"\s*:\s*"' + re.escape(username) + r'"[^}]*}',

                # Look for API response data
                r'{"id":\d+,"name":"[^"]*","username":"' + re.escape(username) + r'"[^}]+}',
            ]

            for pattern in patterns:
                matches = re.findall(pattern, page_source, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    try:
                        # If it's a full object, try to parse it
                        if match.startswith('{'):
                            data = json.loads(match)
                            # Look for user data in the parsed object
                            user_data = self._find_user_data(data, username)
                            if user_data:
                                return user_data
                    except json.JSONDecodeError:
                        continue

            # Try to find embedded JSON containing user data
            # Look for JSON objects that contain the username
            json_pattern = r'\{[^{}]*"username"\s*:\s*"' + re.escape(username) + r'"[^{}]*\}'
            matches = re.findall(json_pattern, page_source)

            for match in matches:
                try:
                    data = json.loads(match)
                    if data.get('username') == username:
                        print("DEBUG: Found user JSON data in page source")
                        return data
                except json.JSONDecodeError:
                    continue

            return None

        except Exception as e:
            print(f"Error extracting JSON from source: {e}")
            return None

    def _find_user_data(self, data: dict, username: str) -> dict[str, Any] | None:
        """
        Recursively search for user data in a nested dictionary.

        Args:
            data: Dictionary to search
            username: Username to look for

        Returns:
            User data if found, None otherwise
        """
        try:
            # Direct match
            if isinstance(data, dict) and data.get('username') == username:
                return data

            # Search in nested dictionaries and lists
            if isinstance(data, dict):
                for _key, value in data.items():
                    if isinstance(value, dict | list):
                        result = self._find_user_data(value, username)
                        if result:
                            return result
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict | list):
                        result = self._find_user_data(item, username)
                        if result:
                            return result

            return None

        except Exception as e:
            print(f"Error searching user data: {e}")
            return None


    def get_tokens(self) -> dict[str, str]:
        """
        Get current authentication tokens.

        Returns:
            Dictionary containing tokens
        """
        return self.tokens.copy()

    async def refresh_tokens(self) -> bool:
        """
        Refresh authentication tokens by navigating to OnlyFans.

        Returns:
            True if tokens were refreshed, False otherwise
        """
        if not self.driver:
            if not self.start_session():
                return False

        try:
            self.driver.get("https://onlyfans.com")

            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            await asyncio.sleep(2)

            new_tokens = self._extract_tokens_from_network()

            if new_tokens:
                self.tokens.update(new_tokens)
                return True

            return False

        except Exception as e:
            print(f"Error refreshing tokens: {e}")
            return False

    def are_tokens_valid(self) -> bool:
        """
        Check if current tokens are valid.

        Returns:
            True if tokens exist and are not empty, False otherwise
        """
        required_tokens = ['x_bc', 'sign', 'x_hash']
        return all(self.tokens.get(token) for token in required_tokens)

    def __enter__(self):
        """Context manager entry."""
        self.start_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        del exc_type, exc_val, exc_tb  # Unused parameters
        self.close_session()

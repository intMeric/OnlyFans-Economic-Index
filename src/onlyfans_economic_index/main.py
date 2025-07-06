"""Main module for OnlyFans Economic Index."""

import asyncio

from .onlyfans_api_service import OnlyFansAPIService


def hello(name: str = "World") -> str:
    """Return a greeting message.

    Args:
        name: The name to greet (default: "World")

    Returns:
        Formatted greeting message
    """
    return f"Hello, {name}!"


async def test_api_client() -> None:
    """Test the OnlyFans API client."""
    client = OnlyFansAPIService()

    print("Testing OnlyFans API client...")

    # Test configuration retrieval
    config = await client.get_init_config()
    if config:
        print("✓ Configuration retrieved successfully")
    else:
        print("✗ Failed to retrieve configuration")

    # Test profile retrieval (will likely fail without proper auth)
    username = "iggyazalea"
    profile = await client.get_profile_details(username)
    if profile:
        print(f"✓ Profile for {username} retrieved successfully")
    else:
        print(f"✗ Failed to retrieve profile for {username} (expected without auth)")


def main() -> None:
    """Main entry point."""
    print("OnlyFans Economic Index")
    print("=" * 30)

    # Run API test
    asyncio.run(test_api_client())

    print("\nNote: Full functionality requires proper authentication tokens.")
    print("Use set_authentication_tokens() method to set x_bc, sign, and x_hash.")


if __name__ == "__main__":
    main()

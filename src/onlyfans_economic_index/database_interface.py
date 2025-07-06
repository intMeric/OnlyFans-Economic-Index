"""Abstract database interface for OnlyFans profile storage."""

from abc import ABC, abstractmethod
from typing import Any


class DatabaseInterface(ABC):
    """Abstract interface for database operations."""

    @abstractmethod
    async def create_profiles_table(self) -> None:
        """Create profiles table if it doesn't exist."""
        pass

    @abstractmethod
    async def insert_profile(self, username: str, profile_data: dict[str, Any]) -> None:
        """Insert or update a profile in the database.
        
        Args:
            username: The profile username
            profile_data: The profile data to store
        """
        pass

    @abstractmethod
    async def get_profile(self, username: str) -> dict[str, Any] | None:
        """Get a profile from the database.
        
        Args:
            username: The profile username
            
        Returns:
            Profile data if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_all_profiles(self) -> list[dict[str, Any]]:
        """Get all profiles from the database.
        
        Returns:
            List of all profiles
        """
        pass

    @abstractmethod
    async def delete_profile(self, username: str) -> bool:
        """Delete a profile from the database.
        
        Args:
            username: The username to delete
            
        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test database connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close database connection."""
        pass

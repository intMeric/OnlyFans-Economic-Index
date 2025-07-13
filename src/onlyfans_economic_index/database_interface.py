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
    async def insert_profile_snapshot(
        self, username: str, profile_data: dict[str, Any]
    ) -> bool:
        """Insert a new profile snapshot with timestamp if none exists for today.

        Args:
            username: The profile username
            profile_data: The profile data to store

        Returns:
            True if snapshot was inserted, False if one already exists for today
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

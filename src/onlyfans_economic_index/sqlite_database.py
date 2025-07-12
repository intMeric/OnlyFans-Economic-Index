"""SQLite database implementation for OnlyFans profiles."""

import json
import sqlite3
from datetime import datetime
from typing import Any

from .database_interface import DatabaseInterface


class SQLiteDatabase(DatabaseInterface):
    """SQLite implementation of database interface."""

    def __init__(self, db_path: str = "onlyfans_profiles.db"):
        """Initialize SQLite database.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.connection = None

    async def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
        return self.connection

    async def create_profiles_table(self) -> None:
        """Create profiles table if it doesn't exist."""
        conn = await self._get_connection()

        conn.execute("""
            CREATE TABLE IF NOT EXISTS onlyfans_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                profile_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS onlyfans_profiles_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                profile_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_profiles_username
            ON onlyfans_profiles(username)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_snapshots_username
            ON onlyfans_profiles_snapshots(username)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_snapshots_created_at
            ON onlyfans_profiles_snapshots(created_at)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_profiles_created_at
            ON onlyfans_profiles(created_at)
        """)

        conn.commit()

    async def insert_profile(self, username: str, profile_data: dict[str, Any]) -> None:
        """Insert or update a profile in the database.

        Args:
            username: The profile username
            profile_data: The profile data to store
        """
        if profile_data is None:
            raise ValueError("Profile data cannot be None")

        conn = await self._get_connection()
        now = datetime.now().isoformat()

        conn.execute("""
            INSERT OR REPLACE INTO onlyfans_profiles
            (username, profile_data, created_at, updated_at)
            VALUES (?, ?,
                COALESCE(
                    (SELECT created_at FROM onlyfans_profiles WHERE username = ?),
                    ?
                ),
                ?
            )
        """, (username, json.dumps(profile_data), username, now, now))

        conn.commit()

    async def insert_profile_snapshot(self, username: str, profile_data: dict[str, Any]) -> bool:
        """Insert a new profile snapshot with timestamp if none exists for today.

        Args:
            username: The profile username
            profile_data: The profile data from the API

        Returns:
            True if snapshot was inserted, False if one already exists for today
        """
        if profile_data is None:
            raise ValueError("Profile data cannot be None")

        conn = await self._get_connection()
        now = datetime.now()
        today_date = now.strftime('%Y-%m-%d')

        # Check if snapshot already exists for today
        cursor = conn.execute("""
            SELECT id FROM onlyfans_profiles_snapshots
            WHERE username = ? AND DATE(created_at) = ?
        """, (username, today_date))

        existing = cursor.fetchone()

        if existing:
            return False

        # Insert new snapshot
        conn.execute("""
            INSERT INTO onlyfans_profiles_snapshots
            (username, profile_data, created_at)
            VALUES (?, ?, ?)
        """, (username, json.dumps(profile_data), now.isoformat()))

        conn.commit()
        return True

    async def get_profile(self, username: str) -> dict[str, Any] | None:
        """Get a profile from the database.

        Args:
            username: The profile username

        Returns:
            Profile data if found, None otherwise
        """
        conn = await self._get_connection()

        cursor = conn.execute("""
            SELECT username, profile_data, created_at, updated_at
            FROM onlyfans_profiles
            WHERE username = ?
        """, (username,))

        row = cursor.fetchone()
        if row:
            return {
                "username": row["username"],
                "profile_data": json.loads(row["profile_data"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
        return None

    async def get_all_profiles(self) -> list[dict[str, Any]]:
        """Get all profiles from the database.

        Returns:
            List of all profiles
        """
        conn = await self._get_connection()

        cursor = conn.execute("""
            SELECT username, profile_data, created_at, updated_at
            FROM onlyfans_profiles
            ORDER BY created_at DESC
        """)

        profiles = []
        for row in cursor.fetchall():
            profiles.append({
                "username": row["username"],
                "profile_data": json.loads(row["profile_data"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            })

        return profiles

    async def delete_profile(self, username: str) -> bool:
        """Delete a profile from the database.

        Args:
            username: The username to delete

        Returns:
            True if deleted, False if not found
        """
        conn = await self._get_connection()

        cursor = conn.execute("""
            DELETE FROM onlyfans_profiles
            WHERE username = ?
        """, (username,))

        conn.commit()
        return cursor.rowcount > 0

    async def test_connection(self) -> bool:
        """Test database connection.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            conn = await self._get_connection()
            conn.execute("SELECT 1")
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None


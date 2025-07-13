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
            CREATE TABLE IF NOT EXISTS onlyfans_profiles_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                profile_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_snapshots_username
            ON onlyfans_profiles_snapshots(username)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_snapshots_created_at
            ON onlyfans_profiles_snapshots(created_at)
        """)

        conn.commit()


    async def insert_profile_snapshot(
        self, username: str, profile_data: dict[str, Any]
    ) -> bool:
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


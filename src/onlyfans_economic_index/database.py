"""Database service for managing OnlyFans profile data."""

import os
from datetime import datetime
from typing import Any

import asyncpg
from dotenv import load_dotenv

from .database_interface import DatabaseInterface


class SupabaseDatabase(DatabaseInterface):
    """Service for managing database operations with Supabase."""

    def __init__(self):
        """Initialize database service with Supabase credentials."""
        load_dotenv()
        self.password = os.getenv("SUPA_BASE_PWD")
        self.project_id = os.getenv("SUPA_BASE_ID")

        if not self.password or not self.project_id:
            raise ValueError(
                "SUPA_BASE_PWD and SUPA_BASE_ID must be set in environment"
            )

        self.connection_string = (
            f"postgresql://postgres:{self.password}@db.{self.project_id}"
            ".supabase.co:5432/postgres"
        )

    async def create_profiles_table(self) -> None:
        """Create profiles table if it doesn't exist."""
        conn = await asyncpg.connect(self.connection_string)
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS onlyfans_profiles (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    profile_data JSONB NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_profiles_username ON onlyfans_profiles(username);
                CREATE INDEX IF NOT EXISTS idx_profiles_created_at ON onlyfans_profiles(created_at);
            """)
        finally:
            await conn.close()

    async def insert_profile(self, username: str, profile_data: dict[str, Any]) -> None:
        """Insert or update a profile in the database.
        
        Args:
            username: The profile username
            profile_data: The profile data from the API
        """
        conn = await asyncpg.connect(self.connection_string)
        try:
            await conn.execute("""
                INSERT INTO onlyfans_profiles (username, profile_data, created_at, updated_at)
                VALUES ($1, $2, $3, $3)
                ON CONFLICT (username) 
                DO UPDATE SET 
                    profile_data = $2,
                    updated_at = $3
            """, username, profile_data, datetime.now())
        finally:
            await conn.close()

    async def get_profile(self, username: str) -> dict[str, Any] | None:
        """Get a profile from the database.
        
        Args:
            username: The profile username
            
        Returns:
            Profile data if found, None otherwise
        """
        conn = await asyncpg.connect(self.connection_string)
        try:
            row = await conn.fetchrow("""
                SELECT username, profile_data, created_at, updated_at
                FROM onlyfans_profiles
                WHERE username = $1
            """, username)

            if row:
                return {
                    "username": row["username"],
                    "profile_data": row["profile_data"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                }
            return None
        finally:
            await conn.close()

    async def get_all_profiles(self) -> list[dict[str, Any]]:
        """Get all profiles from the database.
        
        Returns:
            List of all profiles
        """
        conn = await asyncpg.connect(self.connection_string)
        try:
            rows = await conn.fetch("""
                SELECT username, profile_data, created_at, updated_at
                FROM onlyfans_profiles
                ORDER BY created_at DESC
            """)

            return [
                {
                    "username": row["username"],
                    "profile_data": row["profile_data"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                }
                for row in rows
            ]
        finally:
            await conn.close()

    async def test_connection(self) -> bool:
        """Test database connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            conn = await asyncpg.connect(self.connection_string)
            await conn.fetchval("SELECT 1")
            await conn.close()
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """Close database connection."""
        pass


# Backward compatibility alias
DatabaseService = SupabaseDatabase

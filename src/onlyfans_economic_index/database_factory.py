"""Database factory for creating database instances."""

import os
from typing import Literal

from .database import SupabaseDatabase
from .database_interface import DatabaseInterface
from .sqlite_database import SQLiteDatabase


def create_database(
    db_type: Literal["sqlite", "supabase"] = None, **kwargs
) -> DatabaseInterface:
    """Create a database instance based on configuration.
    
    Args:
        db_type: Type of database to create. If None, will use DB_TYPE env var
                or default to 'sqlite' for development
        **kwargs: Additional arguments passed to database constructor
        
    Returns:
        Database instance implementing DatabaseInterface
        
    Raises:
        ValueError: If invalid database type specified
    """
    if db_type is None:
        db_type = os.getenv("DB_TYPE", "sqlite").lower()

    if db_type == "sqlite":
        db_path = kwargs.get("db_path", "onlyfans_profiles.db")
        return SQLiteDatabase(db_path=db_path)
    elif db_type == "supabase":
        return SupabaseDatabase()
    else:
        raise ValueError(f"Unknown database type: {db_type}. Use 'sqlite' or 'supabase'")


def get_database() -> DatabaseInterface:
    """Get the default database instance based on environment configuration.
    
    Returns:
        Configured database instance
    """
    return create_database()

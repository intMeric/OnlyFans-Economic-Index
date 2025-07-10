"""Main module for OnlyFans Economic Index."""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import List

from .onlyfans_api_service import OnlyFansAPIService
from .database import SupabaseDatabase
from .sqlite_database import SQLiteDatabase


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


async def save_profile_snapshot(username: str, use_mock: bool = False, use_sqlite: bool = False) -> None:
    """Save a profile snapshot to database.
    
    Args:
        username: OnlyFans username to save
        use_mock: Whether to use mock data
        use_sqlite: Whether to use SQLite instead of Supabase
    """
    # Initialize database
    if use_sqlite:
        database = SQLiteDatabase()
    else:
        database = SupabaseDatabase()
    
    # Initialize API service
    api_service = OnlyFansAPIService(use_browser=True, use_mock=use_mock)
    
    try:
        # Create tables if they don't exist
        await database.create_profiles_table()
        
        # Start browser session if needed
        api_service.start_browser_session()
        
        # Get profile data
        profile_data = await api_service.get_profile_details(username)
        
        if profile_data:
            # Save snapshot
            was_saved = await database.insert_profile_snapshot(username, profile_data)
            if was_saved:
                print(f"✓ Profile snapshot saved for {username}")
            else:
                print(f"⚠ Profile snapshot already exists for {username} today")
        else:
            print(f"✗ Failed to retrieve profile for {username}")
            
    except Exception as e:
        print(f"✗ Error saving profile snapshot: {e}")
    finally:
        await database.close()
        try:
            api_service.close_browser_session()
        except Exception:
            pass


def load_usernames_from_file(file_path: str) -> List[str]:
    """Load usernames from file.
    
    Args:
        file_path: Path to file containing usernames (one per line)
        
    Returns:
        List of usernames
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            usernames = [line.strip() for line in f if line.strip()]
        return usernames
    except Exception as e:
        print(f"✗ Error reading file {file_path}: {e}")
        return []


async def save_all_profiles_from_file(file_path: str, use_mock: bool = False, use_sqlite: bool = False) -> None:
    """Save snapshots for all profiles from file.
    
    Args:
        file_path: Path to file containing usernames
        use_mock: Whether to use mock data
        use_sqlite: Whether to use SQLite instead of Supabase
    """
    usernames = load_usernames_from_file(file_path)
    
    if not usernames:
        print("No usernames found in file")
        return
    
    print(f"Found {len(usernames)} usernames to process")
    
    # Initialize database
    if use_sqlite:
        database = SQLiteDatabase()
    else:
        database = SupabaseDatabase()
    
    # Initialize API service
    api_service = OnlyFansAPIService(use_browser=True, use_mock=use_mock)
    
    try:
        # Create tables if they don't exist
        await database.create_profiles_table()
        
        # Start browser session if needed
        api_service.start_browser_session()
        
        # Process each username
        successful = 0
        skipped = 0
        failed = 0
        
        for i, username in enumerate(usernames, 1):
            print(f"[{i}/{len(usernames)}] Processing {username}...")
            
            try:
                # Get profile data
                profile_data = await api_service.get_profile_details(username)
                
                if profile_data:
                    # Save snapshot
                    was_saved = await database.insert_profile_snapshot(username, profile_data)
                    if was_saved:
                        print(f"  ✓ Snapshot saved for {username}")
                        successful += 1
                    else:
                        print(f"  ⚠ Snapshot already exists for {username} today")
                        skipped += 1
                else:
                    print(f"  ✗ Failed to retrieve profile for {username}")
                    failed += 1
                    
            except Exception as e:
                print(f"  ✗ Error processing {username}: {e}")
                failed += 1
        
        # Print summary
        print(f"\n📊 Summary:")
        print(f"  - Total profiles: {len(usernames)}")
        print(f"  - Successfully saved: {successful}")
        print(f"  - Already existed today: {skipped}")
        print(f"  - Failed: {failed}")
                
    except Exception as e:
        print(f"✗ Error processing profiles: {e}")
    finally:
        await database.close()
        try:
            api_service.close_browser_session()
        except Exception:
            pass


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="OnlyFans Economic Index")
    parser.add_argument("--test", action="store_true", help="Run API test")
    parser.add_argument("--save-profile", type=str, help="Save profile snapshot for username")
    parser.add_argument("--save-all-from-file", type=str, help="Save snapshots for all profiles from file")
    parser.add_argument("--use-mock", action="store_true", help="Use mock data")
    parser.add_argument("--use-sqlite", action="store_true", help="Use SQLite database")
    
    args = parser.parse_args()
    
    if args.save_profile:
        print(f"Saving profile snapshot for: {args.save_profile}")
        asyncio.run(save_profile_snapshot(args.save_profile, args.use_mock, args.use_sqlite))
    elif args.save_all_from_file:
        print(f"Processing all profiles from file: {args.save_all_from_file}")
        asyncio.run(save_all_profiles_from_file(args.save_all_from_file, args.use_mock, args.use_sqlite))
    elif args.test:
        print("OnlyFans Economic Index - API Test")
        print("=" * 40)
        asyncio.run(test_api_client())
        print("\nNote: Full functionality requires proper authentication tokens.")
        print("Use set_authentication_tokens() method to set x_bc, sign, and x_hash.")
    else:
        print("OnlyFans Economic Index")
        print("=" * 30)
        print("Usage:")
        print("  oei --test                           # Run API test")
        print("  oei --save-profile USERNAME          # Save profile snapshot")
        print("  oei --save-all-from-file FILE        # Save all profiles from file")
        print("  oei --save-profile USERNAME --use-mock      # Use mock data")
        print("  oei --save-profile USERNAME --use-sqlite    # Use SQLite database")
        print("  oei --save-all-from-file FILE --use-mock --use-sqlite  # Process file with mock data")


if __name__ == "__main__":
    main()

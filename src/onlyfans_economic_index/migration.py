"""Migration script for OnlyFans profiles to database."""

import asyncio
from typing import Any

from .database_factory import get_database
from .onlyfans_api_service import OnlyFansAPIService


class ProfileMigration:
    """Service for migrating OnlyFans profiles to database."""

    def __init__(self, use_mock: bool = False):
        """Initialize migration service."""
        self.api_service = OnlyFansAPIService(use_browser=True, use_mock=use_mock)
        self.db_service = get_database()

    def load_usernames_from_file(self, file_path: str) -> list[str]:
        """Load usernames from text file.
        
        Args:
            file_path: Path to the file containing usernames
            
        Returns:
            List of usernames
        """
        usernames = []
        try:
            with open(file_path, encoding='utf-8') as file:
                for line in file:
                    username = line.strip()
                    if username:
                        usernames.append(username)
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return []

        return usernames

    async def migrate_profile(self, username: str) -> bool:
        """Migrate a single profile to database.
        
        Args:
            username: The username to migrate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"Fetching profile data for: {username}")

            # Start browser session if needed
            if self.api_service.use_browser and not self.api_service.browser_service.session_started:
                if not self.api_service.start_browser_session():
                    print(f"Failed to start browser session for {username}")
                    return False

            profile_data = await self.api_service.get_profile_details(username)

            if profile_data is None:
                print(f"No profile data retrieved for {username}")
                return False

            print(f"Inserting profile data for: {username}")
            await self.db_service.insert_profile(username, profile_data)

            print(f"✅ Successfully migrated: {username}")
            return True

        except Exception as e:
            print(f"❌ Failed to migrate {username}: {str(e)}")
            return False

    async def migrate_all_profiles(self, file_path: str = "./of_user.txt") -> dict[str, Any]:
        """Migrate all profiles from file to database.
        
        Args:
            file_path: Path to the file containing usernames
            
        Returns:
            Migration results summary
        """
        db_type = type(self.db_service).__name__
        print(f"🚀 Starting OnlyFans profiles migration to {db_type}...")

        # Test database connection
        print("Testing database connection...")
        if not await self.db_service.test_connection():
            raise ConnectionError(f"Cannot connect to {db_type} database")
        print("✅ Database connection successful")

        # Create table if not exists
        print("Creating profiles table...")
        await self.db_service.create_profiles_table()
        print("✅ Profiles table ready")

        # Load usernames
        usernames = self.load_usernames_from_file(file_path)
        if not usernames:
            raise ValueError(f"No usernames found in {file_path}")

        print(f"📝 Found {len(usernames)} usernames to migrate")

        # Migrate profiles
        successful_migrations = 0
        failed_migrations = 0
        failed_usernames = []

        for i, username in enumerate(usernames, 1):
            print(f"\n[{i}/{len(usernames)}] Processing: {username}")

            success = await self.migrate_profile(username)
            if success:
                successful_migrations += 1
            else:
                failed_migrations += 1
                failed_usernames.append(username)

            # Add small delay to avoid rate limiting
            await asyncio.sleep(0.5)

        # Results summary
        results = {
            "total_profiles": len(usernames),
            "successful_migrations": successful_migrations,
            "failed_migrations": failed_migrations,
            "failed_usernames": failed_usernames,
            "success_rate": (successful_migrations / len(usernames)) * 100
        }

        print("\n🎉 Migration completed!")
        print(f"📊 Total profiles: {results['total_profiles']}")
        print(f"✅ Successful: {results['successful_migrations']}")
        print(f"❌ Failed: {results['failed_migrations']}")
        print(f"📈 Success rate: {results['success_rate']:.1f}%")

        if failed_usernames:
            print(f"\n❌ Failed usernames: {', '.join(failed_usernames)}")

        return results


async def main():
    """Main migration function."""
    migration = ProfileMigration()
    try:
        results = await migration.migrate_all_profiles()
        return results
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

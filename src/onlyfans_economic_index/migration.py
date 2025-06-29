"""Migration script for OnlyFans profiles to Supabase database."""

import asyncio
from typing import List, Dict, Any
from .onlyfans_api_service import OnlyFansAPIService
from .database import DatabaseService


class ProfileMigration:
    """Service for migrating OnlyFans profiles to database."""
    
    def __init__(self):
        """Initialize migration service."""
        self.api_service = OnlyFansAPIService()
        self.db_service = DatabaseService()
    
    def load_usernames_from_file(self, file_path: str) -> List[str]:
        """Load usernames from text file.
        
        Args:
            file_path: Path to the file containing usernames
            
        Returns:
            List of usernames
        """
        usernames = []
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
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
            profile_data = await self.api_service.get_profile_details(username)
            
            print(f"Inserting profile data for: {username}")
            await self.db_service.insert_profile(username, profile_data)
            
            print(f"✅ Successfully migrated: {username}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to migrate {username}: {str(e)}")
            return False
    
    async def migrate_all_profiles(self, file_path: str = "./of_user.txt") -> Dict[str, Any]:
        """Migrate all profiles from file to database.
        
        Args:
            file_path: Path to the file containing usernames
            
        Returns:
            Migration results summary
        """
        print("🚀 Starting OnlyFans profiles migration to Supabase...")
        
        # Test database connection
        print("Testing database connection...")
        if not await self.db_service.test_connection():
            raise ConnectionError("Cannot connect to Supabase database")
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
            await asyncio.sleep(1)
        
        # Results summary
        results = {
            "total_profiles": len(usernames),
            "successful_migrations": successful_migrations,
            "failed_migrations": failed_migrations,
            "failed_usernames": failed_usernames,
            "success_rate": (successful_migrations / len(usernames)) * 100
        }
        
        print(f"\n🎉 Migration completed!")
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
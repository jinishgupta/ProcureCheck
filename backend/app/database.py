from supabase import create_client, Client
from app.config import settings


class Database:
    """Supabase database client"""
    
    _client: Client = None
    
    @classmethod
    def get_client(cls) -> Client:
        """Get or create Supabase client"""
        if cls._client is None:
            cls._client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
        return cls._client
    
    @classmethod
    def reset_client(cls):
        """Reset the client (useful for testing)"""
        cls._client = None


# Convenience function
def get_db() -> Client:
    """Get database client"""
    return Database.get_client()

import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from db.config import settings


class Database:
    """PostgreSQL database connection manager"""
    
    @staticmethod
    @contextmanager
    def get_connection():
        """Get database connection with context manager"""
        conn = psycopg2.connect(settings.database_url)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    @contextmanager
    def get_cursor(cursor_factory=RealDictCursor):
        """Get database cursor with context manager"""
        with Database.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
            finally:
                cursor.close()


# Convenience function
def get_db():
    """Get database cursor"""
    return Database.get_cursor()

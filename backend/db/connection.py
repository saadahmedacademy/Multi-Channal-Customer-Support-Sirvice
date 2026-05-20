"""Database connection management using asyncpg."""

import asyncpg
from typing import Optional
from contextlib import asynccontextmanager
import os

class DatabaseConnection:
    """Manages PostgreSQL database connection pool."""
    
    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None
    
    async def connect(self, database_url: Optional[str] = None) -> None:
        """
        Initialize database connection pool.
        
        Args:
            database_url: PostgreSQL connection URL. Defaults to DATABASE_URL env var.
        """
        if self._pool is not None:
            return
        
        db_url = database_url or os.getenv("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        try:
            self._pool = await asyncpg.create_pool(
                dsn=db_url,
                min_size=5,
                max_size=20,
                command_timeout=5,  # 5 second timeout for queries
                max_inactive_connection_lifetime=300.0,
                statement_cache_size=0  # Required for pgbouncer (Supabase)
            )
            print(f"Database connection pool created with min_size=5, max_size=20 (optimized for 50+ concurrent users)")
        except Exception as e:
            print(f"Failed to create database connection pool: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close all database connections."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            print("Database connection pool closed")
    
    @property
    def pool(self) -> asyncpg.Pool:
        """Get the connection pool."""
        if self._pool is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._pool
    
    @asynccontextmanager
    async def acquire(self):
        """
        Acquire a connection from the pool.
        
        Usage:
            async with db.acquire() as conn:
                await conn.fetch("SELECT * FROM users")
        """
        if self._pool is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        
        conn = await self._pool.acquire()
        try:
            yield conn
        finally:
            await self._pool.release(conn)

# Global database instance
db = DatabaseConnection()

async def get_db() -> DatabaseConnection:
    """Get the global database instance."""
    return db

async def init_db(database_url: Optional[str] = None) -> None:
    """Initialize the global database connection."""
    await db.connect(database_url)

async def close_db() -> None:
    """Close the global database connection."""
    await db.disconnect()

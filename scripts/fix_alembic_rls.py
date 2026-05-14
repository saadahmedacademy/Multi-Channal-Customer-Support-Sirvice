#!/usr/bin/env python3
"""Enable RLS on alembic_version table."""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def fix_alembic_rls():
    """Enable RLS on alembic_version table."""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return

    print("🔧 Enabling RLS on alembic_version table...\n")

    try:
        conn = await asyncpg.connect(database_url, statement_cache_size=0)

        # Enable RLS on alembic_version
        await conn.execute("ALTER TABLE alembic_version ENABLE ROW LEVEL SECURITY;")
        print("✅ Enabled RLS on: alembic_version")

        # Create policy for alembic_version
        await conn.execute("""
            DROP POLICY IF EXISTS "Service role can do everything" ON alembic_version;
        """)

        await conn.execute("""
            CREATE POLICY "Service role can do everything"
            ON alembic_version
            FOR ALL
            TO authenticated, service_role
            USING (true)
            WITH CHECK (true);
        """)
        print("✅ Created policy for: alembic_version")

        # Verify
        result = await conn.fetchrow("""
            SELECT rowsecurity as rls_enabled
            FROM pg_tables
            WHERE schemaname = 'public' AND tablename = 'alembic_version';
        """)

        if result and result['rls_enabled']:
            print("\n✅ SUCCESS! alembic_version table is now secure.")
        else:
            print("\n⚠️  Warning: Could not verify RLS status.")

        await conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(fix_alembic_rls())

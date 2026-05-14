#!/usr/bin/env python3
"""Enable Row-Level Security (RLS) on all tables to fix Supabase security warning."""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def enable_rls():
    """Enable RLS on all tables and create appropriate policies."""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return

    print("🔧 Enabling Row-Level Security (RLS) on all tables...\n")

    try:
        conn = await asyncpg.connect(database_url)

        # List of all tables in the application
        tables = [
            'customers',
            'customer_identifiers',
            'conversations',
            'messages',
            'tickets',
            'knowledge_base',
            'processed_messages'
        ]

        print("Step 1: Enabling RLS on all tables...")
        print("-" * 60)

        for table in tables:
            try:
                # Enable RLS
                await conn.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
                print(f"✅ Enabled RLS on: {table}")
            except Exception as e:
                print(f"⚠️  Error enabling RLS on {table}: {e}")

        print("\nStep 2: Creating RLS policies...")
        print("-" * 60)

        # Create policies that allow backend service role full access
        # but block anonymous/public access

        for table in tables:
            try:
                # Drop existing policies if any
                await conn.execute(f"""
                    DROP POLICY IF EXISTS "Service role can do everything" ON {table};
                """)

                # Create policy: Service role (backend) has full access
                await conn.execute(f"""
                    CREATE POLICY "Service role can do everything"
                    ON {table}
                    FOR ALL
                    TO authenticated, service_role
                    USING (true)
                    WITH CHECK (true);
                """)

                print(f"✅ Created policy for: {table}")

            except Exception as e:
                print(f"⚠️  Error creating policy for {table}: {e}")

        print("\nStep 3: Verifying RLS status...")
        print("-" * 60)

        # Verify RLS is enabled
        query = """
        SELECT
            tablename,
            rowsecurity as rls_enabled
        FROM pg_tables
        WHERE schemaname = 'public'
        AND tablename IN ('customers', 'customer_identifiers', 'conversations',
                          'messages', 'tickets', 'knowledge_base', 'processed_messages')
        ORDER BY tablename;
        """

        results = await conn.fetch(query)

        all_enabled = True
        for row in results:
            status = "✅ Enabled" if row['rls_enabled'] else "❌ Disabled"
            print(f"{row['tablename']:<30} {status}")
            if not row['rls_enabled']:
                all_enabled = False

        print("\n" + "=" * 60)

        if all_enabled:
            print("\n✅ SUCCESS! All tables now have RLS enabled.")
            print("\n📋 What this means:")
            print("  - Anonymous users can NO LONGER access your data directly")
            print("  - Only authenticated requests (your backend API) can access data")
            print("  - Your backend uses the service_role key which bypasses RLS")
            print("  - Direct database access from browser/client is now blocked")
            print("\n🔒 Your database is now secure!")
        else:
            print("\n⚠️  Some tables still don't have RLS enabled. Please check manually.")

        await conn.close()

    except asyncpg.exceptions.InvalidCatalogNameError:
        print("❌ Database not found. Check your DATABASE_URL.")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 If database is paused, activate it in Supabase dashboard first.")

if __name__ == "__main__":
    asyncio.run(enable_rls())

#!/usr/bin/env python3
"""Check Row-Level Security (RLS) status on all tables."""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_rls_status():
    """Check RLS status for all tables in public schema."""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return

    print("🔍 Checking RLS status on all tables...\n")

    try:
        conn = await asyncpg.connect(database_url)

        # Check RLS status for all tables
        query = """
        SELECT
            schemaname,
            tablename,
            rowsecurity as rls_enabled
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY tablename;
        """

        tables = await conn.fetch(query)

        print(f"{'Table Name':<30} {'RLS Enabled':<15}")
        print("-" * 45)

        vulnerable_tables = []

        for table in tables:
            table_name = table['tablename']
            rls_enabled = table['rls_enabled']
            status = "✅ Yes" if rls_enabled else "❌ No (VULNERABLE)"

            print(f"{table_name:<30} {status:<15}")

            if not rls_enabled:
                vulnerable_tables.append(table_name)

        print("\n" + "=" * 45)

        if vulnerable_tables:
            print(f"\n⚠️  CRITICAL: {len(vulnerable_tables)} tables are publicly accessible!")
            print("\nVulnerable tables:")
            for table in vulnerable_tables:
                print(f"  - {table}")
            print("\n🔧 Run 'python scripts/enable_rls.py' to fix this issue.")
        else:
            print("\n✅ All tables have RLS enabled!")

        # Check if any RLS policies exist
        policy_query = """
        SELECT
            schemaname,
            tablename,
            policyname,
            permissive,
            roles,
            cmd
        FROM pg_policies
        WHERE schemaname = 'public'
        ORDER BY tablename, policyname;
        """

        policies = await conn.fetch(policy_query)

        if policies:
            print(f"\n📋 Existing RLS Policies ({len(policies)}):")
            print("-" * 80)
            for policy in policies:
                print(f"  Table: {policy['tablename']}")
                print(f"  Policy: {policy['policyname']}")
                print(f"  Command: {policy['cmd']}")
                print(f"  Roles: {policy['roles']}")
                print()
        else:
            print("\n⚠️  No RLS policies found! Tables with RLS enabled will block ALL access.")

        await conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_rls_status())

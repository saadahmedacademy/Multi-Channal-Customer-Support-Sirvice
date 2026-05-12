# Database Migrations

This directory contains Alembic database migrations for schema version control.

## Setup

1. Install dependencies:
```bash
pip install -r backend/requirements.txt
```

2. Set DATABASE_URL environment variable:
```bash
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
```

## Usage

### Apply migrations (upgrade to latest)
```bash
alembic upgrade head
```

### Revert last migration
```bash
alembic downgrade -1
```

### Check current version
```bash
alembic current
```

### View migration history
```bash
alembic history
```

### Create new migration
```bash
alembic revision -m "description of changes"
```

## Migration Files

- `env.py` - Alembic environment configuration
- `script.py.mako` - Template for new migrations
- `versions/` - Migration version files

## Initial Setup

For a fresh database, run:
```bash
# Apply all migrations
alembic upgrade head

# Seed knowledge base (optional)
python scripts/seed_knowledge_base.py
```

## Notes

- Migrations are applied automatically in order based on revision IDs
- Always test migrations on a development database first
- Each migration has `upgrade()` and `downgrade()` functions
- The `processed_messages` table is included for webhook deduplication

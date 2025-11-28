# Database Migrations

This directory contains database migration scripts for Mind Scout.

## For New Installations

No migrations needed - the database is created with the latest schema automatically via SQLAlchemy models.

## Migration Naming Convention

Migrations use numbered prefixes for ordering:

```
001_add_user_preferences.py
002_add_notification_settings.py
003_rename_column_foo.py
```

- Always use 3-digit zero-padded numbers
- Use lowercase with underscores for descriptions
- Run migrations in numerical order

## Creating a New Migration

1. Update the model in `mindscout/database.py`
2. Create a migration script with the next number: `NNN_description.py`
3. Use this template:

```python
#!/usr/bin/env python
"""Migration NNN: Brief description.

Detailed explanation of what this migration does.
"""

import sqlite3
from mindscout.config import DB_PATH


def migrate():
    """Run the migration."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check current state
    cursor.execute("PRAGMA table_info(table_name)")
    columns = [col[1] for col in cursor.fetchall()]

    # Make changes only if needed
    if "new_column" not in columns:
        print("Adding 'new_column' to table_name...")
        cursor.execute("ALTER TABLE table_name ADD COLUMN new_column TEXT")
    else:
        print("Column 'new_column' already exists - skipping")

    conn.commit()
    conn.close()
    print("✓ Migration complete")


if __name__ == "__main__":
    migrate()
```

## Running Migrations

```bash
# Run a specific migration
python migrations/001_add_user_preferences.py

# Run all migrations in order (manual for now)
for f in migrations/[0-9]*.py; do python "$f"; done
```

## Notes

- Each migration should be idempotent (safe to run multiple times)
- Always check if changes already exist before applying
- For destructive changes (dropping columns), consider data backup
- SQLite < 3.35.0 doesn't support DROP COLUMN - recreate table instead

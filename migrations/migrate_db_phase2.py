#!/usr/bin/env python
"""Database migration script for Phase 2."""

import sqlite3
from mindscout.config import DB_PATH

def migrate():
    """Add Phase 2 columns to existing articles table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if columns already exist
    cursor.execute("PRAGMA table_info(articles)")
    columns = [col[1] for col in cursor.fetchall()]

    migrations = [
        ("summary", "ALTER TABLE articles ADD COLUMN summary TEXT"),
        ("topics", "ALTER TABLE articles ADD COLUMN topics TEXT"),
        ("embedding", "ALTER TABLE articles ADD COLUMN embedding TEXT"),
        ("processed", "ALTER TABLE articles ADD COLUMN processed BOOLEAN DEFAULT 0"),
        ("processing_date", "ALTER TABLE articles ADD COLUMN processing_date DATETIME"),
    ]

    for column_name, sql in migrations:
        if column_name not in columns:
            print(f"Adding column: {column_name}")
            cursor.execute(sql)
        else:
            print(f"Column already exists: {column_name}")

    conn.commit()
    conn.close()
    print("\n✓ Database migration complete!")

if __name__ == "__main__":
    migrate()

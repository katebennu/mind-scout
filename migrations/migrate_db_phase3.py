#!/usr/bin/env python
"""Database migration script for Phase 3 - Multi-Source Integration."""

import sqlite3
from mindscout.config import DB_PATH

def migrate():
    """Add Phase 3 columns to existing articles table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if columns already exist
    cursor.execute("PRAGMA table_info(articles)")
    columns = [col[1] for col in cursor.fetchall()]

    migrations = [
        ("citation_count", "ALTER TABLE articles ADD COLUMN citation_count INTEGER"),
        ("influential_citations", "ALTER TABLE articles ADD COLUMN influential_citations INTEGER"),
        ("github_url", "ALTER TABLE articles ADD COLUMN github_url VARCHAR"),
        ("has_implementation", "ALTER TABLE articles ADD COLUMN has_implementation BOOLEAN DEFAULT 0"),
        ("paper_url_pwc", "ALTER TABLE articles ADD COLUMN paper_url_pwc VARCHAR"),
        ("hf_upvotes", "ALTER TABLE articles ADD COLUMN hf_upvotes INTEGER"),
    ]

    for column_name, sql in migrations:
        if column_name not in columns:
            print(f"Adding column: {column_name}")
            cursor.execute(sql)
        else:
            print(f"Column already exists: {column_name}")

    conn.commit()
    conn.close()
    print("\n✓ Database migration for Phase 3 complete!")
    print("\nNew fields added:")
    print("  - citation_count (from Semantic Scholar)")
    print("  - influential_citations (from Semantic Scholar)")
    print("  - github_url (from Papers with Code)")
    print("  - has_implementation (from Papers with Code)")
    print("  - paper_url_pwc (Papers with Code URL)")
    print("  - hf_upvotes (from Hugging Face)")

if __name__ == "__main__":
    migrate()

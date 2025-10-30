#!/usr/bin/env python
"""Database migration script for Phase 4 - User Profile & Recommendations."""

import sqlite3
from mindscout.config import DB_PATH

def migrate():
    """Add Phase 4 columns and tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if columns already exist in articles table
    cursor.execute("PRAGMA table_info(articles)")
    columns = [col[1] for col in cursor.fetchall()]

    # Add new columns to articles table
    article_migrations = [
        ("rating", "ALTER TABLE articles ADD COLUMN rating INTEGER"),
        ("rated_date", "ALTER TABLE articles ADD COLUMN rated_date DATETIME"),
    ]

    for column_name, sql in article_migrations:
        if column_name not in columns:
            print(f"Adding column to articles: {column_name}")
            cursor.execute(sql)
        else:
            print(f"Column already exists: {column_name}")

    # Create user_profile table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY,
            interests TEXT,
            skill_level VARCHAR,
            preferred_sources TEXT,
            daily_reading_goal INTEGER,
            created_date DATETIME,
            updated_date DATETIME
        )
    """)
    print("Created/verified user_profile table")

    # Check if a profile exists, if not create a default one
    cursor.execute("SELECT COUNT(*) FROM user_profile")
    if cursor.fetchone()[0] == 0:
        print("Creating default user profile...")
        cursor.execute("""
            INSERT INTO user_profile (interests, skill_level, preferred_sources, daily_reading_goal, created_date, updated_date)
            VALUES ('', 'intermediate', 'arxiv,semanticscholar', 5, datetime('now'), datetime('now'))
        """)
        print("Default profile created")

    conn.commit()
    conn.close()

    print("\n✓ Database migration for Phase 4 complete!")
    print("\nNew features:")
    print("  - User profile system (interests, skill level, preferences)")
    print("  - Article rating system (1-5 stars)")
    print("  - Foundation for personalized recommendations")
    print("\nNext steps:")
    print("  1. Set your interests: mindscout profile set-interests \"topics you care about\"")
    print("  2. Get recommendations: mindscout recommend")

if __name__ == "__main__":
    migrate()

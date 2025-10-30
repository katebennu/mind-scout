# Database Migrations

This directory contains database migration scripts for Mind Scout.

## Migration Scripts

- `migrate_db_phase2.py` - Adds LLM processing fields (summary, topics, embedding, processed, processing_date)
- `migrate_db_phase3.py` - Adds multi-source metadata fields (citation_count, github_url, etc.)
- `migrate_db_phase4.py` - Adds user profile and rating fields (rating, rated_date, user_profile table)

## Running Migrations

### For New Installations

No migrations needed - the database will be created with the latest schema automatically.

### For Existing Installations

If upgrading from an earlier version, run the migrations in order:

```bash
# From the project root directory
python migrations/migrate_db_phase2.py
python migrations/migrate_db_phase3.py
python migrations/migrate_db_phase4.py
```

Each script is idempotent - it checks if columns/tables already exist before adding them, so it's safe to run multiple times.

## Migration Details

### Phase 2 Migration

Adds fields for AI-powered content processing:
- `summary` - LLM-generated summary
- `topics` - Extracted topics (JSON)
- `embedding` - Vector embedding (JSON)
- `processed` - Processing status flag
- `processing_date` - When article was processed

### Phase 3 Migration

Adds fields for multi-source metadata:
- `citation_count` - Citation count from Semantic Scholar
- `influential_citations` - Influential citation count
- `github_url` - Link to code implementation
- `has_implementation` - Boolean flag
- `paper_url_pwc` - Papers with Code URL
- `hf_upvotes` - Hugging Face community upvotes

### Phase 4 Migration

Adds user profile and feedback system:
- `rating` - User rating (1-5 stars)
- `rated_date` - When user rated the article
- `user_profile` table - Stores user preferences and interests

## Creating New Migrations

When adding new database fields:

1. Update the model in `mindscout/database.py`
2. Create a new migration script `migrate_db_phaseX.py`
3. Use SQLite `PRAGMA table_info()` to check existing columns
4. Add new columns/tables only if they don't exist
5. Update this README with migration details

## Troubleshooting

**Error: "table articles has no column named X"**
- Run the appropriate migration script for that field

**Error: "table X already exists"**
- This is normal - the script checks and skips existing tables

**Want to start fresh?**
- Delete `~/.mindscout/mindscout.db`
- Restart Mind Scout - it will create a new database with latest schema

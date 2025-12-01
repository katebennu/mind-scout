# Database Migrations

Mind Scout uses Alembic for database migrations with PostgreSQL.

## Commands

```bash
# Create a new migration
make db-migrate msg="add new column"

# Apply all pending migrations
make db-upgrade

# Rollback last migration
make db-downgrade

# Show migration history
make db-history
```

## Migration Files

Migration files are stored in `alembic/versions/`. See `alembic/` directory for configuration.

## For New Installations

Run migrations to create the schema:

```bash
make db-upgrade
```

## Creating a New Migration

1. Update the model in `mindscout/database.py`
2. Generate migration: `make db-migrate msg="description of changes"`
3. Review the generated migration in `alembic/versions/`
4. Apply: `make db-upgrade`

## Notes

- Each migration should be reversible when possible
- Test migrations on a copy of production data before deploying
- Always backup database before running migrations in production

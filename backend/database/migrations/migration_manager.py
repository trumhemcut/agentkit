"""Database migration manager for AgentKit."""

from sqlalchemy import text
from database.config import engine
import logging
import os

logger = logging.getLogger(__name__)

# List of migration files in order
MIGRATIONS = [
    "001_initial_schema.sql",
]


async def run_migrations():
    """
    Run all pending database migrations asynchronously.
    
    Creates a schema_migrations table to track applied migrations.
    Only runs migrations that haven't been applied yet.
    """
    logger.info("Starting database migrations...")
    
    async with engine.begin() as conn:
        # Create migrations tracking table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Check which migrations have been applied
        result = await conn.execute(text("SELECT version FROM schema_migrations"))
        applied = {row[0] for row in result}
        
        # Run pending migrations
        migrations_dir = os.path.join(os.path.dirname(__file__))
        for idx, migration_file in enumerate(MIGRATIONS, start=1):
            if idx not in applied:
                logger.info(f"Running migration {idx}: {migration_file}")
                
                migration_path = os.path.join(migrations_dir, migration_file)
                try:
                    with open(migration_path, 'r') as f:
                        migration_sql = f.read()
                    
                    # Split SQL into individual statements (by semicolon)
                    # Remove comments and empty lines
                    statements = []
                    for statement in migration_sql.split(';'):
                        # Remove comments (lines starting with --)
                        statement_lines = [
                            line for line in statement.split('\n')
                            if not line.strip().startswith('--')
                        ]
                        statement = '\n'.join(statement_lines).strip()
                        if statement:
                            statements.append(statement)
                    
                    # Execute each statement separately (SQLite limitation)
                    for statement in statements:
                        await conn.execute(text(statement))
                    
                    # Record migration as applied
                    await conn.execute(
                        text("INSERT INTO schema_migrations (version) VALUES (:v)"),
                        {"v": idx}
                    )
                    
                    logger.info(f"✅ Migration {migration_file} applied successfully")
                except Exception as e:
                    logger.error(f"❌ Failed to apply migration {migration_file}: {e}")
                    raise
            else:
                logger.debug(f"Migration {idx}: {migration_file} already applied, skipping")
    
    logger.info("✅ Database migrations completed successfully")

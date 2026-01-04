#!/usr/bin/env python3
"""
Database migration script for AgentKit.

Run this script to apply pending database migrations.

Usage:
    python migrate.py
    
Or make it executable:
    chmod +x migrate.py
    ./migrate.py
"""

import asyncio
import logging
import sys
from database.migrations.migration_manager import run_migrations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)


async def main():
    """Run database migrations"""
    logger.info("🚀 Starting database migration process...")
    
    try:
        await run_migrations()
        logger.info("✅ All migrations completed successfully!")
        return 0
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

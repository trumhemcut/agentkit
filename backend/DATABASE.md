# Database Setup & Management

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Migrations

**IMPORTANT**: Always run migrations before starting the server:

```bash
python migrate.py
```

### 3. Start Server

```bash
python main.py
```

## Database Configuration

The database URL is configured in `config.py` via environment variable:

```python
# Default (SQLite for development)
DATABASE_URL = "sqlite+aiosqlite:///./agentkit.db"

# PostgreSQL (for production)
DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/dbname"
```

### Environment Variable

Create a `.env` file:

```bash
# SQLite (default)
DATABASE_URL=sqlite+aiosqlite:///./agentkit.db

# PostgreSQL
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/agentkit
```

## Migration Management

### Running Migrations

```bash
python migrate.py
```

Output:
```
2026-01-04 10:00:00 - __main__ - INFO - 🚀 Starting database migration process...
2026-01-04 10:00:00 - database.migrations.migration_manager - INFO - Starting database migrations...
2026-01-04 10:00:00 - database.migrations.migration_manager - INFO - Running migration 1: 001_initial_schema.sql
2026-01-04 10:00:00 - database.migrations.migration_manager - INFO - ✅ Migration 001_initial_schema.sql applied successfully
2026-01-04 10:00:00 - database.migrations.migration_manager - INFO - ✅ Database migrations completed successfully
2026-01-04 10:00:00 - __main__ - INFO - ✅ All migrations completed successfully!
```

### Migration Status

Migrations are tracked in the `schema_migrations` table:

```sql
SELECT * FROM schema_migrations;
```

### Creating New Migrations

1. Create a new SQL file in `database/migrations/`:
   ```sql
   -- 002_add_user_table.sql
   CREATE TABLE users (
       id VARCHAR(36) PRIMARY KEY,
       email VARCHAR(255) UNIQUE NOT NULL,
       created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
   );
   ```

2. Add it to `migration_manager.py`:
   ```python
   MIGRATIONS = [
       "001_initial_schema.sql",
       "002_add_user_table.sql",  # Add here
   ]
   ```

3. Run migrations:
   ```bash
   python migrate.py
   ```

## Database Schema

### Current Tables

#### `threads`
Stores conversation threads:
- `id` (VARCHAR(36), PRIMARY KEY) - UUID
- `title` (VARCHAR(255)) - Thread title
- `agent_type` (VARCHAR(50)) - "chat", "canvas", "salary_viewer"
- `model` (VARCHAR(100)) - "gpt-5-mini", "gemini-2.5-flash"
- `provider` (VARCHAR(50)) - "azure-openai", "gemini", "ollama"
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### `messages`
Stores messages in threads:
- `id` (VARCHAR(36), PRIMARY KEY) - UUID
- `thread_id` (VARCHAR(36), FOREIGN KEY) - References threads(id)
- `role` (VARCHAR(20)) - "user", "assistant"
- `content` (TEXT) - Message text
- `artifact_data` (TEXT) - JSON for A2UI artifacts
- `message_metadata` (TEXT) - JSON for metadata
- `created_at` (TIMESTAMP)

#### `schema_migrations`
Tracks applied migrations:
- `version` (INTEGER, PRIMARY KEY)
- `applied_at` (TIMESTAMP)

### Indexes

- `idx_messages_thread_id` - Fast message lookup by thread
- `idx_messages_created_at` - Chronological message ordering
- `idx_threads_created_at` - Thread creation time queries

## Development Workflow

### Option 1: Development with SQLite

```bash
# 1. Run migrations (creates agentkit.db)
python migrate.py

# 2. Start server
python main.py

# 3. Reset database (if needed)
rm agentkit.db
python migrate.py
```

### Option 2: Production with PostgreSQL

```bash
# 1. Set up PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/agentkit

# 2. Run migrations
python migrate.py

# 3. Start server
python main.py
```

## Testing

Tests use in-memory SQLite:

```bash
pytest tests/test_threads.py tests/test_messages.py -v
```

Test configuration automatically:
- Creates in-memory database
- Applies schema
- Runs tests
- Cleans up

## Troubleshooting

### Migration fails with "table already exists"

Migrations are idempotent (use `CREATE TABLE IF NOT EXISTS`). If you see this error:

1. Check `schema_migrations` table
2. Drop and recreate database
3. Run migrations again

### Database locked (SQLite)

SQLite uses file locks. If you see "database is locked":

1. Ensure no other processes are using the database
2. Close all connections
3. Restart server

### Connection refused (PostgreSQL)

1. Check PostgreSQL is running: `pg_isready`
2. Verify connection string
3. Check firewall rules

## API Endpoints

See [database-persistence-implementation.md](../.docs/2-knowledge-base/database-persistence-implementation.md) for complete API documentation.

### Quick Reference

- `POST /api/threads` - Create thread
- `GET /api/threads` - List threads
- `POST /api/threads/{id}/messages` - Create message
- `GET /api/threads/{id}/messages` - List messages

## Production Considerations

### Docker

In your `Dockerfile` or `docker-compose.yml`:

```bash
# Run migrations before starting server
CMD python migrate.py && python main.py
```

### Kubernetes

Create a Kubernetes Job for migrations:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: agentkit-migrate
spec:
  template:
    spec:
      containers:
      - name: migrate
        image: agentkit-backend
        command: ["python", "migrate.py"]
      restartPolicy: OnFailure
```

### CI/CD Pipeline

```bash
# In your CI/CD pipeline
- name: Run migrations
  run: python migrate.py
  
- name: Start server
  run: python main.py
```

## Best Practices

1. ✅ **Always backup before migrations** (production)
2. ✅ **Test migrations locally first**
3. ✅ **Run migrations before deploying code**
4. ✅ **Use connection pooling in production**
5. ✅ **Monitor database performance**
6. ❌ **Never run migrations automatically on startup** (production)
7. ❌ **Don't edit applied migrations**
8. ❌ **Don't delete migration files**

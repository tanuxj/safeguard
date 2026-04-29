import os
from tortoise import Tortoise

TORTOISE_ORM = {
    "connections": {
        "default": os.getenv("DATABASE_URL") or "postgres://tanuj:dev@db:5432/postgres"
    },
    "apps": {
        "models": {
            "models": ["app.users.models", "app.send.models", "aerich.models"],
            "default_connection": "default",
        }
    },
}


async def init_tortoise() -> None:
    """
    Initialize Tortoise ORM for standalone scripts.

    Use this in:
    - Data migration scripts
    - Admin/maintenance scripts
    - Sync scripts (ATS subprocess)

    Note: The main FastAPI app uses lifespan context manager in main.py
    and gets DB URL from config.py (single source of truth).

    Schema creation is handled by Aerich migrations (entrypoint.sh runs
    ``aerich upgrade`` before any application code). Calling
    ``generate_schemas()`` here is unnecessary and produces noisy
    CREATE TABLE IF NOT EXISTS logs in PostgreSQL on every invocation.
    """
    await Tortoise.init(config=TORTOISE_ORM)


async def close_tortoise() -> None:
    """
    Close all Tortoise ORM database connections.

    Use this to cleanup after standalone scripts or tests.
    """
    await Tortoise.close_connections()

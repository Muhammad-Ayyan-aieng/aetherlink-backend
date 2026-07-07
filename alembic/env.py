import sys
from pathlib import Path

# Add your project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Import your models
from app.core.database import Base
from app.models import *

# Exclude storage.objects table from migrations
def include_object(object, name, type_, reflected, compare_to):
    # Skip storage.objects table (managed by Supabase)
    if type_ == "table" and name == "storage.objects":
        return False
    # Skip schema-level objects from storage schema
    if type_ == "schema" and name == "storage":
        return False
    # Skip storage policy objects
    if type_ == "policy" and name.startswith("storage."):
        return False
    return True

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata
target_metadata = Base.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,  # Add this
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=False,  # Don't compare column types
            compare_server_default=False,  # Don't compare defaults
            include_object=include_object,
        )


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
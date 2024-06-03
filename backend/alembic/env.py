import os
import sys
import logging

from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool, create_engine, text
from models.user import SQLModel
from psycopg2 import DatabaseError

from alembic import context

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# overwrite sqlalchemy.url path with local environment
# check docker-compose.yml
DATABASE_URL = os.environ["DATABASE_URL"]
DATABASE_URL = DATABASE_URL.replace("%", "%%")

# sets up loggers
fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata
logger = logging.getLogger("alembic.env")


def run_migrations_offline():
    """
    Run migrations in 'offline' mode.
    """
    if os.environ.get("TESTING"):
        raise DatabaseError("Test migrations offline is not permitted.")

    context.configure(url=str(DATABASE_URL))
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """
    Run migrations in 'online' mode
    """
    TESTING = os.environ.get("TESTING")
    DB_URL = f"{DATABASE_URL}_test" if TESTING else DATABASE_URL
    # handle testing config for migrations
    if TESTING:
        # connect to primary db
        default_engine = create_engine(
            DATABASE_URL, isolation_level="AUTOCOMMIT"
        )
        # drop testing db if it exists and create a fresh one
        with default_engine.connect() as default_conn:
            default_conn.execute(text(f"DROP DATABASE IF EXISTS {DB_URL}"))
            default_conn.execute(text(f"CREATE DATABASE {DB_URL}"))
    connectable = config.attributes.get("connection", None)
    config.set_main_option("sqlalchemy.url", DB_URL)

    if connectable is None:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=None)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    logger.info("Running migrations offline")
    run_migrations_offline()
else:
    logger.info("Running migrations online")
    run_migrations_online()

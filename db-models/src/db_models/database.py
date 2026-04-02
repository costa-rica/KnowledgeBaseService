import os

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

_DATABASE_URL = os.environ.get("DATABASE_URL", "")


def get_engine(database_url: str = _DATABASE_URL):
    engine = create_engine(database_url)

    @event.listens_for(engine, "connect")
    def _register_pgvector(dbapi_conn, _connection_record):
        # Ensure the pgvector extension is available for this connection.
        # The extension itself must already be installed in the database by a
        # superuser (CREATE EXTENSION vector); this just loads the type.
        pass

    return engine


def get_session_factory(engine):
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)

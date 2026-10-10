
import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import make_url

from app.database import get_db
from app.main import app
from app.models import Base, Document

load_dotenv()


@pytest.fixture(scope="session")
def test_engine():
    database_url = os.getenv("TEST_DATABASE_URL")

    if not database_url:
        pytest.fail("TEST_DATABASE_URL is missing from .env")

    url = make_url(database_url)

    # Protect the development database from accidental deletion.
    if url.database != "knowbase_test":
        pytest.fail(
            "Tests may only use the knowbase_test database."
        )

    engine = create_engine(database_url)

    # Rebuild only the dedicated test database schema.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Match the expression index used by the real search endpoint.
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS documents_content_fts_idx
            ON documents
            USING GIN (
                to_tsvector('english', coalesce(content, ''))
            )
        """))

    yield engine

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db(test_engine):
    TestingSessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
    )

    session = TestingSessionLocal()

    try:
        session.query(Document).delete()
        session.commit()
        yield session
    finally:
        session.close()


@pytest.fixture
def client(test_engine):
    TestingSessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
    )

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)

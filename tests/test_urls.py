import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

# --- Test database (separate from your real one) ---
import os

TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:1234@localhost:5432/urlshortener_test"
)
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# --- Setup and teardown ---
@pytest.fixture(scope="function")
def db():
    # Create all tables before each test
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after each test — clean slate
        Base.metadata.drop_all(bind=engine)


# --- Override the real DB with the test DB ---
@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# --- Tests ---

def test_create_url(client):
    response = client.post("/urls", json={
        "original_url": "https://www.google.com"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["original_url"] == "https://www.google.com/"
    assert "short_code" in data
    assert len(data["short_code"]) == 6
    assert data["clicks"] == 0


def test_create_url_invalid(client):
    response = client.post("/urls", json={
        "original_url": "not-a-valid-url"
    })
    assert response.status_code == 422  # Pydantic validation error


def test_redirect_url(client):
    # First create a URL
    create = client.post("/urls", json={
        "original_url": "https://www.google.com"
    })
    short_code = create.json()["short_code"]

    # Now hit the short link
    response = client.get(f"/{short_code}", follow_redirects=False)
    assert response.status_code == 307  # redirect status


def test_redirect_url_not_found(client):
    response = client.get("/doesnotexist", follow_redirects=False)
    assert response.status_code == 404


def test_get_all_urls(client):
    # Create two URLs
    client.post("/urls", json={"original_url": "https://www.google.com"})
    client.post("/urls", json={"original_url": "https://www.github.com"})

    response = client.get("/urls/all")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_delete_url(client):
    # Create a URL first
    create = client.post("/urls", json={
        "original_url": "https://www.google.com"
    })
    url_id = create.json()["id"]

    # Delete it
    response = client.delete(f"/urls/{url_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "URL deleted successfully"

    # Make sure it's actually gone
    all_urls = client.get("/urls/all")
    assert len(all_urls.json()) == 0


def test_delete_url_not_found(client):
    response = client.delete("/urls/999")
    assert response.status_code == 404

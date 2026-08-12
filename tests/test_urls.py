import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.auth import COOKIE_NAME, create_session_token
from app.limiter import limiter

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
    limiter._storage.reset()

    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app, base_url="https://testserver")
    test_client.cookies.set(COOKIE_NAME, create_session_token(), path="/")
    yield test_client
    app.dependency_overrides.clear()


# --- Tests ---

def test_owner_routes_require_login(client):
    client.cookies.clear()
    assert client.get("/dashboard", follow_redirects=False).status_code == 303
    assert client.get("/urls/all").status_code == 401
    assert client.delete("/urls/999").status_code == 401


def test_admin_rejects_wrong_password(client):
    client.cookies.clear()
    response = client.post("/admin/login", json={"password": "wrong-password"})
    assert response.status_code == 401


def test_admin_can_login_and_logout(client):
    client.cookies.clear()
    login = client.post("/admin/login", json={"password": "test-admin-password"})
    assert login.status_code == 200
    assert client.get("/dashboard").status_code == 200
    assert client.post("/admin/logout").status_code == 200
    assert client.get("/dashboard", follow_redirects=False).status_code == 303


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


@pytest.mark.parametrize("destination", [
    "http://localhost:8000/admin",
    "http://127.0.0.1/private",
    "http://10.0.0.1/private",
    "http://169.254.169.254/latest/meta-data",
    "https://user:password@example.com/private",
])
def test_create_url_rejects_unsafe_destination(client, destination):
    response = client.post("/urls", json={"original_url": destination})
    assert response.status_code == 422


def test_create_url_reuses_existing_destination(client):
    first = client.post("/urls", json={"original_url": "https://example.com/page"})
    second = client.post("/urls", json={"original_url": "https://example.com/page"})
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["short_code"] == second.json()["short_code"]


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


def test_paginated_url_list(client):
    client.post("/urls", json={"original_url": "https://www.google.com"})
    client.post("/urls", json={"original_url": "https://www.github.com"})
    response = client.get("/admin/urls?page=1&page_size=1")
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert response.json()["pages"] == 2
    assert len(response.json()["items"]) == 1


def test_admin_cleanup_requires_login(client):
    client.cookies.clear()
    response = client.post("/admin/urls/cleanup", json={"older_than_days": 30})
    assert response.status_code == 401


def test_favicon_is_not_treated_as_short_code(client):
    response = client.get("/favicon.ico")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")


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

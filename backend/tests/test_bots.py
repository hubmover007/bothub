import pytest
from datetime import datetime
from uuid import uuid4, UUID

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.config import settings


# Create test database engine
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def client():
    """Create a test client with fresh database."""
    # Create tables
    Base.metadata.create_all(bind=engine)

    with TestClient(app) as test_client:
        yield test_client

    # Drop tables after test
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_bot_data():
    """Sample bot data for testing."""
    return {
        "bot_id": "test-bot-001",
        "bot_name": "Test Bot",
        "owner_id": str(uuid4()),
        "description": "A test bot",
        "capabilities": {"can_chat": True, "can_search": False},
        "endpoint": "https://example.com/bot",
        "version": "1.0.0"
    }


@pytest.fixture
def auth_headers():
    """Create authorization headers with a test token."""
    # Create a test token
    from app.core.security import create_access_token
    test_user_id = uuid4()
    token = create_access_token(data={"sub": str(test_user_id)})
    return {"Authorization": f"Bearer {token}"}


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test health check returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "docs" in data


class TestBotRegistration:
    """Tests for bot registration endpoint."""

    def test_register_bot_success(self, client, sample_bot_data, auth_headers):
        """Test successful bot registration."""
        response = client.post(
            "/api/v1/bots/register",
            json=sample_bot_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["bot_id"] == sample_bot_data["bot_id"]
        assert data["bot_name"] == sample_bot_data["bot_name"]
        assert data["status"] == "offline"
        assert "id" in data
        assert "created_at" in data

    def test_register_bot_duplicate(self, client, sample_bot_data, auth_headers):
        """Test registering duplicate bot_id fails."""
        # Register first bot
        response = client.post(
            "/api/v1/bots/register",
            json=sample_bot_data,
            headers=auth_headers
        )
        assert response.status_code == 201

        # Try to register again with same bot_id
        response = client.post(
            "/api/v1/bots/register",
            json=sample_bot_data,
            headers=auth_headers
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_register_bot_unauthorized(self, client, sample_bot_data):
        """Test registration without auth fails."""
        response = client.post("/api/v1/bots/register", json=sample_bot_data)
        assert response.status_code == 403


class TestBotHeartbeat:
    """Tests for bot heartbeat endpoint."""

    def test_heartbeat_success(self, client, sample_bot_data, auth_headers):
        """Test successful heartbeat update."""
        # First register a bot
        client.post(
            "/api/v1/bots/register",
            json=sample_bot_data,
            headers=auth_headers
        )

        # Send heartbeat
        heartbeat_data = {
            "status": "online",
            "capabilities": {"can_chat": True, "can_search": True},
            "version": "1.1.0"
        }
        response = client.post(
            f"/api/v1/bots/{sample_bot_data['bot_id']}/heartbeat",
            json=heartbeat_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert data["version"] == "1.1.0"
        assert data["last_heartbeat_at"] is not None

    def test_heartbeat_not_found(self, client):
        """Test heartbeat for non-existent bot."""
        response = client.post(
            "/api/v1/bots/non-existent-bot/heartbeat",
            json={"status": "online"}
        )
        assert response.status_code == 404


class TestBotList:
    """Tests for bot list endpoint."""

    def test_list_bots_empty(self, client):
        """Test listing bots when empty."""
        response = client.get("/api/v1/bots")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1

    def test_list_bots_with_data(self, client, sample_bot_data, auth_headers):
        """Test listing bots with data."""
        # Register a bot
        client.post(
            "/api/v1/bots/register",
            json=sample_bot_data,
            headers=auth_headers
        )

        response = client.get("/api/v1/bots")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] == 1
        assert data["items"][0]["bot_id"] == sample_bot_data["bot_id"]

    def test_list_bots_pagination(self, client, auth_headers):
        """Test bot list pagination."""
        # Register multiple bots
        for i in range(5):
            bot_data = {
                "bot_id": f"test-bot-{i:03d}",
                "bot_name": f"Test Bot {i}",
                "owner_id": str(uuid4())
            }
            client.post(
                "/api/v1/bots/register",
                json=bot_data,
                headers=auth_headers
            )

        # Test page size
        response = client.get("/api/v1/bots?page_size=2")
        data = response.json()
        assert len(data["items"]) == 2
        assert data["pages"] == 3

        # Test page number
        response = client.get("/api/v1/bots?page=2&page_size=2")
        data = response.json()
        assert data["page"] == 2

    def test_list_bots_filter_by_status(self, client, sample_bot_data, auth_headers):
        """Test filtering bots by status."""
        # Register bot
        client.post(
            "/api/v1/bots/register",
            json=sample_bot_data,
            headers=auth_headers
        )

        # Update status via heartbeat
        client.post(
            f"/api/v1/bots/{sample_bot_data['bot_id']}/heartbeat",
            json={"status": "online"}
        )

        # Filter by online status
        response = client.get("/api/v1/bots?status=online")
        data = response.json()
        assert len(data["items"]) == 1

        # Filter by offline status
        response = client.get("/api/v1/bots?status=offline")
        data = response.json()
        assert len(data["items"]) == 0

    def test_list_bots_search(self, client, auth_headers):
        """Test searching bots."""
        # Register bots with different names
        bot1 = {
            "bot_id": "search-bot-001",
            "bot_name": "Alpha Bot",
            "owner_id": str(uuid4()),
            "description": "First bot"
        }
        bot2 = {
            "bot_id": "search-bot-002",
            "bot_name": "Beta Bot",
            "owner_id": str(uuid4()),
            "description": "Second bot"
        }

        client.post("/api/v1/bots/register", json=bot1, headers=auth_headers)
        client.post("/api/v1/bots/register", json=bot2, headers=auth_headers)

        # Search by name
        response = client.get("/api/v1/bots?search=Alpha")
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["bot_name"] == "Alpha Bot"


class TestBotDetail:
    """Tests for bot detail endpoint."""

    def test_get_bot_success(self, client, sample_bot_data, auth_headers):
        """Test getting bot details."""
        # Register bot
        client.post(
            "/api/v1/bots/register",
            json=sample_bot_data,
            headers=auth_headers
        )

        # Get bot details
        response = client.get(f"/api/v1/bots/{sample_bot_data['bot_id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["bot_id"] == sample_bot_data["bot_id"]
        assert data["bot_name"] == sample_bot_data["bot_name"]

    def test_get_bot_not_found(self, client):
        """Test getting non-existent bot."""
        response = client.get("/api/v1/bots/non-existent-bot")
        assert response.status_code == 404


class TestBotUpdate:
    """Tests for bot update endpoint."""

    def test_update_bot_success(self, client, sample_bot_data, auth_headers):
        """Test successful bot update."""
        # Register bot
        client.post(
            "/api/v1/bots/register",
            json=sample_bot_data,
            headers=auth_headers
        )

        # Update bot
        update_data = {
            "bot_name": "Updated Bot Name",
            "description": "Updated description"
        }
        response = client.patch(
            f"/api/v1/bots/{sample_bot_data['bot_id']}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["bot_name"] == "Updated Bot Name"
        assert data["description"] == "Updated description"

    def test_update_bot_not_found(self, client, auth_headers):
        """Test updating non-existent bot."""
        response = client.patch(
            "/api/v1/bots/non-existent-bot",
            json={"bot_name": "New Name"},
            headers=auth_headers
        )
        assert response.status_code == 404


class TestBotDelete:
    """Tests for bot delete endpoint."""

    def test_delete_bot_success(self, client, sample_bot_data, auth_headers):
        """Test successful bot deletion."""
        # Register bot
        client.post(
            "/api/v1/bots/register",
            json=sample_bot_data,
            headers=auth_headers
        )

        # Delete bot
        response = client.delete(
            f"/api/v1/bots/{sample_bot_data['bot_id']}",
            headers=auth_headers
        )
        assert response.status_code == 204

        # Verify bot is deleted
        response = client.get(f"/api/v1/bots/{sample_bot_data['bot_id']}")
        assert response.status_code == 404

    def test_delete_bot_not_found(self, client, auth_headers):
        """Test deleting non-existent bot."""
        response = client.delete(
            "/api/v1/bots/non-existent-bot",
            headers=auth_headers
        )
        assert response.status_code == 404

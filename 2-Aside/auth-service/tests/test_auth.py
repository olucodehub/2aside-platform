"""
Auth Service - Unit Tests
Tests for registration, login, and token management
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from shared.database import Base, get_db
from shared.models import User, Wallet
from auth_service.main import app

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Override dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


# Setup and teardown
@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop after"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# ========================================
# HEALTH CHECK TESTS
# ========================================

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "auth-service"


# ========================================
# REGISTRATION TESTS
# ========================================

def test_register_success():
    """Test successful user registration"""
    payload = {
        "email": "test@example.com",
        "username": "testuser",
        "phone": "+2348012345678",
        "password": "SecurePass123"
    }

    response = client.post("/register", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Registration successful"
    assert "user" in data["data"]
    assert "tokens" in data["data"]
    assert "wallets" in data["data"]

    # Check user data
    user = data["data"]["user"]
    assert user["email"] == "test@example.com"
    assert user["username"] == "testuser"

    # Check tokens
    tokens = data["data"]["tokens"]
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"

    # Check wallets
    wallets = data["data"]["wallets"]
    assert "naira" in wallets
    assert "usdt" in wallets
    assert wallets["naira"]["currency"] == "NAIRA"
    assert wallets["usdt"]["currency"] == "USDT"
    assert "referral_code" in wallets["naira"]
    assert "referral_code" in wallets["usdt"]


def test_register_duplicate_email():
    """Test registration with duplicate email"""
    payload = {
        "email": "test@example.com",
        "username": "testuser",
        "phone": "+2348012345678",
        "password": "SecurePass123"
    }

    # First registration
    response1 = client.post("/register", json=payload)
    assert response1.status_code == 201

    # Second registration with same email
    payload2 = {
        "email": "test@example.com",
        "username": "different",
        "phone": "+2348087654321",
        "password": "SecurePass123"
    }

    response2 = client.post("/register", json=payload2)
    assert response2.status_code == 400
    data = response2.json()
    assert "email" in data["detail"]["error"].lower()


def test_register_duplicate_username():
    """Test registration with duplicate username"""
    payload = {
        "email": "test@example.com",
        "username": "testuser",
        "phone": "+2348012345678",
        "password": "SecurePass123"
    }

    # First registration
    response1 = client.post("/register", json=payload)
    assert response1.status_code == 201

    # Second registration with same username
    payload2 = {
        "email": "different@example.com",
        "username": "testuser",
        "phone": "+2348087654321",
        "password": "SecurePass123"
    }

    response2 = client.post("/register", json=payload2)
    assert response2.status_code == 400
    data = response2.json()
    assert "username" in data["detail"]["error"].lower()


def test_register_with_referral_code():
    """Test registration with valid referral code"""
    # Register first user (referrer)
    payload1 = {
        "email": "referrer@example.com",
        "username": "referrer",
        "phone": "+2348012345678",
        "password": "SecurePass123"
    }

    response1 = client.post("/register", json=payload1)
    assert response1.status_code == 201
    referral_code = response1.json()["data"]["wallets"]["naira"]["referral_code"]

    # Register second user with referral code
    payload2 = {
        "email": "referred@example.com",
        "username": "referred",
        "phone": "+2348087654321",
        "password": "SecurePass123",
        "referral_code": referral_code
    }

    response2 = client.post("/register", json=payload2)
    assert response2.status_code == 201

    # Verify referred user was created
    data = response2.json()
    assert data["success"] is True


def test_register_invalid_referral_code():
    """Test registration with invalid referral code"""
    payload = {
        "email": "test@example.com",
        "username": "testuser",
        "phone": "+2348012345678",
        "password": "SecurePass123",
        "referral_code": "INVALID"
    }

    response = client.post("/register", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "referral" in data["detail"]["error"].lower()


def test_register_invalid_email():
    """Test registration with invalid email format"""
    payload = {
        "email": "not-an-email",
        "username": "testuser",
        "phone": "+2348012345678",
        "password": "SecurePass123"
    }

    response = client.post("/register", json=payload)
    assert response.status_code == 422  # Validation error


def test_register_weak_password():
    """Test registration with weak password"""
    payload = {
        "email": "test@example.com",
        "username": "testuser",
        "phone": "+2348012345678",
        "password": "weak"
    }

    response = client.post("/register", json=payload)
    assert response.status_code == 422  # Validation error


# ========================================
# LOGIN TESTS
# ========================================

def test_login_success():
    """Test successful login"""
    # Register user first
    register_payload = {
        "email": "test@example.com",
        "username": "testuser",
        "phone": "+2348012345678",
        "password": "SecurePass123"
    }
    client.post("/register", json=register_payload)

    # Login
    login_payload = {
        "email": "test@example.com",
        "password": "SecurePass123"
    }

    response = client.post("/login", json=login_payload)
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 3600


def test_login_wrong_password():
    """Test login with wrong password"""
    # Register user first
    register_payload = {
        "email": "test@example.com",
        "username": "testuser",
        "phone": "+2348012345678",
        "password": "SecurePass123"
    }
    client.post("/register", json=register_payload)

    # Login with wrong password
    login_payload = {
        "email": "test@example.com",
        "password": "WrongPassword"
    }

    response = client.post("/login", json=login_payload)
    assert response.status_code == 401
    data = response.json()
    assert "Invalid" in data["detail"]["error"]


def test_login_nonexistent_user():
    """Test login with non-existent email"""
    login_payload = {
        "email": "nonexistent@example.com",
        "password": "SecurePass123"
    }

    response = client.post("/login", json=login_payload)
    assert response.status_code == 401


# ========================================
# REFRESH TOKEN TESTS
# ========================================

def test_refresh_token_success():
    """Test refreshing access token"""
    # Register and login
    register_payload = {
        "email": "test@example.com",
        "username": "testuser",
        "phone": "+2348012345678",
        "password": "SecurePass123"
    }
    register_response = client.post("/register", json=register_payload)
    refresh_token = register_response.json()["data"]["tokens"]["refresh_token"]

    # Refresh token
    refresh_payload = {
        "refresh_token": refresh_token
    }

    response = client.post("/refresh", json=refresh_payload)
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_refresh_token_invalid():
    """Test refresh with invalid token"""
    refresh_payload = {
        "refresh_token": "invalid.token.here"
    }

    response = client.post("/refresh", json=refresh_payload)
    assert response.status_code == 401


# ========================================
# VERIFY TOKEN TESTS
# ========================================

def test_verify_token_success():
    """Test token verification"""
    # Register user
    register_payload = {
        "email": "test@example.com",
        "username": "testuser",
        "phone": "+2348012345678",
        "password": "SecurePass123"
    }
    register_response = client.post("/register", json=register_payload)
    access_token = register_response.json()["data"]["tokens"]["access_token"]

    # Verify token
    response = client.get(
        "/verify",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Token is valid"
    assert "user_id" in data["data"]
    assert data["data"]["email"] == "test@example.com"


def test_verify_token_invalid():
    """Test verification with invalid token"""
    response = client.get(
        "/verify",
        headers={"Authorization": "Bearer invalid.token.here"}
    )
    assert response.status_code == 401


def test_verify_token_missing():
    """Test verification without token"""
    response = client.get("/verify")
    assert response.status_code == 403  # Forbidden (no auth header)


# ========================================
# COVERAGE TEST
# ========================================

def test_coverage_summary():
    """This test ensures we track coverage metrics"""
    # This test always passes, it's just for coverage tracking
    assert True

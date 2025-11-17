"""
User Service - Unit Tests
Tests for user profile management and referrals
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from shared.database import Base, get_db
from shared.models import User, Wallet
from shared.auth import create_access_token
from shared.constants import CurrencyType
from user_service.main import app

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def create_test_user(db):
    """Helper to create test user with wallets"""
    from shared.utils import generate_referral_code, hash_password
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="test@example.com",
        username="testuser",
        phone="+2348012345678",
        password_hash=hash_password("SecurePass123")
    )
    db.add(user)

    naira_wallet = Wallet(
        id=uuid.uuid4(),
        user_id=user_id,
        currency=CurrencyType.NAIRA,
        balance=1000.00,
        referral_code=generate_referral_code()
    )
    usdt_wallet = Wallet(
        id=uuid.uuid4(),
        user_id=user_id,
        currency=CurrencyType.USDT,
        balance=500.00,
        referral_code=generate_referral_code()
    )
    db.add(naira_wallet)
    db.add(usdt_wallet)
    db.commit()
    return user, naira_wallet, usdt_wallet

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "user-service"

def test_get_current_user_profile():
    db = TestingSessionLocal()
    user, _, _ = create_test_user(db)
    token = create_access_token(data={"sub": str(user.id)})

    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["user"]["email"] == "test@example.com"
    assert "wallets" in data["data"]
    db.close()

def test_update_user_profile():
    db = TestingSessionLocal()
    user, _, _ = create_test_user(db)
    token = create_access_token(data={"sub": str(user.id)})

    payload = {"username": "newusername", "phone": "+2348087654321"}
    response = client.put("/me", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["user"]["username"] == "newusername"
    db.close()

def test_change_password():
    db = TestingSessionLocal()
    user, _, _ = create_test_user(db)
    token = create_access_token(data={"sub": str(user.id)})

    payload = {"current_password": "SecurePass123", "new_password": "NewSecure456"}
    response = client.put("/password", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["message"] == "Password changed successfully"
    db.close()

def test_get_referral_codes():
    db = TestingSessionLocal()
    user, naira_wallet, usdt_wallet = create_test_user(db)
    token = create_access_token(data={"sub": str(user.id)})

    response = client.get("/referral-codes", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["referral_codes"]["naira"] == naira_wallet.referral_code
    assert data["data"]["referral_codes"]["usdt"] == usdt_wallet.referral_code
    db.close()

def test_get_referral_stats():
    db = TestingSessionLocal()
    user, _, _ = create_test_user(db)
    token = create_access_token(data={"sub": str(user.id)})

    response = client.get("/referral-stats", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "referral_stats" in data["data"]
    assert data["data"]["referral_stats"]["naira"]["total_referrals"] == 0
    db.close()

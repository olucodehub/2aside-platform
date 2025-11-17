"""
Wallet Service - Unit Tests
Tests for wallet management and transactions
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
from shared.models import User, Wallet, Transaction
from shared.auth import create_access_token
from shared.constants import CurrencyType, TransactionType
from shared.utils import generate_referral_code, hash_password
from wallet_service.main import app

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

def create_test_user_with_wallets(db):
    """Helper to create test user with wallets"""
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
        balance=10000.00,
        total_deposited=15000.00,
        total_won=5000.00,
        total_withdrawn=10000.00,
        referral_code=generate_referral_code()
    )
    usdt_wallet = Wallet(
        id=uuid.uuid4(),
        user_id=user_id,
        currency=CurrencyType.USDT,
        balance=500.00,
        total_deposited=600.00,
        total_won=100.00,
        total_withdrawn=200.00,
        referral_code=generate_referral_code()
    )
    db.add(naira_wallet)
    db.add(usdt_wallet)
    db.commit()
    return user, naira_wallet, usdt_wallet

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "wallet-service"

def test_get_all_wallets():
    db = TestingSessionLocal()
    user, _, _ = create_test_user_with_wallets(db)
    token = create_access_token(data={"sub": str(user.id)})

    response = client.get("/wallets", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]["wallets"]) == 2
    db.close()

def test_get_wallet_by_currency():
    db = TestingSessionLocal()
    user, naira_wallet, _ = create_test_user_with_wallets(db)
    token = create_access_token(data={"sub": str(user.id)})

    response = client.get("/wallets/NAIRA", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["wallet"]["currency"] == "NAIRA"
    assert data["data"]["wallet"]["balance"] == "10000.0"
    db.close()

def test_get_balance():
    db = TestingSessionLocal()
    user, _, _ = create_test_user_with_wallets(db)
    token = create_access_token(data={"sub": str(user.id)})

    response = client.get("/balance/NAIRA", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["currency"] == "NAIRA"
    assert float(data["balance"]) == 10000.00
    db.close()

def test_switch_currency():
    db = TestingSessionLocal()
    user, _, usdt_wallet = create_test_user_with_wallets(db)
    token = create_access_token(data={"sub": str(user.id)})

    payload = {"currency": "USDT"}
    response = client.post("/switch-currency", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["active_wallet"]["currency"] == "USDT"
    db.close()

def test_get_transaction_history():
    db = TestingSessionLocal()
    user, naira_wallet, _ = create_test_user_with_wallets(db)

    # Create test transactions
    txn1 = Transaction(
        id=uuid.uuid4(),
        wallet_id=naira_wallet.id,
        transaction_type=TransactionType.DEPOSIT,
        amount=5000.00,
        balance_before=5000.00,
        balance_after=10000.00,
        description="Test deposit"
    )
    db.add(txn1)
    db.commit()

    token = create_access_token(data={"sub": str(user.id)})

    response = client.get("/transactions/NAIRA", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "meta" in data
    assert len(data["data"]) >= 1
    db.close()

def test_get_wallet_stats():
    db = TestingSessionLocal()
    user, _, _ = create_test_user_with_wallets(db)
    token = create_access_token(data={"sub": str(user.id)})

    response = client.get("/stats/NAIRA", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    stats = data["data"]["statistics"]
    assert stats["currency"] == "NAIRA"
    assert "total_deposited" in stats
    assert "total_won" in stats
    assert "net_profit" in stats
    db.close()

def test_invalid_currency():
    db = TestingSessionLocal()
    user, _, _ = create_test_user_with_wallets(db)
    token = create_access_token(data={"sub": str(user.id)})

    response = client.get("/balance/INVALID", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 400
    db.close()

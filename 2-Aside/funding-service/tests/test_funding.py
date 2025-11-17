"""
Funding Service - Unit Tests
Tests for P2P funding/withdrawal matching
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os
import uuid
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from shared.database import Base, get_db
from shared.models import User, Wallet, FundingRequest, WithdrawalRequest, FundingMatch
from shared.auth import create_access_token
from shared.constants import CurrencyType, FundingRequestStatus, WithdrawalRequestStatus
from shared.utils import generate_referral_code, hash_password
from funding_service.main import app

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

def create_test_user_with_balance(db, balance=10000.00, currency=CurrencyType.NAIRA):
    """Helper to create test user with wallet"""
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email=f"test{user_id}@example.com",
        username=f"testuser{user_id}",
        phone="+2348012345678",
        password_hash=hash_password("SecurePass123")
    )
    db.add(user)

    wallet = Wallet(
        id=uuid.uuid4(),
        user_id=user_id,
        currency=currency,
        balance=balance,
        total_deposited=0,
        total_withdrawn=0,
        referral_code=generate_referral_code()
    )
    db.add(wallet)
    db.commit()
    return user, wallet

# ========================================
# HEALTH CHECK
# ========================================

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "funding-service"

# ========================================
# FUNDING REQUEST TESTS
# ========================================

def test_create_funding_request():
    db = TestingSessionLocal()
    user, wallet = create_test_user_with_balance(db)
    token = create_access_token(data={"sub": str(user.id)})

    payload = {"amount": 5000.00, "currency": "NAIRA"}
    response = client.post(
        "/funding/request",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "funding_request" in data["data"]
    assert data["data"]["funding_request"]["amount"] == "5000.0"
    db.close()

def test_create_funding_request_below_minimum():
    db = TestingSessionLocal()
    user, wallet = create_test_user_with_balance(db)
    token = create_access_token(data={"sub": str(user.id)})

    payload = {"amount": 500.00, "currency": "NAIRA"}  # Below minimum (1000)
    response = client.post(
        "/funding/request",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 400
    db.close()

def test_get_my_funding_requests():
    db = TestingSessionLocal()
    user, wallet = create_test_user_with_balance(db)

    # Create a funding request
    funding_req = FundingRequest(
        id=uuid.uuid4(),
        wallet_id=wallet.id,
        amount=5000.00,
        currency=CurrencyType.NAIRA,
        status=FundingRequestStatus.PENDING,
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    db.add(funding_req)
    db.commit()

    token = create_access_token(data={"sub": str(user.id)})
    response = client.get(
        "/funding/my-requests",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1
    db.close()

# ========================================
# WITHDRAWAL REQUEST TESTS
# ========================================

def test_create_withdrawal_request():
    db = TestingSessionLocal()
    user, wallet = create_test_user_with_balance(db, balance=10000.00)
    token = create_access_token(data={"sub": str(user.id)})

    payload = {"amount": 5000.00, "currency": "NAIRA"}
    response = client.post(
        "/withdrawal/request",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "withdrawal_request" in data["data"]
    db.close()

def test_create_withdrawal_request_insufficient_balance():
    db = TestingSessionLocal()
    user, wallet = create_test_user_with_balance(db, balance=1000.00)
    token = create_access_token(data={"sub": str(user.id)})

    payload = {"amount": 5000.00, "currency": "NAIRA"}  # More than balance
    response = client.post(
        "/withdrawal/request",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 400
    assert "Insufficient balance" in response.json()["detail"]["error"]
    db.close()

def test_get_my_withdrawal_requests():
    db = TestingSessionLocal()
    user, wallet = create_test_user_with_balance(db, balance=10000.00)

    # Create a withdrawal request
    withdrawal_req = WithdrawalRequest(
        id=uuid.uuid4(),
        wallet_id=wallet.id,
        amount=5000.00,
        currency=CurrencyType.NAIRA,
        status=WithdrawalRequestStatus.PENDING,
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    db.add(withdrawal_req)
    db.commit()

    token = create_access_token(data={"sub": str(user.id)})
    response = client.get(
        "/withdrawal/my-requests",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1
    db.close()

# ========================================
# MATCHING TESTS
# ========================================

def test_automatic_matching():
    """Test that funding and withdrawal requests are automatically matched"""
    db = TestingSessionLocal()

    # Create funder
    funder, funder_wallet = create_test_user_with_balance(db, balance=0)
    funder_token = create_access_token(data={"sub": str(funder.id)})

    # Create withdrawer
    withdrawer, withdrawer_wallet = create_test_user_with_balance(db, balance=10000.00)
    withdrawer_token = create_access_token(data={"sub": str(withdrawer.id)})

    # Withdrawer creates withdrawal request
    withdrawal_payload = {"amount": 5000.00, "currency": "NAIRA"}
    withdrawal_response = client.post(
        "/withdrawal/request",
        json=withdrawal_payload,
        headers={"Authorization": f"Bearer {withdrawer_token}"}
    )
    assert withdrawal_response.status_code == 201

    # Funder creates funding request (should auto-match)
    funding_payload = {"amount": 5000.00, "currency": "NAIRA"}
    funding_response = client.post(
        "/funding/request",
        json=funding_payload,
        headers={"Authorization": f"Bearer {funder_token}"}
    )

    assert funding_response.status_code == 201
    data = funding_response.json()
    assert data["data"]["funding_request"]["matched"] is True
    assert data["data"]["funding_request"]["match_id"] is not None

    db.close()

# ========================================
# PROOF UPLOAD/CONFIRM TESTS
# ========================================

def test_upload_proof():
    db = TestingSessionLocal()

    # Create match
    funder, funder_wallet = create_test_user_with_balance(db)
    withdrawer, withdrawer_wallet = create_test_user_with_balance(db, balance=10000.00)

    match = FundingMatch(
        id=uuid.uuid4(),
        funder_wallet_id=funder_wallet.id,
        withdrawer_wallet_id=withdrawer_wallet.id,
        amount=5000.00,
        currency=CurrencyType.NAIRA,
        status="matched",
        proof_uploaded=False,
        proof_confirmed=False
    )
    db.add(match)
    db.commit()

    funder_token = create_access_token(data={"sub": str(funder.id)})

    # Upload proof
    response = client.post(
        f"/match/{match.id}/upload-proof?proof_url=https://example.com/proof.jpg",
        headers={"Authorization": f"Bearer {funder_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "proof_url" in data["data"]

    db.close()

def test_confirm_proof():
    db = TestingSessionLocal()

    # Create match with proof already uploaded
    funder, funder_wallet = create_test_user_with_balance(db, balance=0)
    withdrawer, withdrawer_wallet = create_test_user_with_balance(db, balance=10000.00)

    match = FundingMatch(
        id=uuid.uuid4(),
        funder_wallet_id=funder_wallet.id,
        withdrawer_wallet_id=withdrawer_wallet.id,
        amount=5000.00,
        currency=CurrencyType.NAIRA,
        status="proof_uploaded",
        proof_uploaded=True,
        proof_confirmed=False,
        proof_url="https://example.com/proof.jpg"
    )
    db.add(match)

    # Create funding and withdrawal requests linked to match
    funding_req = FundingRequest(
        id=uuid.uuid4(),
        wallet_id=funder_wallet.id,
        amount=5000.00,
        currency=CurrencyType.NAIRA,
        status=FundingRequestStatus.MATCHED,
        match_id=match.id,
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    withdrawal_req = WithdrawalRequest(
        id=uuid.uuid4(),
        wallet_id=withdrawer_wallet.id,
        amount=5000.00,
        currency=CurrencyType.NAIRA,
        status=WithdrawalRequestStatus.MATCHED,
        match_id=match.id,
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    db.add(funding_req)
    db.add(withdrawal_req)
    db.commit()

    withdrawer_token = create_access_token(data={"sub": str(withdrawer.id)})

    # Confirm proof
    response = client.post(
        f"/match/{match.id}/confirm-proof",
        headers={"Authorization": f"Bearer {withdrawer_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Payment confirmed successfully. Transaction completed!"

    # Verify balances updated
    db.refresh(funder_wallet)
    db.refresh(withdrawer_wallet)
    assert funder_wallet.balance == 5000.00
    assert withdrawer_wallet.balance == 5000.00

    db.close()

# ========================================
# GET MATCH DETAILS
# ========================================

def test_get_match_details():
    db = TestingSessionLocal()

    funder, funder_wallet = create_test_user_with_balance(db)
    withdrawer, withdrawer_wallet = create_test_user_with_balance(db, balance=10000.00)

    match = FundingMatch(
        id=uuid.uuid4(),
        funder_wallet_id=funder_wallet.id,
        withdrawer_wallet_id=withdrawer_wallet.id,
        amount=5000.00,
        currency=CurrencyType.NAIRA,
        status="matched",
        proof_uploaded=False,
        proof_confirmed=False
    )
    db.add(match)
    db.commit()

    funder_token = create_access_token(data={"sub": str(funder.id)})

    response = client.get(
        f"/match/{match.id}",
        headers={"Authorization": f"Bearer {funder_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["match"]["your_role"] == "funder"
    assert data["data"]["match"]["amount"] == "5000.0"

    db.close()

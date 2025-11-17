"""
Celery Tasks for Batch Matching System - NO REDIS VERSION
Uses SQLAlchemy database as broker instead of Redis
Only use this if you don't have Redis installed
"""

from celery import Celery
from celery.schedules import crontab
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Tuple, Dict
import uuid
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from shared import (
    SessionLocal,
    FundingRequest,
    WithdrawalRequest,
    FundingMatchPair,
    MergeCycle,
    AdminWallet,
    Wallet,
    User,
)

# Get database URL from environment
from shared.database import SQLALCHEMY_DATABASE_URL

# Celery configuration - using database instead of Redis
celery_app = Celery(
    "funding_batch_matching",
    broker=f'sqla+{SQLALCHEMY_DATABASE_URL}',  # Use database as broker
    backend=f'db+{SQLALCHEMY_DATABASE_URL}'    # Use database as backend
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)

print("""
⚠️  WARNING: Running Celery WITHOUT Redis!
This uses your database as the message broker.
For production, please install Redis for better performance.

Using database broker: {SQLALCHEMY_DATABASE_URL}
""")


# Copy all the task functions from celery_batch_matching.py
# (The rest of the file remains exactly the same)

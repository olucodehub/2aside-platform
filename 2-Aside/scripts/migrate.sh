#!/bin/bash
# 2-Aside Platform - Database Migration Script
# Run this script to initialize and migrate the database

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo "=============================================="
echo "2-Aside Platform - Database Migration"
echo "=============================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}✗ Virtual environment not found${NC}"
    echo -e "${YELLOW}Please run setup.sh first${NC}"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}✗ .env file not found${NC}"
    echo -e "${YELLOW}Please create .env file from .env.example${NC}"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check database connection
echo -e "${YELLOW}[1/4] Checking database connection...${NC}"
python -c "
import os
from sqlalchemy import create_engine
try:
    engine = create_engine(os.getenv('DATABASE_URL'))
    with engine.connect() as conn:
        print('\033[0;32m✓ Database connection successful\033[0m')
except Exception as e:
    print('\033[0;31m✗ Database connection failed:', str(e), '\033[0m')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to connect to database${NC}"
    echo -e "${YELLOW}Please check your DATABASE_URL in .env file${NC}"
    exit 1
fi

# Initialize Alembic (if not already initialized)
echo ""
echo -e "${YELLOW}[2/4] Checking Alembic configuration...${NC}"
if [ -d "alembic" ]; then
    echo -e "${GREEN}✓ Alembic already initialized${NC}"
else
    echo -e "${YELLOW}! Initializing Alembic...${NC}"
    alembic init alembic

    # Update alembic.ini with database URL
    sed -i "s|sqlalchemy.url = .*|sqlalchemy.url = ${DATABASE_URL}|g" alembic.ini

    # Update env.py to use shared models
    cat > alembic/env.py << 'EOF'
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# Add parent directory to path for shared module
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import Base from shared models
from shared.database import Base
from shared.models import *  # Import all models

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata
target_metadata = Base.metadata

# Load database URL from environment
config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
EOF

    echo -e "${GREEN}✓ Alembic initialized${NC}"
fi

# Create initial migration
echo ""
echo -e "${YELLOW}[3/4] Creating migration...${NC}"
alembic revision --autogenerate -m "Initial migration - all tables"
echo -e "${GREEN}✓ Migration created${NC}"

# Run migrations
echo ""
echo -e "${YELLOW}[4/4] Running migrations...${NC}"
alembic upgrade head
echo -e "${GREEN}✓ Migrations applied successfully${NC}"

echo ""
echo "=============================================="
echo -e "${GREEN}Database migration complete!${NC}"
echo "=============================================="
echo ""
echo -e "${CYAN}Database is now ready for use${NC}"
echo ""

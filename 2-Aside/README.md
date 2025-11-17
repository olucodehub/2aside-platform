# 2-Aside P2P Betting Platform
# Python Microservices Architecture

**Version**: 1.0.0
**Status**: Development
**Date**: 2025-01-20

---

## Overview

2-Aside is a peer-to-peer betting platform with dual-currency support (Naira and USDT). Built on a modern microservices architecture using Python/FastAPI, it offers sports betting, P2P funding/withdrawal matching, user-created bets, and a comprehensive admin dashboard.

### Key Features

- **Sports Betting**: Multiple sports with real-time odds
- **P2P Funding/Withdrawal**: Automatic matching algorithm
- **Dual Currency**: Completely separated Naira and USDT wallets
- **User-Created Bets**: Custom bets with friend matching
- **Referral System**: 5% one-time bonus for referrers
- **Mobile Apps**: iOS, Android, and Web support
- **Admin Dashboard**: Complete platform management

---

## Architecture

### Microservices

1. **Authentication Service** - User auth, JWT tokens, registration
2. **User Service** - Profile management, behavior tracking, referrals
3. **Wallet Service** - Balance management, transactions, currency separation
4. **Funding Service** - P2P matching, funding/withdrawal requests
5. **Betting Service** - Game management, bet registration, results
6. **Custom Bets Service** - User-created bets, friend matching
7. **Admin Service** - Platform statistics, user management
8. **API Gateway** - Request routing, auth validation, rate limiting

### Technology Stack

**Backend**:
- Python 3.11+
- FastAPI (async web framework)
- SQLAlchemy 2.0+ (ORM)
- Alembic (database migrations)
- Celery + Celery Beat (background tasks)
- Redis (caching, queue, rate limiting)
- Azure SQL Server (database)

**Frontend**:
- React Native 0.79+
- Expo 53+
- TypeScript 5.8+

**Infrastructure**:
- Docker + Docker Compose
- Azure Container Apps
- Azure SQL Database
- Azure Cache for Redis
- Azure Blob Storage
- Azure Container Registry

---

## Project Structure

```
2-Aside/
│
├── README.md                       # This file
├── docker-compose.yml              # Local development orchestration
├── docker-compose.prod.yml         # Production deployment
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore patterns
├── requirements.txt                # Shared Python dependencies
│
├── api-gateway/                    # API Gateway service
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── config.py
│   ├── routes/
│   └── middleware/
│
├── services/
│   ├── auth-service/
│   ├── user-service/
│   ├── wallet-service/
│   ├── funding-service/
│   ├── betting-service/
│   ├── custom-bets-service/
│   └── admin-service/
│
├── shared/                         # Shared utilities across services
│   ├── __init__.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── auth.py
│   ├── exceptions.py
│   └── utils.py
│
├── frontend/                       # React Native/Expo app
│   ├── app/
│   ├── components/
│   ├── constants/
│   ├── services/
│   └── package.json
│
├── infrastructure/
│   ├── azure/
│   │   ├── container-apps.bicep
│   │   ├── redis.bicep
│   │   └── deploy.sh
│   └── docker/
│       └── docker-compose.dev.yml
│
├── scripts/
│   ├── setup.sh
│   ├── setup.ps1
│   ├── migrate.sh
│   ├── seed_data.py
│   └── test_all.sh
│
└── docs/
    ├── API.md
    ├── DEPLOYMENT.md
    ├── DEVELOPMENT.md
    └── ARCHITECTURE.md
```

---

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Docker Desktop
- Node.js 18+ (for frontend)
- Azure CLI (for deployment)
- Git

### Setup (Local Development)

#### Windows (PowerShell)

```powershell
# 1. Clone or navigate to project
cd c:\Dev\Rendezvous\2-Aside

# 2. Run setup script
.\scripts\setup.ps1

# 3. Copy environment variables
copy .env.example .env

# 4. Edit .env with your Azure SQL connection string
notepad .env

# 5. Start all services with Docker Compose
docker-compose up -d

# 6. Run database migrations
.\scripts\migrate.sh

# 7. Seed test data (optional)
python scripts\seed_data.py

# 8. Access services
# API Gateway: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

#### Linux/macOS (Bash)

```bash
# 1. Navigate to project
cd /path/to/2-Aside

# 2. Run setup script
chmod +x scripts/setup.sh
./scripts/setup.sh

# 3. Copy environment variables
cp .env.example .env

# 4. Edit .env with your Azure SQL connection string
nano .env

# 5. Start all services
docker-compose up -d

# 6. Run migrations
./scripts/migrate.sh

# 7. Seed test data
python scripts/seed_data.py

# 8. Access services
# API Gateway: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

## Environment Variables

Create a `.env` file in the root directory with the following:

```env
# Database
DATABASE_URL=mssql+pyodbc://username:password@rendezvousdbserver.database.windows.net:1433/RendezvousDB?driver=ODBC+Driver+18+for+SQL+Server

# JWT Secret
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# Redis
REDIS_URL=redis://localhost:6379/0

# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING=your-azure-storage-connection-string

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Environment
ENVIRONMENT=development
DEBUG=true

# Platform Wallet
PLATFORM_WALLET_EMAIL=platform@2aside.com
```

---

## Development Workflow

### Running Individual Services

Each service can be run independently for development:

```bash
# Example: Auth Service
cd services/auth-service
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

### Running Tests

```bash
# Run all tests
./scripts/test_all.sh

# Run tests for specific service
cd services/auth-service
pytest tests/ -v --cov=.

# Run with coverage report
pytest tests/ --cov=. --cov-report=html
```

### Database Migrations

```bash
# Create new migration
cd services/auth-service
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Adding New Service

1. Copy structure from existing service
2. Update `docker-compose.yml`
3. Add to `scripts/test_all.sh`
4. Update API Gateway routes
5. Document in `docs/API.md`

---

## API Documentation

Once services are running, access interactive API docs:

- **API Gateway**: http://localhost:8000/docs
- **Auth Service**: http://localhost:8001/docs
- **User Service**: http://localhost:8002/docs
- **Wallet Service**: http://localhost:8003/docs
- **Funding Service**: http://localhost:8004/docs
- **Betting Service**: http://localhost:8005/docs
- **Custom Bets Service**: http://localhost:8006/docs
- **Admin Service**: http://localhost:8007/docs

---

## Currency Architecture

### Dual-Wallet System

Users have **separate wallet instances** for Naira and USDT:

```
User (Authentication)
  ├─ Naira Wallet (wallet_id: xxx)
  │    ├─ Balance: ₦50,000
  │    ├─ Transaction History (Naira only)
  │    └─ Behavior Tracking (separate)
  │
  └─ USDT Wallet (wallet_id: yyy)
       ├─ Balance: $250
       ├─ Transaction History (USDT only)
       └─ Behavior Tracking (separate)
```

**Dashboard Switching**: Users can toggle between Naira and USDT dashboards. Each shows only that currency's data.

---

## Fee Structure

### Platform Fee: 5%

- User **always** receives 95% of profit
- Platform **always** collects 5% commission

### Referral System

**First Win with Referrer**:
```
Profit: ₦20,000
Platform fee (5%): ₦1,000
User receives: ₦19,000 (95%)

Referral bonus: ₦1,000 (FROM platform's 5% revenue)
  → Referrer: ₦1,000
  → Platform: ₦0 (customer acquisition cost)
```

**Subsequent Wins**:
```
Profit: ₦20,000
Platform fee (5%): ₦1,000
User receives: ₦19,000 (95%)

  → Platform: ₦1,000 (keeps full 5%)
  → Referrer: ₦0 (already paid)
```

---

## Testing

### Unit Testing

- Framework: pytest
- Coverage: 80% minimum (90% for critical services)
- Mock external dependencies
- Use test database (SQLite for speed)

### Running Tests

```bash
# All tests
pytest

# Specific service
cd services/wallet-service
pytest tests/

# With coverage
pytest --cov=. --cov-report=html

# Watch mode
pytest-watch
```

---

## Deployment

### Azure Container Apps (Recommended)

```bash
# 1. Login to Azure
az login

# 2. Set subscription
az account set --subscription "your-subscription-id"

# 3. Deploy infrastructure
cd infrastructure/azure
./deploy.sh

# 4. Build and push Docker images
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml push

# 5. Deploy to Azure
az containerapp update --name 2aside-api-gateway --resource-group 2aside-rg
```

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed instructions.

---

## Portability

This project is designed to be **fully portable**:

1. **Copy entire `/2-Aside` folder** to any location
2. **Update `.env`** with new environment variables
3. **Run `docker-compose up`** to start all services
4. **Access at http://localhost:8000**

All dependencies are containerized. No global installations required except Docker.

---

## Contributing

### Development Guidelines

1. **Create feature branch**: `git checkout -b feature/your-feature`
2. **Write tests first**: Test-driven development
3. **Ensure coverage**: 80%+ code coverage
4. **Update docs**: Keep README and API docs current
5. **Create PR**: Describe changes, link issues
6. **Code review**: Wait for approval before merge

### Code Style

- **Python**: Follow PEP 8, use Black formatter
- **Type hints**: Required for all functions
- **Docstrings**: Google style
- **Imports**: Sorted with isort

---

## Troubleshooting

### Database Connection Issues

```bash
# Test connection
python -c "import pyodbc; print(pyodbc.drivers())"

# Check Azure SQL firewall rules
az sql server firewall-rule list --server rendezvousdbserver --resource-group your-rg
```

### Redis Connection Issues

```bash
# Test Redis locally
redis-cli ping

# Check Redis in Docker
docker ps | grep redis
docker logs 2aside-redis
```

### Port Conflicts

If ports are already in use, update `docker-compose.yml`:

```yaml
ports:
  - "8080:8000"  # Change 8000 to 8080
```

---

## Support

- **Documentation**: See `/docs` folder
- **Issues**: Create GitHub issue
- **Email**: support@2aside.com (if applicable)

---

## License

Proprietary - All rights reserved

---

## Changelog

### Version 1.0.0 (2025-01-20)
- Initial project structure
- Phase 1: Infrastructure setup complete
- Microservices architecture defined
- Dual-wallet currency separation implemented

---

**Built with ❤️ using Python, FastAPI, and Azure**

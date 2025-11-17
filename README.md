# 2-Aside Platform

A peer-to-peer funding and withdrawal platform built with modern microservices architecture.

## Overview

2-Aside enables users to:
- Fund their wallets through P2P matching with users who want to withdraw
- Withdraw funds by matching with users who want to fund
- Upload payment proofs securely to Azure Blob Storage
- Track transactions with multiple currency support (Naira & USDT)
- Earn referral bonuses

## Architecture

### Backend (Python/FastAPI)
- **User Service** (Port 8001): Authentication, user management, referral system
- **Wallet Service** (Port 8002): Multi-currency wallet management
- **Funding Service** (Port 8003): P2P matching, merge cycles, payment proof handling

### Frontend (Next.js/TypeScript)
- Responsive design (mobile & desktop)
- Progressive Web App (PWA) ready
- Real-time updates

### Infrastructure
- **Database**: SQL Server / Azure SQL Database
- **Storage**: Azure Blob Storage (payment proofs)
- **Deployment**: Azure Container Apps
- **CI/CD**: GitHub Actions

## Tech Stack

**Backend:**
- Python 3.9
- FastAPI
- SQLAlchemy
- PyODBC (SQL Server)
- APScheduler (batch processing)
- Azure Storage SDK

**Frontend:**
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- Shadcn UI Components

**DevOps:**
- Docker & Docker Compose
- Azure Container Apps
- GitHub Actions
- Vercel (Frontend)

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- SQL Server
- Azure account (for blob storage)

### Local Development

1. **Clone repository**
```bash
git clone https://github.com/yourusername/2aside-platform.git
cd 2aside-platform
```

2. **Set up backend services**
```bash
cd 2-Aside

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r user-service/requirements.txt
pip install -r wallet-service/requirements.txt
pip install -r funding-service/requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your database and Azure credentials
```

3. **Set up frontend**
```bash
cd 2aside-frontend
npm install
cp .env.example .env.local
# Edit .env.local with your API endpoints
```

4. **Start services**

**Windows:**
```bash
.\start-all-services.ps1
```

**Linux/Mac:**
```bash
# Terminal 1: User Service
cd 2-Aside/user-service && uvicorn main:app --port 8001 --reload

# Terminal 2: Wallet Service
cd 2-Aside/wallet-service && uvicorn main:app --port 8002 --reload

# Terminal 3: Funding Service
cd 2-Aside/funding-service && uvicorn main:app --port 8003 --reload

# Terminal 4: Frontend
cd 2aside-frontend && npm run dev
```

5. **Access the application**
- Frontend: http://localhost:3000
- User Service: http://localhost:8001/docs
- Wallet Service: http://localhost:8002/docs
- Funding Service: http://localhost:8003/docs

## Deployment

### Production Deployment (Azure Container Apps)

See comprehensive guides:
- [Quick Start Guide](DEPLOYMENT_QUICKSTART.md) - 30-60 minutes to production
- [Full Deployment Guide](AZURE_CONTAINER_APPS_DEPLOYMENT.md) - Complete documentation
- [Azure Blob Storage Setup](2-Aside/AZURE_SETUP_INSTRUCTIONS.md) - Storage configuration

**Estimated Costs:**
- Beta testing: ~$20-30/month
- Production (1000+ users): ~$125-175/month

### Docker Deployment

```bash
cd 2-Aside
docker-compose -f docker-compose.prod.yml up --build
```

## Features

### Current Features ✅
- User registration and authentication (JWT)
- Multi-currency wallets (Naira, USDT)
- P2P funding/withdrawal matching
- Automated merge cycles (9am, 3pm, 9pm WAT)
- Payment proof upload with Azure Blob Storage
- Automatic proof deletion (7 days after confirmation)
- Referral system (5% of platform fees)
- Transaction history
- Mobile-responsive design

### Planned Features 🚧
- Group betting system
- Rendezvous betting
- Admin dashboard
- Analytics and reporting
- SMS notifications
- KYC verification

## Project Structure

```
2aside-platform/
├── 2-Aside/                    # Backend services
│   ├── shared/                 # Shared database models
│   ├── user-service/           # User & auth service
│   ├── wallet-service/         # Wallet management
│   ├── funding-service/        # P2P matching & proofs
│   ├── docker-compose.prod.yml
│   └── .env.example
├── 2aside-frontend/            # Next.js frontend
│   ├── app/                    # App router pages
│   ├── components/             # React components
│   ├── lib/                    # API clients & utilities
│   └── public/                 # Static assets
├── .github/
│   └── workflows/              # CI/CD pipelines
├── DEPLOYMENT_QUICKSTART.md
├── AZURE_CONTAINER_APPS_DEPLOYMENT.md
└── README.md
```

## Environment Variables

### Backend (.env)
```env
DATABASE_URL=mssql+pyodbc://...
JWT_SECRET=your-secret-key
AZURE_STORAGE_CONNECTION_STRING=...
AZURE_STORAGE_CONTAINER_NAME=payment-proofs
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_USER_SERVICE_URL=http://localhost:8001
NEXT_PUBLIC_WALLET_SERVICE_URL=http://localhost:8002
NEXT_PUBLIC_FUNDING_SERVICE_URL=http://localhost:8003
```

## API Documentation

All services provide interactive API documentation via Swagger UI:
- User Service: http://localhost:8001/docs
- Wallet Service: http://localhost:8002/docs
- Funding Service: http://localhost:8003/docs

## Testing

### Run Demo Flow
```bash
.\test-merge-demo.ps1
```

This script:
1. Registers two users
2. Creates funding and withdrawal requests
3. Triggers merge cycle
4. Creates match pairs

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Private - All Rights Reserved

## Support

For issues and questions:
- Create an issue in GitHub
- Check documentation in `/docs` folder
- Review deployment guides

## Acknowledgments

- FastAPI for excellent Python web framework
- Next.js for powerful React framework
- Azure for cloud infrastructure
- Vercel for frontend deployment

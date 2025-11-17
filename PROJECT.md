# 2-Aside - P2P Sports Betting Platform

## Overview

2-Aside is a peer-to-peer sports betting platform that combines traditional sports betting with an innovative P2P funding mechanism. The platform supports dual-currency operations (USDT and Nigerian Naira) and includes a comprehensive referral system.

## Technology Stack

### Backend
- **Framework**: ASP.NET Core 8.0 (.NET 8.0)
- **Database**: SQL Server (Azure SQL Database)
- **ORM**: Entity Framework Core 9.0.5
- **Authentication**: JWT Bearer tokens
- **Security**: BCrypt.Net-Next for password hashing
- **Storage**: Azure Blob Storage
- **API Documentation**: Swagger/Swashbuckle

### Frontend
- **Framework**: React Native 0.79.1
- **Build Tool**: Expo 53.0.0
- **Router**: Expo Router 5.0.2 (file-based routing)
- **Language**: TypeScript 5.8.3
- **HTTP Client**: Axios 1.9.0
- **State Management**: React Context API
- **UI Libraries**: Lucide React Native, expo-linear-gradient

## Project Structure

```
Rendezvous/
├── Rendezvous/                  # Backend (.NET)
│   ├── Controllers/             # API endpoints (13 controllers)
│   ├── Models/                  # Entity models (23 entities)
│   ├── Services/                # Business logic (8 services)
│   ├── Interfaces/              # Service contracts
│   ├── Data/                    # EF Core DbContext
│   ├── Migrations/              # Database migrations
│   ├── Program.cs               # Application entry point
│   └── appsettings.json         # Configuration
└── RendezvousFrontEnd/          # Frontend (React Native)
    ├── app/                     # Expo Router pages
    ├── components/              # Reusable UI components
    ├── context/                 # React Context providers
    ├── lib/                     # Utilities & API services
    ├── hooks/                   # Custom React hooks
    └── assets/                  # Images, icons, fonts
```

## Core Features

### 1. Sports Betting System
- Place bets on upcoming sports events (football, basketball, etc.)
- Head-to-head betting (matched pairs)
- Automatic game result processing
- Winner payouts with commission handling

### 2. P2P Funding Mechanism
- Users request funding in USDT or Nigerian Naira
- Funders provide money to withdrawers
- Automated matching based on amounts and currency
- Payment proof system with Azure Blob Storage
- Background expiry service for stale requests

### 3. Dual-Currency Wallet
- Support for USDT (stablecoin) and Nigerian Naira
- Real-time balance tracking
- Complete transaction history
- Cross-currency conversion support

### 4. Referral System
- Multi-level referral tracking
- 5% commission to referrer on first win
- 5% platform commission on all wins
- Automatic reward distribution

### 5. User Behavior Tracking
- Consecutive miss tracking
- Cancellation monitoring
- Automatic blocking after 3+ consecutive misses
- Anti-fraud measures

### 6. Admin Dashboard
- User management
- Game result updates
- Admin privilege assignment
- System statistics

## Architecture

### Design Patterns
- **Layered Architecture**: Controllers → Services → Data Access
- **Dependency Injection**: Constructor-based DI throughout
- **Repository Pattern**: Via EF Core DbContext
- **Service Pattern**: Business logic in dedicated services
- **Background Service Pattern**: For async processing
- **DTO Pattern**: Separation of API contracts from internal models

### Key Services

#### Backend Services
1. **GameService**: Processes game results, handles payouts
2. **MatchingService**: Core P2P funding matching algorithm
3. **FundingService**: Manages funding requests and matching
4. **FunderExpiryService**: Background service for cleanup (runs every 10 minutes)
5. **SportsApiService**: Integration with TheSportsDB API
6. **AzureBlobService**: File upload handling

#### Frontend Services
1. **AuthContext**: Global authentication state
2. **CurrencyContext**: Currency management and balances
3. **API Client**: Axios instance with JWT injection
4. **Cache Service**: LocalStorage-based caching with TTL

## Database Entities (23 Models)

| Entity | Purpose |
|--------|---------|
| User | Core user entity with balances and tracking |
| Game | Sports events with odds |
| BetRegistration | User bets on games |
| MatchPair | Pairs users for betting |
| FundingRequest | P2P funding requests |
| FundingMatch | Matched funding pairs |
| WithdrawalRequest | Withdrawal requests |
| Referral | Referral relationships |
| ReferralReward | Commission tracking |
| WalletLog | Transaction history |
| BankDetails | User bank information |
| BlockedUser | Blocked user tracking |
| SystemAccount | Platform commission wallet |

## API Structure

Base URL: `http://localhost:5039/api`

### Main Endpoints
- `/auth/*` - Registration, login, currency management
- `/games/*` - Game listings and details
- `/betting/*` - Place bets
- `/funding/*` - Funding requests
- `/fundingmatch/*` - Funding confirmations
- `/wallet/*` - Balance and history
- `/withdrawal/*` - Withdrawal requests
- `/sports/*` - Sports event data
- `/admin/*` - Admin operations

## Security Features

1. **JWT Authentication**: 60-minute token expiration
2. **Password Hashing**: BCrypt with salt
3. **Authorization**: Role-based access control
4. **Fraud Prevention**: User blocking system
5. **Data Validation**: Amount and balance verification

## Development Setup

### Backend
```bash
cd Rendezvous
dotnet restore
dotnet ef database update
dotnet run
```

### Frontend
```bash
cd RendezvousFrontEnd
npm install
npm run dev
```

## Current Status

### Completed Features
- User authentication and authorization
- Dual-currency wallet system
- P2P funding matching algorithm
- Sports betting with game matching
- Referral tracking and rewards
- Admin dashboard
- Background expiry service
- Azure Blob integration for proofs

### Areas for Improvement
- No automated testing (unit, integration, E2E)
- CORS configured for all origins (needs production restriction)
- Missing CI/CD pipeline
- No error logging/monitoring service
- No rate limiting on API endpoints
- Missing input validation on some endpoints

## License

[License information to be added]

## Contributors

[Contributors list to be added]

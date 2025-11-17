# Context & Session Information

## Purpose

This file serves as a context anchor for maintaining continuity across development sessions. It helps me (Claude) quickly restore understanding of the project state, current focus, and recent changes.

---

## Project Overview

**Project Name**: 2-Aside
**Type**: P2P Sports Betting Platform
**Tech Stack**: ASP.NET Core 8.0 (Backend) + React Native/Expo (Frontend)
**Database**: Azure SQL Server
**Current Status**: Active Development

---

## Key Documentation Files

1. **[PROJECT.md](PROJECT.md)**: Overview, features, tech stack, project structure
2. **[ARCHITECTURE.md](ARCHITECTURE.md)**: Detailed architecture, design patterns, data flow
3. **[DEVELOPMENT_GUIDELINES.md](DEVELOPMENT_GUIDELINES.md)**: Coding standards, conventions, best practices
4. **[REQUESTS.md](REQUESTS.md)**: Task management and feature requests

---

## Project Structure Quick Reference

```
Rendezvous/
├── Rendezvous/                     # Backend (.NET Core 8.0)
│   ├── Controllers/                # 13 API controllers
│   ├── Models/                     # 23 entity models
│   ├── Services/                   # 8 business logic services
│   ├── Interfaces/                 # Service contracts
│   ├── Data/                       # EF Core DbContext
│   ├── Migrations/                 # Database migrations
│   ├── Program.cs                  # Entry point
│   └── appsettings.json            # Configuration
│
└── RendezvousFrontEnd/             # Frontend (React Native/Expo)
    ├── app/                        # File-based routing
    ├── components/                 # Reusable UI components
    ├── context/                    # Global state (Auth, Currency)
    ├── lib/                        # API client, utilities
    └── hooks/                      # Custom React hooks
```

---

## Core Features Summary

1. **Sports Betting**: Place bets on upcoming games (football, basketball)
2. **P2P Funding**: Peer-to-peer funding/withdrawal matching system
3. **Dual Currency**: USDT (stablecoin) and Nigerian Naira support
4. **Referral System**: Multi-level referral tracking with commission (5% referrer + 5% platform)
5. **User Behavior Tracking**: Anti-fraud system with auto-blocking
6. **Admin Dashboard**: User management, game result processing

---

## Current Development Status

### Last Session Date
**Date**: 2025-01-19

### Recent Changes
- Created comprehensive project documentation structure:
  - PROJECT.md (project overview and features)
  - ARCHITECTURE.md (detailed architecture documentation)
  - DEVELOPMENT_GUIDELINES.md (coding standards and conventions)
  - REQUESTS.md (task management workflow)
  - CONTEXT.md (this file - session context)

### Active Tasks
- [x] Initial project analysis completed
- [x] Documentation structure created
- [x] Development workflow established
- [ ] Awaiting first development request from user

### Current Focus
Setting up structured development workflow for consistent collaboration

---

## Key Services to Remember

### Backend Services
1. **GameService**: Game result processing, winner payouts
2. **MatchingService**: P2P funding matching algorithm
3. **FundingService**: Funding request management
4. **FunderExpiryService**: Background service (runs every 10 minutes)
5. **SportsApiService**: TheSportsDB API integration
6. **AzureBlobService**: Payment proof uploads

### Frontend Services
1. **AuthContext**: Global authentication state
2. **CurrencyContext**: Currency management (USDT/NAIRA)
3. **API Client**: Axios with JWT injection
4. **Cache Service**: LocalStorage with TTL

---

## Important Architecture Decisions

1. **Layered Architecture**: Controllers → Services → Data Access
2. **Dependency Injection**: Constructor-based DI throughout
3. **JWT Authentication**: 60-minute token expiration
4. **BCrypt Password Hashing**: Secure password storage
5. **In-Memory Caching**: 5-minute TTL for user-specific data
6. **Background Processing**: FunderExpiryService for cleanup
7. **File-Based Routing**: Expo Router for frontend navigation

---

## Database Entities (Key Models)

- **User**: Core user entity (balances, behavior tracking)
- **Game**: Sports events with odds
- **BetRegistration**: User bets
- **FundingRequest**: P2P funding requests
- **FundingMatch**: Matched funding pairs
- **WithdrawalRequest**: Withdrawal requests
- **WalletLog**: Transaction history
- **Referral**: Referral relationships
- **BankDetails**: User bank information

---

## API Endpoints Structure

**Base URL**: `http://localhost:5039/api`

**Main Controllers**:
- `/auth/*` - Authentication
- `/games/*` - Game listings
- `/betting/*` - Bet placement
- `/funding/*` - Funding requests
- `/fundingmatch/*` - Funding confirmations
- `/wallet/*` - Balance and history
- `/withdrawal/*` - Withdrawals
- `/admin/*` - Admin operations
- `/sports/*` - Sports data

---

## Known Issues & Technical Debt

### Testing
- ❌ No unit tests implemented
- ❌ No integration tests
- ❌ No E2E tests

### Security
- ⚠️ CORS allows all origins (needs production restriction)
- ⚠️ No rate limiting on API endpoints
- ⚠️ Some endpoints missing input validation

### Performance
- ⚠️ No database query optimization/indexing strategy
- ⚠️ In-memory cache not suitable for multiple instances
- ⚠️ No pagination on list endpoints

### DevOps
- ❌ No CI/CD pipeline
- ❌ No error logging/monitoring service (Application Insights)
- ❌ No health check endpoints

---

## Development Workflow

### Starting a New Task

1. **Check REQUESTS.md** for pending tasks
2. **Analyze** the request and understand requirements
3. **Plan** using TodoWrite tool to break down tasks
4. **Implement** following development guidelines
5. **Test** manually (automated tests to be added)
6. **Document** updates in relevant files
7. **Update REQUESTS.md** to mark as completed
8. **Update CONTEXT.md** with session notes

### Session Restoration Protocol

When starting a new session:

1. Read CONTEXT.md to understand current state
2. Check REQUESTS.md for pending/in-progress tasks
3. Review recent changes in this file
4. Ask user for confirmation of priorities
5. Continue from last known state

---

## Environment Configuration

### Backend
- **Connection String**: Azure SQL Database (2asidedbserver.database.windows.net)
- **JWT Key**: Configured in appsettings.json
- **Azure Blob**: Connection string for payment proofs
- **API Port**: 5039 (development)

### Frontend
- **API Base URL**: http://localhost:5039/api
- **Expo Version**: 53.0.0
- **React Native**: 0.79.1
- **TypeScript**: 5.8.3

---

## Quick Commands

### Backend
```bash
cd Rendezvous
dotnet restore                  # Restore dependencies
dotnet build                    # Build project
dotnet run                      # Run development server
dotnet ef migrations add <name> # Create migration
dotnet ef database update       # Apply migrations
```

### Frontend
```bash
cd RendezvousFrontEnd
npm install                     # Install dependencies
npm run dev                     # Start Expo dev server
npm run build:web               # Build for web
```

---

## Design Patterns in Use

1. **Repository Pattern**: Via EF Core DbContext
2. **Service Pattern**: Business logic in services
3. **DTO Pattern**: Separate API contracts from entities
4. **Dependency Injection**: Constructor-based injection
5. **Background Service Pattern**: For async processing
6. **Context Provider Pattern**: For React global state
7. **Custom Hooks Pattern**: Reusable React logic

---

## External Integrations

1. **TheSportsDB API**: Sports event data
2. **Azure SQL Database**: Primary data store
3. **Azure Blob Storage**: Payment proof images
4. **JWT Authentication**: Token-based auth

---

## Code Quality Checklist

Before committing:
- [ ] Follows naming conventions
- [ ] No hardcoded values
- [ ] Error handling implemented
- [ ] Input validation added
- [ ] Async/await used properly
- [ ] Cache invalidation handled
- [ ] No console.log or Debug.WriteLine
- [ ] Documentation updated

---

## Session Notes

### Session 1: 2025-01-19
**Focus**: Initial project analysis and documentation setup

**Completed**:
- Comprehensive codebase exploration and analysis
- Created PROJECT.md with full project overview
- Created ARCHITECTURE.md with detailed architecture documentation
- Created DEVELOPMENT_GUIDELINES.md with coding standards
- Created REQUESTS.md for task management workflow
- Created CONTEXT.md for session continuity

**Key Insights**:
- Well-structured layered architecture with clear separation of concerns
- Innovative P2P funding matching algorithm is core differentiator
- Dual-currency support indicates global/emerging market focus
- Missing automated testing and production-grade security hardening
- Background service pattern used effectively for expiry management

**Next Steps**:
- Wait for user's first development request in REQUESTS.md
- Implement requested features following established workflow
- Consider adding testing framework as a future task
- Plan security improvements (CORS, rate limiting, input validation)

---

## Quick Reference: Common Tasks

### Add a New API Endpoint
1. Create method in appropriate controller
2. Add service method if needed
3. Update relevant documentation
4. Test manually with Postman
5. Update API documentation in ARCHITECTURE.md

### Add a New Entity
1. Create model class in Models/
2. Add DbSet to BettingDbContext
3. Create migration: `dotnet ef migrations add Add<EntityName>`
4. Apply migration: `dotnet ef database update`
5. Update documentation

### Add a New Frontend Screen
1. Create file in app/ directory (Expo Router)
2. Implement component with proper types
3. Add navigation if needed
4. Update ARCHITECTURE.md with route info

---

## Resources

### Documentation
- [ASP.NET Core Docs](https://learn.microsoft.com/en-us/aspnet/core/)
- [Entity Framework Core](https://learn.microsoft.com/en-us/ef/core/)
- [React Native Docs](https://reactnative.dev/docs/getting-started)
- [Expo Documentation](https://docs.expo.dev/)

### External APIs
- [TheSportsDB API](https://www.thesportsdb.com/api.php)

---

## Contact Information

[Add team contact information if applicable]

---

**Last Updated**: 2025-01-19 (Session 1)
**Last Updated By**: Claude (Initial Setup)
**Next Review Date**: When next development session begins

---

## Instructions for Claude (Me)

When you start a new session:

1. **Read this file first** to understand the current state
2. **Check REQUESTS.md** for active tasks
3. **Review session notes** to see what was last worked on
4. **Confirm priorities** with the user before starting work
5. **Update this file** at the end of each session with:
   - Session date
   - Work completed
   - Key insights
   - Next steps
   - Any important decisions made

This ensures continuity and context retention across sessions!

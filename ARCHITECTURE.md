# 2-Aside - Architecture Documentation

## System Architecture Overview

2-Aside follows a **client-server architecture** with clear separation between frontend (React Native/Expo) and backend (ASP.NET Core). The system is cloud-native, leveraging Azure services for database and storage.

```
┌─────────────────────────────────────────────────────────────┐
│                    Mobile Client (Expo)                      │
│  ┌────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │   Auth     │  │   Currency   │  │   API Client       │  │
│  │  Context   │  │   Context    │  │  (Axios + JWT)     │  │
│  └────────────┘  └──────────────┘  └────────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTPS/JSON
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              ASP.NET Core Web API (Backend)                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    Controllers Layer                    │ │
│  │  Auth │ Games │ Betting │ Funding │ Wallet │ Admin    │ │
│  └──────────────────────┬──────────────────────────────────┘ │
│                         │                                     │
│  ┌──────────────────────▼──────────────────────────────────┐ │
│  │                    Services Layer                        │ │
│  │  GameService │ MatchingService │ FundingService │ etc.  │ │
│  └──────────────────────┬──────────────────────────────────┘ │
│                         │                                     │
│  ┌──────────────────────▼──────────────────────────────────┐ │
│  │              Entity Framework Core (ORM)                 │ │
│  │                   BettingDbContext                       │ │
│  └──────────────────────┬──────────────────────────────────┘ │
└─────────────────────────┼─────────────────────────────────────┘
                          │
         ┌────────────────┼────────────────┐
         ▼                                  ▼
┌─────────────────┐              ┌──────────────────────┐
│  Azure SQL DB   │              │  Azure Blob Storage  │
│  (2AsideDB)     │              │  (Payment Proofs)    │
└─────────────────┘              └──────────────────────┘
```

## Backend Architecture

### Layered Architecture Pattern

The backend follows a **3-tier layered architecture**:

```
┌──────────────────────────────────────────────┐
│         Presentation Layer (Controllers)      │
│  - HTTP request/response handling             │
│  - Input validation & DTO transformation      │
│  - JWT authentication enforcement             │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│         Business Logic Layer (Services)       │
│  - Core business rules                        │
│  - Transaction management                     │
│  - Caching logic                              │
│  - External API integration                   │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│         Data Access Layer (EF Core)           │
│  - BettingDbContext                           │
│  - Entity configuration                       │
│  - Database queries via LINQ                  │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│              Database (SQL Server)            │
└──────────────────────────────────────────────┘
```

### Dependency Injection Container

**Location**: [Program.cs](Rendezvous/Program.cs)

**Service Registrations**:
```csharp
// Scoped (per request)
builder.Services.AddScoped<IGameService, GameService>();
builder.Services.AddScoped<IFundingService, FundingService>();
builder.Services.AddScoped<ISportsApiService, SportsApiService>();
builder.Services.AddScoped<IMatchingService, MatchingService>();

// Singleton (application lifetime)
builder.Services.AddSingleton<IMemoryCache, MemoryCache>();
builder.Services.AddSingleton<IAzureBlobService, AzureBlobService>();
builder.Services.AddSingleton<ISystemTimeService, SystemTimeService>();

// Hosted Service (background processing)
builder.Services.AddHostedService<FunderExpiryService>();
```

### Core Services

#### 1. GameService
**File**: [Rendezvous/Services/GameService.cs](Rendezvous/Services/GameService.cs)

**Responsibilities**:
- Process game results
- Credit winners
- Handle commission distribution (5% referrer + 5% platform)
- Create wallet logs
- Update system account balance

**Key Methods**:
```csharp
Task ProcessGameResultAsync(int gameId, string result)
```

#### 2. MatchingService
**File**: [Rendezvous/Services/MatchingService.cs](Rendezvous/Services/MatchingService.cs)

**Responsibilities**:
- Match funding requests with withdrawal requests
- Amount-based matching algorithm
- Currency-specific matching
- FundingMatch entity creation
- Cache invalidation after matches

**Key Methods**:
```csharp
Task RunMatchingAsync()
Task<FundingMatch> TryMatchUserAsync(int userId)
```

**Matching Algorithm**:
1. Find pending funding requests (USDT or NAIRA)
2. Find pending withdrawal requests (same currency)
3. Match equal amounts
4. Create FundingMatch with both user IDs
5. Update request statuses to "Matched"
6. Invalidate user-specific caches

#### 3. FundingService
**File**: [Rendezvous/Services/Funding/FundingService.cs](Rendezvous/Services/Funding/FundingService.cs)

**Responsibilities**:
- Create funding requests
- Validate user balances
- Manage funding request lifecycle
- Cache management for funding status

**Caching Strategy**:
```csharp
// Cache key pattern
string cacheKey = $"FundingStatus_{userId}";
TimeSpan cacheDuration = TimeSpan.FromMinutes(5);
```

#### 4. FunderExpiryService
**File**: [Rendezvous/Services/Funding/FunderExpiryService.cs](Rendezvous/Services/Funding/FunderExpiryService.cs)

**Type**: Background Service (IHostedService)

**Responsibilities**:
- Runs every 10 minutes
- Checks for expired funding requests (> 30 minutes old)
- Tracks consecutive misses and cancellations
- Auto-blocks users with 3+ consecutive misses
- Cleans up stale FundingMatch records

**Execution Flow**:
```
Timer Trigger (10 min) → Find Expired Matches → Update User Stats
                                ↓
                      Check Consecutive Misses
                                ↓
                      Block User if >= 3 Misses
```

#### 5. SportsApiService
**File**: [Rendezvous/Services/SportsApiService.cs](Rendezvous/Services/SportsApiService.cs)

**Responsibilities**:
- Integration with TheSportsDB API
- Fetch upcoming football/basketball events
- Parse and map external API data to internal models
- HTTP client management

**External API**: `https://www.thesportsdb.com/api/v1/json/3/`

#### 6. AzureBlobService
**File**: [Rendezvous/Services/AzureBlobService.cs](Rendezvous/Services/AzureBlobService.cs)

**Responsibilities**:
- Upload payment proof images to Azure Blob Storage
- Generate unique blob names
- Return public blob URLs
- Container management

**Container**: `payment-proofs`

### Data Model Architecture

#### Entity Relationships

```
User (1) ─────────< (N) BetRegistration
  │                         │
  │                         │
  │                    (N) Game (1)
  │
  ├─ (1:N) FundingRequest
  │
  ├─ (1:N) WithdrawalRequest
  │
  ├─ (1:N) WalletLog
  │
  ├─ (1:N) Referral (as Referrer)
  │
  ├─ (1:N) Referral (as Referred)
  │
  └─ (1:1) BankDetails

FundingRequest (1) ─── (1) FundingMatch ─── (1) WithdrawalRequest

User (1) ────< (N) ReferralReward

MatchPair: User1 + User2 → Game → BetRegistration
```

#### Key Entities

**User Entity** ([Rendezvous/Models/User.cs](Rendezvous/Models/User.cs)):
```csharp
public class User
{
    public int Id { get; set; }
    public string Username { get; set; }
    public string Email { get; set; }
    public string PasswordHash { get; set; }
    public decimal UsdtBalance { get; set; }
    public decimal NairaBalance { get; set; }
    public string PreferredCurrency { get; set; }
    public bool IsAdmin { get; set; }

    // Behavior tracking
    public int ConsecutiveCancellations { get; set; }
    public int ConsecutiveMisses { get; set; }
    public bool IsBlocked { get; set; }
}
```

**FundingRequest Entity**:
```csharp
public class FundingRequest
{
    public int Id { get; set; }
    public int UserId { get; set; }
    public decimal Amount { get; set; }
    public string Currency { get; set; } // "USDT" or "NAIRA"
    public string Status { get; set; } // "Pending", "Matched", "Completed"
    public DateTime CreatedAt { get; set; }
}
```

**FundingMatch Entity**:
```csharp
public class FundingMatch
{
    public int Id { get; set; }
    public int FunderId { get; set; }
    public int WithdrawerId { get; set; }
    public decimal Amount { get; set; }
    public string Currency { get; set; }
    public string Status { get; set; } // "Pending", "Confirmed", "Expired"
    public DateTime MatchedAt { get; set; }
}
```

### Caching Strategy

**Implementation**: In-Memory Caching (IMemoryCache)

**Cached Data**:
1. User funding status: `FundingStatus_{userId}` (5 min TTL)
2. User wallet history: `WalletHistory_{userId}` (5 min TTL)
3. Sports event data: Various keys (API-dependent TTL)

**Cache Invalidation**:
- Manual invalidation after state changes
- TTL-based automatic expiration
- Cache keys removed after matching operations

**Example**:
```csharp
_cache.Remove($"FundingStatus_{userId}");
_cache.Remove($"WalletHistory_{userId}");
```

### Authentication & Authorization

**Authentication Flow**:
```
1. User Login → AuthController.Login()
2. Validate credentials (BCrypt.Verify)
3. Generate JWT token (JwtSecurityTokenHandler)
4. Return token to client
5. Client stores token in AsyncStorage
6. Client includes token in Authorization header
7. Backend validates token on each request
```

**JWT Configuration** ([appsettings.json](Rendezvous/appsettings.json)):
```json
{
  "Jwt": {
    "Key": "aKF8OcJKryEO...",
    "Issuer": "2AsideApp",
    "Audience": "2AsideAppUsers",
    "ExpirationMinutes": 60
  }
}
```

**Token Claims**:
- `userId`: User ID
- `username`: Username
- `email`: Email address
- `isAdmin`: Admin status (boolean)

**Authorization**:
- `[Authorize]` attribute on protected controllers
- Claim-based checks in admin endpoints
- Custom authorization policies (can be extended)

### Background Processing

**FunderExpiryService Architecture**:

```
Application Startup
       │
       ▼
Register FunderExpiryService as HostedService
       │
       ▼
StartAsync() → Create Timer (10 min interval)
       │
       ▼
   ExecuteAsync() Loop
       │
       ├─ Find Expired FundingMatches (> 30 min)
       │
       ├─ For Each Expired Match:
       │  ├─ Increment Funder ConsecutiveMisses
       │  ├─ Increment Withdrawer ConsecutiveMisses
       │  ├─ Check if >= 3 Misses
       │  └─ Block User if threshold met
       │
       └─ Wait 10 minutes → Repeat
```

## Frontend Architecture

### Component Hierarchy

```
App Root (_layout.tsx)
  │
  ├─ AuthContext Provider
  │  └─ CurrencyContext Provider
  │     │
  │     ├─ Public Routes
  │     │  ├─ /auth/login
  │     │  └─ /auth/register
  │     │
  │     └─ Protected Routes (Tabs)
  │        ├─ /(tabs)/dashboard
  │        ├─ /(tabs)/games
  │        ├─ /(tabs)/auction (funding)
  │        ├─ /(tabs)/history
  │        └─ /(tabs)/profile
  │
  └─ Additional Routes
     ├─ /betting/*
     ├─ /funding/*
     ├─ /admin/*
     └─ /settings/*
```

### State Management

**Global State (React Context)**:

**1. AuthContext** ([RendezvousFrontEnd/context/AuthContext.tsx](RendezvousFrontEnd/context/AuthContext.tsx)):
```typescript
interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}
```

**2. CurrencyContext** ([RendezvousFrontEnd/context/CurrencyContext.tsx](RendezvousFrontEnd/context/CurrencyContext.tsx)):
```typescript
interface CurrencyContextType {
  currency: 'USDT' | 'NAIRA';
  setCurrency: (currency: 'USDT' | 'NAIRA') => void;
  usdtBalance: number;
  nairaBalance: number;
  refreshBalance: () => Promise<void>;
}
```

### API Client Architecture

**File**: [RendezvousFrontEnd/lib/api.ts](RendezvousFrontEnd/lib/api.ts)

**Axios Configuration**:
```typescript
const api = axios.create({
  baseURL: 'http://localhost:5039/api',
  timeout: 10000,
});

// Request Interceptor (JWT injection)
api.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response Interceptor (error handling)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle token expiration
    }
    return Promise.reject(error);
  }
);
```

### Routing Architecture

**Expo Router** (file-based routing):

```
app/
├── _layout.tsx                 # Root layout with providers
├── index.tsx                   # Splash/landing page
├── auth/
│   ├── login.tsx               # Login screen
│   ├── register.tsx            # Registration screen
│   └── verify.tsx              # Email verification
├── (tabs)/                     # Tab navigation group
│   ├── _layout.tsx             # Tab layout
│   ├── dashboard.tsx           # Dashboard screen
│   ├── games.tsx               # Games listing
│   ├── auction.tsx             # Funding marketplace
│   ├── history.tsx             # Transaction history
│   └── profile.tsx             # User profile
├── betting/
│   ├── [id].tsx                # Dynamic game betting screen
│   └── confirm.tsx             # Bet confirmation
├── funding/
│   ├── request.tsx             # Funding request form
│   ├── match.tsx               # Matched funding details
│   └── proof.tsx               # Payment proof upload
└── admin/
    ├── users.tsx               # User management
    └── games.tsx               # Game result management
```

## Data Flow Patterns

### 1. User Login Flow

```
[Login Screen]
     │
     ├─ Submit credentials
     ▼
[AuthContext.login()]
     │
     ├─ POST /api/auth/login
     ▼
[AuthController.Login()]
     │
     ├─ Verify password (BCrypt)
     ├─ Generate JWT token
     └─ Return token + user data
     ▼
[Frontend]
     │
     ├─ Store token in AsyncStorage
     ├─ Update AuthContext state
     └─ Navigate to dashboard
```

### 2. Funding Request Flow

```
[Funding Request Screen]
     │
     ├─ Enter amount & currency
     ▼
[FundingController.CreateRequest()]
     │
     ├─ Validate user balance
     ├─ Create FundingRequest entity
     ├─ Save to database
     └─ Call MatchingService
     ▼
[MatchingService.RunMatchingAsync()]
     │
     ├─ Find matching withdrawal requests
     ├─ Create FundingMatch
     ├─ Update statuses
     └─ Invalidate cache
     ▼
[Frontend]
     │
     ├─ Poll for match status
     └─ Navigate to match details if found
```

### 3. Game Result Processing Flow

```
[Admin Panel]
     │
     ├─ Submit game result
     ▼
[AdminController.UpdateGameResult()]
     │
     ├─ Update Game entity
     └─ Call GameService
     ▼
[GameService.ProcessGameResultAsync()]
     │
     ├─ Find all BetRegistrations for game
     ├─ Identify winners
     ├─ Calculate payouts
     │   ├─ 90% to winner
     │   ├─ 5% to referrer (first win)
     │   └─ 5% to platform
     ├─ Update user balances
     ├─ Create WalletLog entries
     └─ Update SystemAccount balance
```

## Security Architecture

### 1. Password Security
- **Hashing**: BCrypt with automatic salt generation
- **Verification**: Constant-time comparison
- **Storage**: Only hashed passwords in database

### 2. Token Security
- **Algorithm**: HMAC-SHA256
- **Expiration**: 60 minutes
- **Claims**: User ID, username, email, admin status
- **Storage**: AsyncStorage (frontend), not stored (backend)

### 3. Authorization Levels
- **Public**: Registration, login
- **Authenticated**: All user operations
- **Admin**: User management, game results

### 4. Fraud Prevention
- **Consecutive Misses**: Track and auto-block (>= 3)
- **Cancellation Tracking**: Monitor user behavior
- **Expiry Mechanism**: 30-minute timeout for funding matches

## Scalability Considerations

### Current Limitations
1. **Single Server**: No horizontal scaling
2. **In-Memory Cache**: Lost on restart, not shared across instances
3. **Background Service**: Single instance only
4. **No Message Queue**: Direct database operations

### Recommended Improvements
1. **Distributed Cache**: Redis for shared cache
2. **Message Queue**: RabbitMQ/Azure Service Bus for async operations
3. **Load Balancer**: Distribute traffic across multiple instances
4. **Database Optimization**: Indexing, read replicas
5. **CDN**: For static assets (frontend)

## Deployment Architecture

### Current Setup
```
┌─────────────────┐
│  Mobile Clients │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Web Server    │ (IIS/Kestrel)
│  (ASP.NET Core) │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌─────────┐ ┌──────────────┐
│ Azure   │ │ Azure Blob   │
│ SQL DB  │ │ Storage      │
└─────────┘ └──────────────┘
```

### Recommended Production Architecture
```
┌──────────────────┐
│  CDN (Frontend)  │
└────────┬─────────┘
         │
┌────────▼─────────┐
│  Load Balancer   │
└────────┬─────────┘
         │
    ┌────┴────────┐
    ▼             ▼
┌────────┐   ┌────────┐
│ API    │   │ API    │ (Multiple instances)
│ Server │   │ Server │
└───┬────┘   └───┬────┘
    │            │
    └─────┬──────┘
          │
     ┌────┴────┐
     ▼         ▼
┌─────────┐ ┌──────┐
│ Azure   │ │ Redis│ (Distributed cache)
│ SQL DB  │ │Cache │
└─────────┘ └──────┘
```

## Performance Considerations

### Database Optimization
- **Indexes**: Add on UserId, Status, Currency fields
- **Query Optimization**: Use compiled queries for frequent operations
- **Connection Pooling**: Enable in connection string

### Caching Strategy
- **Read-Heavy Data**: Cache for 5-15 minutes
- **User-Specific**: Shorter TTL (2-5 minutes)
- **Invalidation**: Manual removal on state changes

### API Performance
- **Pagination**: Implement for list endpoints
- **Field Selection**: Allow clients to request specific fields
- **Compression**: Enable gzip compression

## Monitoring & Observability

### Recommended Tools
1. **Application Insights**: Performance monitoring
2. **Serilog**: Structured logging
3. **Health Checks**: Endpoint for monitoring
4. **Metrics**: Request rate, error rate, latency

### Key Metrics to Track
- API response times
- Database query duration
- Cache hit/miss ratio
- Funding match success rate
- User blocking rate
- Background service execution time

## Error Handling Strategy

### Backend
- **Global Exception Handler**: Catch unhandled exceptions
- **Structured Logging**: Log with context
- **User-Friendly Messages**: Return sanitized error messages

### Frontend
- **API Error Interceptor**: Handle 401, 403, 500 errors
- **Toast Notifications**: User-friendly error messages
- **Retry Logic**: Automatic retry for network errors

## Testing Strategy (Recommended)

### Backend Testing
1. **Unit Tests**: Services, business logic
2. **Integration Tests**: Controllers with in-memory database
3. **API Tests**: Postman collections or automated tests

### Frontend Testing
1. **Component Tests**: React Native Testing Library
2. **E2E Tests**: Detox or Appium
3. **Snapshot Tests**: UI regression testing

## Future Architecture Considerations

### Microservices Migration
- **Funding Service**: Separate service for P2P matching
- **Betting Service**: Game logic and payouts
- **Notification Service**: Push notifications
- **Analytics Service**: Reporting and dashboards

### Event-Driven Architecture
- **Event Sourcing**: Track all state changes
- **CQRS**: Separate read/write models
- **Event Bus**: Pub/sub for cross-service communication

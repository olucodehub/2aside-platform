# Development Guidelines & Conventions

## Overview

This document outlines the coding standards, conventions, and best practices for the 2-Aside project. Following these guidelines ensures consistency, maintainability, and code quality across the codebase.

---

## Table of Contents

1. [General Principles](#general-principles)
2. [Backend Guidelines (C# / ASP.NET Core)](#backend-guidelines)
3. [Frontend Guidelines (React Native / TypeScript)](#frontend-guidelines)
4. [Database Guidelines](#database-guidelines)
5. [API Design Guidelines](#api-design-guidelines)
6. [Git Workflow](#git-workflow)
7. [Testing Guidelines](#testing-guidelines)
8. [Security Best Practices](#security-best-practices)
9. [Performance Guidelines](#performance-guidelines)
10. [Documentation Standards](#documentation-standards)

---

## General Principles

### Code Quality Principles

1. **DRY (Don't Repeat Yourself)**: Extract common logic into reusable functions/services
2. **SOLID Principles**: Follow SOLID design principles for object-oriented code
3. **KISS (Keep It Simple)**: Prefer simple, readable solutions over clever ones
4. **YAGNI (You Aren't Gonna Need It)**: Don't add functionality until it's needed
5. **Separation of Concerns**: Each component should have a single responsibility

### Code Review Standards

- All code changes should be reviewed before merging
- Code should be self-documenting with clear variable/function names
- Complex logic should have explanatory comments
- No commented-out code should be committed
- No console.log or Debug.WriteLine in production code

---

## Backend Guidelines

### C# Coding Standards

#### Naming Conventions

```csharp
// Classes: PascalCase
public class GameService { }

// Interfaces: PascalCase with 'I' prefix
public interface IGameService { }

// Methods: PascalCase
public async Task ProcessGameResultAsync(int gameId) { }

// Private fields: camelCase with underscore prefix
private readonly IGameService _gameService;

// Properties: PascalCase
public decimal UsdtBalance { get; set; }

// Local variables: camelCase
var userId = 123;

// Constants: PascalCase
private const string DefaultCurrency = "USDT";
```

#### File Organization

```csharp
// 1. Using statements (organized)
using System;
using System.Collections.Generic;
using Microsoft.EntityFrameworkCore;

// 2. Namespace
namespace TwoAside.Services
{
    // 3. Class with XML documentation
    /// <summary>
    /// Service for managing game operations and results
    /// </summary>
    public class GameService : IGameService
    {
        // 4. Fields
        private readonly BettingDbContext _context;

        // 5. Constructor
        public GameService(BettingDbContext context)
        {
            _context = context;
        }

        // 6. Public methods
        public async Task ProcessGameResultAsync(int gameId)
        {
            // Implementation
        }

        // 7. Private methods
        private void ValidateGameResult()
        {
            // Implementation
        }
    }
}
```

#### Async/Await Best Practices

```csharp
// ✅ Good: Async all the way
public async Task<User> GetUserAsync(int userId)
{
    return await _context.Users
        .FirstOrDefaultAsync(u => u.Id == userId);
}

// ❌ Bad: Blocking on async code
public User GetUser(int userId)
{
    return _context.Users
        .FirstOrDefaultAsync(u => u.Id == userId).Result; // Don't do this!
}

// ✅ Good: Use ConfigureAwait(false) in library code
public async Task<User> GetUserAsync(int userId)
{
    return await _context.Users
        .FirstOrDefaultAsync(u => u.Id == userId)
        .ConfigureAwait(false);
}
```

#### Dependency Injection

```csharp
// ✅ Good: Constructor injection
public class GameController : ControllerBase
{
    private readonly IGameService _gameService;
    private readonly ILogger<GameController> _logger;

    public GameController(
        IGameService gameService,
        ILogger<GameController> logger)
    {
        _gameService = gameService;
        _logger = logger;
    }
}

// ❌ Bad: Service locator pattern
public class GameController : ControllerBase
{
    public IActionResult GetGames()
    {
        var service = HttpContext.RequestServices
            .GetService<IGameService>(); // Avoid this
    }
}
```

#### Error Handling

```csharp
// ✅ Good: Specific exception handling with logging
public async Task<IActionResult> GetUser(int id)
{
    try
    {
        var user = await _userService.GetUserAsync(id);
        if (user == null)
        {
            return NotFound(new { message = "User not found" });
        }
        return Ok(user);
    }
    catch (DbUpdateException ex)
    {
        _logger.LogError(ex, "Database error while fetching user {UserId}", id);
        return StatusCode(500, new { message = "Database error occurred" });
    }
    catch (Exception ex)
    {
        _logger.LogError(ex, "Unexpected error while fetching user {UserId}", id);
        return StatusCode(500, new { message = "An error occurred" });
    }
}

// ❌ Bad: Swallowing exceptions
public async Task<IActionResult> GetUser(int id)
{
    try
    {
        var user = await _userService.GetUserAsync(id);
        return Ok(user);
    }
    catch
    {
        return null; // Don't do this!
    }
}
```

#### LINQ Best Practices

```csharp
// ✅ Good: Single database query with includes
var user = await _context.Users
    .Include(u => u.BankDetails)
    .Include(u => u.Referrals)
    .FirstOrDefaultAsync(u => u.Id == userId);

// ❌ Bad: N+1 queries
var user = await _context.Users.FirstOrDefaultAsync(u => u.Id == userId);
var bankDetails = await _context.BankDetails.FirstOrDefaultAsync(b => b.UserId == userId);

// ✅ Good: Materialize before complex operations
var users = await _context.Users
    .Where(u => u.IsBlocked == false)
    .ToListAsync();
var processedUsers = users.Select(u => ComplexOperation(u));

// ❌ Bad: Complex operations in query
var users = await _context.Users
    .Select(u => ComplexOperation(u)) // This might not translate to SQL
    .ToListAsync();
```

#### DTOs and Models

```csharp
// ✅ Good: Separate DTOs from entities
public class LoginDto
{
    [Required]
    [StringLength(50)]
    public string Username { get; set; }

    [Required]
    [StringLength(100)]
    public string Password { get; set; }
}

public class UserResponseDto
{
    public int Id { get; set; }
    public string Username { get; set; }
    public decimal UsdtBalance { get; set; }
    // Don't include PasswordHash or sensitive data
}

// Map entities to DTOs
var userDto = new UserResponseDto
{
    Id = user.Id,
    Username = user.Username,
    UsdtBalance = user.UsdtBalance
};
```

---

## Frontend Guidelines

### TypeScript Coding Standards

#### Naming Conventions

```typescript
// Interfaces: PascalCase with 'I' prefix (optional) or just PascalCase
interface User {
  id: number;
  username: string;
}

// Types: PascalCase
type Currency = 'USDT' | 'NAIRA';

// Components: PascalCase
export default function Dashboard() { }

// Functions: camelCase
const fetchUserData = async () => { }

// Constants: UPPER_SNAKE_CASE
const API_BASE_URL = 'http://localhost:5039/api';

// Variables: camelCase
const userId = 123;
```

#### Component Structure

```typescript
// 1. Imports
import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useAuth } from '@/context/AuthContext';

// 2. Types/Interfaces
interface DashboardProps {
  userId: number;
}

// 3. Component
export default function Dashboard({ userId }: DashboardProps) {
  // 3.1 Hooks
  const { user } = useAuth();
  const [balance, setBalance] = useState(0);

  // 3.2 Effects
  useEffect(() => {
    fetchBalance();
  }, [userId]);

  // 3.3 Functions
  const fetchBalance = async () => {
    // Implementation
  };

  // 3.4 Render
  return (
    <View style={styles.container}>
      <Text>Balance: {balance}</Text>
    </View>
  );
}

// 4. Styles
const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
  },
});
```

#### React Hooks Best Practices

```typescript
// ✅ Good: Dependencies array
useEffect(() => {
  fetchData(userId);
}, [userId]); // Include all dependencies

// ❌ Bad: Missing dependencies
useEffect(() => {
  fetchData(userId);
}, []); // Missing userId dependency

// ✅ Good: Cleanup functions
useEffect(() => {
  const timer = setInterval(() => {
    fetchData();
  }, 5000);

  return () => clearInterval(timer); // Cleanup
}, []);

// ✅ Good: Custom hooks for reusable logic
function useWalletBalance(userId: number) {
  const [balance, setBalance] = useState(0);

  useEffect(() => {
    const fetchBalance = async () => {
      const response = await api.get(`/wallet/balance`);
      setBalance(response.data.balance);
    };
    fetchBalance();
  }, [userId]);

  return balance;
}
```

#### API Calls and Error Handling

```typescript
// ✅ Good: Proper error handling with loading states
const [data, setData] = useState(null);
const [loading, setLoading] = useState(false);
const [error, setError] = useState<string | null>(null);

const fetchData = async () => {
  setLoading(true);
  setError(null);

  try {
    const response = await api.get('/games/upcoming');
    setData(response.data);
  } catch (err: any) {
    setError(err.response?.data?.message || 'An error occurred');
    Toast.show({
      type: 'error',
      text1: 'Error',
      text2: error,
    });
  } finally {
    setLoading(false);
  }
};

// ❌ Bad: No error handling
const fetchData = async () => {
  const response = await api.get('/games/upcoming');
  setData(response.data);
};
```

#### Type Safety

```typescript
// ✅ Good: Type everything
interface Game {
  id: number;
  homeTeam: string;
  awayTeam: string;
  odds: number;
}

const processGame = (game: Game): string => {
  return `${game.homeTeam} vs ${game.awayTeam}`;
};

// ❌ Bad: Using 'any'
const processGame = (game: any) => {
  return game.homeTeam + ' vs ' + game.awayTeam;
};

// ✅ Good: Union types for specific values
type BetStatus = 'pending' | 'won' | 'lost' | 'cancelled';

// ❌ Bad: String without constraints
type BetStatus = string;
```

#### State Management

```typescript
// ✅ Good: Context for global state
export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);

  const login = async (username: string, password: string) => {
    // Implementation
  };

  const value = {
    user,
    token,
    login,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// ✅ Good: Custom hook for context
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
```

---

## Database Guidelines

### Entity Design

```csharp
// ✅ Good: Clear entity with validation
public class User
{
    public int Id { get; set; }

    [Required]
    [StringLength(50)]
    public string Username { get; set; }

    [Required]
    [EmailAddress]
    public string Email { get; set; }

    [Required]
    public string PasswordHash { get; set; }

    [Column(TypeName = "decimal(18,2)")]
    public decimal UsdtBalance { get; set; }

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    // Navigation properties
    public virtual ICollection<BetRegistration> Bets { get; set; }
    public virtual BankDetails BankDetails { get; set; }
}
```

### Migration Best Practices

```bash
# Create migration with descriptive name
dotnet ef migrations add AddUserVerificationFields

# Review migration before applying
# Check Up() and Down() methods

# Apply migration
dotnet ef database update

# Rollback if needed
dotnet ef database update PreviousMigrationName
```

### DbContext Configuration

```csharp
protected override void OnModelCreating(ModelBuilder modelBuilder)
{
    // ✅ Good: Configure relationships explicitly
    modelBuilder.Entity<User>()
        .HasOne(u => u.BankDetails)
        .WithOne(b => b.User)
        .HasForeignKey<BankDetails>(b => b.UserId)
        .OnDelete(DeleteBehavior.Cascade);

    // ✅ Good: Configure indexes
    modelBuilder.Entity<User>()
        .HasIndex(u => u.Username)
        .IsUnique();

    // ✅ Good: Configure decimal precision
    modelBuilder.Entity<User>()
        .Property(u => u.UsdtBalance)
        .HasColumnType("decimal(18,2)");
}
```

---

## API Design Guidelines

### REST Conventions

```csharp
// ✅ Good: RESTful endpoints
[HttpGet("api/games")]              // GET /api/games
[HttpGet("api/games/{id}")]         // GET /api/games/123
[HttpPost("api/games")]             // POST /api/games
[HttpPut("api/games/{id}")]         // PUT /api/games/123
[HttpDelete("api/games/{id}")]      // DELETE /api/games/123

// ✅ Good: Nested resources
[HttpGet("api/users/{userId}/bets")]

// ✅ Good: Action endpoints for non-CRUD operations
[HttpPost("api/funding/cancel")]
[HttpPost("api/games/{id}/process-result")]
```

### Request/Response Standards

```csharp
// ✅ Good: Consistent response structure
public class ApiResponse<T>
{
    public bool Success { get; set; }
    public T Data { get; set; }
    public string Message { get; set; }
    public List<string> Errors { get; set; }
}

// Success response
return Ok(new ApiResponse<User>
{
    Success = true,
    Data = user,
    Message = "User retrieved successfully"
});

// Error response
return BadRequest(new ApiResponse<object>
{
    Success = false,
    Message = "Invalid request",
    Errors = new List<string> { "Username is required" }
});
```

### HTTP Status Codes

```csharp
// 200 OK - Successful GET, PUT, PATCH
return Ok(data);

// 201 Created - Successful POST
return CreatedAtAction(nameof(GetUser), new { id = user.Id }, user);

// 204 No Content - Successful DELETE
return NoContent();

// 400 Bad Request - Invalid input
return BadRequest(new { message = "Invalid data" });

// 401 Unauthorized - Not authenticated
return Unauthorized();

// 403 Forbidden - Authenticated but not authorized
return Forbid();

// 404 Not Found - Resource doesn't exist
return NotFound(new { message = "User not found" });

// 500 Internal Server Error - Server error
return StatusCode(500, new { message = "An error occurred" });
```

---

## Git Workflow

### Branch Naming

```bash
# Feature branches
feature/add-pagination
feature/user-verification

# Bug fix branches
bugfix/fix-login-error
bugfix/wallet-calculation

# Hotfix branches (urgent production fixes)
hotfix/security-patch

# Refactoring branches
refactor/simplify-matching-service
```

### Commit Messages

```bash
# ✅ Good: Clear, descriptive commits
git commit -m "Add pagination to games listing endpoint"
git commit -m "Fix wallet balance calculation for NAIRA"
git commit -m "Refactor MatchingService for better performance"

# ❌ Bad: Vague commits
git commit -m "Fix bug"
git commit -m "Update code"
git commit -m "WIP"
```

### Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring
- `docs`: Documentation changes
- `test`: Adding tests
- `style`: Code style changes (formatting, etc.)
- `chore`: Maintenance tasks

**Example:**
```
feat: Add pagination to games API

- Add page and pageSize query parameters
- Return total count and page metadata
- Update frontend to support pagination
- Default page size is 20 games

Closes #123
```

### Pull Request Guidelines

1. **Title**: Clear and descriptive
2. **Description**: Explain what and why
3. **Testing**: Describe how it was tested
4. **Screenshots**: For UI changes
5. **Checklist**:
   - [ ] Code follows style guidelines
   - [ ] Tests added/updated
   - [ ] Documentation updated
   - [ ] No breaking changes (or documented)

---

## Testing Guidelines

### Backend Unit Tests (Recommended)

```csharp
[Fact]
public async Task ProcessGameResult_ShouldCreditWinner()
{
    // Arrange
    var options = new DbContextOptionsBuilder<BettingDbContext>()
        .UseInMemoryDatabase(databaseName: "TestDb")
        .Options;

    using var context = new BettingDbContext(options);
    var service = new GameService(context);

    var game = new Game { Id = 1, Result = "Home" };
    var user = new User { Id = 1, UsdtBalance = 100 };
    context.Games.Add(game);
    context.Users.Add(user);
    await context.SaveChangesAsync();

    // Act
    await service.ProcessGameResultAsync(1, "Home");

    // Assert
    var updatedUser = await context.Users.FindAsync(1);
    Assert.True(updatedUser.UsdtBalance > 100);
}
```

### Frontend Tests (Recommended)

```typescript
import { render, fireEvent, waitFor } from '@testing-library/react-native';

describe('LoginScreen', () => {
  it('should display error for invalid credentials', async () => {
    const { getByPlaceholderText, getByText } = render(<LoginScreen />);

    const usernameInput = getByPlaceholderText('Username');
    const passwordInput = getByPlaceholderText('Password');
    const loginButton = getByText('Login');

    fireEvent.changeText(usernameInput, 'testuser');
    fireEvent.changeText(passwordInput, 'wrongpassword');
    fireEvent.press(loginButton);

    await waitFor(() => {
      expect(getByText('Invalid credentials')).toBeTruthy();
    });
  });
});
```

---

## Security Best Practices

### Authentication

```csharp
// ✅ Good: Use strong JWT keys (32+ characters)
"Jwt": {
  "Key": "your-secure-random-key-min-32-chars",
  "ExpirationMinutes": 60
}

// ✅ Good: Hash passwords with BCrypt
var hashedPassword = BCrypt.Net.BCrypt.HashPassword(password);

// ✅ Good: Verify passwords securely
var isValid = BCrypt.Net.BCrypt.Verify(password, user.PasswordHash);
```

### Input Validation

```csharp
// ✅ Good: Validate all inputs
public async Task<IActionResult> CreateFundingRequest([FromBody] FundingRequestDto dto)
{
    if (!ModelState.IsValid)
    {
        return BadRequest(ModelState);
    }

    if (dto.Amount <= 0)
    {
        return BadRequest(new { message = "Amount must be positive" });
    }

    // Process request
}
```

### Secure Configuration

```csharp
// ✅ Good: Use environment variables for secrets
var connectionString = Environment.GetEnvironmentVariable("DB_CONNECTION_STRING");
var jwtKey = Environment.GetEnvironmentVariable("JWT_KEY");

// ❌ Bad: Hardcoded secrets
var connectionString = "Server=myserver;Password=secret123";
```

---

## Performance Guidelines

### Backend Performance

```csharp
// ✅ Good: Async operations
public async Task<List<Game>> GetGamesAsync()
{
    return await _context.Games.ToListAsync();
}

// ✅ Good: Use pagination
public async Task<List<Game>> GetGamesAsync(int page, int pageSize)
{
    return await _context.Games
        .Skip((page - 1) * pageSize)
        .Take(pageSize)
        .ToListAsync();
}

// ✅ Good: Cache expensive operations
var cacheKey = $"Games_{page}_{pageSize}";
if (!_cache.TryGetValue(cacheKey, out List<Game> games))
{
    games = await GetGamesFromDb(page, pageSize);
    _cache.Set(cacheKey, games, TimeSpan.FromMinutes(5));
}
```

### Frontend Performance

```typescript
// ✅ Good: Memoize expensive computations
const expensiveValue = useMemo(() => {
  return computeExpensiveValue(data);
}, [data]);

// ✅ Good: Use React.memo for pure components
const GameCard = React.memo(({ game }: { game: Game }) => {
  return <View>...</View>;
});

// ✅ Good: Debounce API calls
const debouncedSearch = useMemo(
  () => debounce((query: string) => {
    searchGames(query);
  }, 500),
  []
);
```

---

## Documentation Standards

### Code Documentation

```csharp
/// <summary>
/// Processes the result of a completed game and distributes payouts
/// </summary>
/// <param name="gameId">The unique identifier of the game</param>
/// <param name="result">The result of the game (e.g., "Home", "Away", "Draw")</param>
/// <returns>A task representing the asynchronous operation</returns>
/// <exception cref="ArgumentException">Thrown when gameId is invalid</exception>
public async Task ProcessGameResultAsync(int gameId, string result)
{
    // Implementation
}
```

### README Updates

- Keep README.md up to date with setup instructions
- Document environment variables
- Include example configuration files
- Add troubleshooting section

### API Documentation

- Use Swagger/OpenAPI for API documentation
- Add XML comments to controllers
- Include example requests/responses
- Document authentication requirements

---

## Code Review Checklist

Before submitting code for review:

- [ ] Code follows naming conventions
- [ ] No hardcoded values (use configuration)
- [ ] Error handling implemented
- [ ] Input validation added
- [ ] Async/await used properly
- [ ] No N+1 queries
- [ ] Cache invalidation handled
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No console.log or Debug.WriteLine
- [ ] No commented-out code
- [ ] Security considerations addressed
- [ ] Performance considerations addressed

---

## Tools and Extensions

### Recommended VS Code Extensions

- ESLint
- Prettier
- React Native Tools
- TypeScript Error Translator
- GitLens

### Recommended Visual Studio Extensions

- ReSharper (or built-in analyzers)
- CodeMaid
- SonarLint

### Recommended Tools

- Postman (API testing)
- Azure Data Studio (database management)
- Redis Insight (cache management)
- Expo Go (mobile testing)

---

## Contact and Questions

For questions about these guidelines or suggestions for improvements:

1. Open a discussion in the team chat
2. Create an issue in the repository
3. Update this document with proposed changes

---

**Last Updated**: 2025-01-19
**Version**: 1.0

# 2-Aside Demo - Step-by-Step Testing Guide

**Purpose:** Test the P2P matching system end-to-end
**Time Required:** ~15 minutes
**Prerequisites:** Services running, 2 test user accounts

---

## Quick Start Summary

1. **Create 2 users** (User A wants to fund, User B wants to withdraw)
2. **User A:** Create funding request for ₦500,000
3. **User B:** Create withdrawal request for ₦500,000
4. **Admin:** Run demo merge script
5. **Verify:** Both users see their matches
6. **User A:** Upload payment proof
7. **Admin:** Confirm completion

---

## Detailed Step-by-Step Instructions

### Step 0: Start Services

```powershell
cd C:\Dev\Rendezvous

# Stop any running services
.\stop-all-services.ps1

# Start all services fresh
.\start-all-services.ps1

# Wait for services to fully start (~30 seconds)
# You should see:
#   - API Gateway:      http://localhost:8000
#   - Auth Service:     http://localhost:8001
#   - Wallet Service:   http://localhost:8002
#   - User Service:     http://localhost:8003
#   - Funding Service:  http://localhost:8004
#   - Web Application:  http://localhost:3000
```

**Verify services are running:**
```powershell
# Check if all ports are listening
netstat -an | findstr "8000 8001 8002 8003 8004 3000"
```

You should see 6 listening ports.

---

### Step 1: Create Test User A (Funder)

1. **Open browser:** http://localhost:3000
2. **Click "Sign Up"**
3. **Fill in registration:**
   - Username: `alice`
   - Email: `alice@test.com`
   - Phone: `08012345678`
   - Password: `Test1234!`
   - Confirm Password: `Test1234!`
4. **Click "Create Account"**
5. **You should see:** "Registration successful" message
6. **You'll be automatically logged in**

---

### Step 2: Set Up Bank Details for User A

1. **On dashboard, you'll see:** "Complete your profile"
2. **Click "Setup" in navigation** or go to http://localhost:3000/setup
3. **Select Currency:** NAIRA
4. **Fill in bank details:**
   - Bank Name: `GTBank` (or any Nigerian bank)
   - Account Number: `0123456789`
   - Account Name: `Alice Test` (should auto-populate)
5. **Click "Save Bank Details"**
6. **You should see:** "Bank details saved successfully"

**What just happened:**
- ✅ NAIRA wallet created for Alice
- ✅ Bank account linked to wallet
- ✅ Referral code generated
- ✅ Alice can now create funding requests

---

### Step 3: Create Funding Request (User A)

1. **Click "Fund Wallet" in navigation**
2. **You should see:**
   - Next merge time (e.g., "9:00 AM WAT")
   - Quick select buttons with preset amounts
3. **Click the ₦500,000 button** (or enter custom amount)
4. **Review details:**
   - Amount: ₦500,000.00
   - Currency: NAIRA
   - Next merge time displayed
5. **Click "Create Funding Request"**
6. **You should see:**
   - Success message
   - "Redirecting to status page..."
   - Automatically redirected to status page

**Status Page Shows:**
- Your funding request for ₦500,000
- Status: "Pending Match"
- Requested time (in WAT)
- Next merge time

**What just happened:**
- ✅ Funding request created in database
- ✅ Request is pending (not matched yet)
- ✅ Alice is waiting for a withdrawer to be matched

---

### Step 4: Create Test User B (Withdrawer)

1. **Open a NEW INCOGNITO/PRIVATE window** (so you can be logged in as 2 users)
2. **Go to:** http://localhost:3000
3. **Click "Sign Up"**
4. **Fill in registration:**
   - Username: `bob`
   - Email: `bob@test.com`
   - Phone: `08087654321`
   - Password: `Test1234!`
   - Confirm Password: `Test1234!`
5. **Click "Create Account"**
6. **You'll be automatically logged in**

---

### Step 5: Set Up Bank Details for User B

1. **Click "Setup" in navigation**
2. **Select Currency:** NAIRA
3. **Fill in bank details:**
   - Bank Name: `Access Bank`
   - Account Number: `9876543210`
   - Account Name: `Bob Test`
4. **Click "Save Bank Details"**

**What just happened:**
- ✅ NAIRA wallet created for Bob
- ✅ Bank account linked
- ✅ Bob can now create withdrawal requests

---

### Step 6: Fund Bob's Wallet (Simulate Balance)

Bob needs a balance to withdraw from. Let's add funds manually via database:

```powershell
sqlcmd -S localhost -d RendezvousDB -Q "
-- Get Bob's NAIRA wallet ID
DECLARE @BobWalletId UNIQUEIDENTIFIER;
SELECT @BobWalletId = id FROM wallets
WHERE user_id = (SELECT id FROM users WHERE email = 'bob@test.com')
AND currency = 'NAIRA';

-- Add balance to Bob's wallet
UPDATE wallets
SET balance = 500000.00,
    total_deposited = 500000.00
WHERE id = @BobWalletId;

-- Verify
SELECT u.username, w.currency, w.balance
FROM wallets w
JOIN users u ON w.user_id = u.id
WHERE u.email = 'bob@test.com';
"
```

**Expected Output:**
```
username   currency   balance
bob        NAIRA      500000.00
```

**Alternative (If sqlcmd doesn't work):**
Use Azure Data Studio or SQL Server Management Studio to run the SQL commands manually.

---

### Step 7: Create Withdrawal Request (User B)

1. **In Bob's browser window, click "Withdraw"**
2. **You should see:**
   - Current balance: ₦500,000.00
   - Quick select buttons
3. **Click the ₦500,000 button**
4. **Review details:**
   - Amount: ₦500,000.00
   - Your balance will become: ₦0.00
5. **Click "Create Withdrawal Request"**
6. **You should see:**
   - Success message
   - Redirected to status page

**Status Page Shows:**
- Your withdrawal request for ₦500,000
- Status: "Pending Match"
- Requested time (in WAT)

**What just happened:**
- ✅ Withdrawal request created
- ✅ Bob's wallet balance deducted
- ✅ Bob is waiting to be matched with a funder

---

### Step 8: Run Demo Merge (Trigger Matching)

Now we have:
- ✅ Alice wants to FUND ₦500,000
- ✅ Bob wants to WITHDRAW ₦500,000
- ✅ Both are pending match

**Let's match them!**

```powershell
cd C:\Dev\Rendezvous
.\test-merge-demo.ps1
```

**The script will prompt you:**

1. **Enter Admin Email:** (Use your admin account or create one first)
   - If you don't have an admin, run:
   ```powershell
   sqlcmd -S localhost -d RendezvousDB -Q "
   UPDATE users SET is_admin = 1 WHERE email = 'alice@test.com';
   "
   ```
   Then use: `alice@test.com`

2. **Enter Admin Password:** `Test1234!`

3. **Script will show:**
   ```
   [OK] Login successful

   ========================================
     Step 1: Viewing Pending Requests
   ========================================

   Funding Requests:
     Count: 1
     Total NAIRA: ₦500,000.00
     Total USDT: $0.00

     Details:
       - alice: NAIRA 500000.0 (Opted In: False)

   Withdrawal Requests:
     Count: 1
     Total NAIRA: ₦500,000.00
     Total USDT: $0.00

     Details:
       - bob: NAIRA 500000.0 (Opted In: False)
   ```

4. **Script asks:** "Do you want to trigger a merge now? (Y/N)"
   - Type: `Y` and press Enter

5. **Script will show:**
   ```
   [OK] Merge completed successfully!

   Merge Results:
   {
     "triggered_by": "alice",
     "merge_result": {
       "matched_pairs": 1,
       "total_amount_matched": 500000.0
     },
     "note": "This was a demo merge triggered manually"
   }
   ```

**What just happened:**
- ✅ Matching algorithm ran
- ✅ Alice matched with Bob
- ✅ Match pair created in database
- ✅ Both requests marked as fully matched

---

### Step 9: Verify Match - User A (Alice)

1. **In Alice's browser window:**
2. **Go to "Funding Status"** or refresh the status page
3. **You should now see:**
   ```
   Status: Matched ✓
   Matched Amount: ₦500,000.00

   Matched Withdrawal Details:
   - Username: bob
   - Bank: Access Bank
   - Account Number: 9876543210
   - Account Name: Bob Test

   Instructions:
   Send ₦500,000.00 to the bank account above.
   Then upload payment proof below.
   ```

4. **Upload Payment Proof section visible**

**What this means:**
- Alice now knows Bob's bank details
- Alice should send ₦500,000 to Bob's account
- Alice will upload proof after sending

---

### Step 10: Verify Match - User B (Bob)

1. **In Bob's browser window (incognito):**
2. **Go to "Withdrawal Status"** or refresh the status page
3. **You should see:**
   ```
   Status: Matched ✓
   Matched Amount: ₦500,000.00

   Matched Funder Details:
   - Username: alice
   - Bank: GTBank
   - Account Number: 0123456789
   - Account Name: Alice Test

   Instructions:
   Wait for alice to send money to your account.
   Once received, transaction will be complete.
   ```

**What this means:**
- Bob knows Alice will send money to his account
- Bob should expect ₦500,000 in his Access Bank account
- Bob waits for Alice to upload proof

---

### Step 11: Upload Payment Proof (User A)

**In real life:** Alice would:
1. Send ₦500,000 from her personal bank to Bob's Access Bank account
2. Get a receipt/screenshot
3. Upload the proof

**For testing:**

1. **In Alice's browser, on the funding status page:**
2. **Find "Upload Payment Proof" section**
3. **Click "Choose File"**
4. **Select any image file** (for testing, can be any .jpg/.png)
   - In production, this would be a bank receipt screenshot
5. **Add optional note:** "Sent via bank transfer - Reference: ABC123"
6. **Click "Upload Proof"**
7. **You should see:**
   ```
   ✓ Payment proof uploaded successfully
   Status: Awaiting Admin Confirmation
   ```

**What just happened:**
- ✅ Proof uploaded to server (would be Azure Blob Storage in production)
- ✅ Proof URL saved in match pair record
- ✅ Admin notified to verify payment

---

### Step 12: Admin Confirms Payment

**Admin needs to:**
1. Verify Bob actually received the money in his bank account
2. Confirm the transaction is complete

**Via API (Quick Test):**
```powershell
# Get the match pair ID
$token = "YOUR_ADMIN_TOKEN_HERE"  # From login

# Get all match pairs
Invoke-RestMethod -Uri "http://localhost:8004/admin/matches/pending" `
  -Headers @{ Authorization = "Bearer $token" } `
  | ConvertTo-Json -Depth 5

# Confirm the match (replace MATCH_PAIR_ID with actual ID)
Invoke-RestMethod -Uri "http://localhost:8004/admin/match/MATCH_PAIR_ID/confirm" `
  -Method Post `
  -Headers @{ Authorization = "Bearer $token" } `
  | ConvertTo-Json
```

**Or via Database (Quick Test):**
```powershell
sqlcmd -S localhost -d RendezvousDB -Q "
-- Confirm the match pair
UPDATE funding_match_pairs
SET is_confirmed = 1, confirmed_at = GETDATE()
WHERE id = (SELECT TOP 1 id FROM funding_match_pairs ORDER BY created_at DESC);

-- Mark funding request as complete
UPDATE funding_requests
SET is_completed = 1
WHERE id IN (
  SELECT funding_request_id
  FROM funding_match_pairs
  WHERE id = (SELECT TOP 1 id FROM funding_match_pairs ORDER BY created_at DESC)
);

-- Mark withdrawal request as complete
UPDATE withdrawal_requests
SET is_completed = 1
WHERE id IN (
  SELECT withdrawal_request_id
  FROM funding_match_pairs
  WHERE id = (SELECT TOP 1 id FROM funding_match_pairs ORDER BY created_at DESC)
);
"
```

---

### Step 13: Verify Completion

**Alice's View:**
1. Refresh funding status page
2. Should see: `Status: Completed ✓`
3. Transaction closed

**Bob's View:**
1. Refresh withdrawal status page
2. Should see: `Status: Completed ✓`
3. Withdrawal processed

**Alice's Wallet:**
- Balance increased by ₦500,000

**Bob's Wallet:**
- Balance remains 0 (already deducted when withdrawal was requested)

---

## Test Scenario Summary

| Step | User | Action | Result |
|------|------|--------|--------|
| 1 | Alice | Sign up | Account created |
| 2 | Alice | Add bank details | Wallet created |
| 3 | Alice | Create funding request ₦500K | Request pending |
| 4 | Bob | Sign up | Account created |
| 5 | Bob | Add bank details | Wallet created |
| 6 | DB Admin | Give Bob ₦500K balance | Balance added |
| 7 | Bob | Create withdrawal request ₦500K | Request pending |
| 8 | Admin | Run merge script | Alice ↔ Bob matched |
| 9 | Alice | View match | See Bob's bank details |
| 10 | Bob | View match | See Alice's bank details |
| 11 | Alice | Upload proof | Proof uploaded |
| 12 | Admin | Confirm payment | Transaction complete |
| 13 | Both | Check status | Both show "Completed" |

---

## Expected Database State After Demo

**users table:**
```
id  username  email           is_admin
--- --------- --------------- --------
1   alice     alice@test.com  1
2   bob       bob@test.com    0
```

**wallets table:**
```
user_id  currency  balance
-------  --------  --------
1        NAIRA     500000.00  (Alice got funded)
2        NAIRA     0.00       (Bob withdrew)
```

**funding_requests table:**
```
wallet_id  amount     is_fully_matched  is_completed
---------  ---------  ----------------  ------------
1          500000.00  1                 1
```

**withdrawal_requests table:**
```
wallet_id  amount     is_fully_matched  is_completed
---------  ---------  ----------------  ------------
2          500000.00  1                 1
```

**funding_match_pairs table:**
```
funding_request_id  withdrawal_request_id  amount     is_confirmed  payment_proof_url
------------------  ---------------------  ---------  ------------  -----------------
1                   1                      500000.00  1             /uploads/xxx.jpg
```

---

## Troubleshooting

### Issue: "Admin access required"
**Solution:** Make user admin:
```powershell
sqlcmd -S localhost -d RendezvousDB -Q "
UPDATE users SET is_admin = 1 WHERE email = 'alice@test.com';
"
```

### Issue: "No pending requests found"
**Solution:** Go back and create funding/withdrawal requests in Steps 3 and 7.

### Issue: Bob can't create withdrawal (insufficient balance)
**Solution:** Run Step 6 to add balance to Bob's wallet.

### Issue: Services not running
**Solution:**
```powershell
cd C:\Dev\Rendezvous
.\stop-all-services.ps1
.\start-all-services.ps1
```

### Issue: "Port already in use"
**Solution:** Kill processes on conflicting ports:
```powershell
# Find process on port 8004 (example)
netstat -ano | findstr :8004

# Kill process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

---

## Clean Up After Testing

If you want to reset and test again:

```powershell
# Option 1: Delete test users
sqlcmd -S localhost -d RendezvousDB -Q "
DELETE FROM funding_match_pairs;
DELETE FROM funding_requests;
DELETE FROM withdrawal_requests;
DELETE FROM wallets WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%@test.com');
DELETE FROM users WHERE email LIKE '%@test.com';
"

# Option 2: Keep users but reset transactions
sqlcmd -S localhost -d RendezvousDB -Q "
DELETE FROM funding_match_pairs;
DELETE FROM funding_requests;
DELETE FROM withdrawal_requests;
UPDATE wallets SET balance = 0, total_deposited = 0 WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%@test.com');
"
```

---

## Next: Test Additional Scenarios

1. **Partial Matching:**
   - Alice funds ₦1,000,000
   - Bob withdraws ₦300,000
   - Charlie withdraws ₦700,000
   - Alice should be matched with both

2. **Admin Wallet Fallback:**
   - Alice funds ₦500,000
   - No one wants to withdraw
   - Admin wallet acts as withdrawer

3. **Multiple Currency:**
   - Alice funds USDT $500
   - Bob withdraws USDT $500
   - Test USDT wallet addresses

---

**You're all set! Run the demo and see the matching system in action! 🚀**

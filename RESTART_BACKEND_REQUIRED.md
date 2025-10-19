# ⚠️ Backend Restart Required

## Issue

Active Instances showing "Instance #undefined"

## Cause

**Backend needs to be restarted** to apply the recent fixes:
1. Active instances lookup fix
2. CSV-based session data
3. Last success/attempt tracking
4. Cooldown check improvements

## Solution

### Step 1: Stop Backend

Press `Ctrl+C` in the terminal running the backend

### Step 2: Restart Backend

```bash
cd backend
python app.py
```

### Step 3: Refresh Browser

Press `F5` or click refresh

## What Will Be Fixed

After restart, you should see:

**Before:**
```
Instance #undefined⏸️ Paused - Hourly Limit
IP: 119.13.231.144
Votes: 0
```

**After:**
```
Instance #11⏸️ Paused - Hourly Limit
IP: 119.13.231.144
Votes: 1
```

## All Recent Fixes Applied

1. ✅ Active instances lookup (by IP, then get instance_id)
2. ✅ CSV-based session data (source of truth)
3. ✅ Last successful vote + last attempted vote
4. ✅ Cooldown check using time_of_click
5. ✅ File flushing for session data
6. ✅ Variable scope fixes
7. ✅ Monitoring state persistence

## Quick Restart

**Windows:**
```powershell
# In backend terminal
Ctrl+C
python app.py
```

**Then refresh browser (F5)**

## Verification

After restart, check:
1. ✅ Active Instances show correct instance IDs
2. ✅ Sessions tab shows last success & last attempt
3. ✅ Vote counts are accurate
4. ✅ Cooldown checking works

## Status

⚠️ **Action Required:** Restart backend to apply all fixes

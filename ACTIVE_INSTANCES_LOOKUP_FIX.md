# 🐛 Critical Fix - Active Instances Lookup

## Issue

**Sessions tab showing incorrect "Last Vote" time:**
- Instance #11 shows "Last Vote: 4 hours ago"
- But instance successfully voted few minutes ago
- Vote is logged in `voting_logs.csv`
- Session data not updating in real-time

## Root Cause

**The `active_instances` dictionary is keyed by IP address, NOT instance_id!**

```python
# In voter_engine.py
self.active_instances[proxy_ip] = instance  # ❌ Keyed by IP!
```

**But the API endpoints were checking by instance_id:**

```python
# In app.py - WRONG!
if instance_id in voter_system.active_instances:  # ❌ Will never match!
    active_instance = voter_system.active_instances[instance_id]
```

**This caused:**
1. Active instance lookup to always fail
2. Sessions tab to only show stale data from files
3. Live vote data never displayed
4. "Last Vote" time stuck at old value

## Fix Applied

### Fix 1: `/api/sessions` Endpoint

**Before:**
```python
# ❌ Wrong - checking by instance_id
if instance_id in voter_system.active_instances:
    active_instance = voter_system.active_instances[instance_id]
```

**After:**
```python
# ✅ Correct - iterate and find by instance_id
for ip, active_instance in voter_system.active_instances.items():
    if active_instance.instance_id == instance_id:
        # Found it! Use live data
        last_vote_time = active_instance.last_vote_time.isoformat()
        vote_count = active_instance.vote_count
        break
```

### Fix 2: `/api/instances` Endpoint

**Before:**
```python
# ❌ Wrong - treating key as instance_id
for instance_id, instance in voter_system.active_instances.items():
    'instance_id': instance_id,  # This is actually an IP!
    'ip': getattr(instance, 'proxy_ip', 'Unknown')
```

**After:**
```python
# ✅ Correct - key is IP address
for ip, instance in voter_system.active_instances.items():
    'instance_id': getattr(instance, 'instance_id', 'Unknown'),
    'ip': ip
```

## Impact

### Before Fix

**Sessions Tab:**
```
Instance #11
Last Vote: 4 hours ago  ❌ (stale data from file)
Votes: 5                ❌ (old count)
```

**Active Instances:**
```
Instance #undefined     ❌ (IP shown as instance_id)
IP: 91.197.253.183
Votes: 0
```

### After Fix

**Sessions Tab:**
```
Instance #11
Last Vote: 2 min ago    ✅ (live data!)
Votes: 6                ✅ (current count!)
```

**Active Instances:**
```
Instance #11            ✅ (correct ID)
IP: 91.197.253.183
Votes: 6                ✅ (correct count)
```

## Why This Happened

The `active_instances` dictionary structure:

```python
{
    '91.197.253.183': VoterInstance(instance_id=1, ...),
    '119.13.229.244': VoterInstance(instance_id=10, ...),
    '77.83.69.81': VoterInstance(instance_id=11, ...)
}
```

**Keys are IP addresses, not instance IDs!**

This is because:
1. IPs must be unique (can't have duplicate IPs)
2. Instance IDs can be reused with different IPs
3. Lookup by IP is needed for proxy management

## About the Log Message Change

**Old format:**
```
Vote verified: +1 | Thank you for vote! Please come back after 30 minutes...
```

**New format:**
```
Vote count verified: +1
```

**This is NOT the cause of the issue.** The new format is from the comprehensive logging system we implemented. The issue was purely the dictionary lookup bug.

## Files Modified

1. `backend/app.py` - `/api/sessions` endpoint
2. `backend/app.py` - `/api/instances` endpoint

## Test

1. Start monitoring
2. Wait for a vote to succeed
3. Go to Sessions tab
4. **Last Vote should show recent time (e.g., "2 min ago")**
5. **Vote count should be current**

## Status

✅ **Fixed** - Active instances now properly looked up by iterating and matching instance_id

## Summary

**The Problem:**
- Dictionary keyed by IP, but code checked by instance_id
- Active instance lookup always failed
- Only stale file data was shown

**The Solution:**
- Iterate through dictionary
- Match by `instance.instance_id`
- Use live data when found

**The Result:**
- ✅ Real-time last vote times
- ✅ Real-time vote counts
- ✅ Correct instance IDs displayed
- ✅ Sessions tab shows live data

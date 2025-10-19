# 🐛 Sessions Tab - Last Vote Time Fix

## Issue

The Sessions tab was showing incorrect "Last Vote" times - displaying old data from `session_info.json` instead of live data from active instances.

## Root Cause

The `/api/sessions` endpoint only read from saved `session_info.json` files, which are only updated when:
1. A session is first saved
2. After a successful vote (when `save_session_data()` is called)

**Problem:** If an instance is actively running and voting, the Sessions tab shows stale data from the last time the file was written.

## Fix Applied

**Now checks if instance is currently active and uses live data:**

```python
# Load session info from file
last_vote_time = session_info.get('last_vote_time', 'Never')
vote_count = session_info.get('vote_count', 0)

# ✅ If instance is active, get live data
if voter_system and hasattr(voter_system, 'active_instances'):
    if instance_id in voter_system.active_instances:
        active_instance = voter_system.active_instances[instance_id]
        
        # Use live last_vote_time
        if hasattr(active_instance, 'last_vote_time') and active_instance.last_vote_time:
            last_vote_time = active_instance.last_vote_time.isoformat()
        
        # Use live vote_count
        if hasattr(active_instance, 'vote_count'):
            vote_count = active_instance.vote_count
```

## How It Works

**For inactive instances:**
- ✅ Shows data from `session_info.json` (last saved state)

**For active instances:**
- ✅ Shows live data from memory (real-time)
- ✅ Last vote time updates immediately after vote
- ✅ Vote count updates immediately after vote

## Example

**Before fix:**
```
Instance #1
Last Vote: 232 min ago  ❌ (from old session_info.json)
Votes: 5                ❌ (from old session_info.json)
```

**After fix (instance is active and just voted):**
```
Instance #1
Last Vote: 1 min ago    ✅ (live data from active instance)
Votes: 6                ✅ (live data from active instance)
```

## Benefits

1. ✅ Real-time last vote time for active instances
2. ✅ Real-time vote count for active instances
3. ✅ Still shows saved data for inactive instances
4. ✅ No need to wait for file writes

## Test

1. Start monitoring
2. Wait for a vote to succeed
3. Go to Sessions tab
4. Last vote should show "X min ago" (recent time)
5. Vote count should be updated

**File Modified:** `backend/app.py` - `/api/sessions` endpoint

## Status

✅ **Fixed** - Sessions tab now shows live data for active instances

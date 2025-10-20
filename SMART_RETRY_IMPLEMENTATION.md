# Smart Retry Mechanism - Implementation Complete

## Overview
Implemented intelligent retry mechanism that differentiates between technical failures (retry in 5 minutes) and IP cooldown/hourly limits (wait 31 minutes). Additionally, hourly limits now pause ALL instances until the next full hour.

---

## Key Features

### 1. **Smart Retry Based on Failure Type**
- **Technical Failures:** Retry in 5 minutes
- **IP Cooldown/Hourly Limit:** Wait 31 minutes

### 2. **Global Hourly Limit Handling**
- When hourly limit detected, ALL instances pause
- Resume at next full hour (e.g., if detected at 3:45 PM, resume at 4:00 PM)
- Sequential resume to prevent memory overload

---

## Implementation Details

### Configuration (`config.py`)

```python
# Retry configuration (minutes to wait before retrying after failure)
RETRY_DELAY_TECHNICAL = 5   # Technical failures (button not found, exception, etc.)
RETRY_DELAY_COOLDOWN = 31   # IP cooldown / hourly limit (respect voting restrictions)
```

**Easy to tune:**
- Increase `RETRY_DELAY_TECHNICAL` if technical issues need more time
- Adjust `RETRY_DELAY_COOLDOWN` based on voting site requirements

---

## Failure Type Classification

### IP Cooldown (`ip_cooldown`) - Wait 31 minutes
1. Hourly limit reached
2. Already voted (30 min cooldown)
3. IP in cooldown period
4. Fallback cooldown detection

### Technical (`technical`) - Retry in 5 minutes
1. Vote button not found
2. Vote count did not increase
3. Exception during vote
4. Other technical errors

---

## Changes Made

### 1. VoterInstance Field (`voter_engine.py`)
```python
# Line 99
self.last_failure_type = None  # Type of failure: "ip_cooldown" or "technical"
```

### 2. Set Failure Type in Each Scenario

**Vote button not found (Line 665):**
```python
self.last_failure_type = "technical"
```

**Hourly limit detected (Line 804):**
```python
self.last_failure_type = "ip_cooldown"
```

**Vote count unchanged (Line 838):**
```python
self.last_failure_type = "technical"
```

**Exception (Line 979):**
```python
self.last_failure_type = "technical"
```

**Fallback cooldown (Line 937):**
```python
self.last_failure_type = "ip_cooldown"
```

**Clear on success (Line 703):**
```python
self.last_failure_type = None
```

### 3. Smart Retry Logic (`run_voting_cycle`)

**Before:**
```python
if success:
    await asyncio.sleep(31 * 60)
else:
    await asyncio.sleep(31 * 60)  # Same for all failures!
```

**After:**
```python
if success:
    await asyncio.sleep(RETRY_DELAY_COOLDOWN * 60)
else:
    if self.last_failure_type == "ip_cooldown":
        # Hourly limit - wait full cycle
        wait_minutes = RETRY_DELAY_COOLDOWN
        self.status = f"⏳ Cooldown ({wait_minutes} min)"
    else:
        # Technical failure - retry sooner
        wait_minutes = RETRY_DELAY_TECHNICAL
        self.status = f"🔄 Retry in {wait_minutes} min"
    
    await asyncio.sleep(wait_minutes * 60)
```

### 4. API Updates (`app.py`)

Added `last_failure_type` to:
- `/api/instances` endpoint (Line 376)
- Socket.IO `instances_update` emission (Line 217)

---

## Hourly Limit Handling

### Already Implemented (Verified)

**When hourly limit detected:**
1. Sets `global_hourly_limit = True`
2. Calculates next full hour:
   ```python
   next_hour = (datetime.now() + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
   ```
3. Pauses ALL active instances
4. Monitors and resumes at next full hour
5. Sequential resume (one by one with delays)

**Example:**
```
Hourly limit detected at 3:45 PM
  ↓
All instances paused
  ↓
Resume at 4:00 PM (next full hour)
  ↓
Sequential resume: Instance 1 → wait 5s → Instance 2 → wait 5s → ...
```

---

## Status Display

### New Status Messages

**Success:**
```
✅ Vote Successful
```

**IP Cooldown:**
```
⏳ Cooldown (31 min)
```

**Technical Failure:**
```
🔄 Retry in 5 min
```

**Hourly Limit (All Instances):**
```
⏸️ Paused - Hourly Limit
```

---

## Example Scenarios

### Scenario 1: Vote Button Not Found
```
1. Attempt vote → Button not found
2. Set: last_failure_type = "technical"
3. Status: "🔄 Retry in 5 min"
4. Wait 5 minutes
5. Retry vote → Maybe page loaded correctly now
```

### Scenario 2: Hourly Limit Detected
```
1. Instance #1 attempts vote → Hourly limit detected
2. Set: last_failure_type = "ip_cooldown"
3. Trigger: handle_hourly_limit()
   ↓
4. Pause ALL instances (not just #1)
5. Calculate next hour: 4:00 PM
6. Status (all): "⏸️ Paused - Hourly Limit"
7. Wait until 4:00 PM
8. Resume all instances sequentially
```

### Scenario 3: Exception then Success
```
1. Attempt vote → Network timeout exception
2. Set: last_failure_type = "technical"
3. Status: "🔄 Retry in 5 min"
4. Wait 5 minutes
5. Retry vote → Success! ✅
6. Clear: last_failure_type = None
7. Status: "✅ Vote Successful"
8. Wait 31 minutes for next vote
```

### Scenario 4: Mixed Failures
```
Instance #1:
  - Technical failure → Wait 5 min → Success → Wait 31 min

Instance #2:
  - Hourly limit → Pause ALL → Wait until next hour → Resume

Instance #3:
  - Success → Wait 31 min → Technical failure → Wait 5 min
```

---

## Benefits

### 1. **Faster Recovery**
- Technical issues retry in 5 minutes instead of 31
- More voting attempts per hour
- Quicker detection of resolved issues

### 2. **Respects Voting Rules**
- Hourly limits still wait 31 minutes
- All instances pause when hourly limit detected
- Resume at next full hour (URL-specific limit)

### 3. **Better Resource Utilization**
- Don't waste 31 minutes on technical failures
- Sequential resume prevents memory overload
- Smart retry based on failure type

### 4. **Clear User Feedback**
```
✅ Vote Successful        → Wait 31 min
⏳ Cooldown (31 min)      → Wait 31 min (hourly limit)
🔄 Retry in 5 min         → Wait 5 min (technical)
⏸️ Paused - Hourly Limit  → Wait until next hour (all instances)
```

---

## Countdown Timer Integration

The countdown timer automatically adapts to different wait times:

**Technical Failure (5 min):**
```
🔄 Retry in 5 min
⏱️ 5:00
⏱️ 4:59
⏱️ 4:58
...
Ready to vote
```

**Cooldown (31 min):**
```
⏳ Cooldown (31 min)
⏱️ 31:00
⏱️ 30:59
...
Ready to vote
```

**Hourly Limit (until next hour):**
```
⏸️ Paused - Hourly Limit
⏱️ 15:00  (if 15 minutes until 4:00 PM)
⏱️ 14:59
...
Ready to vote
```

---

## API Response

### New Field: `last_failure_type`

```json
{
  "instance_id": 1,
  "status": "🔄 Retry in 5 min",
  "last_failure_reason": "Could not find vote button",
  "last_failure_type": "technical",
  "seconds_remaining": 300
}
```

**Values:**
- `"ip_cooldown"` - Hourly limit / cooldown
- `"technical"` - Technical failure
- `null` - No failure or after success

---

## UI Display Enhancement (Optional)

### Show Failure Type Badge

**Technical Failure:**
```
❌ Last Failure: Could not find vote button (Technical)
🔄 Retry in 5 min
```

**IP Cooldown:**
```
❌ Last Failure: Hourly voting limit reached (Cooldown)
⏳ Cooldown (31 min)
```

### Color Coding
- **Technical:** Orange/Yellow (temporary issue)
- **Cooldown:** Blue (expected behavior)

---

## Testing

### Test Case 1: Technical Failure Recovery
1. **Simulate:** Temporarily break vote button selector
2. **Expected:** 
   - Status: "🔄 Retry in 5 min"
   - Countdown: 5:00 → 0:00
   - Retry after 5 minutes
3. **Verify:** Faster recovery when issue resolved

### Test Case 2: Hourly Limit Coordination
1. **Trigger:** Hit hourly limit on one instance
2. **Expected:**
   - ALL instances pause
   - Status: "⏸️ Paused - Hourly Limit"
   - Resume at next full hour (e.g., 4:00 PM)
3. **Verify:** All instances coordinated

### Test Case 3: Mixed Failures
1. **Instance #1:** Technical failure → Wait 5 min
2. **Instance #2:** Success → Wait 31 min
3. **Instance #3:** Hourly limit → ALL pause until next hour
4. **Verify:** Each uses correct wait time

### Test Case 4: Sequential Resume
1. **Trigger:** Hourly limit
2. **Wait:** Until next full hour
3. **Observe:** Instances resume one by one with 5s delays
4. **Verify:** No memory spike

---

## Configuration Tuning

### Adjust Retry Delays

**For slower servers:**
```python
RETRY_DELAY_TECHNICAL = 10  # Give more time for technical issues
RETRY_DELAY_COOLDOWN = 31   # Keep cooldown as is
```

**For faster recovery:**
```python
RETRY_DELAY_TECHNICAL = 3   # Quick retry for network issues
RETRY_DELAY_COOLDOWN = 31   # Keep cooldown as is
```

**For different voting sites:**
```python
RETRY_DELAY_TECHNICAL = 5
RETRY_DELAY_COOLDOWN = 60   # If site has 1-hour cooldown
```

---

## Logging

### New Log Messages

**Technical Failure:**
```
[CYCLE] Instance #1 technical failure, retrying in 5 minutes...
```

**IP Cooldown:**
```
[CYCLE] Instance #1 in cooldown, waiting 31 minutes...
```

**Hourly Limit (All Instances):**
```
[HOURLY_LIMIT] 🚫 HOURLY LIMIT DETECTED - Pausing ALL instances
[HOURLY_LIMIT] Will resume at 04:00 PM
[HOURLY_LIMIT] Paused 5 instances
```

**Resume:**
```
[HOURLY_LIMIT] ✅ Hourly limit expired - Resuming instances SEQUENTIALLY
[HOURLY_LIMIT] Resumed instance #1 (1/5)
[HOURLY_LIMIT] Waiting 5s before next resume...
```

---

## Files Modified

1. **backend/config.py**
   - Added `RETRY_DELAY_TECHNICAL = 5`
   - Added `RETRY_DELAY_COOLDOWN = 31`

2. **backend/voter_engine.py**
   - Imported retry delay configs
   - Added `last_failure_type` field (line 99)
   - Set failure type in 6 scenarios (lines 665, 703, 804, 838, 937, 979)
   - Updated `run_voting_cycle()` with smart retry logic (lines 1107-1120)

3. **backend/app.py**
   - Added `last_failure_type` to API response (line 376)
   - Added `last_failure_type` to Socket.IO emission (line 217)

---

## Summary

**Implemented:**
✅ Smart retry mechanism (5 min for technical, 31 min for cooldown)  
✅ Failure type tracking (`ip_cooldown` vs `technical`)  
✅ Different wait times based on failure type  
✅ Global hourly limit handling (all instances pause)  
✅ Resume at next full hour  
✅ Sequential resume to prevent memory overload  
✅ API includes failure type  
✅ Clear status messages  
✅ Configurable retry delays  

**Result:**
- Faster recovery from technical issues (5 min vs 31 min)
- Respects voting site cooldowns (31 min)
- All instances coordinate on hourly limits
- Better resource utilization
- Clear user feedback

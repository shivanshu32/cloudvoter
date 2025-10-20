# Retry Mechanism Design for Technical Failures

## Current Behavior (Problem)

**All failures wait 31 minutes:**
```python
if success:
    await asyncio.sleep(31 * 60)  # 31 minutes
else:
    await asyncio.sleep(31 * 60)  # 31 minutes (same for all failures!)
```

**Issues:**
- Technical failures (button not found, exception) wait 31 minutes unnecessarily
- Only cooldown/hourly limit should wait 31 minutes
- Technical failures could be retried much sooner (5 minutes)

---

## Proposed Solution

### Design Approach: Differentiate Failure Types

**Add failure type tracking to VoterInstance:**
```python
self.last_failure_type = None  # "ip_cooldown" or "technical"
```

**Different wait times based on failure type:**
- **IP Cooldown/Hourly Limit:** Wait 31 minutes (expected behavior)
- **Technical Failures:** Wait 5 minutes (retry sooner)

---

## Implementation Plan

### Step 1: Add Failure Type Tracking

**In VoterInstance.__init__:**
```python
# Voting state
self.last_vote_time = None
self.last_successful_vote = None
self.last_attempted_vote = None
self.last_failure_reason = None
self.last_failure_type = None  # NEW: Track failure type
self.vote_count = 0
self.failed_attempts = 0
```

### Step 2: Update attempt_vote() to Return Failure Type

**Current return:**
```python
return True   # Success
return False  # Failure (any type)
```

**Proposed return:**
```python
return ("success", None)           # Success
return ("failure", "ip_cooldown")  # Cooldown failure
return ("failure", "technical")    # Technical failure
```

**OR simpler approach - set instance variable:**
```python
# In each failure detection
self.last_failure_type = "ip_cooldown"  # or "technical"
return False
```

### Step 3: Update run_voting_cycle() to Use Different Wait Times

```python
# Attempt vote
success = await self.attempt_vote()

if success:
    self.status = "✅ Vote Successful"
    logger.info(f"[CYCLE] Instance #{self.instance_id} waiting 31 minutes...")
    await asyncio.sleep(31 * 60)  # 31 minute wait
else:
    # Check failure type to determine wait time
    if self.last_failure_type == "ip_cooldown":
        # Hourly limit / cooldown - wait full cycle
        self.status = "⏳ Cooldown"
        wait_minutes = 31
        logger.info(f"[CYCLE] Instance #{self.instance_id} in cooldown, waiting {wait_minutes} minutes...")
        await asyncio.sleep(wait_minutes * 60)
    else:
        # Technical failure - retry sooner
        self.status = "🔄 Retry in 5 min"
        wait_minutes = 5
        logger.info(f"[CYCLE] Instance #{self.instance_id} technical failure, retrying in {wait_minutes} minutes...")
        await asyncio.sleep(wait_minutes * 60)
```

---

## Configuration

**Add to config.py:**
```python
# Retry configuration
RETRY_DELAY_TECHNICAL = 5  # Minutes to wait before retrying technical failures
RETRY_DELAY_COOLDOWN = 31  # Minutes to wait for cooldown/hourly limit
```

---

## Detailed Implementation

### File: voter_engine.py

#### Change 1: Add failure type field
```python
# Line ~96
self.last_failure_type = None  # Track failure type: "ip_cooldown" or "technical"
```

#### Change 2: Set failure type in each failure scenario

**Scenario 1: Vote button not found (Line ~661)**
```python
self.last_attempted_vote = datetime.now()
self.last_failure_reason = "Could not find vote button"
self.last_failure_type = "technical"  # NEW
```

**Scenario 2: Hourly limit detected (Line ~791)**
```python
self.last_failure_reason = cooldown_message
self.last_failure_type = "ip_cooldown"  # NEW
```

**Scenario 3: Vote count unchanged (Line ~784)**
```python
self.last_failure_reason = "Vote count did not increase"
self.last_failure_type = "technical"  # NEW
```

**Scenario 4: Exception (Line ~891)**
```python
self.last_failure_reason = f"Exception: {str(e)[:100]}"
self.last_failure_type = "technical"  # NEW
```

**Scenario 5: Fallback cooldown (Line ~915)**
```python
self.last_failure_reason = cooldown_message
self.last_failure_type = "ip_cooldown"  # NEW
```

#### Change 3: Clear failure type on success
```python
# Line ~698
self.last_failure_reason = None
self.last_failure_type = None  # NEW
```

#### Change 4: Update run_voting_cycle with smart retry logic
```python
# Line ~1094-1103
success = await self.attempt_vote()

if success:
    self.status = "✅ Vote Successful"
    logger.info(f"[CYCLE] Instance #{self.instance_id} waiting 31 minutes...")
    await asyncio.sleep(31 * 60)
else:
    # Determine wait time based on failure type
    if self.last_failure_type == "ip_cooldown":
        # Hourly limit / cooldown - wait full cycle
        self.status = "⏳ Cooldown (31 min)"
        wait_minutes = 31
        logger.info(f"[CYCLE] Instance #{self.instance_id} in cooldown, waiting {wait_minutes} minutes...")
    else:
        # Technical failure - retry sooner
        self.status = "🔄 Retry in 5 min"
        wait_minutes = 5
        logger.info(f"[CYCLE] Instance #{self.instance_id} technical failure, retrying in {wait_minutes} minutes...")
    
    await asyncio.sleep(wait_minutes * 60)
```

---

## Benefits

### 1. **Faster Recovery from Technical Issues**
- Button not found → Retry in 5 minutes (maybe page loaded now)
- Exception → Retry in 5 minutes (maybe network recovered)
- Vote count issue → Retry in 5 minutes (maybe temporary glitch)

### 2. **Respects Cooldown Periods**
- Hourly limit → Still waits 31 minutes (correct behavior)
- Already voted → Still waits 31 minutes (correct behavior)

### 3. **Better Resource Utilization**
- Don't waste 31 minutes on technical failures
- More voting attempts per hour for technical issues
- Faster detection of resolved issues

### 4. **Clear Status Display**
```
✅ Vote Successful        → Wait 31 min
⏳ Cooldown (31 min)      → Wait 31 min (hourly limit)
🔄 Retry in 5 min         → Wait 5 min (technical failure)
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

### Scenario 2: Hourly Limit
```
1. Attempt vote → Hourly limit detected
2. Set: last_failure_type = "ip_cooldown"
3. Status: "⏳ Cooldown (31 min)"
4. Wait 31 minutes
5. Retry vote → Should work now
```

### Scenario 3: Exception then Success
```
1. Attempt vote → Exception (network timeout)
2. Set: last_failure_type = "technical"
3. Status: "🔄 Retry in 5 min"
4. Wait 5 minutes
5. Retry vote → Success! ✅
6. Clear: last_failure_type = None
7. Wait 31 minutes for next vote
```

---

## Advanced: Configurable Retry Delays

### Option 1: Simple Config
```python
# config.py
RETRY_DELAY_TECHNICAL = 5   # Minutes
RETRY_DELAY_COOLDOWN = 31   # Minutes
```

### Option 2: Per-Failure-Type Config
```python
# config.py
RETRY_DELAYS = {
    "button_not_found": 5,      # Maybe page will load
    "count_unchanged": 10,      # Give server more time
    "exception": 3,             # Quick retry for network issues
    "ip_cooldown": 31,          # Respect cooldown
    "hourly_limit": 31          # Respect hourly limit
}
```

### Option 3: Exponential Backoff
```python
# For repeated failures
retry_attempts = 0
wait_time = 5 * (2 ** retry_attempts)  # 5, 10, 20, 40 minutes
max_wait = 31  # Cap at 31 minutes
```

---

## Recommended Approach

**Use Simple Config (Option 1):**
- Easy to understand
- Easy to configure
- Covers 99% of use cases
- Two clear categories: technical vs cooldown

**Implementation:**
1. Add `last_failure_type` field
2. Set it in each failure scenario
3. Use it in `run_voting_cycle()` to determine wait time
4. Add config values for easy tuning

---

## Testing

### Test Case 1: Technical Failure Recovery
1. **Simulate:** Remove vote button from page
2. **Expected:** Retry in 5 minutes
3. **Verify:** Status shows "🔄 Retry in 5 min"
4. **Result:** Faster recovery when page fixed

### Test Case 2: Hourly Limit Respect
1. **Trigger:** Hit hourly limit
2. **Expected:** Wait 31 minutes
3. **Verify:** Status shows "⏳ Cooldown (31 min)"
4. **Result:** Respects cooldown period

### Test Case 3: Mixed Failures
1. **First attempt:** Technical failure → Wait 5 min
2. **Second attempt:** Success → Wait 31 min
3. **Third attempt:** Hourly limit → Wait 31 min
4. **Verify:** Each uses correct wait time

---

## Countdown Timer Update

The countdown timer will automatically work with different wait times:

**For technical failures (5 min):**
```
⏱️ 5:00
⏱️ 4:59
⏱️ 4:58
...
Ready to vote
```

**For cooldown (31 min):**
```
⏱️ 31:00
⏱️ 30:59
...
Ready to vote
```

---

## API/UI Updates

### Add to API response:
```python
{
    'instance_id': 1,
    'last_failure_type': 'technical',  # NEW
    'last_failure_reason': 'Could not find vote button',
    'seconds_remaining': 300  # 5 minutes for technical
}
```

### UI can show:
```
❌ Last Failure: Could not find vote button (Technical)
⏱️ 4:30 (Retrying soon)
```

vs

```
❌ Last Failure: Hourly voting limit reached (Cooldown)
⏱️ 28:30 (Normal cooldown)
```

---

## Summary

**Best Implementation:**
1. ✅ Add `last_failure_type` field to track failure category
2. ✅ Set it in each failure scenario ("ip_cooldown" or "technical")
3. ✅ Use it in `run_voting_cycle()` to determine wait time
4. ✅ Technical failures: 5 minutes
5. ✅ Cooldown failures: 31 minutes
6. ✅ Add config values for easy tuning
7. ✅ Update UI to show failure type and retry time

**Result:**
- Faster recovery from technical issues
- Respects cooldown periods
- Better resource utilization
- Clear user feedback

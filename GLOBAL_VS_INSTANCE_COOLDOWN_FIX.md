# Global vs Instance-Specific Cooldown Fix

## Problem Identified

**Issue:** The script was treating ALL cooldown messages as global hourly limits, causing ALL instances to pause when only ONE instance hit its 30-minute cooldown.

**Example:**
```
Instance #9: "You have voted already! Please come back at your next voting time of 30 minutes."
Result: ALL instances paused ❌ (INCORRECT)
```

**Root Cause:**
- The message "please come back at your next voting time" is instance-specific (30-minute cooldown)
- Script was triggering `handle_hourly_limit()` for ALL cooldown patterns
- This paused all instances unnecessarily

---

## Solution Implemented

### Distinguish Between Two Types of Cooldowns

#### 1. **Global Hourly Limit** (URL-wide)
- Affects ALL instances
- Should pause ALL instances
- Resume at next full hour

**Patterns:**
- "hourly limit"
- "someone has already voted out of this ip"

#### 2. **Instance-Specific Cooldown** (Per-instance)
- Affects ONLY that specific instance
- Should NOT pause other instances
- Instance waits individually (31 minutes)

**Patterns:**
- "please come back at your next voting time" (30-minute cooldown)
- "already voted" (instance-specific)
- "wait before voting again" (instance-specific)

---

## Implementation

### 1. Configuration (`config.py`)

Added two new pattern lists:

```python
# Global hourly limit patterns (these affect ALL instances, not just one)
# Only these patterns should trigger global pause of all instances
GLOBAL_HOURLY_LIMIT_PATTERNS = [
    "hourly limit",
    "someone has already voted out of this ip"
]

# Instance-specific cooldown patterns (only affect the specific instance)
# These should NOT trigger global pause
INSTANCE_COOLDOWN_PATTERNS = [
    "please come back at your next voting time",  # 30-minute cooldown
    "already voted",  # Instance-specific
    "wait before voting again"  # Instance-specific
]
```

### 2. Detection Logic (`voter_engine.py`)

**Before:**
```python
# Trigger global hourly limit handling
if self.voter_manager:
    asyncio.create_task(self.voter_manager.handle_hourly_limit())
```

**After:**
```python
# Check if this is a GLOBAL hourly limit or INSTANCE-SPECIFIC cooldown
is_global_limit = any(pattern in page_content.lower() for pattern in GLOBAL_HOURLY_LIMIT_PATTERNS)
is_instance_cooldown = any(pattern in page_content.lower() for pattern in INSTANCE_COOLDOWN_PATTERNS)

if is_global_limit:
    logger.warning(f"[GLOBAL_LIMIT] Instance #{self.instance_id} detected GLOBAL hourly limit - will pause ALL instances")
elif is_instance_cooldown:
    logger.info(f"[INSTANCE_COOLDOWN] Instance #{self.instance_id} in instance-specific cooldown (30 min) - only this instance affected")

# ONLY trigger global hourly limit handling for GLOBAL patterns
if is_global_limit and self.voter_manager:
    logger.warning(f"[GLOBAL_LIMIT] Triggering global hourly limit handler")
    asyncio.create_task(self.voter_manager.handle_hourly_limit())
else:
    logger.info(f"[INSTANCE_COOLDOWN] Instance #{self.instance_id} will wait individually, other instances continue")
```

---

## Behavior Changes

### Before Fix

**Scenario:** Instance #9 tries to vote within 30 minutes
```
Instance #9: "Please come back at your next voting time of 30 minutes"
    ↓
Script: Triggers handle_hourly_limit()
    ↓
Result: ALL instances paused ❌
    ↓
Status: All show "⏸️ Paused - Hourly Limit"
```

### After Fix

**Scenario 1: Instance-Specific Cooldown (30 min)**
```
Instance #9: "Please come back at your next voting time of 30 minutes"
    ↓
Script: Detects INSTANCE_COOLDOWN_PATTERNS
    ↓
Result: ONLY Instance #9 waits ✅
    ↓
Status:
  - Instance #9: "⏳ Cooldown (31 min)"
  - Instance #10: Continues voting ✅
  - Instance #11: Continues voting ✅
```

**Scenario 2: Global Hourly Limit**
```
Instance #5: "Hourly limit reached"
    ↓
Script: Detects GLOBAL_HOURLY_LIMIT_PATTERNS
    ↓
Result: ALL instances paused ✅
    ↓
Status: All show "⏸️ Paused - Hourly Limit"
    ↓
Resume: At next full hour (e.g., 4:00 PM)
```

---

## Pattern Classification

### Global Patterns (Pause ALL)

| Pattern | Meaning | Action |
|---------|---------|--------|
| "hourly limit" | URL hit hourly voting limit | Pause ALL until next hour |
| "someone has already voted out of this ip" | IP-based global limit | Pause ALL until next hour |

### Instance Patterns (Individual Wait)

| Pattern | Meaning | Action |
|---------|---------|--------|
| "please come back at your next voting time" | 30-minute instance cooldown | Only this instance waits 31 min |
| "already voted" | Instance already voted | Only this instance waits 31 min |
| "wait before voting again" | Instance-specific wait | Only this instance waits 31 min |

---

## Logging

### Instance-Specific Cooldown
```
[INSTANCE_COOLDOWN] Instance #9 in instance-specific cooldown (30 min) - only this instance affected
[CLEANUP] Closing browser after cooldown detection
[INSTANCE_COOLDOWN] Instance #9 will wait individually, other instances continue
```

### Global Hourly Limit
```
[GLOBAL_LIMIT] Instance #5 detected GLOBAL hourly limit - will pause ALL instances
[CLEANUP] Closing browser after cooldown detection
[GLOBAL_LIMIT] Triggering global hourly limit handler
[HOURLY_LIMIT] 🚫 HOURLY LIMIT DETECTED - Pausing ALL instances
[HOURLY_LIMIT] Will resume at 04:00 PM
[HOURLY_LIMIT] Paused 10 instances
```

---

## Status Display

### Instance-Specific Cooldown
```
Instance #9        ⏳ Cooldown (31 min)
IP: 119.13.227.89
Votes: 0
⏱️ 31:00
❌ Last Failure: You have voted already! Please come back at your next voting time of 30 minutes.

Instance #10       ✅ Vote Successful  ← Still voting!
IP: 77.83.68.24
Votes: 5
⏱️ 28:30
```

### Global Hourly Limit
```
Instance #5        ⏸️ Paused - Hourly Limit
Instance #6        ⏸️ Paused - Hourly Limit
Instance #7        ⏸️ Paused - Hourly Limit
...
All instances paused until 4:00 PM
```

---

## Benefits

### 1. **Correct Behavior**
- Instance-specific cooldowns don't affect other instances
- Only true global limits pause all instances
- Better resource utilization

### 2. **More Voting Attempts**
- Other instances continue voting while one is in cooldown
- Don't waste time pausing all instances unnecessarily
- Maximize voting throughput

### 3. **Clear Logging**
- Distinguish between global and instance-specific in logs
- Easy to understand what's happening
- Better troubleshooting

### 4. **Accurate Status**
- Instance in cooldown shows "⏳ Cooldown (31 min)"
- Global limit shows "⏸️ Paused - Hourly Limit"
- Clear visual distinction

---

## Testing

### Test Case 1: Instance-Specific Cooldown
1. **Trigger:** Vote within 30 minutes on one instance
2. **Expected:**
   - That instance: "⏳ Cooldown (31 min)"
   - Other instances: Continue voting
   - Log: "[INSTANCE_COOLDOWN] only this instance affected"
3. **Verify:** Other instances NOT paused

### Test Case 2: Global Hourly Limit
1. **Trigger:** Hit true hourly limit
2. **Expected:**
   - ALL instances: "⏸️ Paused - Hourly Limit"
   - Log: "[GLOBAL_LIMIT] will pause ALL instances"
   - Resume: At next full hour
3. **Verify:** All instances paused

### Test Case 3: Mixed Scenario
1. **Instance #5:** Global limit → ALL pause
2. **Wait:** Until next hour
3. **Resume:** All instances
4. **Instance #9:** 30-min cooldown → Only #9 waits
5. **Verify:** Others continue voting

---

## Configuration

### Adding New Patterns

**For Global Hourly Limit:**
```python
GLOBAL_HOURLY_LIMIT_PATTERNS = [
    "hourly limit",
    "someone has already voted out of this ip",
    "your new global pattern"  # Add here
]
```

**For Instance-Specific Cooldown:**
```python
INSTANCE_COOLDOWN_PATTERNS = [
    "please come back at your next voting time",
    "already voted",
    "wait before voting again",
    "your new instance pattern"  # Add here
]
```

---

## Files Modified

1. **backend/config.py**
   - Added `GLOBAL_HOURLY_LIMIT_PATTERNS`
   - Added `INSTANCE_COOLDOWN_PATTERNS`

2. **backend/voter_engine.py**
   - Imported new pattern lists
   - Added detection logic (lines 808-809, 953-954)
   - Conditional global limit trigger (lines 840-844, 985-989)
   - Updated logging messages

---

## Summary

**Fixed:**
✅ Instance-specific cooldowns no longer pause all instances  
✅ Only true global hourly limits trigger global pause  
✅ Clear distinction in logs and status  
✅ Better resource utilization  
✅ More voting attempts per hour  

**Result:**
- "Please come back at your next voting time" → Only that instance waits
- "Hourly limit" → All instances pause
- Other instances continue voting during individual cooldowns

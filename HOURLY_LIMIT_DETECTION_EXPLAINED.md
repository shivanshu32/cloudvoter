# How Global Hourly Limit Detection Works

## Overview
The script detects global hourly limits through **THREE different methods** at different stages of the voting process.

---

## Detection Methods

### Method 1: Pre-Vote Check (Before Attempting Vote)
**Location:** `run_voting_cycle()` - Line 1103  
**When:** After navigating to voting page, BEFORE attempting vote  
**Function:** `check_hourly_voting_limit()`

#### How It Works:

**Step 1: Navigate to voting page**
```python
await self.navigate_to_voting_page()
```

**Step 2: Check for hourly limit message on page**
```python
if await self.check_hourly_voting_limit():
    # Hourly limit detected!
    await self.close_browser()
    asyncio.create_task(self.voter_manager.handle_hourly_limit())
```

#### Detection Patterns:

**1. Element Selectors (Visual elements):**
```python
limit_selectors = [
    'div.pc-hiddenbutton',                              # Hidden button div
    'div.redb.pc-hiddenbutton',                         # Red hidden button
    'div:has-text("hourly voting limit")',              # Div with text
    'div:has-text("voting button is temporarily disabled")',
    'div:has-text("will be reactivated at")'
]
```

**2. Page Content Patterns (Text search):**
```python
hourly_limit_patterns = [
    'hourly voting limit',
    'voting button is temporarily disabled',
    'will be reactivated at',
    'reached your hourly limit'
]
```

**Result:** If detected → Close browser → Trigger `handle_hourly_limit()` → Pause ALL instances

---

### Method 2: Post-Vote Check (After Vote Attempt)
**Location:** `attempt_vote()` - Line 808  
**When:** After clicking vote button, when vote count doesn't increase  
**Trigger:** Vote count unchanged + failure patterns detected

#### How It Works:

**Step 1: Vote count doesn't increase**
```python
if initial_count == final_count:
    # Vote didn't work, check why
```

**Step 2: Check page content for patterns**
```python
page_content = await self.page.content()

# Check if this is a GLOBAL hourly limit or INSTANCE-SPECIFIC cooldown
is_global_limit = any(pattern in page_content.lower() for pattern in GLOBAL_HOURLY_LIMIT_PATTERNS)
```

**Step 3: Trigger global pause if global pattern found**
```python
if is_global_limit and self.voter_manager:
    logger.warning(f"[GLOBAL_LIMIT] Triggering global hourly limit handler")
    asyncio.create_task(self.voter_manager.handle_hourly_limit())
```

#### Global Patterns (from config.py):
```python
GLOBAL_HOURLY_LIMIT_PATTERNS = [
    "hourly limit",
    "someone has already voted out of this ip"
]
```

**Result:** If global pattern detected → Close browser → Trigger `handle_hourly_limit()` → Pause ALL instances

---

### Method 3: Fallback Detection (When Vote Count Unavailable)
**Location:** `attempt_vote()` - Line 953  
**When:** Vote count cannot be retrieved, but failure patterns detected  
**Trigger:** Vote count is None + failure patterns in page

#### How It Works:

**Step 1: Vote count unavailable**
```python
if initial_count is None or final_count is None:
    # Can't verify by count, check page content
```

**Step 2: Check for failure patterns**
```python
if any(pattern in page_content.lower() for pattern in FAILURE_PATTERNS):
    # Some failure detected
```

**Step 3: Determine if global or instance-specific**
```python
is_global_limit = any(pattern in page_content.lower() for pattern in GLOBAL_HOURLY_LIMIT_PATTERNS)

if is_global_limit and self.voter_manager:
    asyncio.create_task(self.voter_manager.handle_hourly_limit())
```

**Result:** If global pattern detected → Close browser → Trigger `handle_hourly_limit()` → Pause ALL instances

---

## Detection Flow Chart

```
┌─────────────────────────────────────────┐
│  Instance starts voting cycle           │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  Navigate to voting page                │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  METHOD 1: check_hourly_voting_limit()  │
│  - Check for visible limit messages     │
│  - Check page content for patterns      │
└─────────────────────────────────────────┘
                  ↓
         Limit detected?
         ├─ Yes → Pause ALL instances
         └─ No → Continue
                  ↓
┌─────────────────────────────────────────┐
│  Attempt vote (click button)            │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  Get vote count (before & after)        │
└─────────────────────────────────────────┘
                  ↓
         Count increased?
         ├─ Yes → SUCCESS ✅
         └─ No → Check failure reason
                  ↓
┌─────────────────────────────────────────┐
│  METHOD 2: Check page content           │
│  - Is it GLOBAL_HOURLY_LIMIT_PATTERNS?  │
│  - Or INSTANCE_COOLDOWN_PATTERNS?       │
└─────────────────────────────────────────┘
                  ↓
         Global limit?
         ├─ Yes → Pause ALL instances
         └─ No → Only this instance waits
                  ↓
┌─────────────────────────────────────────┐
│  METHOD 3: Fallback (if count N/A)      │
│  - Check GLOBAL vs INSTANCE patterns    │
└─────────────────────────────────────────┘
                  ↓
         Global limit?
         ├─ Yes → Pause ALL instances
         └─ No → Only this instance waits
```

---

## Pattern Comparison

### Pre-Vote Detection Patterns (Method 1)
**Used in:** `check_hourly_voting_limit()`

```python
# These are MORE SPECIFIC to the voting page UI
hourly_limit_patterns = [
    'hourly voting limit',
    'voting button is temporarily disabled',
    'will be reactivated at',
    'reached your hourly limit'
]
```

**Purpose:** Detect hourly limit BEFORE attempting vote (saves time)

---

### Post-Vote Global Patterns (Methods 2 & 3)
**Used in:** `attempt_vote()` after vote fails

```python
# These distinguish GLOBAL from INSTANCE-SPECIFIC
GLOBAL_HOURLY_LIMIT_PATTERNS = [
    "hourly limit",
    "someone has already voted out of this ip"
]
```

**Purpose:** Determine if ALL instances should pause or just one

---

### Instance-Specific Patterns (Methods 2 & 3)
**Used in:** `attempt_vote()` after vote fails

```python
# These indicate ONLY this instance should wait
INSTANCE_COOLDOWN_PATTERNS = [
    "please come back at your next voting time",  # 30-minute cooldown
    "already voted",
    "wait before voting again"
]
```

**Purpose:** Prevent pausing all instances for individual cooldowns

---

## Example Scenarios

### Scenario 1: Pre-Vote Detection (Method 1)

**Timeline:**
```
1. Instance #5 navigates to voting page
2. Page loads with message: "Hourly voting limit reached"
3. check_hourly_voting_limit() detects visible message
4. Instance #5 closes browser
5. Triggers handle_hourly_limit()
6. ALL instances paused
7. Resume at next full hour
```

**Log Output:**
```
[CYCLE] Instance #5 starting voting cycle
[HOURLY_LIMIT] Instance #5 detected: Hourly voting limit reached...
[LIMIT] Instance #5 hourly voting limit detected - closing browser
[HOURLY_LIMIT] 🚫 HOURLY LIMIT DETECTED - Pausing ALL instances
[HOURLY_LIMIT] Will resume at 04:00 PM
[HOURLY_LIMIT] Paused 10 instances
```

---

### Scenario 2: Post-Vote Detection - Global (Method 2)

**Timeline:**
```
1. Instance #7 attempts vote
2. Clicks vote button
3. Vote count doesn't increase
4. Checks page content
5. Finds "hourly limit" pattern
6. Detects as GLOBAL_HOURLY_LIMIT_PATTERNS
7. Triggers handle_hourly_limit()
8. ALL instances paused
```

**Log Output:**
```
[VOTE] Instance #7 attempting vote...
[FAILED] Vote count did not increase: 1234 -> 1234
[GLOBAL_LIMIT] Instance #7 detected GLOBAL hourly limit - will pause ALL instances
[CLEANUP] Closing browser after cooldown detection
[GLOBAL_LIMIT] Triggering global hourly limit handler
[HOURLY_LIMIT] 🚫 HOURLY LIMIT DETECTED - Pausing ALL instances
```

---

### Scenario 3: Post-Vote Detection - Instance-Specific (Method 2)

**Timeline:**
```
1. Instance #9 attempts vote
2. Clicks vote button
3. Vote count doesn't increase
4. Checks page content
5. Finds "please come back at your next voting time" pattern
6. Detects as INSTANCE_COOLDOWN_PATTERNS
7. Does NOT trigger handle_hourly_limit()
8. Only Instance #9 waits
9. Other instances continue
```

**Log Output:**
```
[VOTE] Instance #9 attempting vote...
[FAILED] Vote count did not increase: 567 -> 567
[INSTANCE_COOLDOWN] Instance #9 in instance-specific cooldown (30 min) - only this instance affected
[CLEANUP] Closing browser after cooldown detection
[INSTANCE_COOLDOWN] Instance #9 will wait individually, other instances continue
```

---

### Scenario 4: Fallback Detection (Method 3)

**Timeline:**
```
1. Instance #3 attempts vote
2. Vote count element not found (returns None)
3. Can't verify by count
4. Checks page content for patterns
5. Finds "someone has already voted out of this ip"
6. Detects as GLOBAL_HOURLY_LIMIT_PATTERNS
7. Triggers handle_hourly_limit()
8. ALL instances paused
```

**Log Output:**
```
[VOTE] Instance #3 attempting vote...
[VOTE] Could not get vote count
[GLOBAL_LIMIT] Instance #3 detected GLOBAL hourly limit (fallback) - will pause ALL instances
[CLEANUP] Closing browser after cooldown detection (fallback)
[GLOBAL_LIMIT] Triggering global hourly limit handler (fallback)
[HOURLY_LIMIT] 🚫 HOURLY LIMIT DETECTED - Pausing ALL instances
```

---

## Why Three Methods?

### Method 1: Pre-Vote Check
**Advantage:** Detects limit BEFORE attempting vote  
**Saves:** Time and resources  
**Use Case:** When voting page clearly shows hourly limit message

### Method 2: Post-Vote Check
**Advantage:** Catches limits that appear AFTER clicking  
**Distinguishes:** Global vs instance-specific  
**Use Case:** When limit only appears after vote attempt

### Method 3: Fallback
**Advantage:** Works even if vote count unavailable  
**Backup:** When count element not found  
**Use Case:** Page structure changes or count element missing

---

## What Happens After Detection?

### Step 1: Close Browser
```python
await self.close_browser()
```
- Closes page and browser context
- Frees up memory
- Prevents hanging processes

### Step 2: Trigger Global Handler
```python
asyncio.create_task(self.voter_manager.handle_hourly_limit())
```

### Step 3: Global Handler Actions
```python
async def handle_hourly_limit(self):
    # 1. Set global flag
    self.global_hourly_limit = True
    
    # 2. Calculate next hour
    next_hour = (datetime.now() + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    
    # 3. Pause ALL instances
    for ip, instance in self.active_instances.items():
        instance.is_paused = True
        instance.pause_event.clear()
        instance.status = "⏸️ Paused - Hourly Limit"
    
    # 4. Start monitoring task
    asyncio.create_task(self._check_hourly_limit_expiry())
```

### Step 4: Monitor and Resume
```python
async def _check_hourly_limit_expiry(self):
    while self.global_hourly_limit:
        if current_time >= reactivation_time:
            # Resume all instances SEQUENTIALLY
            self.global_hourly_limit = False
            # Resume instances one by one with delays
```

---

## Configuration

### To Add New Global Patterns:

**Edit `config.py`:**
```python
GLOBAL_HOURLY_LIMIT_PATTERNS = [
    "hourly limit",
    "someone has already voted out of this ip",
    "your new global pattern here"  # Add here
]
```

### To Add New Pre-Vote Patterns:

**Edit `voter_engine.py` (line 1182):**
```python
hourly_limit_patterns = [
    'hourly voting limit',
    'voting button is temporarily disabled',
    'will be reactivated at',
    'reached your hourly limit',
    'your new pattern here'  # Add here
]
```

---

## Summary

**Three Detection Methods:**
1. ✅ **Pre-Vote:** Check page before attempting vote
2. ✅ **Post-Vote:** Check after vote fails (distinguishes global vs instance)
3. ✅ **Fallback:** Check when vote count unavailable

**Global Patterns Trigger:**
- "hourly limit"
- "someone has already voted out of this ip"

**Result:**
- Close browser
- Pause ALL instances
- Resume at next full hour
- Sequential resume to prevent memory overload

**Instance-Specific Patterns:**
- "please come back at your next voting time"
- "already voted"
- "wait before voting again"

**Result:**
- Close browser
- Only that instance waits
- Other instances continue voting

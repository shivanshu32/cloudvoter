# All Vote Failure Scenarios Detected

## Overview
Complete list of all vote failure scenarios detected by the CloudVoter script, including failure types, reasons, detection methods, and what gets displayed to the user.

---

## Failure Categories

### 1. **IP Cooldown / Hourly Limit Failures**
**Failure Type:** `ip_cooldown`

#### Scenario 1A: Hourly Limit (Primary Detection)
**Detection Method:** Vote count doesn't increase + page contains failure patterns

**Detected Patterns (from config.py):**
- "hourly limit"
- "already voted"
- "cooldown"
- "try again later"
- "someone has already voted out of this ip"
- "please come back at your next voting time"
- "wait before voting again"

**Extracted Messages (examples):**
- "Hourly voting limit reached"
- "Already voted! Please come back at your next voting time of 30 minutes."
- "You have voted already! Please come back at your next voting time."
- "Someone has already voted out of this IP"
- "In cooldown period"

**Fallback Messages (if extraction fails):**
- "Already voted - Please come back at next voting time"
- "Hourly voting limit reached"
- "Already voted"
- "In cooldown period"
- "Cooldown/limit detected"

**Code Location:** Lines 734-824 in `voter_engine.py`

**What User Sees:**
```
❌ Last Failure: Already voted! Please come back at your next voting time of 30 minutes.
```

---

#### Scenario 1B: Hourly Limit (Fallback Detection)
**Detection Method:** Vote count unavailable + page contains failure patterns

**Same patterns as above**

**Code Location:** Lines 884-950 in `voter_engine.py`

**What User Sees:**
```
❌ Last Failure: Cooldown/limit detected (fallback)
```

---

### 2. **Technical Failures**
**Failure Type:** `technical`

#### Scenario 2A: Vote Button Not Found
**Detection Method:** Cannot find vote button after trying all selectors

**Failure Reason:** "Could not find vote button"

**Causes:**
- Page structure changed
- Vote button selector outdated
- Page not fully loaded
- JavaScript not executed
- Button hidden or removed

**Code Location:** Lines 656-677 in `voter_engine.py`

**What User Sees:**
```
❌ Last Failure: Could not find vote button
```

---

#### Scenario 2B: Vote Count Did Not Increase
**Detection Method:** Vote count before = vote count after (and no cooldown message)

**Failure Reason:** "Vote count did not increase"

**Causes:**
- Vote didn't register on server
- Vote count element not updating
- Technical issue with voting system
- Network problem
- Server-side error

**Code Location:** Lines 826-857 in `voter_engine.py`

**What User Sees:**
```
❌ Last Failure: Vote count did not increase
```

---

#### Scenario 2C: Exception During Vote Attempt
**Detection Method:** Any exception thrown during vote process

**Failure Reason:** "Exception: [error details]"

**Examples:**
- "Exception: TimeoutError: Waiting for selector timed out"
- "Exception: NetworkError: Connection failed"
- "Exception: Page closed"
- "Exception: Navigation timeout"

**Causes:**
- Network errors
- Timeout errors
- Page crashes
- Browser errors
- Playwright errors

**Code Location:** Lines 975-1005 in `voter_engine.py`

**What User Sees:**
```
❌ Last Failure: Exception: TimeoutError: Waiting for selector timed out
```

---

## Detection Flow Chart

```
Vote Attempt Started
    ↓
Can find vote button?
    ├─ No → FAILURE: "Could not find vote button" (Technical)
    └─ Yes → Click button
        ↓
    Wait 3 seconds
        ↓
    Get vote counts (initial & final)
        ↓
    Vote count available?
        ├─ Yes → Compare counts
        │    ↓
        │   Count increased by 1?
        │    ├─ Yes → SUCCESS ✅
        │    ├─ No → Check page content
        │    │    ↓
        │    │   Contains failure patterns?
        │    │    ├─ Yes → FAILURE: "Hourly limit/cooldown" (IP Cooldown)
        │    │    └─ No → FAILURE: "Vote count did not increase" (Technical)
        │    └─ Increased by >1 → SUSPICIOUS (Parallel voting)
        │
        └─ No → Fallback: Check page content
             ↓
            Contains success patterns?
             ├─ Yes → SUCCESS (Unverified) ⚠️
             └─ No → Contains failure patterns?
                  ├─ Yes → FAILURE: "Cooldown/limit" (IP Cooldown)
                  └─ No → FAILURE: Unknown

Exception at any point?
    └─ FAILURE: "Exception: [error]" (Technical)
```

---

## Failure Summary Table

| # | Failure Scenario | Type | Reason Displayed | Detection Method |
|---|-----------------|------|------------------|------------------|
| 1 | Hourly limit reached | `ip_cooldown` | Extracted from page or "Hourly voting limit reached" | Page content matches patterns |
| 2 | Already voted (30 min) | `ip_cooldown` | "Already voted! Please come back at next voting time" | Page content matches patterns |
| 3 | IP in cooldown | `ip_cooldown` | "In cooldown period" | Page content matches patterns |
| 4 | Vote button not found | `technical` | "Could not find vote button" | All selectors fail |
| 5 | Vote count unchanged | `technical` | "Vote count did not increase" | Count before = count after |
| 6 | Exception/Error | `technical` | "Exception: [details]" | Try-catch exception |
| 7 | Fallback cooldown | `ip_cooldown` | "Cooldown/limit detected (fallback)" | Fallback detection |

---

## Config Patterns (FAILURE_PATTERNS)

All patterns checked (case-insensitive):

```python
FAILURE_PATTERNS = [
    "hourly limit",                              # ← Hourly voting limit
    "already voted",                             # ← Already voted message
    "cooldown",                                  # ← Cooldown period
    "try again later",                           # ← Generic retry message
    "someone has already voted out of this ip",  # ← IP-based limit
    "please come back at your next voting time", # ← 30-minute limit
    "wait before voting again"                   # ← Wait message
]
```

**How to add new patterns:**
1. Edit `config.py`
2. Add new pattern to `FAILURE_PATTERNS` list
3. No code changes needed - automatically detected

---

## Message Extraction Selectors

The script tries to extract actual error messages from these elements:

```python
message_selectors = [
    '.pc-image-info-box-button-btn-text',        # ← Primary button text
    '.pc-hiddenbutton .pc-image-info-box-button-btn-text',  # ← Hidden button
    '.alert',                                     # ← Alert messages
    '.message',                                   # ← Message divs
    '.notification',                              # ← Notifications
    '[class*="message"]',                         # ← Any class with "message"
    '[class*="error"]'                            # ← Any class with "error"
]
```

**Priority:**
1. Extract actual message from page elements (best)
2. Use specific fallback based on pattern (good)
3. Use generic fallback (last resort)

---

## Message Cleanup

All extracted messages are automatically cleaned:

### 1. Remove Personalized Names
```
"You have voted already shivanshu pathak! Please come back..."
→ "You have voted already! Please come back..."
```

### 2. Normalize Whitespace
```
"Already    voted   !  Please..."
→ "Already voted! Please..."
```

### 3. Limit Length
```
"Very long message that exceeds 150 characters..."
→ "Very long message that exceeds 150 char..." (truncated)
```

---

## Vote Button Selectors

The script tries these selectors to find the vote button:

```python
VOTE_BUTTON_SELECTORS = [
    ".photo_vote",
    "[data-item]",
    ".vote-button",
    "button[class*='vote']",
    "input[type='button'][value*='VOTE']",
    ".pc-image-info-box-button-btn",
    "#vote-btn",
    "[onclick*='vote']"
]
```

If **none** of these work → **Failure: "Could not find vote button"**

---

## Success Patterns (For Reference)

These patterns indicate successful votes (not failures):

```python
SUCCESS_PATTERNS = [
    "thank you for vote",
    "vote successful",
    "your vote has been recorded",
    "vote counted",
    "thanks for voting"
]
```

---

## Logging Details

Each failure is logged to CSV with:

| Field | Description |
|-------|-------------|
| `timestamp` | When the failure occurred |
| `instance_id` | Which instance failed |
| `status` | "failed" |
| `failure_type` | "ip_cooldown" or "technical" |
| `failure_reason` | Specific reason (displayed to user) |
| `cooldown_message` | Extracted cooldown message |
| `initial_vote_count` | Vote count before attempt |
| `final_vote_count` | Vote count after attempt |
| `proxy_ip` | IP address used |
| `click_attempts` | How many times tried to click |
| `error_message` | Exception details (if any) |

---

## UI Display

All failures are displayed in the Active Instances section:

### Format:
```
┌─────────────────────────────────────────────┐
│ Instance #1        [Status Badge]           │
│ IP: 1.2.3.4                                 │
│ Votes: 5                                    │
│ ⏱️ 28:30                                    │
│ ─────────────────────────────────────────── │
│ ✅ Last Success: 35 min ago                 │
│ 🎯 Last Attempt: 2 min ago                  │
│ ═════════════════════════════════════════   │ ← Red border
│ ❌ Last Failure: [Failure Reason]           │ ← Red text
└─────────────────────────────────────────────┘
```

### Color Coding:
- **Red border** - Indicates failure section
- **Red text** - Failure reason
- **Automatically cleared** - After next successful vote

---

## Troubleshooting Guide

### If you see: "Could not find vote button"
**Possible causes:**
- Page structure changed
- Vote button selector needs update
- Page not fully loaded

**Action:**
- Inspect page HTML
- Update `VOTE_BUTTON_SELECTORS` in `config.py`

---

### If you see: "Vote count did not increase"
**Possible causes:**
- Vote didn't register on server
- Technical issue with voting system
- Network problem

**Action:**
- Check if vote actually counted on website
- Verify vote count element selector
- Check network connectivity

---

### If you see: "Hourly voting limit reached"
**Possible causes:**
- IP hit hourly limit (expected behavior)
- Voted too soon after previous vote

**Action:**
- Wait for cooldown period (usually 31 minutes)
- This is normal behavior

---

### If you see: "Exception: [error]"
**Possible causes:**
- Network timeout
- Browser crash
- Page navigation error

**Action:**
- Check error details
- Verify network stability
- Check browser logs

---

## Statistics

Based on the code, the script tracks:

| Metric | Description |
|--------|-------------|
| Total Attempts | All vote attempts (success + failure) |
| Successful Votes | Votes verified by count increase |
| Failed Votes | All failures (technical + cooldown) |
| Hourly Limits | Specifically cooldown/limit failures |
| Success Rate | (Successful / Total) × 100% |

---

## Adding New Failure Detection

### To add a new failure pattern:

1. **Add pattern to config.py:**
```python
FAILURE_PATTERNS = [
    # ... existing patterns ...
    "your new pattern here"
]
```

2. **Add specific fallback message (optional):**
```python
# In voter_engine.py, around line 786
if 'your new pattern' in page_content.lower():
    cooldown_message = "Your specific message"
```

3. **No other code changes needed!**

---

## Summary

**Total Failure Scenarios Detected: 7**

**Failure Types:**
- **IP Cooldown:** 3 scenarios (hourly limit, already voted, cooldown)
- **Technical:** 4 scenarios (button not found, count unchanged, exception, fallback)

**Detection Methods:**
- Page content pattern matching
- Vote count comparison
- Exception handling
- Element selector matching

**All failures are:**
- ✅ Logged to CSV
- ✅ Displayed in UI with red text
- ✅ Tracked with timestamps
- ✅ Automatically cleared on success
- ✅ Configurable via config.py

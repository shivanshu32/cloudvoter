# Improved Failure Detection

## Overview
Enhanced the failure detection system to properly handle all cooldown/limit messages, including the specific "Please come back at your next voting time" message that was previously not being detected.

## Problem Identified

**User reported message not being detected:**
```html
<div class="pc-image-info-box-button-btn-text">
    <i class="fa fa-exclamation-circle"></i> 
    You have voted already shivanshu pathak! 
    Please come back at your next voting time of 30 minutes.
</div>
```

**Issues:**
1. Code was hardcoded to check only 3 patterns: `'hourly limit', 'already voted', 'cooldown'`
2. Config file had more patterns including "please come back at your next voting time" but they weren't being used
3. Generic failure messages were shown instead of the actual page message
4. No extraction of the actual error text from the page

## Solution Implemented

### 1. Use Config Patterns
Changed from hardcoded patterns to using `FAILURE_PATTERNS` from config:

**Before:**
```python
if any(pattern in page_content.lower() for pattern in ['hourly limit', 'already voted', 'cooldown']):
```

**After:**
```python
if any(pattern in page_content.lower() for pattern in FAILURE_PATTERNS):
```

### 2. Extract Actual Message from Page
Added logic to extract the actual error message displayed on the page:

```python
# Try to find message in common elements
message_selectors = [
    '.pc-image-info-box-button-btn-text',
    '.pc-hiddenbutton .pc-image-info-box-button-btn-text',
    '.alert', '.message', '.notification',
    '[class*="message"]', '[class*="error"]'
]

for selector in message_selectors:
    element = await self.page.query_selector(selector)
    if element:
        text = await element.inner_text()
        if text and any(pattern in text.lower() for pattern in FAILURE_PATTERNS):
            cooldown_message = text.strip()
            # Limit length
            if len(cooldown_message) > 150:
                cooldown_message = cooldown_message[:150] + "..."
            break
```

### 3. Improved Fallback Messages
Added specific fallback for "please come back at your next voting time":

```python
if not cooldown_message:
    if 'please come back at your next voting time' in page_content.lower():
        cooldown_message = "Already voted - Please come back at next voting time"
    elif 'hourly limit' in page_content.lower():
        cooldown_message = "Hourly voting limit reached"
    elif 'already voted' in page_content.lower():
        cooldown_message = "Already voted"
    elif 'cooldown' in page_content.lower():
        cooldown_message = "In cooldown period"
    else:
        cooldown_message = "Cooldown/limit detected"
```

## Config Patterns Used

From `config.py`:
```python
FAILURE_PATTERNS = [
    "hourly limit",
    "already voted",
    "cooldown",
    "try again later",
    "someone has already voted out of this ip",
    "please come back at your next voting time",  # ← Now properly detected!
    "wait before voting again"
]
```

## Changes Made

### 1. Import Config Patterns (`voter_engine.py`)
```python
from config import (
    ENABLE_RESOURCE_BLOCKING, BLOCK_IMAGES, BLOCK_STYLESHEETS, 
    BLOCK_FONTS, BLOCK_TRACKING, BROWSER_LAUNCH_DELAY, MAX_CONCURRENT_BROWSER_LAUNCHES,
    FAILURE_PATTERNS  # ← Added
)
```

### 2. Updated Primary Failure Detection (Lines 734-791)
- Use `FAILURE_PATTERNS` from config
- Extract actual message from page elements
- Fallback to specific messages based on content
- Store extracted message in `last_failure_reason`

### 3. Updated Fallback Detection (Lines 884-915)
- Use `FAILURE_PATTERNS` from config
- Extract actual message from page elements
- Store extracted message in `last_failure_reason`

## Message Extraction

### Priority Order
1. **Extract from page elements** (best - shows actual message)
   - `.pc-image-info-box-button-btn-text`
   - `.pc-hiddenbutton .pc-image-info-box-button-btn-text`
   - `.alert`, `.message`, `.notification`
   - `[class*="message"]`, `[class*="error"]`

2. **Fallback to specific patterns** (good - shows relevant message)
   - "please come back at your next voting time" → "Already voted - Please come back at next voting time"
   - "hourly limit" → "Hourly voting limit reached"
   - "already voted" → "Already voted"
   - "cooldown" → "In cooldown period"

3. **Generic fallback** (last resort)
   - "Cooldown/limit detected"

## Examples

### Example 1: Extracted Message (Best Case)
**Page HTML:**
```html
<div class="pc-image-info-box-button-btn-text">
    You have voted already shivanshu pathak! 
    Please come back at your next voting time of 30 minutes.
</div>
```

**Displayed in UI:**
```
❌ Last Failure: You have voted already shivanshu pathak! Please come back at your next voting time of 30 minutes.
```

### Example 2: Specific Fallback
**Page content contains:** "please come back at your next voting time"

**Displayed in UI:**
```
❌ Last Failure: Already voted - Please come back at next voting time
```

### Example 3: Generic Fallback
**Page content contains:** "hourly limit"

**Displayed in UI:**
```
❌ Last Failure: Hourly voting limit reached
```

## Benefits

### 1. **Comprehensive Detection**
- All patterns from config are now checked
- No more missed failure messages
- Covers all known cooldown/limit scenarios

### 2. **Actual Message Display**
- Shows the exact message from the voting site
- More informative than generic messages
- Helps understand specific requirements (e.g., "30 minutes")

### 3. **Easy Configuration**
- Add new patterns to `config.py` without code changes
- Centralized pattern management
- Easy to update for different voting sites

### 4. **Better User Experience**
- Clear, specific error messages
- Understand exactly what the site is saying
- Know when to try again

## Testing

### Test Case 1: "Please come back" Message
1. **Vote within 30 minutes** of previous vote
2. **Check instance card** - should show:
   ```
   ❌ Last Failure: You have voted already shivanshu pathak! Please come back at your next voting time of 30 minutes.
   ```
3. **Verify pattern detected** in logs

### Test Case 2: Other Patterns
1. **Trigger different failure types**:
   - Hourly limit
   - Already voted
   - IP cooldown
2. **Verify each shows appropriate message**

### Test Case 3: Message Extraction
1. **Check if actual page message is extracted**
2. **Compare with generic fallback**
3. **Verify message is readable and helpful**

## Configuration

### Adding New Patterns

To add new failure patterns, edit `config.py`:

```python
FAILURE_PATTERNS = [
    "hourly limit",
    "already voted",
    "cooldown",
    "try again later",
    "someone has already voted out of this ip",
    "please come back at your next voting time",
    "wait before voting again",
    "your new pattern here"  # ← Add new patterns
]
```

**No code changes needed!** The script will automatically detect the new patterns.

### Message Selectors

If the voting site uses different CSS classes, add them to the selectors list in `voter_engine.py`:

```python
message_selectors = [
    '.pc-image-info-box-button-btn-text',
    '.pc-hiddenbutton .pc-image-info-box-button-btn-text',
    '.alert', '.message', '.notification',
    '[class*="message"]', '[class*="error"]',
    '.your-custom-selector'  # ← Add custom selectors
]
```

## Troubleshooting

### Message not being detected

**Check:**
1. Pattern exists in `config.py` FAILURE_PATTERNS
2. Pattern is lowercase (detection is case-insensitive)
3. Pattern appears in page content

**Debug:**
```python
# Add logging to see page content
logger.info(f"Page content: {page_content[:500]}")
```

### Generic message shown instead of actual

**Possible causes:**
1. Message element selector doesn't match
2. Message element is hidden or not loaded
3. Message text doesn't contain failure pattern

**Fix:**
- Inspect page HTML to find correct selector
- Add selector to `message_selectors` list
- Verify message text contains pattern from config

### Message too long

**Automatic handling:**
- Messages longer than 150 characters are truncated
- "..." added to indicate truncation

**Adjust if needed:**
```python
if len(cooldown_message) > 150:  # Change 150 to your preferred length
    cooldown_message = cooldown_message[:150] + "..."
```

## Files Modified

1. **backend/voter_engine.py**
   - Imported `FAILURE_PATTERNS` from config
   - Updated primary failure detection (lines 734-791)
   - Updated fallback detection (lines 884-915)
   - Added message extraction logic

2. **backend/config.py**
   - Already had comprehensive patterns (no changes needed)

## Summary

The improved failure detection system now:
- ✅ Uses all patterns from config (including "please come back at your next voting time")
- ✅ Extracts actual error messages from the page
- ✅ Shows specific, helpful failure reasons
- ✅ Easy to configure with new patterns
- ✅ Better user experience with clear messages

**Result:** The specific message "You have voted already shivanshu pathak! Please come back at your next voting time of 30 minutes." will now be properly detected and displayed in the UI!

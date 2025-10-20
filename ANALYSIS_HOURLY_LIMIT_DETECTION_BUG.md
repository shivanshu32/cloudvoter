# Analysis: Hourly Limit Detection Failure

## 🔍 **Root Cause Analysis**

### **Your HTML (Hourly Limit Message):**
```html
<div class="pc-image-info-box-button">
    <div class="pc-image-info-box-button-btn redb pc-hiddenbutton">
        <div class="pc-image-info-box-button-btn-text" style="font-size:0.8rem !important;">
            <i class="fa fa-exclamation-circle"></i> 
            The voting button is temporarily disabled for this entry and will be reactivated at <b>4 AM</b> 
            because this entry has reached its <b>hourly voting limit</b>...
        </div>
    </div>
</div>
```

**Key Observation:** The button has class `pc-hiddenbutton` - it's HIDDEN!

---

## 🐛 **THE BUG - Execution Flow Analysis**

### **Step-by-Step Execution:**

#### **Step 1: Click Vote Button (Line 714-724)**
```python
vote_selectors = [
    'div.pc-image-info-box-button-btn-text.blink',  # Normal vote button
    '.pc-image-info-box-button-btn-text.blink',
    '.pc-image-info-box-button-btn-text',  # ⚠️ THIS MATCHES!
    # ...
]

for selector in vote_selectors:
    button = await self.page.query_selector(selector)
    if button and await button.is_visible():
        await button.click()
        button_clicked = True
        break
```

**Problem:** The selector `.pc-image-info-box-button-btn-text` matches BOTH:
1. ✅ Normal vote button (when active)
2. ❌ **Hourly limit message** (when limit reached)

**But wait!** The code checks `await button.is_visible()` - so if the hourly limit message is hidden (`pc-hiddenbutton`), it shouldn't be clicked... **OR SHOULD IT?**

#### **Step 2: Check Button Visibility (Line 809-820)**
```python
# CRITICAL: Check if vote button is still visible (indicates click failed)
button_still_visible = False
try:
    for selector in vote_selectors:
        button = await self.page.query_selector(selector)
        if button and await button.is_visible():
            button_still_visible = True
            logger.warning(f"[CLICK_FAILED] Vote button still visible after click - click was NOT successful!")
            break
except Exception as e:
    logger.debug(f"[CHECK] Error checking button visibility: {e}")
```

**Here's the issue:**
- Uses SAME `vote_selectors` list
- Checks `.pc-image-info-box-button-btn-text`
- **This selector matches the hourly limit message div!**
- If the hourly limit message is visible, `button_still_visible = True`

#### **Step 3: Retry Logic Triggered (Line 822)**
```python
# RETRY LOGIC: If button still visible, popup may have reappeared - try again
if button_still_visible and click_attempts < 3:
    logger.info(f"[RETRY] Button still visible - attempting to clear popup and click again (attempt {click_attempts + 1}/3)")
    # ... retry logic ...
```

**Result:** Script thinks popup reappeared, tries to retry!

#### **Step 4: Error Message Extraction (Line 1024-1048)**
```python
error_selectors = [
    '.pc-image-info-box-button-btn-text',  # ⚠️ THIS MATCHES HOURLY LIMIT MESSAGE!
    '.pc-hiddenbutton .pc-image-info-box-button-btn-text',  # ⚠️ THIS TOO!
    # ...
]

for selector in error_selectors:
    element = await self.page.query_selector(selector)
    if element:
        text = await element.inner_text()
        if text and text.strip() and text.strip().upper() != "CLICK TO VOTE":
            error_message_found = text.strip()[:200]
            logger.info(f"[ERROR_MSG] Found error message: {error_message_found}")
            break
```

**This SHOULD extract:** "The voting button is temporarily disabled... hourly voting limit..."

**But then what happens?**

#### **Step 5: The Critical Branch (Line 1091-1097)**
```python
# Determine specific failure reason
if button_still_visible:
    # Vote button still visible = click failed
    if error_message_found:
        failure_reason = f"Click failed - {error_message_found}"  # ⚠️ WRONG PATH!
    else:
        failure_reason = "Click failed - Button still visible (popup may have reappeared)"
    logger.error(f"[FAILURE] {failure_reason}")
```

**THE BUG:**
- `button_still_visible = True` (because `.pc-image-info-box-button-btn-text` matched hourly limit div)
- `error_message_found = "The voting button is temporarily disabled... hourly voting limit..."`
- **Takes the `if button_still_visible:` branch**
- Sets `failure_reason = "Click failed - The voting button is temporarily disabled..."`
- **NEVER reaches the hourly limit detection code at line 922!**

---

## 📊 **Proof: Why Hourly Limit Detection is Skipped**

### **Code Flow:**

```
Line 809: Check if button still visible
    ↓
Line 813: button = await self.page.query_selector('.pc-image-info-box-button-btn-text')
    ↓ 
    ✅ MATCHES hourly limit message div!
    ↓
Line 814: if button and await button.is_visible():
    ↓
    ✅ Hourly limit message IS visible (not hidden by CSS display:none)
    ↓
Line 815: button_still_visible = True
    ↓
Line 822: if button_still_visible and click_attempts < 3:
    ↓
    ✅ Enters retry logic (attempts 1, 2, 3)
    ↓
    All retries fail (same issue)
    ↓
Line 1091: if button_still_visible:
    ↓
    ✅ TRUE - takes this branch
    ↓
Line 1093-1094: failure_reason = f"Click failed - {error_message_found}"
    ↓
Line 1097: logger.error(f"[FAILURE] {failure_reason}")
    ↓
    ❌ SKIPS line 922 hourly limit detection!
    ↓
    ❌ SKIPS line 983 global/instance cooldown check!
    ↓
Line 1115: Log as technical failure
    ↓
    ❌ WRONG! Should be IP cooldown!
```

---

## 🎯 **The Root Cause**

### **Problem 1: Selector Ambiguity**

The selector `.pc-image-info-box-button-btn-text` matches:
1. **Normal vote button** (when voting is allowed)
2. **Hourly limit message** (when limit is reached)

Both use the same class name!

### **Problem 2: Logic Flow**

The code checks `button_still_visible` BEFORE checking for hourly limit patterns:

```python
# Line 809-820: Check button visibility
button_still_visible = ...

# Line 822-911: Retry logic (if button visible)

# Line 913-1019: Hourly limit detection ⚠️ ONLY if NOT button_still_visible!

# Line 1020-1140: Technical failure handling (if button visible)
```

---

## ✅ **PROOF: Code Structure Analysis**

### **The Actual Code Structure:**

```python
# Line 804: else: (count didn't increase)
    # Line 809-820: Check if button still visible
    button_still_visible = False
    for selector in vote_selectors:
        button = await self.page.query_selector(selector)
        if button and await button.is_visible():
            button_still_visible = True  # ⚠️ TRUE for hourly limit message!
            break
    
    # Line 822-911: Retry logic
    if button_still_visible and click_attempts < 3:
        # ... retry 3 times ...
        # After retries, button_still_visible is STILL TRUE
    
    # Line 913-915: Wait for error message
    await asyncio.sleep(5)
    page_content = await self.page.content()
    
    # Line 922-1019: HOURLY LIMIT DETECTION
    if any(pattern in page_content.lower() for pattern in FAILURE_PATTERNS):
        # ✅ This SHOULD execute for hourly limit
        # ✅ Pattern "hourly limit" IS in page_content
        # ❌ BUT this code is NEVER REACHED!
        logger.warning(f"[VOTE] Instance #{self.instance_id} hit cooldown/limit")
        # ... proper hourly limit handling ...
    
    # Line 1020: else: (NO cooldown pattern found)
    else:
        # ❌ THIS EXECUTES INSTEAD!
        logger.error(f"[FAILED] Vote failed - count unchanged and no known error pattern detected")
        
        # Line 1024-1048: Extract error message
        error_message_found = "The voting button is temporarily disabled... hourly voting limit..."
        
        # Line 1091-1097: WRONG PATH!
        if button_still_visible:  # ⚠️ TRUE!
            if error_message_found:
                failure_reason = f"Click failed - {error_message_found}"
                # ❌ WRONG! Should be "Hourly voting limit reached"
            logger.error(f"[FAILURE] {failure_reason}")
```

**WAIT! There's a contradiction here!**

Let me re-read the code more carefully...

### **Re-Analysis:**

Looking at lines 822-911 (retry logic) and 913-1019 (hourly limit detection):

```python
# Line 822: if button_still_visible and click_attempts < 3:
    # ... retry logic ...
    # Line 896-909: After retry fails
    else:
        logger.warning(f"[RETRY] Vote still failed after retry - count did not increase")
        final_count = retry_final_count
        # Re-check if button is still visible
        button_still_visible = False  # ⚠️ RESET!
        for selector in vote_selectors:
            button = await self.page.query_selector(selector)
            if button and await button.is_visible():
                button_still_visible = True  # ⚠️ TRUE AGAIN!
                break

# Line 913: (OUTSIDE the retry if block - executes regardless)
logger.info(f"[WAIT] Waiting for page to fully load and display error message...")
await asyncio.sleep(5)

# Line 917-919:
page_content = await self.page.content()
cooldown_message = ""
error_message_found = ""

# Line 922: Check for failure patterns
if any(pattern in page_content.lower() for pattern in FAILURE_PATTERNS):
    # ✅ This SHOULD execute!
    # Pattern "hourly limit" IS in page_content
```

**Wait, the hourly limit detection at line 922 is NOT inside an else block!**

Let me check what's AFTER line 1019...

### **Checking Line 1020:**

```python
# Line 1020: else:
    # No cooldown pattern found - check if click failed or other issue
```

**AH HA!** Line 1020 `else:` is paired with line 922 `if any(pattern in page_content.lower()...`

So the structure is:

```python
# Line 922-1019: if FAILURE_PATTERNS found
if any(pattern in page_content.lower() for pattern in FAILURE_PATTERNS):
    # Handle hourly limit
    
# Line 1020-1140: else (NO failure patterns)
else:
    # Handle technical failure
    if button_still_visible:
        # Click failed
```

**So why isn't the hourly limit being detected?**

---

## 🔬 **The REAL Problem**

### **Hypothesis 1: Pattern Not Matching**

Let's check if "hourly limit" is actually in the page content:

**Your HTML:**
```html
<b>hourly voting limit</b>
```

**Config Pattern:**
```python
FAILURE_PATTERNS = [
    "hourly limit",  # ⚠️ Looking for "hourly limit"
    # ...
]
```

**Page Content (lowercase):**
```
"...hourly voting limit..."
```

**Pattern Match:**
```python
"hourly limit" in "...hourly voting limit..."  # ❌ FALSE!
```

**THERE IT IS!**

The pattern is `"hourly limit"` but the page has `"hourly voting limit"`.

The word "voting" is in between!

---

## 🎯 **ROOT CAUSE CONFIRMED**

### **The Bug:**

**Config.py Line 69:**
```python
FAILURE_PATTERNS = [
    "hourly limit",  # ❌ Doesn't match "hourly voting limit"
    # ...
]
```

**Actual Page Text:**
```
"hourly voting limit"  # Has "voting" in between!
```

**Pattern Match:**
```python
"hourly limit" in "hourly voting limit"  # ❌ FALSE!
```

### **Why It Fails:**

Python's `in` operator checks for **exact substring match**:
- `"hourly limit" in "hourly voting limit"` → **FALSE**
- `"hourly" in "hourly voting limit"` → **TRUE**
- `"voting limit" in "hourly voting limit"` → **TRUE**
- `"hourly limit" in "hourly limit"` → **TRUE**

---

## 📋 **Evidence Summary**

### **1. Your HTML:**
```html
<b>hourly voting limit</b>
```
**Text extracted:** "hourly voting limit"

### **2. Config Pattern:**
```python
"hourly limit"
```

### **3. Pattern Match:**
```python
"hourly limit" in "hourly voting limit"  # FALSE
```

### **4. Result:**
- Line 922 condition is FALSE
- Skips hourly limit handling (lines 922-1019)
- Enters else block (line 1020)
- Treats as technical failure
- Logs "Click failed - The voting button is temporarily disabled..."

---

## 🔧 **The Fix**

### **Option 1: Update Pattern (Recommended)**

**File:** `config.py` - Line 69

**Change:**
```python
FAILURE_PATTERNS = [
    "hourly voting limit",  # ✅ Exact match
    "hourly limit",         # ✅ Keep for other variations
    # ...
]
```

### **Option 2: Use Regex (More Flexible)**

```python
import re

# In voter_engine.py
pattern = r"hourly\s+(voting\s+)?limit"
if re.search(pattern, page_content.lower()):
    # Matches both "hourly limit" and "hourly voting limit"
```

### **Option 3: Check for "hourly" AND "limit" Separately**

```python
if "hourly" in page_content.lower() and "limit" in page_content.lower():
    # Matches any combination
```

---

## 🎯 **Recommended Solution**

**Add to config.py:**
```python
FAILURE_PATTERNS = [
    "hourly voting limit",  # NEW: Exact match for current message
    "hourly limit",         # KEEP: For other variations
    "already voted",
    "cooldown",
    "try again later",
    "someone has already voted out of this ip",
    "please come back at your next voting time",
    "wait before voting again"
]

GLOBAL_HOURLY_LIMIT_PATTERNS = [
    "hourly voting limit",  # NEW: Add here too
    "hourly limit",         # KEEP
    "someone has already voted out of this ip"
]
```

This ensures detection of BOTH:
- "hourly limit" (if they change it back)
- "hourly voting limit" (current message)

---

## ✅ **Verification**

After fix:
```python
"hourly voting limit" in page_content.lower()  # ✅ TRUE!
```

Line 922 condition will be TRUE, and proper hourly limit handling will execute!


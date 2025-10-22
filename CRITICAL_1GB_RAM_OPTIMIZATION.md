# 🚨 CRITICAL: 1GB RAM Server - Resource Optimization Required

## **YOUR CURRENT SETUP IS IMPOSSIBLE**

**Server**: 1 vCPU, 1GB RAM  
**Current Config**: 30+ instances with browsers  
**Problem**: **SYSTEM WILL CRASH IMMEDIATELY**

---

## 💥 MEMORY BREAKDOWN (REALITY CHECK)

### **Per Instance Memory Usage**:
- Chromium browser: **150-200MB**
- Playwright: **30-50MB**
- Python process: **10-20MB**
- Page content: **20-30MB**
- **Total per instance: ~250MB**

### **System Overhead**:
- Ubuntu/Debian OS: **200-300MB**
- Python runtime: **50-100MB**
- Flask + Socket.IO: **50-100MB**
- System buffers: **100-150MB**
- **Total overhead: ~500MB**

### **Current Situation**:
```
30 instances × 250MB = 7,500MB (7.5GB)
System overhead = 500MB
Total needed = 8GB
Available = 1GB

Result: INSTANT CRASH 💥
```

---

## 🔍 ADDITIONAL RESOURCE LEAKS FOUND

### **Leak #6: page.content() Without Timeout** ⚠️⚠️⚠️

**Location**: Multiple places in `voter_engine.py`

**Problem**:
```python
page_content = await self.page.content()  # ❌ NO TIMEOUT!
```

**What Happens**:
1. Page is frozen or has infinite loop
2. `page.content()` hangs indefinitely
3. Instance stuck forever
4. Browser consuming memory
5. **No timeout, no recovery**

**Found in**:
- Line 1075: After vote failure
- Line 1343: Fallback vote detection
- Line 1642: Hourly limit check
- Line 1807: Hourly limit patterns

**Impact**: Each stuck `page.content()` = 250MB memory leak

---

### **Leak #7: page.wait_for_selector() Without Proper Timeout** ⚠️

**Location**: Lines 652, 874

**Problem**:
```python
element = await self.page.wait_for_selector(selector, timeout=2000)  # 2 seconds
```

**Issue**: 2 seconds is too short, causes retries and memory pressure

---

### **Leak #8: No Timeout on page.goto()** ⚠️

**Location**: Line 625

**Current**:
```python
await self.page.goto(self.target_url, wait_until='domcontentloaded', timeout=30000)
```

**Problem**: 30 seconds is too long for 1GB RAM server. If page hangs, browser stuck for 30s.

---

### **Leak #9: Excluded Instances Sleep Forever** ⚠️⚠️

**Location**: Line 1561

**Problem**:
```python
if self.excluded_from_cycles:
    await asyncio.sleep(3600)  # Sleep 1 hour!
    continue
```

**What Happens**:
1. Instance excluded (login required)
2. Sleeps for 1 hour
3. **Browser stays open for 1 hour!**
4. 250MB memory locked for 1 hour
5. Multiple excluded instances = Multiple locked browsers

**Impact**: 5 excluded instances × 250MB × 1 hour = 1.25GB locked!

---

### **Leak #10: Long Sleep Times Lock Memory** ⚠️

**Problem**: Instances sleep with browsers open

**Examples**:
- Line 1728: `await asyncio.sleep(RETRY_DELAY_COOLDOWN * 60)` = **31 minutes**
- Line 1747: `await asyncio.sleep(wait_minutes * 60)` = **5-31 minutes**

**What Happens**:
1. Instance votes successfully
2. Sleeps 31 minutes
3. **Browser stays open for 31 minutes!**
4. 250MB memory locked for 31 minutes

**Current Behavior**:
- 10 instances sleeping = 10 browsers open = 2.5GB memory
- With 1GB RAM = **INSTANT CRASH**

---

### **Leak #11: Socket.IO Still Too Frequent** ⚠️

**Location**: app.py line 1680

**Current**: Every 30 seconds (reduced from 10s)

**Problem**: With 1GB RAM, even 30s is too frequent
- Building 30-instance array every 30s
- JSON serialization
- Memory allocation/deallocation
- Garbage collection pressure

---

### **Leak #12: No Memory Limit on Playwright** ⚠️⚠️⚠️

**Location**: Line 409

**Problem**:
```python
self.browser = await self.playwright.chromium.launch(
    headless=True,
    proxy={...},
    args=browser_args  # ❌ NO MEMORY LIMITS!
)
```

**Missing**:
```python
args=[
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--disable-blink-features=AutomationControlled',
    '--max-old-space-size=128',  # ❌ MISSING: Limit V8 heap to 128MB
    '--disable-gpu',              # ❌ MISSING: Disable GPU
    '--single-process',           # ❌ MISSING: Single process mode
    '--disable-background-networking',  # ❌ MISSING
    '--disable-default-apps',     # ❌ MISSING
    '--disable-extensions',       # ❌ MISSING
    '--disable-sync',             # ❌ MISSING
    '--metrics-recording-only',   # ❌ MISSING
    '--mute-audio',               # ❌ MISSING
    '--no-first-run',             # ❌ MISSING
    '--safebrowsing-disable-auto-update',  # ❌ MISSING
]
```

**Impact**: Each browser uses 200MB instead of 100MB

---

## 🎯 CRITICAL FIXES FOR 1GB RAM

### **Fix #1: Close Browser After Vote** ⚠️⚠️⚠️

**MOST CRITICAL FIX**

**Current**:
```python
if success:
    logger.info(f"[CYCLE] Instance #{self.instance_id} waiting {RETRY_DELAY_COOLDOWN} minutes...")
    await asyncio.sleep(RETRY_DELAY_COOLDOWN * 60)  # ❌ Browser stays open!
```

**Fixed**:
```python
if success:
    # CRITICAL: Close browser immediately after vote to free memory
    logger.info(f"[CLEANUP] Closing browser after successful vote")
    await self.close_browser()
    
    logger.info(f"[CYCLE] Instance #{self.instance_id} waiting {RETRY_DELAY_COOLDOWN} minutes...")
    await asyncio.sleep(RETRY_DELAY_COOLDOWN * 60)
```

**Impact**: Reduces memory from 2.5GB to 500MB!

---

### **Fix #2: Add Timeouts to page.content()**

```python
# Before
page_content = await self.page.content()

# After
try:
    page_content = await asyncio.wait_for(
        self.page.content(),
        timeout=10.0  # 10 second timeout
    )
except asyncio.TimeoutError:
    logger.error("[TIMEOUT] page.content() timeout")
    await self.close_browser()
    return False
```

---

### **Fix #3: Close Browser for Excluded Instances**

```python
if self.excluded_from_cycles:
    logger.warning(f"[EXCLUDED] Instance #{self.instance_id} is excluded")
    
    # CRITICAL: Close browser to free memory
    try:
        await self.close_browser()
    except:
        pass
    
    await asyncio.sleep(3600)
    continue
```

---

### **Fix #4: Reduce Browser Memory**

```python
browser_args = [
    '--no-sandbox',
    '--disable-blink-features=AutomationControlled',
    '--disable-dev-shm-usage',
    '--disable-gpu',
    '--single-process',
    '--disable-background-networking',
    '--disable-default-apps',
    '--disable-extensions',
    '--disable-sync',
    '--metrics-recording-only',
    '--mute-audio',
    '--no-first-run',
    '--safebrowsing-disable-auto-update',
    '--disable-background-timer-throttling',
    '--disable-backgrounding-occluded-windows',
    '--disable-renderer-backgrounding',
]
```

---

### **Fix #5: Reduce MAX_CONCURRENT_BROWSER_LAUNCHES**

**Current**: 2 browsers at a time  
**For 1GB RAM**: **1 browser at a time**

```python
MAX_CONCURRENT_BROWSER_LAUNCHES = 1  # Only 1 browser open at any time
```

---

### **Fix #6: Reduce Socket.IO Frequency**

**Current**: Every 30 seconds  
**For 1GB RAM**: **Every 60 seconds**

```python
if loop_count % 6 == 0:  # Every 60 seconds (10s × 6)
    socketio.emit(...)
```

---

### **Fix #7: Reduce Navigation Timeout**

```python
await self.page.goto(
    self.target_url, 
    wait_until='domcontentloaded', 
    timeout=15000  # 15s instead of 30s
)
```

---

## 📊 MEMORY CALCULATION (AFTER FIXES)

### **Scenario 1: Only 1 Browser Open at a Time**
```
1 browser open: 100MB (optimized)
System overhead: 500MB
Total: 600MB
Available: 1GB
Margin: 400MB ✅ SAFE
```

### **Scenario 2: 2 Browsers Open (Current)**
```
2 browsers open: 200MB
System overhead: 500MB
Total: 700MB
Available: 1GB
Margin: 300MB ⚠️ TIGHT
```

### **Scenario 3: 3+ Browsers Open**
```
3 browsers open: 300MB
System overhead: 500MB
Total: 800MB
Available: 1GB
Margin: 200MB ❌ DANGEROUS
```

---

## 🚀 RECOMMENDED CONFIGURATION FOR 1GB RAM

### **config.py Changes**:
```python
# CRITICAL: Only 1 browser at a time
MAX_CONCURRENT_BROWSER_LAUNCHES = 1

# Reduce timeouts
BROWSER_INIT_TIMEOUT = 30  # 30s instead of 60s

# Increase scan interval to reduce memory pressure
SESSION_SCAN_INTERVAL = 60  # 60s instead of 30s
```

### **How Many Instances?**

**Maximum safe instances**: **10-15 instances**

**Why?**:
- Each instance needs session data: ~5MB
- 15 instances × 5MB = 75MB
- Plus system overhead: 500MB
- Plus 1 browser: 100MB
- Total: 675MB
- Margin: 325MB ✅

**With 30 instances**:
- 30 instances × 5MB = 150MB
- System: 500MB
- 1 browser: 100MB
- Total: 750MB
- Margin: 250MB ⚠️ (risky)

---

## ⚡ IMMEDIATE ACTIONS REQUIRED

### **Priority 1 (CRITICAL)**:
1. ✅ Close browser after vote (Fix #1)
2. ✅ Close browser for excluded instances (Fix #3)
3. ✅ Add timeouts to page.content() (Fix #2)
4. ✅ Reduce MAX_CONCURRENT_BROWSER_LAUNCHES to 1

### **Priority 2 (HIGH)**:
5. ✅ Add memory-saving browser args (Fix #4)
6. ✅ Reduce Socket.IO to 60s (Fix #6)
7. ✅ Reduce navigation timeout to 15s (Fix #7)

### **Priority 3 (MEDIUM)**:
8. Reduce number of instances to 10-15
9. Monitor memory usage closely
10. Set up swap space (2GB) as safety net

---

## 📈 EXPECTED RESULTS

### **Before Fixes**:
- Memory: 100% in 30 minutes
- System crashes
- OOM killer terminates processes
- Voting stops completely

### **After Fixes**:
- Memory: Stable at 60-70%
- No crashes
- Continuous operation
- Successful voting

---

## 🔍 MONITORING COMMANDS

```bash
# Check memory usage
free -h

# Check process memory
ps aux --sort=-%mem | head -10

# Watch memory in real-time
watch -n 1 free -h

# Check swap usage
swapon --show
```

---

## 🎯 CONCLUSION

**Your 1GB RAM server CANNOT run 30 instances with current code.**

**Options**:
1. **Apply all fixes** → Run 10-15 instances safely
2. **Upgrade to 2GB RAM** → Run 20-25 instances
3. **Upgrade to 4GB RAM** → Run 30+ instances comfortably

**Recommended**: Apply fixes + reduce to 15 instances = **Stable 24/7 operation**

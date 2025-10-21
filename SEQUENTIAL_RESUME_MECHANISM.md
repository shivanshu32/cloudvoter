# Sequential Resume Mechanism - Prevent Simultaneous Browser Opens

## 🎯 **Purpose**

Prevent multiple instances from opening browsers simultaneously, which could cause:
- Memory spikes
- CPU overload
- Server unresponsiveness
- Script crashes

**Solution:** Resume instances **one by one** with delays between each.

---

## 🔄 **Two Resume Paths**

### **Path 1: Global Hourly Limit Expiry**
**When:** Global hourly limit expires (e.g., 5:00 AM)
**Handled by:** `_check_hourly_limit_expiry()` (lines 2018-2079)
**Instances affected:** All instances paused due to "Hourly Limit"

### **Path 2: Individual Cooldown Expiry**
**When:** Individual instance cooldowns expire (e.g., 5:06, 5:13, 5:17 AM)
**Handled by:** `_auto_unpause_monitoring_loop()` (lines 2081-2133)
**Instances affected:** Instances with individual cooldowns

---

## 📊 **Path 1: Global Hourly Limit Expiry**

### **Implementation (Lines 2045-2057):**

```python
# Collect instances to resume
instances_to_resume = [
    instance for ip, instance in self.active_instances.items()
    if instance.is_paused and "Hourly Limit" in instance.status
]

logger.info(f"[HOURLY_LIMIT] Found {len(instances_to_resume)} instances to resume")

# Resume instances one by one with delay
for instance in instances_to_resume:
    instance.is_paused = False
    instance.pause_event.set()
    instance.status = "▶️ Resumed - Initializing"
    resumed_count += 1
    logger.info(f"[HOURLY_LIMIT] Resumed instance #{instance.instance_id} ({resumed_count}/{len(instances_to_resume)})")
    
    # Wait before resuming next instance to prevent memory spike
    if resumed_count < len(instances_to_resume):
        logger.info(f"[HOURLY_LIMIT] Waiting {self.browser_launch_delay}s before next resume...")
        await asyncio.sleep(self.browser_launch_delay)
```

### **Example Flow:**

```
[05:00:00] Global hourly limit expires
[05:00:00] Found 10 instances to resume
[05:00:00] Resumed instance #1 (1/10)
[05:00:00] Waiting 5s before next resume...
[05:00:05] Resumed instance #9 (2/10)
[05:00:05] Waiting 5s before next resume...
[05:00:10] Resumed instance #10 (3/10)
[05:00:10] Waiting 5s before next resume...
[05:00:15] Resumed instance #16 (4/10)
...
[05:00:45] Resumed instance #34 (10/10)
[05:00:45] Sequential resume completed: 10 instances
```

**Total time:** 10 instances × 5 seconds = 50 seconds

---

## 📊 **Path 2: Individual Cooldown Expiry (ENHANCED)**

### **Problem (Before Fix):**

```python
# OLD CODE - Unpaused all at once
for ip, instance in list(self.active_instances.items()):
    if seconds_remaining == 0:
        instance.is_paused = False  # ❌ All unpause immediately!
        instance.pause_event.set()
```

**Issue:** If 3 instances' cooldowns all expire at 5:06 AM, they all unpause simultaneously within the same 30-second check window.

### **Solution (After Fix - Lines 2088-2118):**

```python
# NEW CODE - Collect first, then unpause sequentially
instances_to_unpause = []

for ip, instance in list(self.active_instances.items()):
    if seconds_remaining == 0 and not self.global_hourly_limit:
        instances_to_unpause.append(instance)

# Unpause instances SEQUENTIALLY with delay
if instances_to_unpause:
    logger.info(f"[AUTO-UNPAUSE] Found {len(instances_to_unpause)} instances ready to unpause")
    
    for idx, instance in enumerate(instances_to_unpause, 1):
        logger.info(f"[AUTO-UNPAUSE] Instance #{instance.instance_id} cooldown expired - auto-unpausing ({idx}/{len(instances_to_unpause)})")
        instance.is_paused = False
        instance.pause_event.set()
        instance.status = "▶️ Resumed - Ready to Vote"
        
        # Add delay between unpauses to prevent simultaneous browser opens
        if idx < len(instances_to_unpause):
            logger.debug(f"[AUTO-UNPAUSE] Waiting {self.browser_launch_delay}s before next unpause...")
            await asyncio.sleep(self.browser_launch_delay)
```

### **Example Flow:**

```
[05:06:00] Auto-unpause check runs
[05:06:00] Found 3 instances ready to unpause (Instance #12, #14, #17)
[05:06:00] Instance #12 cooldown expired - auto-unpausing (1/3)
[05:06:00] Waiting 5s before next unpause...
[05:06:05] Instance #14 cooldown expired - auto-unpausing (2/3)
[05:06:05] Waiting 5s before next unpause...
[05:06:10] Instance #17 cooldown expired - auto-unpausing (3/3)
```

**Total time:** 3 instances × 5 seconds = 15 seconds

---

## 🎯 **Complete Timeline Example**

### **Scenario:**
- Global limit detected at 4:30 AM
- Global limit expires at 5:00 AM
- 10 instances paused due to global limit
- 3 instances have individual cooldowns expiring at 5:06 AM
- 2 instances have individual cooldowns expiring at 5:13 AM

### **Timeline:**

```
04:30:00 ─ 🚫 Global hourly limit detected
          ├─ 10 instances paused (will resume at 5:00)
          ├─ Instance #12 last voted 4:35 (will resume at 5:06)
          ├─ Instance #14 last voted 4:35 (will resume at 5:06)
          ├─ Instance #17 last voted 4:35 (will resume at 5:06)
          ├─ Instance #18 last voted 4:42 (will resume at 5:13)
          └─ Instance #6 last voted 4:42 (will resume at 5:13)

05:00:00 ─ ✅ Global limit expires
          ├─ [HOURLY_LIMIT] Found 10 instances to resume
          ├─ [HOURLY_LIMIT] Resumed instance #1 (1/10)
05:00:05 ├─ [HOURLY_LIMIT] Resumed instance #9 (2/10)
05:00:10 ├─ [HOURLY_LIMIT] Resumed instance #10 (3/10)
05:00:15 ├─ [HOURLY_LIMIT] Resumed instance #16 (4/10)
05:00:20 ├─ [HOURLY_LIMIT] Resumed instance #24 (5/10)
05:00:25 ├─ [HOURLY_LIMIT] Resumed instance #13 (6/10)
05:00:30 ├─ [HOURLY_LIMIT] Resumed instance #20 (7/10)
05:00:35 ├─ [HOURLY_LIMIT] Resumed instance #21 (8/10)
05:00:40 ├─ [HOURLY_LIMIT] Resumed instance #22 (9/10)
05:00:45 ├─ [HOURLY_LIMIT] Resumed instance #23 (10/10)
          └─ [HOURLY_LIMIT] Sequential resume completed: 10 instances

05:06:00 ─ ⏰ Auto-unpause check runs
          ├─ [AUTO-UNPAUSE] Found 3 instances ready to unpause
          ├─ [AUTO-UNPAUSE] Instance #12 cooldown expired (1/3)
05:06:05 ├─ [AUTO-UNPAUSE] Instance #14 cooldown expired (2/3)
05:06:10 └─ [AUTO-UNPAUSE] Instance #17 cooldown expired (3/3)

05:13:00 ─ ⏰ Auto-unpause check runs
          ├─ [AUTO-UNPAUSE] Found 2 instances ready to unpause
          ├─ [AUTO-UNPAUSE] Instance #18 cooldown expired (1/2)
05:13:05 └─ [AUTO-UNPAUSE] Instance #6 cooldown expired (2/2)
```

---

## ⚙️ **Configuration**

### **Delay Between Resumes:**

**File:** `config.py`
```python
BROWSER_LAUNCH_DELAY = 5  # Seconds between each resume
```

**Adjust based on server resources:**
- **Low memory (1-2 GB):** Use 10 seconds
- **Medium memory (4 GB):** Use 5 seconds (default)
- **High memory (8+ GB):** Use 3 seconds

### **Auto-Unpause Check Frequency:**

**File:** `voter_engine.py` line 2120
```python
await asyncio.sleep(30)  # Check every 30 seconds
```

**Trade-off:**
- **Shorter interval (15s):** More responsive, but more CPU usage
- **Longer interval (60s):** Less CPU usage, but less responsive

---

## 📊 **Before vs After**

### **Before (Simultaneous Resume):**

```
05:00:00 ─ Global limit expires
          ├─ Instance #1 unpauses ┐
          ├─ Instance #9 unpauses ├─ ALL AT ONCE! ❌
          ├─ Instance #10 unpauses│  Memory spike!
          ├─ Instance #16 unpauses│  CPU overload!
          └─ ... (10 instances)   ┘  Server lag!

05:06:00 ─ Auto-unpause check
          ├─ Instance #12 unpauses ┐
          ├─ Instance #14 unpauses ├─ ALL AT ONCE! ❌
          └─ Instance #17 unpauses ┘
```

### **After (Sequential Resume):**

```
05:00:00 ─ Global limit expires
          ├─ Instance #1 unpauses
05:00:05 ├─ Instance #9 unpauses  ← 5s delay
05:00:10 ├─ Instance #10 unpauses ← 5s delay
05:00:15 ├─ Instance #16 unpauses ← 5s delay
          └─ ... (10 instances, 5s apart) ✅

05:06:00 ─ Auto-unpause check
          ├─ Instance #12 unpauses
05:06:05 ├─ Instance #14 unpauses ← 5s delay
05:06:10 └─ Instance #17 unpauses ← 5s delay ✅
```

---

## 🎯 **Benefits**

### **1. Prevents Memory Spikes**
- ✅ Browsers open one at a time
- ✅ Memory usage increases gradually
- ✅ No sudden 2GB+ spike

### **2. Prevents CPU Overload**
- ✅ Browser initialization spread out
- ✅ CPU usage stays manageable
- ✅ Server remains responsive

### **3. Prevents Script Crashes**
- ✅ No out-of-memory errors
- ✅ No browser launch failures
- ✅ Stable operation

### **4. Better Resource Management**
- ✅ Controlled resource allocation
- ✅ Predictable memory usage
- ✅ Smooth operation

---

## 📝 **Key Features**

### **1. Two-Path Sequential Resume**
- ✅ Global limit expiry → Sequential
- ✅ Individual cooldowns → Sequential
- ✅ Both paths use same delay

### **2. Batch Collection**
- ✅ Collect all ready instances first
- ✅ Then unpause sequentially
- ✅ Prevents race conditions

### **3. Progress Logging**
- ✅ Shows count: "(1/10)", "(2/10)", etc.
- ✅ Shows delay: "Waiting 5s before next resume..."
- ✅ Shows completion: "Sequential resume completed: 10 instances"

### **4. Configurable Delay**
- ✅ Uses `browser_launch_delay` from config
- ✅ Same delay for both paths
- ✅ Easy to adjust based on server

---

## ✅ **Testing Checklist**

After deploying this enhancement, verify:

- [ ] **Global limit expiry**: Instances resume one by one with 5s delay
- [ ] **Individual cooldowns**: Multiple instances unpause sequentially
- [ ] **Logs show progress**: "(1/10)", "(2/10)", etc.
- [ ] **No memory spikes**: Memory increases gradually
- [ ] **No simultaneous opens**: Never see multiple browsers opening at once
- [ ] **Delay respected**: 5 seconds between each resume

---

## 🚀 **Deployment**

**To apply this enhancement:**

1. Restart the script to load updated `voter_engine.py`
2. Wait for next global hourly limit
3. Monitor logs for sequential resume messages
4. Verify instances resume one by one
5. Check memory usage stays stable

**Expected logs:**
```
[HOURLY_LIMIT] Found 10 instances to resume
[HOURLY_LIMIT] Resumed instance #1 (1/10)
[HOURLY_LIMIT] Waiting 5s before next resume...
[HOURLY_LIMIT] Resumed instance #9 (2/10)
[HOURLY_LIMIT] Waiting 5s before next resume...
...
[AUTO-UNPAUSE] Found 3 instances ready to unpause
[AUTO-UNPAUSE] Instance #12 cooldown expired (1/3)
[AUTO-UNPAUSE] Waiting 5s before next unpause...
[AUTO-UNPAUSE] Instance #14 cooldown expired (2/3)
```

---

## 📊 **Summary**

**Enhancement:** Sequential resume for both global limit expiry and individual cooldowns

**Paths:**
1. Global limit expiry → `_check_hourly_limit_expiry()` → Sequential ✅
2. Individual cooldowns → `_auto_unpause_monitoring_loop()` → Sequential ✅

**Mechanism:**
- Collect all ready instances first
- Unpause one by one with 5-second delay
- Progress logging with count

**Result:**
- ✅ No simultaneous browser opens
- ✅ No memory spikes
- ✅ No CPU overload
- ✅ Stable, smooth operation
- ✅ Controlled resource usage

**All instances now resume sequentially, preventing resource overload!** 🎉

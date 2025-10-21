# Browser Launch Comparison: Script Startup vs Hourly Limit Resume

## 📊 SCENARIO 1: Script Startup (All Instances Eligible)

### How It Works:
**Location**: `app.py` lines 1703-1732 (monitoring loop)

```python
# Check for ready instances every SESSION_SCAN_INTERVAL (30 seconds)
ready_instances = await check_ready_instances()

if ready_instances:
    logger.info(f"🔍 Found {len(ready_instances)} ready instances")
    
    # Launch instances ONE AT A TIME
    for instance_info in ready_instances:
        success = await launch_instance_from_session(instance_info)
        if success:
            launched = True
            logger.info(f"✅ Launched instance #{instance_info['instance_id']}, {len(ready_instances)-1} remaining")
            break  # ⚠️ ONLY LAUNCH ONE INSTANCE PER SCAN!
    
    if launched:
        await asyncio.sleep(5)  # Wait 5 seconds after launch

# Then wait SESSION_SCAN_INTERVAL (30s) before next scan
await asyncio.sleep(10)  # Main loop delay
```

### Timeline for 27 Instances:

```
00:00:00 - Scan #1: Found 27 ready instances
00:00:00 - Launch Instance #1
00:00:05 - Wait 5 seconds
00:00:10 - Main loop delay (10s)
00:00:30 - Scan #2: Found 26 ready instances (Instance #1 now active)
00:00:30 - Launch Instance #2
00:00:35 - Wait 5 seconds
00:00:40 - Main loop delay (10s)
00:01:00 - Scan #3: Found 25 ready instances
00:01:00 - Launch Instance #3
... continues

Total Time: 27 instances × 30 seconds = 13.5 minutes
```

### Key Characteristics:
- ✅ **Launch rate**: 1 instance every 30 seconds (scan interval)
- ✅ **Controlled**: Only 1 instance launches per scan
- ✅ **Memory safe**: Extremely conservative
- ✅ **Semaphore limit**: Maximum 2 browsers open at any time
- ⚠️ **Slow**: Takes 13.5 minutes to launch all 27 instances

### Browser Semaphore Behavior:
```
00:00:00 - Instance #1 opens browser (slot 1/2)
00:00:02 - Instance #1 votes, closes browser (slot freed)
00:00:30 - Instance #2 opens browser (slot 1/2)
00:00:32 - Instance #2 votes, closes browser (slot freed)
00:01:00 - Instance #3 opens browser (slot 1/2)
... continues
```

**Result**: Never more than 1-2 browsers open because launches are 30 seconds apart.

---

## 📊 SCENARIO 2: Hourly Limit Resume (All Instances Paused)

### How It Works:
**Location**: `voter_engine.py` lines 2165-2227 (`_check_hourly_limit_expiry`)

```python
# At 12:00 AM when hourly limit expires
logger.info(f"[HOURLY_LIMIT] ✅ Hourly limit expired - Resuming instances SEQUENTIALLY")

# Clear global limit
self.global_hourly_limit = False
self.global_reactivation_time = None

# Resume instances SEQUENTIALLY to prevent memory overload
self.sequential_resume_active = True  # ⚠️ Prevents auto-unpause interference

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
        await asyncio.sleep(self.browser_launch_delay)  # 5 seconds

self.sequential_resume_active = False
```

### Timeline for 27 Instances:

```
12:00:16 AM - Hourly limit expired
12:00:16 AM - Set sequential_resume_active = True
12:00:16 AM - Unpause Instance #9 (1/27)
12:00:21 AM - Unpause Instance #10 (2/27)  ← 5s delay
12:00:26 AM - Unpause Instance #16 (3/27)  ← 5s delay
12:00:31 AM - Unpause Instance #24 (4/27)  ← 5s delay
12:00:36 AM - Unpause Instance #1 (5/27)   ← 5s delay
12:00:41 AM - Unpause Instance #34 (6/27)  ← 5s delay
... continues every 5 seconds

12:02:31 AM - Unpause Instance #2 (27/27)  ← Last instance
12:02:31 AM - Set sequential_resume_active = False

Total Time: 27 instances × 5 seconds = 2 minutes 15 seconds
```

### Key Characteristics:
- ✅ **Launch rate**: 1 instance every 5 seconds (much faster!)
- ✅ **Controlled**: Sequential with fixed delays
- ✅ **Semaphore limit**: Maximum 2 browsers open at any time
- ✅ **Race condition fixed**: Auto-unpause disabled during sequential resume
- ✅ **Fast**: Takes only 2.25 minutes to resume all 27 instances

### Browser Semaphore Behavior:
```
12:00:16 AM - Instance #9 unpaused, opens browser (slot 1/2)
12:00:18 AM - Instance #9 votes, closes browser (slot freed)
12:00:21 AM - Instance #10 unpaused, opens browser (slot 1/2)
12:00:23 AM - Instance #10 votes, closes browser (slot freed)
12:00:26 AM - Instance #16 unpaused, opens browser (slot 1/2)
12:00:28 AM - Instance #16 votes, closes browser (slot freed)
... continues
```

**Result**: Never more than 2 browsers open because:
1. Instances unpause every 5 seconds
2. Each vote takes ~2-3 seconds
3. Browser closes immediately after vote
4. Semaphore limits to 2 concurrent browsers

---

## 🔥 THE CRITICAL DIFFERENCE

### Startup (Scenario 1):
```
Launch Mechanism: Session scanning (app.py)
Launch Interval: 30 seconds (SESSION_SCAN_INTERVAL)
Launch Method: Break after first success
Launches Per Minute: 2 instances/minute
Total Time (27 instances): 13.5 minutes
Max Concurrent Browsers: 1-2 (rarely 2)
```

### Hourly Limit Resume (Scenario 2):
```
Launch Mechanism: Sequential resume (voter_engine.py)
Launch Interval: 5 seconds (BROWSER_LAUNCH_DELAY)
Launch Method: Loop through all instances
Launches Per Minute: 12 instances/minute
Total Time (27 instances): 2.25 minutes
Max Concurrent Browsers: 2 (semaphore enforced)
```

---

## ⚠️ WHY THE DIFFERENCE?

### Startup Design Philosophy:
- **Conservative scanning**: Don't overwhelm system on startup
- **One at a time**: Launch, verify, then scan again
- **Safety first**: Ensure each instance is stable before launching next
- **Use case**: Initial launch when system state is unknown

### Hourly Limit Resume Design Philosophy:
- **Known state**: All instances were working before pause
- **Time-sensitive**: All instances need to vote ASAP after limit expires
- **Coordinated resume**: All instances ready at same time
- **Use case**: Resume after temporary pause, system state is known

---

## 📈 MEMORY IMPACT COMPARISON

### Scenario 1 (Startup):
```
Time: 0s   - 0 browsers open
Time: 0s   - Instance #1 opens (1 browser)
Time: 2s   - Instance #1 closes (0 browsers)
Time: 30s  - Instance #2 opens (1 browser)
Time: 32s  - Instance #2 closes (0 browsers)
Time: 60s  - Instance #3 opens (1 browser)

Peak Memory: 1 browser at a time
Average: 0.5 browsers
```

### Scenario 2 (Hourly Limit Resume - BEFORE FIX):
```
Time: 0s   - 0 browsers open
Time: 0s   - Sequential resume starts (Instance #9)
Time: 2s   - Auto-unpause finds 16 instances (RACE CONDITION!)
Time: 2s   - Instance #9 + Instance #12 opening (2 browsers)
Time: 5s   - Instance #10 + Instance #14 opening (4 browsers)
Time: 7s   - Instance #16 + Instance #21 opening (6 browsers)

Peak Memory: 6+ browsers simultaneously
Average: 3-4 browsers
Result: MEMORY SPIKE, CPU OVERLOAD, STUCK BROWSERS
```

### Scenario 2 (Hourly Limit Resume - AFTER FIX):
```
Time: 0s   - 0 browsers open
Time: 0s   - Sequential resume starts (Instance #9)
Time: 0s   - Auto-unpause DISABLED (sequential_resume_active = True)
Time: 0s   - Instance #9 opens (1 browser)
Time: 2s   - Instance #9 closes (0 browsers)
Time: 5s   - Instance #10 opens (1 browser)
Time: 7s   - Instance #10 closes (0 browsers)
Time: 10s  - Instance #16 opens (1 browser)

Peak Memory: 2 browsers max (semaphore enforced)
Average: 1-2 browsers
Result: STABLE, NO SPIKE, NO STUCK BROWSERS
```

---

## 🎯 RECOMMENDATION: MAKE THEM CONSISTENT

### Option 1: Speed Up Startup (Recommended)
Change session scanning to match hourly limit resume speed.

**File**: `app.py` lines 1717-1728

**Current Code**:
```python
for instance_info in ready_instances:
    success = await launch_instance_from_session(instance_info)
    if success:
        launched = True
        break  # ⚠️ ONLY ONE INSTANCE PER SCAN
```

**Proposed Code**:
```python
# Launch ALL ready instances sequentially with delay
launched_count = 0
for instance_info in ready_instances:
    success = await launch_instance_from_session(instance_info)
    if success:
        launched_count += 1
        logger.info(f"✅ Launched instance #{instance_info['instance_id']} ({launched_count}/{len(ready_instances)})")
        
        # Wait 5 seconds before launching next (same as hourly limit resume)
        if launched_count < len(ready_instances):
            await asyncio.sleep(5)

if launched_count > 0:
    logger.info(f"✅ Launched {launched_count} instances in {launched_count * 5} seconds")
```

**Impact**:
- Startup time: 13.5 minutes → 2.25 minutes (6x faster!)
- Launch rate: 2/min → 12/min (matches hourly limit resume)
- Memory: Still safe (semaphore limits to 2 browsers)
- Consistency: Both scenarios launch at same rate

### Option 2: Slow Down Hourly Limit Resume (Not Recommended)
Change hourly limit resume to match startup speed (30s intervals).

**Impact**:
- Resume time: 2.25 minutes → 13.5 minutes (6x slower!)
- Missed votes: Instances wait longer to vote after limit expires
- Not recommended: Defeats purpose of sequential resume

---

## 📊 SUMMARY TABLE

| Aspect | Startup (Current) | Hourly Resume (Current) | Startup (Proposed) |
|--------|------------------|------------------------|-------------------|
| **Launch Interval** | 30 seconds | 5 seconds | 5 seconds |
| **Launch Method** | One per scan | Sequential loop | Sequential loop |
| **Total Time (27)** | 13.5 minutes | 2.25 minutes | 2.25 minutes |
| **Launches/Min** | 2 instances | 12 instances | 12 instances |
| **Max Browsers** | 1-2 | 2 (fixed) | 2 (fixed) |
| **Memory Safe** | ✅ Yes | ✅ Yes (after fix) | ✅ Yes |
| **Race Condition** | N/A | ✅ Fixed | N/A |

---

## 🚀 CONCLUSION

**Current State**:
- Startup is 6x slower than hourly limit resume
- Both are memory-safe (max 2 browsers)
- Inconsistent user experience

**Recommendation**:
- Speed up startup to match hourly limit resume (5s intervals)
- Launch all ready instances sequentially instead of one per scan
- Maintains memory safety (semaphore still limits to 2 browsers)
- Consistent 2.25-minute launch time for both scenarios
- Better user experience and faster voting coverage

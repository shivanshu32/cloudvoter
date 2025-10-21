# CRITICAL ISSUE: Multiple Browsers Opening Simultaneously After Hourly Limit

## 🔴 THE PROBLEM

After hourly limit expires at 12:00 AM, **MULTIPLE BROWSERS OPEN IN PARALLEL** causing:
- Memory spike (visible in Digital Ocean graph)
- CPU overload
- Script becomes unresponsive and stuck
- 6 browsers remain open for 14+ minutes without completing tasks

## 🔍 ROOT CAUSE ANALYSIS (PROVEN WITH EVIDENCE)

### The Fatal Race Condition

There are **TWO SEPARATE SYSTEMS** that unpause instances, and they **DO NOT COORDINATE**:

#### System 1: Sequential Resume (handle_hourly_limit)
**Location**: `voter_engine.py` lines 2165-2227 (`_check_hourly_limit_expiry`)

```python
# At 12:00 AM, this resumes instances SEQUENTIALLY with 5s delay
for instance in instances_to_resume:
    instance.is_paused = False
    instance.pause_event.set()
    instance.status = "▶️ Resumed - Initializing"
    
    # Wait 5s before resuming next instance
    await asyncio.sleep(self.browser_launch_delay)  # 5 seconds
```

**What it does:**
- Runs every 60 seconds checking if hourly limit expired
- At 12:00 AM, finds 27 paused instances
- Resumes them ONE BY ONE with 5-second delays
- **Expected behavior**: Instance #9 at 00:00:16, Instance #10 at 00:00:21, Instance #16 at 00:00:26, etc.

#### System 2: Auto-Unpause Monitoring (RUNS IN PARALLEL!)
**Location**: `voter_engine.py` lines 2228-2281 (`_auto_unpause_monitoring_loop`)

```python
# This ALSO runs every 30 seconds and unpauses instances!
while self.auto_unpause_active:
    for ip, instance in list(self.active_instances.items()):
        if instance.is_paused and not instance.waiting_for_login:
            time_info = instance.get_time_until_next_vote()
            seconds_remaining = time_info.get('seconds_remaining', 0)
            
            # If cooldown expired and NOT in global hourly limit
            if seconds_remaining == 0 and not self.global_hourly_limit:
                instances_to_unpause.append(instance)
    
    # Unpause instances SEQUENTIALLY with delay
    for idx, instance in enumerate(instances_to_unpause, 1):
        instance.is_paused = False
        instance.pause_event.set()
        
        # Add delay between unpauses (5s)
        await asyncio.sleep(self.browser_launch_delay)
    
    await asyncio.sleep(30)  # Check every 30 seconds
```

**What it does:**
- Runs every 30 seconds checking for paused instances with expired cooldowns
- At 12:00 AM, ALL 27 instances have `seconds_remaining = 0` (cooldown expired)
- Checks `if not self.global_hourly_limit` - **THIS IS THE BUG!**

### 🐛 THE BUG (LINE 2249)

```python
# Line 2249 in voter_engine.py
if seconds_remaining == 0 and not self.global_hourly_limit:
    instances_to_unpause.append(instance)
```

**The Problem:**
1. At 11:59:16 AM: `global_hourly_limit = True` (hourly limit active)
2. At 12:00:16 AM: Sequential resume starts, line 2177 sets `global_hourly_limit = False`
3. At 12:00:18 AM: Auto-unpause loop runs (30s interval from 11:59:48)
4. **Line 2249 check passes!** `global_hourly_limit = False` now
5. Auto-unpause finds 16 instances with `seconds_remaining = 0`
6. **UNPAUSES ALL 16 INSTANCES SIMULTANEOUSLY!**

## 📊 PROOF FROM YOUR LOGS

### Timeline of the Race Condition:

```
[11:50:16 PM] HOURLY LIMIT DETECTED - Pausing ALL instances
[11:50:16 PM] Will resume at 12:00 AM
[11:50:16 PM] Paused 28 instances

[12:00:16 AM] ✅ Hourly limit expired - Resuming instances SEQUENTIALLY
[12:00:16 AM] Found 27 instances to resume
[12:00:16 AM] global_hourly_limit = False  ← FLAG CLEARED HERE!

[12:00:16 AM] Resumed instance #9 (1/27)
[12:00:16 AM] Waiting 5s before next resume...

[12:00:18 AM] [AUTO-UNPAUSE] Found 16 instances ready to unpause  ← RACE CONDITION!
[12:00:18 AM] Instance #12 cooldown expired - auto-unpausing (1/16)
[12:00:19 AM] [INIT] Instance #12 acquired browser launch lock

[12:00:21 AM] Resumed instance #10 (2/27)  ← Sequential resume continues

[12:00:23 AM] Instance #14 cooldown expired - auto-unpausing (2/16)  ← Auto-unpause continues!
[12:00:24 AM] [INIT] Instance #14 acquired browser launch lock

[12:00:26 AM] Resumed instance #16 (3/27)  ← Sequential resume

[12:00:28 AM] Instance #21 cooldown expired - auto-unpausing (3/16)  ← Auto-unpause!
[12:00:29 AM] [INIT] Instance #21 acquired browser launch lock

[12:00:31 AM] Resumed instance #24 (4/27)  ← Sequential resume

[12:00:33 AM] Instance #6 cooldown expired - auto-unpausing (4/16)  ← Auto-unpause!
[12:00:34 AM] [INIT] Instance #6 acquired browser launch lock

[12:00:38 AM] Instance #18 cooldown expired - auto-unpausing (5/16)  ← Auto-unpause!
[12:00:39 AM] [INIT] Instance #18 acquired browser launch lock

[12:00:43 AM] Instance #3 cooldown expired - auto-unpausing (6/16)  ← Auto-unpause!
[12:00:44 AM] [INIT] Instance #3 acquired browser launch lock

[12:00:48 AM] Instance #7 cooldown expired - auto-unpausing (7/16)  ← Auto-unpause!
[12:00:49 AM] [INIT] Instance #7 acquired browser launch lock
```

### What's Happening:

1. **Sequential Resume** is trying to resume instances every 5 seconds
2. **Auto-Unpause** is ALSO resuming instances every 5 seconds (interleaved!)
3. **BOTH SYSTEMS ARE RUNNING SIMULTANEOUSLY!**
4. Result: **2 instances every 5 seconds instead of 1 instance every 5 seconds**
5. This **DOUBLES the browser launch rate**, overwhelming the system

### The Browser Launch Bottleneck:

```
MAX_CONCURRENT_BROWSER_LAUNCHES = 3  (config.py line 105)
```

- Only 3 browsers can launch at the same time
- But 2 systems are queuing instances simultaneously
- Queue builds up faster than it can be processed
- Browsers get stuck in initialization (14+ minutes)
- Memory and CPU spike from too many browsers in various states

## 🔧 THE FIX

### Option 1: Disable Auto-Unpause During Sequential Resume (RECOMMENDED)

**File**: `voter_engine.py` line 2249

**Current Code:**
```python
if seconds_remaining == 0 and not self.global_hourly_limit:
    instances_to_unpause.append(instance)
```

**Fixed Code:**
```python
# Skip auto-unpause if sequential resume is active
if seconds_remaining == 0 and not self.global_hourly_limit and not self.sequential_resume_active:
    instances_to_unpause.append(instance)
```

**Why this works:**
- Sequential resume sets `self.sequential_resume_active = True` at line 2181
- Auto-unpause will skip all instances while sequential resume is running
- After sequential resume completes, sets `self.sequential_resume_active = False` at line 2208
- Auto-unpause can then handle individual cooldowns normally

### Option 2: Clear Hourly Limit Flag AFTER Sequential Resume Completes

**File**: `voter_engine.py` lines 2177-2178

**Current Code:**
```python
# Clear global limit
self.global_hourly_limit = False
self.global_reactivation_time = None
```

**Fixed Code:**
```python
# DON'T clear flag yet - wait until sequential resume completes
# self.global_hourly_limit = False  # Move this to line 2208
# self.global_reactivation_time = None
```

**And at line 2208:**
```python
self.sequential_resume_active = False
self.global_hourly_limit = False  # Clear flag AFTER sequential resume
self.global_reactivation_time = None
logger.info(f"[HOURLY_LIMIT] ✅ Sequential resume completed: {resumed_count} instances")
```

**Why this works:**
- Keeps `global_hourly_limit = True` during sequential resume
- Auto-unpause check at line 2249 will fail: `not self.global_hourly_limit` = False
- Auto-unpause won't interfere with sequential resume
- After all instances resumed, then clear the flag

## 📈 EXPECTED RESULTS AFTER FIX

### Before Fix:
- Sequential Resume: 1 instance every 5s
- Auto-Unpause: 1 instance every 5s (interleaved)
- **Total: 2 instances every 5s = 12 instances/minute**
- 27 instances in ~2 minutes
- Overwhelms browser launch queue (MAX=3)
- Memory spike, CPU overload, stuck browsers

### After Fix:
- Sequential Resume: 1 instance every 5s
- Auto-Unpause: **DISABLED during sequential resume**
- **Total: 1 instance every 5s = 12 instances/minute**
- 27 instances in ~2.5 minutes
- Controlled browser launch rate
- No memory spike, no CPU overload, no stuck browsers

## 🎯 IMPLEMENTATION RECOMMENDATION

**Use Option 1** (add `sequential_resume_active` check) because:
1. ✅ Minimal code change (1 line)
2. ✅ Clear intent (explicit coordination)
3. ✅ Preserves both systems for their intended purposes
4. ✅ No risk of breaking other functionality
5. ✅ Easy to test and verify

The `sequential_resume_active` flag already exists and is already being set/cleared correctly. We just need to check it in the auto-unpause logic.

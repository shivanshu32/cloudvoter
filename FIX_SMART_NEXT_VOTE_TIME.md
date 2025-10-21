# Smart Next Vote Time - Use Later of Global or Individual Time

## 🎯 **Enhancement**

Instances now intelligently compare their individual next vote time with the global hourly limit resume time and display whichever is **later**.

**Logic:** An instance can't vote until **BOTH** conditions are met:
1. Global hourly limit has expired (if active)
2. Individual 31-minute cooldown has expired

Therefore, display the **later** of the two times.

---

## 📊 **Scenarios**

### **Scenario 1: Individual Cooldown BEFORE Global Limit**

**Example:**
- Instance #1 last voted at: **4:25 AM**
- Individual next vote: **4:56 AM** (4:25 + 31 min)
- Global limit expires: **5:00 AM**

**Logic:**
```
Individual: 4:56 AM
Global:     5:00 AM
           ↓
Use LATER: 5:00 AM ✅
```

**Display:**
```
Instance #1 ⏸️ Paused - Hourly Limit
⏳ Next vote 5:00 (global limit)
```

**Reason:** Even though individual cooldown expires at 4:56, instance can't vote until global limit expires at 5:00.

---

### **Scenario 2: Individual Cooldown AFTER Global Limit**

**Example:**
- Instance #6 last voted at: **4:46 AM**
- Individual next vote: **5:17 AM** (4:46 + 31 min)
- Global limit expires: **5:00 AM**

**Logic:**
```
Individual: 5:17 AM
Global:     5:00 AM
           ↓
Use LATER: 5:17 AM ✅
```

**Display:**
```
Instance #6 ⏸️ Paused - Hourly Limit
⏳ Next vote 5:17 (individual cooldown)
```

**Reason:** Even though global limit expires at 5:00, instance must wait until 5:17 for its individual cooldown.

---

### **Scenario 3: No Last Vote (New Instance)**

**Example:**
- Instance #3 has never voted
- Individual next vote: **N/A** (no last vote)
- Global limit expires: **5:00 AM**

**Logic:**
```
Individual: 0 seconds (no cooldown)
Global:     5:00 AM
           ↓
Use LATER: 5:00 AM ✅
```

**Display:**
```
Instance #3 ⏸️ Paused - Hourly Limit
⏳ Next vote 5:00 (global limit)
```

**Reason:** No individual cooldown, so only global limit applies.

---

## 💻 **Implementation**

### **Code Logic (Lines 136-172):**

```python
# PRIORITY: Check if global hourly limit is active
if self.voter_manager and self.voter_manager.global_hourly_limit:
    if self.voter_manager.global_reactivation_time:
        # Calculate global limit time
        reactivation_dt = datetime.fromisoformat(self.voter_manager.global_reactivation_time)
        global_time_diff = (reactivation_dt - current_time).total_seconds()
        global_seconds = max(0, int(global_time_diff))
        
        # Calculate individual next vote time (31 min after last vote)
        individual_seconds = 0
        individual_next_time = None
        
        if self.last_vote_time:
            individual_next_time = self.last_vote_time + timedelta(minutes=31)
            individual_time_diff = (individual_next_time - current_time).total_seconds()
            individual_seconds = max(0, int(individual_time_diff))
        
        # Use whichever is LATER (can't vote until both conditions met)
        if individual_seconds > global_seconds:
            # Individual cooldown is longer - use that
            return {
                'seconds_remaining': individual_seconds,
                'next_vote_time': individual_next_time.isoformat(),
                'status': 'cooldown',
                'retry_type': 'individual_cooldown_during_global_limit'
            }
        else:
            # Global limit is longer or equal - use that
            return {
                'seconds_remaining': global_seconds,
                'next_vote_time': self.voter_manager.global_reactivation_time,
                'status': 'global_hourly_limit',
                'retry_type': 'global_limit'
            }
```

---

## 🎨 **UI Display Examples**

### **Example 1: Most Instances Show Global Time**

**Current Time: 4:30 AM**
**Global Limit Expires: 5:00 AM**

```
┌────────────────────────────────────────┐
│ Instance #1 ⏸️ Paused - Hourly Limit   │
│ Last voted: 4:25 AM                   │
│ Individual: 4:56 AM (4:25 + 31)       │
│ Global: 5:00 AM                       │
│ ⏳ Next vote 5:00 (30:00)              │ ← Shows GLOBAL (later)
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│ Instance #9 ⏸️ Paused - Hourly Limit   │
│ Last voted: 4:20 AM                   │
│ Individual: 4:51 AM (4:20 + 31)       │
│ Global: 5:00 AM                       │
│ ⏳ Next vote 5:00 (30:00)              │ ← Shows GLOBAL (later)
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│ Instance #10 ⏸️ Paused - Hourly Limit  │
│ Last voted: 4:28 AM                   │
│ Individual: 4:59 AM (4:28 + 31)       │
│ Global: 5:00 AM                       │
│ ⏳ Next vote 5:00 (30:00)              │ ← Shows GLOBAL (later)
└────────────────────────────────────────┘
```

### **Example 2: Some Instances Show Individual Time**

**Current Time: 4:30 AM**
**Global Limit Expires: 5:00 AM**

```
┌────────────────────────────────────────┐
│ Instance #6 ⏸️ Paused - Hourly Limit   │
│ Last voted: 4:46 AM                   │
│ Individual: 5:17 AM (4:46 + 31)       │
│ Global: 5:00 AM                       │
│ ⏳ Next vote 5:17 (47:00)              │ ← Shows INDIVIDUAL (later)
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│ Instance #18 ⏸️ Paused - Hourly Limit  │
│ Last voted: 4:42 AM                   │
│ Individual: 5:13 AM (4:42 + 31)       │
│ Global: 5:00 AM                       │
│ ⏳ Next vote 5:13 (43:00)              │ ← Shows INDIVIDUAL (later)
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│ Instance #12 ⏸️ Paused - Hourly Limit  │
│ Last voted: 4:35 AM                   │
│ Individual: 5:06 AM (4:35 + 31)       │
│ Global: 5:00 AM                       │
│ ⏳ Next vote 5:06 (36:00)              │ ← Shows INDIVIDUAL (later)
└────────────────────────────────────────┘
```

---

## 📈 **Timeline Visualization**

### **Timeline: Global Limit at 4:30 AM, Expires at 5:00 AM**

```
4:20 AM ─┬─ Instance #9 votes
         │
4:25 AM ─┼─ Instance #1 votes
         │
4:28 AM ─┼─ Instance #10 votes
         │
4:30 AM ─┼─ 🚫 GLOBAL HOURLY LIMIT DETECTED
         │   All instances paused
         │
4:35 AM ─┼─ Instance #12 would be ready (4:35 + 31 = 5:06)
         │
4:42 AM ─┼─ Instance #18 would be ready (4:42 + 31 = 5:13)
         │
4:46 AM ─┼─ Instance #6 would be ready (4:46 + 31 = 5:17)
         │
4:51 AM ─┼─ Instance #9 individual cooldown expires
         │   But global limit still active → waits
         │
4:56 AM ─┼─ Instance #1 individual cooldown expires
         │   But global limit still active → waits
         │
4:59 AM ─┼─ Instance #10 individual cooldown expires
         │   But global limit still active → waits
         │
5:00 AM ─┼─ ✅ GLOBAL LIMIT EXPIRES
         │   Instances #1, #9, #10 can vote (individual cooldown already done)
         │   Instances #12, #18, #6 still waiting (individual cooldown not done)
         │
5:06 AM ─┼─ ✅ Instance #12 can vote (individual cooldown done)
         │
5:13 AM ─┼─ ✅ Instance #18 can vote (individual cooldown done)
         │
5:17 AM ─┴─ ✅ Instance #6 can vote (individual cooldown done)
```

---

## 🔄 **Comparison: Before vs After**

### **Before (Incorrect - All Show Global Time):**

```
Instance #1  ⏳ Next vote 5:00 (voted 4:25, ready 4:56)
Instance #6  ⏳ Next vote 5:00 (voted 4:46, ready 5:17) ❌ WRONG!
Instance #9  ⏳ Next vote 5:00 (voted 4:20, ready 4:51)
Instance #12 ⏳ Next vote 5:00 (voted 4:35, ready 5:06) ❌ WRONG!
Instance #18 ⏳ Next vote 5:00 (voted 4:42, ready 5:13) ❌ WRONG!
```

**Problem:** Instances #6, #12, #18 show 5:00 but actually can't vote until later due to individual cooldown.

### **After (Correct - Show Later Time):**

```
Instance #1  ⏳ Next vote 5:00 (voted 4:25, ready 4:56 < 5:00) ✅
Instance #6  ⏳ Next vote 5:17 (voted 4:46, ready 5:17 > 5:00) ✅
Instance #9  ⏳ Next vote 5:00 (voted 4:20, ready 4:51 < 5:00) ✅
Instance #12 ⏳ Next vote 5:06 (voted 4:35, ready 5:06 > 5:00) ✅
Instance #18 ⏳ Next vote 5:13 (voted 4:42, ready 5:13 > 5:00) ✅
```

**Fixed:** Each instance shows accurate time when it can actually vote.

---

## 🎯 **Benefits**

### **1. Accurate Time Display**
- ✅ Shows when instance can **actually** vote
- ✅ Accounts for both global and individual constraints
- ✅ No confusion about why instance doesn't vote at 5:00

### **2. Better User Understanding**
- ✅ Clear why some instances resume at 5:00
- ✅ Clear why some instances resume later
- ✅ Transparent about individual cooldowns

### **3. Realistic Expectations**
- ✅ Users know exact resume time for each instance
- ✅ No surprise delays after global limit expires
- ✅ Better planning and monitoring

---

## 📝 **Logic Summary**

### **Decision Tree:**

```
Is global hourly limit active?
├─ NO → Use normal calculation (individual cooldown or retry)
└─ YES → Compare times:
    ├─ Individual cooldown > Global limit?
    │   └─ YES → Show individual time (later)
    └─ NO → Show global time (later or equal)
```

### **Formula:**

```python
next_vote_time = max(
    global_reactivation_time,
    last_vote_time + 31 minutes
)
```

---

## ✅ **Testing Scenarios**

### **Test 1: Instance Voted Recently (Before Limit)**

```
Last vote: 4:25 AM
Individual: 4:56 AM
Global: 5:00 AM
Expected: 5:00 AM ✅
```

### **Test 2: Instance Voted Long Ago (Before Limit)**

```
Last vote: 4:10 AM
Individual: 4:41 AM
Global: 5:00 AM
Expected: 5:00 AM ✅
```

### **Test 3: Instance Voted During Limit**

```
Last vote: 4:50 AM (during limit)
Individual: 5:21 AM
Global: 5:00 AM
Expected: 5:21 AM ✅
```

### **Test 4: Instance Never Voted**

```
Last vote: Never
Individual: N/A (0 seconds)
Global: 5:00 AM
Expected: 5:00 AM ✅
```

---

## 🚀 **Deployment**

**To apply this enhancement:**

1. Restart the script to load updated `voter_engine.py`
2. Wait for next global hourly limit detection
3. Verify instances show correct times:
   - Instances that voted early → Show 5:00 (global)
   - Instances that voted late → Show their individual time
4. Verify instances resume at displayed times

**Expected behavior:**
```
[05:00:00] Global limit expires
[05:00:05] Instance #1 resumes (showed 5:00)
[05:00:10] Instance #9 resumes (showed 5:00)
[05:06:00] Instance #12 resumes (showed 5:06)
[05:13:00] Instance #18 resumes (showed 5:13)
[05:17:00] Instance #6 resumes (showed 5:17)
```

---

## 📊 **Summary**

**Enhancement:** Smart next vote time calculation during global hourly limit

**Logic:** Use **later** of global reactivation time or individual cooldown time

**Reason:** Instance can't vote until **both** conditions are met

**Result:**
- ✅ Accurate time display for each instance
- ✅ Some instances show global time (5:00)
- ✅ Some instances show individual time (5:06, 5:13, 5:17, etc.)
- ✅ Clear understanding of when each instance will resume
- ✅ No confusion about delayed resumes

**All instances now show realistic, accurate next vote times!** 🎉

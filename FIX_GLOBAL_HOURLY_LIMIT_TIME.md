# Fix: Global Hourly Limit - Unified Next Vote Time

## 🐛 **Issue**

After global hourly limit was detected, instances showed **different** "Next vote" times:

```
Instance #1  ⏳ Next vote 5:04
Instance #3  ✅ Ready to vote
Instance #6  ⏳ Next vote 16:58
Instance #9  ⏳ Next vote 0:22
Instance #10 ⏳ Next vote 1:35
Instance #12 ⏳ Next vote 11:31
...
```

**Problem:** Each instance calculated "Next vote" based on their individual `last_vote_time + 31 minutes`, but during a **global hourly limit**, ALL instances should resume at the **same time** (next full hour).

---

## 🔍 **Root Cause**

### **How It Should Work:**

When global hourly limit is detected:
1. `MultiInstanceVoter.handle_hourly_limit()` sets `global_reactivation_time` (next full hour)
2. ALL instances should show this same time
3. ALL instances resume together

### **What Was Happening:**

`get_time_until_next_vote()` method calculated time based on:
- Individual instance's `last_vote_time + 31 minutes`
- OR individual instance's `last_attempted_vote + retry_delay`

**It never checked for global hourly limit!**

**Result:** Each instance showed different "Next vote" time based on when they last voted, even though they would all actually resume at the same time.

---

## ✅ **Fix Implemented**

### **Modified `get_time_until_next_vote()` (Lines 136-152)**

**Added priority check for global hourly limit:**

```python
def get_time_until_next_vote(self) -> dict:
    """
    Calculate time remaining until next vote or retry.
    
    Handles:
    - Global hourly limit: All instances resume at same time ✅ NEW
    - Successful votes: 31 minute cooldown
    - Failed votes: 5 min (technical) or 31 min (IP cooldown) retry delay
    """
    current_time = datetime.now()
    
    # PRIORITY: Check if global hourly limit is active
    if self.voter_manager and self.voter_manager.global_hourly_limit:
        if self.voter_manager.global_reactivation_time:
            try:
                reactivation_dt = datetime.fromisoformat(self.voter_manager.global_reactivation_time)
                time_diff = (reactivation_dt - current_time).total_seconds()
                seconds_remaining = max(0, int(time_diff))
                
                return {
                    'seconds_remaining': seconds_remaining,
                    'next_vote_time': self.voter_manager.global_reactivation_time,
                    'status': 'global_hourly_limit' if seconds_remaining > 0 else 'ready',
                    'retry_type': 'global_limit'
                }
            except Exception as e:
                logger.debug(f"[TIME] Error parsing global reactivation time: {e}")
                # Fall through to normal calculation
    
    # Rest of the normal calculation logic...
```

### **Priority Order:**

1. **FIRST:** Check global hourly limit → Use `global_reactivation_time` ✅
2. **SECOND:** Check recent failure → Use retry delay
3. **THIRD:** Check successful vote → Use 31-minute cooldown
4. **FOURTH:** No history → Ready to vote

---

## 📊 **Before vs After**

### **Before (Incorrect - Different Times):**

```
Instance #1  ⏳ Next vote 5:04   (based on last vote at 4:33)
Instance #6  ⏳ Next vote 16:58  (based on last vote at 4:46)
Instance #9  ⏳ Next vote 0:22   (based on last vote at 4:30)
Instance #10 ⏳ Next vote 1:35   (based on last vote at 4:31)
Instance #12 ⏳ Next vote 11:31  (based on last vote at 4:41)
```

**Issues:**
- ❌ Each instance shows different time
- ❌ Times based on individual last votes
- ❌ Confusing - they'll all resume together anyway
- ❌ Some show "Ready to vote" even though paused

### **After (Correct - Same Time):**

```
Instance #1  ⏳ Next vote 5:00   (global reactivation time)
Instance #6  ⏳ Next vote 5:00   (global reactivation time)
Instance #9  ⏳ Next vote 5:00   (global reactivation time)
Instance #10 ⏳ Next vote 5:00   (global reactivation time)
Instance #12 ⏳ Next vote 5:00   (global reactivation time)
```

**Fixed:**
- ✅ ALL instances show same time
- ✅ Time is next full hour (5:00 AM)
- ✅ Clear indication they'll resume together
- ✅ Accurate countdown

---

## 🎯 **How It Works**

### **Scenario: Global Hourly Limit Detected at 4:30 AM**

**Step 1: Detection**
```
[04:30:15] Instance #3 detects global hourly limit
[04:30:15] MultiInstanceVoter.handle_hourly_limit() called
[04:30:15] global_reactivation_time set to "2025-10-21T05:00:00"
[04:30:15] All instances paused
```

**Step 2: Time Calculation**
```
Instance #1 calls get_time_until_next_vote():
  ✅ Check: global_hourly_limit = True
  ✅ Use: global_reactivation_time = "2025-10-21T05:00:00"
  ✅ Calculate: 5:00 AM - 4:30 AM = 30 minutes
  ✅ Return: seconds_remaining = 1800, next_vote_time = "5:00 AM"

Instance #6 calls get_time_until_next_vote():
  ✅ Check: global_hourly_limit = True
  ✅ Use: global_reactivation_time = "2025-10-21T05:00:00"
  ✅ Calculate: 5:00 AM - 4:30 AM = 30 minutes
  ✅ Return: seconds_remaining = 1800, next_vote_time = "5:00 AM"

... (ALL instances return same time)
```

**Step 3: UI Display**
```
ALL instances show: ⏳ Next vote 5:00
Countdown updates every second: 29:59, 29:58, 29:57...
```

**Step 4: Resume**
```
[05:00:00] Hourly limit expires
[05:00:00] All instances resume SEQUENTIALLY
[05:00:05] Instance #1 resumes
[05:00:10] Instance #6 resumes
[05:00:15] Instance #9 resumes
... (5-second delay between each)
```

---

## 🎨 **UI Display**

### **During Global Hourly Limit:**

```
┌────────────────────────────────────────┐
│ Instance #1 ⏸️ Paused - Hourly Limit   │
│ IP: 43.225.188.139                    │
│ Votes: 1                              │
│ ⏸️ Paused                              │
│ ⏳ Next vote 5:00 (29:45 remaining)    │
│ ✅ Last Success: 25 min ago            │
│ 🎯 Last Attempt: 25 min ago            │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│ Instance #6 ⏸️ Paused - Hourly Limit   │
│ IP: 119.13.239.221                    │
│ Votes: 1                              │
│ ⏸️ Paused                              │
│ ⏳ Next vote 5:00 (29:45 remaining)    │ ← SAME TIME!
│ ✅ Last Success: 14 min ago            │
│ 🎯 Last Attempt: 14 min ago            │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│ Instance #9 ⏸️ Paused - Hourly Limit   │
│ IP: 43.225.188.171                    │
│ Votes: 1                              │
│ ⏸️ Paused                              │
│ ⏳ Next vote 5:00 (29:45 remaining)    │ ← SAME TIME!
│ ✅ Last Success: 30 min ago            │
│ 🎯 Last Attempt: 30 min ago            │
└────────────────────────────────────────┘
```

**All instances show:**
- ✅ Same "Next vote" time (5:00)
- ✅ Same countdown (29:45)
- ✅ Clear indication of global pause

### **After Global Hourly Limit Expires:**

```
┌────────────────────────────────────────┐
│ Instance #1 ▶️ Resumed - Ready to Vote │
│ IP: 43.225.188.139                    │
│ Votes: 1                              │
│ ✅ Ready to vote                       │
│ ⏱️ 0:00 until next vote                │
│ ✅ Last Success: 55 min ago            │
│ 🎯 Last Attempt: 55 min ago            │
└────────────────────────────────────────┘
```

---

## 🔄 **Comparison: Different Scenarios**

### **1. Global Hourly Limit (ALL instances same time)**
```
Status: "⏸️ Paused - Hourly Limit"
Next Vote: "5:00" (global_reactivation_time)
Countdown: Same for ALL instances
Resume: ALL at once (sequentially)
```

### **2. Instance-Specific Cooldown (Individual times)**
```
Status: "⏳ Cooldown (31 min)"
Next Vote: Individual (last_vote_time + 31 min)
Countdown: Different for each instance
Resume: Each individually when cooldown expires
```

### **3. Technical Failure (Individual retry)**
```
Status: "🔄 Retry in 5 min"
Next Vote: Individual (last_attempted_vote + 5 min)
Countdown: Different for each instance
Resume: Each individually when retry time reached
```

---

## ✅ **Testing Checklist**

After deploying this fix, verify:

- [ ] **Global hourly limit**: ALL instances show same "Next vote" time
- [ ] **Time displayed**: Shows next full hour (e.g., 5:00 AM)
- [ ] **Countdown**: All instances countdown together
- [ ] **Resume**: All instances resume at displayed time
- [ ] **Instance cooldown**: Individual instances show their own times
- [ ] **Technical failure**: Individual instances show their own retry times

---

## 🚀 **Deployment**

**To apply this fix:**

1. Restart the script to load updated `voter_engine.py`
2. Wait for next global hourly limit detection
3. Verify ALL instances show same "Next vote" time
4. Verify countdown is synchronized across all instances
5. Verify all instances resume at the displayed time

**Expected logs:**
```
[HOURLY_LIMIT] 🚫 HOURLY LIMIT DETECTED - Pausing ALL instances
[HOURLY_LIMIT] Will resume at 05:00 AM
[HOURLY_LIMIT] Paused 18 instances
[TIME] All instances will show: Next vote 5:00
```

---

## 📊 **Summary**

**Issue:** Instances showed different "Next vote" times during global hourly limit

**Root Cause:** `get_time_until_next_vote()` didn't check for global hourly limit

**Fix:** Added priority check for `global_hourly_limit` and use `global_reactivation_time`

**Result:**
- ✅ ALL instances show same "Next vote" time during global limit
- ✅ Time is next full hour (accurate)
- ✅ Countdown synchronized across all instances
- ✅ Clear indication of when ALL instances will resume
- ✅ Individual cooldowns still work correctly

**All instances now show accurate, synchronized resume time during global hourly limit!** 🎉

# Countdown Timer Feature

## Overview
Added a real-time countdown timer to the Active Instances section that shows the remaining time until each instance's next vote. The timer updates every second, providing clear visual feedback on when each instance will vote next.

## Problem Solved

**Before:**
- Status showed "⏳ Cooldown" or "✅ Vote Successful" without any time information
- Users didn't know when the next vote would happen
- "Cooldown" was unclear - users didn't understand what it meant

**After:**
- Clear countdown timer showing "⏱️ MM:SS" format
- Updates every second in real-time
- Shows "Ready to vote" when countdown reaches 0
- Color-coded: Blue (waiting), Green (ready)

## Changes Made

### 1. Backend - VoterInstance Class (`backend/voter_engine.py`)

**Added `get_time_until_next_vote()` method:**
```python
def get_time_until_next_vote(self) -> dict:
    """
    Calculate time remaining until next vote.
    Returns dict with seconds_remaining and next_vote_time.
    """
    if not self.last_vote_time:
        return {
            'seconds_remaining': 0,
            'next_vote_time': None,
            'status': 'ready'
        }
    
    # Calculate next vote time (31 minutes after last vote)
    next_vote_time = self.last_vote_time + timedelta(minutes=31)
    current_time = datetime.now()
    
    # Calculate seconds remaining
    time_diff = (next_vote_time - current_time).total_seconds()
    seconds_remaining = max(0, int(time_diff))
    
    return {
        'seconds_remaining': seconds_remaining,
        'next_vote_time': next_vote_time.isoformat(),
        'status': 'cooldown' if seconds_remaining > 0 else 'ready'
    }
```

**Key Features:**
- Calculates time remaining based on 31-minute voting cycle
- Returns 0 if no previous vote (ready to vote)
- Returns ISO format timestamp for next vote time
- Returns status: 'ready' or 'cooldown'

### 2. Backend - API Endpoint (`backend/app.py`)

**Updated `/api/instances` endpoint:**
```python
# Get time until next vote
time_info = instance.get_time_until_next_vote() if hasattr(instance, 'get_time_until_next_vote') else {
    'seconds_remaining': 0,
    'next_vote_time': None,
    'status': 'unknown'
}

instances.append({
    'instance_id': instance_id,
    'ip': ip,
    'status': getattr(instance, 'status', 'Unknown'),
    'vote_count': getattr(instance, 'vote_count', 0),
    'seconds_remaining': time_info['seconds_remaining'],  # NEW
    'next_vote_time': time_info['next_vote_time'],        # NEW
    'last_vote_time': ...                                  # NEW
})
```

**Updated Socket.IO emission:**
- Added same timing fields to `instances_update` event
- Real-time updates pushed to frontend every 10 seconds

### 3. Frontend - Display (`backend/templates/index.html`)

**Added countdown formatting function:**
```javascript
function formatCountdown(seconds) {
    if (seconds <= 0) return 'Ready to vote';
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `⏱️ ${minutes}:${secs.toString().padStart(2, '0')}`;
}
```

**Updated instance card HTML:**
```html
<div class="font-semibold ${secondsRemaining > 0 ? 'text-blue-600' : 'text-green-600'}" 
     data-countdown="${instanceId}">
    ${countdownText}
</div>
```

**Added countdown update function:**
```javascript
function updateCountdowns() {
    const instanceCards = document.querySelectorAll('[data-instance-id]');
    instanceCards.forEach(card => {
        let seconds = parseInt(card.getAttribute('data-seconds') || '0');
        
        if (seconds > 0) {
            seconds--;
            card.setAttribute('data-seconds', seconds);
            countdownElement.textContent = formatCountdown(seconds);
            
            // Update color: blue (waiting) or green (ready)
            if (seconds > 0) {
                countdownElement.className = 'font-semibold text-blue-600';
            } else {
                countdownElement.className = 'font-semibold text-green-600';
            }
        }
    });
}

// Update every second
setInterval(updateCountdowns, 1000);
```

## How It Works

### Data Flow

```
1. Instance votes successfully
   ↓
2. self.last_vote_time = datetime.now()
   ↓
3. get_time_until_next_vote() calculates:
   - next_vote_time = last_vote_time + 31 minutes
   - seconds_remaining = (next_vote_time - now).seconds
   ↓
4. API/Socket.IO sends to frontend:
   {
     instance_id: 1,
     seconds_remaining: 1860,  // 31 minutes
     next_vote_time: "2025-10-20T16:45:00"
   }
   ↓
5. Frontend displays: "⏱️ 31:00"
   ↓
6. JavaScript decrements every second:
   "⏱️ 30:59" → "⏱️ 30:58" → ... → "Ready to vote"
```

### Update Mechanisms

**Three-tier update system:**

1. **Socket.IO (every 10s)**: 
   - Backend pushes fresh countdown data
   - Resyncs if client-side countdown drifts

2. **Polling (every 5s)**:
   - Fallback if Socket.IO disconnects
   - Fetches fresh data from API

3. **Client-side countdown (every 1s)**:
   - Smooth countdown animation
   - No network requests needed
   - Resynced by Socket.IO/polling

## Visual Examples

### Instance Card Display

**Waiting to vote (31 minutes remaining):**
```
┌─────────────────────────────────────┐
│ Instance #1        ✅ Vote Successful│
│ IP: 1.2.3.4                         │
│ Votes: 5                            │
│ ⏱️ 31:00                            │ ← Blue color
└─────────────────────────────────────┘
```

**Almost ready (30 seconds remaining):**
```
┌─────────────────────────────────────┐
│ Instance #2        ⏳ Cooldown       │
│ IP: 5.6.7.8                         │
│ Votes: 3                            │
│ ⏱️ 0:30                             │ ← Blue color
└─────────────────────────────────────┘
```

**Ready to vote:**
```
┌─────────────────────────────────────┐
│ Instance #3        ▶️ Resumed        │
│ IP: 9.10.11.12                      │
│ Votes: 8                            │
│ Ready to vote                       │ ← Green color
└─────────────────────────────────────┘
```

## Color Coding

| State | Color | Meaning |
|-------|-------|---------|
| `⏱️ MM:SS` (blue) | Blue | Waiting for cooldown to expire |
| `Ready to vote` (green) | Green | Cooldown expired, ready to vote |

## Benefits

### 1. **Clear Communication**
- No more confusion about "Cooldown" status
- Users know exactly when next vote happens
- Real-time feedback builds confidence

### 2. **Better Monitoring**
- See which instances are about to vote
- Identify stuck instances (countdown not moving)
- Plan actions based on timing

### 3. **Professional UI**
- Smooth countdown animation
- Color-coded status
- Consistent with modern web apps

### 4. **Performance**
- Client-side countdown (no constant API calls)
- Periodic resyncing prevents drift
- Minimal network overhead

## Technical Details

### Voting Cycle Timing

**31-minute cycle:**
```
Vote cast at 16:00:00
  ↓
Wait 31 minutes
  ↓
Next vote at 16:31:00
```

### Countdown Calculation

```python
# Backend calculation
last_vote_time = datetime(2025, 10, 20, 16, 0, 0)
next_vote_time = last_vote_time + timedelta(minutes=31)  # 16:31:00
current_time = datetime(2025, 10, 20, 16, 15, 30)        # Now
seconds_remaining = (next_vote_time - current_time).total_seconds()  # 930 seconds = 15:30
```

```javascript
// Frontend display
formatCountdown(930)  // Returns: "⏱️ 15:30"
formatCountdown(65)   // Returns: "⏱️ 1:05"
formatCountdown(5)    // Returns: "⏱️ 0:05"
formatCountdown(0)    // Returns: "Ready to vote"
```

### Data Attributes

Each instance card has:
```html
<div data-instance-id="1" data-seconds="1860">
  <div data-countdown="1">⏱️ 31:00</div>
</div>
```

- `data-instance-id`: Unique identifier
- `data-seconds`: Current countdown value
- `data-countdown`: Target element for updates

## Testing

### Verify Countdown Works

1. **Start monitoring** and launch instances
2. **Wait for a vote** to complete
3. **Check instance card** - should show "⏱️ 31:00"
4. **Watch countdown** - should decrement every second
5. **Wait until 0** - should show "Ready to vote" in green

### Test Resync

1. **Open browser console** (F12)
2. **Manually change** `data-seconds` attribute:
   ```javascript
   document.querySelector('[data-instance-id="1"]').setAttribute('data-seconds', '999999');
   ```
3. **Wait 5-10 seconds** - Socket.IO/polling should resync to correct value

### Test Multiple Instances

1. **Launch 5+ instances**
2. **Verify each** shows its own countdown
3. **Check they're independent** - different times based on when each voted

## Troubleshooting

### Countdown not showing

**Check:**
1. Instance has voted at least once (`last_vote_time` is set)
2. Backend is sending `seconds_remaining` field
3. Browser console for errors

**Debug:**
```javascript
// Check instance data
fetch('/api/instances')
  .then(r => r.json())
  .then(d => console.log(d.instances[0]));

// Should show: { seconds_remaining: 1860, next_vote_time: "..." }
```

### Countdown not updating

**Check:**
1. `setInterval(updateCountdowns, 1000)` is running
2. No JavaScript errors in console
3. Instance cards have `data-seconds` attribute

**Fix:**
- Refresh page
- Check browser console for errors

### Countdown drifts over time

**Normal behavior:**
- Client-side countdown may drift slightly
- Resynced every 5-10 seconds by Socket.IO/polling
- Drift should never exceed 10 seconds

### Shows "Ready to vote" but not voting

**Possible causes:**
1. Instance is paused
2. Hourly limit active
3. Login required
4. Browser closed

**Check status badge** for more info

## Future Enhancements

Possible improvements:
- [ ] Show hours for longer cooldowns
- [ ] Progress bar visualization
- [ ] Sound notification when ready
- [ ] Estimated next vote time tooltip
- [ ] Countdown for paused instances (until resume)
- [ ] Different colors for different time ranges

## Files Modified

1. **backend/voter_engine.py**
   - Added `get_time_until_next_vote()` method

2. **backend/app.py**
   - Updated `/api/instances` endpoint
   - Updated Socket.IO `instances_update` emission

3. **backend/templates/index.html**
   - Added `formatCountdown()` function
   - Updated `renderInstances()` to show countdown
   - Added `updateCountdowns()` function
   - Added countdown interval timer

## Summary

The countdown timer feature provides clear, real-time feedback on when each instance will vote next. It replaces the ambiguous "Cooldown" status with an actual countdown timer that updates every second, making the UI more informative and professional.

**Key Features:**
- ⏱️ Real-time countdown (MM:SS format)
- 🔵 Blue color while waiting
- 🟢 Green "Ready to vote" when done
- 🔄 Auto-syncs every 5-10 seconds
- 📊 Per-instance tracking

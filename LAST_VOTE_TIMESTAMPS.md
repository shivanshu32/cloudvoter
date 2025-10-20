# Last Vote Timestamps Feature

## Overview
Added "Last Success" and "Last Attempt" timestamps to the Active Instances display, matching the format used in the Saved Sessions view. This provides better visibility into each instance's voting history.

## Problem Solved

**Before:**
- Active instances only showed current status and vote count
- No visibility into when last successful vote occurred
- No way to see when last attempt was made (success or failure)
- Had to check saved sessions to see this information

**After:**
- Each active instance card shows:
  - ✅ **Last Success**: When the last successful vote occurred
  - 🎯 **Last Attempt**: When the last vote attempt was made (success or failure)
- Formatted as relative time: "5 min ago", "2 hours ago", "3 days ago"
- Consistent with saved sessions display

## Changes Made

### 1. Backend - VoterInstance Class (`backend/voter_engine.py`)

**Added timestamp tracking:**
```python
# Voting state
self.last_vote_time = None
self.last_successful_vote = None  # Timestamp of last successful vote
self.last_attempted_vote = None   # Timestamp of last vote attempt (success or fail)
self.vote_count = 0
self.failed_attempts = 0
```

**Updated successful vote tracking:**
```python
if count_increase == 1:
    # VERIFIED SUCCESS - Count increased by exactly 1
    current_time = datetime.now()
    self.last_vote_time = current_time
    self.last_successful_vote = current_time  # Track last successful vote
    self.last_attempted_vote = current_time   # Track last attempt
    self.vote_count += 1
```

**Updated failed vote tracking:**
```python
if any(pattern in page_content.lower() for pattern in ['hourly limit', 'already voted', 'cooldown']):
    # Track last attempt (failed)
    self.last_attempted_vote = datetime.now()
```

### 2. Backend - API Endpoints (`backend/app.py`)

**Updated `/api/instances` endpoint:**
```python
instances.append({
    'instance_id': instance_id,
    'ip': ip,
    'status': getattr(instance, 'status', 'Unknown'),
    'vote_count': getattr(instance, 'vote_count', 0),
    'seconds_remaining': time_info['seconds_remaining'],
    'next_vote_time': time_info['next_vote_time'],
    'last_vote_time': ...,
    'last_successful_vote': getattr(instance, 'last_successful_vote', None).isoformat() if ... else None,  # NEW
    'last_attempted_vote': getattr(instance, 'last_attempted_vote', None).isoformat() if ... else None     # NEW
})
```

**Updated Socket.IO emission:**
- Added same fields to `instances_update` event
- Real-time updates pushed to frontend

### 3. Frontend - Display (`backend/templates/index.html`)

**Added timestamp display to instance cards:**
```html
<div class="grid grid-cols-2 gap-2 text-xs text-gray-500 mt-2 pt-2 border-t border-gray-200">
    <div>✅ Last Success: ${formatLastVote(instance.last_successful_vote)}</div>
    <div>🎯 Last Attempt: ${formatLastVote(instance.last_attempted_vote)}</div>
</div>
```

**Uses existing `formatLastVote()` function:**
```javascript
function formatLastVote(lastVote) {
    if (!lastVote || lastVote === 'Never') return 'Never';
    try {
        const date = new Date(lastVote);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        
        if (diffMins < 60) return `${diffMins} min ago`;
        if (diffHours < 24) return `${diffHours} hours ago`;
        return `${Math.floor(diffHours / 24)} days ago`;
    } catch {
        return lastVote;
    }
}
```

## Visual Example

### Active Instance Card Display

```
┌─────────────────────────────────────────────┐
│ Instance #1        ✅ Vote Successful       │
│ IP: 1.2.3.4                                 │
│ Votes: 5                                    │
│ ⏱️ 25:30                                    │
│ ─────────────────────────────────────────── │
│ ✅ Last Success: 5 min ago                  │
│ 🎯 Last Attempt: 5 min ago                  │
└─────────────────────────────────────────────┘
```

**After failed attempt (hourly limit):**
```
┌─────────────────────────────────────────────┐
│ Instance #2        ⏳ Cooldown              │
│ IP: 5.6.7.8                                 │
│ Votes: 3                                    │
│ ⏱️ 30:45                                    │
│ ─────────────────────────────────────────── │
│ ✅ Last Success: 35 min ago                 │
│ 🎯 Last Attempt: 2 min ago                  │
└─────────────────────────────────────────────┘
```

**New instance (never voted):**
```
┌─────────────────────────────────────────────┐
│ Instance #3        ▶️ Resumed               │
│ IP: 9.10.11.12                              │
│ Votes: 0                                    │
│ Ready to vote                               │
│ ─────────────────────────────────────────── │
│ ✅ Last Success: Never                      │
│ 🎯 Last Attempt: Never                      │
└─────────────────────────────────────────────┘
```

## Timestamp Tracking

### Success Scenario
```
1. Vote cast at 16:00:00
   ↓
2. Vote verified successful
   ↓
3. Set timestamps:
   - last_vote_time = 16:00:00
   - last_successful_vote = 16:00:00
   - last_attempted_vote = 16:00:00
```

### Failure Scenario (Hourly Limit)
```
1. Vote cast at 16:05:00
   ↓
2. Hourly limit detected
   ↓
3. Set timestamps:
   - last_vote_time = (unchanged from last success)
   - last_successful_vote = (unchanged from last success)
   - last_attempted_vote = 16:05:00  ← Updated
```

### Result Display
```
✅ Last Success: 5 min ago    (16:00:00)
🎯 Last Attempt: 2 sec ago    (16:05:00)
```

## Benefits

### 1. **Better Monitoring**
- See when each instance last voted successfully
- Track failed attempts separately
- Identify instances that haven't voted in a while

### 2. **Troubleshooting**
- If "Last Attempt" is recent but "Last Success" is old → Instance hitting hourly limits
- If both are old → Instance might be stuck or paused
- If "Last Success" is "Never" → Instance hasn't voted yet

### 3. **Consistency**
- Matches saved sessions display format
- Familiar UI pattern
- Same relative time formatting

### 4. **Real-Time Updates**
- Updates via Socket.IO every 10 seconds
- Polling fallback every 5 seconds
- Always shows current information

## Use Cases

### Scenario 1: Successful Voting
```
Instance #1
✅ Last Success: 2 min ago
🎯 Last Attempt: 2 min ago
```
**Interpretation**: Instance is voting successfully, last attempt was successful.

### Scenario 2: Hitting Hourly Limits
```
Instance #2
✅ Last Success: 35 min ago
🎯 Last Attempt: 5 min ago
```
**Interpretation**: Instance tried to vote 5 min ago but hit hourly limit. Last successful vote was 35 min ago.

### Scenario 3: Stuck Instance
```
Instance #3
✅ Last Success: 2 hours ago
🎯 Last Attempt: 2 hours ago
```
**Interpretation**: Instance hasn't attempted to vote in 2 hours. May be stuck or paused.

### Scenario 4: New Instance
```
Instance #4
✅ Last Success: Never
🎯 Last Attempt: Never
```
**Interpretation**: Brand new instance that hasn't voted yet.

## Time Format

| Time Difference | Display Format |
|----------------|----------------|
| < 1 minute | "0 min ago" |
| 1-59 minutes | "X min ago" |
| 1-23 hours | "X hours ago" |
| 24+ hours | "X days ago" |
| No timestamp | "Never" |

## Technical Details

### Data Flow

```
Vote Attempt
    ↓
Success? ──Yes──> last_successful_vote = now
    │             last_attempted_vote = now
    │
    No
    ↓
Failure (hourly limit)
    ↓
last_attempted_vote = now
(last_successful_vote unchanged)
    ↓
API/Socket.IO sends to frontend
    ↓
formatLastVote() displays relative time
```

### Timestamp Format

**Backend (ISO 8601):**
```python
'last_successful_vote': '2025-10-20T16:00:00'
'last_attempted_vote': '2025-10-20T16:05:00'
```

**Frontend (Relative Time):**
```javascript
'✅ Last Success: 5 min ago'
'🎯 Last Attempt: 2 sec ago'
```

## Comparison with Saved Sessions

Both displays now show the same information:

**Saved Sessions:**
```
Instance #1
IP: 1.2.3.4
✅ Last Success: 5 min ago
🎯 Last Attempt: 5 min ago
📊 Total Votes: 5
```

**Active Instances:**
```
Instance #1        ✅ Vote Successful
IP: 1.2.3.4
Votes: 5
⏱️ 25:30
─────────────────────────────
✅ Last Success: 5 min ago
🎯 Last Attempt: 5 min ago
```

## Testing

### Verify Timestamps Display

1. **Start monitoring** and launch instances
2. **Wait for votes** to complete
3. **Check instance cards** - should show timestamps
4. **Verify format** - should show "X min ago"

### Test Success Tracking

1. **Wait for successful vote**
2. **Check both timestamps** - should be the same
3. **Format**: "✅ Last Success: 2 min ago" and "🎯 Last Attempt: 2 min ago"

### Test Failure Tracking

1. **Wait for hourly limit**
2. **Check timestamps** - should be different
3. **Last Success**: Older timestamp (last successful vote)
4. **Last Attempt**: Recent timestamp (failed attempt)

### Test New Instance

1. **Launch new instance**
2. **Before first vote** - should show "Never" for both
3. **After first vote** - should show timestamps

## Troubleshooting

### Timestamps show "Never"

**Possible causes:**
1. Instance hasn't voted yet
2. Instance was just launched
3. Timestamps not being set in backend

**Check:**
- Wait for instance to vote
- Check backend logs for vote attempts
- Verify `last_successful_vote` and `last_attempted_vote` are being set

### Timestamps not updating

**Possible causes:**
1. Socket.IO not connected
2. Polling not working
3. Backend not sending timestamps

**Check:**
- Connection status (should be green "Connected")
- Browser console for errors
- API response: `fetch('/api/instances').then(r => r.json()).then(console.log)`

### Wrong time format

**Expected format:**
- "X min ago" for < 60 minutes
- "X hours ago" for < 24 hours
- "X days ago" for 24+ hours

**If showing ISO timestamp:**
- `formatLastVote()` function may have error
- Check browser console for JavaScript errors

## Files Modified

1. **backend/voter_engine.py**
   - Added `last_successful_vote` and `last_attempted_vote` fields
   - Updated vote tracking to set these timestamps

2. **backend/app.py**
   - Updated `/api/instances` endpoint to include new fields
   - Updated Socket.IO emission to include new fields

3. **backend/templates/index.html**
   - Updated instance card HTML to display timestamps
   - Uses existing `formatLastVote()` function

## Future Enhancements

Possible improvements:
- [ ] Tooltip showing exact timestamp on hover
- [ ] Color coding based on time since last success
- [ ] Alert if instance hasn't voted in X hours
- [ ] Chart showing vote success rate over time
- [ ] Export vote history per instance

## Summary

The Last Vote Timestamps feature adds visibility into each instance's voting history directly in the Active Instances display. It shows when the last successful vote occurred and when the last attempt was made, helping you monitor instance health and troubleshoot issues.

**Key Features:**
- ✅ Last successful vote timestamp
- 🎯 Last vote attempt timestamp (success or failure)
- 🕐 Relative time format ("X min ago")
- 🔄 Real-time updates via Socket.IO
- 📊 Consistent with saved sessions display

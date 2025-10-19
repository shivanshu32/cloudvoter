# 🐛 Frontend Bug Fixed - instance.id vs instance.instance_id

## Issue

Active Instances showing "Instance #undefined"

## Root Cause

**Frontend JavaScript was using wrong field name!**

**Backend API returns:**
```json
{
  "instance_id": 11,
  "ip": "119.13.231.144",
  "status": "Paused - Hourly Limit",
  "vote_count": 1
}
```

**Frontend was accessing:**
```javascript
Instance #${instance.id}  // ❌ Wrong! This field doesn't exist
```

**Should be:**
```javascript
Instance #${instance.instance_id}  // ✅ Correct!
```

## Fix Applied

**File:** `backend/templates/index.html`

**Line 524:**

**Before:**
```javascript
<span>Instance #${instance.id}</span>  // ❌ undefined
```

**After:**
```javascript
<span>Instance #${instance.instance_id}</span>  // ✅ Works!
```

## Why This Happened

The API field name is `instance_id` (with underscore), but the frontend was trying to access `id` (without underscore).

This is a simple typo/mismatch between backend and frontend field names.

## Result

**Before fix:**
```
Instance #undefined⏸️ Paused - Hourly Limit
IP: 119.13.231.144
Votes: 1
```

**After fix:**
```
Instance #11⏸️ Paused - Hourly Limit
IP: 119.13.231.144
Votes: 1
```

## Test

**Just refresh the browser (F5)** - no backend restart needed!

The Active Instances section should now show correct instance IDs.

## Files Modified

- `backend/templates/index.html` - Changed `instance.id` to `instance.instance_id`

## Status

✅ **Fixed** - Frontend now correctly accesses `instance_id` field

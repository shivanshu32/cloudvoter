# 🐛 Instance Display Fix - "undefined" Issue

## Issue

**UI showing:**
```
Instance #undefined⏳ Cooldown
IP: 91.197.253.183
Votes: 0
```

## Root Cause

The `/api/instances` endpoint was iterating over `active_instances` dictionary incorrectly:

**Before:**
```python
for ip, instance in voter_system.active_instances.items():
    instances.append({
        'instance_id': getattr(instance, 'instance_id', 'Unknown'),  # ❌ Wrong!
        'ip': ip,  # This was the IP, not instance_id
        # ...
    })
```

**Problem:** The dictionary is keyed by `instance_id`, not `ip`!

## Fix Applied

**After:**
```python
for instance_id, instance in voter_system.active_instances.items():
    instances.append({
        'instance_id': instance_id,  # ✅ Correct!
        'ip': getattr(instance, 'proxy_ip', 'Unknown'),  # ✅ Get IP from instance
        'vote_count': getattr(instance, 'vote_count', 0),  # ✅ Added vote_count
        # ...
    })
```

## Changes

1. ✅ Fixed dictionary iteration (instance_id is the key, not IP)
2. ✅ Get IP from `instance.proxy_ip` attribute
3. ✅ Added `vote_count` field to response

## Result

**UI will now show:**
```
Instance #1⏳ Cooldown
IP: 91.197.253.183
Votes: 0

Instance #10⏳ Cooldown
IP: 119.13.229.244
Votes: 0
```

## Test

Refresh the browser - instance IDs should now display correctly!

**File Modified:** `backend/app.py`

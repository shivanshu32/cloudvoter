# Sequential Browser Launch Implementation

## Problem
When the hourly voting limit expires, all paused browser instances were resuming simultaneously, causing multiple browsers to open at once. This overwhelmed the limited memory resources on Digital Ocean, making the script unresponsive.

## Solution
Implemented a sequential browser launch mechanism that ensures browsers initialize one at a time with configurable delays between launches.

## Changes Made

### 1. Configuration (`backend/config.py`)
Added new configuration options:
```python
# Sequential browser launch configuration (prevents memory overload)
BROWSER_LAUNCH_DELAY = 5  # Seconds to wait between browser launches
MAX_CONCURRENT_BROWSER_LAUNCHES = 1  # Maximum number of browsers that can launch simultaneously
```

### 2. VoterManager Class (`backend/voter_engine.py`)
**Added sequential launch control:**
- `browser_launch_semaphore`: Asyncio semaphore limiting concurrent browser launches
- `browser_launch_delay`: Configurable delay between browser launches
- `sequential_resume_active`: Flag to track when sequential resume is in progress

**Modified `_check_hourly_limit_expiry()` method:**
- Changed from resuming all instances simultaneously to sequential resume
- Added delay between each instance resume
- Provides detailed logging of resume progress (e.g., "Resumed instance #3 (3/10)")

### 3. VoterInstance Class (`backend/voter_engine.py`)
**Modified browser initialization methods:**
- `initialize()`: Now acquires semaphore before launching browser
- `initialize_with_saved_session()`: Now acquires semaphore before launching browser
- Added internal methods `_initialize_browser()` and `_initialize_browser_with_session()` that execute within the semaphore lock

**Modified `run_voting_cycle()` method:**
- Added browser re-initialization check when resuming from pause
- Ensures browser is active before attempting to navigate
- Uses saved session if available, otherwise initializes fresh

## How It Works

### Sequential Resume Flow
1. **Hourly limit detected** → All instances paused, browsers closed
2. **Limit expires** → `_check_hourly_limit_expiry()` triggers
3. **Sequential resume begins:**
   - Collects all paused instances
   - Resumes them one by one
   - Waits `BROWSER_LAUNCH_DELAY` seconds between each resume
   - Logs progress: "Resumed instance #X (X/total)"

### Browser Launch Control
1. **Instance needs browser** → Calls `initialize()` or `initialize_with_saved_session()`
2. **Semaphore acquisition** → Waits for lock (only 1 browser can launch at a time)
3. **Browser launches** → Playwright starts, browser opens
4. **Semaphore released** → Next instance can now launch
5. **Delay enforced** → Wait before resuming next instance

## Benefits

### Memory Management
- **Prevents memory spikes**: Only 1 browser launches at a time
- **Controlled resource usage**: Configurable delay allows memory to stabilize
- **Predictable behavior**: No more random crashes from simultaneous launches

### Monitoring & Debugging
- **Detailed logging**: Track exactly which instance is launching and when
- **Progress visibility**: See resume progress (e.g., "3/10 instances resumed")
- **Status updates**: Each instance shows "Resumed - Initializing" status

### Flexibility
- **Configurable delay**: Adjust `BROWSER_LAUNCH_DELAY` based on server resources
- **Configurable concurrency**: Change `MAX_CONCURRENT_BROWSER_LAUNCHES` if needed
- **Easy tuning**: Modify config.py without touching core code

## Configuration Recommendations

### For Limited Resources (512MB - 1GB RAM)
```python
BROWSER_LAUNCH_DELAY = 10  # Wait 10 seconds between launches
MAX_CONCURRENT_BROWSER_LAUNCHES = 1  # Only 1 at a time
```

### For Medium Resources (2GB - 4GB RAM)
```python
BROWSER_LAUNCH_DELAY = 5  # Wait 5 seconds between launches
MAX_CONCURRENT_BROWSER_LAUNCHES = 2  # Allow 2 concurrent launches
```

### For High Resources (8GB+ RAM)
```python
BROWSER_LAUNCH_DELAY = 3  # Wait 3 seconds between launches
MAX_CONCURRENT_BROWSER_LAUNCHES = 3  # Allow 3 concurrent launches
```

## Testing

### Verify Sequential Launch
1. Start the voter system with multiple instances
2. Wait for hourly limit to trigger
3. Observe logs when limit expires:
   ```
   [HOURLY_LIMIT] ✅ Hourly limit expired - Resuming instances SEQUENTIALLY
   [HOURLY_LIMIT] Found 5 instances to resume
   [HOURLY_LIMIT] Resumed instance #1 (1/5)
   [HOURLY_LIMIT] Waiting 5s before next resume...
   [HOURLY_LIMIT] Resumed instance #2 (2/5)
   ...
   ```

### Monitor Memory Usage
```bash
# On Digital Ocean droplet
watch -n 1 free -m
```
You should see gradual memory increase instead of sudden spikes.

## Logs to Watch For

### Success Indicators
- `[INIT] Instance #X acquired browser launch lock`
- `[HOURLY_LIMIT] Resumed instance #X (X/total)`
- `[HOURLY_LIMIT] ✅ Sequential resume completed: X instances`

### Potential Issues
- `[INIT] Instance #X browser re-initialization failed` → Check memory/resources
- Multiple instances showing "Initializing" simultaneously → Semaphore not working

## Rollback Instructions

If you need to revert to simultaneous launches:
1. Set `MAX_CONCURRENT_BROWSER_LAUNCHES = 999` in `config.py`
2. Set `BROWSER_LAUNCH_DELAY = 0` in `config.py`

This effectively disables sequential launching while keeping the code intact.

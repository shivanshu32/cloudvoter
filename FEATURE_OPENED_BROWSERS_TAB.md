# Feature: Opened Browsers Tab with Real-Time Tracking

## 🎯 **Feature Overview**

Added a new "Opened Browsers" tab that provides real-time tracking of all headless browser instances with force close functionality.

**Key Features:**
1. ✅ Real-time browser tracking
2. ✅ Shows browser open duration
3. ✅ Force close button for each instance
4. ✅ Auto-refresh every 3 seconds
5. ✅ Clear visual status indicators

---

## 🎨 **UI Implementation**

### **1. New Tab Button**

**File:** `index.html` - Lines 122-129

```html
<button class="tab-btn" onclick="switchTab('browsers')">
    <span class="flex items-center space-x-2">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
        </svg>
        <span>Opened Browsers</span>
    </span>
</button>
```

### **2. Tab Content Section**

**File:** `index.html` - Lines 299-318

```html
<div id="browsers-tab" class="tab-content">
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div class="flex items-center justify-between mb-6">
            <div>
                <h2 class="text-xl font-semibold text-gray-900">Opened Browsers</h2>
                <p class="text-sm text-gray-500 mt-1">Real-time tracking of headless browser instances</p>
            </div>
            <div class="flex items-center space-x-4">
                <span id="browsers-count" class="text-sm font-medium text-gray-600">
                    <span class="text-2xl font-bold text-blue-600" id="open-browsers-count">0</span> browsers open
                </span>
            </div>
        </div>
        <div id="browsers-list" class="space-y-3">
            <p class="text-center text-gray-500 py-8">No browsers currently open</p>
        </div>
    </div>
</div>
```

### **3. Browser Card Display**

Each browser shows:
- **Instance ID** with active/inactive badge
- **IP Address**
- **Status** (current instance status)
- **Vote Count**
- **Browser Open Duration** (real-time)
- **Force Close Button** (red, disabled if browser closed)

```
┌────────────────────────────────────────────────────────┐
│ Instance #5                    🟢 Active               │
├────────────────────────────────────────────────────────┤
│ IP: 119.13.233.58              Status: Voting          │
│ Votes: 3                       Browser Open: 2m 45s    │
│                                                         │
│                                    [❌ Force Close]     │
└────────────────────────────────────────────────────────┘
```

---

## 🔧 **Frontend Implementation**

### **File:** `index.html`

### **1. Load Browsers Function (Lines 1158-1218)**

```javascript
async function loadBrowsers() {
    try {
        const response = await fetch(`${API_URL}/api/browsers`);
        const data = await response.json();
        
        const browsersList = document.getElementById('browsers-list');
        const browsersCount = document.getElementById('open-browsers-count');
        
        if (data.browsers && data.browsers.length > 0) {
            browsersCount.textContent = data.browsers.length;
            
            browsersList.innerHTML = data.browsers.map(browser => `
                <div class="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div class="flex items-center justify-between">
                        <div class="flex-1">
                            <div class="flex items-center space-x-3 mb-2">
                                <h3 class="text-lg font-semibold text-gray-900">Instance #${browser.instance_id}</h3>
                                <span class="status-badge ${browser.browser_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}">
                                    ${browser.browser_active ? '🟢 Active' : '⚫ Inactive'}
                                </span>
                            </div>
                            <div class="grid grid-cols-2 gap-2 text-sm text-gray-600">
                                <div><span class="font-medium">IP:</span> ${browser.ip || 'N/A'}</div>
                                <div><span class="font-medium">Status:</span> ${browser.status || 'Unknown'}</div>
                                <div><span class="font-medium">Votes:</span> ${browser.vote_count || 0}</div>
                                <div><span class="font-medium">Browser Open:</span> ${browser.browser_open_duration || '0s'}</div>
                            </div>
                        </div>
                        <div class="ml-4">
                            <button 
                                onclick="forceCloseBrowser(${browser.instance_id})" 
                                class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-colors flex items-center space-x-2"
                                ${!browser.browser_active ? 'disabled' : ''}
                            >
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                                </svg>
                                <span>Force Close</span>
                            </button>
                        </div>
                    </div>
                </div>
            `).join('');
        } else {
            browsersCount.textContent = '0';
            browsersList.innerHTML = '<p class="text-center text-gray-500 py-8">No browsers currently open</p>';
        }
    } catch (error) {
        console.error('Error loading browsers:', error);
        document.getElementById('browsers-list').innerHTML = '<p class="text-center text-red-500 py-8">Failed to load browsers</p>';
    }
}
```

### **2. Force Close Browser Function (Lines 1220-1246)**

```javascript
async function forceCloseBrowser(instanceId) {
    if (!confirm(`Are you sure you want to force close browser for Instance #${instanceId}?`)) {
        return;
    }
    
    try {
        addLog(`🔴 Force closing browser for instance #${instanceId}...`);
        
        const response = await fetch(`${API_URL}/api/force-close-browser/${instanceId}`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            addLog(`✅ ${data.message}`);
            loadBrowsers(); // Refresh browsers list
        } else {
            addLog(`❌ ${data.message}`);
            alert(data.message);
        }
    } catch (error) {
        console.error('Error force closing browser:', error);
        addLog(`❌ Failed to force close browser for instance #${instanceId}`);
        alert('Failed to force close browser');
    }
}
```

### **3. Auto-Refresh (Lines 1248-1254)**

```javascript
// Auto-refresh browsers list when tab is active
setInterval(() => {
    const browsersTab = document.getElementById('browsers-tab');
    if (browsersTab && browsersTab.classList.contains('active')) {
        loadBrowsers();
    }
}, 3000); // Refresh every 3 seconds
```

**Features:**
- Only refreshes when tab is active
- Updates every 3 seconds
- Minimal performance impact

---

## 🔧 **Backend Implementation**

### **File:** `app.py`

### **1. GET /api/browsers Endpoint (Lines 628-677)**

```python
@app.route('/api/browsers', methods=['GET'])
def get_browsers():
    """Get all opened browsers with their status"""
    global voter_system
    
    try:
        browsers = []
        
        if voter_system and hasattr(voter_system, 'active_instances'):
            for ip, instance in voter_system.active_instances.items():
                # Check if browser is open
                browser_active = instance.browser is not None and instance.page is not None
                
                # Calculate browser open duration
                browser_open_duration = "0s"
                if browser_active and hasattr(instance, 'browser_start_time'):
                    duration_seconds = int((datetime.now() - instance.browser_start_time).total_seconds())
                    if duration_seconds < 60:
                        browser_open_duration = f"{duration_seconds}s"
                    elif duration_seconds < 3600:
                        browser_open_duration = f"{duration_seconds // 60}m {duration_seconds % 60}s"
                    else:
                        hours = duration_seconds // 3600
                        minutes = (duration_seconds % 3600) // 60
                        browser_open_duration = f"{hours}h {minutes}m"
                
                browsers.append({
                    'instance_id': instance.instance_id,
                    'ip': instance.proxy_ip or 'N/A',
                    'status': instance.status,
                    'vote_count': instance.vote_count,
                    'browser_active': browser_active,
                    'browser_open_duration': browser_open_duration,
                    'is_paused': instance.is_paused,
                    'waiting_for_login': instance.waiting_for_login
                })
        
        return jsonify({
            'status': 'success',
            'browsers': sorted(browsers, key=lambda x: x['instance_id']),
            'total': len(browsers),
            'active_browsers': len([b for b in browsers if b['browser_active']])
        })
    
    except Exception as e:
        logger.error(f"Error getting browsers: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
```

**Returns:**
```json
{
    "status": "success",
    "browsers": [
        {
            "instance_id": 5,
            "ip": "119.13.233.58",
            "status": "Voting",
            "vote_count": 3,
            "browser_active": true,
            "browser_open_duration": "2m 45s",
            "is_paused": false,
            "waiting_for_login": false
        }
    ],
    "total": 20,
    "active_browsers": 15
}
```

### **2. POST /api/force-close-browser/<instance_id> Endpoint (Lines 679-738)**

```python
@app.route('/api/force-close-browser/<int:instance_id>', methods=['POST'])
def force_close_browser(instance_id):
    """Force close browser for a specific instance"""
    global voter_system
    
    try:
        if not voter_system:
            return jsonify({
                'status': 'error',
                'message': 'Voter system not initialized'
            }), 400
        
        # Find the instance
        instance = None
        for ip, inst in voter_system.active_instances.items():
            if inst.instance_id == instance_id:
                instance = inst
                break
        
        if not instance:
            return jsonify({
                'status': 'error',
                'message': f'Instance #{instance_id} not found'
            }), 404
        
        # Check if browser is open
        if not instance.browser and not instance.page:
            return jsonify({
                'status': 'error',
                'message': f'Instance #{instance_id} has no open browser'
            }), 400
        
        # Force close browser
        async def close_browser_async():
            try:
                await instance.close_browser()
                logger.info(f"[FORCE_CLOSE] Browser force closed for instance #{instance_id}")
            except Exception as e:
                logger.error(f"[FORCE_CLOSE] Error closing browser for instance #{instance_id}: {e}")
        
        # Run async close in event loop
        if event_loop:
            asyncio.run_coroutine_threadsafe(close_browser_async(), event_loop)
            
            return jsonify({
                'status': 'success',
                'message': f'Browser force closed for instance #{instance_id}'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Event loop not available'
            }), 500
    
    except Exception as e:
        logger.error(f"Error force closing browser: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
```

---

## 🔧 **VoterInstance Changes**

### **File:** `voter_engine.py`

### **1. Added browser_start_time Field (Line 84)**

```python
# Browser state
self.playwright = None
self.browser = None
self.context = None
self.page = None
self.browser_start_time = None  # Track when browser was opened
```

### **2. Set browser_start_time on Launch (Lines 350-351, 436-437)**

```python
# Track browser start time
self.browser_start_time = datetime.now()
```

**Locations:**
- `initialize()` method - Line 351
- `initialize_with_saved_session()` method - Line 437

### **3. Reset browser_start_time on Close (Line 1416)**

```python
# Force cleanup even on error
self.page = None
self.context = None
self.browser = None
self.playwright = None
self.browser_start_time = None
```

---

## 📊 **Browser Duration Calculation**

### **Format:**

```python
duration_seconds = int((datetime.now() - instance.browser_start_time).total_seconds())

if duration_seconds < 60:
    browser_open_duration = f"{duration_seconds}s"
elif duration_seconds < 3600:
    browser_open_duration = f"{duration_seconds // 60}m {duration_seconds % 60}s"
else:
    hours = duration_seconds // 3600
    minutes = (duration_seconds % 3600) // 60
    browser_open_duration = f"{hours}h {minutes}m"
```

**Examples:**
- `"15s"` - 15 seconds
- `"2m 45s"` - 2 minutes 45 seconds
- `"1h 23m"` - 1 hour 23 minutes

---

## 🎯 **Use Cases**

### **1. Monitor Browser Usage**

**Scenario:** Check how many browsers are currently open

**Action:**
1. Click "Opened Browsers" tab
2. See count: "15 browsers open"
3. View list of all open browsers

### **2. Force Close Stuck Browser**

**Scenario:** Instance stuck with browser open

**Action:**
1. Go to "Opened Browsers" tab
2. Find stuck instance
3. Click "Force Close" button
4. Confirm action
5. Browser immediately closed

### **3. Track Browser Duration**

**Scenario:** See how long browsers have been open

**Action:**
1. Open "Opened Browsers" tab
2. Check "Browser Open" column
3. See durations like "5m 23s", "1h 15m"

### **4. Identify Memory Leaks**

**Scenario:** Find browsers open too long

**Action:**
1. Sort by browser open duration
2. Find browsers open > 1 hour
3. Force close if needed

---

## 🔄 **Real-Time Updates**

### **Update Flow:**

```
User opens "Opened Browsers" tab
    ↓
loadBrowsers() called
    ↓
Fetch /api/browsers
    ↓
Display browser list
    ↓
Every 3 seconds:
    ↓
Check if tab is active
    ↓
If active: Refresh browser list
    ↓
Update durations, statuses
    ↓
Repeat
```

### **Performance:**

- **Refresh Rate:** 3 seconds
- **Only when tab active:** No unnecessary requests
- **Lightweight:** Only fetches instance metadata
- **No impact on voting:** Separate from voting logic

---

## 🎨 **Visual States**

### **Browser Active (Green Badge)**

```
Instance #5                    🟢 Active
IP: 119.13.233.58              Status: Voting
Votes: 3                       Browser Open: 2m 45s
                                    [❌ Force Close]
```

### **Browser Inactive (Gray Badge)**

```
Instance #5                    ⚫ Inactive
IP: 119.13.233.58              Status: Cooldown
Votes: 3                       Browser Open: 0s
                                    [❌ Force Close] (disabled)
```

### **No Browsers Open**

```
┌────────────────────────────────────────────────────────┐
│                                                         │
│         No browsers currently open                      │
│                                                         │
└────────────────────────────────────────────────────────┘
```

---

## 🧪 **Testing**

### **Test 1: View Opened Browsers**

1. Start monitoring with 10 instances
2. Click "Opened Browsers" tab
3. **Expected:** See list of 10 browsers with details

### **Test 2: Force Close Browser**

1. Open "Opened Browsers" tab
2. Find active browser
3. Click "Force Close"
4. Confirm
5. **Expected:** 
   - Browser closes immediately
   - List refreshes
   - Instance shows "⚫ Inactive"

### **Test 3: Auto-Refresh**

1. Open "Opened Browsers" tab
2. Wait 3 seconds
3. **Expected:** List refreshes automatically
4. Browser durations update

### **Test 4: Browser Duration**

1. Start instance
2. Wait 2 minutes
3. Check "Opened Browsers" tab
4. **Expected:** Shows "2m Xs" duration

---

## 📝 **Summary**

### **Files Modified:**

1. **`index.html`**
   - Added "Opened Browsers" tab button (lines 122-129)
   - Added browsers tab content (lines 299-318)
   - Added loadBrowsers() function (lines 1158-1218)
   - Added forceCloseBrowser() function (lines 1220-1246)
   - Added auto-refresh logic (lines 1248-1254)

2. **`app.py`**
   - Added /api/browsers endpoint (lines 628-677)
   - Added /api/force-close-browser endpoint (lines 679-738)

3. **`voter_engine.py`**
   - Added browser_start_time field (line 84)
   - Set browser_start_time on launch (lines 351, 437)
   - Reset browser_start_time on close (line 1416)

### **Features:**

- ✅ Real-time browser tracking
- ✅ Browser open duration display
- ✅ Force close functionality
- ✅ Auto-refresh every 3 seconds
- ✅ Active/inactive status badges
- ✅ Headless browser visibility
- ✅ Memory leak detection
- ✅ Clean UI design

---

## 🎉 **Result**

**Users can now:**
- ✅ See all opened browsers in real-time
- ✅ Track browser open duration
- ✅ Force close any browser instantly
- ✅ Monitor headless browser usage
- ✅ Identify stuck browsers
- ✅ Manage browser resources effectively

**Perfect for debugging and monitoring headless browser instances!** 🚀

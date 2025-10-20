# Persistent Configuration Storage Implementation

## ✅ **Feature Implemented**

Users can now save and persist:
1. **Voting URL** - Saved separately with its own button
2. **Bright Data Credentials** - Username and Password saved together

**All saved values persist across server restarts!**

---

## 🎯 **What Was Added**

### **1. Two Separate Save Buttons**

#### **Save URL Button** (Blue)
- Located next to the Voting URL input field
- Validates URL format before saving
- Shows success/error status messages

#### **Save Credentials Button** (Green)
- Located below the username/password fields
- Validates both fields are filled
- Shows success/error status messages

---

## 🔧 **Backend Implementation**

### **File:** `app.py`

#### **1. Updated `/api/config` Endpoint** - Lines 110-182

**Features:**
- **GET**: Load saved config from `user_config.json`
- **POST/PUT**: Save config to `user_config.json`
- **Persistent Storage**: JSON file in project root

**Priority Order:**
```
Saved Config > Environment Variables > config.py Defaults
```

**Code:**
```python
@app.route('/api/config', methods=['GET', 'POST', 'PUT'])
def config_endpoint():
    """Get or update configuration with persistent storage"""
    config_file = os.path.join(project_root, 'user_config.json')
    
    if request.method == 'GET':
        # Load saved config from file
        saved_config = {}
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                saved_config = json.load(f)
        
        return jsonify({
            'voting_url': saved_config.get('voting_url', TARGET_URL),
            'bright_data_username': saved_config.get('bright_data_username', ...),
            'bright_data_password': saved_config.get('bright_data_password', ...)
        })
    
    elif request.method in ['POST', 'PUT']:
        # Save to file
        with open(config_file, 'w') as f:
            json.dump(saved_config, f, indent=2)
        
        return jsonify({'status': 'success', 'message': 'Configuration saved'})
```

#### **2. Updated `/api/start-monitoring`** - Lines 184-208

Now loads saved config automatically:

```python
# Load saved config if available
config_file = os.path.join(project_root, 'user_config.json')
saved_config = {}
if os.path.exists(config_file):
    with open(config_file, 'r') as f:
        saved_config = json.load(f)

# Priority: request data > saved config > environment > config.py
username = data.get('username') or saved_config.get('bright_data_username') or ...
password = data.get('password') or saved_config.get('bright_data_password') or ...
voting_url = data.get('voting_url') or saved_config.get('voting_url') or TARGET_URL
```

---

## 🎨 **Frontend Implementation**

### **File:** `index.html`

#### **1. Updated HTML Structure** - Lines 155-189

**Before:**
```html
<input type="text" id="voting-url" ...>
<input type="text" id="username" ...>
<input type="password" id="password" ...>
```

**After:**
```html
<!-- Voting URL Section -->
<div class="bg-white p-4 rounded-lg border border-gray-200">
    <label>Voting URL</label>
    <div class="flex gap-2">
        <input type="text" id="voting-url" class="flex-1" ...>
        <button id="save-url-btn" class="bg-blue-600 text-white">
            💾 Save URL
        </button>
    </div>
    <p id="url-save-status" class="text-sm mt-2 hidden"></p>
</div>

<!-- Bright Data Credentials Section -->
<div class="bg-white p-4 rounded-lg border border-gray-200">
    <label>Bright Data Credentials</label>
    <div class="grid grid-cols-2 gap-4">
        <input type="text" id="username" ...>
        <input type="password" id="password" ...>
    </div>
    <button id="save-credentials-btn" class="bg-green-600 text-white">
        💾 Save Credentials
    </button>
    <p id="credentials-save-status" class="text-sm mt-2 hidden"></p>
</div>
```

#### **2. JavaScript Functions** - Lines 418-567

**Load Configuration (on page load):**
```javascript
async function loadConfiguration() {
    const response = await fetch(`${API_URL}/api/config`);
    const data = await response.json();
    
    votingUrlInput.value = data.voting_url || '';
    usernameInput.value = data.bright_data_username || '';
    passwordInput.value = data.bright_data_password || '';
    
    addLog('✅ Configuration loaded successfully');
}
```

**Save Voting URL:**
```javascript
async function saveVotingUrl() {
    const votingUrl = urlInput.value.trim();
    
    // Validate URL
    if (!votingUrl) {
        showStatus(statusElement, '⚠️ Please enter a voting URL', 'text-orange-600');
        return;
    }
    
    try {
        new URL(votingUrl);  // Validate URL format
    } catch (e) {
        showStatus(statusElement, '❌ Invalid URL format', 'text-red-600');
        return;
    }
    
    // Save to backend
    const response = await fetch(`${API_URL}/api/config`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ voting_url: votingUrl })
    });
    
    const data = await response.json();
    if (data.status === 'success') {
        showStatus(statusElement, '✅ Voting URL saved successfully!', 'text-green-600');
        addLog(`💾 Voting URL saved: ${votingUrl}`);
    }
}
```

**Save Credentials:**
```javascript
async function saveCredentials() {
    const username = usernameInput.value.trim();
    const password = passwordInput.value.trim();
    
    // Validate inputs
    if (!username || !password) {
        showStatus(statusElement, '⚠️ Please enter both username and password', 'text-orange-600');
        return;
    }
    
    // Save to backend
    const response = await fetch(`${API_URL}/api/config`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            bright_data_username: username,
            bright_data_password: password
        })
    });
    
    const data = await response.json();
    if (data.status === 'success') {
        showStatus(statusElement, '✅ Credentials saved successfully!', 'text-green-600');
        addLog('💾 Bright Data credentials saved');
    }
}
```

**Helper Function:**
```javascript
function showStatus(element, message, className) {
    element.textContent = message;
    element.className = `text-sm mt-2 ${className}`;
    element.classList.remove('hidden');
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        element.classList.add('hidden');
    }, 5000);
}
```

#### **3. Event Listeners** - Lines 548-568

```javascript
function setupEventListeners() {
    // Save buttons
    document.getElementById('save-url-btn').addEventListener('click', saveVotingUrl);
    document.getElementById('save-credentials-btn').addEventListener('click', saveCredentials);
    
    // Optional: Save on Enter key
    votingUrlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') saveVotingUrl();
    });
    usernameInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') saveCredentials();
    });
    passwordInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') saveCredentials();
    });
}
```

---

## 📁 **Storage File**

### **File:** `user_config.json` (created in project root)

**Location:** `c:\Users\shubh\OneDrive\Desktop\cloudvoter\user_config.json`

**Format:**
```json
{
  "voting_url": "https://www.cutebabyvote.com/october-2025/?contest=photo-detail&photo_id=463146",
  "voting_urls": [
    "https://www.cutebabyvote.com/october-2025/?contest=photo-detail&photo_id=463146"
  ],
  "bright_data_username": "hl_47ba96ab",
  "bright_data_password": "tcupn0cw7pbz"
}
```

**Features:**
- ✅ Persists across server restarts
- ✅ Human-readable JSON format
- ✅ Auto-created on first save
- ✅ Gitignored (add to `.gitignore`)

---

## 🎯 **User Workflow**

### **Scenario 1: First Time Setup**

1. **Open CloudVoter** → Page loads with empty fields
2. **Enter Voting URL** → Type URL in field
3. **Click "💾 Save URL"** → URL saved to `user_config.json`
4. **See confirmation** → "✅ Voting URL saved successfully!"
5. **Enter Credentials** → Type username and password
6. **Click "💾 Save Credentials"** → Credentials saved
7. **See confirmation** → "✅ Credentials saved successfully!"

### **Scenario 2: Restart Server**

1. **Stop server** → `Ctrl+C`
2. **Restart server** → `python app.py`
3. **Open CloudVoter** → Page loads
4. **Fields auto-filled** → Saved values loaded automatically!
5. **Start monitoring** → Uses saved credentials

### **Scenario 3: Update Configuration**

1. **Change Voting URL** → Edit URL in field
2. **Click "💾 Save URL"** → New URL saved
3. **See confirmation** → "✅ Voting URL saved successfully!"
4. **Old value replaced** → `user_config.json` updated

---

## 🎨 **Visual Design**

### **Voting URL Section:**
```
┌─────────────────────────────────────────────────────┐
│ Voting URL                                          │
├─────────────────────────────────────────────────────┤
│ [https://www.cutebabyvote.com/...] [💾 Save URL]   │
│ ✅ Voting URL saved successfully!                   │
└─────────────────────────────────────────────────────┘
```

### **Credentials Section:**
```
┌─────────────────────────────────────────────────────┐
│ Bright Data Credentials                             │
├─────────────────────────────────────────────────────┤
│ Username                    Password                │
│ [hl_47ba96ab]              [••••••••••]            │
│                                                     │
│ [💾 Save Credentials] ✅ Credentials saved!         │
└─────────────────────────────────────────────────────┘
```

---

## ✅ **Validation**

### **Voting URL:**
- ✅ Not empty
- ✅ Valid URL format (uses `new URL()`)
- ✅ Shows error if invalid

### **Credentials:**
- ✅ Both username and password required
- ✅ Shows error if either is missing
- ✅ Trims whitespace

---

## 🔄 **Status Messages**

### **Success Messages (Green):**
- ✅ Voting URL saved successfully!
- ✅ Credentials saved successfully!

### **Warning Messages (Orange):**
- ⚠️ Please enter a voting URL
- ⚠️ Please enter both username and password

### **Error Messages (Red):**
- ❌ Invalid URL format
- ❌ Failed to save voting URL
- ❌ Failed to save credentials

**Auto-hide:** All messages disappear after 5 seconds

---

## 🚀 **Features**

### **1. Persistent Storage**
- ✅ Saves to JSON file
- ✅ Survives server restarts
- ✅ Survives script restarts
- ✅ Human-readable format

### **2. Auto-Load**
- ✅ Loads on page load
- ✅ Fills input fields automatically
- ✅ No manual action needed

### **3. Separate Save Buttons**
- ✅ Save URL independently
- ✅ Save credentials independently
- ✅ Update anytime

### **4. Validation**
- ✅ URL format validation
- ✅ Required field validation
- ✅ Clear error messages

### **5. User Feedback**
- ✅ Button states (Saving...)
- ✅ Status messages
- ✅ Log entries
- ✅ Auto-hide messages

### **6. Keyboard Shortcuts**
- ✅ Press Enter in URL field → Save URL
- ✅ Press Enter in username/password → Save credentials

---

## 🔒 **Security Considerations**

### **Current Implementation:**
- Credentials stored in plain text in `user_config.json`
- File is on local server (not exposed to internet)

### **Recommendations:**

1. **Add to `.gitignore`:**
```
# User configuration (contains credentials)
user_config.json
```

2. **File Permissions:**
```bash
chmod 600 user_config.json  # Read/write for owner only
```

3. **Future Enhancement:**
Consider encrypting credentials:
```python
from cryptography.fernet import Fernet

# Encrypt before saving
cipher = Fernet(key)
encrypted_password = cipher.encrypt(password.encode())

# Decrypt when loading
decrypted_password = cipher.decrypt(encrypted_password).decode()
```

---

## 📊 **Priority Order**

When starting monitoring, credentials are loaded in this order:

1. **Request data** (from Start Monitoring button)
2. **Saved config** (`user_config.json`)
3. **Environment variables** (`BRIGHT_DATA_USERNAME`, `BRIGHT_DATA_PASSWORD`)
4. **Config.py defaults** (`BRIGHT_DATA_USERNAME`, `BRIGHT_DATA_PASSWORD`)

**Example:**
```
User clicks "Start Monitoring" without entering credentials
    ↓
Check request data → Empty
    ↓
Check saved config → Found! Use saved credentials
    ↓
Start monitoring with saved credentials ✅
```

---

## 🧪 **Testing**

### **Test 1: Save Voting URL**
1. Enter URL: `https://example.com/vote`
2. Click "💾 Save URL"
3. **Expected:** 
   - Button shows "💾 Saving..."
   - Success message appears
   - Log shows "💾 Voting URL saved"
   - File `user_config.json` created with URL

### **Test 2: Save Credentials**
1. Enter username: `test_user`
2. Enter password: `test_pass`
3. Click "💾 Save Credentials"
4. **Expected:**
   - Button shows "💾 Saving..."
   - Success message appears
   - Log shows "💾 Bright Data credentials saved"
   - File `user_config.json` updated with credentials

### **Test 3: Restart Server**
1. Save URL and credentials
2. Stop server (`Ctrl+C`)
3. Restart server (`python app.py`)
4. Refresh browser
5. **Expected:**
   - URL field auto-filled
   - Username field auto-filled
   - Password field auto-filled

### **Test 4: Validation**
1. Click "💾 Save URL" with empty field
2. **Expected:** "⚠️ Please enter a voting URL"
3. Enter invalid URL: `not-a-url`
4. Click "💾 Save URL"
5. **Expected:** "❌ Invalid URL format"

### **Test 5: Update Values**
1. Save URL: `https://example.com/vote1`
2. Change to: `https://example.com/vote2`
3. Click "💾 Save URL"
4. **Expected:**
   - New URL saved
   - Old URL replaced in file

---

## 📝 **Summary**

### **What Was Implemented:**

✅ **Two separate save buttons:**
- 💾 Save URL (Blue button)
- 💾 Save Credentials (Green button)

✅ **Persistent storage:**
- Saves to `user_config.json`
- Survives server restarts

✅ **Auto-load:**
- Loads saved values on page load
- Fills input fields automatically

✅ **Validation:**
- URL format validation
- Required field validation

✅ **User feedback:**
- Success/error messages
- Button states
- Log entries

✅ **Keyboard shortcuts:**
- Enter key to save

### **Files Modified:**

1. **`app.py`** - Backend API endpoints
2. **`index.html`** - Frontend UI and JavaScript

### **Files Created:**

1. **`user_config.json`** - Persistent storage (auto-created)

---

## 🎉 **Result**

Users can now:
- ✅ Save Voting URL independently
- ✅ Save Bright Data credentials independently
- ✅ Update values anytime
- ✅ Have values persist across restarts
- ✅ See clear success/error feedback
- ✅ Use keyboard shortcuts (Enter key)

**Configuration is now fully persistent and user-friendly!** 🚀

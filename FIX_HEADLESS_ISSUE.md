# Fix Headless Browser Issue on DigitalOcean

## 🔍 Root Cause Analysis

Your **local code** already has `headless=True` in the correct places:
- ✅ `voter_engine.py` line 236: `headless=True`
- ✅ `voter_engine.py` line 300: `headless=True`
- ✅ `config.py` line 23: `HEADLESS_MODE = True`

**But your server is still using old code with `headless=False`!**

---

## 🎯 The Problem

Your server has **outdated code** that wasn't updated when you pushed to GitHub or the changes weren't pulled properly.

---

## ✅ Solution: Update Server Code from GitHub

### **Step 1: Connect to Server**

```bash
ssh root@YOUR_DROPLET_IP
```

### **Step 2: Stop PM2**

```bash
pm2 stop cloudvoter-backend
pm2 delete cloudvoter-backend
```

### **Step 3: Backup Session Data**

```bash
cd /root/cloudvoter/backend
tar -czf /root/session_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
    brightdata_session_data/ \
    voting_logs.csv \
    config.py
```

### **Step 4: Pull Latest Code from GitHub**

```bash
cd /root/cloudvoter
git status
git stash  # Save any local changes
git pull origin main
```

**If git pull fails:**
```bash
git fetch origin
git reset --hard origin/main
```

### **Step 5: Restore Session Data (if needed)**

```bash
cd /root/cloudvoter/backend

# Check if session data exists
ls -la brightdata_session_data/

# If missing, restore from backup
if [ ! -d "brightdata_session_data" ]; then
    tar -xzf /root/session_backup_*.tar.gz
fi
```

### **Step 6: Verify Code is Updated**

```bash
cd /root/cloudvoter/backend

# Check voter_engine.py line 236
sed -n '236p' voter_engine.py
# Should show: headless=True,

# Check voter_engine.py line 300
sed -n '300p' voter_engine.py
# Should show: headless=True,

# Check config.py
grep HEADLESS_MODE config.py
# Should show: HEADLESS_MODE = True
```

### **Step 7: Verify config.py Has Credentials**

```bash
nano config.py
```

**Make sure these are set:**
```python
BRIGHT_DATA_USERNAME = "hl_47ba96ab"
BRIGHT_DATA_PASSWORD = "your-actual-password"
TARGET_URL = "https://www.cutebabyvote.com/vote/..."
HEADLESS_MODE = True
```

**Save: Ctrl+X, Y, Enter**

### **Step 8: Restart PM2**

```bash
pm2 start ecosystem.config.js
pm2 save
```

### **Step 9: Monitor Logs**

```bash
pm2 logs cloudvoter-backend
```

**You should now see:**
```
✅ Browser launched successfully (headless mode)
🔍 Navigating to voting page...
✅ Navigation successful
```

---

## 🔧 Alternative: Manual Fix (If Git Pull Doesn't Work)

### **Option 1: Edit voter_engine.py Directly**

```bash
cd /root/cloudvoter/backend

# Find all headless=False
grep -n "headless=False" voter_engine.py

# Replace all occurrences
sed -i 's/headless=False/headless=True/g' voter_engine.py

# Verify
grep -n "headless=" voter_engine.py

# Restart
pm2 restart cloudvoter-backend
```

### **Option 2: Upload Fresh voter_engine.py**

**From your local machine:**

```powershell
# Upload the correct file
scp C:\Users\shubh\OneDrive\Desktop\cloudvoter\backend\voter_engine.py root@YOUR_DROPLET_IP:/root/cloudvoter/backend/

# Then on server
ssh root@YOUR_DROPLET_IP
pm2 restart cloudvoter-backend
```

---

## 🐛 Debugging: Check What's Actually Running

### **Check if PM2 is using the correct file**

```bash
pm2 show cloudvoter-backend
```

**Look for:**
- `cwd`: Should be `/root/cloudvoter/backend`
- `script path`: Should be `/root/cloudvoter/backend/venv/bin/python`

### **Check the actual code being executed**

```bash
cd /root/cloudvoter/backend

# Show the exact line that's failing (line 299)
sed -n '295,305p' voter_engine.py
```

**Should show:**
```python
# Launch browser with proxy
self.browser = await self.playwright.chromium.launch(
    headless=True,  # <-- Must be True
    proxy={
        'server': self.proxy_config['server'],
        'username': self.proxy_config['username'],
        'password': self.proxy_config['password']
    },
    args=browser_args
)
```

### **Verify Python is importing the correct config**

```bash
cd /root/cloudvoter/backend
source venv/bin/activate
python3 -c "from config import HEADLESS_MODE; print('HEADLESS_MODE:', HEADLESS_MODE)"
```

**Should output:**
```
HEADLESS_MODE: True
```

---

## 📊 Complete Verification Checklist

Run these commands and verify each output:

```bash
# 1. Check config.py
grep HEADLESS_MODE /root/cloudvoter/backend/config.py
# Expected: HEADLESS_MODE = True

# 2. Check voter_engine.py line 236
sed -n '236p' /root/cloudvoter/backend/voter_engine.py
# Expected: headless=True,

# 3. Check voter_engine.py line 300
sed -n '300p' /root/cloudvoter/backend/voter_engine.py
# Expected: headless=True,

# 4. Check for any headless=False
grep -n "headless=False" /root/cloudvoter/backend/voter_engine.py
# Expected: (empty - no results)

# 5. Check PM2 is using correct directory
pm2 show cloudvoter-backend | grep cwd
# Expected: /root/cloudvoter/backend

# 6. Check Python imports
cd /root/cloudvoter/backend && source venv/bin/activate && python3 -c "from config import HEADLESS_MODE; print(HEADLESS_MODE)"
# Expected: True
```

**If ALL checks pass, restart PM2:**
```bash
pm2 restart cloudvoter-backend
pm2 logs cloudvoter-backend
```

---

## 🚨 Nuclear Option: Fresh Deployment

If nothing works, redeploy from scratch:

```bash
# 1. Backup everything
cd /root/cloudvoter/backend
tar -czf /root/full_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
    brightdata_session_data/ \
    voting_logs.csv \
    config.py \
    cloudvoter.log

# 2. Stop PM2
pm2 stop cloudvoter-backend
pm2 delete cloudvoter-backend
pm2 kill

# 3. Remove old code
cd /root
mv cloudvoter cloudvoter.old

# 4. Clone fresh from GitHub
git clone https://github.com/YOUR_USERNAME/cloudvoter.git
cd cloudvoter/backend

# 5. Restore session data
tar -xzf /root/full_backup_*.tar.gz

# 6. Setup virtual environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
playwright install-deps chromium

# 7. Verify config
nano config.py
# Set credentials

# 8. Create PM2 config
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [{
    name: 'cloudvoter-backend',
    script: 'venv/bin/python',
    args: 'app.py',
    cwd: '/root/cloudvoter/backend',
    interpreter: 'none',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '2G',
    env: { PYTHONUNBUFFERED: '1' }
  }]
};
EOF

mkdir -p logs

# 9. Start PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
# Run the command it outputs
pm2 save

# 10. Verify
pm2 logs cloudvoter-backend
```

---

## 📞 Quick Commands Summary

```bash
# Stop PM2
pm2 stop cloudvoter-backend && pm2 delete cloudvoter-backend

# Pull latest code
cd /root/cloudvoter && git pull origin main

# Verify code
grep -n "headless=" /root/cloudvoter/backend/voter_engine.py

# Start PM2
pm2 start /root/cloudvoter/backend/ecosystem.config.js && pm2 save

# Watch logs
pm2 logs cloudvoter-backend
```

---

## ✅ Expected Success Output

After fixing, you should see:

```
[10:50:00 AM] 🚀 Launching instance #9 from saved session
[10:50:01 AM] [IP] Assigned IP: 77.83.69.235
[10:50:01 AM] [INIT] Instance #9 initializing with saved session...
[10:50:03 AM] ✅ Browser launched successfully
[10:50:04 AM] 🔍 Navigating to voting page...
[10:50:06 AM] ✅ Navigation successful
[10:50:06 AM] 🔑 Checking login status...
[10:50:07 AM] ✅ Already logged in (session restored)
[10:50:07 AM] 🗳️ Starting voting cycle...
[10:50:10 AM] ✅ Vote submitted successfully
```

---

## 🎯 Root Cause Summary

**Problem:** Server code is outdated with `headless=False`

**Solution:** Pull latest code from GitHub or manually fix voter_engine.py

**Prevention:** Always pull latest code after pushing to GitHub

---

**Follow the steps above and the headless issue will be resolved!** 🚀

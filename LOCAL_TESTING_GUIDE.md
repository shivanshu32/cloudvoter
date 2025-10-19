# CloudVoter Local Testing Guide

## 🎯 Complete Step-by-Step Testing Instructions

Follow these steps to test CloudVoter on your local Windows machine before deploying to DigitalOcean.

---

## 📋 Prerequisites

Before starting, ensure you have:

- [ ] Python 3.11 or higher installed
- [ ] Node.js 16+ and npm installed
- [ ] Git (optional)
- [ ] Command Prompt or PowerShell access

**Check versions:**
```bash
python --version
node --version
npm --version
```

---

## 🚀 Step 1: Copy Required Data

### Copy Session Data and Voting Logs

```bash
# Navigate to cloudvoter folder
cd C:\Users\shubh\OneDrive\Desktop\cloudvoter

# Run the copy script
copy_all_data.bat
```

**What this does:**
- ✅ Copies `brightdata_session_data/` from googleloginautomate
- ✅ Copies `voting_logs.csv` from googleloginautomate
- ✅ Creates necessary directories

**Verify:**
```bash
# Check session data
dir brightdata_session_data

# Check voting logs
dir voting_logs.csv
```

---

## 🔧 Step 2: Setup Backend

### 2.1 Navigate to Backend Folder

```bash
cd C:\Users\shubh\OneDrive\Desktop\cloudvoter\backend
```

### 2.2 Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv
```

### 2.3 Activate Virtual Environment

```bash
# Activate (Windows Command Prompt)
venv\Scripts\activate.bat

# OR (Windows PowerShell)
venv\Scripts\Activate.ps1
```

**You should see `(venv)` in your prompt:**
```
(venv) C:\Users\shubh\OneDrive\Desktop\cloudvoter\backend>
```

### 2.4 Install Python Dependencies

**For Windows (Recommended):**
```bash
pip install -r requirements-windows.txt
```

**For Linux/Mac:**
```bash
pip install -r requirements.txt
```

**Expected output:**
```
Installing collected packages: Flask, Flask-CORS, Flask-SocketIO, playwright, ...
Successfully installed Flask-3.0.0 ...
```

**Note:** Windows uses `requirements-windows.txt` to avoid compilation issues. See WINDOWS_SETUP_FIX.md if you encounter errors.

### 2.5 Install Playwright Browsers

```bash
playwright install chromium
```

**This downloads Chromium browser (~300MB):**
```
Downloading Chromium...
✅ Chromium installed successfully
```

### 2.6 Verify Backend Setup

```bash
# Check if all imports work
python -c "from voter_engine import MultiInstanceVoter; print('✅ Backend setup complete')"
```

---

## 🎨 Step 3: Setup Frontend

### 3.1 Open New Terminal

**Keep backend terminal open!** Open a **new** Command Prompt or PowerShell window.

### 3.2 Navigate to Frontend Folder

```bash
cd C:\Users\shubh\OneDrive\Desktop\cloudvoter\frontend
```

### 3.3 Install Node Dependencies

```bash
npm install
```

**Expected output:**
```
added 1500 packages in 2m
✅ Dependencies installed
```

**This installs:**
- React
- Socket.IO client
- Axios
- Lucide icons
- All other dependencies

### 3.4 Verify Frontend Setup

```bash
# Check if node_modules exists
dir node_modules

# Should show many folders
```

---

## ▶️ Step 4: Start Backend Server

### 4.1 In Backend Terminal

```bash
# Make sure you're in backend folder with venv activated
cd C:\Users\shubh\OneDrive\Desktop\cloudvoter\backend
venv\Scripts\activate

# Start backend
python app.py
```

### 4.2 Expected Output

```
✅ Event loop thread started
 * Serving Flask app 'app'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

### 4.3 Verify Backend Running

**Open browser and visit:**
```
http://localhost:5000/api/health
```

**Should show:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-19T01:05:00",
  "monitoring_active": false
}
```

✅ **Backend is running!**

---

## ▶️ Step 5: Start Frontend Server

### 5.1 In Frontend Terminal (Second Terminal)

```bash
# Make sure you're in frontend folder
cd C:\Users\shubh\OneDrive\Desktop\cloudvoter\frontend

# Start frontend
npm start
```

### 5.2 Expected Output

```
Compiled successfully!

You can now view cloudvoter-frontend in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.1.x:3000

Note that the development build is not optimized.
To create a production build, use npm run build.

webpack compiled with 0 warnings
```

### 5.3 Browser Opens Automatically

Browser should automatically open to:
```
http://localhost:3000
```

If not, manually open browser and go to `http://localhost:3000`

✅ **Frontend is running!**

---

## 🧪 Step 6: Test the Application

### 6.1 Verify UI Loads

**You should see:**
- ✅ CloudVoter Control Panel header
- ✅ Dashboard with statistics (all zeros initially)
- ✅ Configuration section with pre-filled credentials
- ✅ "Start Ultra Monitoring" button
- ✅ Logs tab

### 6.2 Check Configuration Loaded

**In the logs section, you should see:**
```
[HH:MM:SS] 🔌 Connected to CloudVoter server
[HH:MM:SS] ✅ Configuration loaded from config.py
```

**In the configuration section:**
- Username field should show: `hl_47ba96ab`
- Password field should show: `••••••••••••`
- Voting URL should show: `https://www.cutebabyvote.com/...`

✅ **Configuration loaded successfully!**

### 6.3 Test Start Ultra Monitoring

**Click "Start Ultra Monitoring" button**

**Expected logs:**
```
[HH:MM:SS] 🚀 Starting ultra monitoring...
[HH:MM:SS] ✅ Ultra monitoring started successfully
[HH:MM:SS] 🔍 Scanning saved sessions...
[HH:MM:SS] 📋 Found X saved sessions
[HH:MM:SS] ⏰ Instance #1: Y minutes remaining in cooldown
[HH:MM:SS] ✅ Instance #2: Ready to launch!
[HH:MM:SS] 🚀 Launching Instance #2...
```

**Button should change to:**
```
⏹ Stop Ultra Monitoring
```

**Status indicator should turn green:**
```
🟢 Monitoring Active
```

✅ **Ultra Monitoring started!**

### 6.4 Watch Instance Launch

**If instances are ready, you'll see:**
```
[HH:MM:SS] 🌐 Bright Data assigned IP: 103.45.67.89
[HH:MM:SS] 🔍 Navigating to voting page...
[HH:MM:SS] ✅ Navigation successful
[HH:MM:SS] 🔑 Checking login status...
[HH:MM:SS] ✅ Already logged in
[HH:MM:SS] 🗳️ Starting voting cycle...
```

**Dashboard should update:**
- Active Instances count increases
- Instance cards appear showing status

✅ **Instances launching successfully!**

### 6.5 Test Manual Instance Launch

**Click "Launch Instance" button**

**Expected:**
```
[HH:MM:SS] 🚀 Launching new instance...
[HH:MM:SS] 🌐 Getting unique IP from Bright Data...
[HH:MM:SS] 🌐 Assigned IP: 104.56.78.90
[HH:MM:SS] 🚀 Instance #3 created
```

✅ **Manual launch working!**

### 6.6 Test Stop Monitoring

**Click "Stop Ultra Monitoring" button**

**Expected:**
```
[HH:MM:SS] ⏹ Stopping ultra monitoring...
[HH:MM:SS] ✅ Ultra monitoring stopped
```

**Button changes back to:**
```
🚀 Start Ultra Monitoring
```

**Status indicator turns gray:**
```
⚪ Monitoring Inactive
```

✅ **Stop working!**

---

## ✅ Step 7: Verify Everything Works

### Checklist

- [ ] Backend running on http://localhost:5000
- [ ] Frontend running on http://localhost:3000
- [ ] UI loads without errors
- [ ] Configuration pre-filled from config.py
- [ ] WebSocket connected (green status)
- [ ] "Start Ultra Monitoring" button works
- [ ] Logs appear in real-time
- [ ] Instances launch (if sessions ready)
- [ ] Dashboard statistics update
- [ ] "Stop Ultra Monitoring" works
- [ ] "Launch Instance" works

**If all checked:** ✅ **CloudVoter is working perfectly!**

---

## 🔍 Step 8: Test Specific Features

### Test 1: Session Restoration

**If you have saved sessions with completed cooldowns:**

1. Click "Start Ultra Monitoring"
2. Watch logs for session scanning
3. Should see: "Found X saved sessions"
4. Should see: "Instance #Y ready to launch"
5. Instance should launch automatically
6. Browser should restore session (already logged in)

### Test 2: Cooldown Detection

**If sessions are in cooldown:**

1. Click "Start Ultra Monitoring"
2. Should see: "Instance #X: Y minutes remaining"
3. System waits for cooldown
4. After Y minutes, instance launches automatically

### Test 3: Login Detection

**If session requires login:**

1. Instance launches
2. Should see: "🔑 Checking login status..."
3. Should see: "🔑 Login required"
4. Status shows: "🔑 Waiting for Login"
5. Browser stays open (headless=False in config)

### Test 4: Real-Time Updates

1. Open browser console (F12)
2. Check Network tab
3. Should see WebSocket connection
4. Logs should appear in real-time
5. Statistics should update every 5 seconds

### Test 5: Statistics

1. After some voting attempts
2. Dashboard should show:
   - Active Instances count
   - Successful Votes count
   - Success Rate percentage
3. Numbers should update in real-time

---

## 🐛 Troubleshooting

### Problem: Backend won't start

**Error: "Port 5000 already in use"**

```bash
# Find process using port 5000
netstat -ano | findstr :5000

# Kill the process (replace PID with actual number)
taskkill /PID <PID> /F

# Or use different port
# Edit app.py, change port to 5001
```

**Error: "Module not found"**

```bash
# Make sure venv is activated
venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

**Error: "Playwright not found"**

```bash
# Install Playwright browsers
playwright install chromium
```

### Problem: Frontend won't start

**Error: "npm command not found"**

```bash
# Install Node.js from nodejs.org
# Then try again
```

**Error: "Port 3000 already in use"**

```bash
# Kill process on port 3000
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Or set different port
set PORT=3001 && npm start
```

**Error: "Dependencies not installed"**

```bash
# Delete node_modules and reinstall
rmdir /s /q node_modules
npm install
```

### Problem: UI loads but shows errors

**Check browser console (F12):**

```
Common errors:
- WebSocket connection failed → Backend not running
- API calls failing → Check backend URL
- CORS errors → Backend CORS not configured
```

**Solutions:**
```bash
# Restart backend
cd backend
python app.py

# Check backend health
curl http://localhost:5000/api/health
```

### Problem: Configuration not loading

**Symptoms:**
- Credentials empty in UI
- No log message about config loading

**Solutions:**
```bash
# Check config.py syntax
python -c "from config import BRIGHT_DATA_USERNAME; print(BRIGHT_DATA_USERNAME)"

# Check API endpoint
curl http://localhost:5000/api/config

# Check browser console for errors
```

### Problem: Instances not launching

**Check logs for:**
- "Authentication failed" → Wrong credentials
- "Could not get unique IP" → Bright Data connection issue
- "No saved sessions" → Run copy_all_data.bat

**Solutions:**
```bash
# Verify credentials in config.py
cat backend/config.py | grep BRIGHT_DATA

# Test Bright Data connection
# (Check backend logs for connection test)

# Copy session data
copy_all_data.bat
```

### Problem: Browser not visible

**This is normal!** Browsers run in background by default.

**To see browsers:**
1. Edit `backend/config.py`
2. Set `HEADLESS_MODE = False`
3. Restart backend
4. Browsers will be visible

---

## 📊 Expected Terminal Output

### Backend Terminal

```
(venv) C:\...\cloudvoter\backend> python app.py

✅ Event loop thread started
 * Serving Flask app 'app'
 * Debug mode: off
WARNING: This is a development server.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit

[2025-01-19 01:05:00] INFO - ✅ Configuration loaded
[2025-01-19 01:05:15] INFO - 🔌 Client connected
[2025-01-19 01:05:20] INFO - 🚀 Starting ultra monitoring
[2025-01-19 01:05:21] INFO - 🔍 Scanning saved sessions
[2025-01-19 01:05:22] INFO - 📋 Found 5 saved sessions
```

### Frontend Terminal

```
C:\...\cloudvoter\frontend> npm start

Compiled successfully!

You can now view cloudvoter-frontend in the browser.

  Local:            http://localhost:3000

webpack compiled successfully
```

---

## 🎯 Quick Test Script

Create a test script to verify everything:

```bash
# test_local.bat
@echo off
echo Testing CloudVoter Locally
echo.

echo 1. Checking backend health...
curl http://localhost:5000/api/health
echo.

echo 2. Checking config endpoint...
curl http://localhost:5000/api/config
echo.

echo 3. Checking frontend...
curl http://localhost:3000
echo.

echo Tests complete!
pause
```

---

## ✅ Success Criteria

CloudVoter is working correctly if:

1. ✅ Backend starts without errors
2. ✅ Frontend starts and opens browser
3. ✅ UI loads completely
4. ✅ Configuration pre-filled
5. ✅ WebSocket connects (green indicator)
6. ✅ "Start Ultra Monitoring" works
7. ✅ Logs appear in real-time
8. ✅ Instances launch (if sessions ready)
9. ✅ Dashboard updates
10. ✅ No errors in browser console

---

## 🚀 Next Steps After Local Testing

Once local testing is successful:

1. **Deploy to DigitalOcean**
   - Follow QUICKSTART.md
   - Use deploy.sh script

2. **Test on Server**
   - Same functionality
   - Accessible remotely

3. **Monitor Production**
   - Check logs regularly
   - Monitor statistics
   - Backup session data

---

## 📝 Testing Checklist

Print this checklist and check off as you test:

```
□ Prerequisites installed (Python, Node.js)
□ Session data copied (copy_all_data.bat)
□ Backend virtual environment created
□ Python dependencies installed
□ Playwright browsers installed
□ Frontend dependencies installed
□ Backend starts successfully
□ Frontend starts successfully
□ UI loads in browser
□ Configuration pre-filled
□ WebSocket connected
□ Start monitoring works
□ Logs appear in real-time
□ Instances launch
□ Dashboard updates
□ Stop monitoring works
□ Manual launch works
□ No console errors
□ All features tested
```

---

## 🎉 Summary

**To test CloudVoter locally:**

```bash
# 1. Copy data
copy_all_data.bat

# 2. Setup backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

# 3. Setup frontend (new terminal)
cd frontend
npm install

# 4. Start backend (terminal 1)
cd backend
venv\Scripts\activate
python app.py

# 5. Start frontend (terminal 2)
cd frontend
npm start

# 6. Test in browser
# Open http://localhost:3000
# Click "Start Ultra Monitoring"
# Watch it work!
```

**That's it!** CloudVoter should now be running locally and fully functional! 🚀

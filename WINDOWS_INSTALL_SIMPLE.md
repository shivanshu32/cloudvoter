# Windows Installation - Simple Method (No Compilation)

## 🎯 Problem

Both `eventlet` and `gevent` require compilation on Windows, which needs Visual C++ Build Tools.

## ✅ Solution

Use Flask's built-in development server for local testing. No compilation needed!

---

## 🚀 Quick Install (Copy & Paste)

```bash
# 1. Navigate to backend
cd C:\Users\shubh\OneDrive\Desktop\cloudvoter\backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate
venv\Scripts\activate

# 4. Install dependencies (Windows-compatible)
pip install -r requirements-windows.txt

# 5. Install Playwright browsers
playwright install chromium

# 6. Test installation
python -c "from voter_engine import MultiInstanceVoter; print('✅ Backend setup complete!')"

# 7. Start backend
python app.py
```

---

## 📋 What Gets Installed

```
Flask==3.0.0              # Web framework
Flask-CORS==4.0.0         # CORS support
Flask-SocketIO==5.3.5     # WebSocket support
python-socketio==5.10.0   # Socket.IO implementation
playwright==1.40.0        # Browser automation
python-dotenv==1.0.0      # Environment variables
```

**No compilation required!** All packages have pre-built Windows wheels.

---

## 🔍 How It Works

### Production (Linux/Docker)
```python
# Uses gunicorn + eventlet
socketio.run(app, async_mode='eventlet')
```

### Windows Local Testing
```python
# Uses Flask's built-in server
socketio.run(app, allow_unsafe_werkzeug=True)
```

**Same functionality, different server implementation!**

---

## ✅ Expected Output

### During Installation
```
(venv) C:\...\backend> pip install -r requirements-windows.txt

Collecting Flask==3.0.0
  Using cached flask-3.0.0-py3-none-any.whl
Collecting Flask-CORS==4.0.0
  Using cached Flask_Cors-4.0.0-py2.py3-none-any.whl
Collecting Flask-SocketIO==5.3.5
  Using cached Flask_SocketIO-5.3.5-py3-none-any.whl
Collecting python-socketio==5.10.0
  Using cached python_socketio-5.10.0-py3-none-any.whl
Collecting playwright==1.40.0
  Using cached playwright-1.40.0-py3-none-win_amd64.whl
Collecting python-dotenv==1.0.0
  Using cached python_dotenv-1.0.0-py3-none-any.whl
...
Successfully installed Flask-3.0.0 Flask-CORS-4.0.0 ...
```

### When Starting Backend
```
(venv) C:\...\backend> python app.py

✅ Event loop thread started
🚀 Starting CloudVoter Backend Server...
📍 Server will be available at http://localhost:5000
 * Serving Flask app 'app'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.1.x:5000
Press CTRL+C to quit
```

---

## 🧪 Verify Installation

```bash
# Test each component
python -c "from flask import Flask; print('✅ Flask OK')"
python -c "from flask_socketio import SocketIO; print('✅ SocketIO OK')"
python -c "from playwright.async_api import async_playwright; print('✅ Playwright OK')"
python -c "from voter_engine import MultiInstanceVoter; print('✅ Voter Engine OK')"
python -c "from config import BRIGHT_DATA_USERNAME; print('✅ Config OK')"
```

All should print "✅ OK"

---

## 🐛 Troubleshooting

### Problem: "No module named 'flask'"

**Solution:**
```bash
# Make sure venv is activated
venv\Scripts\activate

# You should see (venv) in prompt
(venv) C:\...\backend>
```

### Problem: "playwright not found"

**Solution:**
```bash
# Install Playwright browsers
playwright install chromium
```

### Problem: Port 5000 already in use

**Solution:**
```bash
# Find process using port 5000
netstat -ano | findstr :5000

# Kill the process (replace <PID> with actual number)
taskkill /PID <PID> /F

# Or edit app.py to use different port
# Change: socketio.run(app, port=5001)
```

### Problem: Import errors

**Solution:**
```bash
# Reinstall dependencies
pip uninstall -r requirements-windows.txt -y
pip install -r requirements-windows.txt
```

---

## 📊 Performance Comparison

| Feature | Production (eventlet) | Windows (Werkzeug) |
|---------|----------------------|-------------------|
| **WebSocket** | ✅ Full support | ✅ Full support |
| **Async Tasks** | ✅ Optimized | ✅ Works well |
| **Concurrent Users** | ✅ 1000+ | ✅ 10+ (sufficient for testing) |
| **Browser Automation** | ✅ Full support | ✅ Full support |
| **Voting Logic** | ✅ Same code | ✅ Same code |

**For local testing, Werkzeug is perfect!**

---

## 🎯 Why This Works

### Flask-SocketIO is Smart

Flask-SocketIO automatically detects the available async mode:

```python
# Priority order:
1. eventlet (if installed) - Production
2. gevent (if installed) - Alternative
3. threading (always available) - Fallback for Windows
```

On Windows without eventlet/gevent, it uses threading mode, which works perfectly for local testing!

---

## ✅ Complete Setup Commands

Copy and paste this entire block:

```bash
# Navigate to backend folder
cd C:\Users\shubh\OneDrive\Desktop\cloudvoter\backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements-windows.txt

# Install Playwright browsers
playwright install chromium

# Verify installation
python -c "from voter_engine import MultiInstanceVoter; print('✅ All dependencies installed successfully!')"

# Start backend server
python app.py
```

---

## 🎉 Success Criteria

You'll know it's working when you see:

```
✅ Event loop thread started
🚀 Starting CloudVoter Backend Server...
📍 Server will be available at http://localhost:5000
 * Running on http://127.0.0.1:5000
```

Then open browser to http://localhost:5000/api/health and you should see:

```json
{
  "status": "healthy",
  "timestamp": "2025-01-19T01:16:00",
  "monitoring_active": false
}
```

---

## 📞 Next Steps

After backend is running:

1. ✅ Keep backend terminal open
2. ✅ Open new terminal for frontend
3. ✅ Follow frontend setup in LOCAL_TESTING_GUIDE.md
4. ✅ Test complete application

---

## 🚀 Summary

**Problem:** eventlet/gevent need compilation on Windows

**Solution:** Use Flask's built-in server (no compilation needed)

**Command:**
```bash
pip install -r requirements-windows.txt
```

**Result:** ✅ All dependencies install cleanly!

**Performance:** Perfect for local testing!

Your CloudVoter backend will work flawlessly on Windows! 🎉

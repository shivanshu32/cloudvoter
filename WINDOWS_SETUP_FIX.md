# Windows Setup Fix - Greenlet Compilation Error

## 🐛 Problem

You encountered this error:
```
error: Microsoft Visual C++ 14.0 or greater is required.
ERROR: Failed building wheel for greenlet
```

This happens because `eventlet` (used for production deployment) requires compilation on Windows.

---

## ✅ Solution: Use Windows-Compatible Requirements

### Quick Fix (Recommended)

```bash
# In backend folder with venv activated
pip install -r requirements-windows.txt
```

This installs Windows-compatible packages without needing Visual C++ Build Tools.

---

## 📝 Step-by-Step Fix

### 1. Clean Previous Installation

```bash
# Deactivate venv if active
deactivate

# Delete venv folder
cd C:\Users\shubh\OneDrive\Desktop\cloudvoter\backend
rmdir /s /q venv
```

### 2. Create Fresh Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

```bash
venv\Scripts\activate
```

### 4. Install Windows Requirements

```bash
pip install -r requirements-windows.txt
```

### 5. Install Playwright Browsers

```bash
playwright install chromium
```

### 6. Verify Installation

```bash
python -c "from voter_engine import MultiInstanceVoter; print('✅ Setup complete!')"
```

---

## 🎯 What Changed?

### Original requirements.txt (Production)
```
gunicorn==21.2.0    # Linux-only
eventlet==0.33.3    # Needs compilation on Windows
```

### requirements-windows.txt (Local Testing)
```
gevent==24.2.1           # Windows-compatible
gevent-websocket==0.10.1 # WebSocket support
```

**Both work the same way, just different implementations!**

---

## 🚀 Alternative: Install Build Tools (Not Recommended)

If you really want to use the original requirements.txt:

### Option 1: Install Visual Studio Build Tools

1. Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Install "Desktop development with C++"
3. Restart computer
4. Run: `pip install -r requirements.txt`

**Note:** This is ~6GB download and not necessary for local testing!

### Option 2: Use Pre-built Wheels

```bash
pip install --only-binary :all: eventlet
```

---

## ✅ Recommended Approach

**For Windows local testing:**
```bash
pip install -r requirements-windows.txt
```

**For Linux/Docker deployment:**
```bash
pip install -r requirements.txt
```

The Dockerfile already uses the correct requirements.txt for Linux!

---

## 🧪 Test After Fix

```bash
# 1. Activate venv
venv\Scripts\activate

# 2. Start backend
python app.py

# Expected output:
# ✅ Event loop thread started
# * Running on http://127.0.0.1:5000
```

---

## 📊 Package Comparison

| Package | Production (Linux) | Windows Testing |
|---------|-------------------|-----------------|
| Web Server | gunicorn | Flask dev server |
| Async | eventlet | gevent |
| WebSocket | Flask-SocketIO | Flask-SocketIO |
| Browser | Playwright | Playwright |

**All core functionality works the same!**

---

## 🎉 Summary

**Problem:** `eventlet` needs Visual C++ compiler on Windows

**Solution:** Use `requirements-windows.txt` instead

**Command:**
```bash
pip install -r requirements-windows.txt
```

**Result:** ✅ All dependencies install without compilation!

---

## 📞 Next Steps

After successful installation:

1. ✅ Install Playwright: `playwright install chromium`
2. ✅ Start backend: `python app.py`
3. ✅ Continue with frontend setup
4. ✅ Follow LOCAL_TESTING_GUIDE.md

Your CloudVoter will work perfectly on Windows! 🚀

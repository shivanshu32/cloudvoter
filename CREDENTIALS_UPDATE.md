# Updating Bright Data Credentials in CloudVoter

## 📝 Overview

CloudVoter now loads Bright Data credentials from `backend/config.py`, making it easy to update when your credentials change.

---

## 🔑 How It Works

### Configuration Flow

```
1. Credentials stored in backend/config.py
   ↓
2. Backend loads from config.py on startup
   ↓
3. Frontend fetches config via /api/config
   ↓
4. UI displays credentials (pre-filled)
   ↓
5. User can override if needed
```

---

## 🛠️ Method 1: Update config.py (Recommended)

### Step 1: Edit config.py

Open `backend/config.py` and update the credentials:

```python
# Bright Data Proxy Credentials
# Update these when credentials change
BRIGHT_DATA_USERNAME = "hl_47ba96ab"  # ← Change this
BRIGHT_DATA_PASSWORD = "tcupn0cw7pbz"  # ← Change this
```

### Step 2: Restart Backend

**Local Development:**
```bash
# Stop backend (Ctrl+C)
# Start again
cd backend
python app.py
```

**Docker Deployment:**
```bash
docker-compose restart cloudvoter
```

**DigitalOcean:**
```bash
ssh root@YOUR_DROPLET_IP
cd cloudvoter
docker-compose restart
```

### Step 3: Verify

1. Open web control panel
2. Credentials should be pre-filled with new values
3. Click "Start Ultra Monitoring" to test

---

## 🌐 Method 2: Update via Web UI

You can also update credentials directly in the web interface:

### Step 1: Open Control Panel

Navigate to your CloudVoter control panel

### Step 2: Update Fields

1. Find the configuration section
2. Update **Bright Data Username** field
3. Update **Bright Data Password** field

### Step 3: Start Monitoring

Click "Start Ultra Monitoring" - new credentials will be used

**Note:** This method only updates for the current session. To make it permanent, update `config.py`.

---

## 🔄 Method 3: Environment Variables

For production deployments, you can use environment variables:

### Step 1: Update .env File

```bash
# Edit .env file
nano .env

# Add or update:
BRIGHT_DATA_USERNAME=your_new_username
BRIGHT_DATA_PASSWORD=your_new_password
```

### Step 2: Restart

```bash
docker-compose restart
```

### Priority Order

CloudVoter checks credentials in this order:
1. Environment variables (`.env` file)
2. `config.py` defaults
3. User input in web UI

---

## 📋 Complete Update Example

### Scenario: Your Bright Data credentials changed

**Old credentials:**
```
Username: hl_47ba96ab
Password: tcupn0cw7pbz
```

**New credentials:**
```
Username: hl_98xy76cd
Password: newpass123xyz
```

### Update Steps:

#### 1. Update config.py

```python
# backend/config.py
BRIGHT_DATA_USERNAME = "hl_98xy76cd"      # Updated
BRIGHT_DATA_PASSWORD = "newpass123xyz"    # Updated
```

#### 2. Restart Backend

**If running locally:**
```bash
# Stop backend (Ctrl+C in terminal)
cd backend
python app.py
```

**If deployed with Docker:**
```bash
docker-compose restart cloudvoter
```

#### 3. Verify in UI

1. Open `http://YOUR_SERVER_IP`
2. Check configuration section
3. Should show new credentials
4. Test by clicking "Start Ultra Monitoring"

---

## 🔍 Verification Checklist

After updating credentials:

- [ ] `config.py` has new values
- [ ] Backend restarted
- [ ] Web UI shows new credentials
- [ ] "Start Ultra Monitoring" works
- [ ] Instances launch successfully
- [ ] Proxy connection successful

---

## 🚨 Troubleshooting

### Problem: Old credentials still showing

**Cause:** Backend not restarted

**Solution:**
```bash
# Restart backend
docker-compose restart cloudvoter

# Or if local
# Stop and start python app.py
```

### Problem: "Authentication failed" error

**Cause:** Incorrect credentials

**Solution:**
1. Verify credentials in Bright Data dashboard
2. Copy exact username and password
3. Update `config.py`
4. Restart backend

### Problem: UI shows empty credentials

**Cause:** Backend not loading config properly

**Solution:**
```bash
# Check backend logs
docker-compose logs cloudvoter

# Or if local
# Check terminal output

# Verify config.py syntax
python -c "from backend.config import BRIGHT_DATA_USERNAME; print(BRIGHT_DATA_USERNAME)"
```

### Problem: Changes not persisting

**Cause:** Only updated in UI, not in config.py

**Solution:**
- Update `config.py` file
- Restart backend
- Changes will persist across restarts

---

## 📝 Best Practices

### 1. Always Update config.py

For permanent changes, always update `config.py`:
```python
BRIGHT_DATA_USERNAME = "your_username"
BRIGHT_DATA_PASSWORD = "your_password"
```

### 2. Use Environment Variables in Production

For production deployments:
```bash
# .env file
BRIGHT_DATA_USERNAME=production_username
BRIGHT_DATA_PASSWORD=production_password
```

### 3. Test After Update

Always test after updating:
1. Restart backend
2. Open web UI
3. Verify credentials displayed
4. Click "Start Ultra Monitoring"
5. Check logs for successful connection

### 4. Keep Credentials Secure

- Don't commit credentials to git
- Use `.env` for sensitive data
- `.env` is in `.gitignore` by default

### 5. Document Changes

Keep track of when credentials change:
```python
# config.py
# Credentials updated: 2025-01-19
BRIGHT_DATA_USERNAME = "hl_98xy76cd"
BRIGHT_DATA_PASSWORD = "newpass123xyz"
```

---

## 🔐 Security Notes

### config.py Security

**Good:**
- ✅ Credentials in `config.py` (not committed to git if in .gitignore)
- ✅ Easy to update
- ✅ Version controlled (if private repo)

**Better:**
- ✅ Use environment variables (`.env` file)
- ✅ Never commit `.env` to git
- ✅ Different credentials per environment

### .gitignore Check

Verify `.gitignore` includes:
```
.env
.env.local
*.log
brightdata_session_data/
```

---

## 📊 Credential Update Workflow

### Development Environment

```
1. Update config.py
2. Restart: python app.py
3. Test in browser
```

### Production Environment

```
1. SSH into server
2. Edit config.py or .env
3. Restart: docker-compose restart
4. Verify in browser
```

### Multi-Environment Setup

```
Development:
- config.py: dev_username / dev_password

Production:
- .env: prod_username / prod_password
- Overrides config.py
```

---

## 🎯 Quick Reference

### Update Credentials

```bash
# 1. Edit config
nano backend/config.py

# 2. Update values
BRIGHT_DATA_USERNAME = "new_username"
BRIGHT_DATA_PASSWORD = "new_password"

# 3. Restart
docker-compose restart cloudvoter

# 4. Verify
curl http://localhost:5000/api/config
```

### Check Current Credentials

```bash
# Via API
curl http://localhost:5000/api/config

# Via config.py
cat backend/config.py | grep BRIGHT_DATA
```

### Test Connection

```bash
# Start monitoring and check logs
docker-compose logs -f cloudvoter | grep "Bright Data"
```

---

## 📞 Related Files

- **`backend/config.py`** - Main configuration file
- **`.env.example`** - Environment variables template
- **`.env`** - Your environment variables (create from .env.example)
- **`backend/app.py`** - Loads configuration
- **`frontend/src/App.jsx`** - Displays configuration

---

## ✅ Summary

**To update Bright Data credentials:**

1. **Edit `backend/config.py`:**
   ```python
   BRIGHT_DATA_USERNAME = "new_username"
   BRIGHT_DATA_PASSWORD = "new_password"
   ```

2. **Restart backend:**
   ```bash
   docker-compose restart cloudvoter
   ```

3. **Verify in web UI:**
   - Open control panel
   - Check credentials are pre-filled
   - Test "Start Ultra Monitoring"

**That's it!** Credentials are now updated and will be used for all voting operations.

---

## 🎉 Benefits of This Approach

- ✅ **Centralized**: All credentials in one place (`config.py`)
- ✅ **Easy to update**: Just edit one file
- ✅ **Automatic loading**: Frontend loads from backend
- ✅ **Consistent**: Same credentials everywhere
- ✅ **Version controlled**: Track changes (if private repo)
- ✅ **Flexible**: Can override with environment variables

Just like the original `gui_control_panel.py`, but easier to manage!

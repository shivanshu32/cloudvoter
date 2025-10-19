# CloudVoter Backend Deployment with PM2

## 🎯 Overview

Deploy CloudVoter backend using PM2 process manager - simpler and lighter than Docker.

**Advantages:**
- ✅ Lightweight (no Docker overhead)
- ✅ Auto-restart on crashes
- ✅ Easy log management
- ✅ Simple start/stop/restart
- ✅ Startup on boot

---

## 📋 Prerequisites

- [x] CloudVoter folder uploaded to DigitalOcean
- [x] `backend/` folder with Python files
- [x] `brightdata_session_data/` folder with sessions
- [x] `voting_logs.csv` file

---

## 🚀 Step 1: Connect to Droplet

```bash
ssh root@YOUR_DROPLET_IP
```

---

## 📂 Step 2: Verify Files

```bash
cd /root/cloudvoter
ls -la
```

**You should see:**
```
backend/
brightdata_session_data/
voting_logs.csv
```

**Check backend files:**
```bash
ls -la backend/
```

**Should show:**
```
app.py
voter_engine.py
config.py
vote_logger.py
requirements.txt
```

---

## 🐍 Step 3: Install Python Dependencies (5 min)

### 3.1 Update System

```bash
apt-get update
apt-get upgrade -y
```

### 3.2 Install Python 3.11

```bash
# Add deadsnakes PPA for Python 3.11
apt-get install -y software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update

# Install Python 3.11
apt-get install -y python3.11 python3.11-venv python3.11-dev
```

### 3.3 Create Virtual Environment

```bash
cd /root/cloudvoter/backend
python3.11 -m venv venv
```

### 3.4 Activate Virtual Environment

```bash
source venv/bin/activate
```

**You should see `(venv)` in your prompt**

### 3.5 Install Python Packages

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Expected output:**
```
Installing collected packages: Flask, Flask-CORS, Flask-SocketIO, playwright, ...
Successfully installed ...
```

### 3.6 Install Playwright Browsers

```bash
playwright install chromium
playwright install-deps chromium
```

**This downloads Chromium (~300MB)**

---

## ⚙️ Step 4: Configure Environment (2 min)

### 4.1 Edit config.py

```bash
nano config.py
```

**Update credentials:**
```python
# Bright Data Configuration
BRIGHT_DATA_USERNAME = "hl_47ba96ab"
BRIGHT_DATA_PASSWORD = "your-actual-password-here"

# Target URL
TARGET_URL = "https://www.cutebabyvote.com/vote/..."

# Other settings
HEADLESS_MODE = True
DATA_SAVER_MODE = True
```

**Save and exit:**
- Press `Ctrl+X`
- Press `Y`
- Press `Enter`

### 4.2 Verify Configuration

```bash
python3 -c "from config import BRIGHT_DATA_USERNAME; print('✅ Config loaded:', BRIGHT_DATA_USERNAME)"
```

---

## 📦 Step 5: Install Node.js and PM2 (3 min)

### 5.1 Install Node.js

```bash
# Install Node.js 18.x
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs
```

**Verify installation:**
```bash
node --version
npm --version
```

### 5.2 Install PM2 Globally

```bash
npm install -g pm2
```

**Verify PM2:**
```bash
pm2 --version
```

---

## 🎮 Step 6: Create PM2 Configuration (2 min)

### 6.1 Create PM2 Ecosystem File

```bash
cd /root/cloudvoter/backend
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
    env: {
      PYTHONUNBUFFERED: '1',
      PYTHONPATH: '/root/cloudvoter/backend'
    },
    error_file: '/root/cloudvoter/backend/logs/error.log',
    out_file: '/root/cloudvoter/backend/logs/output.log',
    log_file: '/root/cloudvoter/backend/logs/combined.log',
    time: true,
    merge_logs: true
  }]
};
EOF
```

### 6.2 Create Logs Directory

```bash
mkdir -p logs
```

---

## ▶️ Step 7: Start Backend with PM2 (1 min)

### 7.1 Start Application

```bash
pm2 start ecosystem.config.js
```

**Expected output:**
```
[PM2] Starting /root/cloudvoter/backend/venv/bin/python in fork_mode (1 instance)
[PM2] Done.
┌─────┬──────────────────────┬─────────────┬─────────┬─────────┬──────────┐
│ id  │ name                 │ mode        │ ↺       │ status  │ cpu      │
├─────┼──────────────────────┼─────────────┼─────────┼─────────┼──────────┤
│ 0   │ cloudvoter-backend   │ fork        │ 0       │ online  │ 0%       │
└─────┴──────────────────────┴─────────────┴─────────┴─────────┴──────────┘
```

### 7.2 Save PM2 Process List

```bash
pm2 save
```

### 7.3 Setup PM2 Startup (Auto-start on Boot)

```bash
pm2 startup
```

**Copy and run the command it outputs**, example:
```bash
sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u root --hp /root
```

Then save again:
```bash
pm2 save
```

---

## ✅ Step 8: Verify Backend is Running (2 min)

### 8.1 Check PM2 Status

```bash
pm2 status
```

**Should show:**
```
┌─────┬──────────────────────┬─────────────┬─────────┬─────────┬──────────┐
│ id  │ name                 │ mode        │ ↺       │ status  │ cpu      │
├─────┼──────────────────────┼─────────────┼─────────┼─────────┼──────────┤
│ 0   │ cloudvoter-backend   │ fork        │ 0       │ online  │ 5%       │
└─────┴──────────────────────┴─────────────┴─────────┴─────────┴──────────┘
```

**Status should be `online`**

### 8.2 View Logs

```bash
pm2 logs cloudvoter-backend
```

**Look for:**
```
✅ Event loop thread started
✅ Configuration loaded
* Running on http://0.0.0.0:5000
```

**Press `Ctrl+C` to exit**

### 8.3 Test Health Endpoint

```bash
curl http://localhost:5000/api/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-19T00:00:00",
  "monitoring_active": false
}
```

### 8.4 Check Session Data

```bash
ls -la /root/cloudvoter/backend/brightdata_session_data/
```

**Should show all your instances**

### 8.5 Get Public IP

```bash
curl ifconfig.me
```

**Note this IP for API access**

---

## 🔒 Step 9: Configure Firewall (2 min)

```bash
# Allow SSH (IMPORTANT!)
ufw allow 22/tcp

# Allow backend API
ufw allow 5000/tcp

# Enable firewall
ufw enable
```

**Type `y` when prompted**

**Verify:**
```bash
ufw status
```

**Expected:**
```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
5000/tcp                   ALLOW       Anywhere
```

---

## 🧪 Step 10: Test from Local Machine (2 min)

### From Your Local PowerShell

```powershell
# Health check
curl http://YOUR_DROPLET_IP:5000/api/health

# Get configuration
curl http://YOUR_DROPLET_IP:5000/api/config

# Start monitoring
curl -X POST http://YOUR_DROPLET_IP:5000/api/start-monitoring

# Check status
curl http://YOUR_DROPLET_IP:5000/api/status
```

**Expected responses:**
```json
{"success": true, "message": "Ultra monitoring started"}
```

---

## 📊 PM2 Management Commands

### View Status
```bash
pm2 status
```

### View Logs (Real-time)
```bash
# All logs
pm2 logs cloudvoter-backend

# Last 100 lines
pm2 logs cloudvoter-backend --lines 100

# Only errors
pm2 logs cloudvoter-backend --err

# Only output
pm2 logs cloudvoter-backend --out
```

### Restart Backend
```bash
pm2 restart cloudvoter-backend
```

### Stop Backend
```bash
pm2 stop cloudvoter-backend
```

### Start Backend
```bash
pm2 start cloudvoter-backend
```

### Delete from PM2
```bash
pm2 delete cloudvoter-backend
```

### Monitor Resources
```bash
pm2 monit
```

**Press `Ctrl+C` to exit**

### Show Detailed Info
```bash
pm2 show cloudvoter-backend
```

### Flush Logs
```bash
pm2 flush cloudvoter-backend
```

---

## 💾 Step 11: Setup Backups (3 min)

### 11.1 Create Backup Script

```bash
cat > /root/cloudvoter/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/root/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="cloudvoter_backup_${DATE}.tar.gz"

mkdir -p $BACKUP_DIR

cd /root/cloudvoter
tar -czf "${BACKUP_DIR}/${BACKUP_FILE}" \
    backend/brightdata_session_data/ \
    backend/voting_logs.csv \
    backend/cloudvoter.log \
    backend/logs/

echo "✅ Backup created: ${BACKUP_FILE}"
ls -lh "${BACKUP_DIR}/${BACKUP_FILE}"

# Keep only last 7 backups
cd $BACKUP_DIR
ls -t cloudvoter_backup_*.tar.gz | tail -n +8 | xargs -r rm
echo "✅ Old backups cleaned (keeping last 7)"
EOF

chmod +x backup.sh
```

### 11.2 Test Backup

```bash
./backup.sh
```

### 11.3 Schedule Daily Backups

```bash
# Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /root/cloudvoter/backup.sh >> /root/cloudvoter/backup.log 2>&1") | crontab -

# Verify
crontab -l
```

---

## 🔄 Update Session Data (Future Updates)

### From Local Machine

```powershell
# Upload updated session data
scp -r brightdata_session_data root@YOUR_DROPLET_IP:/root/cloudvoter/backend/

# Upload updated logs
scp voting_logs.csv root@YOUR_DROPLET_IP:/root/cloudvoter/backend/
```

### On Droplet

```bash
cd /root/cloudvoter/backend
pm2 restart cloudvoter-backend
```

---

## 🔄 Update Backend Code (Future Updates)

### If You Update Python Files

```bash
cd /root/cloudvoter/backend

# Backup current code
cp app.py app.py.backup
cp voter_engine.py voter_engine.py.backup

# Upload new files from local machine or edit directly
# Then restart:
pm2 restart cloudvoter-backend

# View logs to verify
pm2 logs cloudvoter-backend
```

---

## 🐛 Troubleshooting

### Problem: PM2 shows "errored" status

```bash
# Check logs
pm2 logs cloudvoter-backend --err

# Check if Python dependencies are installed
source /root/cloudvoter/backend/venv/bin/activate
python -c "import flask; print('✅ Flask installed')"

# Restart
pm2 restart cloudvoter-backend
```

### Problem: "Module not found" errors

```bash
# Reinstall dependencies
cd /root/cloudvoter/backend
source venv/bin/activate
pip install -r requirements.txt

# Restart
pm2 restart cloudvoter-backend
```

### Problem: Playwright not working

```bash
# Reinstall Playwright browsers
source /root/cloudvoter/backend/venv/bin/activate
playwright install chromium
playwright install-deps chromium

# Restart
pm2 restart cloudvoter-backend
```

### Problem: Can't access API from local machine

```bash
# Check if backend is running
pm2 status

# Check if port is listening
netstat -tulpn | grep :5000

# Check firewall
ufw status

# Test locally first
curl http://localhost:5000/api/health
```

### Problem: Backend crashes frequently

```bash
# Check error logs
pm2 logs cloudvoter-backend --err

# Check memory usage
pm2 monit

# Increase memory limit in ecosystem.config.js
nano ecosystem.config.js
# Change: max_memory_restart: '4G'

# Reload PM2
pm2 reload cloudvoter-backend
```

### Problem: Session data not found

```bash
# Check if data exists
ls -la /root/cloudvoter/backend/brightdata_session_data/

# Check Python path
cd /root/cloudvoter/backend
source venv/bin/activate
python -c "import os; print(os.path.exists('brightdata_session_data'))"

# Verify in logs
pm2 logs cloudvoter-backend | grep -i session
```

### Problem: Port 5000 already in use

```bash
# Find process using port 5000
netstat -tulpn | grep :5000

# Kill the process
kill -9 <PID>

# Or change port in app.py
nano app.py
# Change: app.run(host='0.0.0.0', port=5001)

# Update firewall
ufw allow 5001/tcp

# Restart
pm2 restart cloudvoter-backend
```

---

## 📈 Performance Optimization

### Monitor Resource Usage

```bash
# PM2 monitoring
pm2 monit

# System resources
htop

# Memory usage
free -h

# Disk usage
df -h
```

### Optimize Configuration

```bash
nano /root/cloudvoter/backend/config.py
```

**Set:**
```python
HEADLESS_MODE = True
DATA_SAVER_MODE = True
MAX_CONCURRENT_INSTANCES = 3  # Adjust based on RAM
```

**Restart:**
```bash
pm2 restart cloudvoter-backend
```

### Increase PM2 Memory Limit

```bash
nano ecosystem.config.js
```

**Change:**
```javascript
max_memory_restart: '4G',  // Increase if you have more RAM
```

**Reload:**
```bash
pm2 reload cloudvoter-backend
```

---

## 🌐 API Endpoints Reference

```bash
# Health check
GET http://YOUR_IP:5000/api/health

# Get configuration
GET http://YOUR_IP:5000/api/config

# Start monitoring
POST http://YOUR_IP:5000/api/start-monitoring

# Stop monitoring
POST http://YOUR_IP:5000/api/stop-monitoring

# Get status
GET http://YOUR_IP:5000/api/status

# Get statistics
GET http://YOUR_IP:5000/api/stats

# Launch instance
POST http://YOUR_IP:5000/api/launch-instance

# Get active instances
GET http://YOUR_IP:5000/api/instances
```

---

## ✅ Deployment Checklist

```
□ Connected to DigitalOcean droplet
□ Verified cloudvoter folder exists
□ Verified backend files exist
□ Verified session data exists
□ Verified voting logs exist
□ Python 3.11 installed
□ Virtual environment created
□ Python dependencies installed
□ Playwright browsers installed
□ config.py configured with credentials
□ Node.js and npm installed
□ PM2 installed globally
□ PM2 ecosystem.config.js created
□ Backend started with PM2
□ PM2 process saved
□ PM2 startup configured
□ Backend status is "online"
□ Health endpoint returns 200 OK
□ Firewall configured (ports 22, 5000)
□ API accessible from local machine
□ Backup script created
□ Daily backups scheduled
```

---

## 📞 Quick Commands Reference

| Task | Command |
|------|---------|
| **Connect** | `ssh root@YOUR_IP` |
| **Status** | `pm2 status` |
| **View logs** | `pm2 logs cloudvoter-backend` |
| **Restart** | `pm2 restart cloudvoter-backend` |
| **Stop** | `pm2 stop cloudvoter-backend` |
| **Start** | `pm2 start cloudvoter-backend` |
| **Monitor** | `pm2 monit` |
| **Backup** | `./backup.sh` |
| **Test API** | `curl http://YOUR_IP:5000/api/health` |

---

## 🎉 Success!

Your CloudVoter backend is now running with PM2!

**Backend API:**
```
http://YOUR_DROPLET_IP:5000
```

**Health Check:**
```
http://YOUR_DROPLET_IP:5000/api/health
```

**Start Voting:**
```bash
curl -X POST http://YOUR_DROPLET_IP:5000/api/start-monitoring
```

**View Logs:**
```bash
pm2 logs cloudvoter-backend
```

**Monitor Resources:**
```bash
pm2 monit
```

---

## 🔄 Daily Operations

### Morning Check
```bash
pm2 status
pm2 logs cloudvoter-backend --lines 50
```

### Restart if Needed
```bash
pm2 restart cloudvoter-backend
```

### Check Backups
```bash
ls -lh /root/backups/
```

### Download Latest Backup
```powershell
# From local machine
scp root@YOUR_IP:/root/backups/cloudvoter_backup_*.tar.gz C:\Users\shubh\Desktop\
```

---

## 🚀 Advantages of PM2

✅ **Lightweight** - No Docker overhead  
✅ **Auto-restart** - Crashes handled automatically  
✅ **Easy logs** - `pm2 logs` for instant access  
✅ **Resource monitoring** - `pm2 monit` built-in  
✅ **Startup on boot** - Survives server restarts  
✅ **Simple commands** - Easy to manage  
✅ **Fast deployment** - No image building  

---

**Total Deployment Time: ~20 minutes**

**Need help?** Check the troubleshooting section above!

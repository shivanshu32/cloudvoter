# CloudVoter Backend-Only Deployment to DigitalOcean

## 🎯 Overview

Deploy CloudVoter backend with session data and voting logs to DigitalOcean.
**No frontend required** - Backend runs standalone with Flask API and SocketIO.

---

## 📋 What Gets Deployed

✅ **Backend Python application** (`app.py`, `voter_engine.py`, `config.py`)  
✅ **Session data** (`brightdata_session_data/` folder with all instances)  
✅ **Voting logs** (`voting_logs.csv`)  
✅ **Dependencies** (Flask, Playwright, etc.)  
✅ **Docker container** (automated setup)  

---

## 🚀 Step 1: Create DigitalOcean Droplet

### 1.1 Create Droplet

1. Go to https://cloud.digitalocean.com/
2. Click **"Create"** → **"Droplets"**
3. Configuration:
   - **Image**: Ubuntu 22.04 LTS
   - **Plan**: Basic
   - **RAM**: 2GB minimum (4GB recommended)
   - **Price**: $12-24/month
   - **Region**: Choose closest to target
   - **Authentication**: SSH key or password
   - **Hostname**: `cloudvoter-backend`

4. Click **"Create Droplet"**
5. **Note your IP**: `___.___.___.___`

---

## 📦 Step 2: Prepare Backend Package

### 2.1 Create Preparation Script

Create `prepare_backend_deployment.bat`:

```batch
@echo off
echo ========================================
echo CloudVoter Backend Deployment Package
echo ========================================
echo.

REM Clean up old package
if exist backend_deploy (
    rmdir /s /q backend_deploy
)

echo Creating deployment package...
mkdir backend_deploy

echo.
echo [1/5] Copying backend files...
xcopy backend\*.py backend_deploy\ /Y >nul
xcopy backend\requirements*.txt backend_deploy\ /Y >nul
echo ✅ Backend files copied

echo.
echo [2/5] Copying session data...
if exist brightdata_session_data (
    xcopy brightdata_session_data backend_deploy\brightdata_session_data\ /E /I /Y >nul
    echo ✅ Session data copied
) else (
    echo ⚠️  WARNING: brightdata_session_data not found!
)

echo.
echo [3/5] Copying voting logs...
if exist voting_logs.csv (
    copy voting_logs.csv backend_deploy\ /Y >nul
    echo ✅ Voting logs copied
) else (
    echo Creating empty voting logs...
    echo timestamp,instance_id,vote_status,ip_address,session_status > backend_deploy\voting_logs.csv
    echo ✅ Empty voting logs created
)

echo.
echo [4/5] Creating deployment files...

REM Create Dockerfile
(
echo FROM python:3.11-slim
echo.
echo WORKDIR /app
echo.
echo # Install system dependencies
echo RUN apt-get update ^&^& apt-get install -y \
echo     wget \
echo     gnupg \
echo     ca-certificates \
echo     fonts-liberation \
echo     libasound2 \
echo     libatk-bridge2.0-0 \
echo     libatk1.0-0 \
echo     libatspi2.0-0 \
echo     libcups2 \
echo     libdbus-1-3 \
echo     libdrm2 \
echo     libgbm1 \
echo     libgtk-3-0 \
echo     libnspr4 \
echo     libnss3 \
echo     libwayland-client0 \
echo     libxcomposite1 \
echo     libxdamage1 \
echo     libxfixes3 \
echo     libxkbcommon0 \
echo     libxrandr2 \
echo     xdg-utils \
echo     ^&^& rm -rf /var/lib/apt/lists/*
echo.
echo # Copy requirements
echo COPY requirements.txt .
echo RUN pip install --no-cache-dir -r requirements.txt
echo.
echo # Install Playwright browsers
echo RUN playwright install chromium
echo RUN playwright install-deps chromium
echo.
echo # Copy application files
echo COPY *.py ./
echo COPY brightdata_session_data/ ./brightdata_session_data/
echo COPY voting_logs.csv ./
echo.
echo # Create necessary directories
echo RUN mkdir -p templates
echo.
echo # Expose port
echo EXPOSE 5000
echo.
echo # Run application
echo CMD ["python", "app.py"]
) > backend_deploy\Dockerfile
echo ✅ Dockerfile created

REM Create docker-compose.yml
(
echo version: '3.8'
echo.
echo services:
echo   cloudvoter-backend:
echo     build: .
echo     container_name: cloudvoter-backend
echo     ports:
echo       - "5000:5000"
echo     volumes:
echo       - ./brightdata_session_data:/app/brightdata_session_data
echo       - ./voting_logs.csv:/app/voting_logs.csv
echo       - ./cloudvoter.log:/app/cloudvoter.log
echo     environment:
echo       - PYTHONUNBUFFERED=1
echo     restart: unless-stopped
echo     deploy:
echo       resources:
echo         limits:
echo           cpus: '2'
echo           memory: 3G
) > backend_deploy\docker-compose.yml
echo ✅ docker-compose.yml created

REM Create deploy.sh
(
echo #!/bin/bash
echo set -e
echo.
echo echo "=========================================="
echo echo "CloudVoter Backend Deployment"
echo echo "=========================================="
echo echo ""
echo.
echo echo "Updating system packages..."
echo apt-get update
echo apt-get upgrade -y
echo.
echo echo "Installing Docker..."
echo if ! command -v docker ^&^>/dev/null; then
echo     curl -fsSL https://get.docker.com -o get-docker.sh
echo     sh get-docker.sh
echo     rm get-docker.sh
echo     echo "✅ Docker installed"
echo else
echo     echo "✅ Docker already installed"
echo fi
echo.
echo echo "Installing Docker Compose..."
echo if ! command -v docker-compose ^&^>/dev/null; then
echo     curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
echo     chmod +x /usr/local/bin/docker-compose
echo     echo "✅ Docker Compose installed"
echo else
echo     echo "✅ Docker Compose already installed"
echo fi
echo.
echo echo "Building Docker image..."
echo docker-compose build
echo.
echo echo "Starting CloudVoter backend..."
echo docker-compose up -d
echo.
echo echo "=========================================="
echo echo "✅ CloudVoter Backend is running!"
echo echo "=========================================="
echo echo ""
echo echo "Backend API: http://$(curl -s ifconfig.me):5000"
echo echo "Health check: http://$(curl -s ifconfig.me):5000/api/health"
echo echo ""
echo echo "View logs: docker-compose logs -f"
echo echo "Stop: docker-compose down"
echo echo "Restart: docker-compose restart"
echo echo ""
) > backend_deploy\deploy.sh
echo ✅ deploy.sh created

REM Create .env template
(
echo # Bright Data Credentials
echo BRIGHT_DATA_USERNAME=hl_47ba96ab
echo BRIGHT_DATA_PASSWORD=your-password-here
echo.
echo # Flask Configuration
echo SECRET_KEY=change-this-to-secure-random-key
echo.
echo # Voting Configuration
echo TARGET_URL=https://www.cutebabyvote.com/vote/...
) > backend_deploy\.env
echo ✅ .env template created

echo.
echo [5/5] Creating archive...
cd backend_deploy
where tar >nul 2>&1
if %errorlevel% equ 0 (
    tar -czf ..\cloudvoter-backend.tar.gz *
    echo ✅ Archive created: cloudvoter-backend.tar.gz
) else (
    echo ⚠️  tar not found - create archive manually
)
cd ..

echo.
echo ========================================
echo ✅ Backend Package Ready!
echo ========================================
echo.
echo Package: backend_deploy\
echo Archive: cloudvoter-backend.tar.gz
echo.
echo 📋 NEXT STEPS:
echo.
echo 1. Edit backend_deploy\.env:
echo    - Set BRIGHT_DATA_PASSWORD
echo    - Generate SECRET_KEY: python -c "import secrets; print(secrets.token_hex(32))"
echo.
echo 2. Upload to DigitalOcean:
echo    scp cloudvoter-backend.tar.gz root@YOUR_IP:/root/
echo.
echo 3. Deploy on server (see BACKEND_ONLY_DEPLOYMENT.md)
echo.

REM Show statistics
echo 📊 Package Statistics:
if exist backend_deploy\brightdata_session_data (
    dir backend_deploy\brightdata_session_data /b | find /c /v ""
    echo    session instances found
)
if exist backend_deploy\voting_logs.csv (
    for %%A in (backend_deploy\voting_logs.csv) do echo    %%~zA bytes in voting_logs.csv
)
echo.
pause
```

Save as `prepare_backend_deployment.bat` in cloudvoter folder.

### 2.2 Run Preparation Script

```powershell
cd C:\Users\shubh\OneDrive\Desktop\cloudvoter
prepare_backend_deployment.bat
```

### 2.3 Configure Environment

Edit `backend_deploy\.env`:

```env
BRIGHT_DATA_USERNAME=hl_47ba96ab
BRIGHT_DATA_PASSWORD=your-actual-password-here
SECRET_KEY=<generate-secure-key>
TARGET_URL=https://www.cutebabyvote.com/vote/...
```

**Generate SECRET_KEY:**
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 📤 Step 3: Upload to DigitalOcean

### 3.1 Upload Package

```powershell
scp cloudvoter-backend.tar.gz root@YOUR_DROPLET_IP:/root/
```

**Example:**
```powershell
scp cloudvoter-backend.tar.gz root@165.227.123.45:/root/
```

**Enter password when prompted**

---

## 🖥️ Step 4: Deploy on Server

### 4.1 Connect to Droplet

```powershell
ssh root@YOUR_DROPLET_IP
```

### 4.2 Extract Files

```bash
cd /root
mkdir cloudvoter-backend
cd cloudvoter-backend
tar -xzf ../cloudvoter-backend.tar.gz
ls -la
```

**You should see:**
```
app.py
voter_engine.py
config.py
vote_logger.py
requirements.txt
Dockerfile
docker-compose.yml
deploy.sh
.env
brightdata_session_data/
voting_logs.csv
```

### 4.3 Verify Session Data

```bash
ls -la brightdata_session_data/
```

**Should show:**
```
instance_1/
instance_2/
instance_3/
...
```

### 4.4 Run Deployment

```bash
chmod +x deploy.sh
./deploy.sh
```

**This will:**
1. Update system packages
2. Install Docker
3. Install Docker Compose
4. Build Docker image
5. Start backend container

**Takes 5-10 minutes**

---

## ✅ Step 5: Verify Deployment

### 5.1 Check Container Status

```bash
docker-compose ps
```

**Expected:**
```
NAME                    STATUS              PORTS
cloudvoter-backend      Up 2 minutes        0.0.0.0:5000->5000/tcp
```

### 5.2 View Logs

```bash
docker-compose logs -f cloudvoter-backend
```

**Look for:**
```
✅ Event loop thread started
✅ Configuration loaded
* Running on http://0.0.0.0:5000
```

**Press Ctrl+C to exit**

### 5.3 Test Health Endpoint

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

### 5.4 Verify Session Data

```bash
docker-compose exec cloudvoter-backend ls -la /app/brightdata_session_data/
```

**Should show all your instances**

### 5.5 Get Public IP

```bash
curl ifconfig.me
```

**Note this IP for API access**

---

## 🔒 Step 6: Configure Firewall

```bash
# Allow SSH (IMPORTANT!)
ufw allow 22/tcp

# Allow backend API
ufw allow 5000/tcp

# Enable firewall
ufw enable
```

**Type 'y' when prompted**

**Verify:**
```bash
ufw status
```

---

## 🧪 Step 7: Test Backend API

### From Your Local Machine

**Test health endpoint:**
```powershell
curl http://YOUR_DROPLET_IP:5000/api/health
```

**Test config endpoint:**
```powershell
curl http://YOUR_DROPLET_IP:5000/api/config
```

**Expected response:**
```json
{
  "bright_data_username": "hl_47ba96ab",
  "target_url": "https://www.cutebabyvote.com/...",
  "headless_mode": true
}
```

### Test WebSocket Connection

Create `test_backend.py` locally:

```python
import socketio
import time

# Replace with your droplet IP
BACKEND_URL = "http://YOUR_DROPLET_IP:5000"

sio = socketio.Client()

@sio.on('connect')
def on_connect():
    print('✅ Connected to backend')

@sio.on('log_update')
def on_log(data):
    print(f"📝 Log: {data['message']}")

@sio.on('stats_update')
def on_stats(data):
    print(f"📊 Stats: {data}")

try:
    sio.connect(BACKEND_URL)
    print('Listening for events... (Ctrl+C to exit)')
    time.sleep(60)
except KeyboardInterrupt:
    print('\nDisconnecting...')
finally:
    sio.disconnect()
```

**Run:**
```powershell
python test_backend.py
```

---

## 🎮 Step 8: Start Voting System

### 8.1 Start Ultra Monitoring via API

```bash
# On droplet or from local machine
curl -X POST http://YOUR_DROPLET_IP:5000/api/start-monitoring
```

**Expected response:**
```json
{
  "success": true,
  "message": "Ultra monitoring started"
}
```

### 8.2 Monitor Logs

```bash
# On droplet
docker-compose logs -f cloudvoter-backend
```

**You should see:**
```
🚀 Starting ultra monitoring...
✅ Ultra monitoring started
🔍 Scanning saved sessions...
📋 Found X saved sessions
⏰ Instance #1: Y minutes remaining
✅ Instance #2: Ready to launch!
🚀 Launching Instance #2...
```

### 8.3 Check Status

```bash
curl http://YOUR_DROPLET_IP:5000/api/status
```

**Response:**
```json
{
  "monitoring_active": true,
  "active_instances": 2,
  "total_votes": 15,
  "success_rate": 93.3
}
```

---

## 💾 Step 9: Setup Backups

### 9.1 Create Backup Script

```bash
cat > /root/cloudvoter-backend/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/root/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="cloudvoter_backup_${DATE}.tar.gz"

mkdir -p $BACKUP_DIR

cd /root/cloudvoter-backend
tar -czf "${BACKUP_DIR}/${BACKUP_FILE}" \
    brightdata_session_data/ \
    voting_logs.csv \
    cloudvoter.log

echo "✅ Backup created: ${BACKUP_FILE}"
ls -lh "${BACKUP_DIR}/${BACKUP_FILE}"

# Keep only last 7 backups
cd $BACKUP_DIR
ls -t cloudvoter_backup_*.tar.gz | tail -n +8 | xargs -r rm

echo "✅ Old backups cleaned"
EOF

chmod +x backup.sh
```

### 9.2 Run Backup

```bash
./backup.sh
```

### 9.3 Schedule Daily Backups

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /root/cloudvoter-backend/backup.sh >> /root/cloudvoter-backend/backup.log 2>&1

# Save and exit
```

### 9.4 Download Backup to Local Machine

```powershell
# From local machine
scp root@YOUR_DROPLET_IP:/root/backups/cloudvoter_backup_*.tar.gz C:\Users\shubh\Desktop\
```

---

## 🔄 Step 10: Update Session Data

### When You Need to Update Session Data Later

**From local machine:**

```powershell
# Create update archive
cd C:\Users\shubh\OneDrive\Desktop\cloudvoter
tar -czf session_update.tar.gz brightdata_session_data/ voting_logs.csv

# Upload to droplet
scp session_update.tar.gz root@YOUR_DROPLET_IP:/root/
```

**On droplet:**

```bash
cd /root/cloudvoter-backend

# Stop backend
docker-compose down

# Backup current data
mv brightdata_session_data brightdata_session_data.backup
mv voting_logs.csv voting_logs.csv.backup

# Extract new data
tar -xzf /root/session_update.tar.gz

# Restart backend
docker-compose up -d

# Verify
docker-compose logs -f cloudvoter-backend
```

---

## 📊 Management Commands

### View Logs
```bash
# Real-time logs
docker-compose logs -f cloudvoter-backend

# Last 100 lines
docker-compose logs --tail=100 cloudvoter-backend

# Search for errors
docker-compose logs cloudvoter-backend | grep -i error
```

### Restart Backend
```bash
docker-compose restart cloudvoter-backend
```

### Stop Backend
```bash
docker-compose down
```

### Start Backend
```bash
docker-compose up -d
```

### Check Status
```bash
# Container status
docker-compose ps

# Resource usage
docker stats cloudvoter-backend

# System resources
free -h
df -h
```

### Access Container Shell
```bash
docker-compose exec cloudvoter-backend bash
```

### View Configuration
```bash
cat .env
```

---

## 🐛 Troubleshooting

### Problem: Container Won't Start

```bash
# Check logs
docker-compose logs cloudvoter-backend

# Check if port is in use
netstat -tulpn | grep :5000

# Rebuild from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Problem: Can't Access API

```bash
# Check if container is running
docker-compose ps

# Check firewall
ufw status

# Test locally on droplet
curl http://localhost:5000/api/health

# Check if port is exposed
docker-compose port cloudvoter-backend 5000
```

### Problem: Session Data Not Found

```bash
# Check if data exists in container
docker-compose exec cloudvoter-backend ls -la /app/brightdata_session_data/

# Check volume mounts
docker-compose exec cloudvoter-backend df -h

# Re-copy data
docker-compose down
# Upload session data again
docker-compose up -d
```

### Problem: Voting Not Working

```bash
# Check logs for errors
docker-compose logs -f cloudvoter-backend | grep -i error

# Verify credentials
docker-compose exec cloudvoter-backend python -c "from config import BRIGHT_DATA_USERNAME; print(BRIGHT_DATA_USERNAME)"

# Test Playwright
docker-compose exec cloudvoter-backend playwright --version

# Restart backend
docker-compose restart cloudvoter-backend
```

### Problem: Out of Memory

```bash
# Check memory usage
free -h
docker stats

# Increase droplet size
# Go to DigitalOcean dashboard → Resize droplet

# Or optimize config.py
docker-compose exec cloudvoter-backend nano config.py
# Set HEADLESS_MODE = True
# Set DATA_SAVER_MODE = True
```

---

## 🚀 API Endpoints Reference

### Health Check
```bash
GET http://YOUR_IP:5000/api/health
```

### Get Configuration
```bash
GET http://YOUR_IP:5000/api/config
```

### Start Monitoring
```bash
POST http://YOUR_IP:5000/api/start-monitoring
```

### Stop Monitoring
```bash
POST http://YOUR_IP:5000/api/stop-monitoring
```

### Get Status
```bash
GET http://YOUR_IP:5000/api/status
```

### Get Statistics
```bash
GET http://YOUR_IP:5000/api/stats
```

### Launch Instance
```bash
POST http://YOUR_IP:5000/api/launch-instance
```

### Get Active Instances
```bash
GET http://YOUR_IP:5000/api/instances
```

---

## 📈 Performance Optimization

### For High-Volume Voting

**1. Increase Docker Resources**

Edit `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 6G
    reservations:
      memory: 4G
```

**2. Optimize Configuration**

Edit `config.py`:
```python
HEADLESS_MODE = True
DATA_SAVER_MODE = True
MAX_CONCURRENT_INSTANCES = 5  # Adjust based on RAM
```

**3. Monitor Resources**
```bash
# Install monitoring tools
apt-get install htop iotop

# Monitor in real-time
htop
```

---

## 🔐 Security Best Practices

1. ✅ **Change SECRET_KEY** in `.env`
2. ✅ **Use strong passwords**
3. ✅ **Enable firewall** (ufw)
4. ✅ **Use SSH keys** instead of passwords
5. ✅ **Regular backups** of session data
6. ✅ **Keep system updated:**
   ```bash
   apt-get update && apt-get upgrade -y
   ```
7. ✅ **Monitor logs** for suspicious activity
8. ✅ **Limit API access** (optional: add authentication)

---

## ✅ Deployment Checklist

```
□ DigitalOcean droplet created (2GB+ RAM)
□ Session data exists locally
□ Voting logs exist locally
□ Backend package prepared (prepare_backend_deployment.bat)
□ .env file configured with credentials
□ Package uploaded to droplet
□ Docker installed on droplet
□ Backend container running
□ Firewall configured (ports 22, 5000)
□ Health endpoint accessible
□ Session data verified in container
□ Ultra monitoring tested
□ Backup script created
□ Daily backups scheduled
```

---

## 📞 Quick Commands Reference

| Task | Command |
|------|---------|
| **Connect** | `ssh root@YOUR_IP` |
| **View logs** | `docker-compose logs -f cloudvoter-backend` |
| **Restart** | `docker-compose restart` |
| **Stop** | `docker-compose down` |
| **Start** | `docker-compose up -d` |
| **Backup** | `./backup.sh` |
| **Status** | `docker-compose ps` |
| **Resources** | `docker stats` |
| **Test API** | `curl http://YOUR_IP:5000/api/health` |

---

## 🎉 Success!

Your CloudVoter backend is now deployed with:
- ✅ Full backend functionality
- ✅ All session data preserved
- ✅ Voting logs maintained
- ✅ Real-time API access
- ✅ Automatic session restoration
- ✅ Secure firewall configuration
- ✅ Automated backups

**Access your backend:**
```
http://YOUR_DROPLET_IP:5000
```

**API health check:**
```
http://YOUR_DROPLET_IP:5000/api/health
```

**Monitor logs:**
```bash
docker-compose logs -f cloudvoter-backend
```

---

**Total deployment time: ~20 minutes**

**Need help?** Check the troubleshooting section above!

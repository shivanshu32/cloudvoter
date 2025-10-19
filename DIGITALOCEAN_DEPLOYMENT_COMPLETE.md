# Complete DigitalOcean Deployment Guide with Session Data

## 🎯 Overview

This guide covers deploying CloudVoter to DigitalOcean including:
- Backend application
- Session data (`brightdata_session_data/`)
- Voting logs (`voting_logs.csv`)
- Docker setup
- Nginx reverse proxy

---

## 📋 Prerequisites

- DigitalOcean account
- Local machine with CloudVoter working
- Session data in `brightdata_session_data/` folder
- Voting logs in `voting_logs.csv`
- SSH client (built into Windows 10+)

---

## 🚀 Step 1: Create DigitalOcean Droplet

### 1.1 Log into DigitalOcean

Go to: https://cloud.digitalocean.com/

### 1.2 Create New Droplet

1. Click **"Create"** → **"Droplets"**
2. Choose configuration:

**Image:**
- Distribution: **Ubuntu 22.04 LTS**

**Droplet Size:**
- Plan: **Basic**
- CPU Options: **Regular**
- RAM: **2GB minimum** (4GB recommended for multiple instances)
- Price: $12-24/month

**Datacenter Region:**
- Choose closest to your target audience
- Recommended: New York, San Francisco, or London

**Authentication:**
- **Option A (Recommended):** SSH Key
  - Click "New SSH Key"
  - Follow instructions to add your key
- **Option B:** Password
  - Set a strong root password

**Hostname:**
- Set to: `cloudvoter-production`

3. Click **"Create Droplet"**
4. Wait 1-2 minutes for creation
5. **Note your droplet's IP address** (e.g., `165.227.123.45`)

---

## 🔧 Step 2: Prepare Files for Upload

### 2.1 Create Deployment Package on Local Machine

Open PowerShell in your CloudVoter directory:

```powershell
cd C:\Users\shubh\OneDrive\Desktop\cloudvoter
```

### 2.2 Create Archive Script

Create `prepare_deployment.bat`:

```batch
@echo off
echo Creating deployment package...

REM Create temporary deployment folder
mkdir deploy_package
mkdir deploy_package\backend
mkdir deploy_package\frontend

REM Copy backend files
xcopy backend\*.py deploy_package\backend\ /Y
xcopy backend\requirements*.txt deploy_package\backend\ /Y
xcopy backend\config.py deploy_package\backend\ /Y

REM Copy session data
xcopy brightdata_session_data deploy_package\backend\brightdata_session_data\ /E /I /Y

REM Copy voting logs
copy voting_logs.csv deploy_package\backend\ /Y

REM Copy Docker files
copy Dockerfile deploy_package\ /Y
copy docker-compose.yml deploy_package\ /Y
copy nginx.conf deploy_package\ /Y
copy deploy.sh deploy_package\ /Y
copy .env.example deploy_package\.env /Y

REM Copy frontend build (if exists)
if exist frontend\build (
    xcopy frontend\build deploy_package\frontend\build\ /E /I /Y
) else (
    echo WARNING: Frontend build not found. Run 'npm run build' in frontend folder first.
)

echo.
echo ✅ Deployment package created in deploy_package\
echo.
echo Next steps:
echo 1. Edit deploy_package\.env with your credentials
echo 2. Upload to DigitalOcean
pause
```

### 2.3 Build Frontend

```powershell
cd frontend
npm run build
cd ..
```

### 2.4 Run Preparation Script

```powershell
prepare_deployment.bat
```

### 2.5 Configure Environment Variables

Edit `deploy_package\.env`:

```env
# Flask Configuration
SECRET_KEY=your-secure-random-key-here-change-this

# Bright Data Credentials
BRIGHT_DATA_USERNAME=hl_47ba96ab
BRIGHT_DATA_PASSWORD=your-actual-password-here

# Voting Configuration
TARGET_URL=https://www.cutebabyvote.com/vote/...

# Optional: Email notifications
EMAIL_NOTIFICATIONS=false
```

**Generate a secure SECRET_KEY:**
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 📤 Step 3: Upload to DigitalOcean

### 3.1 Create Archive

```powershell
# In cloudvoter directory
cd deploy_package
tar -czf cloudvoter-deploy.tar.gz *
cd ..
```

**Or use 7-Zip if tar not available:**
- Right-click `deploy_package` folder
- 7-Zip → Add to archive
- Format: tar.gz
- Name: `cloudvoter-deploy.tar.gz`

### 3.2 Upload via SCP

Replace `YOUR_DROPLET_IP` with your actual IP:

```powershell
scp deploy_package\cloudvoter-deploy.tar.gz root@YOUR_DROPLET_IP:/root/
```

**Example:**
```powershell
scp deploy_package\cloudvoter-deploy.tar.gz root@165.227.123.45:/root/
```

**If using password authentication:**
- Enter your root password when prompted

**If using SSH key:**
- Should upload without password

**Expected output:**
```
cloudvoter-deploy.tar.gz    100%  150MB  5.2MB/s  00:29
```

---

## 🖥️ Step 4: Connect to Droplet

### 4.1 SSH into Droplet

```powershell
ssh root@YOUR_DROPLET_IP
```

**Example:**
```powershell
ssh root@165.227.123.45
```

### 4.2 Verify Upload

```bash
ls -lh /root/
```

You should see `cloudvoter-deploy.tar.gz`

---

## 🔨 Step 5: Setup on DigitalOcean

### 5.1 Extract Files

```bash
cd /root
mkdir cloudvoter
cd cloudvoter
tar -xzf ../cloudvoter-deploy.tar.gz
ls -la
```

**You should see:**
```
backend/
frontend/
Dockerfile
docker-compose.yml
nginx.conf
deploy.sh
.env
```

### 5.2 Verify Session Data

```bash
ls -la backend/brightdata_session_data/
```

**Should show:**
```
instance_1/
instance_2/
instance_3/
...
```

### 5.3 Verify Voting Logs

```bash
ls -lh backend/voting_logs.csv
```

---

## 🐳 Step 6: Install Docker

### 6.1 Make Deploy Script Executable

```bash
chmod +x deploy.sh
```

### 6.2 Run Deployment Script

```bash
./deploy.sh
```

**This script will:**
1. ✅ Update system packages
2. ✅ Install Docker
3. ✅ Install Docker Compose
4. ✅ Build Docker images
5. ✅ Start containers

**Expected output:**
```
Installing Docker...
✅ Docker installed successfully

Installing Docker Compose...
✅ Docker Compose installed

Building Docker images...
✅ Images built successfully

Starting CloudVoter...
✅ CloudVoter is running!

Access your application at: http://YOUR_DROPLET_IP
```

**This takes 5-10 minutes.**

---

## ✅ Step 7: Verify Deployment

### 7.1 Check Container Status

```bash
docker-compose ps
```

**Expected output:**
```
NAME                STATUS              PORTS
cloudvoter          Up 2 minutes        0.0.0.0:5000->5000/tcp
nginx               Up 2 minutes        0.0.0.0:80->80/tcp
```

### 7.2 Check Logs

```bash
# View all logs
docker-compose logs -f

# View backend only
docker-compose logs -f cloudvoter

# Press Ctrl+C to exit
```

**Look for:**
```
✅ Event loop thread started
✅ Configuration loaded
* Running on http://0.0.0.0:5000
```

### 7.3 Test Health Endpoint

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

### 7.4 Verify Session Data Inside Container

```bash
docker-compose exec cloudvoter ls -la /app/brightdata_session_data/
```

**Should show your instances:**
```
instance_1/
instance_2/
instance_3/
...
```

### 7.5 Verify Voting Logs

```bash
docker-compose exec cloudvoter ls -lh /app/voting_logs.csv
```

---

## 🌐 Step 8: Access CloudVoter

### 8.1 Open in Browser

Navigate to:
```
http://YOUR_DROPLET_IP
```

**Example:**
```
http://165.227.123.45
```

### 8.2 Verify UI Loads

You should see:
- ✅ CloudVoter Control Panel
- ✅ Dashboard with statistics
- ✅ Configuration section
- ✅ Start Ultra Monitoring button
- ✅ Logs section

### 8.3 Check Configuration

Configuration should be pre-filled from your `.env` file:
- Username: `hl_47ba96ab`
- Password: `••••••••••••`
- Voting URL: Your target URL

---

## 🧪 Step 9: Test Voting System

### 9.1 Start Ultra Monitoring

1. Click **"Start Ultra Monitoring"**
2. Watch logs in real-time

**Expected logs:**
```
[HH:MM:SS] 🚀 Starting ultra monitoring...
[HH:MM:SS] ✅ Ultra monitoring started
[HH:MM:SS] 🔍 Scanning saved sessions...
[HH:MM:SS] 📋 Found X saved sessions
[HH:MM:SS] ⏰ Instance #1: Y minutes remaining
[HH:MM:SS] ✅ Instance #2: Ready to launch!
```

### 9.2 Verify Session Restoration

If sessions are ready:
```
[HH:MM:SS] 🚀 Launching Instance #2...
[HH:MM:SS] 🌐 Bright Data assigned IP: 103.45.67.89
[HH:MM:SS] 🔍 Navigating to voting page...
[HH:MM:SS] ✅ Already logged in (session restored)
[HH:MM:SS] 🗳️ Starting voting cycle...
```

### 9.3 Monitor Dashboard

Dashboard should update:
- Active Instances: 1, 2, 3...
- Successful Votes: Incrementing
- Success Rate: Percentage

---

## 🔒 Step 10: Configure Firewall (Security)

### 10.1 Enable UFW Firewall

```bash
# Allow SSH (IMPORTANT: Do this first!)
ufw allow 22/tcp

# Allow HTTP
ufw allow 80/tcp

# Allow HTTPS (for future SSL)
ufw allow 443/tcp

# Enable firewall
ufw enable
```

**Type 'y' when prompted**

### 10.2 Verify Firewall

```bash
ufw status
```

**Expected output:**
```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
443/tcp                    ALLOW       Anywhere
```

---

## 📊 Step 11: Monitor and Manage

### View Live Logs

```bash
# All logs
docker-compose logs -f

# Backend only
docker-compose logs -f cloudvoter

# Last 100 lines
docker-compose logs --tail=100 cloudvoter
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart backend only
docker-compose restart cloudvoter
```

### Stop CloudVoter

```bash
docker-compose down
```

### Start CloudVoter

```bash
docker-compose up -d
```

### Check Resource Usage

```bash
# Container stats
docker stats

# System resources
htop
# (Press 'q' to exit)
```

---

## 💾 Step 12: Backup Session Data

### 12.1 Create Backup Script

```bash
nano backup.sh
```

**Add:**
```bash
#!/bin/bash
BACKUP_DIR="/root/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="cloudvoter_backup_${DATE}.tar.gz"

mkdir -p $BACKUP_DIR

cd /root/cloudvoter
tar -czf "${BACKUP_DIR}/${BACKUP_FILE}" \
    backend/brightdata_session_data/ \
    backend/voting_logs.csv \
    backend/cloudvoter.log

echo "✅ Backup created: ${BACKUP_FILE}"
ls -lh "${BACKUP_DIR}/${BACKUP_FILE}"
```

**Make executable:**
```bash
chmod +x backup.sh
```

### 12.2 Run Backup

```bash
./backup.sh
```

### 12.3 Download Backup to Local Machine

**From your local PowerShell:**
```powershell
scp root@YOUR_DROPLET_IP:/root/backups/cloudvoter_backup_*.tar.gz C:\Users\shubh\Desktop\
```

### 12.4 Schedule Automatic Backups (Optional)

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /root/cloudvoter/backup.sh

# Save and exit
```

---

## 🔄 Step 13: Update Session Data

### If You Need to Update Session Data Later

**From local machine:**

```powershell
# Create new archive with updated data
cd C:\Users\shubh\OneDrive\Desktop\cloudvoter
tar -czf session_update.tar.gz brightdata_session_data/ voting_logs.csv

# Upload to droplet
scp session_update.tar.gz root@YOUR_DROPLET_IP:/root/
```

**On droplet:**

```bash
# Stop CloudVoter
cd /root/cloudvoter
docker-compose down

# Backup current data
mv backend/brightdata_session_data backend/brightdata_session_data.backup
mv backend/voting_logs.csv backend/voting_logs.csv.backup

# Extract new data
cd backend
tar -xzf /root/session_update.tar.gz

# Restart CloudVoter
cd /root/cloudvoter
docker-compose up -d

# Verify
docker-compose logs -f cloudvoter
```

---

## 🐛 Troubleshooting

### Problem: Can't Access Web Interface

**Check if containers are running:**
```bash
docker-compose ps
```

**Check nginx logs:**
```bash
docker-compose logs nginx
```

**Check firewall:**
```bash
ufw status
```

**Restart services:**
```bash
docker-compose restart
```

### Problem: Session Data Not Found

**Verify data inside container:**
```bash
docker-compose exec cloudvoter ls -la /app/brightdata_session_data/
```

**If empty, check Dockerfile volume mounts:**
```bash
cat Dockerfile | grep COPY
```

**Re-copy data:**
```bash
docker-compose down
# Upload session data again
docker-compose up -d
```

### Problem: Voting Not Working

**Check backend logs:**
```bash
docker-compose logs -f cloudvoter | grep -i error
```

**Verify credentials:**
```bash
cat .env | grep BRIGHT_DATA
```

**Test Bright Data connection:**
```bash
docker-compose exec cloudvoter python -c "from config import BRIGHT_DATA_USERNAME; print(BRIGHT_DATA_USERNAME)"
```

**Restart backend:**
```bash
docker-compose restart cloudvoter
```

### Problem: Out of Memory

**Check memory usage:**
```bash
free -h
docker stats
```

**Solution: Upgrade droplet**
1. Go to DigitalOcean dashboard
2. Select your droplet
3. Click "Resize"
4. Choose larger plan (4GB or 8GB RAM)

### Problem: Disk Space Full

**Check disk usage:**
```bash
df -h
```

**Clean Docker:**
```bash
docker system prune -a
```

**Clean old logs:**
```bash
cd /root/cloudvoter/backend
rm cloudvoter.log.old
```

---

## 📈 Performance Optimization

### For High-Volume Voting

**1. Increase Docker Resources**

Edit `docker-compose.yml`:
```yaml
services:
  cloudvoter:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 3G
        reservations:
          memory: 2G
```

**2. Optimize Playwright**

Edit `backend/config.py`:
```python
# Reduce browser memory usage
HEADLESS_MODE = True
DATA_SAVER_MODE = True
```

**3. Monitor Resources**
```bash
# Install htop
apt-get install htop

# Monitor in real-time
htop
```

---

## 🔐 Security Best Practices

1. ✅ **Change default SECRET_KEY** in `.env`
2. ✅ **Use strong passwords**
3. ✅ **Enable firewall** (ufw)
4. ✅ **Use SSH keys** instead of passwords
5. ✅ **Regular backups** of session data
6. ✅ **Keep system updated:**
   ```bash
   apt-get update && apt-get upgrade -y
   ```
7. ✅ **Monitor logs** for suspicious activity
8. ✅ **Setup SSL/HTTPS** (see next section)

---

## 🔒 Optional: Setup SSL/HTTPS

### Using Certbot (Free SSL)

```bash
# Install Certbot
apt-get install certbot

# Stop nginx temporarily
docker-compose stop nginx

# Get certificate (replace with your domain)
certbot certonly --standalone -d yourdomain.com

# Certificates saved to:
# /etc/letsencrypt/live/yourdomain.com/
```

### Update Nginx Configuration

```bash
cd /root/cloudvoter
nano nginx.conf
```

**Add HTTPS server block:**
```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://cloudvoter:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

**Restart nginx:**
```bash
docker-compose restart nginx
```

---

## ✅ Deployment Checklist

```
□ DigitalOcean droplet created
□ Session data prepared locally
□ Frontend built (npm run build)
□ .env file configured with credentials
□ Files uploaded to droplet
□ Docker installed
□ Containers running
□ Firewall configured
□ Web interface accessible
□ Ultra monitoring tested
□ Session restoration verified
□ Backup script created
□ Logs monitored
□ Performance optimized
```

---

## 📞 Quick Reference Commands

### On Local Machine (PowerShell)
```powershell
# Build frontend
cd frontend && npm run build

# Create deployment package
prepare_deployment.bat

# Upload to droplet
scp deploy_package\cloudvoter-deploy.tar.gz root@YOUR_IP:/root/

# Connect to droplet
ssh root@YOUR_IP

# Download backup
scp root@YOUR_IP:/root/backups/*.tar.gz C:\Users\shubh\Desktop\
```

### On DigitalOcean Droplet
```bash
# Start CloudVoter
docker-compose up -d

# Stop CloudVoter
docker-compose down

# View logs
docker-compose logs -f cloudvoter

# Restart
docker-compose restart

# Backup
./backup.sh

# Update system
apt-get update && apt-get upgrade -y

# Check status
docker-compose ps
docker stats
```

---

## 🎉 Success!

Your CloudVoter is now deployed to DigitalOcean with:
- ✅ Full backend functionality
- ✅ All session data preserved
- ✅ Voting logs maintained
- ✅ Real-time monitoring
- ✅ Automatic session restoration
- ✅ Secure firewall configuration

**Access your CloudVoter at:**
```
http://YOUR_DROPLET_IP
```

**Monitor logs:**
```bash
docker-compose logs -f cloudvoter
```

**Need help?** Check the troubleshooting section above!

---

## 📚 Additional Resources

- **DEPLOYMENT.md** - Original deployment guide
- **LOCAL_TESTING_GUIDE.md** - Local testing instructions
- **USAGE_GUIDE.md** - How to use CloudVoter
- **ARCHITECTURE.md** - System architecture details
- **DigitalOcean Docs** - https://docs.digitalocean.com/

---

**Note:** This guide assumes you're deploying from Windows. For Linux/Mac, replace PowerShell commands with bash equivalents.

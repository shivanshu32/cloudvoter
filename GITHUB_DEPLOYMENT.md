# CloudVoter Backend Deployment from GitHub

## 🎯 Overview

Deploy CloudVoter backend directly from your GitHub repository to DigitalOcean.

**Advantages:**
- ✅ No need to upload files manually
- ✅ Easy updates with `git pull`
- ✅ Version control
- ✅ Faster deployment

---

## 📋 Prerequisites

- [x] CloudVoter pushed to GitHub
- [ ] DigitalOcean account
- [ ] Session data ready locally (`brightdata_session_data/`)
- [ ] Voting logs ready locally (`voting_logs.csv`)

---

## 🚀 Step 1: Create DigitalOcean Droplet (5 min)

### 1.1 Create Droplet

1. Go to https://cloud.digitalocean.com/
2. Click **"Create"** → **"Droplets"**
3. Choose:
   - **Image**: Ubuntu 22.04 LTS
   - **Plan**: Basic
   - **RAM**: 2GB minimum ($12/month) or 4GB recommended ($24/month)
   - **Region**: Choose closest to target
   - **Authentication**: SSH key or password
   - **Hostname**: `cloudvoter-backend`

4. Click **"Create Droplet"**
5. **Note your IP**: `___.___.___.___`

---

## 🖥️ Step 2: Connect to Droplet (1 min)

```powershell
ssh root@YOUR_DROPLET_IP
```

**Enter password when prompted**

---

## 📥 Step 3: Clone Repository (2 min)

### 3.1 Install Git (if needed)

```bash
apt-get update
apt-get install -y git
```

### 3.2 Clone Your Repository

```bash
cd /root
git clone https://github.com/YOUR_USERNAME/cloudvoter.git
cd cloudvoter
```

**Replace `YOUR_USERNAME` with your actual GitHub username**

**Example:**
```bash
git clone https://github.com/shivanshu32/cloudvoter.git
cd cloudvoter
```

### 3.3 Verify Files

```bash
ls -la
```

**You should see:**
```
backend/
brightdata_session_data/ (might be empty or gitignored)
voting_logs.csv (might be empty or gitignored)
Dockerfile
docker-compose.yml
deploy.sh
.env.example
README.md
...
```

---

## 📤 Step 4: Upload Session Data & Logs (5 min)

### 4.1 From Your Local Machine

**Open a NEW PowerShell window** (keep SSH session open):

```powershell
cd C:\Users\shubh\OneDrive\Desktop\cloudvoter

# Upload session data
scp -r brightdata_session_data root@YOUR_DROPLET_IP:/root/cloudvoter/backend/

# Upload voting logs
scp voting_logs.csv root@YOUR_DROPLET_IP:/root/cloudvoter/backend/
```

**This uploads:**
- All session instances
- Complete voting history

**Expected output:**
```
brightdata_session_data/instance_1/cookies.json    100%
brightdata_session_data/instance_1/session_info.json    100%
...
voting_logs.csv    100%  5MB  2.1MB/s  00:02
```

### 4.2 Verify Upload (Back in SSH session)

```bash
# Check session data
ls -la backend/brightdata_session_data/

# Check voting logs
ls -lh backend/voting_logs.csv
```

---

## ⚙️ Step 5: Configure Environment (3 min)

### 5.1 Create .env File

```bash
cd /root/cloudvoter
cp .env.example .env
nano .env
```

### 5.2 Edit Configuration

**Update these values:**

```env
# Bright Data Credentials
BRIGHT_DATA_USERNAME=hl_47ba96ab
BRIGHT_DATA_PASSWORD=your-actual-password-here

# Flask Configuration
SECRET_KEY=your-secure-random-key-here

# Voting Configuration
TARGET_URL=https://www.cutebabyvote.com/vote/...
```

**Generate SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**Copy the output and paste as SECRET_KEY**

**Save and exit:**
- Press `Ctrl+X`
- Press `Y`
- Press `Enter`

### 5.3 Verify Configuration

```bash
cat .env | grep -v PASSWORD
```

---

## 🐳 Step 6: Deploy with Docker (10 min)

### 6.1 Make Deploy Script Executable

```bash
chmod +x deploy.sh
```

### 6.2 Run Deployment

```bash
./deploy.sh
```

**This will:**
1. ✅ Update system packages
2. ✅ Install Docker
3. ✅ Install Docker Compose
4. ✅ Build Docker image (includes Playwright + Chromium)
5. ✅ Start backend container

**Expected output:**
```
==========================================
CloudVoter Backend Deployment
==========================================

Updating system packages...
✅ System updated

Installing Docker...
✅ Docker installed

Installing Docker Compose...
✅ Docker Compose installed

Building Docker image...
[+] Building 180.5s
✅ Image built

Starting CloudVoter backend...
✅ CloudVoter Backend is running!

==========================================
Backend API: http://YOUR_IP:5000
Health check: http://YOUR_IP:5000/api/health

View logs: docker-compose logs -f
Stop: docker-compose down
Restart: docker-compose restart
==========================================
```

**This takes 5-10 minutes** (Docker image build with Playwright)

---

## ✅ Step 7: Verify Deployment (2 min)

### 7.1 Check Container Status

```bash
docker-compose ps
```

**Expected:**
```
NAME                    STATUS              PORTS
cloudvoter-backend      Up 1 minute         0.0.0.0:5000->5000/tcp
```

### 7.2 View Logs

```bash
docker-compose logs -f cloudvoter-backend
```

**Look for:**
```
✅ Event loop thread started
✅ Configuration loaded
* Running on http://0.0.0.0:5000
```

**Press `Ctrl+C` to exit**

### 7.3 Test Health Endpoint

```bash
curl http://localhost:5000/api/health
```

**Expected:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-19T00:00:00",
  "monitoring_active": false
}
```

### 7.4 Verify Session Data

```bash
docker-compose exec cloudvoter-backend ls -la /app/brightdata_session_data/
```

**Should show all your instances:**
```
instance_1/
instance_2/
instance_3/
...
```

### 7.5 Get Public IP

```bash
curl ifconfig.me
```

**This is your backend API URL**

---

## 🔒 Step 8: Configure Firewall (2 min)

```bash
# Allow SSH (IMPORTANT - do this first!)
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

## 🧪 Step 9: Test from Local Machine (2 min)

### 9.1 Test API Endpoints

**From your local PowerShell:**

```powershell
# Health check
curl http://YOUR_DROPLET_IP:5000/api/health

# Get configuration
curl http://YOUR_DROPLET_IP:5000/api/config

# Get status
curl http://YOUR_DROPLET_IP:5000/api/status
```

### 9.2 Start Ultra Monitoring

```powershell
curl -X POST http://YOUR_DROPLET_IP:5000/api/start-monitoring
```

**Expected response:**
```json
{
  "success": true,
  "message": "Ultra monitoring started"
}
```

### 9.3 Monitor Logs

**Back in SSH session:**

```bash
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
🌐 Bright Data assigned IP: 103.45.67.89
```

---

## 💾 Step 10: Setup Backups (3 min)

### 10.1 Create Backup Script

```bash
cat > /root/cloudvoter/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/root/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="cloudvoter_backup_${DATE}.tar.gz"

mkdir -p $BACKUP_DIR

cd /root/cloudvoter/backend
tar -czf "${BACKUP_DIR}/${BACKUP_FILE}" \
    brightdata_session_data/ \
    voting_logs.csv \
    cloudvoter.log

echo "✅ Backup created: ${BACKUP_FILE}"
ls -lh "${BACKUP_DIR}/${BACKUP_FILE}"

# Keep only last 7 backups
cd $BACKUP_DIR
ls -t cloudvoter_backup_*.tar.gz | tail -n +8 | xargs -r rm
echo "✅ Old backups cleaned (keeping last 7)"
EOF

chmod +x backup.sh
```

### 10.2 Test Backup

```bash
./backup.sh
```

**Expected:**
```
✅ Backup created: cloudvoter_backup_20250119_000000.tar.gz
-rw-r--r-- 1 root root 45M Jan 19 00:00 /root/backups/cloudvoter_backup_20250119_000000.tar.gz
✅ Old backups cleaned (keeping last 7)
```

### 10.3 Schedule Daily Backups

```bash
# Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /root/cloudvoter/backup.sh >> /root/cloudvoter/backup.log 2>&1") | crontab -

# Verify
crontab -l
```

### 10.4 Download Backup to Local Machine

**From local PowerShell:**

```powershell
scp root@YOUR_DROPLET_IP:/root/backups/cloudvoter_backup_*.tar.gz C:\Users\shubh\Desktop\
```

---

## 🔄 Step 11: Update Deployment (Future Updates)

### When You Push Changes to GitHub

**On droplet:**

```bash
cd /root/cloudvoter

# Stop backend
docker-compose down

# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose build
docker-compose up -d

# View logs
docker-compose logs -f cloudvoter-backend
```

### Update Session Data Only

**From local machine:**

```powershell
# Upload updated session data
scp -r brightdata_session_data root@YOUR_DROPLET_IP:/root/cloudvoter/backend/

# Upload updated logs
scp voting_logs.csv root@YOUR_DROPLET_IP:/root/cloudvoter/backend/
```

**On droplet:**

```bash
cd /root/cloudvoter
docker-compose restart cloudvoter-backend
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
cd /root/cloudvoter
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
htop  # Press 'q' to exit
```

### Access Container Shell
```bash
docker-compose exec cloudvoter-backend bash
```

### Pull Latest Code
```bash
cd /root/cloudvoter
git pull origin main
docker-compose down
docker-compose build
docker-compose up -d
```

---

## 🐛 Troubleshooting

### Problem: Git clone fails

**Error: "Permission denied"**

```bash
# Make sure you're using HTTPS URL, not SSH
git clone https://github.com/YOUR_USERNAME/cloudvoter.git

# If repository is private, you'll need a personal access token
# GitHub → Settings → Developer settings → Personal access tokens
```

### Problem: Session data not uploading

```bash
# Check if folder exists locally
ls C:\Users\shubh\OneDrive\Desktop\cloudvoter\brightdata_session_data

# Try uploading one instance at a time
scp -r brightdata_session_data/instance_1 root@YOUR_IP:/root/cloudvoter/backend/brightdata_session_data/
```

### Problem: Container won't start

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

### Problem: Can't access API from local machine

```bash
# Check if container is running
docker-compose ps

# Check firewall
ufw status

# Test locally on droplet first
curl http://localhost:5000/api/health

# Check if port is exposed
docker-compose port cloudvoter-backend 5000
```

### Problem: Session data not found in container

```bash
# Check if data exists on host
ls -la /root/cloudvoter/backend/brightdata_session_data/

# Check if data exists in container
docker-compose exec cloudvoter-backend ls -la /app/brightdata_session_data/

# If missing, re-upload from local machine
```

### Problem: Out of memory

```bash
# Check memory usage
free -h
docker stats

# Upgrade droplet
# DigitalOcean Dashboard → Select Droplet → Resize → 4GB or 8GB
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
□ DigitalOcean droplet created (Ubuntu 22.04, 2GB+ RAM)
□ Connected to droplet via SSH
□ Git installed on droplet
□ Repository cloned from GitHub
□ Session data uploaded (brightdata_session_data/)
□ Voting logs uploaded (voting_logs.csv)
□ .env file created and configured
□ SECRET_KEY generated and set
□ deploy.sh executed successfully
□ Container running (docker-compose ps)
□ Health endpoint returns 200 OK
□ Session data verified in container
□ Firewall configured (ports 22, 5000)
□ API accessible from local machine
□ Ultra monitoring tested
□ Backup script created
□ Daily backups scheduled
```

---

## 🎉 Success!

Your CloudVoter backend is now deployed from GitHub!

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

**Monitor:**
```bash
docker-compose logs -f cloudvoter-backend
```

**Update Code:**
```bash
cd /root/cloudvoter
git pull
docker-compose down && docker-compose build && docker-compose up -d
```

---

## 📞 Quick Commands Summary

| Task | Command |
|------|---------|
| **Connect** | `ssh root@YOUR_IP` |
| **View logs** | `docker-compose logs -f cloudvoter-backend` |
| **Restart** | `docker-compose restart` |
| **Stop** | `docker-compose down` |
| **Start** | `docker-compose up -d` |
| **Update code** | `git pull && docker-compose down && docker-compose build && docker-compose up -d` |
| **Backup** | `./backup.sh` |
| **Status** | `docker-compose ps` |

---

## 📚 Additional Resources

- **BACKEND_ONLY_DEPLOYMENT.md** - Detailed deployment guide
- **USAGE_GUIDE.md** - How to use the API
- **ARCHITECTURE.md** - System architecture

---

**Total Deployment Time: ~30 minutes**

**Advantages of GitHub deployment:**
- ✅ Easy updates with `git pull`
- ✅ Version control
- ✅ No manual file uploads for code
- ✅ Cleaner workflow

**Need help?** Check the troubleshooting section above!

# 🚀 Backend-Only Deployment - Quick Reference

## One-Page Guide to Deploy CloudVoter Backend

---

## 📋 Prerequisites

- [ ] DigitalOcean account
- [ ] Session data in `brightdata_session_data/` folder
- [ ] Voting logs in `voting_logs.csv`

---

## ⚡ 4-Step Deployment (20 minutes)

### **Step 1: Prepare Package** (3 min)

```powershell
cd C:\Users\shubh\OneDrive\Desktop\cloudvoter

# Run preparation script
prepare_backend_deployment.bat

# Edit credentials
notepad backend_deploy\.env
```

**In `.env` file:**
```env
BRIGHT_DATA_USERNAME=hl_47ba96ab
BRIGHT_DATA_PASSWORD=your-actual-password
SECRET_KEY=<run: python -c "import secrets; print(secrets.token_hex(32))">
TARGET_URL=https://www.cutebabyvote.com/vote/...
```

---

### **Step 2: Create Droplet** (3 min)

1. Go to https://cloud.digitalocean.com/
2. Create → Droplets
3. **Ubuntu 22.04** | **2GB RAM** | **$12/month**
4. Note IP: `___.___.___.___`

---

### **Step 3: Upload & Deploy** (10 min)

```powershell
# Upload
scp cloudvoter-backend.tar.gz root@YOUR_IP:/root/

# Connect
ssh root@YOUR_IP
```

**On droplet:**
```bash
# Extract
cd /root
mkdir cloudvoter-backend
cd cloudvoter-backend
tar -xzf ../cloudvoter-backend.tar.gz

# Deploy
chmod +x deploy.sh
./deploy.sh
```

**Wait for:**
```
✅ CloudVoter Backend is running!
Backend API: http://YOUR_IP:5000
```

---

### **Step 4: Verify** (2 min)

```bash
# Check status
docker-compose ps

# View logs
docker-compose logs -f cloudvoter-backend

# Test API
curl http://localhost:5000/api/health
```

**Configure firewall:**
```bash
ufw allow 22/tcp
ufw allow 5000/tcp
ufw enable
```

---

## 🧪 Test from Local Machine

```powershell
# Health check
curl http://YOUR_IP:5000/api/health

# Start monitoring
curl -X POST http://YOUR_IP:5000/api/start-monitoring

# Check status
curl http://YOUR_IP:5000/api/status
```

---

## 💾 Setup Backup (2 min)

```bash
# Create backup script
cat > /root/cloudvoter-backend/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/root/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
cd /root/cloudvoter-backend
tar -czf "${BACKUP_DIR}/cloudvoter_backup_${DATE}.tar.gz" \
    brightdata_session_data/ voting_logs.csv cloudvoter.log
echo "✅ Backup: cloudvoter_backup_${DATE}.tar.gz"
ls -t $BACKUP_DIR/cloudvoter_backup_*.tar.gz | tail -n +8 | xargs -r rm
EOF

chmod +x backup.sh

# Run backup
./backup.sh

# Schedule daily backups at 2 AM
(crontab -l 2>/dev/null; echo "0 2 * * * /root/cloudvoter-backend/backup.sh") | crontab -
```

---

## 📊 Management Commands

| Task | Command |
|------|---------|
| **View logs** | `docker-compose logs -f cloudvoter-backend` |
| **Restart** | `docker-compose restart` |
| **Stop** | `docker-compose down` |
| **Start** | `docker-compose up -d` |
| **Status** | `docker-compose ps` |
| **Resources** | `docker stats` |
| **Backup** | `./backup.sh` |

---

## 🔄 Update Session Data

```powershell
# From local machine
cd C:\Users\shubh\OneDrive\Desktop\cloudvoter
tar -czf session_update.tar.gz brightdata_session_data/ voting_logs.csv
scp session_update.tar.gz root@YOUR_IP:/root/
```

```bash
# On droplet
cd /root/cloudvoter-backend
docker-compose down
mv brightdata_session_data brightdata_session_data.backup
mv voting_logs.csv voting_logs.csv.backup
tar -xzf /root/session_update.tar.gz
docker-compose up -d
```

---

## 🐛 Quick Troubleshooting

### Container won't start?
```bash
docker-compose logs cloudvoter-backend
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Can't access API?
```bash
docker-compose ps
ufw status
curl http://localhost:5000/api/health
```

### Session data missing?
```bash
docker-compose exec cloudvoter-backend ls -la /app/brightdata_session_data/
```

### Out of memory?
```bash
free -h
docker stats
# Upgrade droplet to 4GB RAM
```

---

## 🌐 API Endpoints

```bash
# Health check
GET http://YOUR_IP:5000/api/health

# Get config
GET http://YOUR_IP:5000/api/config

# Start monitoring
POST http://YOUR_IP:5000/api/start-monitoring

# Stop monitoring
POST http://YOUR_IP:5000/api/stop-monitoring

# Get status
GET http://YOUR_IP:5000/api/status

# Launch instance
POST http://YOUR_IP:5000/api/launch-instance
```

---

## ✅ Success Checklist

```
□ Droplet created (Ubuntu 22.04, 2GB RAM)
□ Backend package prepared
□ .env configured with credentials
□ Package uploaded to droplet
□ deploy.sh executed successfully
□ Container running (docker-compose ps)
□ Firewall configured (ports 22, 5000)
□ API accessible from local machine
□ Session data verified in container
□ Backup script created and tested
□ Daily backups scheduled
```

---

## 🎉 You're Done!

**Backend API:** `http://YOUR_IP:5000`

**Health Check:** `http://YOUR_IP:5000/api/health`

**Start Voting:**
```bash
curl -X POST http://YOUR_IP:5000/api/start-monitoring
```

**Monitor:**
```bash
docker-compose logs -f cloudvoter-backend
```

---

## 📚 Full Documentation

- **BACKEND_ONLY_DEPLOYMENT.md** - Complete deployment guide
- **USAGE_GUIDE.md** - How to use the API
- **ARCHITECTURE.md** - System architecture

---

**Total Time: ~20 minutes**

**Questions?** Check BACKEND_ONLY_DEPLOYMENT.md for detailed troubleshooting!

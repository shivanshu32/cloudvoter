# 🚀 CloudVoter DigitalOcean Deployment - Quick Start

## One-Page Deployment Guide

### 📋 Before You Start

- [ ] DigitalOcean account ready
- [ ] Session data in `brightdata_session_data/` folder
- [ ] Voting logs in `voting_logs.csv`
- [ ] Frontend built (`npm run build` in frontend folder)

---

## 🎯 5-Step Deployment Process

### **Step 1: Create DigitalOcean Droplet** (5 min)

1. Go to https://cloud.digitalocean.com/
2. Create → Droplets
3. **Ubuntu 22.04 LTS** | **2GB RAM** | **$12/month**
4. Note your IP: `___.___.___.___`

---

### **Step 2: Prepare Deployment Package** (2 min)

```powershell
# In cloudvoter directory
cd C:\Users\shubh\OneDrive\Desktop\cloudvoter

# Build frontend (if not done)
cd frontend
npm run build
cd ..

# Create deployment package
prepare_deployment.bat
```

**Edit `deploy_package\.env`:**
```env
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
BRIGHT_DATA_USERNAME=hl_47ba96ab
BRIGHT_DATA_PASSWORD=<your-actual-password>
TARGET_URL=https://www.cutebabyvote.com/vote/...
```

---

### **Step 3: Upload to DigitalOcean** (3 min)

```powershell
# Upload archive (replace YOUR_IP with your droplet IP)
scp cloudvoter-deploy.tar.gz root@YOUR_IP:/root/
```

**Enter password when prompted**

---

### **Step 4: Deploy on Server** (10 min)

```powershell
# Connect to droplet
ssh root@YOUR_IP
```

**On the droplet:**
```bash
# Extract files
cd /root
mkdir cloudvoter
cd cloudvoter
tar -xzf ../cloudvoter-deploy.tar.gz

# Run deployment
chmod +x deploy.sh
./deploy.sh
```

**Wait for:**
```
✅ CloudVoter is running!
Access your application at: http://YOUR_IP
```

---

### **Step 5: Verify & Test** (2 min)

```bash
# Check status
docker-compose ps

# View logs
docker-compose logs -f cloudvoter
```

**Open browser:**
```
http://YOUR_IP
```

**Test:**
1. Click "Start Ultra Monitoring"
2. Watch logs for session scanning
3. Verify instances launch

---

## 🔒 Security Setup (5 min)

```bash
# On droplet
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

---

## 💾 Backup Setup (2 min)

```bash
# Create backup script
cat > /root/cloudvoter/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/root/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
cd /root/cloudvoter
tar -czf "${BACKUP_DIR}/cloudvoter_backup_${DATE}.tar.gz" \
    backend/brightdata_session_data/ \
    backend/voting_logs.csv
echo "✅ Backup created: cloudvoter_backup_${DATE}.tar.gz"
EOF

chmod +x /root/cloudvoter/backup.sh

# Run backup
./backup.sh
```

---

## 📊 Management Commands

### View Logs
```bash
docker-compose logs -f cloudvoter
```

### Restart
```bash
docker-compose restart
```

### Stop
```bash
docker-compose down
```

### Start
```bash
docker-compose up -d
```

### Update Session Data
```powershell
# From local machine
scp session_update.tar.gz root@YOUR_IP:/root/
```

```bash
# On droplet
cd /root/cloudvoter
docker-compose down
cd backend
tar -xzf /root/session_update.tar.gz
cd /root/cloudvoter
docker-compose up -d
```

---

## 🐛 Quick Troubleshooting

### Can't access web interface?
```bash
docker-compose ps          # Check if running
docker-compose logs nginx  # Check nginx logs
ufw status                 # Check firewall
```

### Session data not found?
```bash
docker-compose exec cloudvoter ls -la /app/brightdata_session_data/
```

### Voting not working?
```bash
docker-compose logs -f cloudvoter | grep -i error
cat .env | grep BRIGHT_DATA
```

### Out of memory?
```bash
free -h
docker stats
# Upgrade droplet to 4GB RAM
```

---

## ✅ Success Checklist

```
□ Droplet created and IP noted
□ Frontend built locally
□ Deployment package created
□ .env file configured
□ Files uploaded to droplet
□ deploy.sh executed successfully
□ Containers running (docker-compose ps)
□ Web interface accessible at http://YOUR_IP
□ Ultra monitoring starts without errors
□ Sessions restored successfully
□ Firewall configured
□ Backup script created
```

---

## 📞 Quick Commands Reference

| Task | Command |
|------|---------|
| **Connect to droplet** | `ssh root@YOUR_IP` |
| **View logs** | `docker-compose logs -f cloudvoter` |
| **Restart** | `docker-compose restart` |
| **Stop** | `docker-compose down` |
| **Start** | `docker-compose up -d` |
| **Backup** | `./backup.sh` |
| **Check status** | `docker-compose ps` |
| **Check resources** | `docker stats` |

---

## 🎉 You're Done!

**Access CloudVoter:**
```
http://YOUR_DROPLET_IP
```

**Monitor:**
```bash
docker-compose logs -f cloudvoter
```

**For detailed instructions, see:**
- `DIGITALOCEAN_DEPLOYMENT_COMPLETE.md` - Full deployment guide
- `DEPLOYMENT.md` - Original deployment documentation
- `USAGE_GUIDE.md` - How to use CloudVoter

---

**Total Time: ~30 minutes**

**Need help?** Check `DIGITALOCEAN_DEPLOYMENT_COMPLETE.md` for detailed troubleshooting!

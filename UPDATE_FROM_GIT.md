# Update CloudVoter from Git Repository

## 🔄 Steps to Pull Latest Code from GitHub

---

## ⚠️ Important: Backup First!

Before updating, backup your session data and logs:

```bash
cd /root/cloudvoter
./backup.sh
```

**Or manual backup:**
```bash
mkdir -p /root/backups
tar -czf /root/backups/backup_before_update_$(date +%Y%m%d_%H%M%S).tar.gz \
    backend/brightdata_session_data/ \
    backend/voting_logs.csv \
    backend/cloudvoter.log
```

---

## 🚀 Method 1: Pull Latest Changes (Recommended)

### Step 1: Stop PM2 Process

```bash
cd /root/cloudvoter/backend
pm2 stop cloudvoter-backend
```

### Step 2: Backup Current Session Data & Logs

```bash
# Create temporary backup
cp -r brightdata_session_data brightdata_session_data.backup
cp voting_logs.csv voting_logs.csv.backup
cp config.py config.py.backup
```

### Step 3: Pull Latest Code

```bash
cd /root/cloudvoter
git pull origin main
```

**Or if you're on a different branch:**
```bash
git pull origin master
```

**Expected output:**
```
remote: Enumerating objects: 10, done.
remote: Counting objects: 100% (10/10), done.
remote: Compressing objects: 100% (6/6), done.
remote: Total 6 (delta 4), reused 0 (delta 0)
Unpacking objects: 100% (6/6), done.
From https://github.com/YOUR_USERNAME/cloudvoter
   abc1234..def5678  main -> origin/main
Updating abc1234..def5678
Fast-forward
 backend/app.py | 25 +++++++++++++++++++------
 1 file changed, 19 insertions(+), 6 deletions(-)
```

### Step 4: Restore Session Data & Config (If Overwritten)

```bash
cd /root/cloudvoter/backend

# Check if session data still exists
ls -la brightdata_session_data/

# If missing or empty, restore from backup
if [ ! -d "brightdata_session_data" ] || [ -z "$(ls -A brightdata_session_data)" ]; then
    echo "Restoring session data..."
    rm -rf brightdata_session_data
    cp -r brightdata_session_data.backup brightdata_session_data
fi

# Restore voting logs if needed
if [ ! -f "voting_logs.csv" ] || [ ! -s "voting_logs.csv" ]; then
    echo "Restoring voting logs..."
    cp voting_logs.csv.backup voting_logs.csv
fi

# Restore config if needed (check your credentials)
nano config.py
# Verify BRIGHT_DATA_PASSWORD is set correctly
```

### Step 5: Update Dependencies (If requirements.txt Changed)

```bash
cd /root/cloudvoter/backend
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

### Step 6: Restart PM2

```bash
pm2 restart cloudvoter-backend
```

### Step 7: Verify

```bash
# Check status
pm2 status

# View logs
pm2 logs cloudvoter-backend --lines 50

# Test API
curl http://localhost:5000/api/health
```

---

## 🔄 Method 2: Fresh Clone (If Git Pull Fails)

### Step 1: Stop PM2

```bash
pm2 stop cloudvoter-backend
pm2 delete cloudvoter-backend
```

### Step 2: Backup Everything

```bash
# Backup session data and logs
mkdir -p /root/backups
cd /root/cloudvoter/backend
tar -czf /root/backups/session_data_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
    brightdata_session_data/ \
    voting_logs.csv \
    config.py \
    cloudvoter.log
```

### Step 3: Remove Old Folder

```bash
cd /root
mv cloudvoter cloudvoter.old
```

### Step 4: Clone Fresh Repository

```bash
cd /root
git clone https://github.com/YOUR_USERNAME/cloudvoter.git
cd cloudvoter
```

**Replace `YOUR_USERNAME` with your GitHub username**

### Step 5: Restore Session Data & Logs

```bash
cd /root/cloudvoter/backend

# Extract backup
tar -xzf /root/backups/session_data_backup_*.tar.gz

# Or copy from old folder
cp -r /root/cloudvoter.old/backend/brightdata_session_data ./
cp /root/cloudvoter.old/backend/voting_logs.csv ./
cp /root/cloudvoter.old/backend/config.py ./
```

### Step 6: Recreate Virtual Environment

```bash
cd /root/cloudvoter/backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### Step 7: Verify Configuration

```bash
nano config.py
# Verify credentials are correct
```

### Step 8: Recreate PM2 Config

```bash
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
      PYTHONUNBUFFERED: '1'
    }
  }]
};
EOF

mkdir -p logs
```

### Step 9: Start with PM2

```bash
pm2 start ecosystem.config.js
pm2 save
```

### Step 10: Verify

```bash
pm2 status
pm2 logs cloudvoter-backend
curl http://localhost:5000/api/health
```

### Step 11: Clean Up Old Folder (Optional)

```bash
# After verifying everything works
rm -rf /root/cloudvoter.old
```

---

## 🐛 Troubleshooting

### Problem: Git pull shows conflicts

```bash
# See what files have conflicts
git status

# Option 1: Stash your changes
git stash
git pull origin main
git stash pop

# Option 2: Reset to remote (CAUTION: loses local changes)
git fetch origin
git reset --hard origin/main

# Option 3: Keep your local files
# Backup first, then:
git fetch origin
git reset --hard origin/main
# Restore your backed up files
```

### Problem: "Your local changes would be overwritten"

```bash
# Backup important files first
cp backend/config.py backend/config.py.backup
cp backend/brightdata_session_data backend/brightdata_session_data.backup -r
cp backend/voting_logs.csv backend/voting_logs.csv.backup

# Force pull
git fetch origin
git reset --hard origin/main

# Restore your files
cp backend/config.py.backup backend/config.py
cp backend/brightdata_session_data.backup backend/brightdata_session_data -r
cp backend/voting_logs.csv.backup backend/voting_logs.csv
```

### Problem: Session data disappeared after git pull

```bash
# Check if .gitignore excludes session data
cat .gitignore | grep brightdata_session_data

# Restore from backup
cd /root/cloudvoter/backend
cp -r brightdata_session_data.backup brightdata_session_data

# Or extract from backup
tar -xzf /root/backups/session_data_backup_*.tar.gz
```

### Problem: PM2 won't restart after update

```bash
# Check logs for errors
pm2 logs cloudvoter-backend --err

# Delete and recreate PM2 process
pm2 delete cloudvoter-backend
pm2 start ecosystem.config.js
pm2 save

# Check if virtual environment is activated
cd /root/cloudvoter/backend
source venv/bin/activate
python app.py
# If it runs, Ctrl+C and use PM2
```

### Problem: Dependencies missing after update

```bash
cd /root/cloudvoter/backend
source venv/bin/activate
pip install -r requirements.txt --upgrade
playwright install chromium
pm2 restart cloudvoter-backend
```

---

## 📋 Quick Update Checklist

```
□ Backup session data and logs
□ Stop PM2 process
□ Pull latest code (git pull)
□ Verify session data still exists
□ Verify config.py has correct credentials
□ Update dependencies if needed
□ Restart PM2
□ Check PM2 status
□ View logs for errors
□ Test API endpoint
□ Verify session data accessible
```

---

## 🔄 Regular Update Workflow

### Daily/Weekly Updates

```bash
# 1. Backup
cd /root/cloudvoter
./backup.sh

# 2. Stop
pm2 stop cloudvoter-backend

# 3. Update
git pull origin main

# 4. Restart
pm2 restart cloudvoter-backend

# 5. Verify
pm2 logs cloudvoter-backend --lines 20
curl http://localhost:5000/api/health
```

---

## 📞 Quick Commands

| Task | Command |
|------|---------|
| **Stop backend** | `pm2 stop cloudvoter-backend` |
| **Pull updates** | `cd /root/cloudvoter && git pull origin main` |
| **Restart backend** | `pm2 restart cloudvoter-backend` |
| **View logs** | `pm2 logs cloudvoter-backend` |
| **Check status** | `pm2 status` |
| **Backup data** | `./backup.sh` |

---

## 🎯 Best Practices

1. **Always backup before updating**
   ```bash
   ./backup.sh
   ```

2. **Check what changed**
   ```bash
   git fetch origin
   git log HEAD..origin/main --oneline
   ```

3. **Test locally first** (if possible)
   - Pull changes on local machine
   - Test thoroughly
   - Then update production

4. **Keep session data safe**
   - Session data should be in `.gitignore`
   - Never commit session data to git
   - Always backup before updates

5. **Monitor after updates**
   ```bash
   pm2 logs cloudvoter-backend -f
   ```

---

## 🚨 Emergency Rollback

### If Update Breaks Something

```bash
# Stop current version
pm2 stop cloudvoter-backend

# Restore from backup
cd /root
rm -rf cloudvoter
mv cloudvoter.old cloudvoter

# Restart
cd /root/cloudvoter/backend
pm2 restart cloudvoter-backend

# Or restore from git
cd /root/cloudvoter
git reflog
git reset --hard HEAD@{1}  # Go back one commit
pm2 restart cloudvoter-backend
```

---

## ✅ Verification After Update

```bash
# 1. Check PM2 status
pm2 status
# Should show: online

# 2. Check logs for errors
pm2 logs cloudvoter-backend --err --lines 50

# 3. Test health endpoint
curl http://localhost:5000/api/health

# 4. Verify session data
ls -la /root/cloudvoter/backend/brightdata_session_data/

# 5. Test voting (if monitoring was active)
curl -X POST http://localhost:5000/api/start-monitoring
pm2 logs cloudvoter-backend -f
```

---

## 🎉 Update Complete!

Your CloudVoter backend is now updated with the latest code from GitHub!

**Monitor for a few minutes:**
```bash
pm2 logs cloudvoter-backend -f
```

**Check status:**
```bash
pm2 status
```

**Test API:**
```bash
curl http://YOUR_IP:5000/api/health
```

---

**Need help?** Check the troubleshooting section above or review PM2_DEPLOYMENT.md!

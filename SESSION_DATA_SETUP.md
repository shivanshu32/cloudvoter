# Session Data Setup for CloudVoter

## ⚠️ Important: Session Data Required

CloudVoter needs the **saved browser sessions** from your googleloginautomate project to work properly. These sessions contain:

- Google login cookies
- Browser storage data
- Session metadata (last vote time, IP, etc.)

Without these sessions, CloudVoter will need to login to Google from scratch for each instance.

---

## 📁 What is Session Data?

The `brightdata_session_data` folder contains saved browser sessions:

```
brightdata_session_data/
├── instance_1/
│   ├── cookies.json          # Browser cookies
│   ├── session_info.json     # Metadata (last vote time, IP, etc.)
│   └── storage_state.json    # Full browser state
├── instance_2/
├── instance_3/
└── instance_N/
```

Each `instance_N` folder represents a saved browser session with:
- ✅ Google login already completed
- ✅ Voting page cookies
- ✅ Last vote timestamp
- ✅ Proxy IP used

---

## 🔄 How to Copy Session Data

### Option 1: Use the Copy Script (Recommended)

**Run the provided script:**

```bash
# In cloudvoter folder
copy_sessions.bat
```

This will automatically copy all sessions from googleloginautomate to cloudvoter.

### Option 2: Manual Copy

**Copy the entire folder:**

```bash
# Source
C:\Users\shubh\OneDrive\Desktop\googleloginautomate\brightdata_session_data\

# Destination
C:\Users\shubh\OneDrive\Desktop\cloudvoter\brightdata_session_data\
```

**Steps:**
1. Open File Explorer
2. Navigate to `googleloginautomate` folder
3. Copy `brightdata_session_data` folder
4. Paste into `cloudvoter` folder

### Option 3: PowerShell Command

```powershell
Copy-Item -Path "C:\Users\shubh\OneDrive\Desktop\googleloginautomate\brightdata_session_data" -Destination "C:\Users\shubh\OneDrive\Desktop\cloudvoter\" -Recurse -Force
```

---

## ✅ Verify Session Data

After copying, verify the sessions:

```bash
# Check if folder exists
dir cloudvoter\brightdata_session_data

# Should show:
# instance_1, instance_2, instance_3, etc.
```

**Check session contents:**

```bash
# Check instance_1
dir cloudvoter\brightdata_session_data\instance_1

# Should show:
# cookies.json
# session_info.json
# storage_state.json
```

---

## 🎯 What Happens With Session Data

### With Session Data (Recommended)
```
1. Click "Start Ultra Monitoring"
2. System scans brightdata_session_data/
3. Finds saved sessions (e.g., 10 sessions)
4. Checks cooldown for each session
5. Launches ready sessions automatically
6. Sessions already logged in to Google
7. Voting starts immediately
8. No manual login required!
```

### Without Session Data (Fresh Start)
```
1. Click "Start Ultra Monitoring"
2. System scans brightdata_session_data/
3. Finds no saved sessions
4. You must click "Launch Instance" manually
5. Browser opens but not logged in
6. System detects "Login Required"
7. You must login to Google manually
8. After login, session is saved
9. Next time, session will be reused
```

---

## 🔍 Understanding Session Files

### session_info.json
```json
{
  "instance_id": 1,
  "proxy_ip": "103.45.67.89",
  "session_id": "abc123xyz",
  "last_vote_time": "2025-01-19T12:30:00",
  "vote_count": 45,
  "saved_at": "2025-01-19T13:01:00"
}
```

**Key fields:**
- `last_vote_time` - Used for cooldown detection (31 minutes)
- `proxy_ip` - Unique IP for this session
- `vote_count` - Total votes cast by this instance

### storage_state.json
Contains full browser state:
- Cookies (including Google login)
- localStorage
- sessionStorage
- IndexedDB

This is what keeps you logged in!

---

## 🚀 Deployment with Session Data

### Local Development

```bash
# 1. Copy sessions
copy_sessions.bat

# 2. Start backend
cd backend
python app.py

# 3. Start frontend
cd frontend
npm start

# 4. Access http://localhost:3000
# 5. Click "Start Ultra Monitoring"
# 6. Sessions launch automatically!
```

### DigitalOcean Deployment

**Before deploying:**

```bash
# 1. Copy sessions to cloudvoter
copy_sessions.bat

# 2. Upload cloudvoter folder (with sessions)
scp -r cloudvoter root@YOUR_DROPLET_IP:/root/

# 3. Deploy
ssh root@YOUR_DROPLET_IP
cd cloudvoter
./deploy.sh

# Sessions are now on the server!
```

**After deploying:**

The Docker volume will persist the session data:

```yaml
# docker-compose.yml already includes:
volumes:
  - ./brightdata_session_data:/app/brightdata_session_data
```

---

## 🔄 Syncing Sessions Between Systems

### From Desktop to Cloud

**After voting on desktop, sync to cloud:**

```bash
# 1. Copy latest sessions from desktop
copy_sessions.bat

# 2. Upload to server
scp -r brightdata_session_data root@YOUR_DROPLET_IP:/root/cloudvoter/

# 3. Restart CloudVoter
ssh root@YOUR_DROPLET_IP
cd cloudvoter
docker-compose restart
```

### From Cloud to Desktop

**Download sessions from cloud:**

```bash
# Download from server
scp -r root@YOUR_DROPLET_IP:/root/cloudvoter/brightdata_session_data ./

# Copy to googleloginautomate
xcopy brightdata_session_data c:\Users\shubh\OneDrive\Desktop\googleloginautomate\brightdata_session_data /E /I /H /Y
```

---

## 📊 Session Statistics

### Check How Many Sessions You Have

```bash
# Count instance folders
dir brightdata_session_data | find /c "instance_"
```

### Check Session Status

Open any `session_info.json` to see:
- When last vote was cast
- How many votes total
- Which IP was used

### Example: 10 Sessions

```
brightdata_session_data/
├── instance_1/  ← Last vote: 5 min ago  (26 min cooldown remaining)
├── instance_2/  ← Last vote: 32 min ago (Ready to launch!)
├── instance_3/  ← Last vote: 15 min ago (16 min cooldown remaining)
├── instance_4/  ← Last vote: 31 min ago (Ready to launch!)
├── instance_5/  ← Last vote: 10 min ago (21 min cooldown remaining)
├── instance_6/  ← Last vote: 45 min ago (Ready to launch!)
├── instance_7/  ← Last vote: 2 min ago  (29 min cooldown remaining)
├── instance_8/  ← Last vote: 35 min ago (Ready to launch!)
├── instance_9/  ← Last vote: 20 min ago (11 min cooldown remaining)
└── instance_10/ ← Last vote: 40 min ago (Ready to launch!)

Result: 5 instances ready to launch immediately!
```

---

## 🛠️ Troubleshooting

### Problem: No sessions found

**Symptom:**
```
[12:35:00] 🔍 Scanning saved sessions...
[12:35:01] 📋 Found 0 saved sessions
```

**Solution:**
```bash
# Copy sessions from googleloginautomate
copy_sessions.bat

# Verify
dir brightdata_session_data
```

### Problem: Sessions not launching

**Check session files:**
```bash
# Each instance folder should have 3 files
dir brightdata_session_data\instance_1

# Should show:
# cookies.json
# session_info.json
# storage_state.json
```

**If files are missing:**
- Session is corrupted
- Delete that instance folder
- Let system create new session

### Problem: All sessions in cooldown

**This is normal!**

If all sessions voted recently (< 31 minutes ago), they're all in cooldown.

**What happens:**
```
[12:35:00] 🔍 Found 10 saved sessions
[12:35:01] ⏰ All sessions in cooldown
[12:35:02] ⏰ Next ready in 5 minutes (instance_3)
[12:40:02] ✅ Instance #3 ready! Launching...
```

System will automatically launch when cooldown completes.

---

## 📝 Best Practices

### 1. Regular Backups

**Backup sessions daily:**
```bash
# Create backup
tar -czf sessions-backup-$(date +%Y%m%d).tar.gz brightdata_session_data/

# Or on Windows
copy_sessions.bat
```

### 2. Keep Sessions Synced

If using both desktop and cloud:
- Sync sessions after each voting session
- Avoid running both simultaneously (IP conflicts)

### 3. Clean Corrupted Sessions

**If a session keeps failing:**
```bash
# Delete corrupted session
rm -rf brightdata_session_data/instance_X/

# System will create new session
```

### 4. Monitor Session Health

**Check session_info.json regularly:**
- Last vote time should update after each vote
- Vote count should increase
- If stuck, session may be broken

---

## 🎯 Quick Reference

### Copy Sessions
```bash
copy_sessions.bat
```

### Verify Sessions
```bash
dir brightdata_session_data
```

### Count Sessions
```bash
dir brightdata_session_data | find /c "instance_"
```

### Backup Sessions
```bash
# Windows
xcopy brightdata_session_data backup\brightdata_session_data /E /I /H /Y

# Linux/Mac
tar -czf sessions-backup.tar.gz brightdata_session_data/
```

### Upload to Server
```bash
scp -r brightdata_session_data root@YOUR_DROPLET_IP:/root/cloudvoter/
```

---

## ✅ Checklist Before Deployment

- [ ] Session data copied from googleloginautomate
- [ ] Verified sessions exist in cloudvoter folder
- [ ] Each instance folder has 3 files (cookies, session_info, storage_state)
- [ ] Checked session_info.json for valid data
- [ ] Ready to deploy!

---

## 🎉 Summary

**Session data is essential for CloudVoter to work efficiently!**

- ✅ Copy sessions from googleloginautomate
- ✅ Use `copy_sessions.bat` for easy copying
- ✅ Verify sessions before deployment
- ✅ Sessions enable automatic launching
- ✅ No manual login required with sessions
- ✅ System manages 31-minute cooldowns automatically

**With session data, CloudVoter works exactly like googleloginautomate!**

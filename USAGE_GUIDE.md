# CloudVoter Usage Guide

## 🎯 Complete Step-by-Step Usage Instructions

---

## Part 1: Initial Setup (One-Time)

### Step 1: Create DigitalOcean Droplet

1. **Login to DigitalOcean**
   - Go to https://cloud.digitalocean.com
   - Click "Create" → "Droplets"

2. **Choose Configuration**
   ```
   Image:      Ubuntu 22.04 (LTS) x64
   Plan:       Basic
   CPU:        Regular with SSD
   RAM:        2 GB (minimum) or 4 GB (recommended)
   Location:   Choose closest to your target
   ```

3. **Authentication**
   - Choose SSH keys (recommended) or Password
   - Create droplet

4. **Note Your IP**
   ```
   Example: 165.227.123.45
   ```

### Step 2: Upload CloudVoter

**Option A: Using SCP (from your computer)**
```bash
# Navigate to Desktop
cd C:\Users\shubh\OneDrive\Desktop

# Upload cloudvoter folder
scp -r cloudvoter root@YOUR_DROPLET_IP:/root/
```

**Option B: Using Git (if you have a repository)**
```bash
# SSH into droplet
ssh root@YOUR_DROPLET_IP

# Clone repository
git clone https://github.com/yourusername/cloudvoter.git
cd cloudvoter
```

**Option C: Manual Upload**
1. Compress cloudvoter folder to .zip
2. Use FileZilla or WinSCP to upload
3. Extract on server

### Step 3: Deploy CloudVoter

```bash
# SSH into your droplet
ssh root@YOUR_DROPLET_IP

# Navigate to cloudvoter
cd cloudvoter

# Make deploy script executable
chmod +x deploy.sh

# Run deployment (takes 5-10 minutes)
./deploy.sh
```

**What the script does:**
- ✅ Updates system packages
- ✅ Installs Docker
- ✅ Installs Docker Compose
- ✅ Creates necessary directories
- ✅ Builds Docker containers
- ✅ Starts CloudVoter

**Expected Output:**
```
🚀 CloudVoter Deployment Script
================================
✓ Running as root
✓ Docker installed
✓ Docker Compose installed
✓ Directories created
🏗️  Building Docker containers...
🚀 Starting CloudVoter...
✓ CloudVoter is running!

================================
🎉 Deployment Complete!
================================

Access your CloudVoter control panel at:
  http://165.227.123.45
```

---

## Part 2: Daily Usage

### Accessing the Control Panel

1. **Open Your Browser**
   - Any browser (Chrome, Firefox, Safari, Edge)
   - On any device (Desktop, Laptop, Tablet, Phone)

2. **Navigate to Your Server**
   ```
   http://YOUR_DROPLET_IP
   
   Example: http://165.227.123.45
   ```

3. **You'll See the Control Panel**
   ```
   ┌─────────────────────────────────────────────┐
   │  CloudVoter Control Panel                   │
   │  Web-Based Voting Automation System         │
   │                                             │
   │  Status: ⚪ Monitoring Inactive             │
   └─────────────────────────────────────────────┘
   ```

### Starting Ultra Monitoring

#### Step 1: Verify Configuration

The control panel shows pre-filled configuration:

```
┌─────────────────────────────────────────────┐
│  Configuration Settings                      │
├─────────────────────────────────────────────┤
│                                             │
│  🗳️ Voting URL:                            │
│  [https://www.cutebabyvote.com/...]        │
│                                             │
│  🌐 Bright Data Username:                   │
│  [hl_47ba96ab]                              │
│                                             │
│  🔑 Bright Data Password:                   │
│  [••••••••••••]  👁                         │
│                                             │
└─────────────────────────────────────────────┘
```

**These are already configured correctly!**

#### Step 2: Click "Start Ultra Monitoring"

```
┌─────────────────────────────────────────────┐
│                                             │
│   [🚀 Start Ultra Monitoring]               │
│                                             │
└─────────────────────────────────────────────┘
```

**What happens when you click:**

1. **Button Changes**
   ```
   [🚀 Start Ultra Monitoring]  →  [⏹ Stop Ultra Monitoring]
   ```

2. **Status Updates**
   ```
   Status: ⚪ Inactive  →  Status: 🟢 Active
   ```

3. **Logs Start Appearing**
   ```
   [12:34:56] 🚀 Starting ultra monitoring...
   [12:34:57] ✅ Ultra monitoring started successfully
   [12:34:58] 🔍 Scanning saved sessions...
   [12:34:59] 📋 Found 3 saved sessions
   [12:35:00] ⏰ Instance #1: 5 minutes remaining in cooldown
   [12:35:01] ⏰ Instance #2: 15 minutes remaining in cooldown
   [12:35:02] ✅ Instance #3: Ready to launch!
   [12:35:03] 🚀 Launching Instance #3...
   [12:35:05] 🌐 Assigned IP: 103.45.67.89
   [12:35:08] 🔍 Navigating to voting page...
   [12:35:10] ✅ Navigation successful
   [12:35:11] 🔑 Checking login status...
   [12:35:12] ✅ Already logged in
   [12:35:13] 🗳️ Starting voting cycle...
   ```

#### Step 3: Monitor the Dashboard

The dashboard updates in real-time:

```
┌─────────────────────────────────────────────┐
│  Dashboard                                   │
├─────────────────────────────────────────────┤
│                                             │
│  📊 Statistics                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ Active   │ │ Success  │ │ Success  │   │
│  │ Instances│ │ Votes    │ │ Rate     │   │
│  │    3     │ │   156    │ │  94.2%   │   │
│  └──────────┘ └──────────┘ └──────────┘   │
│                                             │
│  🎮 Active Instances                        │
│  ┌─────────────────────────────────────┐   │
│  │ Instance #1                         │   │
│  │ IP: 103.45.67.89                    │   │
│  │ Status: ✅ Vote Successful          │   │
│  │ Next vote in: 28 minutes            │   │
│  └─────────────────────────────────────┘   │
│  ┌─────────────────────────────────────┐   │
│  │ Instance #2                         │   │
│  │ IP: 104.56.78.90                    │   │
│  │ Status: ⏳ Cooldown (12m remaining) │   │
│  └─────────────────────────────────────┘   │
│  ┌─────────────────────────────────────┐   │
│  │ Instance #3                         │   │
│  │ IP: 105.67.89.01                    │   │
│  │ Status: 🔑 Waiting for Login        │   │
│  └─────────────────────────────────────┘   │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Part 3: Understanding What Happens

### The Ultra Monitoring Cycle

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  1. SCAN SESSIONS (Every 2 seconds)                    │
│     ↓                                                   │
│     Checks brightdata_session_data/ folder             │
│     Looks for saved browser sessions                   │
│                                                         │
│  2. CHECK COOLDOWNS                                     │
│     ↓                                                   │
│     For each session:                                  │
│     - Read last_vote_time                              │
│     - Calculate time since last vote                   │
│     - If >= 31 minutes → Ready to launch               │
│     - If < 31 minutes → Show remaining time            │
│                                                         │
│  3. LAUNCH READY INSTANCES                             │
│     ↓                                                   │
│     For each ready session:                            │
│     - Get unique IP from Bright Data                   │
│     - Launch browser with saved session                │
│     - Navigate to voting page                          │
│     - Check if still logged in                         │
│                                                         │
│  4. HANDLE LOGIN STATUS                                │
│     ↓                                                   │
│     If logged in:                                      │
│     → Start voting cycle                               │
│                                                         │
│     If not logged in:                                  │
│     → Pause and show "Waiting for Login"               │
│     → Keep browser open for manual login               │
│                                                         │
│  5. VOTING CYCLE (If logged in)                        │
│     ↓                                                   │
│     - Find vote button                                 │
│     - Click vote button                                │
│     - Wait for response                                │
│     - Check success/failure message                    │
│     - Save session data                                │
│     - Wait 31 minutes                                  │
│     - Repeat                                           │
│                                                         │
│  6. REPEAT                                             │
│     ↓                                                   │
│     Loop back to step 1                                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### What You See in Real-Time

**Logs Tab shows everything:**

```
[12:35:00] 🔍 LOOP #1 | ⏰ 12:35:00 | 🚀 3 ACTIVE | 🔍 SCANNING
[12:35:02] 🔍 Found 5 saved sessions
[12:35:03] ⏰ Instance #1: 28 minutes remaining
[12:35:03] ⏰ Instance #2: 15 minutes remaining
[12:35:03] ✅ Instance #3: Ready to launch!
[12:35:03] ✅ Instance #4: Ready to launch!
[12:35:03] ⏰ Instance #5: 2 minutes remaining
[12:35:04] 🚀 Launching Instance #3 from saved session
[12:35:05] 🌐 Bright Data assigned IP: 103.45.67.89
[12:35:08] 🔍 Navigating to voting page...
[12:35:10] ✅ Navigation successful
[12:35:11] 🔑 Checking login status...
[12:35:12] ✅ Already logged in - session valid
[12:35:13] 🗳️ Attempting vote...
[12:35:15] ✅ Vote button clicked
[12:35:18] ✅ Vote successful! "Thank you for voting"
[12:35:19] 💾 Session saved
[12:35:20] ⏰ Instance #3 waiting 31 minutes for next cycle
```

---

## Part 4: Common Scenarios

### Scenario 1: First Time Setup (No Saved Sessions)

**What happens:**
1. Click "Start Ultra Monitoring"
2. System scans but finds no saved sessions
3. You need to manually launch first instance

**Steps:**
```
1. Click "Launch Instance" button
2. System creates new browser with unique IP
3. Browser navigates to voting page
4. System detects login required
5. Status shows "🔑 Waiting for Login"
6. Browser stays open (on server)
7. You need to login via VNC or similar
8. After login, system saves session
9. Voting cycle starts automatically
10. Session saved for future automatic use
```

### Scenario 2: Saved Sessions Exist

**What happens:**
1. Click "Start Ultra Monitoring"
2. System scans brightdata_session_data/
3. Finds saved sessions
4. Checks cooldown for each
5. Launches ready instances automatically
6. No manual intervention needed!

**Timeline:**
```
Time    | Action
--------|--------------------------------------------------
12:00   | You click "Start Ultra Monitoring"
12:00   | System finds 3 saved sessions
12:00   | Instance #1: 5 min cooldown remaining
12:00   | Instance #2: 15 min cooldown remaining
12:00   | Instance #3: Ready! Launches immediately
12:05   | Instance #1 cooldown complete, launches automatically
12:15   | Instance #2 cooldown complete, launches automatically
12:31   | Instance #3 completes vote, waits 31 minutes
13:02   | Instance #3 launches again automatically
```

### Scenario 3: Login Required

**What happens:**
1. Instance launches
2. Navigates to voting page
3. Detects Google login required
4. Status changes to "🔑 Waiting for Login"
5. Browser stays open on server
6. You need to login manually

**How to handle:**
```
Option 1: VNC to Server
- Install VNC server on droplet
- Connect via VNC client
- See the browser window
- Perform Google login
- System detects login completion
- Voting starts automatically

Option 2: Remote Desktop
- Use Chrome Remote Desktop
- Access server desktop
- Login to Google
- System continues automatically

Option 3: Let it wait
- System keeps browser open
- Periodically checks if logged in
- Once logged in, continues automatically
```

### Scenario 4: Hourly Limit Hit

**What happens:**
1. Instance attempts vote
2. Receives "hourly limit" message
3. System detects the message
4. Marks instance as in cooldown
5. Waits 31 minutes
6. Tries again automatically

**Logs show:**
```
[12:35:15] 🗳️ Attempting vote...
[12:35:18] ⚠️ Hourly limit detected
[12:35:19] ⏰ Instance #3 entering cooldown
[12:35:20] ⏰ Will retry in 31 minutes
[13:06:20] ⏰ Cooldown complete for Instance #3
[13:06:21] 🚀 Launching Instance #3...
[13:06:25] 🗳️ Attempting vote...
[13:06:28] ✅ Vote successful!
```

---

## Part 5: Monitoring and Management

### Checking System Status

**Dashboard Tab:**
- Shows active instances count
- Shows successful votes
- Shows success rate
- Shows each instance status

**Logs Tab:**
- Shows real-time activity
- Auto-scrolls to latest
- Timestamped entries
- Color-coded by importance

### Manual Actions Available

**1. Launch Instance**
```
Click "Launch Instance" button
→ Manually creates new browser instance
→ Gets unique IP from Bright Data
→ Navigates to voting page
→ Checks login status
```

**2. Stop Monitoring**
```
Click "Stop Ultra Monitoring" button
→ Stops automatic session scanning
→ Existing instances continue their cycles
→ No new instances launched
```

**3. View Statistics**
```
Dashboard shows:
- Total active instances
- Successful votes count
- Failed votes count
- Success rate percentage
```

---

## Part 6: Maintenance

### Daily Checks

**Morning Check (5 minutes):**
```
1. Open control panel
2. Check dashboard statistics
3. Verify instances are active
4. Review logs for any errors
5. Ensure monitoring is active
```

### Weekly Tasks

**Session Backup (10 minutes):**
```bash
# SSH into server
ssh root@YOUR_DROPLET_IP

# Create backup
cd cloudvoter
tar -czf backup-$(date +%Y%m%d).tar.gz brightdata_session_data/

# Download backup
exit
scp root@YOUR_DROPLET_IP:/root/cloudvoter/backup-*.tar.gz ./
```

**Log Review:**
```
1. Check voting_logs.csv
2. Review success rate
3. Identify any patterns
4. Adjust if needed
```

### Monthly Tasks

**System Update:**
```bash
# SSH into server
ssh root@YOUR_DROPLET_IP

# Update system
apt-get update && apt-get upgrade -y

# Restart CloudVoter
cd cloudvoter
docker-compose restart
```

---

## Part 7: Troubleshooting

### Problem: Can't Access Control Panel

**Check 1: Is server running?**
```bash
ssh root@YOUR_DROPLET_IP
docker-compose ps

# Should show:
# cloudvoter        Up      0.0.0.0:5000->5000/tcp
# cloudvoter-nginx  Up      0.0.0.0:80->80/tcp
```

**Check 2: Is firewall blocking?**
```bash
ufw status
ufw allow 80/tcp
ufw allow 443/tcp
```

**Check 3: Check logs**
```bash
docker-compose logs nginx
docker-compose logs cloudvoter
```

### Problem: Instances Not Launching

**Check 1: Verify credentials**
```
1. Open control panel
2. Check Bright Data username/password
3. Click "Test Connection" if available
```

**Check 2: Check logs**
```
Look for errors like:
- "Authentication failed"
- "Could not get unique IP"
- "Proxy connection failed"
```

**Check 3: Verify saved sessions**
```bash
ssh root@YOUR_DROPLET_IP
cd cloudvoter/brightdata_session_data
ls -la

# Should show instance_1, instance_2, etc.
```

### Problem: Login Required Every Time

**Cause:** Sessions not being saved properly

**Solution:**
```bash
# Check session directory permissions
cd cloudvoter
chmod -R 755 brightdata_session_data/

# Restart CloudVoter
docker-compose restart
```

---

## Part 8: Advanced Usage

### Viewing Live Logs

**From Server:**
```bash
ssh root@YOUR_DROPLET_IP
cd cloudvoter
docker-compose logs -f cloudvoter
```

**From Browser:**
```
Click "Logs" tab in control panel
→ Shows real-time logs
→ Auto-scrolls to latest
→ Searchable
```

### Manually Managing Instances

**View All Instances:**
```bash
# SSH into server
ssh root@YOUR_DROPLET_IP
cd cloudvoter/brightdata_session_data
ls -la

# Each instance_N folder contains:
# - storage_state.json (cookies, localStorage)
# - session_info.json (metadata)
```

**Delete Specific Instance:**
```bash
# Remove instance folder
rm -rf brightdata_session_data/instance_3/

# System will no longer restore this session
```

### Backup and Restore

**Backup:**
```bash
# Create full backup
tar -czf cloudvoter-backup-$(date +%Y%m%d).tar.gz \
    brightdata_session_data/ \
    voting_logs.csv \
    .env

# Download to local machine
scp root@YOUR_DROPLET_IP:/root/cloudvoter/cloudvoter-backup-*.tar.gz ./
```

**Restore:**
```bash
# Upload backup to server
scp cloudvoter-backup-20250101.tar.gz root@YOUR_DROPLET_IP:/root/cloudvoter/

# SSH into server
ssh root@YOUR_DROPLET_IP
cd cloudvoter

# Extract backup
tar -xzf cloudvoter-backup-20250101.tar.gz

# Restart
docker-compose restart
```

---

## 🎯 Quick Reference

### Essential Commands

```bash
# Start CloudVoter
docker-compose up -d

# Stop CloudVoter
docker-compose down

# Restart CloudVoter
docker-compose restart

# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Update and restart
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

### Essential URLs

```
Control Panel:  http://YOUR_DROPLET_IP
API Health:     http://YOUR_DROPLET_IP/api/health
API Status:     http://YOUR_DROPLET_IP/api/status
```

### Support Checklist

When asking for help, provide:
- [ ] CloudVoter version
- [ ] Error message from logs
- [ ] Steps to reproduce
- [ ] Expected vs actual behavior
- [ ] Browser console errors (F12)

---

**That's it!** You now know everything about using CloudVoter. The system is designed to be simple: just click "Start Ultra Monitoring" and let it run automatically.

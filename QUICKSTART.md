# CloudVoter Quick Start Guide

Get CloudVoter running in 5 minutes!

## 🚀 Quick Deploy to DigitalOcean

### 0. Copy All Data (1 minute) ⚠️ CRITICAL

**Before deploying, copy ALL data from googleloginautomate:**

```bash
# In cloudvoter folder, run:
copy_all_data.bat

# This copies:
# ✓ Session data (saved Google logins)
# ✓ Voting logs (voting history for cooldown detection)
```

**Why both are needed:**
- **Sessions**: Avoid manual Google login
- **Logs**: System uses this to decide when to launch instances!

📖 **See SESSION_DATA_SETUP.md and VOTING_LOGS_SETUP.md**

### 1. Create Droplet (2 minutes)

```bash
# On DigitalOcean:
# - Create Ubuntu 22.04 droplet (2GB RAM minimum)
# - Note your droplet IP
```

### 2. Deploy CloudVoter (2 minutes)

```bash
# SSH into your droplet
ssh root@YOUR_DROPLET_IP

# Download and run deployment script
curl -sSL https://raw.githubusercontent.com/yourusername/cloudvoter/main/deploy.sh | bash

# OR if you have the files:
cd cloudvoter
chmod +x deploy.sh
sudo ./deploy.sh
```

### 3. Access Control Panel (1 minute)

```bash
# Open in browser:
http://YOUR_DROPLET_IP
```

### 4. Start Voting

1. **Configure Credentials** (already pre-filled):
   - Bright Data Username: `hl_47ba96ab`
   - Bright Data Password: `tcupn0cw7pbz`

2. **Set Voting URL**:
   ```
   https://www.cutebabyvote.com/october-2025/?contest=photo-detail&photo_id=463146
   ```

3. **Click "Start Ultra Monitoring"** 🚀

That's it! CloudVoter will now:
- ✅ Launch browser instances with unique IPs
- ✅ Detect login requirements automatically
- ✅ Manage voting cycles (31-minute intervals)
- ✅ Handle hourly limits
- ✅ Restore sessions after cooldowns

## 📊 Monitor Your Voting

The dashboard shows:
- **Active Instances**: Number of running browsers
- **Successful Votes**: Total votes cast
- **Success Rate**: Voting success percentage
- **Live Logs**: Real-time system activity

## 🎮 Control Panel Features

### Start Ultra Monitoring
Automatically manages all voting instances:
- Launches instances from saved sessions
- Detects cooldown periods
- Handles login requirements
- Manages 31-minute voting cycles

### Launch Instance
Manually launch a new browser instance with unique IP

### Instance Management
- View all active instances
- See IP addresses and status
- Monitor login requirements
- Track voting cycles

## 📱 Access from Anywhere

CloudVoter is web-based, so you can:
- Access from any device with a browser
- Monitor from your phone
- Control from anywhere with internet

## 🔧 Common Tasks

### View Logs
```bash
docker-compose logs -f
```

### Restart System
```bash
docker-compose restart
```

### Stop System
```bash
docker-compose down
```

### Update Credentials
1. Edit `.env` file
2. Restart: `docker-compose restart`

## 💡 Tips

1. **Let Ultra Monitoring Run**: It automatically handles everything
2. **Check Logs**: Monitor the "Logs" tab for real-time updates
3. **Session Persistence**: Login once, system reuses sessions
4. **Automatic Recovery**: System handles errors and restarts automatically

## 🆘 Quick Troubleshooting

### Can't Access Control Panel?
```bash
# Check if running
docker-compose ps

# Check firewall
ufw allow 80/tcp
```

### No Instances Launching?
1. Check Bright Data credentials
2. View logs: `docker-compose logs -f`
3. Verify voting URL is correct

### Browser Not Opening?
- System runs in headless mode on server
- Browsers run in background
- Monitor status in control panel

## 📚 Next Steps

- **Setup SSL**: See DEPLOYMENT.md for HTTPS setup
- **Configure Domain**: Point your domain to droplet IP
- **Backup Sessions**: Regularly backup `brightdata_session_data/`
- **Monitor Resources**: Use `docker stats` to check usage

## 🎯 How Ultra Monitoring Works

1. **Scans saved sessions** every 2 seconds
2. **Checks cooldown periods** (31 minutes)
3. **Launches ready instances** automatically
4. **Manages login requirements** (pauses for manual login)
5. **Handles hourly limits** (waits and retries)
6. **Saves sessions** for reuse

## 🔐 Security Notes

- Change `SECRET_KEY` in `.env` for production
- Use HTTPS in production (see DEPLOYMENT.md)
- Keep Bright Data credentials secure
- Regular system updates recommended

## 📞 Support

- **Logs**: Check `docker-compose logs -f` for errors
- **Documentation**: See README.md and DEPLOYMENT.md
- **Status**: Monitor dashboard for system health

---

**That's it!** CloudVoter is now running and managing your voting automation. The system will handle everything automatically once you click "Start Ultra Monitoring".

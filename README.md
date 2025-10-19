# CloudVoter - Web-Based Voting Automation Control Panel

A web-based control panel for managing multi-instance voting automation with Bright Data proxy integration. This application can be deployed to DigitalOcean and accessed via web browser.

## Features

- **Web-Based Control Panel**: Access from any browser
- **Ultra Monitoring**: Automated voting cycle management
- **Multi-Instance Support**: Run multiple browser instances with unique IPs
- **Real-Time Updates**: WebSocket-based live status updates
- **Session Management**: Persistent Google login sessions
- **Bright Data Integration**: Automatic proxy rotation with unique IPs

## Architecture

### Backend (Flask + Python)
- Flask REST API for control operations
- Flask-SocketIO for real-time updates
- Playwright for browser automation
- Bright Data proxy integration
- Async task management with asyncio

### Frontend (React + TailwindCSS)
- Modern responsive UI
- Real-time status dashboard
- Instance management controls
- Live log streaming
- Configuration management

## Project Structure

```
cloudvoter/
├── backend/
│   ├── app.py                 # Flask application
│   ├── voter_engine.py        # Core voting automation logic
│   ├── config.py              # Configuration management
│   ├── utils.py               # Utility functions
│   ├── vote_logger.py         # Vote logging system
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── App.jsx           # Main application
│   │   └── index.js          # Entry point
│   ├── package.json
│   └── tailwind.config.js
├── deployment/
│   ├── Dockerfile            # Docker configuration
│   ├── docker-compose.yml    # Multi-container setup
│   ├── nginx.conf            # Nginx reverse proxy
│   └── deploy.sh             # Deployment script
├── brightdata_session_data/  # Session storage
├── failure_screenshots/      # Error screenshots
└── README.md

```

## Installation

### ⚠️ IMPORTANT: Copy Data from GoogleLoginAutomate

**Before starting, copy saved data from googleloginautomate:**

```bash
# Run the copy script (copies EVERYTHING)
copy_all_data.bat

# This copies:
# ✓ Session data (brightdata_session_data/)
# ✓ Voting logs (voting_logs.csv)
```

**Why is this critical?**

1. **Session Data** - Contains saved Google logins
   - Without it: Must login manually for each instance
   
2. **Voting Logs** - Used for cooldown detection and decisions
   - Without it: System can't determine when instances last voted
   - System may launch instances too early
   - Can't track voting history

📖 **See SESSION_DATA_SETUP.md and VOTING_LOGS_SETUP.md for details**

### Local Development

1. **Backend Setup**
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

2. **Frontend Setup**
```bash
cd frontend
npm install
```

3. **Run Development Servers**
```bash
# Terminal 1 - Backend
cd backend
python app.py

# Terminal 2 - Frontend
cd frontend
npm start
```

### DigitalOcean Deployment

1. **Prerequisites**
   - DigitalOcean account
   - Docker installed on droplet
   - Domain name (optional)

2. **Deploy with Docker**
```bash
# Clone repository on droplet
git clone <your-repo>
cd cloudvoter

# Build and run
docker-compose up -d
```

3. **Access Application**
   - Open browser: `http://your-droplet-ip:3000`
   - Or with domain: `https://your-domain.com`

## Configuration

### Bright Data Credentials

Credentials are loaded from `backend/config.py`:

```python
# backend/config.py
BRIGHT_DATA_USERNAME = "hl_47ba96ab"
BRIGHT_DATA_PASSWORD = "tcupn0cw7pbz"
```

**When credentials change:**
1. Update `backend/config.py`
2. Restart backend: `docker-compose restart cloudvoter`
3. Credentials auto-load in web UI

📖 **See CREDENTIALS_UPDATE.md for detailed instructions**

### Voting URLs
Configure target voting URLs in `backend/config.py`:
```python
TARGET_URLS = [
    "https://www.cutebabyvote.com/october-2025/?contest=photo-detail&photo_id=463146"
]
```

## Usage

### Starting Ultra Monitoring

1. Open the web control panel
2. Configure Bright Data credentials
3. Set voting URL
4. Click **"Start Ultra Monitoring"** button
5. System will:
   - Launch browser instances with unique IPs
   - Detect login requirements
   - Manage voting cycles automatically
   - Handle hourly limits
   - Restore sessions after cooldowns

### Monitoring Features

- **Dashboard**: Real-time statistics and status
- **Active Instances**: View all running browser instances
- **Voting Queue**: See scheduled voting times
- **Saved Sessions**: Manage persistent login sessions
- **Vote History**: Track all voting attempts
- **Live Logs**: Real-time system logs

## API Endpoints

### Control Operations
- `POST /api/start-monitoring` - Start ultra monitoring
- `POST /api/stop-monitoring` - Stop monitoring
- `POST /api/launch-instance` - Launch new instance
- `POST /api/pause-instance` - Pause specific instance
- `POST /api/resume-instance` - Resume paused instance
- `DELETE /api/delete-instance` - Delete instance

### Status & Data
- `GET /api/status` - Get system status
- `GET /api/instances` - Get all instances
- `GET /api/sessions` - Get saved sessions
- `GET /api/vote-history` - Get voting history
- `GET /api/statistics` - Get statistics

### WebSocket Events
- `connect` - Client connected
- `log_update` - New log message
- `status_update` - Status changed
- `instance_update` - Instance status changed

## Environment Variables

Create `.env` file:
```env
FLASK_ENV=production
SECRET_KEY=your-secret-key
BRIGHT_DATA_USERNAME=hl_47ba96ab
BRIGHT_DATA_PASSWORD=tcupn0cw7pbz
PORT=5000
```

## Security Considerations

- Use HTTPS in production
- Set strong SECRET_KEY
- Implement authentication (optional)
- Restrict access by IP (optional)
- Keep Bright Data credentials secure

## Troubleshooting

### Browser Not Launching
- Check Playwright installation: `playwright install chromium`
- Verify Bright Data credentials
- Check proxy connectivity

### Session Not Saving
- Ensure `brightdata_session_data/` directory exists
- Check file permissions
- Verify disk space

### WebSocket Connection Failed
- Check firewall settings
- Verify port 5000 is accessible
- Check CORS configuration

## License

MIT License

## Support

For issues and questions, please open an issue on GitHub.

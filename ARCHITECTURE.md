# CloudVoter Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER DEVICES                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Desktop  │  │  Laptop  │  │  Tablet  │  │  Mobile  │       │
│  │ Browser  │  │  Browser │  │  Browser │  │  Browser │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       │             │              │             │              │
│       └─────────────┴──────────────┴─────────────┘              │
│                          │                                       │
│                    HTTP/HTTPS                                    │
│                          │                                       │
└──────────────────────────┼───────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  DIGITALOCEAN DROPLET                            │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    NGINX (Port 80/443)                     │ │
│  │              Reverse Proxy & Load Balancer                 │ │
│  └──────────────────────────┬─────────────────────────────────┘ │
│                             │                                    │
│                             ▼                                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              FLASK BACKEND (Port 5000)                     │ │
│  │                                                            │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │              REST API Endpoints                      │ │ │
│  │  │  • POST /api/start-monitoring                       │ │ │
│  │  │  • POST /api/stop-monitoring                        │ │ │
│  │  │  • POST /api/launch-instance                        │ │ │
│  │  │  • GET  /api/status                                 │ │ │
│  │  │  • GET  /api/instances                              │ │ │
│  │  │  • GET  /api/statistics                             │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  │                                                            │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │           WebSocket (Socket.IO)                      │ │ │
│  │  │  • Real-time log updates                            │ │ │
│  │  │  • Status updates                                    │ │ │
│  │  │  • Instance updates                                  │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  │                                                            │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │           Voter Engine (Core Logic)                  │ │ │
│  │  │                                                       │ │ │
│  │  │  ┌─────────────────────────────────────────────┐    │ │ │
│  │  │  │     MultiInstanceVoter Manager              │    │ │ │
│  │  │  │  • Instance lifecycle management             │    │ │ │
│  │  │  │  • Session restoration                       │    │ │ │
│  │  │  │  • Cooldown detection                        │    │ │ │
│  │  │  │  • Browser monitoring                        │    │ │ │
│  │  │  └─────────────────────────────────────────────┘    │ │ │
│  │  │                                                       │ │ │
│  │  │  ┌─────────────────────────────────────────────┐    │ │ │
│  │  │  │     VoterInstance (Per Browser)             │    │ │ │
│  │  │  │  • Playwright browser automation             │    │ │ │
│  │  │  │  • Navigation & voting logic                 │    │ │ │
│  │  │  │  • Login detection                           │    │ │ │
│  │  │  │  • Session persistence                       │    │ │ │
│  │  │  └─────────────────────────────────────────────┘    │ │ │
│  │  │                                                       │ │ │
│  │  │  ┌─────────────────────────────────────────────┐    │ │ │
│  │  │  │     BrightDataAPI (Proxy Manager)           │    │ │ │
│  │  │  │  • Proxy configuration                       │    │ │ │
│  │  │  │  • IP rotation                               │    │ │ │
│  │  │  │  • Connection testing                        │    │ │ │
│  │  │  └─────────────────────────────────────────────┘    │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  │                                                            │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │           React Frontend (Static Build)              │ │ │
│  │  │  • Dashboard UI                                      │ │ │
│  │  │  • Control Panel                                     │ │ │
│  │  │  • Live Logs                                         │ │ │
│  │  │  • Instance Management                               │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    PERSISTENT STORAGE                      │ │
│  │                                                            │ │
│  │  brightdata_session_data/    voting_logs.csv             │ │
│  │  ├── instance_1/             failure_screenshots/         │ │
│  │  │   ├── cookies.json                                     │ │
│  │  │   ├── session_info.json                                │ │
│  │  │   └── storage_state.json                               │ │
│  │  ├── instance_2/                                           │ │
│  │  └── instance_N/                                           │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BRIGHT DATA PROXY NETWORK                     │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Proxy 1  │  │ Proxy 2  │  │ Proxy 3  │  │ Proxy N  │       │
│  │ IP: x.x  │  │ IP: y.y  │  │ IP: z.z  │  │ IP: n.n  │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       │             │              │             │              │
│       └─────────────┴──────────────┴─────────────┘              │
│                          │                                       │
└──────────────────────────┼───────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TARGET VOTING WEBSITE                         │
│         https://www.cutebabyvote.com/october-2025/              │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. User Clicks "Start Ultra Monitoring"

```
User Browser
    │
    │ HTTP POST /api/start-monitoring
    │ { username, password, voting_url }
    ▼
Flask Backend
    │
    │ Validate credentials
    │ Initialize MultiInstanceVoter
    │ Start monitoring loop in asyncio
    ▼
Monitoring Loop (every 2 seconds)
    │
    │ Scan brightdata_session_data/
    │ Check cooldown periods (31 min)
    │ Find ready instances
    ▼
Launch Ready Instances
    │
    ├─► Get unique IP from Bright Data
    │   └─► Create VoterInstance
    │       └─► Initialize Playwright browser
    │           └─► Navigate to voting page
    │               └─► Check login required
    │                   ├─► If YES: Pause for manual login
    │                   └─► If NO: Start voting cycle
    │
    └─► Emit WebSocket updates to browser
        └─► User sees real-time status
```

### 2. Voting Cycle Flow

```
VoterInstance.run_voting_cycle()
    │
    ▼
Navigate to voting page
    │
    ▼
Check if login required
    │
    ├─► YES: Pause and wait for manual login
    │         └─► Monitor login completion
    │             └─► Resume when logged in
    │
    └─► NO: Continue to voting
        │
        ▼
    Attempt vote
        │
        ├─► Find vote button
        │   └─► Click button
        │       └─► Wait for response
        │           └─► Check success/failure
        │
        ▼
    Save session data
        │
        ├─► storage_state.json (cookies, localStorage)
        ├─► session_info.json (metadata)
        └─► Log to voting_logs.csv
        │
        ▼
    Wait 31 minutes
        │
        └─► Repeat cycle
```

### 3. WebSocket Real-Time Updates

```
Backend Event
    │
    │ Log message / Status change
    │
    ▼
SocketIO.emit('log_update')
    │
    │ WebSocket connection
    │
    ▼
Frontend Socket Handler
    │
    │ Update React state
    │
    ▼
UI Re-renders
    │
    └─► User sees update immediately
```

## Component Interactions

### Backend Components

```
app.py (Flask Application)
    │
    ├─► voter_engine.py (Core Logic)
    │   ├─► MultiInstanceVoter
    │   │   ├─► Manages multiple VoterInstance objects
    │   │   ├─► Coordinates IP allocation
    │   │   └─► Handles session restoration
    │   │
    │   ├─► VoterInstance
    │   │   ├─► Controls single browser
    │   │   ├─► Performs voting actions
    │   │   └─► Manages session data
    │   │
    │   └─► BrightDataAPI
    │       ├─► Proxy configuration
    │       └─► IP management
    │
    ├─► config.py (Configuration)
    │   ├─► Voting URLs
    │   ├─► Timing settings
    │   └─► Selectors
    │
    └─► vote_logger.py (Logging)
        ├─► CSV logging
        └─► Statistics calculation
```

### Frontend Components

```
App.jsx (Main Component)
    │
    ├─► State Management
    │   ├─► monitoringActive
    │   ├─► instances[]
    │   ├─► logs[]
    │   ├─► statistics{}
    │   └─► config{}
    │
    ├─► WebSocket Connection
    │   ├─► Connect to backend
    │   ├─► Listen for updates
    │   └─► Update state
    │
    ├─► API Calls (Axios)
    │   ├─► Start/Stop monitoring
    │   ├─► Launch instance
    │   ├─► Fetch status
    │   └─► Get statistics
    │
    └─► UI Components
        ├─► Dashboard Tab
        │   ├─► StatCard
        │   ├─► Control Panel
        │   └─► InstanceCard
        │
        └─► Logs Tab
            └─► Live log display
```

## Deployment Architecture

### Docker Containers

```
Docker Compose
    │
    ├─► cloudvoter (Main Application)
    │   ├─► Flask Backend
    │   ├─► React Frontend (built)
    │   ├─► Playwright + Chromium
    │   └─► Python dependencies
    │
    └─► nginx (Reverse Proxy)
        ├─► HTTP/HTTPS termination
        ├─► WebSocket proxying
        └─► Static file serving
```

### Network Flow

```
Internet
    │
    │ Port 80/443
    ▼
Nginx Container
    │
    │ Reverse Proxy
    │ Port 5000
    ▼
CloudVoter Container
    │
    ├─► Flask API (Port 5000)
    ├─► WebSocket (Socket.IO)
    └─► Playwright Browsers
        │
        │ Via Bright Data Proxy
        ▼
    Target Website
```

## Session Persistence

### Session Storage Structure

```
brightdata_session_data/
    │
    ├─► instance_1/
    │   ├─► storage_state.json
    │   │   ├─► cookies
    │   │   ├─► localStorage
    │   │   └─► sessionStorage
    │   │
    │   └─► session_info.json
    │       ├─► instance_id
    │       ├─► proxy_ip
    │       ├─► session_id
    │       ├─► last_vote_time
    │       └─► vote_count
    │
    ├─► instance_2/
    └─► instance_N/
```

### Session Lifecycle

```
1. New Instance Launch
    │
    ├─► Get unique IP from Bright Data
    ├─► Create Playwright browser with proxy
    ├─► Navigate to voting page
    └─► Check login status
        │
        ├─► If logged in:
        │   └─► Save session immediately
        │
        └─► If not logged in:
            └─► Wait for manual login
                └─► Save session after login

2. Session Reuse (31 min later)
    │
    ├─► Load storage_state.json
    ├─► Restore browser context
    ├─► Navigate to voting page
    └─► Verify still logged in
        │
        ├─► If YES: Continue voting
        └─► If NO: Request login again

3. Session Expiry
    │
    └─► Detect login required
        └─► Mark session as expired
            └─► Request new login
```

## Monitoring Loop Logic

### Ultra Monitoring Algorithm

```
while monitoring_active:
    │
    ├─► Scan brightdata_session_data/
    │   │
    │   └─► For each instance_N/:
    │       │
    │       ├─► Load session_info.json
    │       ├─► Get last_vote_time
    │       ├─► Calculate time_since_vote
    │       │
    │       └─► If time_since_vote >= 31 minutes:
    │           └─► Add to ready_instances[]
    │
    ├─► For each ready instance:
    │   │
    │   ├─► Check if IP already in use
    │   ├─► Create VoterInstance
    │   ├─► Initialize browser with saved session
    │   ├─► Navigate to voting page
    │   ├─► Check login status
    │   │
    │   ├─► If logged in:
    │   │   └─► Start voting cycle
    │   │
    │   └─► If not logged in:
    │       └─► Pause for manual login
    │
    ├─► Emit status updates via WebSocket
    │
    └─► Sleep 2 seconds
        └─► Repeat
```

## Security Architecture

### Authentication Flow

```
User → Nginx (SSL/TLS) → Flask Backend
                            │
                            ├─► Validate credentials
                            ├─► Check SECRET_KEY
                            └─► Process request
```

### Data Protection

```
Sensitive Data:
    │
    ├─► Bright Data Credentials
    │   └─► Stored in .env file
    │       └─► Not in git (.gitignore)
    │
    ├─► Session Data
    │   └─► Stored in brightdata_session_data/
    │       └─► Contains cookies and tokens
    │
    └─► SECRET_KEY
        └─► Used for Flask session encryption
```

## Scalability

### Horizontal Scaling

```
Load Balancer
    │
    ├─► CloudVoter Instance 1
    ├─► CloudVoter Instance 2
    └─► CloudVoter Instance N
        │
        └─► Shared Storage (NFS/S3)
            └─► brightdata_session_data/
```

### Vertical Scaling

```
Increase Droplet Resources:
    │
    ├─► More RAM → More concurrent instances
    ├─► More CPU → Faster processing
    └─► More Disk → More session storage
```

This architecture ensures CloudVoter is:
- **Reliable**: Docker containers with auto-restart
- **Scalable**: Can handle multiple instances
- **Maintainable**: Clear separation of concerns
- **Secure**: SSL/TLS, credential management
- **Real-time**: WebSocket for live updates
- **Accessible**: Web-based from anywhere

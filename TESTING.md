# CloudVoter Testing Guide

## Pre-Deployment Testing Checklist

### Local Development Testing

#### 1. Backend Testing

```bash
cd backend

# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Run backend
python app.py

# Expected output:
# ✅ Event loop thread started
# ✅ Starting CloudVoter Backend Server...
# ✅ Server will be available at http://localhost:5000
```

**Test API Endpoints:**

```bash
# Health check
curl http://localhost:5000/api/health

# Expected: {"status":"healthy","timestamp":"...","monitoring_active":false}

# Get status
curl http://localhost:5000/api/status

# Expected: {"monitoring_active":false,"active_instances":[],"total_instances":0}
```

#### 2. Frontend Testing

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm start

# Expected:
# ✅ Compiled successfully!
# ✅ webpack compiled with 0 warnings
# ✅ Opens browser at http://localhost:3000
```

**Test UI Components:**

- [ ] Dashboard loads without errors
- [ ] Configuration fields are editable
- [ ] Buttons are clickable
- [ ] Logs tab switches correctly
- [ ] WebSocket connection indicator shows

#### 3. Integration Testing

**Start both backend and frontend, then test:**

1. **Configuration Test**
   - [ ] Enter Bright Data credentials
   - [ ] Enter voting URL
   - [ ] Click "Test Connection" (if implemented)

2. **Monitoring Test**
   - [ ] Click "Start Ultra Monitoring"
   - [ ] Verify button changes to "Stop Ultra Monitoring"
   - [ ] Check logs for startup messages
   - [ ] Verify monitoring status indicator turns green

3. **Instance Launch Test**
   - [ ] Click "Launch Instance"
   - [ ] Watch logs for instance creation
   - [ ] Verify instance appears in dashboard
   - [ ] Check instance status updates

4. **WebSocket Test**
   - [ ] Open browser console
   - [ ] Verify WebSocket connection established
   - [ ] Trigger action (start monitoring)
   - [ ] Verify real-time log updates appear

5. **Stop Monitoring Test**
   - [ ] Click "Stop Ultra Monitoring"
   - [ ] Verify button changes back
   - [ ] Check logs for shutdown messages
   - [ ] Verify status indicator turns gray

## Docker Testing

### Build Test

```bash
# Build Docker image
docker-compose build

# Expected:
# ✅ Successfully built frontend
# ✅ Successfully installed Python packages
# ✅ Successfully installed Playwright
# ✅ Image built successfully
```

### Container Test

```bash
# Start containers
docker-compose up -d

# Check status
docker-compose ps

# Expected:
# cloudvoter        running   0.0.0.0:5000->5000/tcp
# cloudvoter-nginx  running   0.0.0.0:80->80/tcp

# Check logs
docker-compose logs -f

# Expected:
# ✅ Flask application started
# ✅ Gunicorn worker started
# ✅ Nginx started
```

### Access Test

```bash
# Test from host machine
curl http://localhost

# Expected: HTML response from React app

# Test API through Nginx
curl http://localhost/api/health

# Expected: {"status":"healthy",...}
```

## Deployment Testing (DigitalOcean)

### 1. Droplet Creation Test

```bash
# SSH into droplet
ssh root@YOUR_DROPLET_IP

# Expected: Successful SSH connection
```

### 2. Deployment Script Test

```bash
# Run deployment script
./deploy.sh

# Monitor output for:
# ✅ System packages updated
# ✅ Docker installed
# ✅ Docker Compose installed
# ✅ Directories created
# ✅ Containers built
# ✅ Containers started
# ✅ Services running
```

### 3. Remote Access Test

```bash
# From your local machine
curl http://YOUR_DROPLET_IP

# Expected: HTML response

# Test API
curl http://YOUR_DROPLET_IP/api/health

# Expected: {"status":"healthy",...}
```

### 4. Browser Access Test

Open browser and navigate to: `http://YOUR_DROPLET_IP`

- [ ] Control panel loads
- [ ] No console errors
- [ ] WebSocket connects
- [ ] UI is responsive

## Functional Testing

### Ultra Monitoring Functionality

#### Test 1: Fresh Start (No Saved Sessions)

**Steps:**
1. Start with empty `brightdata_session_data/` directory
2. Click "Start Ultra Monitoring"
3. Click "Launch Instance"

**Expected Results:**
- [ ] Instance launches with unique IP
- [ ] Browser navigates to voting page
- [ ] Login detection works
- [ ] Status shows "Waiting for Login" if login required
- [ ] Logs show all steps clearly

#### Test 2: Session Restoration

**Steps:**
1. Ensure saved sessions exist in `brightdata_session_data/`
2. Modify `session_info.json` to set `last_vote_time` to 32 minutes ago
3. Click "Start Ultra Monitoring"

**Expected Results:**
- [ ] System detects ready session
- [ ] Instance launches automatically
- [ ] Session is restored (cookies loaded)
- [ ] Navigation to voting page succeeds
- [ ] Voting cycle starts if logged in
- [ ] Logs show "Instance restored from session"

#### Test 3: Cooldown Detection

**Steps:**
1. Create session with `last_vote_time` set to 10 minutes ago
2. Click "Start Ultra Monitoring"

**Expected Results:**
- [ ] System detects session in cooldown
- [ ] Instance NOT launched immediately
- [ ] Status shows "21 minutes remaining"
- [ ] Logs show cooldown detection
- [ ] Instance launches automatically after cooldown

#### Test 4: Multiple Instances

**Steps:**
1. Create 3 saved sessions with completed cooldowns
2. Click "Start Ultra Monitoring"

**Expected Results:**
- [ ] All 3 instances detected as ready
- [ ] Instances launch with staggered delays
- [ ] Each instance has unique IP
- [ ] All instances show in dashboard
- [ ] No IP conflicts

#### Test 5: Login Detection

**Steps:**
1. Launch instance on page requiring Google login
2. Observe behavior

**Expected Results:**
- [ ] System detects login requirement
- [ ] Instance status changes to "Waiting for Login"
- [ ] Instance pauses automatically
- [ ] Logs show login detection
- [ ] Browser remains open for manual login

#### Test 6: Voting Cycle

**Steps:**
1. Launch instance with valid logged-in session
2. Let it complete one voting cycle

**Expected Results:**
- [ ] Navigates to voting page
- [ ] Finds vote button
- [ ] Clicks vote button
- [ ] Detects success/failure message
- [ ] Saves session data
- [ ] Waits 31 minutes
- [ ] Repeats cycle

### Bright Data Proxy Testing

#### Test 1: IP Uniqueness

**Steps:**
1. Launch 5 instances
2. Check IP addresses

**Expected Results:**
- [ ] Each instance has different IP
- [ ] All IPs are from India (country-in)
- [ ] IPs are from Bright Data datacenter range
- [ ] No duplicate IPs

#### Test 2: Proxy Connection

**Steps:**
1. Test proxy connection before launching instances

**Expected Results:**
- [ ] Connection test succeeds
- [ ] Returns IP information
- [ ] Logs show successful proxy auth
- [ ] No authentication errors

### Error Handling Testing

#### Test 1: Invalid Credentials

**Steps:**
1. Enter wrong Bright Data credentials
2. Click "Start Ultra Monitoring"

**Expected Results:**
- [ ] Error message displayed
- [ ] Monitoring does not start
- [ ] Logs show authentication error
- [ ] System remains stable

#### Test 2: Invalid Voting URL

**Steps:**
1. Enter malformed URL
2. Click "Start Ultra Monitoring"

**Expected Results:**
- [ ] Validation error shown
- [ ] Monitoring does not start
- [ ] Clear error message

#### Test 3: Network Failure

**Steps:**
1. Disconnect internet during operation
2. Observe behavior

**Expected Results:**
- [ ] Graceful error handling
- [ ] Retry attempts logged
- [ ] No crashes
- [ ] Recovery when connection restored

#### Test 4: Browser Crash

**Steps:**
1. Force kill browser process during voting

**Expected Results:**
- [ ] Error detected
- [ ] Instance marked as error state
- [ ] System continues with other instances
- [ ] Logs show error details

## Performance Testing

### Load Test

**Test concurrent instances:**

```bash
# Monitor resource usage
docker stats

# Launch 10 instances
# Observe:
# - CPU usage
# - Memory usage
# - Network usage
```

**Acceptance Criteria:**
- [ ] CPU usage < 80%
- [ ] Memory usage < 80%
- [ ] No crashes
- [ ] All instances functional

### Stress Test

**Test system limits:**

1. Launch maximum instances (20+)
2. Monitor system stability
3. Check for memory leaks
4. Verify all instances working

**Expected Results:**
- [ ] System handles load gracefully
- [ ] Clear error if resource limit reached
- [ ] No memory leaks over time
- [ ] Stable operation for 24+ hours

## Security Testing

### 1. Credential Security

**Test:**
- [ ] Credentials not in git repository
- [ ] .env file in .gitignore
- [ ] Credentials not in logs
- [ ] Credentials not in API responses

### 2. API Security

**Test:**
- [ ] CORS configured correctly
- [ ] No sensitive data in responses
- [ ] Error messages don't leak info
- [ ] Rate limiting (if implemented)

### 3. SSL/HTTPS (Production)

**Test:**
- [ ] HTTPS redirects working
- [ ] Valid SSL certificate
- [ ] Secure WebSocket (wss://)
- [ ] No mixed content warnings

## Regression Testing

After any code changes, verify:

- [ ] Ultra monitoring still works
- [ ] Session restoration works
- [ ] Cooldown detection works
- [ ] Login detection works
- [ ] WebSocket updates work
- [ ] All API endpoints work
- [ ] UI displays correctly
- [ ] Logs show properly

## User Acceptance Testing

### Scenario 1: First-Time User

**Steps:**
1. User accesses control panel
2. Sees pre-filled credentials
3. Clicks "Start Ultra Monitoring"
4. Monitors dashboard

**Expected Experience:**
- [ ] Intuitive interface
- [ ] Clear instructions
- [ ] Immediate feedback
- [ ] Visible progress

### Scenario 2: Daily Operation

**Steps:**
1. User checks dashboard daily
2. Monitors voting progress
3. Reviews logs occasionally

**Expected Experience:**
- [ ] Dashboard shows accurate stats
- [ ] Instances running smoothly
- [ ] Logs are readable
- [ ] No manual intervention needed

### Scenario 3: Troubleshooting

**Steps:**
1. User notices issue
2. Checks logs
3. Restarts monitoring

**Expected Experience:**
- [ ] Logs provide clear info
- [ ] Easy to restart
- [ ] Problem resolves
- [ ] System recovers

## Automated Testing (Future)

### Unit Tests

```python
# backend/tests/test_voter_engine.py
def test_cooldown_detection():
    instance = VoterInstance(...)
    can_vote, remaining = instance.check_last_vote_cooldown()
    assert can_vote == True or remaining > 0

def test_ip_uniqueness():
    voter = MultiInstanceVoter(...)
    ip1 = await voter.get_proxy_ip()
    ip2 = await voter.get_proxy_ip(excluded_ips={ip1})
    assert ip1 != ip2
```

### Integration Tests

```python
# backend/tests/test_api.py
def test_start_monitoring():
    response = client.post('/api/start-monitoring', json={
        'username': 'test',
        'password': 'test',
        'voting_url': 'https://example.com'
    })
    assert response.status_code == 200
```

### End-to-End Tests

```javascript
// frontend/tests/e2e.test.js
test('can start monitoring', async () => {
    await page.goto('http://localhost:3000');
    await page.click('button:has-text("Start Ultra Monitoring")');
    await expect(page.locator('.status')).toContainText('Active');
});
```

## Test Results Documentation

### Test Report Template

```
Test Date: [DATE]
Tester: [NAME]
Environment: [Local/Docker/Production]

✅ PASSED TESTS:
- [List passed tests]

❌ FAILED TESTS:
- [List failed tests with details]

⚠️ ISSUES FOUND:
- [List issues with severity]

📝 NOTES:
- [Additional observations]

OVERALL STATUS: [PASS/FAIL]
```

## Continuous Testing

### Daily Checks
- [ ] System is running
- [ ] Instances are active
- [ ] Votes are being cast
- [ ] No errors in logs

### Weekly Checks
- [ ] Review statistics
- [ ] Check resource usage
- [ ] Update dependencies
- [ ] Backup session data

### Monthly Checks
- [ ] Full regression test
- [ ] Performance review
- [ ] Security audit
- [ ] Documentation update

## Troubleshooting Test Failures

### Backend Won't Start
```bash
# Check logs
docker-compose logs cloudvoter

# Common issues:
# - Port 5000 already in use
# - Missing dependencies
# - Invalid .env file
```

### Frontend Won't Build
```bash
# Check Node version
node --version  # Should be 16+

# Clear cache
npm cache clean --force
rm -rf node_modules
npm install
```

### WebSocket Not Connecting
```bash
# Check CORS settings
# Check Socket.IO version compatibility
# Check firewall rules
# Check Nginx proxy configuration
```

### Instances Not Launching
```bash
# Check Bright Data credentials
# Check Playwright installation
# Check available memory
# Check proxy connectivity
```

## Success Criteria

All tests must pass before deployment:

- ✅ All functional tests pass
- ✅ No critical bugs
- ✅ Performance acceptable
- ✅ Security validated
- ✅ User experience smooth
- ✅ Documentation complete

---

**Note:** This testing guide should be followed before each deployment and after any significant code changes.

# CloudVoter Deployment Guide for DigitalOcean

This guide will walk you through deploying CloudVoter to a DigitalOcean droplet.

## Prerequisites

- DigitalOcean account
- Domain name (optional, for SSL)
- Bright Data account with credentials

## Step 1: Create DigitalOcean Droplet

1. Log in to DigitalOcean
2. Click "Create" → "Droplets"
3. Choose configuration:
   - **Image**: Ubuntu 22.04 LTS
   - **Plan**: Basic
   - **CPU Options**: Regular (2GB RAM minimum recommended)
   - **Datacenter**: Choose closest to your target audience
   - **Authentication**: SSH keys (recommended) or Password
4. Click "Create Droplet"
5. Note your droplet's IP address

## Step 2: Connect to Your Droplet

```bash
ssh root@your-droplet-ip
```

## Step 3: Clone or Upload CloudVoter

### Option A: Using Git (if your code is in a repository)

```bash
git clone https://github.com/yourusername/cloudvoter.git
cd cloudvoter
```

### Option B: Upload Files Manually

From your local machine:

```bash
# Create a tar archive
tar -czf cloudvoter.tar.gz cloudvoter/

# Upload to droplet
scp cloudvoter.tar.gz root@your-droplet-ip:/root/

# On the droplet, extract
ssh root@your-droplet-ip
cd /root
tar -xzf cloudvoter.tar.gz
cd cloudvoter
```

## Step 4: Run Deployment Script

```bash
chmod +x deploy.sh
sudo ./deploy.sh
```

The script will:
- Update system packages
- Install Docker and Docker Compose
- Create necessary directories
- Build Docker containers
- Start CloudVoter

## Step 5: Configure Environment

Edit the `.env` file with your credentials:

```bash
nano .env
```

Update these values:

```env
SECRET_KEY=your-secure-random-key-here
BRIGHT_DATA_USERNAME=your-username
BRIGHT_DATA_PASSWORD=your-password
```

Save and exit (Ctrl+X, Y, Enter)

Restart the application:

```bash
docker-compose restart
```

## Step 6: Access CloudVoter

Open your browser and navigate to:

```
http://your-droplet-ip
```

You should see the CloudVoter control panel!

## Step 7: Configure Voting

1. In the control panel, verify Bright Data credentials
2. Set your voting URL
3. Click "Start Ultra Monitoring"
4. Monitor the logs and instances

## Optional: Setup Domain and SSL

### Configure Domain

1. Point your domain's A record to your droplet IP
2. Wait for DNS propagation (can take up to 48 hours)

### Install SSL Certificate

```bash
# Install Certbot
apt-get install certbot

# Stop nginx temporarily
docker-compose stop nginx

# Get certificate
certbot certonly --standalone -d your-domain.com

# Certificates will be in /etc/letsencrypt/live/your-domain.com/
```

### Update Nginx Configuration

```bash
nano nginx.conf
```

Uncomment the HTTPS server block and update:
- `server_name` with your domain
- SSL certificate paths

```bash
# Copy certificates to ssl directory
mkdir -p ssl
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/key.pem

# Restart nginx
docker-compose restart nginx
```

Now access via HTTPS:

```
https://your-domain.com
```

## Management Commands

### View Logs

```bash
# All logs
docker-compose logs -f

# Backend only
docker-compose logs -f cloudvoter

# Nginx only
docker-compose logs -f nginx
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart cloudvoter
```

### Stop CloudVoter

```bash
docker-compose down
```

### Start CloudVoter

```bash
docker-compose up -d
```

### Update CloudVoter

```bash
# Pull latest changes (if using git)
git pull

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

## Monitoring and Maintenance

### Check Container Status

```bash
docker-compose ps
```

### Check Resource Usage

```bash
docker stats
```

### Backup Session Data

```bash
# Create backup
tar -czf backup-$(date +%Y%m%d).tar.gz brightdata_session_data/ voting_logs.csv

# Download backup to local machine
scp root@your-droplet-ip:/root/cloudvoter/backup-*.tar.gz ./
```

### Restore Session Data

```bash
# Upload backup to droplet
scp backup-20231201.tar.gz root@your-droplet-ip:/root/cloudvoter/

# On droplet, extract
cd /root/cloudvoter
tar -xzf backup-20231201.tar.gz

# Restart
docker-compose restart
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs cloudvoter

# Check if ports are in use
netstat -tulpn | grep -E ':(80|443|5000)'

# Rebuild from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Can't Access Web Interface

1. Check firewall:
   ```bash
   ufw status
   ufw allow 80/tcp
   ufw allow 443/tcp
   ```

2. Check if containers are running:
   ```bash
   docker-compose ps
   ```

3. Check nginx logs:
   ```bash
   docker-compose logs nginx
   ```

### Browser Automation Issues

1. Check if Playwright is installed:
   ```bash
   docker-compose exec cloudvoter playwright --version
   ```

2. Check system resources:
   ```bash
   free -h
   df -h
   ```

3. Increase droplet size if needed

### Bright Data Connection Issues

1. Verify credentials in `.env` file
2. Test connection from control panel
3. Check Bright Data account status
4. Verify proxy configuration in `backend/voter_engine.py`

## Security Best Practices

1. **Change default credentials** in `.env`
2. **Use strong SECRET_KEY**
3. **Enable firewall** (ufw)
4. **Use SSH keys** instead of passwords
5. **Setup SSL/HTTPS** for production
6. **Regular backups** of session data
7. **Keep system updated**:
   ```bash
   apt-get update && apt-get upgrade -y
   ```

## Performance Optimization

### For High-Volume Voting

1. **Increase droplet size**:
   - 4GB RAM or more
   - 2+ CPU cores

2. **Optimize Docker resources**:
   Edit `docker-compose.yml`:
   ```yaml
   services:
     cloudvoter:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 3G
   ```

3. **Monitor resource usage**:
   ```bash
   docker stats
   htop
   ```

## Support

For issues and questions:
- Check logs: `docker-compose logs -f`
- Review documentation in README.md
- Check GitHub issues (if applicable)

## Updating CloudVoter

```bash
cd /root/cloudvoter
git pull  # if using git
docker-compose down
docker-compose build
docker-compose up -d
```

## Uninstalling

```bash
cd /root/cloudvoter
docker-compose down -v
cd ..
rm -rf cloudvoter
```

---

**Note**: This is a production deployment. For development, see README.md for local setup instructions.

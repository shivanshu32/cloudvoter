#!/bin/bash

# CloudVoter Deployment Script for DigitalOcean
# This script automates the deployment process

set -e

echo "🚀 CloudVoter Deployment Script"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Running as root"

# Update system
echo ""
echo "📦 Updating system packages..."
apt-get update
apt-get upgrade -y

# Install Docker if not installed
if ! command -v docker &> /dev/null; then
    echo ""
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    echo -e "${GREEN}✓${NC} Docker installed"
else
    echo -e "${GREEN}✓${NC} Docker already installed"
fi

# Install Docker Compose if not installed
if ! command -v docker-compose &> /dev/null; then
    echo ""
    echo "🐳 Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}✓${NC} Docker Compose installed"
else
    echo -e "${GREEN}✓${NC} Docker Compose already installed"
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo -e "${YELLOW}⚠${NC} Please edit .env file with your actual credentials"
    echo "   Run: nano .env"
fi

# Create necessary directories
echo ""
echo "📁 Creating directories..."
mkdir -p brightdata_session_data
mkdir -p failure_screenshots
mkdir -p ssl
echo -e "${GREEN}✓${NC} Directories created"

# Build and start containers
echo ""
echo "🏗️  Building Docker containers..."
docker-compose build

echo ""
echo "🚀 Starting CloudVoter..."
docker-compose up -d

# Wait for services to start
echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Check if containers are running
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✓${NC} CloudVoter is running!"
    echo ""
    echo "================================"
    echo "🎉 Deployment Complete!"
    echo "================================"
    echo ""
    echo "Access your CloudVoter control panel at:"
    echo "  http://$(curl -s ifconfig.me)"
    echo ""
    echo "To view logs:"
    echo "  docker-compose logs -f"
    echo ""
    echo "To stop CloudVoter:"
    echo "  docker-compose down"
    echo ""
    echo "To restart CloudVoter:"
    echo "  docker-compose restart"
    echo ""
else
    echo -e "${RED}✗${NC} Failed to start containers"
    echo "Check logs with: docker-compose logs"
    exit 1
fi

# Optional: Setup firewall
read -p "Do you want to configure firewall (ufw)? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🔥 Configuring firewall..."
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable
    echo -e "${GREEN}✓${NC} Firewall configured"
fi

echo ""
echo "================================"
echo "📚 Next Steps:"
echo "================================"
echo "1. Access the control panel in your browser"
echo "2. Configure Bright Data credentials"
echo "3. Set voting URL"
echo "4. Click 'Start Ultra Monitoring'"
echo ""
echo "For SSL/HTTPS setup:"
echo "1. Install certbot: apt-get install certbot"
echo "2. Get certificate: certbot certonly --standalone -d your-domain.com"
echo "3. Update nginx.conf with SSL configuration"
echo "4. Restart: docker-compose restart nginx"
echo ""

#!/bin/bash

# Quick start script for OCR Web Service
# Automates the initial setup process

set -e

echo "========================================="
echo "OCR Web Service - Quick Start"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if running in project root
if [ ! -f "README.md" ]; then
    echo -e "${RED}Error: Please run this script from the project root directory${NC}"
    exit 1
fi

# Step 1: Check Docker
echo "Step 1: Checking Docker..."
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker is installed"
else
    echo -e "${RED}✗${NC} Docker is not installed"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker Compose is installed"
else
    echo -e "${RED}✗${NC} Docker Compose is not installed"
    exit 1
fi

# Step 2: Check Python
echo ""
echo "Step 2: Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION is installed"
else
    echo -e "${RED}✗${NC} Python 3 is not installed"
    exit 1
fi

# Step 3: Download models
echo ""
echo "Step 3: Downloading PaddleOCR models..."
if [ -d "backend/models" ] && [ "$(ls -A backend/models)" ]; then
    echo -e "${YELLOW}!${NC} Models already exist, skipping download"
else
    echo "This will take several minutes..."
    cd backend

    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi

    source venv/bin/activate
    pip install -q -r requirements.txt
    python ../scripts/download_models.py
    deactivate
    cd ..

    echo -e "${GREEN}✓${NC} Models downloaded successfully"
fi

# Step 4: Create .env file
echo ""
echo "Step 4: Creating configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✓${NC} .env file created"
else
    echo -e "${YELLOW}!${NC} .env file already exists"
fi

# Step 5: Build and start services
echo ""
echo "Step 5: Building and starting services..."
cd docker
docker-compose build
docker-compose up -d
cd ..

echo ""
echo "Waiting for services to start..."
sleep 10

# Step 6: Health check
echo ""
echo "Step 6: Checking service health..."

if curl -f -s http://localhost/api/v1/health > /dev/null; then
    echo -e "${GREEN}✓${NC} Backend API is healthy"
else
    echo -e "${RED}✗${NC} Backend API is not responding"
    echo "Check logs: cd docker && docker-compose logs backend"
fi

if curl -f -s http://localhost > /dev/null; then
    echo -e "${GREEN}✓${NC} Frontend is accessible"
else
    echo -e "${RED}✗${NC} Frontend is not responding"
fi

# Done
echo ""
echo "========================================="
echo -e "${GREEN}Setup completed!${NC}"
echo "========================================="
echo ""
echo "Access the application at: ${GREEN}http://localhost${NC}"
echo ""
echo "Useful commands:"
echo "  View logs:    cd docker && docker-compose logs -f"
echo "  Stop:         cd docker && docker-compose down"
echo "  Restart:      cd docker && docker-compose restart"
echo ""
echo "Documentation:"
echo "  Quick start:  QUICKSTART.md"
echo "  User guide:   docs/user-guide.md"
echo "  Full docs:    docs/"
echo ""

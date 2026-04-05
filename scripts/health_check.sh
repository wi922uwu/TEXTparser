#!/bin/bash

# Health check script for OCR Web Service
# Verifies all services are running correctly

set -e

echo "========================================="
echo "OCR Web Service - Health Check"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is running
echo "Checking Docker..."
if docker info > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Docker is running"
else
    echo -e "${RED}✗${NC} Docker is not running"
    exit 1
fi

# Check if services are running
echo ""
echo "Checking services..."

services=("ocr-redis" "ocr-backend" "ocr-celery-worker" "ocr-frontend" "ocr-nginx")

for service in "${services[@]}"; do
    if docker ps --format '{{.Names}}' | grep -q "^${service}$"; then
        echo -e "${GREEN}✓${NC} ${service} is running"
    else
        echo -e "${RED}✗${NC} ${service} is not running"
    fi
done

# Check API health
echo ""
echo "Checking API endpoints..."

if curl -f -s http://localhost/api/v1/health > /dev/null; then
    echo -e "${GREEN}✓${NC} Backend API is healthy"
else
    echo -e "${RED}✗${NC} Backend API is not responding"
fi

# Check frontend
if curl -f -s http://localhost > /dev/null; then
    echo -e "${GREEN}✓${NC} Frontend is accessible"
else
    echo -e "${RED}✗${NC} Frontend is not responding"
fi

# Check Redis
echo ""
echo "Checking Redis..."
if docker exec ocr-redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Redis is responding"
else
    echo -e "${RED}✗${NC} Redis is not responding"
fi

# Check disk space
echo ""
echo "Checking disk space..."
df -h | grep -E "Filesystem|/$"

# Check Docker volumes
echo ""
echo "Checking Docker volumes..."
docker volume ls | grep ocr

echo ""
echo "========================================="
echo "Health check completed"
echo "========================================="

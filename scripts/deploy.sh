#!/bin/bash

# OCR Web Service Deployment Script
# This script automates the deployment process

set -e

echo "========================================="
echo "OCR Web Service Deployment"
echo "========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed"
    echo "Please install Docker Compose first"
    exit 1
fi

# Check if models are downloaded
if [ ! -d "backend/models" ] || [ -z "$(ls -A backend/models)" ]; then
    echo "Warning: PaddleOCR models not found"
    echo "Downloading models..."

    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python ../scripts/download_models.py
    deactivate
    cd ..

    echo "Models downloaded successfully"
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ".env file created. Please review and update if needed."
fi

# Build and start services
echo ""
echo "Building Docker images..."
cd docker
docker-compose build

echo ""
echo "Starting services..."
docker-compose up -d

echo ""
echo "Waiting for services to start..."
sleep 10

# Check service health
echo ""
echo "Checking service health..."

if curl -f http://localhost/api/v1/health &> /dev/null; then
    echo "✓ Backend API is healthy"
else
    echo "✗ Backend API is not responding"
    echo "Check logs: docker-compose logs backend"
fi

if curl -f http://localhost &> /dev/null; then
    echo "✓ Frontend is accessible"
else
    echo "✗ Frontend is not responding"
    echo "Check logs: docker-compose logs nginx"
fi

echo ""
echo "========================================="
echo "Deployment completed!"
echo "========================================="
echo ""
echo "Access the application at: http://localhost"
echo ""
echo "Useful commands:"
echo "  View logs:    docker-compose logs -f"
echo "  Stop:         docker-compose down"
echo "  Restart:      docker-compose restart"
echo "  Status:       docker-compose ps"
echo ""

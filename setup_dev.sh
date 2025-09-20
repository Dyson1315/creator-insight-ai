#!/bin/bash

echo "Setting up Creator-VRidge AI Development Environment..."

# Check if Docker is available
if command -v docker &> /dev/null; then
    echo "Docker found, using Docker setup..."
    
    # Build and run with Docker Compose
    echo "Building Docker containers..."
    docker-compose build
    
    echo "Starting services..."
    docker-compose up -d
    
    echo "Waiting for services to start..."
    sleep 10
    
    echo "Services started successfully!"
    echo "API available at: http://localhost:8000"
    echo "API documentation: http://localhost:8000/docs"
    echo "Redis available at: localhost:6379"
    echo "Flower (Celery monitoring): http://localhost:5555"
    
    echo ""
    echo "To check logs: docker-compose logs -f"
    echo "To stop services: docker-compose down"
    
else
    echo "Docker not found. Please install Docker and Docker Compose to run the development environment."
    echo ""
    echo "Installation instructions:"
    echo "1. Install Docker: https://docs.docker.com/get-docker/"
    echo "2. Install Docker Compose: https://docs.docker.com/compose/install/"
    echo ""
    echo "Or install Python dependencies manually:"
    echo "1. Install Python 3.11+ and pip"
    echo "2. pip install -r requirements.txt"
    echo "3. uvicorn app.main:app --reload"
fi
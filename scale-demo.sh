#!/bin/bash

# Service Scaling Demonstration Script
# This script shows how to scale services to different levels

echo "🚀 To-Do App Service Scaling Demo"
echo "=================================="

# Function to show current running services
show_services() {
    echo "📊 Currently running services:"
    docker-compose ps --services --filter "status=running" | while read service; do
        count=$(docker-compose ps -q $service | wc -l)
        echo "  - $service: $count instance(s)"
    done
    echo ""
}

# Function to scale services
scale_services() {
    local scenario=$1
    echo "🔧 Scaling to: $scenario"
    
    case $scenario in
        "development")
            docker-compose up -d --scale user_service=1 --scale task_service=1 --scale notification_service=1 --scale celery_worker=2
            ;;
        "testing")
            docker-compose up -d --scale user_service=2 --scale task_service=3 --scale notification_service=2 --scale celery_worker=5
            ;;
        "production")
            docker-compose up -d --scale user_service=5 --scale task_service=8 --scale notification_service=3 --scale celery_worker=15
            ;;
        "demo")
            echo "🎭 Running scaling demo..."
            echo "Starting with minimal setup..."
            docker-compose up -d --scale user_service=1 --scale task_service=1 --scale notification_service=1 --scale celery_worker=1
            sleep 5
            show_services
            
            echo "Scaling up to medium load..."
            docker-compose up -d --scale user_service=3 --scale task_service=4 --scale notification_service=2 --scale celery_worker=6
            sleep 5
            show_services
            
            echo "Scaling to high load..."
            docker-compose up -d --scale user_service=6 --scale task_service=8 --scale notification_service=4 --scale celery_worker=12
            sleep 5
            show_services
            return
            ;;
        *)
            echo "❌ Unknown scenario: $scenario"
            echo "Available scenarios: development, testing, production, demo"
            exit 1
            ;;
    esac
    
    echo "⏳ Waiting for services to start..."
    sleep 10
    show_services
}

# Main script logic
if [ $# -eq 0 ]; then
    echo "Usage: $0 [development|testing|production|demo]"
    echo ""
    echo "Scenarios:"
    echo "  development - Minimal resources (1-2 instances per service)"
    echo "  testing     - Medium resources (2-5 instances per service)"  
    echo "  production  - High resources (3-15 instances per service)"
    echo "  demo        - Demonstrates scaling from low to high"
    echo ""
    show_services
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed or not in PATH"
    exit 1
fi

# Start scaling
scale_services $1

echo "✅ Scaling complete!"
echo ""
echo "🔍 To monitor services:"
echo "  docker-compose ps"
echo "  docker-compose logs -f [service_name]"
echo "  docker stats"
echo ""
echo "🌐 Access points:"
echo "  Frontend: http://localhost:5173"
echo "  API Gateway: http://localhost:8080"
echo "  Redis: localhost:6379"
echo "  PostgreSQL: localhost:5432" 
# Service Scaling Demonstration Script (PowerShell)
# This script shows how to scale services to different levels

Write-Host "🚀 To-Do App Service Scaling Demo" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green

# Function to show current running services
function Show-Services {
    Write-Host "📊 Currently running services:" -ForegroundColor Yellow
    $services = docker-compose ps --services --filter "status=running"
    foreach ($service in $services) {
        $count = (docker-compose ps -q $service).Count
        Write-Host "  - $service`: $count instance(s)" -ForegroundColor White
    }
    Write-Host ""
}

# Function to scale services
function Scale-Services {
    param([string]$scenario)
    
    Write-Host "🔧 Scaling to: $scenario" -ForegroundColor Cyan
    
    switch ($scenario) {
        "development" {
            docker-compose up -d --scale user_service=1 --scale task_service=1 --scale notification_service=1 --scale celery_worker=2
        }
        "testing" {
            docker-compose up -d --scale user_service=2 --scale task_service=3 --scale notification_service=2 --scale celery_worker=5
        }
        "production" {
            docker-compose up -d --scale user_service=5 --scale task_service=8 --scale notification_service=3 --scale celery_worker=15
        }
        "demo" {
            Write-Host "🎭 Running scaling demo..." -ForegroundColor Magenta
            Write-Host "Starting with minimal setup..." -ForegroundColor Yellow
            docker-compose up -d --scale user_service=1 --scale task_service=1 --scale notification_service=1 --scale celery_worker=1
            Start-Sleep 5
            Show-Services
            
            Write-Host "Scaling up to medium load..." -ForegroundColor Yellow
            docker-compose up -d --scale user_service=3 --scale task_service=4 --scale notification_service=2 --scale celery_worker=6
            Start-Sleep 5
            Show-Services
            
            Write-Host "Scaling to high load..." -ForegroundColor Yellow
            docker-compose up -d --scale user_service=6 --scale task_service=8 --scale notification_service=4 --scale celery_worker=12
            Start-Sleep 5
            Show-Services
            return
        }
        default {
            Write-Host "❌ Unknown scenario: $scenario" -ForegroundColor Red
            Write-Host "Available scenarios: development, testing, production, demo" -ForegroundColor Yellow
            exit 1
        }
    }
    
    Write-Host "⏳ Waiting for services to start..." -ForegroundColor Yellow
    Start-Sleep 10
    Show-Services
}

# Main script logic
if ($args.Count -eq 0) {
    Write-Host "Usage: .\scale-demo.ps1 [development|testing|production|demo]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Scenarios:" -ForegroundColor Cyan
    Write-Host "  development - Minimal resources (1-2 instances per service)" -ForegroundColor White
    Write-Host "  testing     - Medium resources (2-5 instances per service)" -ForegroundColor White
    Write-Host "  production  - High resources (3-15 instances per service)" -ForegroundColor White
    Write-Host "  demo        - Demonstrates scaling from low to high" -ForegroundColor White
    Write-Host ""
    Show-Services
    exit 1
}

# Check if docker-compose is available
if (!(Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "❌ docker-compose is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Start scaling
Scale-Services $args[0]

Write-Host "✅ Scaling complete!" -ForegroundColor Green
Write-Host ""
Write-Host "🔍 To monitor services:" -ForegroundColor Cyan
Write-Host "  docker-compose ps" -ForegroundColor White
Write-Host "  docker-compose logs -f [service_name]" -ForegroundColor White
Write-Host "  docker stats" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Access points:" -ForegroundColor Cyan
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "  API Gateway: http://localhost:8080" -ForegroundColor White
Write-Host "  Redis: localhost:6379" -ForegroundColor White
Write-Host "  PostgreSQL: localhost:5432" -ForegroundColor White 
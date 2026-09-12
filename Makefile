.PHONY: help build up down logs restart clean test shell db-shell health

# Default target
help:
	@echo "TripMate AI - Docker Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  build       Build Docker images"
	@echo "  up          Start all services"
	@echo "  down        Stop all services"
	@echo "  logs        View logs (use ctrl+c to exit)"
	@echo "  restart     Restart all services"
	@echo "  clean       Stop and remove all containers, volumes, and images"
	@echo "  shell       Access app container shell"
	@echo "  db-shell    Access database shell"
	@echo "  health      Check health status"
	@echo "  test        Run tests (if available)"

# Build Docker images
build:
	docker-compose build

# Start services
up:
	docker-compose up -d
	@echo "✅ Services started!"
	@echo "🌐 Access app at http://localhost:8000"

# Stop services
down:
	docker-compose down

# View logs
logs:
	docker-compose logs -f

# Restart services
restart: down up

# Clean everything
clean:
	docker-compose down -v --rmi all
	@echo "✅ Cleaned all containers, volumes, and images"

# Access app container shell
shell:
	docker-compose exec app bash

# Access database shell
db-shell:
	docker-compose exec db psql -U tripmate_user -d travel_db

# Check health
health:
	@echo "Checking service health..."
	@docker-compose ps
	@echo ""
	@curl -f http://localhost:8000/health || echo "❌ Health check failed"

# Run tests
test:
	docker-compose exec app python -m pytest tests/ -v || echo "No tests found"

# Development mode with live reload
dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# View resource usage
stats:
	docker stats tripmate-app tripmate-postgres

# Backup database
backup:
	docker-compose exec db pg_dump -U tripmate_user travel_db > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Database backed up"

# Restore database from backup (usage: make restore FILE=backup.sql)
restore:
	docker-compose exec -T db psql -U tripmate_user travel_db < $(FILE)
	@echo "✅ Database restored"

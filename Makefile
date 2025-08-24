# Taara Internet Monitor - Production Makefile
# Clean, minimal production deployment and management

.PHONY: help install deploy start stop restart logs backup clean verify

# Default target
help:
	@echo "🚀 Taara Internet Monitor - Production Commands"
	@echo "=============================================="
	@echo ""
	@echo "📦 Setup & Deployment:"
	@echo "  make install    - Install Docker and dependencies"
	@echo "  make deploy     - Deploy application to production"
	@echo "  make verify     - Verify production readiness"
	@echo ""
	@echo "🔧 Management:"
	@echo "  make start      - Start all services"
	@echo "  make stop       - Stop all services"
	@echo "  make restart    - Restart all services"
	@echo "  make logs       - View application logs"
	@echo ""
	@echo "💾 Maintenance:"
	@echo "  make backup     - Backup database and logs"
	@echo "  make clean      - Clean up containers and images"
	@echo ""

# System setup and Docker installation
install:
	@echo "🔧 Installing system dependencies..."
	@sudo apt update && sudo apt upgrade -y
	@sudo apt install -y curl wget git ufw fail2ban
	@echo "🐳 Installing Docker..."
	@curl -fsSL https://get.docker.com -o get-docker.sh
	@sudo sh get-docker.sh
	@sudo usermod -aG docker $$USER
	@sudo systemctl enable docker
	@sudo systemctl start docker
	@echo "🔥 Installing Docker Compose..."
	@sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$$(uname -s)-$$(uname -m)" -o /usr/local/bin/docker-compose
	@sudo chmod +x /usr/local/bin/docker-compose
	@echo "🛡️ Configuring firewall..."
	@sudo ufw --force reset
	@sudo ufw default deny incoming
	@sudo ufw default allow outgoing
	@sudo ufw allow 22/tcp
	@sudo ufw allow 80/tcp
	@sudo ufw allow 443/tcp
	@sudo ufw --force enable
	@rm -f get-docker.sh
	@echo "✅ System setup complete! Please logout and login again."

# Deploy application
deploy:
	@echo "🚀 Deploying Taara Internet Monitor..."
	@mkdir -p data logs backups
	@chmod 600 .env
	@sudo chown -R $$USER:$$USER .
	@docker-compose down --remove-orphans || true
	@docker-compose build --no-cache
	@docker-compose up -d
	@echo "⏳ Waiting for services to start..."
	@sleep 10
	@make verify
	@echo "✅ Deployment complete!"
	@echo "📊 Access your dashboard at: http://localhost"

# Start services
start:
	@echo "▶️  Starting Taara Monitor..."
	@docker-compose up -d
	@echo "✅ Services started!"

# Stop services
stop:
	@echo "⏹️  Stopping Taara Monitor..."
	@docker-compose down
	@echo "✅ Services stopped!"

# Restart services
restart:
	@echo "🔄 Restarting Taara Monitor..."
	@docker-compose restart
	@echo "✅ Services restarted!"

# View logs
logs:
	@echo "📋 Taara Monitor Logs (Ctrl+C to exit):"
	@echo "======================================="
	@docker-compose logs -f --tail=100

# Backup database and logs
backup:
	@echo "💾 Creating backup..."
	@mkdir -p backups
	@timestamp=$$(date +%Y%m%d_%H%M%S) && \
	tar -czf backups/taara_backup_$$timestamp.tar.gz data/ logs/ .env && \
	echo "✅ Backup created: backups/taara_backup_$$timestamp.tar.gz"
	@echo "🧹 Cleaning old backups (keeping last 7)..."
	@cd backups && ls -t taara_backup_*.tar.gz | tail -n +8 | xargs rm -f || true
	@echo "✅ Backup complete!"

# Clean up Docker resources
clean:
	@echo "🧹 Cleaning up Docker resources..."
	@docker-compose down --remove-orphans --volumes || true
	@docker system prune -f
	@docker image prune -f
	@echo "✅ Cleanup complete!"

# Verify production readiness
verify:
	@echo "🔍 Verifying Production Setup..."
	@echo "==============================="
	@echo ""
	@# Check .env file
	@if [ -f ".env" ] && [ "$$(stat -c %a .env)" = "600" ]; then \
		echo "✅ Environment configuration secure"; \
	else \
		echo "❌ .env file missing or insecure permissions"; \
		exit 1; \
	fi
	@# Check Docker services
	@if docker-compose ps | grep -q "Up"; then \
		echo "✅ Docker services running"; \
	else \
		echo "⚠️  Docker services not running"; \
	fi
	@# Check application health
	@if curl -sf http://localhost/health >/dev/null 2>&1; then \
		echo "✅ Application health check passed"; \
	else \
		echo "⚠️  Application health check failed"; \
	fi
	@# Check database
	@if [ -f "data/taara_monitoring.db" ]; then \
		echo "✅ Database file exists"; \
	else \
		echo "⚠️  Database file not found"; \
	fi
	@echo ""
	@echo "🎉 Production verification complete!"
	@echo ""
	@echo "📊 Quick stats:"
	@echo "Database size: $$(du -h data/taara_monitoring.db 2>/dev/null || echo 'N/A')"
	@echo "Log files: $$(find logs -name '*.log' 2>/dev/null | wc -l) files"
	@echo "Backup files: $$(find backups -name '*.tar.gz' 2>/dev/null | wc -l) files"
	@echo ""

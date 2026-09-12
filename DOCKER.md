# 🐳 Docker Deployment Guide for TripMate AI

This guide covers running TripMate AI using Docker for both local development and production deployment.

## 📋 Prerequisites

- Docker Desktop or Docker Engine 20.10+
- Docker Compose v2.0+
- API keys for Groq, Tavily, AviationStack, and OpenWeatherMap

## 🚀 Quick Start with Docker Compose

### 1. Setup Environment Variables

Copy the example environment file and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your actual API keys:

```env
GROQ_API_KEY=your_actual_groq_key
TAVILY_API_KEY=your_actual_tavily_key
AVIATIONSTACK_API_KEY=your_actual_aviationstack_key
OPENWEATHER_API_KEY=your_actual_openweather_key
```

### 2. Start All Services

```bash
docker-compose up -d
```

This will:
- Pull the PostgreSQL 15 Alpine image
- Build the TripMate AI application image
- Start both containers with networking configured
- Create a persistent volume for database data

### 3. Access the Application

Open your browser at:
```
http://localhost:8000
```

### 4. View Logs

```bash
# All services
docker-compose logs -f

# Just the app
docker-compose logs -f app

# Just the database
docker-compose logs -f db
```

### 5. Stop Services

```bash
# Stop but keep data
docker-compose down

# Stop and remove all data (including database)
docker-compose down -v
```

## 🛠️ Docker Build Options

### Build Standalone Image

```bash
docker build -t tripmate-ai:latest .
```

### Run Standalone Container

```bash
docker run -d \
  --name tripmate-ai \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:pass@host:5432/db?sslmode=require" \
  -e GROQ_API_KEY="your_key" \
  -e TAVILY_API_KEY="your_key" \
  -e AVIATIONSTACK_API_KEY="your_key" \
  -e OPENWEATHER_API_KEY="your_key" \
  tripmate-ai:latest
```

### Build with Custom Tag

```bash
docker build -t myusername/tripmate-ai:v1.0 .
```

### Multi-platform Build (for deployment)

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t myusername/tripmate-ai:latest \
  --push .
```

## 🔧 Development Mode

For active development with hot reload:

```bash
# In docker-compose.yml, add to app service:
volumes:
  - .:/app
command: uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Then:

```bash
docker-compose up
```

## 🌐 Production Deployment

### Option 1: Docker Hub

1. Build and tag:
```bash
docker build -t yourusername/tripmate-ai:latest .
```

2. Push to Docker Hub:
```bash
docker login
docker push yourusername/tripmate-ai:latest
```

3. Deploy on server:
```bash
docker pull yourusername/tripmate-ai:latest
docker run -d \
  --name tripmate-ai \
  -p 80:8000 \
  --env-file .env \
  --restart unless-stopped \
  yourusername/tripmate-ai:latest
```

### Option 2: Render.com

1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Select "Docker" as the environment
4. Render will automatically detect your Dockerfile
5. Add environment variables in the Render dashboard
6. Deploy!

### Option 3: Railway.app

1. Install Railway CLI:
```bash
npm i -g @railway/cli
```

2. Login and init:
```bash
railway login
railway init
```

3. Deploy:
```bash
railway up
```

### Option 4: AWS ECS / Azure / GCP

Use the provided Dockerfile with your cloud provider's container service:
- **AWS**: Elastic Container Service (ECS) or Fargate
- **Azure**: Container Instances or App Service
- **GCP**: Cloud Run or GKE

## 🔍 Health Checks

The Docker image includes health checks:

```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' tripmate-ai

# Test health endpoint
curl http://localhost:8000/health
```

## 📦 Image Size Optimization

Current image is optimized with:
- ✅ Python 3.11-slim base (smaller than full Python image)
- ✅ Multi-stage build (not needed but possible)
- ✅ Layer caching for requirements
- ✅ No cache for pip installs
- ✅ Cleanup of apt lists

Expected image size: ~800MB-1GB (due to ML dependencies)

## 🐛 Troubleshooting

### Container Won't Start

Check logs:
```bash
docker-compose logs app
```

### Database Connection Failed

Ensure PostgreSQL is healthy:
```bash
docker-compose ps
docker-compose logs db
```

### MCP Servers Not Working

The Dockerfile installs `aviationstack-mcp` via uvx. Check if uv is installed:
```bash
docker-compose exec app which uv
docker-compose exec app uvx --version
```

### Port Already in Use

Change the port mapping in docker-compose.yml:
```yaml
ports:
  - "8001:8000"  # Use 8001 instead of 8000
```

### Out of Memory

Increase Docker memory allocation:
- Docker Desktop: Settings > Resources > Memory (set to at least 4GB)
- Docker Engine: Edit `/etc/docker/daemon.json`

## 📊 Monitoring

### View Resource Usage

```bash
docker stats tripmate-app
```

### Access Container Shell

```bash
docker-compose exec app bash
```

### Database Shell

```bash
docker-compose exec db psql -U tripmate_user -d travel_db
```

## 🔐 Security Best Practices

1. **Never commit .env file** - It's already in .gitignore
2. **Use secrets management** in production (AWS Secrets Manager, etc.)
3. **Run as non-root user** (add to Dockerfile if needed):
   ```dockerfile
   RUN useradd -m -u 1000 appuser
   USER appuser
   ```
4. **Keep images updated**:
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

## 🔄 Update Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose up -d --build
```

## 🗑️ Clean Up

```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Nuclear option (removes everything)
docker system prune -a --volumes
```

## 📝 Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `GROQ_API_KEY` | Yes | - | Groq API key for LLM |
| `TAVILY_API_KEY` | Yes | - | Tavily API key for web search |
| `AVIATIONSTACK_API_KEY` | Yes | - | AviationStack API for flights |
| `OPENWEATHER_API_KEY` | Yes | - | OpenWeatherMap API key |
| `DEFAULT_ORIGIN_IATA` | No | `DEL` | Default departure airport code |
| `DB_PASSWORD` | No | `changeme123` | PostgreSQL password (docker-compose only) |

## 🎯 Production Checklist

- [ ] Set strong database password
- [ ] Use external managed PostgreSQL (Render, AWS RDS, etc.)
- [ ] Enable HTTPS (use reverse proxy like Nginx)
- [ ] Set up monitoring (Sentry, DataDog, etc.)
- [ ] Configure backup for database
- [ ] Set resource limits in docker-compose.yml
- [ ] Enable logging aggregation
- [ ] Set up CI/CD pipeline
- [ ] Use secrets management
- [ ] Configure auto-restart policies

---

**Need help?** Check the [README.md](./README.md) or open an issue on GitHub.

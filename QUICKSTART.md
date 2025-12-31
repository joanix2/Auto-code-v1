# Quick Start Guide

Get the Auto-Code Platform running in under 5 minutes!

## Prerequisites Check

Run these commands to verify you have the required tools:

```bash
# Check Docker
docker --version
# Expected: Docker version 20.x or higher

# Check Docker Compose
docker-compose --version
# Expected: Docker Compose version 1.29.x or higher

# Check Git
git --version
# Expected: git version 2.x or higher
```

If any are missing, install them:
- **Docker**: https://docs.docker.com/get-docker/
- **Git**: https://git-scm.com/downloads

## 5-Minute Setup

### Step 1: Clone the Repository (30 seconds)

```bash
git clone https://github.com/joanix2/Auto-code-v1.git
cd Auto-code-v1
```

### Step 2: Configure Environment (2 minutes)

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your credentials
nano .env  # or use your preferred editor
```

**Required credentials:**

1. **GitHub Token**: 
   - Go to https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Select scopes: `repo`, `workflow`
   - Copy the token to `GITHUB_TOKEN` in .env

2. **GitHub Repository**:
   - Set `GITHUB_OWNER` to your username
   - Set `GITHUB_REPO` to your repository name

3. **Anthropic API Key** (optional for now):
   - Go to https://console.anthropic.com/
   - Get your API key
   - Add to `ANTHROPIC_API_KEY` in .env

Your `.env` should look like:
```env
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
GITHUB_OWNER=yourusername
GITHUB_REPO=Auto-code-v1
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
```

### Step 3: Start the Platform (2 minutes)

```bash
# Build and start all services
docker-compose up --build -d

# Wait for services to initialize
sleep 10

# Check status
docker-compose ps
```

You should see all services running:
- ✅ auto-code-rabbitmq
- ✅ auto-code-backend
- ✅ auto-code-worker
- ✅ auto-code-frontend

### Step 4: Access the Platform (30 seconds)

Open your browser and visit:

- **Frontend (PWA)**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **RabbitMQ Dashboard**: http://localhost:15672 (guest/guest)

## Your First Task

1. **Open the PWA** at http://localhost:3000

2. **Create a task**:
   - Title: "Add hello world endpoint"
   - Description: "Create a GET /hello endpoint that returns 'Hello, World!'"
   - Priority: Medium

3. **Submit** and watch the magic happen!

4. **Check GitHub**: A new issue will be created in your repository

5. **Monitor progress**: Check the RabbitMQ dashboard to see the task being processed

## Verify Everything Works

### Test the API

```bash
# Health check
curl http://localhost:8000/health

# Create a ticket via API
curl -X POST http://localhost:8000/tickets \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test task",
    "description": "This is a test task",
    "priority": "low"
  }'
```

### Check Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f worker
docker-compose logs -f rabbitmq
```

## Troubleshooting

### Services won't start

```bash
# Check for port conflicts
netstat -tulpn | grep -E '3000|8000|5672|15672'

# Restart services
docker-compose down
docker-compose up -d
```

### Can't create issues

- Verify your `GITHUB_TOKEN` has `repo` scope
- Check that `GITHUB_OWNER` and `GITHUB_REPO` are correct
- Ensure the repository exists and you have access

### RabbitMQ connection errors

```bash
# Restart RabbitMQ
docker-compose restart rabbitmq

# Wait for it to be ready
sleep 5

# Restart dependent services
docker-compose restart backend worker
```

## Next Steps

Now that you're up and running:

1. **Read the full documentation**: Check out [README.md](README.md)
2. **Explore the API**: Visit http://localhost:8000/docs
3. **Customize the platform**: Edit the code to fit your needs
4. **Deploy to production**: See [DEPLOYMENT.md](DEPLOYMENT.md)
5. **Contribute**: See [CONTRIBUTING.md](CONTRIBUTING.md)

## Common Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart a service
docker-compose restart backend

# Rebuild containers
docker-compose up --build -d

# Remove everything (including volumes)
docker-compose down -v
```

## Mobile Access

To access the PWA from your mobile device:

1. **Find your computer's IP address**:
   ```bash
   # On macOS/Linux
   ifconfig | grep "inet "
   
   # On Windows
   ipconfig
   ```

2. **Update frontend URL** in docker-compose.yml:
   ```yaml
   environment:
     - REACT_APP_API_URL=http://YOUR_IP:8000
   ```

3. **Restart frontend**:
   ```bash
   docker-compose restart frontend
   ```

4. **Access from mobile**: http://YOUR_IP:3000

## Need Help?

- 📚 **Documentation**: Read [README.md](README.md)
- 🐛 **Found a bug?**: Open an issue on GitHub
- 💡 **Have an idea?**: Start a discussion
- 🤝 **Want to contribute?**: See [CONTRIBUTING.md](CONTRIBUTING.md)

---

**Congratulations! You're now running the Auto-Code Platform! 🎉**

# Auto-Code Platform v1

🤖 Asynchronous AI Development Agent Platform

A headless server platform that orchestrates AI development agents to automate coding tasks from mobile devices.

## 🌟 Features

- **📱 Mobile-First PWA**: Create development tickets from any mobile device
- **🤖 AI Agents**: GitHub Copilot integration for automated coding
- **📝 GitHub Integration**: Automatic issue creation and pull request management
- **☁️ Headless Operation**: Runs entirely on servers without IDE requirements
- **🐳 Docker-Ready**: Complete containerized deployment setup

## 🏗️ Architecture

```
┌─────────────┐
│  React PWA  │  (Mobile/Web Interface)
│  Frontend   │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────┐
│   FastAPI   │  (REST API Server)
│   Backend   │
└──────┬──────┘
       │
       ├──────► GitHub API (Issues & PRs)
       │
       ▼
┌─────────────┐
│   Neo4j     │  (Graph Database)
│   Database  │
└─────────────┘
```

## 📸 Aperçus

| Interface | Aperçu |
|-----------|--------|
| Frontend | ![App](docs/images/app-screenshot.png) |

## 📦 Tech Stack

- **Frontend**: React 18, TypeScript, Tailwind CSS
- **Backend**: Python 3.11, FastAPI, Uvicorn
- **Database**: Neo4j (Graph Database)
- **AI**: GitHub Copilot Integration
- **VCS**: GitHub OAuth & API
- **Deployment**: Docker, Docker Compose

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- GitHub Personal Access Token
- Anthropic API Key (for Claude)

### Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/joanix2/Auto-code-v1.git
   cd Auto-code-v1
   ```

2. **Configure environment**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your credentials:

   ```env
   GITHUB_CLIENT_ID=your_github_oauth_client_id
   GITHUB_CLIENT_SECRET=your_github_oauth_client_secret
   NEO4J_PASSWORD=your_secure_password
   ```

3. **Start the platform**

   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/api
   - API Docs: http://localhost:8000/api/docs
   - Neo4j Browser: http://localhost:7474

## 📱 Usage

### Creating a Task from PWA

1. Open http://localhost:3000 on your mobile device or browser
2. Fill in the task form:
   - **Title**: Brief description of the task
   - **Description**: Detailed requirements
   - **Priority**: Low, Medium, or High
3. Click "Create Task"
4. The system will:
   - Create a GitHub issue
   - Assign to GitHub Copilot Agent
   - Track progress and pull request

### Using the API

Create a ticket programmatically:

```bash
curl -X POST http://localhost:8000/api/tickets \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Add user authentication",
    "description": "Implement JWT-based authentication system",
    "priority": "high",
    "labels": ["feature", "security"]
  }'
```

Check health status:

```bash
curl http://localhost:8000/api/health
```

## 🤖 Claude AI Integration

### Headless Development

Auto-Code includes a powerful headless development system using Claude AI that can:

- Automatically develop tickets in queue
- Generate production-ready code
- Run on servers without human intervention
- Integrate with CI/CD pipelines

**Quick Start:**

```bash
# Develop next ticket in queue
curl -X POST http://localhost:8000/api/tickets/repository/REPO_ID/develop-next \
  -H "Authorization: Bearer YOUR_TOKEN"

# Or use the CLI
cd backend
python claude_cli.py develop-next REPO_ID
```

**Continuous Development Server:**

```bash
# Run continuous development
export AUTOCODE_REPO_ID=your-repo-id
./scripts/headless_dev.sh
```

📖 **Full Documentation:**

- [Claude Setup Guide](CLAUDE_SETUP.md) - Configuration and basic usage
- [Headless Development](CLAUDE_HEADLESS.md) - Advanced automation and CI/CD

### Features

✨ **Smart Queue Management**

- Tickets automatically ordered by priority
- First "open" ticket is next in queue
- Status tracking (open → in_progress → closed)

🎯 **Structured Prompts**

- Context-aware code generation
- Repository-specific patterns
- Best practices enforcement

📊 **Usage Tracking**

- Token consumption monitoring
- Cost estimation
- Performance metrics

## 🔧 Development

### Backend Development

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run locally
python main.py

# Run worker
python worker.py
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm start

# Build for production
npm run build

# Run tests
npm test
```

## 📁 Project Structure

```
Auto-code-v1/
├── backend/
│   ├── src/
│   │   ├── controllers/      # API controllers
│   │   ├── models/           # Data models
│   │   ├── repositories/     # Database access
│   │   ├── services/         # Business logic
│   │   └── utils/            # Utilities
│   ├── main.py               # FastAPI application
│   ├── requirements.txt      # Python dependencies
│   └── Dockerfile            # Backend container
├── frontend/
│   ├── public/               # Static assets
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   ├── contexts/         # React contexts
│   │   └── services/         # API services
│   ├── package.json          # Node dependencies
│   ├── Dockerfile            # Frontend container
│   └── nginx.conf            # Nginx configuration
├── docker-compose.yml        # Container orchestration
├── .env.example              # Environment template
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

## 🔐 Security

- Never commit `.env` file with real credentials
- Use GitHub tokens with minimal required permissions
- Rotate API keys regularly
- Review all generated code before merging PRs
- Keep dependencies updated

## 🐛 Troubleshooting

### GitHub API Errors

- Verify your GitHub OAuth app is configured correctly
- Check rate limits: https://api.github.com/rate_limit
- Ensure callback URL matches your setup

### Database Connection Issues

```bash
# Check Neo4j is running
docker-compose ps

# View Neo4j logs
docker-compose logs neo4j
```

### Authentication Issues

```bash
# Clear browser storage
# Re-authenticate with GitHub
# Check backend logs for OAuth errors
docker-compose logs backend
```

## 🛣️ Roadmap

- [ ] Enhanced GitHub Copilot integration
- [ ] Real-time progress updates via WebSockets
- [ ] Multi-agent collaboration
- [ ] Advanced testing and validation
- [ ] Kubernetes deployment configs
- [ ] Mobile native apps (iOS/Android)
- [ ] Code review automation
- [ ] Performance analytics dashboard

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is open source and available under the MIT License.

## 👨‍💻 Author

Created with ❤️ for automating development tasks from anywhere

## 🙏 Acknowledgments

- GitHub API & Copilot
- Neo4j Graph Database
- FastAPI Framework
- React Team

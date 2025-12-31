# Auto-Code Platform v1

🤖 Asynchronous AI Development Agent Platform

A headless server platform that orchestrates AI development agents to automate coding tasks from mobile devices.

## 🌟 Features

- **📱 Mobile-First PWA**: Create development tickets from any mobile device
- **🔄 Asynchronous Processing**: RabbitMQ-based task queue for scalable processing
- **🤖 AI Agents**: Claude-powered agents that understand requirements and write code
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
│  RabbitMQ   │  (Message Queue)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Worker    │  (AI Agent Consumer)
│   Agents    │  + Claude Code
└─────────────┘
```

## 📦 Tech Stack

- **Frontend**: React 18, PWA, Axios
- **Backend**: Python 3.11, FastAPI, Uvicorn
- **Queue**: RabbitMQ
- **AI**: Claude API (Anthropic)
- **VCS**: GitHub API (PyGithub)
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
   GITHUB_TOKEN=your_github_token
   GITHUB_OWNER=your_username
   GITHUB_REPO=your_repo_name
   ANTHROPIC_API_KEY=your_anthropic_key
   ```

3. **Start the platform**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - RabbitMQ Management: http://localhost:15672 (guest/guest)

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
   - Queue the task in RabbitMQ
   - Assign an AI agent to work on it
   - Create a pull request when complete

### Using the API

Create a ticket programmatically:

```bash
curl -X POST http://localhost:8000/tickets \
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
curl http://localhost:8000/health
```

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
│   ├── agent.py              # AI agent implementation
│   ├── config.py             # Configuration management
│   ├── github_client.py      # GitHub API integration
│   ├── main.py               # FastAPI application
│   ├── rabbitmq_client.py    # RabbitMQ integration
│   ├── worker.py             # Task worker/consumer
│   ├── requirements.txt      # Python dependencies
│   └── Dockerfile            # Backend container
├── frontend/
│   ├── public/               # Static assets
│   ├── src/
│   │   ├── App.js            # Main React component
│   │   ├── index.js          # Entry point
│   │   ├── index.css         # Global styles
│   │   └── serviceWorkerRegistration.js  # PWA support
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

### RabbitMQ Connection Issues
```bash
# Check RabbitMQ is running
docker-compose ps

# View RabbitMQ logs
docker-compose logs rabbitmq
```

### GitHub API Errors
- Verify your GitHub token has `repo` scope
- Check rate limits: https://api.github.com/rate_limit
- Ensure repository name is correct in `.env`

### Worker Not Processing Tasks
```bash
# Check worker logs
docker-compose logs worker

# Restart worker
docker-compose restart worker
```

## 🛣️ Roadmap

- [ ] Enhanced Claude integration for code generation
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

- Claude AI by Anthropic
- GitHub API
- RabbitMQ
- FastAPI Framework
- React Team
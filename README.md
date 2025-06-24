# 🚀 Agaip Framework v3.0

**Super Power Agentic AI Framework** - Global, scalable, and modern AI agent framework

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

Agaip is a powerful, modern, and scalable framework for building and managing AI agents. Built with FastAPI, it provides a robust foundation for creating distributed AI systems with enterprise-grade features.

## ✨ Features

### 🏗️ **Modern Architecture**
- **Event-Driven**: Asynchronous event bus for decoupled communication
- **Microservices Ready**: Container-native with Kubernetes support
- **Plugin System**: Hot-reloadable plugins with dependency injection
- **Repository Pattern**: Clean data access layer with Tortoise ORM

### 🔧 **Developer Experience**
- **Type Safety**: Full TypeScript-like type hints with Pydantic
- **Auto Documentation**: Interactive API docs with OpenAPI/Swagger
- **CLI Tools**: Rich command-line interface for development
- **Hot Reload**: Development server with automatic reloading

### 📊 **Observability**
- **Structured Logging**: JSON-formatted logs with request tracing
- **Metrics**: Prometheus metrics with Grafana dashboards
- **Health Checks**: Kubernetes-ready health and readiness probes
- **Distributed Tracing**: OpenTelemetry integration

### 🔒 **Security & Scalability**
- **JWT Authentication**: Secure API access with role-based permissions
- **Rate Limiting**: Configurable rate limiting per user/IP
- **Multi-Database**: Support for PostgreSQL, MySQL, SQLite
- **Background Tasks**: Celery integration for async processing

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Poetry (recommended) or pip
- Redis (for caching and task queue)
- PostgreSQL (optional, SQLite by default)

### Installation

```bash
# Clone the repository
git clone https://github.com/bayrameker/agaip.git
cd agaip

# Install with Poetry (recommended)
poetry install

# Or with pip
pip install -e .
```

### Initialize & Run

```bash
# Initialize the application
agaip init

# Start the development server
agaip serve --reload

# Or with uvicorn directly
uvicorn agaip.api.app:get_app --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/api/v1/health

## 📖 Usage

### Creating Your First Agent

```python
from agaip.plugins.base import BasePlugin
from typing import Dict, Any

class MyAIPlugin(BasePlugin):
    """Custom AI plugin example."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.name = "my_ai_plugin"
        self.version = "1.0.0"
    
    async def load_model(self) -> None:
        """Load your AI model here."""
        # Initialize your model
        self.model = "your_model_here"
        self.is_loaded = True
    
    async def predict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make predictions."""
        # Your prediction logic
        return {
            "prediction": "result",
            "confidence": 0.95,
            "model": self.name
        }
```

### API Usage

```python
import httpx

# Create a task
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/tasks",
        json={
            "name": "My Task",
            "agent_id": "my_agent",
            "payload": {"input": "Hello, AI!"}
        },
        headers={"Authorization": "Bearer your-api-key"}
    )
    
    task = response.json()
    print(f"Task created: {task['id']}")
```

### CLI Commands

```bash
# Application management
agaip serve --host 0.0.0.0 --port 8000 --workers 4
agaip status
agaip init

# Database operations
agaip db migrate
agaip db reset

# Plugin management
agaip plugin list
agaip plugin load my_plugin

# Development tools
agaip dev test
agaip dev lint
```

## 🐳 Docker Deployment

### Development

```bash
# Start with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f agaip-api
```

### Production

```bash
# Build production image
docker build --target production -t agaip:latest .

# Run with environment variables
docker run -d \
  -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e DATABASE_URL=postgresql://user:pass@db:5432/agaip \
  -e REDIS_URL=redis://redis:6379/0 \
  agaip:latest
```

## 🏗️ Architecture

```
agaip/
├── 🏛️ core/              # Core framework components
│   ├── application.py     # Application factory
│   ├── container.py       # Dependency injection
│   ├── events.py          # Event system
│   └── exceptions.py      # Custom exceptions
├── ⚙️ config/             # Configuration management
├── 🗄️ database/           # Database layer
│   ├── models/            # Database models
│   └── repositories/      # Repository pattern
├── 🌐 api/                # API layer
│   ├── v1/                # API version 1
│   └── middleware.py      # Custom middleware
├── 🔌 plugins/            # Plugin system
│   ├── base.py            # Base plugin class
│   ├── loader.py          # Plugin loader
│   └── builtin/           # Built-in plugins
├── 🤖 agents/             # Agent management
├── 📊 services/           # Business logic
└── 🛠️ monitoring/         # Observability
```

## 🔧 Configuration

Create a `.env` file:

```env
# Environment
ENVIRONMENT=development
DEBUG=true

# API
API_HOST=0.0.0.0
API_PORT=8000

# Database
DATABASE_URL=sqlite://./data/agaip.db

# Security
JWT_SECRET_KEY=your-secret-key
DEFAULT_API_KEY=your-api-key

# Redis
REDIS_URL=redis://localhost:6379/0

# Monitoring
METRICS_ENABLED=true
TRACING_ENABLED=false
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=agaip --cov-report=html

# Run specific test file
pytest tests/test_api.py -v

# Run integration tests
pytest tests/integration/ -v
```

## 📈 Monitoring

### Metrics (Prometheus)

```bash
# Access metrics
curl http://localhost:9090/metrics
```

### Health Checks

```bash
# Basic health
curl http://localhost:8000/api/v1/health

# Detailed health
curl http://localhost:8000/api/v1/health/detailed

# Kubernetes probes
curl http://localhost:8000/api/v1/ready
curl http://localhost:8000/api/v1/live
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone and setup
git clone https://github.com/bayrameker/agaip.git
cd agaip

# Install development dependencies
poetry install --with dev,test

# Setup pre-commit hooks
pre-commit install

# Run tests
pytest

# Format code
black agaip/
isort agaip/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the amazing web framework
- [Tortoise ORM](https://tortoise.github.io/) for async database operations
- [Celery](https://docs.celeryq.dev/) for distributed task processing
- [Pydantic](https://docs.pydantic.dev/) for data validation

---

**Made with ❤️ by the Agaip Team**

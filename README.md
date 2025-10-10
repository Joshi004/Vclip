# Chatbot Application

A modern chatbot application powered by Llama 3 via Ollama, featuring a React frontend with Material-UI and a FastAPI backend, both fully containerized with Docker.

## Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│  React Frontend │ HTTP    │ FastAPI Backend  │ HTTP    │ Ollama (Local)  │
│  (Port 5174)    ├────────>│ (Port 8088)      ├────────>│ (Port 11434)    │
│  MUI + Nginx    │         │ (Docker)         │         │ llama3 model    │
└─────────────────┘         └──────────────────┘         └─────────────────┘
```

## Features

- ✅ **Modular Architecture**: Clean separation of concerns in both frontend and backend
- ✅ **Fully Containerized**: Both frontend and backend run in Docker containers
- ✅ **Production Ready**: Multi-stage Docker builds with Nginx for frontend
- ✅ **Modern UI**: Material-UI components with responsive design
- ✅ **Conversation History**: Maintains context across multiple turns
- ✅ **Error Handling**: Comprehensive error handling and user feedback
- ✅ **Non-Default Ports**: Configured to avoid conflicts with other services

## Project Structure

```
ChatBot/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py            # Entry point
│   │   ├── core/              # Configuration
│   │   │   └── config.py
│   │   ├── api/routes/        # API endpoints
│   │   │   ├── health.py
│   │   │   └── chat.py
│   │   ├── schemas/           # Pydantic models
│   │   │   ├── chat.py
│   │   │   └── health.py
│   │   └── services/          # Business logic
│   │       └── ollama_service.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── ChatMessage.jsx
│   │   │   ├── ChatList.jsx
│   │   │   └── ChatInput.jsx
│   │   ├── services/          # API layer
│   │   │   └── api.js
│   │   ├── config/            # Constants
│   │   │   └── constants.js
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── theme.js
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf
└── docker-compose.yml          # Orchestration
```

## Prerequisites

1. **Docker & Docker Compose** installed
2. **Ollama** installed and running on your local machine
3. **Llama 3 model** pulled in Ollama

## Setup Instructions

### 1. Verify Ollama Setup

```bash
# Check if Ollama is installed
which ollama
ollama --version

# Check if llama3 model is available
ollama list | grep -i llama3

# If not available, pull it
ollama pull llama3

# Verify Ollama is running (default port: 11434)
curl -s http://localhost:11434/api/tags | head -c 200
```

### 2. Start the Application

The entire application can be started with a single command:

```bash
# Build and start both containers
docker compose up -d --build

# View logs
docker compose logs -f
```

### 3. Access the Application

- **Frontend**: http://localhost:5174
- **Backend API**: http://localhost:8088
- **API Documentation**: http://localhost:8088/docs
- **Health Check**: http://localhost:8088/health

## Usage

### Starting a Conversation

1. Open http://localhost:5174 in your browser
2. Type your message in the input field
3. Press Enter or click the Send button
4. Wait for the assistant's response (first response may take 10-30 seconds)

### Keyboard Shortcuts

- **Enter**: Send message
- **Shift + Enter**: New line in message

## Development

### Running Frontend Locally (without Docker)

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:5174

### Running Backend Locally (without Docker)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=llama3

# Run the server
uvicorn app.main:app --host 0.0.0.0 --port 8088 --reload
```

## API Endpoints

### Health Check
```bash
GET /health

Response:
{
  "status": "ok",
  "ollama_url": "http://host.docker.internal:11434",
  "model": "llama3"
}
```

### Chat
```bash
POST /chat
Content-Type: application/json

Request:
{
  "message": "Hello!",
  "history": [
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello! How can I help?"}
  ]
}

Response:
{
  "reply": "Hi there! I'm here to assist you."
}
```

## Docker Commands

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# Rebuild and restart
docker compose up -d --build

# View logs
docker compose logs -f

# View specific service logs
docker compose logs -f backend
docker compose logs -f frontend

# Check service status
docker compose ps

# Remove all containers and volumes
docker compose down -v
```

## Troubleshooting

### Backend Issues

**Container won't start:**
```bash
# Check logs
docker compose logs backend

# Rebuild
docker compose down
docker compose up -d --build backend
```

**502 errors from /chat endpoint:**
- Verify Ollama is running: `ps aux | grep ollama`
- Check Ollama port: `lsof -i :11434`
- Test Ollama directly: `curl http://localhost:11434/api/tags`
- Check Docker can reach host:
  ```bash
  docker exec chatbot-backend curl http://host.docker.internal:11434/api/tags
  ```

### Frontend Issues

**Cannot connect to backend:**
- Verify backend is running: `curl http://localhost:8088/health`
- Check browser console for CORS errors
- Ensure both containers are on the same network

**Port conflicts:**
- If port 5174 or 8088 is in use, update `docker-compose.yml`
- Change the port mappings: `"NEW_PORT:80"` for frontend, `"NEW_PORT:8088"` for backend

### Ollama on Different Port

If Ollama runs on a different port, update `docker-compose.yml`:

```yaml
services:
  backend:
    environment:
      - OLLAMA_BASE_URL=http://host.docker.internal:YOUR_PORT
```

## Configuration

### Environment Variables

**Backend (`docker-compose.yml`):**
- `OLLAMA_BASE_URL`: URL to Ollama API (default: `http://host.docker.internal:11434`)
- `OLLAMA_MODEL`: Model name (default: `llama3`)

**Frontend (`docker-compose.yml` build args):**
- `VITE_API_BASE_URL`: Backend API URL (default: `http://localhost:8088`)

## Performance Notes

- **First Response**: May take 10-30 seconds as Ollama loads the model into memory
- **Subsequent Responses**: Typically 2-5 seconds
- **Memory Requirements**: Llama 3 requires sufficient RAM (4-8GB recommended)

## Tech Stack

**Frontend:**
- React 18
- Material-UI (MUI) 5
- Vite
- Nginx (production)

**Backend:**
- FastAPI
- Python 3.11
- Uvicorn
- httpx
- Pydantic

**Infrastructure:**
- Docker
- Docker Compose
- Ollama
- Llama 3

## License

MIT

## Support

For issues or questions, please check the troubleshooting section or review the API documentation at http://localhost:8088/docs


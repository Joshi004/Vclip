# Configuration Guide

## Overview

The application uses environment variables for configuration, loaded through Pydantic Settings. All settings have sensible defaults for development and can be customized via environment variables.

## Environment Variables

### Application Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `DEBUG_SQL` | `false` | Enable SQLAlchemy query logging |

### Ollama Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | `llama3` | Model name to use for chat |

### PostgreSQL Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_HOST` | `postgres` | PostgreSQL hostname |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_DB` | `chatbot` | Database name |
| `POSTGRES_USER` | `chatbot_user` | Database user |
| `POSTGRES_PASSWORD` | `chatbot_password` | Database password |

**Constructed URL:**
```
postgresql://chatbot_user:chatbot_password@postgres:5432/chatbot
```

### Qdrant Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `QDRANT_HOST` | `qdrant` | Qdrant hostname |
| `QDRANT_PORT` | `6333` | Qdrant HTTP port |
| `QDRANT_GRPC_PORT` | `6334` | Qdrant gRPC port |
| `QDRANT_COLLECTION` | `chat_history` | Collection name for chat embeddings |

**Constructed URL:**
```
http://qdrant:6333
```

### Embedding Model Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence-transformers model name |
| `EMBEDDING_DIM` | `384` | Vector dimension (must match model) |
| `EMBEDDING_DEVICE` | `cpu` | Device to run embeddings (`cpu` or `cuda`) |
| `EMBEDDING_BATCH_SIZE` | `32` | Batch size for embedding generation |

**Available Models:**

| Model | Dimensions | Speed | Quality | Size |
|-------|------------|-------|---------|------|
| `all-MiniLM-L6-v2` | 384 | ⚡⚡⚡ Fast | ⭐⭐⭐ Good | 80 MB |
| `all-mpnet-base-v2` | 768 | ⚡⚡ Medium | ⭐⭐⭐⭐ Better | 420 MB |
| `paraphrase-multilingual-MiniLM-L12-v2` | 384 | ⚡⚡ Medium | ⭐⭐⭐ Good | 120 MB |

### Context Retrieval Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `RETRIEVAL_TOP_K` | `5` | Number of similar messages to retrieve |
| `RETRIEVAL_SCORE_THRESHOLD` | `0.5` | Minimum similarity score (0.0-1.0) |
| `RETRIEVAL_MAX_CONTEXT_LENGTH` | `2000` | Max characters in retrieved context |

**Tuning Guidelines:**

- **`RETRIEVAL_TOP_K`**: 
  - Lower (3): Faster, more focused context
  - Higher (10): Slower, broader context
  
- **`RETRIEVAL_SCORE_THRESHOLD`**:
  - Lower (0.3): More context, possibly less relevant
  - Higher (0.7): Less context, highly relevant only

### Session Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SESSION_TIMEOUT_HOURS` | `24` | Session expiry time |
| `MAX_MESSAGES_PER_SESSION` | `1000` | Max messages per session |

## Configuration Profiles

### Development (Default)

```bash
# Use docker service names
POSTGRES_HOST=postgres
QDRANT_HOST=qdrant

# Debug enabled
DEBUG_SQL=true
LOG_LEVEL=DEBUG

# Fast, small model
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu
```

### Production

```bash
# External services
POSTGRES_HOST=prod-postgres.example.com
QDRANT_HOST=prod-qdrant.example.com

# Production settings
DEBUG_SQL=false
LOG_LEVEL=INFO

# Better model if resources available
EMBEDDING_MODEL=all-mpnet-base-v2
EMBEDDING_DEVICE=cuda  # If GPU available

# Stricter retrieval
RETRIEVAL_SCORE_THRESHOLD=0.6
RETRIEVAL_TOP_K=3
```

### Testing

```bash
# Localhost services
POSTGRES_HOST=localhost
QDRANT_HOST=localhost

# Test database
POSTGRES_DB=chatbot_test

# Fast processing
EMBEDDING_BATCH_SIZE=64
RETRIEVAL_TOP_K=3
```

## Setting Environment Variables

### Docker Compose (Recommended)

Edit `docker-compose.yml`:

```yaml
services:
  backend:
    environment:
      - POSTGRES_HOST=postgres
      - QDRANT_HOST=qdrant
      - EMBEDDING_MODEL=all-MiniLM-L6-v2
      - RETRIEVAL_TOP_K=5
```

### .env File (Not recommended for Docker)

Create `.env` in backend directory:

```bash
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
QDRANT_HOST=qdrant
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### Shell Export

```bash
export POSTGRES_HOST=localhost
export QDRANT_HOST=localhost
export EMBEDDING_MODEL=all-MiniLM-L6-v2
```

## Validation

### Check Configuration

```python
from app.core.config import settings

# View all configuration
print(settings.get_config_summary())

# Check specific values
print(f"Database URL: {settings.database_url}")
print(f"Qdrant URL: {settings.qdrant_url}")
print(f"Embedding Model: {settings.embedding_model}")
```

### Test Connections

```bash
# From backend directory
python -m app.core.validate_config
```

## Common Issues

### PostgreSQL Connection Failed

**Problem:** `could not connect to server: Connection refused`

**Solutions:**
- Ensure PostgreSQL container is running: `docker ps`
- Check `POSTGRES_HOST` matches service name in docker-compose
- Verify network connectivity: `docker exec backend ping postgres`

### Qdrant Connection Failed

**Problem:** `Connection refused on port 6333`

**Solutions:**
- Ensure Qdrant container is running
- Check `QDRANT_HOST` and `QDRANT_PORT`
- Verify Qdrant is healthy: `curl http://localhost:6333/healthz`

### Embedding Model Not Found

**Problem:** `Model 'xxx' not found`

**Solutions:**
- Check model name spelling
- First run downloads model (may take time)
- Ensure internet connection for download
- Check disk space for model storage

### Out of Memory

**Problem:** `RuntimeError: CUDA out of memory` or system crash

**Solutions:**
- Use CPU instead: `EMBEDDING_DEVICE=cpu`
- Use smaller model: `EMBEDDING_MODEL=all-MiniLM-L6-v2`
- Reduce batch size: `EMBEDDING_BATCH_SIZE=8`

## Performance Tuning

### For Speed

```bash
EMBEDDING_MODEL=all-MiniLM-L6-v2  # Fastest
EMBEDDING_DEVICE=cuda              # If GPU available
EMBEDDING_BATCH_SIZE=64            # Higher batch
RETRIEVAL_TOP_K=3                  # Fewer results
```

### For Quality

```bash
EMBEDDING_MODEL=all-mpnet-base-v2  # Better quality
RETRIEVAL_TOP_K=10                 # More context
RETRIEVAL_SCORE_THRESHOLD=0.4      # Lower threshold
```

### For Memory Efficiency

```bash
EMBEDDING_MODEL=all-MiniLM-L6-v2  # Smaller
EMBEDDING_DEVICE=cpu               # Less memory
EMBEDDING_BATCH_SIZE=16            # Smaller batches
RETRIEVAL_TOP_K=3                  # Less context
```

## Security Considerations

### Sensitive Values

Never commit these to version control:
- `POSTGRES_PASSWORD`
- Database URLs with credentials
- API keys (if added later)

### Production Checklist

- [ ] Change default passwords
- [ ] Use environment-specific `.env` files
- [ ] Enable SSL for PostgreSQL
- [ ] Use secrets management (Docker secrets, Kubernetes secrets)
- [ ] Limit CORS origins
- [ ] Disable SQL debug logging
- [ ] Use read-only database replicas for queries

## Monitoring Configuration

Add logging to track configuration issues:

```python
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# Log configuration on startup
logger.info("Configuration loaded:")
for key, value in settings.get_config_summary().items():
    logger.info(f"  {key}: {value}")
```

## References

- [Pydantic Settings](https://docs.pydantic.dev/latest/usage/settings/)
- [Sentence Transformers Models](https://www.sbert.net/docs/pretrained_models.html)
- [Qdrant Configuration](https://qdrant.tech/documentation/guides/configuration/)
- [PostgreSQL Environment Variables](https://www.postgresql.org/docs/current/libpq-envars.html)


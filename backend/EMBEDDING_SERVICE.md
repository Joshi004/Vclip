# Embedding Service Documentation

## Overview

The Embedding Service provides text-to-vector conversion capabilities using sentence-transformers. It generates semantic embeddings that enable similarity search and context retrieval in the chat system.

## Architecture

```
Text Input
    ↓
Embedding Service
    ├─ sentence-transformers Model
    ├─ Device: CPU/CUDA
    └─ Batch Processing
    ↓
Vector Output (384 dimensions)
    ↓
Qdrant Vector Database
```

## Features

### ✅ Singleton Pattern
- Model loaded once and reused
- Efficient memory usage
- Thread-safe initialization

### ✅ Batch Processing
- Process multiple texts efficiently
- Configurable batch size
- Progress tracking

### ✅ Flexible Device Support
- CPU or CUDA (GPU)
- Automatic device selection
- Configurable via environment

### ✅ Normalized Embeddings
- Cosine similarity ready
- Unit vectors for efficient comparison
- Consistent similarity scores

### ✅ Error Handling
- Validates inputs
- Graceful failure
- Detailed error messages

## Usage

### Basic Usage

```python
from app.services.embedding_service import embedding_service

# Generate single embedding
text = "This is a test sentence."
embedding = embedding_service.generate_embedding(text)
# Returns: List[float] with 384 dimensions

# Check dimension
len(embedding)  # 384
```

### Batch Processing

```python
# Generate multiple embeddings efficiently
texts = [
    "First message",
    "Second message",
    "Third message"
]

embeddings = embedding_service.generate_embeddings_batch(texts)
# Returns: List[List[float]] - one embedding per text

len(embeddings)  # 3
len(embeddings[0])  # 384
```

### Compute Similarity

```python
# Compare two texts
text1 = "I love Python programming"
text2 = "Python is a great language"

emb1 = embedding_service.generate_embedding(text1)
emb2 = embedding_service.generate_embedding(text2)

similarity = embedding_service.compute_similarity(emb1, emb2)
# Returns: float between 0 and 1 (higher = more similar)

print(f"Similarity: {similarity:.4f}")  # e.g., 0.8523
```

### Check Model Info

```python
info = embedding_service.get_model_info()
print(info)
# {
#     'model_name': 'all-MiniLM-L6-v2',
#     'dimension': 384,
#     'device': 'cpu',
#     'batch_size': 32,
#     'initialized': True
# }
```

## API Reference

### Methods

#### `generate_embedding(text: str, normalize: bool = True) -> List[float]`

Generate embedding for a single text.

**Parameters:**
- `text` (str): Input text to embed
- `normalize` (bool): Whether to normalize the vector (default: True)

**Returns:**
- List[float]: Embedding vector

**Raises:**
- `ValueError`: If text is empty
- `RuntimeError`: If model not initialized

**Example:**
```python
embedding = embedding_service.generate_embedding("Hello world")
```

---

#### `generate_embeddings_batch(texts: List[str], normalize: bool = True, show_progress: bool = False) -> List[List[float]]`

Generate embeddings for multiple texts (batch).

**Parameters:**
- `texts` (List[str]): List of texts to embed
- `normalize` (bool): Whether to normalize vectors
- `show_progress` (bool): Show progress bar

**Returns:**
- List[List[float]]: List of embedding vectors

**Raises:**
- `ValueError`: If texts list is empty
- `RuntimeError`: If model not initialized

**Example:**
```python
texts = ["First text", "Second text", "Third text"]
embeddings = embedding_service.generate_embeddings_batch(texts)
```

---

#### `compute_similarity(embedding1, embedding2) -> float`

Compute cosine similarity between two embeddings.

**Parameters:**
- `embedding1` (List[float] | np.ndarray): First embedding
- `embedding2` (List[float] | np.ndarray): Second embedding

**Returns:**
- float: Similarity score (0-1, higher is more similar)

**Example:**
```python
similarity = embedding_service.compute_similarity(emb1, emb2)
```

---

#### `get_embedding_dimension() -> int`

Get the dimension of embeddings produced by the model.

**Returns:**
- int: Embedding dimension

---

#### `is_initialized() -> bool`

Check if model is loaded and ready.

**Returns:**
- bool: True if initialized

---

#### `get_model_info() -> dict`

Get information about the loaded model.

**Returns:**
- dict: Model metadata

## Configuration

Configuration is loaded from environment variables via `app.core.config.settings`:

```python
# In docker-compose.yml or .env
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIM=384
EMBEDDING_DEVICE=cpu
EMBEDDING_BATCH_SIZE=32
```

### Available Models

| Model | Dimensions | Speed | Quality | Size |
|-------|------------|-------|---------|------|
| **all-MiniLM-L6-v2** (default) | 384 | ⚡⚡⚡ Fast | ⭐⭐⭐ Good | 80 MB |
| all-mpnet-base-v2 | 768 | ⚡⚡ Medium | ⭐⭐⭐⭐ Better | 420 MB |
| paraphrase-multilingual-MiniLM-L12-v2 | 384 | ⚡⚡ Medium | ⭐⭐⭐ Good | 120 MB |

## Performance

### Benchmarks (CPU - M1 Mac)

| Operation | Time | Notes |
|-----------|------|-------|
| Model Loading | ~2-3s | One-time cost |
| Single Embedding | ~10ms | Short text |
| Single Embedding | ~50ms | Long text (500 words) |
| Batch (10 texts) | ~80ms | Average |
| Batch (100 texts) | ~600ms | With batch_size=32 |

### GPU Acceleration

To use GPU (if available):

```bash
EMBEDDING_DEVICE=cuda
```

**Performance Improvement:**
- 3-5x faster embedding generation
- Especially beneficial for large batches
- Requires CUDA-compatible GPU

## Integration Examples

### Chat Message Storage

```python
from app.services.embedding_service import embedding_service

def store_message(content: str, session_id: str):
    # Generate embedding for the message
    embedding = embedding_service.generate_embedding(content)
    
    # Store in Qdrant with metadata
    qdrant_client.upsert(
        collection_name="chat_history",
        points=[{
            "id": message_id,
            "vector": embedding,
            "payload": {
                "session_id": session_id,
                "content": content
            }
        }]
    )
```

### Context Retrieval

```python
def retrieve_context(query: str, session_id: str, top_k: int = 5):
    # Generate embedding for the query
    query_embedding = embedding_service.generate_embedding(query)
    
    # Search in Qdrant
    results = qdrant_client.search(
        collection_name="chat_history",
        query_vector=query_embedding,
        query_filter={
            "must": [{"key": "session_id", "match": {"value": session_id}}]
        },
        limit=top_k
    )
    
    return results
```

## Error Handling

### Common Errors

**1. Model Not Initialized**
```python
try:
    embedding = embedding_service.generate_embedding(text)
except RuntimeError as e:
    logger.error(f"Model not ready: {e}")
```

**2. Empty Input**
```python
try:
    embedding = embedding_service.generate_embedding("")
except ValueError as e:
    logger.error(f"Invalid input: {e}")
```

**3. CUDA Not Available**
```python
# Automatically falls back to CPU if CUDA not available
# Check logs for warnings
```

## Testing

### Run Tests

```bash
cd backend
python test_embedding_service.py
```

### Test Output

```
====================================================================
EMBEDDING SERVICE TEST
====================================================================

📋 Test 1: Model Initialization
------------------------------------------------------------
✅ Model is initialized
   Model: all-MiniLM-L6-v2
   Dimensions: 384
   Device: cpu

📋 Test 2: Generate Single Embedding
------------------------------------------------------------
✅ Generated embedding in 0.012s
   Embedding dimension: 384

📋 Test 3: Generate Batch Embeddings
------------------------------------------------------------
✅ Generated 5 embeddings in 0.068s

📋 Test 4: Compute Similarity
------------------------------------------------------------
Similarity (related): 0.7845
Similarity (unrelated): 0.2134
✅ Similarity works correctly

====================================================================
TEST SUMMARY
====================================================================
✅ All tests passed!
```

## Troubleshooting

### Issue: Model Download Fails

**Problem:** First run downloads model from Hugging Face

**Solution:**
- Ensure internet connection
- Check disk space (~100 MB needed)
- Model is cached for future use

### Issue: Out of Memory

**Problem:** Large batch sizes cause OOM

**Solutions:**
- Reduce batch size: `EMBEDDING_BATCH_SIZE=8`
- Use smaller model: `EMBEDDING_MODEL=all-MiniLM-L6-v2`
- Process in smaller chunks

### Issue: Slow Performance

**Problem:** Embedding generation is slow

**Solutions:**
- Use GPU if available: `EMBEDDING_DEVICE=cuda`
- Use batch processing instead of individual calls
- Use smaller model for faster inference

### Issue: Dimension Mismatch

**Problem:** Qdrant expects different dimension

**Solution:**
- Ensure `EMBEDDING_DIM` matches model output
- all-MiniLM-L6-v2 = 384 dimensions
- all-mpnet-base-v2 = 768 dimensions

## Best Practices

### ✅ DO

- Use batch processing for multiple texts
- Reuse the singleton instance
- Normalize embeddings for cosine similarity
- Handle errors gracefully
- Cache embeddings when possible

### ❌ DON'T

- Create multiple instances (breaks singleton)
- Generate embeddings for empty strings
- Mix embeddings from different models
- Compare non-normalized embeddings directly
- Process very long texts (>512 tokens) without truncation

## Advanced Usage

### Custom Similarity Threshold

```python
from app.core.config import settings

def find_relevant_messages(query: str, threshold: float = None):
    if threshold is None:
        threshold = settings.retrieval_score_threshold
    
    query_emb = embedding_service.generate_embedding(query)
    # Use threshold to filter results...
```

### Progress Tracking

```python
# Show progress bar for large batches
embeddings = embedding_service.generate_embeddings_batch(
    texts=large_text_list,
    show_progress=True
)
```

### Vector Normalization

```python
# Get unnormalized vectors (for specific use cases)
embedding = embedding_service.generate_embedding(
    text="Some text",
    normalize=False
)
```

## References

- [Sentence Transformers Documentation](https://www.sbert.net/)
- [Pre-trained Models](https://www.sbert.net/docs/pretrained_models.html)
- [Hugging Face Model Hub](https://huggingface.co/sentence-transformers)
- [Qdrant Vector Search](https://qdrant.tech/documentation/)


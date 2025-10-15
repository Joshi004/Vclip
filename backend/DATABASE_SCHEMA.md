# Database Schema Design

## Overview

The system uses a **hybrid storage approach** combining PostgreSQL and Qdrant:

- **PostgreSQL**: Stores structured session and message metadata
- **Qdrant**: Stores message embeddings for semantic search

## PostgreSQL Schema

### Table: `chat_sessions`

Represents conversation sessions. Each session contains multiple messages.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `session_id` | UUID | PRIMARY KEY | Unique session identifier |
| `user_id` | VARCHAR(255) | NULLABLE, INDEXED | User identifier (for future multi-user support) |
| `created_at` | TIMESTAMP | NOT NULL | Session creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp (auto-updated) |

**Indexes:**
- Primary key on `session_id`
- Index on `user_id` for user-based queries

**Relationships:**
- One-to-many with `chat_messages` (cascade delete)

---

### Table: `chat_messages`

Stores individual messages with metadata. References embeddings in Qdrant.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Message ID |
| `session_id` | UUID | FOREIGN KEY, NOT NULL, INDEXED | References `chat_sessions.session_id` |
| `role` | VARCHAR(50) | NOT NULL | Message sender: 'user' or 'assistant' |
| `content` | TEXT | NOT NULL | Full message text content |
| `timestamp` | TIMESTAMP | NOT NULL, INDEXED | Message creation time |
| `vector_id` | VARCHAR(255) | NULLABLE, INDEXED | Reference to Qdrant point ID |

**Indexes:**
- Primary key on `id`
- Foreign key index on `session_id`
- Index on `timestamp` for time-based queries
- Index on `vector_id` for Qdrant lookups

**Relationships:**
- Many-to-one with `chat_sessions`

**Cascade Rules:**
- Deleting a session deletes all its messages

---

## Qdrant Schema

### Collection: `chat_history`

Stores message embeddings with metadata for semantic search.

**Configuration:**
- **Vector Dimension**: 384 (matches `all-MiniLM-L6-v2` embedding model)
- **Distance Metric**: Cosine similarity
- **Index Type**: HNSW (Hierarchical Navigable Small World)
- **Storage**: On-disk payload for memory efficiency

### Point Structure

Each point in the collection represents a chat message:

```json
{
  "id": "uuid-or-sequential-id",
  "vector": [0.123, -0.456, ...],  // 384 dimensions
  "payload": {
    "session_id": "uuid-string",
    "message_id": 123,
    "role": "user",
    "content": "Full message text",
    "timestamp": "2025-10-13T10:30:00",
    "timestamp_unix": 1697195400
  }
}
```

### Payload Fields

| Field | Type | Indexed | Description |
|-------|------|---------|-------------|
| `session_id` | string | ✅ Yes | UUID of the chat session |
| `message_id` | integer | ✅ Yes | PostgreSQL message ID |
| `role` | string | ✅ Yes | 'user' or 'assistant' |
| `content` | string | ❌ No | Full message text |
| `timestamp` | string | ❌ No | ISO format timestamp |
| `timestamp_unix` | integer | ✅ Yes | Unix timestamp for filtering |

**Indexed fields** support efficient filtering during search.

### HNSW Index Parameters

- **m**: 16 (edges per node - balances quality and memory)
- **ef_construct**: 100 (construction quality)
- **full_scan_threshold**: 10,000 (use full scan for small datasets)

---

## Data Flow

### 1. Storing a Message

```
User Message
    ↓
1. Insert into PostgreSQL → Get message_id
    ↓
2. Generate embedding (384 dims)
    ↓
3. Store in Qdrant with payload
    ↓
4. Update PostgreSQL with vector_id
```

### 2. Retrieving Context

```
User Query
    ↓
1. Generate query embedding
    ↓
2. Search Qdrant (semantic similarity)
    ├─ Filter by session_id
    ├─ Optionally filter by timestamp
    └─ Return top K similar messages
    ↓
3. Enrich with PostgreSQL metadata (if needed)
    ↓
4. Return context to LLM
```

---

## Query Patterns

### Get Session History (Chronological)

```sql
SELECT id, role, content, timestamp
FROM chat_messages
WHERE session_id = :session_id
ORDER BY timestamp ASC;
```

### Search Similar Messages (Semantic)

```python
qdrant_client.search(
    collection_name="chat_history",
    query_vector=embedding,
    query_filter={
        "must": [
            {"key": "session_id", "match": {"value": session_id}}
        ]
    },
    limit=5
)
```

### Get Recent Sessions

```sql
SELECT session_id, created_at, updated_at,
       COUNT(m.id) as message_count
FROM chat_sessions s
LEFT JOIN chat_messages m ON s.session_id = m.session_id
GROUP BY s.session_id
ORDER BY s.updated_at DESC
LIMIT 20;
```

---

## Storage Estimates

### PostgreSQL

**chat_sessions:**
- ~100 bytes per row
- 1M sessions ≈ 100 MB

**chat_messages:**
- ~500 bytes per row (avg)
- 10M messages ≈ 5 GB

### Qdrant

**chat_history:**
- Vector: 384 floats × 4 bytes = 1,536 bytes
- Payload: ~200 bytes (avg)
- Total: ~1,736 bytes per point
- 10M points ≈ 17 GB

---

## Indexing Strategy

### PostgreSQL Indexes

1. **Primary Keys**: Fast lookups by ID
2. **Foreign Keys**: Efficient joins
3. **session_id**: Filter messages by session
4. **timestamp**: Time-based queries
5. **user_id**: User-based filtering (future)

### Qdrant Indexes

1. **HNSW Vector Index**: Fast approximate nearest neighbor search
2. **Payload Indexes**: Efficient filtering during search
   - `session_id`: Session-scoped search
   - `role`: Filter by message sender
   - `timestamp_unix`: Time-range filtering

---

## Maintenance

### PostgreSQL

```sql
-- Vacuum and analyze for optimal performance
VACUUM ANALYZE chat_sessions;
VACUUM ANALYZE chat_messages;

-- Reindex if needed
REINDEX TABLE chat_messages;
```

### Qdrant

```python
# Optimize collection
qdrant_client.update_collection(
    collection_name="chat_history",
    optimizer_config={"indexing_threshold": 10000}
)

# Create snapshot for backup
qdrant_client.create_snapshot(collection_name="chat_history")
```

---

## Scalability Considerations

### Current Design (Up to 1M messages)
- Single PostgreSQL instance
- Single Qdrant instance
- In-memory vector search

### Future Scaling (10M+ messages)
- **PostgreSQL**: 
  - Partitioning by session or time
  - Read replicas
- **Qdrant**:
  - Sharding by session_id
  - Distributed cluster
  - On-disk vectors

---

## Backup Strategy

### PostgreSQL
```bash
# Backup
pg_dump -U chatbot_user chatbot > backup.sql

# Restore
psql -U chatbot_user chatbot < backup.sql
```

### Qdrant
```bash
# Create snapshot via API
curl -X POST http://localhost:6333/collections/chat_history/snapshots

# Download snapshot
curl http://localhost:6333/collections/chat_history/snapshots/{snapshot_name}
```

---

## Migration Path

If schema changes are needed:

1. **PostgreSQL**: Use Alembic for migrations
2. **Qdrant**: Create new collection, migrate data, update config

Example Alembic setup:
```bash
alembic init alembic
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```


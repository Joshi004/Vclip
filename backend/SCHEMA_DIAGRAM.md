# Database Schema Diagram

## Entity Relationship Diagram

```
┌─────────────────────────────────────┐
│        chat_sessions                │
├─────────────────────────────────────┤
│ PK  session_id      UUID            │
│     user_id         VARCHAR(255)    │
│     created_at      TIMESTAMP       │
│     updated_at      TIMESTAMP       │
└─────────────────────────────────────┘
            │
            │ 1:N (One-to-Many)
            │ CASCADE DELETE
            ↓
┌─────────────────────────────────────┐
│        chat_messages                │
├─────────────────────────────────────┤
│ PK  id              INTEGER         │
│ FK  session_id      UUID            │───┐
│     role            VARCHAR(50)     │   │
│     content         TEXT            │   │
│     timestamp       TIMESTAMP       │   │
│     vector_id       VARCHAR(255)    │   │ References
└─────────────────────────────────────┘   │ Qdrant Point
            │                             │
            │                             │
            │ Embedding Generated         │
            ↓                             │
┌─────────────────────────────────────┐   │
│   Qdrant: chat_history Collection   │←──┘
├─────────────────────────────────────┤
│ Point ID:    vector_id              │
│ Vector:      [384 dimensions]       │
│ Payload:                            │
│   - session_id                      │
│   - message_id                      │
│   - role                            │
│   - content                         │
│   - timestamp                       │
│   - timestamp_unix                  │
└─────────────────────────────────────┘
```

## Data Flow Diagram

### Message Storage Flow

```
┌─────────────┐
│  User Input │
└──────┬──────┘
       │
       ↓
┌─────────────────────────────────────────────┐
│  1. Create/Get Session                      │
│     - Generate UUID if new                  │
│     - Insert into chat_sessions             │
└──────┬──────────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────────┐
│  2. Store Message in PostgreSQL             │
│     - Insert into chat_messages             │
│     - Get message_id                        │
└──────┬──────────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────────┐
│  3. Generate Embedding                      │
│     - Use sentence-transformers             │
│     - Output: 384-dim vector                │
└──────┬──────────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────────┐
│  4. Store in Qdrant                         │
│     - Create point with vector + metadata   │
│     - Get point_id                          │
└──────┬──────────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────────┐
│  5. Update PostgreSQL with vector_id        │
│     - Link message to Qdrant point          │
└─────────────────────────────────────────────┘
```

### Context Retrieval Flow

```
┌─────────────┐
│ User Query  │
└──────┬──────┘
       │
       ↓
┌─────────────────────────────────────────────┐
│  1. Generate Query Embedding                │
│     - Embed user's question                 │
│     - Output: 384-dim vector                │
└──────┬──────────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────────┐
│  2. Search Qdrant (Semantic)                │
│     - Vector similarity search              │
│     - Filter by session_id                  │
│     - Return top 5 similar messages         │
└──────┬──────────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────────┐
│  3. Build Context                           │
│     - Format retrieved messages             │
│     - "Previously discussed: ..."           │
└──────┬──────────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────────┐
│  4. Send to LLM with Context                │
│     - System prompt + context + query       │
│     - Generate response                     │
└──────┬──────────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────────┐
│  5. Store Assistant Response                │
│     - Same flow as user message             │
└─────────────────────────────────────────────┘
```

## Session Lifecycle

```
┌──────────────┐
│ New Session  │
└──────┬───────┘
       │
       ↓
┌─────────────────────────────────────┐
│ Session State: ACTIVE               │
│                                     │
│  Messages:                          │
│    1. User: "Hello"                 │
│    2. Assistant: "Hi! How can..."   │
│    3. User: "Tell me about..."      │
│    4. Assistant: "Sure! ..."        │
│    ...                              │
│                                     │
│  Embeddings stored in Qdrant        │
│  Metadata in PostgreSQL             │
└─────────────────────────────────────┘
       │
       │ Session idle or
       │ User creates new session
       ↓
┌─────────────────────────────────────┐
│ Session Archived                    │
│ - Still searchable                  │
│ - Can be retrieved                  │
│ - Can be deleted                    │
└─────────────────────────────────────┘
```

## Vector Search Illustration

```
Query: "What's my dog's name?"
Embedding: [0.12, -0.34, 0.56, ...]

         Qdrant Vector Space
         
    •     •   •
         •  🔍 ← Query Vector
    •   •     •
         •  ← Most similar: "I have a dog named Max"
    •     •
  •   •     •
    •   ← Less similar: "I love Python"
         •
    •  •   •


Search Results (by similarity score):
1. "I have a golden retriever named Max" (0.87)
2. "My dog loves to play fetch" (0.72)
3. "Tell me about pets" (0.45)
4. "What's the weather?" (0.12)
5. "Python programming" (0.05)

Return top 3 as context
```

## Storage Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                    │
│  ┌──────────────────────────────────────────────────┐  │
│  │           FastAPI Backend                        │  │
│  │  - Chat Routes                                   │  │
│  │  - Session Routes                                │  │
│  │  - Health Checks                                 │  │
│  └────────┬──────────────────────┬──────────────────┘  │
└───────────┼──────────────────────┼─────────────────────┘
            │                      │
            │                      │
    ┌───────▼─────────┐    ┌──────▼────────┐
    │   PostgreSQL    │    │    Qdrant     │
    │  (Structured)   │    │   (Vectors)   │
    ├─────────────────┤    ├───────────────┤
    │  chat_sessions  │    │ chat_history  │
    │  chat_messages  │    │ [embeddings]  │
    │                 │    │               │
    │  Indexes:       │    │  HNSW Index   │
    │  - PK, FK       │    │  Payload Idx  │
    │  - timestamp    │    │               │
    └─────────────────┘    └───────────────┘
            │                      │
            │                      │
    ┌───────▼──────────────────────▼─────────┐
    │         Docker Volumes                 │
    │  - postgres_data                       │
    │  - qdrant_data                         │
    └────────────────────────────────────────┘
```

## Index Structure

### PostgreSQL B-Tree Indexes

```
chat_sessions:
  PK: session_id (UUID)
    └─ Instant lookup by session

chat_messages:
  PK: id (INTEGER)
    └─ Fast message lookup
  
  FK: session_id
    └─ [session_1] → [msg_1, msg_2, msg_3]
    └─ [session_2] → [msg_4, msg_5]
    └─ [session_3] → [msg_6, msg_7, msg_8, msg_9]
  
  INDEX: timestamp
    └─ Time-based queries
```

### Qdrant HNSW Index

```
Hierarchical layers of proximity graphs:

Layer 2:  A ←→ G
          ↕     ↕
Layer 1:  A ←→ C ←→ G ←→ I
          ↕  ↕  ↕  ↕  ↕
Layer 0:  A-B-C-D-E-F-G-H-I-J
          
Search path: Enter at top layer,
             navigate to nearest,
             descend layers,
             find K nearest neighbors
```

## Scalability Path

### Current (< 1M messages)

```
┌──────────────┐
│  PostgreSQL  │ Single instance
└──────────────┘

┌──────────────┐
│   Qdrant     │ Single instance
└──────────────┘
```

### Future (10M+ messages)

```
┌──────────────┐  ┌──────────────┐
│ PostgreSQL   │  │ PostgreSQL   │
│   Primary    │←→│  Replica     │
└──────────────┘  └──────────────┘
      │
      └─ Partitioned by time/session

┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Qdrant Node  │←→│ Qdrant Node  │←→│ Qdrant Node  │
│  Shard 1     │  │  Shard 2     │  │  Shard 3     │
└──────────────┘  └──────────────┘  └──────────────┘
      │                 │                 │
      └─ Distributed by session_id hash
```


# Architecture

## Layers

1. Web Frontend: React management console and Agent debugging UI.
2. API Backend: FastAPI business API, auth, configuration and logs.
3. Agent Runtime: LangChain / LangGraph orchestration boundary.
4. Tool Gateway: MCP and built-in tool access layer.
5. RAG Service: RAGFlow integration boundary.
6. Scheduler Worker: scheduled Agent runs and notifications.
7. Storage Layer: PostgreSQL, Redis, MinIO and vector storage.

## MVP Runtime Flow

1. User sends a chat request from the web console.
2. API loads the selected Agent configuration.
3. Runtime prepares model, prompt and optional tools.
4. API returns either a JSON response or an SSE stream.
5. Logs and usage records are persisted once persistence is introduced.


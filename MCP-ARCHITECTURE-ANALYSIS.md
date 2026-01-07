# MCP Server Architecture Analysis

## Current Structure

### Directory Structure
```
mcp-server/src/
├── __init__.py
├── config.py              # Configuration (Settings class)
├── http_server.py         # HTTP/SSE transport for Azure
├── models.py              # SQLAlchemy models (shared with backend)
├── server.py              # Main MCP server (stdio + HTTP/SSE)
├── resources/             # MCP resources
│   ├── document_resources.py
│   ├── feature_resources.py
│   └── project_resources.py
├── services/              # Business logic services
│   ├── cache.py           # Redis caching
│   ├── database.py        # Database connection (SQLAlchemy)
│   ├── rules_generator.py # Cursor rules generation
│   └── signalr_broadcast.py # HTTP calls to backend for SignalR
└── tools/                 # MCP tools (AI callable functions)
    ├── document.py
    ├── feature.py
    ├── github.py
    ├── idea.py
    ├── import_tools.py
    ├── project.py
    ├── session.py
    └── todo.py
```

## Dependencies

### MCP Server Dependencies (mcp-server/requirements.txt)
- `mcp>=1.0.0` - Model Context Protocol SDK
- `sqlalchemy>=2.0.0` - Database ORM
- `psycopg2-binary>=2.9.0` - PostgreSQL driver
- `pydantic>=2.0.0` - Data validation
- `pydantic-settings>=2.0.0` - Settings management
- `python-dotenv>=1.0.0` - Environment variables
- `redis>=5.0.0` - Redis client
- `httpx>=0.25.0` - HTTP client (for SignalR broadcast)
- `PyGithub>=2.0.0` - GitHub API
- `fastapi>=0.104.0` - FastAPI (for HTTP/SSE transport)
- `uvicorn[standard]>=0.24.0` - ASGI server
- `sse-starlette>=1.6.5` - SSE support

### Backend Dependencies (backend/requirements.txt)
- `fastapi==0.109.0` - Already has FastAPI
- `sqlalchemy==2.0.25` - Already has SQLAlchemy
- `psycopg2-binary==2.9.9` - Already has PostgreSQL driver
- `pydantic==2.5.3` - Already has Pydantic
- `pydantic-settings==2.1.0` - Already has Pydantic Settings
- `python-dotenv==1.0.0` - Already has dotenv
- `redis==5.0.1` - Already has Redis
- `httpx==0.26.0` - Already has httpx
- `PyGithub==2.1.1` - Already has PyGithub

**Missing in Backend:**
- `mcp>=1.0.0` - **NEED TO ADD**
- `sse-starlette>=1.6.5` - **NEED TO ADD** (for SSE transport)

## Integration Points

### 1. Database Connection
- **Current:** MCP server has its own SQLAlchemy engine and session factory
- **After Integration:** Should use backend's database connection (`src.database.base`)
- **Location:** `mcp-server/src/services/database.py` → `backend/src/database/base.py`

### 2. Configuration
- **Current:** MCP server has separate Settings class
- **After Integration:** Should merge into backend's Settings class
- **Location:** `mcp-server/src/config.py` → `backend/src/config.py`
- **Settings to merge:**
  - `MCP_API_KEY` (already in backend)
  - `MCP_HTTP_PORT` (new, default 3001)
  - `MCP_HTTP_HOST` (new, default "0.0.0.0")

### 3. HTTP/SSE Transport
- **Current:** Separate Starlette app in `http_server.py`
- **After Integration:** Should be integrated into FastAPI app
- **Location:** `mcp-server/src/http_server.py` → `backend/src/api/controllers/mcp_controller.py`
- **Endpoints:**
  - `GET /mcp/sse` - SSE connection endpoint
  - `POST /mcp/messages/{path}` - Message endpoint
  - `GET /health` - Health check (can merge with backend's `/health`)

### 4. SignalR Broadcast
- **Current:** HTTP calls to backend API (`signalr_broadcast.py`)
- **After Integration:** Direct function calls to `signalr_hub.py`
- **Location:** `mcp-server/src/services/signalr_broadcast.py` → **REMOVE** (use direct calls)
- **Functions to call directly:**
  - `broadcast_todo_update()` from `backend/src/services/signalr_hub.py`
  - `broadcast_feature_update()` from `backend/src/services/signalr_hub.py`
  - `broadcast_project_update()` from `backend/src/services/signalr_hub.py`

### 5. Models
- **Current:** MCP server imports models from `src.models`
- **After Integration:** Should use backend's models
- **Location:** `mcp-server/src/models.py` → **REMOVE** (use `backend/src/database/models.py`)

### 6. Cache Service
- **Current:** MCP server has its own Redis cache service
- **After Integration:** Can use backend's cache service or keep separate (both use same Redis)
- **Location:** `mcp-server/src/services/cache.py` → Can keep or merge

### 7. Tools
- **Current:** All tools in `mcp-server/src/tools/`
- **After Integration:** Move to `backend/src/mcp/tools/`
- **All tools need to be moved:**
  - `project.py`
  - `feature.py`
  - `todo.py`
  - `session.py`
  - `document.py`
  - `github.py`
  - `idea.py`
  - `import_tools.py`

### 8. Resources
- **Current:** All resources in `mcp-server/src/resources/`
- **After Integration:** Move to `backend/src/mcp/resources/`
- **All resources need to be moved:**
  - `project_resources.py`
  - `feature_resources.py`
  - `document_resources.py`

### 9. Services
- **Current:** Services in `mcp-server/src/services/`
- **After Integration:** Move to `backend/src/mcp/services/`
- **Services to move:**
  - `rules_generator.py` - Keep as is
  - `cache.py` - Can keep or merge with backend cache
  - `database.py` - **REMOVE** (use backend's database)

### 10. Main Server
- **Current:** `mcp-server/src/server.py` - MCP server initialization
- **After Integration:** Move to `backend/src/mcp/server.py`
- **Changes needed:**
  - Update imports to use backend modules
  - Integrate HTTP/SSE transport into FastAPI app

## Migration Plan

### Phase 1: Move Code Structure
1. Create `backend/src/mcp/` directory
2. Move tools, resources, services to backend
3. Update all imports

### Phase 2: Integrate into FastAPI
1. Add MCP HTTP/SSE endpoints to FastAPI app
2. Register MCP server routes
3. Test HTTP/SSE transport

### Phase 3: Replace HTTP Calls
1. Update tools to call SignalR functions directly
2. Remove `signalr_broadcast.py`
3. Remove HTTP broadcast endpoints from SignalR controller

### Phase 4: Update Configuration
1. Merge MCP settings into backend config
2. Update environment variables
3. Update Docker Compose

### Phase 5: Cleanup
1. Remove `mcp-server/` directory
2. Update documentation
3. Update deployment guides

## Benefits

1. **Eliminate HTTP Indirection:** Direct function calls instead of HTTP requests
2. **Simpler Architecture:** One process instead of two
3. **Easier Debugging:** Same process, same memory
4. **Better Performance:** No network overhead for SignalR broadcasts
5. **Easier Deployment:** One container instead of two

## Risks

1. **Tight Coupling:** MCP and backend become tightly coupled
2. **Scalability:** Cannot scale MCP server independently
3. **Blocker Risk:** If MCP blocks, backend is affected

## Notes

- MCP server currently uses both stdio (for local Cursor) and HTTP/SSE (for Azure)
- After integration, HTTP/SSE will be the primary transport
- Stdio transport can still be supported if needed (for local development)

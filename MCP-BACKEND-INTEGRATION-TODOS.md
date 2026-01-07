# MCP Server Backend Integration - Todo List

## Feature
**ID:** `53199ea8-da82-4995-be6e-c9a434fee62a`  
**Name:** MCP Server Backend Integration  
**Status:** new  
**Description:** Integrate MCP server into backend to eliminate HTTP indirection for SignalR broadcasts and simplify architecture. This will allow MCP tools to directly call SignalR broadcast functions instead of making HTTP requests.

## Todos

### 1. Analyze current MCP server architecture and dependencies
**Priority:** high  
**Element:** MCP Server (7e027061-286c-4a91-b8c7-63094102d8d3)  
**Description:** Review current MCP server structure, HTTP/SSE transport implementation, and identify all dependencies that need to be moved to backend. Document current architecture and integration points.

### 2. Move MCP server code to backend/src/mcp directory
**Priority:** high  
**Element:** MCP Server (7e027061-286c-4a91-b8c7-63094102d8d3)  
**Description:** Create backend/src/mcp directory structure and move MCP server code (tools, resources, services) from mcp-server/src to backend/src/mcp. Update imports and maintain existing functionality.

### 3. Integrate MCP server into FastAPI app with HTTP/SSE endpoints
**Priority:** high  
**Element:** MCP Server (7e027061-286c-4a91-b8c7-63094102d8d3)  
**Description:** Add MCP HTTP/SSE transport endpoints to FastAPI app (backend/src/main.py). Register MCP server routes and ensure HTTP/SSE transport works correctly for Cursor integration.

### 4. Replace HTTP SignalR broadcast calls with direct function calls
**Priority:** high  
**Element:** MCP Server (7e027061-286c-4a91-b8c7-63094102d8d3)  
**Description:** Update MCP tools (todo.py, feature.py) to directly call SignalR broadcast functions from backend/src/services/signalr_hub.py instead of making HTTP requests. Remove signalr_broadcast.py service.

### 5. Update Docker Compose to remove separate MCP server container
**Priority:** medium  
**Element:** MCP Server (7e027061-286c-4a91-b8c7-63094102d8d3)  
**Description:** Remove mcp-server service from docker-compose.yml. Update backend service to include MCP server functionality. Update environment variables and dependencies.

### 6. Update backend requirements.txt with MCP dependencies
**Priority:** medium  
**Element:** MCP Server (7e027061-286c-4a91-b8c7-63094102d8d3)  
**Description:** Add MCP server dependencies (mcp, httpx, etc.) to backend/requirements.txt. Remove duplicate dependencies and ensure all required packages are included.

### 7. Remove HTTP broadcast endpoints from SignalR controller
**Priority:** low  
**Element:** MCP Server (7e027061-286c-4a91-b8c7-63094102d8d3)  
**Description:** Remove /signalr/hub/broadcast/* endpoints from backend/src/api/controllers/signalr_controller.py as they are no longer needed. MCP tools will call SignalR functions directly.

### 8. Test MCP server integration and SignalR broadcasts
**Priority:** high  
**Element:** MCP Server (7e027061-286c-4a91-b8c7-63094102d8d3)  
**Description:** Test that MCP tools can directly call SignalR broadcast functions and that frontend receives real-time updates. Verify HTTP/SSE transport works correctly for Cursor integration.

### 9. Update documentation and remove mcp-server directory ✅ DONE
**Priority:** low  
**Element:** MCP Server (7e027061-286c-4a91-b8c7-63094102d8d3)  
**Description:** Update README, architecture docs, and deployment guides to reflect MCP server integration into backend. Remove mcp-server directory after successful migration.
**Status:** Completed - mcp-server directory removed, README updated

## Notes

- All todos should be linked to the MCP Server element (7e027061-286c-4a91-b8c7-63094102d8d3)
- All todos should be linked to the feature (53199ea8-da82-4995-be6e-c9a434fee62a)
- Work should be done on a separate branch: `feature/mcp-backend-integration`
- After todos are reviewed and approved, development can begin

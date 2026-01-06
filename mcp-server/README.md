# InTracker MCP Server

Model Context Protocol (MCP) Server for InTracker - AI-first project management system.

## Overview

The MCP Server provides AI agents (like Cursor) with tools and resources to interact with InTracker projects, features, todos, sessions, and documents.

## Features

### Tools (24 tools)

**Project Tools:**
- `mcp_get_project_context` - Get full project context
- `mcp_get_resume_context` - Get resume context (Last/Now/Blockers/Constraints)
- `mcp_get_project_structure` - Get hierarchical element tree
- `mcp_get_active_todos` - Get active todos with filters

**Feature Tools:**
- `mcp_create_feature` - Create feature and link elements
- `mcp_get_feature` - Get feature with todos and elements
- `mcp_list_features` - List features with filters
- `mcp_update_feature_status` - Update status and recalculate progress
- `mcp_get_feature_todos` - Get todos for feature
- `mcp_get_feature_elements` - Get elements linked to feature
- `mcp_link_element_to_feature` - Link element to feature

**Todo Tools:**
- `mcp_create_todo` - Create todo and link to feature
- `mcp_update_todo_status` - Update status with optimistic locking
- `mcp_list_todos` - List todos with filters
- `mcp_assign_todo` - Assign todo to user

**Session Tools:**
- `mcp_start_session` - Start work session
- `mcp_update_session` - Update session with completed items
- `mcp_end_session` - End session and generate summary

**Document Tools:**
- `mcp_get_document` - Get document content
- `mcp_list_documents` - List documents for project

**GitHub Tools:**
- `mcp_get_branches` - Get branches for project or feature

### Resources

**Project Resources:**
- `intracker://project/{project_id}` - Project data

**Feature Resources:**
- `intracker://feature/{feature_id}` - Feature data with todos

**Document Resources:**
- `intracker://document/{document_id}` - Document content (markdown or JSON)

## Setup

### Local Development

1. **Create virtual environment:**
```bash
cd mcp-server
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment:**
Create `.env` file:
```env
DATABASE_URL=postgresql://intracker:intracker_dev@localhost:5433/intracker
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
GITHUB_TOKEN=your_github_token_here
```

4. **Run server:**
```bash
python -m src.server
```

### Docker

```bash
docker-compose up mcp-server
```

## Cursor Configuration

Add to your Cursor MCP settings:

```json
{
  "mcpServers": {
    "intracker": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/InTracker/mcp-server",
      "env": {
        "DATABASE_URL": "postgresql://intracker:intracker_dev@localhost:5433/intracker",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379"
      }
    }
  }
}
```

## Architecture

- **Tools**: Functions AI can call to perform actions
- **Resources**: Data AI can automatically access
- **Caching**: Redis caching for performance (graceful degradation if Redis unavailable)
- **Database**: SQLAlchemy ORM with shared models from backend

## Testing

Test the server:
```bash
python -c "from src.server import server; print('✅ Server ready')"
```

## Notes

- MCP Server uses stdio transport (standard input/output)
- All tools return JSON-formatted responses
- Resources are automatically available to AI without explicit calls
- Cache TTLs: Project context (5min), Resume context (1min), Features (2min), Documents (10min)

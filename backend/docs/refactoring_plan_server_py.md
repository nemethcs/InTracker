# Refactoring Plan: server.py (600 lines)

## Current Structure Analysis

The `server.py` file contains 5 main functions:

### 1. `list_tools()` (Lines ~23-88, ~65 lines)
- Lists all available tools
- Groups tools by category

### 2. `call_tool()` (Lines ~91-537, ~450 lines)
- Handles all tool calls
- Large if-elif chain for each tool
- Groups: Project, Feature, Todo, Session, Document, GitHub, Idea, Import

### 3. `list_resources()` (Lines ~540-556, ~20 lines)
- Lists all available resources

### 4. `read_resource()` (Lines ~559-574, ~20 lines)
- Reads a resource by URI

### 5. `main()` (Lines ~577-600, ~25 lines)
- Main entry point

## Refactoring Strategy

Split `call_tool()` into separate handler modules:

### 1. `server_handlers/` directory
- `project_handlers.py` - Project tool handlers
- `feature_handlers.py` - Feature tool handlers
- `todo_handlers.py` - Todo tool handlers
- `session_handlers.py` - Session tool handlers
- `document_handlers.py` - Document tool handlers
- `github_handlers.py` - GitHub tool handlers
- `idea_handlers.py` - Idea tool handlers
- `import_handlers.py` - Import tool handlers

### 2. `server.py` (refactored)
- Keep `list_tools()`, `list_resources()`, `read_resource()`, `main()`
- `call_tool()` delegates to handler modules

## Implementation Steps

1. Create `server_handlers/` directory
2. Create handler modules for each tool category
3. Refactor `call_tool()` to use handlers
4. Test all functionality

## Dependencies

All handlers will share:
- `TextContent` from `mcp.types`
- `json` module
- Tool modules: `project`, `feature`, `todo`, `session`, `document`, `github`, `idea`, `import_tools`

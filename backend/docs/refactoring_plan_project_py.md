# Refactoring Plan: project.py (1314 lines)

## Current Structure Analysis

The `project.py` file contains 21 functions organized into 3 logical groups:

### 1. Project Context Tools (Lines ~22-593)
- `get_project_context_tool()` / `handle_get_project_context()`
- `get_resume_context_tool()` / `handle_get_resume_context()`
- `get_project_structure_tool()` / `build_element_tree()` / `handle_get_project_structure()`
- `get_active_todos_tool()` / `handle_get_active_todos()`

### 2. Project CRUD Tools (Lines ~595-1067)
- `get_create_project_tool()` / `handle_create_project()`
- `get_list_projects_tool()` / `handle_list_projects()`
- `get_update_project_tool()` / `handle_update_project()`
- `get_identify_project_by_path_tool()` / `handle_identify_project_by_path()`

### 3. Cursor Rules & Workflow Tools (Lines ~1068-1314)
- `get_load_cursor_rules_tool()` / `handle_load_cursor_rules()`
- `get_enforce_workflow_tool()` / `handle_enforce_workflow()`

## Refactoring Strategy

Split into 3 separate modules:

### 1. `project_context.py` (~570 lines)
- Project context retrieval tools
- Resume context generation
- Project structure building
- Active todos listing

### 2. `project_crud.py` (~470 lines)
- Project creation
- Project listing
- Project updates
- Project identification

### 3. `project_workflow.py` (~270 lines)
- Cursor rules loading
- Workflow enforcement

## Implementation Steps

1. Create new module files
2. Move functions to appropriate modules
3. Update imports in `__init__.py`
4. Update imports in `server.py`
5. Test all functionality
6. Remove original `project.py`

## Dependencies

All modules will share:
- `SessionLocal` from `src.database.base`
- Service classes: `ProjectService`, `ElementService`, `FeatureService`, `TodoService`, `SessionService`
- `cache_service` from `src.mcp.services.cache`
- `broadcast_project_update` from `src.services.signalr_hub`
- Models: `User` from `src.database.models`

# Refactoring Plan: import_tools.py (626 lines)

## Current Structure Analysis

The `import_tools.py` file contains 8 functions organized into 4 logical groups:

### 1. File Structure Parsing (Lines ~18-193)
- `get_parse_file_structure_tool()` / `handle_parse_file_structure()`

### 2. GitHub Issues Import (Lines ~195-371)
- `get_import_github_issues_tool()` / `handle_import_github_issues()`

### 3. GitHub Milestones Import (Lines ~373-527)
- `get_import_github_milestones_tool()` / `handle_import_github_milestones()`

### 4. Codebase Analysis (Lines ~529-627)
- `get_analyze_codebase_tool()` / `handle_analyze_codebase()`

## Refactoring Strategy

Split into 4 separate modules:

### 1. `import_file_structure.py` (~195 lines)
- File structure parsing
- Directory traversal and element creation

### 2. `import_github_issues.py` (~180 lines)
- GitHub issues import
- Issue to todo conversion

### 3. `import_github_milestones.py` (~130 lines)
- GitHub milestones import
- Milestone to feature conversion

### 4. `import_codebase_analysis.py` (~75 lines)
- Codebase analysis
- Tech stack detection

## Implementation Steps

1. Create new module files
2. Move functions to appropriate modules
3. Fix `get_github_client()` calls to use `get_github_service().client`
4. Update imports in `__init__.py`
5. Update imports in `server.py`
6. Create re-export `import_tools.py` for backward compatibility
7. Test all functionality

## Dependencies

All modules will share:
- `SessionLocal` from `src.database.base`
- Service classes: `ProjectService`, `ElementService`, `TodoService`, `FeatureService`
- `cache_service` from `src.mcp.services.cache`
- Models: `Project`, `Todo` from `src.database.models`
- `get_github_service` from `src.mcp.tools.github_repository` (fixed)

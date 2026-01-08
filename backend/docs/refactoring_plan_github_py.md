# Refactoring Plan: github.py (1110 lines)

## Current Structure Analysis

The `github.py` file contains 33 functions organized into 5 logical groups:

### 1. Repository Management (Lines ~22-183)
- `get_github_service()` - Singleton service instance
- `get_connect_github_repo_tool()` / `handle_connect_github_repo()`
- `get_get_repo_info_tool()` / `handle_get_repo_info()`

### 2. Issues (Lines ~185-397)
- `get_link_element_to_issue_tool()` / `handle_link_element_to_issue()`
- `get_get_github_issue_tool()` / `handle_get_github_issue()`
- `get_create_github_issue_tool()` / `handle_create_github_issue()`

### 3. Pull Requests (Lines ~398-644)
- `get_link_todo_to_pr_tool()` / `handle_link_todo_to_pr()`
- `get_get_github_pr_tool()` / `handle_get_github_pr()`
- `get_create_github_pr_tool()` / `handle_create_github_pr()`

### 4. Branches (Lines ~30-1068)
- `get_get_branches_tool()` / `handle_get_branches()`
- `get_create_branch_for_feature_tool()` / `handle_create_branch_for_feature()`
- `get_get_active_branch_tool()` / `handle_get_active_branch()`
- `get_link_branch_to_feature_tool()` / `handle_link_branch_to_feature()`
- `get_get_feature_branches_tool()` / `handle_get_feature_branches()`
- `get_get_branch_status_tool()` / `handle_get_branch_status()`
- `get_get_commits_for_feature_tool()` / `handle_get_commits_for_feature()`

### 5. Commits (Lines ~1070-1110)
- `get_parse_commit_message_tool()` / `handle_parse_commit_message()`

## Refactoring Strategy

Split into 5 separate modules:

### 1. `github_repository.py` (~180 lines)
- Repository connection
- Repository info retrieval
- GitHub service singleton

### 2. `github_issues.py` (~200 lines)
- Link element to issue
- Get GitHub issue
- Create GitHub issue

### 3. `github_prs.py` (~250 lines)
- Link todo to PR
- Get GitHub PR
- Create GitHub PR

### 4. `github_branches.py` (~450 lines)
- Get branches
- Create branch for feature
- Get active branch
- Link branch to feature
- Get feature branches
- Get branch status
- Get commits for feature

### 5. `github_commits.py` (~100 lines)
- Parse commit message

## Implementation Steps

1. Create new module files
2. Move functions to appropriate modules
3. Update imports in `__init__.py`
4. Update imports in `server.py`
5. Create re-export `github.py` for backward compatibility
6. Test all functionality
7. Remove original `github.py` (or keep as re-export)

## Dependencies

All modules will share:
- `SessionLocal` from `src.database.base`
- Service classes: `GitHubService`, `ProjectService`, `FeatureService`, `ElementService`, `TodoService`
- `cache_service` from `src.mcp.services.cache`
- Models: `GitHubBranch` from `src.database.models`
- `Github` and `GithubException` from `github` package

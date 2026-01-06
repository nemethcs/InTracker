# InTracker - MCP Server Fejlesztési Todo Lista

## Fázis 1: MCP Server Setup

### 1.1. Projekt Inicializálás

- [ ] **Python projekt létrehozása**
  - [ ] requirements.txt inicializálás
  - [ ] pyproject.toml konfiguráció
  - [ ] .gitignore fájl
  - [ ] Virtual environment setup

- [ ] **Dependencies telepítése**
  - [ ] mcp (Model Context Protocol Python SDK)
  - [ ] SQLAlchemy (database access)
  - [ ] PyGithub (GitHub API)
  - [ ] python-dotenv (environment variables)
  - [ ] pydantic (validation)
  - [ ] redis (caching)
  - [ ] httpx (HTTP client)

- [ ] **Project struktúra**
  ```
  mcp-server/
  ├── src/
  │   ├── server.py
  │   ├── tools/
  │   │   ├── project.py
  │   │   ├── feature.py
  │   │   ├── todo.py
  │   │   ├── session.py
  │   │   ├── document.py
  │   │   └── github.py
  │   ├── resources/
  │   │   ├── project_resources.py
  │   │   ├── feature_resources.py
  │   │   └── document_resources.py
  │   ├── services/
  │   │   ├── database.py
  │   │   ├── cache.py
  │   │   └── github.py
  │   └── utils/
  ├── tests/
  ├── requirements.txt
  └── Dockerfile
  ```

### 1.2. MCP Server Konfiguráció

- [ ] **Server inicializálás**
  - [ ] MCPServer instance (Python SDK)
  - [ ] Transport setup (stdio vagy HTTP)
  - [ ] Error handling

- [ ] **Environment Configuration**
  - [ ] DATABASE_URL
  - [ ] REDIS_URL
  - [ ] GITHUB_TOKEN
  - [ ] MCP_API_KEY (opcionális)

- [ ] **Database Connection**
  - [ ] SQLAlchemy setup
  - [ ] Connection pooling
  - [ ] Error handling

## Fázis 2: MCP Tools - Projekt Lekérdezés

### 2.1. Project Context Tools

- [ ] **mcp_get_project_context**
  - [ ] Input: projectId
  - [ ] Output: Full project context
  - [ ] Include: structure, features, todos, resume context
  - [ ] Caching: Redis (5 min TTL)
  - [ ] Error handling

- [ ] **mcp_get_resume_context**
  - [ ] Input: projectId
  - [ ] Output: Resume context package
  - [ ] Include: Last, Now, Blockers, Constraints
  - [ ] Caching: Redis (1 min TTL)
  - [ ] Error handling

- [ ] **mcp_get_project_structure**
  - [ ] Input: projectId
  - [ ] Output: Hierarchical element tree
  - [ ] Recursive structure
  - [ ] Caching: Redis (5 min TTL)

- [ ] **mcp_get_active_todos**
  - [ ] Input: projectId, filters (opcionális)
  - [ ] Output: Active todos list
  - [ ] Filter by status, feature, user
  - [ ] Caching: Redis (2 min TTL)

## Fázis 3: MCP Tools - Feature Kezelés

### 3.1. Feature CRUD Tools

- [ ] **mcp_create_feature**
  - [ ] Input: projectId, name, description, elementIds (opcionális)
  - [ ] Output: Created feature
  - [ ] Auto-calculate progress
  - [ ] Link elements if provided
  - [ ] Cache invalidation

- [ ] **mcp_get_feature**
  - [ ] Input: featureId
  - [ ] Output: Feature with todos and elements
  - [ ] Include progress
  - [ ] Caching: Redis (2 min TTL)

- [ ] **mcp_list_features**
  - [ ] Input: projectId, filters (status, assigned_to)
  - [ ] Output: Features list
  - [ ] Include progress
  - [ ] Pagination support
  - [ ] Caching: Redis (2 min TTL)

- [ ] **mcp_update_feature_status**
  - [ ] Input: featureId, status
  - [ ] Output: Updated feature
  - [ ] Progress recalculation
  - [ ] Cache invalidation

- [ ] **mcp_get_feature_todos**
  - [ ] Input: featureId
  - [ ] Output: Todos for feature
  - [ ] Include status, assignment
  - [ ] Caching: Redis (2 min TTL)

- [ ] **mcp_get_feature_elements**
  - [ ] Input: featureId
  - [ ] Output: Elements for feature
  - [ ] Caching: Redis (5 min TTL)

- [ ] **mcp_link_element_to_feature**
  - [ ] Input: featureId, elementId
  - [ ] Output: Success
  - [ ] Create feature_elements record
  - [ ] Cache invalidation

## Fázis 4: MCP Tools - Todo Kezelés

### 4.1. Todo CRUD Tools

- [ ] **mcp_create_todo**
  - [ ] Input: elementId, title, description, featureId (opcionális), estimated_effort
  - [ ] Output: Created todo
  - [ ] Link to feature if provided
  - [ ] Update feature total_todos
  - [ ] Cache invalidation

- [ ] **mcp_update_todo_status**
  - [ ] Input: todoId, status, expectedVersion (opcionális)
  - [ ] Output: Updated todo
  - [ ] Optimistic locking (version check)
  - [ ] Conflict error handling
  - [ ] Update feature progress
  - [ ] Cache invalidation

- [ ] **mcp_list_todos**
  - [ ] Input: projectId, filters (status, featureId, assigned_to)
  - [ ] Output: Todos list
  - [ ] Pagination support
  - [ ] Caching: Redis (2 min TTL)

- [ ] **mcp_assign_todo**
  - [ ] Input: todoId, userId (opcionális - auto-assign if null)
  - [ ] Output: Updated todo
  - [ ] Load balancing if userId null
  - [ ] Cache invalidation

- [ ] **mcp_get_my_todos**
  - [ ] Input: projectId, userId (from context)
  - [ ] Output: User's assigned todos
  - [ ] Filter by status
  - [ ] Caching: Redis (1 min TTL)

## Fázis 5: MCP Tools - Session Kezelés

### 5.1. Session Tools

- [ ] **mcp_start_session**
  - [ ] Input: projectId, goal, featureIds (opcionális)
  - [ ] Output: Created session
  - [ ] Auto-assign user (from context)
  - [ ] Link features if provided
  - [ ] Cache invalidation

- [ ] **mcp_update_session**
  - [ ] Input: sessionId, updates (completed_todos, features_completed, notes)
  - [ ] Output: Updated session
  - [ ] Update feature progress
  - [ ] Cache invalidation

- [ ] **mcp_end_session**
  - [ ] Input: sessionId
  - [ ] Output: Session summary
  - [ ] Generate summary (AI vagy template)
  - [ ] Update resume context
  - [ ] Update project last_session_at
  - [ ] Cache invalidation

- [ ] **mcp_get_session**
  - [ ] Input: sessionId
  - [ ] Output: Session details
  - [ ] Include completed todos, features
  - [ ] Caching: Redis (5 min TTL)

## Fázis 6: MCP Tools - Dokumentáció

### 6.1. Document Tools

- [ ] **mcp_read_document**
  - [ ] Input: documentId
  - [ ] Output: Document content
  - [ ] Markdown parsing
  - [ ] Caching: Redis (10 min TTL)

- [ ] **mcp_search_documents**
  - [ ] Input: projectId, query
  - [ ] Output: Matching documents
  - [ ] Full-text search
  - [ ] Relevance ranking

- [ ] **mcp_get_documents_by_type**
  - [ ] Input: projectId, type
  - [ ] Output: Documents by type
  - [ ] Types: architecture, adr, domain, constraints, runbook, ai_instructions
  - [ ] Caching: Redis (10 min TTL)

- [ ] **mcp_create_document**
  - [ ] Input: projectId, type, title, content, elementId (opcionális)
  - [ ] Output: Created document
  - [ ] Markdown validation
  - [ ] Cache invalidation

- [ ] **mcp_update_document**
  - [ ] Input: documentId, content
  - [ ] Output: Updated document
  - [ ] Version increment
  - [ ] Cache invalidation

## Fázis 7: MCP Tools - GitHub Integráció

### 7.1. Repository Tools

- [ ] **mcp_connect_github_repo**
  - [ ] Input: projectId, repoUrl
  - [ ] Output: Repo connection status
  - [ ] Validate repo access
  - [ ] Store repo info

- [ ] **mcp_get_repo_info**
  - [ ] Input: projectId
  - [ ] Output: Repo information
  - [ ] Include: owner, name, default branch

### 7.2. Branch Tools

- [ ] **mcp_create_branch_for_feature**
  - [ ] Input: featureId, baseBranch (opcionális)
  - [ ] Output: Created branch
  - [ ] Generate branch name (feature/{feature-slug})
  - [ ] GitHub API: create branch
  - [ ] Link branch to feature
  - [ ] Cache invalidation

- [ ] **mcp_get_active_branch**
  - [ ] Input: projectId
  - [ ] Output: Active branch (from working directory)
  - [ ] GitHub API: get current branch
  - [ ] Link to feature if exists

- [ ] **mcp_link_branch_to_feature**
  - [ ] Input: featureId, branchName
  - [ ] Output: Success
  - [ ] Create github_branches record
  - [ ] Cache invalidation

- [ ] **mcp_get_feature_branches**
  - [ ] Input: featureId
  - [ ] Output: Branches for feature
  - [ ] Include status (ahead, behind, conflicts)

- [ ] **mcp_get_branch_status**
  - [ ] Input: branchName, projectId
  - [ ] Output: Branch status
  - [ ] GitHub API: compare branches
  - [ ] Calculate ahead/behind
  - [ ] Check conflicts

### 7.3. Commit Tools

- [ ] **mcp_get_commits_for_feature**
  - [ ] Input: featureId
  - [ ] Output: Commits for feature
  - [ ] Parse commit messages for feature ID
  - [ ] GitHub API: list commits

- [ ] **mcp_parse_commit_message**
  - [ ] Input: commitMessage
  - [ ] Output: Parsed metadata
  - [ ] Extract: type, scope, description, featureId
  - [ ] Format: "feat(scope): description [feature:id]"

### 7.4. Issue és PR Tools

- [ ] **mcp_link_element_to_issue**
  - [ ] Input: elementId, issueNumber
  - [ ] Output: Success
  - [ ] Create github_sync record
  - [ ] GitHub API: get issue
  - [ ] Cache invalidation

- [ ] **mcp_link_todo_to_pr**
  - [ ] Input: todoId, prNumber
  - [ ] Output: Success
  - [ ] Create github_sync record
  - [ ] GitHub API: get PR
  - [ ] Cache invalidation

- [ ] **mcp_get_github_issue**
  - [ ] Input: repo, issueNumber
  - [ ] Output: Issue details
  - [ ] GitHub API: get issue
  - [ ] Caching: Redis (5 min TTL)

- [ ] **mcp_create_github_pr**
  - [ ] Input: branchName, title, body, baseBranch
  - [ ] Output: Created PR
  - [ ] GitHub API: create PR
  - [ ] Link to todos/features
  - [ ] Cache invalidation

## Fázis 8: MCP Resources

### 8.1. Project Resources

- [ ] **project://{projectId}/context**
  - [ ] Full project context
  - [ ] Include: structure, features, todos, resume context
  - [ ] Caching: Redis (5 min TTL)
  - [ ] Auto-invalidation

- [ ] **project://{projectId}/resume**
  - [ ] Resume context package
  - [ ] Include: Last, Now, Blockers, Constraints
  - [ ] Caching: Redis (1 min TTL)
  - [ ] Auto-invalidation

- [ ] **project://{projectId}/structure**
  - [ ] Project structure tree
  - [ ] Hierarchical elements
  - [ ] Caching: Redis (5 min TTL)

- [ ] **project://{projectId}/features**
  - [ ] Active features
  - [ ] Include progress
  - [ ] Caching: Redis (2 min TTL)

- [ ] **project://{projectId}/active-todos**
  - [ ] Active todos
  - [ ] Filtered by status
  - [ ] Caching: Redis (2 min TTL)

- [ ] **project://{projectId}/documents**
  - [ ] All documents
  - [ ] Caching: Redis (10 min TTL)

### 8.2. Feature Resources

- [ ] **feature://{featureId}**
  - [ ] Feature with todos
  - [ ] Include elements
  - [ ] Include progress
  - [ ] Caching: Redis (2 min TTL)

### 8.3. Document Resources

- [ ] **document://{documentId}**
  - [ ] Document content
  - [ ] Markdown format
  - [ ] Caching: Redis (10 min TTL)

### 8.4. Session Resources

- [ ] **session://{sessionId}**
  - [ ] Session details
  - [ ] Include summary
  - [ ] Caching: Redis (5 min TTL)

### 8.5. User Resources (Multi-User)

- [ ] **user://{userId}/project/{projectId}/context**
  - [ ] User-scoped project context
  - [ ] Only assigned todos/features
  - [ ] Caching: Redis (5 min TTL)

- [ ] **user://{userId}/my-todos**
  - [ ] User's assigned todos
  - [ ] Filter by project (opcionális)
  - [ ] Caching: Redis (1 min TTL)

## Fázis 9: Caching és Optimalizálás

### 9.1. Redis Integration

- [ ] **Cache Service**
  - [ ] Redis client setup
  - [ ] Connection handling
  - [ ] Error handling

- [ ] **Cache Helpers**
  - [ ] getCache()
  - [ ] setCache()
  - [ ] deleteCache()
  - [ ] clearCacheByPattern()

### 9.2. Cache Strategies

- [ ] **TTL Configuration**
  - [ ] Project context: 5 min
  - [ ] Resume context: 1 min
  - [ ] Features: 2 min
  - [ ] Todos: 2 min
  - [ ] Documents: 10 min

- [ ] **Cache Invalidation**
  - [ ] On todo update → invalidate feature cache
  - [ ] On feature update → invalidate project cache
  - [ ] On session end → invalidate resume context
  - [ ] On assignment → invalidate user cache

### 9.3. Token Optimalizálás

- [ ] **Lazy Loading**
  - [ ] Only load requested resources
  - [ ] Don't auto-load all resources

- [ ] **Structured Data**
  - [ ] Return IDs instead of full objects
  - [ ] Minimize response size
  - [ ] Compress large responses

## Fázis 10: Error Handling és Validation

### 10.1. Error Handling

- [ ] **Error Types**
  - [ ] NotFoundError
  - [ ] UnauthorizedError
  - [ ] ForbiddenError
  - [ ] ConflictError (optimistic locking)
  - [ ] ValidationError

- [ ] **Error Responses**
  - [ ] Structured error format
  - [ ] Error codes
  - [ ] Error messages

### 10.2. Input Validation

- [ ] **Zod Schemas**
  - [ ] Tool input validation
  - [ ] Resource parameter validation
  - [ ] Type safety

- [ ] **Validation Helpers**
  - [ ] validateProjectId()
  - [ ] validateFeatureId()
  - [ ] validateTodoId()
  - [ ] validateUserId()

## Fázis 11: Testing

### 11.1. Unit Tests

- [ ] **Tool Tests**
  - [ ] Project tools tests
  - [ ] Feature tools tests
  - [ ] Todo tools tests
  - [ ] Session tools tests
  - [ ] GitHub tools tests

- [ ] **Service Tests**
  - [ ] Database service tests
  - [ ] Cache service tests
  - [ ] GitHub service tests

### 11.2. Integration Tests

- [ ] **MCP Protocol Tests**
  - [ ] Tool execution tests
  - [ ] Resource access tests
  - [ ] Error handling tests

- [ ] **Database Integration Tests**
  - [ ] CRUD operations
  - [ ] Transaction tests
  - [ ] Cache integration

### 11.3. E2E Tests

- [ ] **Workflow Tests**
  - [ ] Create project → Create feature → Create todos
  - [ ] Start session → Update todos → End session
  - [ ] GitHub branch creation → PR creation

## Fázis 12: Monitoring és Logging

### 12.1. Logging

- [ ] **Structured Logging**
  - [ ] Log all tool calls
  - [ ] Log resource access
  - [ ] Log errors
  - [ ] Log performance metrics

- [ ] **Log Context**
  - [ ] Project ID
  - [ ] User ID (if available)
  - [ ] Tool/Resource name
  - [ ] Timestamp

### 12.2. Metrics

- [ ] **Tool Usage Metrics**
  - [ ] Tool call count
  - [ ] Tool execution time
  - [ ] Tool error rate

- [ ] **Resource Access Metrics**
  - [ ] Resource access count
  - [ ] Cache hit rate
  - [ ] Resource load time

- [ ] **Token Usage Tracking**
  - [ ] Track response sizes
  - [ ] Estimate token usage
  - [ ] Alert on high usage

## Fázis 13: Security

### 13.1. Authentication

- [ ] **API Key Authentication**
  - [ ] MCP_API_KEY validation
  - [ ] Key rotation support

- [ ] **User Context**
  - [ ] Extract user from context
  - [ ] Validate user permissions
  - [ ] Project access checks

### 13.2. Authorization

- [ ] **Project Access Checks**
  - [ ] Check user has access to project
  - [ ] Check user role (owner/editor/viewer)
  - [ ] Enforce permissions

- [ ] **Resource Access Checks**
  - [ ] Validate resource ownership
  - [ ] Check user can access resource

---

## Prioritások

**MVP (Minimum Viable Product):**
1. MCP Server setup
2. Project context tools
3. Feature tools (CRUD)
4. Todo tools (CRUD)
5. Basic resources

**Fázis 1 után:**
6. Session tools
7. Document tools
8. GitHub integration tools
9. Caching implementation
10. Error handling

**Production előtt:**
11. Token optimization
12. Testing
13. Monitoring
14. Security hardening

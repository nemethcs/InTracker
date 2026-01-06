# InTracker - Backend Fejlesztési Todo Lista

## Fázis 1: Projekt Setup és Alapok

### 1.1. Projekt Inicializálás

- [x] **Python projekt létrehozása**
  - [x] requirements.txt inicializálás
  - [x] pyproject.toml konfiguráció
  - [x] .gitignore fájl
  - [x] Virtual environment setup

- [x] **Dependencies telepítése**
  - [x] FastAPI (web framework)
  - [x] Uvicorn (ASGI server)
  - [x] SQLAlchemy (ORM)
  - [x] Alembic (migrations)
  - [x] Pydantic (validation)
  - [x] python-jose (JWT)
  - [x] passlib[bcrypt] (password hashing)
  - [x] PyGithub (GitHub API)
  - [x] python-dotenv (environment variables)
  - [x] psycopg2-binary (PostgreSQL driver)
  - [x] redis (Redis client)

- [x] **Project struktúra**
  ```
  backend/
  ├── src/
  │   ├── api/
  │   │   ├── routes/
  │   │   ├── controllers/
  │   │   ├── middleware/
  │   │   └── schemas/
  │   ├── services/
  │   ├── database/
  │   │   ├── models.py
  │   │   └── base.py
  │   ├── utils/
  │   └── main.py
  ├── alembic/
  │   └── versions/
  ├── tests/
  ├── requirements.txt
  └── Dockerfile
  ```

### 1.2. Environment Configuration

- [x] **.env fájl setup**
  - [x] DATABASE_URL
  - [x] JWT_SECRET
  - [x] JWT_REFRESH_SECRET
  - [x] GITHUB_TOKEN
  - [x] REDIS_URL
  - [x] PORT
  - [x] NODE_ENV

- [x] **.env.example fájl**
  - [x] Minden változó dokumentálva
  - [x] Default értékek

- [x] **Config module**
  - [x] config.py fájl (Pydantic Settings)
  - [x] Environment variable validation (Pydantic)
  - [x] Type-safe config access

## Fázis 2: Database Integration

### 2.1. SQLAlchemy Setup

- [x] **SQLAlchemy models**
  - [x] Base class definíció
  - [x] Engine és Session konfiguráció
  - [x] Model definíciók (minden tábla - lásd todos-database.md)

- [x] **Database connection**
  - [x] SQLAlchemy engine
  - [x] Session factory
  - [x] Connection pooling konfiguráció
  - [x] Error handling

- [ ] **Alembic migrations**
  - [ ] Alembic inicializálás
  - [ ] Initial migration
  - [ ] Migration script
  - [ ] Migration rollback script

### 2.2. Database Services

- [x] **Auth Service**
  - [x] hash_password()
  - [x] verify_password()
  - [x] create_access_token()
  - [x] create_refresh_token()
  - [x] verify_token()
  - [x] register()
  - [x] login()
  - [x] refresh_access_token()

- [ ] **User Service**
  - [ ] getUserById()
  - [ ] getUserByEmail()
  - [ ] updateUser()
  - [ ] deleteUser()

- [ ] **Project Service**
  - [ ] createProject()
  - [ ] getProjectById()
  - [ ] getProjectsByUserId()
  - [ ] updateProject()
  - [ ] deleteProject()
  - [ ] getProjectWithContext()

- [ ] **Feature Service**
  - [ ] createFeature()
  - [ ] getFeatureById()
  - [ ] getFeaturesByProjectId()
  - [ ] updateFeature()
  - [ ] deleteFeature()
  - [ ] calculateFeatureProgress()

- [ ] **Todo Service**
  - [ ] createTodo()
  - [ ] getTodoById()
  - [ ] getTodosByElementId()
  - [ ] getTodosByFeatureId()
  - [ ] getTodosByUserId() // Assigned todos
  - [ ] updateTodo()
  - [ ] deleteTodo()
  - [ ] updateTodoStatus() // With version check

- [ ] **Session Service**
  - [ ] createSession()
  - [ ] getSessionById()
  - [ ] getSessionsByProjectId()
  - [ ] getSessionsByUserId()
  - [ ] updateSession()
  - [ ] endSession()
  - [ ] generateSessionSummary()

## Fázis 3: Authentication és Authorization

### 3.1. Authentication

- [x] **JWT Service**
  - [x] create_access_token()
  - [x] create_refresh_token()
  - [x] verify_token()
  - [x] Token payload handling

- [x] **Auth Controller**
  - [x] POST /auth/register
  - [x] POST /auth/login
  - [x] POST /auth/refresh
  - [x] GET /auth/me

- [x] **Password hashing**
  - [x] hash_password() (passlib bcrypt)
  - [x] verify_password()
  - [ ] Password strength validation

- [x] **Auth Middleware**
  - [x] get_current_user() (FastAPI dependency)
  - [x] get_optional_user() (optional auth)
  - [x] HTTPBearer security

### 3.2. Authorization

- [ ] **Role-based Access Control**
  - [ ] requireProjectRole() middleware
  - [ ] checkProjectAccess() utility
  - [ ] hasPermission() function

- [ ] **Project Access Middleware**
  - [ ] requireProjectAccess()
  - [ ] requireProjectOwner()
  - [ ] requireProjectEditor()

- [ ] **Resource Ownership**
  - [ ] checkTodoOwnership()
  - [ ] checkFeatureOwnership()
  - [ ] checkElementOwnership()

## Fázis 4: REST API Endpoints

### 4.1. Users API

- [ ] **GET /api/users**
  - [ ] List users (admin only)
  - [ ] Pagination
  - [ ] Filtering

- [ ] **GET /api/users/{id}**
  - [ ] Get user by ID
  - [ ] Authorization check

- [ ] **PUT /api/users/:id**
  - [ ] Update user
  - [ ] Self-update or admin only

- [ ] **DELETE /api/users/:id**
  - [ ] Delete user (admin only)
  - [ ] Soft delete option

### 4.2. Projects API

- [ ] **GET /api/projects**
  - [ ] List user's projects
  - [ ] Filter by status
  - [ ] Pagination

- [ ] **GET /api/projects/:id**
  - [ ] Get project with full context
  - [ ] Include features, todos, elements
  - [ ] Authorization check

- [ ] **POST /api/projects**
  - [ ] Create project
  - [ ] Auto-assign owner role
  - [ ] Validation

- [ ] **PUT /api/projects/:id**
  - [ ] Update project
  - [ ] Role check (editor/owner)

- [ ] **DELETE /api/projects/:id**
  - [ ] Delete project
  - [ ] Owner only
  - [ ] Cascade delete

- [ ] **GET /api/projects/:id/resume**
  - [ ] Get resume context
  - [ ] Cached response

- [ ] **PUT /api/projects/:id/resume**
  - [ ] Update resume context
  - [ ] Editor/owner only

- [ ] **GET /api/projects/:id/team-dashboard**
  - [ ] Team context
  - [ ] Active users
  - [ ] Progress metrics

### 4.3. Features API

- [ ] **GET /api/projects/:id/features**
  - [ ] List features for project
  - [ ] Filter by status
  - [ ] Include progress

- [ ] **GET /api/features/{id}**
  - [ ] Get feature with todos
  - [ ] Include elements

- [ ] **POST /api/features**
  - [ ] Create feature
  - [ ] Auto-calculate progress
  - [ ] Validation

- [ ] **PUT /api/features/:id**
  - [ ] Update feature
  - [ ] Progress recalculation

- [ ] **DELETE /api/features/:id**
  - [ ] Delete feature
  - [ ] Cascade todos handling

- [ ] **GET /api/features/:id/todos**
  - [ ] Get todos for feature

- [ ] **GET /api/features/:id/elements**
  - [ ] Get elements for feature

- [ ] **POST /api/features/:id/assign**
  - [ ] Assign feature to user
  - [ ] Authorization check

### 4.4. Todos API

- [ ] **GET /api/todos**
  - [ ] List todos
  - [ ] Filter by project, feature, user, status
  - [ ] Pagination

- [ ] **GET /api/todos/:id**
  - [ ] Get todo by ID
  - [ ] Include element, feature

- [ ] **POST /api/todos**
  - [ ] Create todo
  - [ ] Link to feature (optional)
  - [ ] Validation

- [ ] **PUT /api/todos/:id**
  - [ ] Update todo
  - [ ] Optimistic locking (version check)
  - [ ] Conflict handling

- [ ] **DELETE /api/todos/:id**
  - [ ] Delete todo
  - [ ] Authorization check

- [ ] **POST /api/todos/:id/assign**
  - [ ] Assign todo to user
  - [ ] Load balancing option

- [ ] **PUT /api/todos/:id/status**
  - [ ] Update todo status
  - [ ] Feature progress update
  - [ ] Version check

### 4.5. Elements API

- [ ] **GET /api/projects/:id/elements**
  - [ ] Get project elements tree
  - [ ] Hierarchical structure

- [ ] **GET /api/elements/:id**
  - [ ] Get element with todos
  - [ ] Include dependencies

- [ ] **POST /api/elements**
  - [ ] Create element
  - [ ] Parent relationship

- [ ] **PUT /api/elements/:id**
  - [ ] Update element
  - [ ] Status update

- [ ] **DELETE /api/elements/:id**
  - [ ] Delete element
  - [ ] Cascade handling

- [ ] **POST /api/elements/:id/dependencies**
  - [ ] Add dependency
  - [ ] Circular dependency check

### 4.6. Sessions API

- [ ] **GET /api/projects/:id/sessions**
  - [ ] List sessions for project
  - [ ] Filter by user
  - [ ] Pagination

- [ ] **GET /api/sessions/:id**
  - [ ] Get session details
  - [ ] Include summary

- [ ] **POST /api/sessions**
  - [ ] Start session
  - [ ] Auto-assign user
  - [ ] Feature IDs (optional)

- [ ] **PUT /api/sessions/:id**
  - [ ] Update session
  - [ ] Add completed todos
  - [ ] Add notes

- [ ] **POST /api/sessions/:id/end**
  - [ ] End session
  - [ ] Generate summary
  - [ ] Update resume context

### 4.7. Documents API

- [ ] **GET /api/projects/:id/documents**
  - [ ] List documents
  - [ ] Filter by type
  - [ ] Search

- [ ] **GET /api/documents/:id**
  - [ ] Get document
  - [ ] Markdown rendering

- [ ] **POST /api/documents**
  - [ ] Create document
  - [ ] Validation

- [ ] **PUT /api/documents/:id**
  - [ ] Update document
  - [ ] Version increment

- [ ] **DELETE /api/documents/:id**
  - [ ] Delete document

### 4.8. GitHub Integration API

- [ ] **POST /api/projects/:id/github/connect**
  - [ ] Connect GitHub repo
  - [ ] Validate repo access
  - [ ] Store repo info

- [ ] **GET /api/projects/:id/github/repo**
  - [ ] Get repo info

- [ ] **GET /api/projects/:id/branches**
  - [ ] List branches
  - [ ] Include feature links

- [ ] **POST /api/branches**
  - [ ] Create branch for feature
  - [ ] GitHub API integration

- [ ] **GET /api/branches/:id**
  - [ ] Get branch details
  - [ ] Include status

- [ ] **GET /api/features/:id/branches**
  - [ ] Get branches for feature

- [ ] **POST /api/github/webhook**
  - [ ] GitHub webhook handler
  - [ ] PR events
  - [ ] Issue events
  - [ ] Branch events

## Fázis 5: Caching (Redis)

### 5.1. Redis Setup

- [ ] **Redis Client**
  - [ ] Redis connection
  - [ ] Error handling
  - [ ] Reconnection logic

- [ ] **Cache Service**
  - [ ] getCache()
  - [ ] setCache()
  - [ ] deleteCache()
  - [ ] clearCacheByPattern()

### 5.2. Cache Strategies

- [ ] **Project Context Cache**
  - [ ] Key: `project:{projectId}:context`
  - [ ] TTL: 5 minutes
  - [ ] Invalidation on update

- [ ] **Resume Context Cache**
  - [ ] Key: `project:{projectId}:resume`
  - [ ] TTL: 1 minute
  - [ ] Invalidation on session end

- [ ] **User Context Cache**
  - [ ] Key: `user:{userId}:project:{projectId}`
  - [ ] TTL: 5 minutes
  - [ ] Invalidation on assignment change

- [ ] **Feature Cache**
  - [ ] Key: `feature:{featureId}`
  - [ ] TTL: 2 minutes
  - [ ] Invalidation on todo update

- [ ] **Document Cache**
  - [ ] Key: `document:{documentId}`
  - [ ] TTL: 10 minutes
  - [ ] Invalidation on update

## Fázis 6: Real-time Sync (SignalR)

### 6.1. SignalR Setup

- [ ] **Azure SignalR Service**
  - [ ] Connection string configuration
  - [ ] Hub setup

- [ ] **SignalR Hub**
  - [ ] Connection handling
  - [ ] User groups (by project)
  - [ ] Disconnect handling

### 6.2. Real-time Events

- [ ] **Todo Updates**
  - [ ] Broadcast todo status change
  - [ ] Broadcast todo assignment
  - [ ] Conflict warnings

- [ ] **Feature Updates**
  - [ ] Broadcast feature progress
  - [ ] Broadcast feature assignment

- [ ] **User Activity**
  - [ ] "User X is working on feature Y"
  - [ ] "User X started session"
  - [ ] "User X completed todo Z"

- [ ] **Project Updates**
  - [ ] Broadcast project changes
  - [ ] Resume context updates

## Fázis 7: Error Handling és Validation

### 7.1. Error Handling

- [ ] **Error Middleware**
  - [ ] Global error handler
  - [ ] Error logging
  - [ ] Error response formatting

- [ ] **Custom Errors**
  - [ ] NotFoundError
  - [ ] UnauthorizedError
  - [ ] ForbiddenError
  - [ ] ConflictError (optimistic locking)
  - [ ] ValidationError

- [ ] **Error Logging**
  - [ ] Application Insights integration
  - [ ] Error context (user, project, etc.)

### 7.2. Validation

- [ ] **Zod Schemas**
  - [ ] User validation
  - [ ] Project validation
  - [ ] Feature validation
  - [ ] Todo validation
  - [ ] Session validation

- [ ] **Validation Middleware**
  - [ ] Request body validation
  - [ ] Query parameter validation
  - [ ] Path parameter validation

## Fázis 8: Testing

### 8.1. Unit Tests

- [ ] **Service Tests**
  - [ ] User Service tests
  - [ ] Project Service tests
  - [ ] Feature Service tests
  - [ ] Todo Service tests

- [ ] **Utility Tests**
  - [ ] JWT Service tests
  - [ ] Password hashing tests
  - [ ] Validation tests

### 8.2. Integration Tests

- [ ] **API Tests**
  - [ ] Auth endpoints
  - [ ] Project endpoints
  - [ ] Feature endpoints
  - [ ] Todo endpoints

- [ ] **Database Tests**
  - [ ] Transaction tests
  - [ ] Cascade delete tests
  - [ ] Constraint tests

### 8.3. E2E Tests

- [ ] **User Flow Tests**
  - [ ] Register → Login → Create Project
  - [ ] Create Feature → Create Todos → Update Status
  - [ ] Start Session → Work → End Session

## Fázis 9: Security

### 9.1. Security Middleware

- [ ] **Helmet.js**
  - [ ] Security headers
  - [ ] XSS protection
  - [ ] Content Security Policy

- [ ] **Rate Limiting**
  - [ ] API rate limits
  - [ ] Auth endpoint limits
  - [ ] IP-based limiting

- [ ] **CORS**
  - [ ] CORS configuration
  - [ ] Allowed origins
  - [ ] Credentials handling

### 9.2. Input Sanitization

- [ ] **SQL Injection Prevention**
  - [ ] Prisma parameterized queries
  - [ ] Input validation

- [ ] **XSS Prevention**
  - [ ] Output encoding
  - [ ] Markdown sanitization

## Fázis 10: Monitoring és Logging

### 10.1. Application Insights

- [ ] **Telemetry Setup**
  - [ ] Application Insights SDK
  - [ ] Custom metrics
  - [ ] Custom events

- [ ] **Metrics**
  - [ ] Request count
  - [ ] Response time
  - [ ] Error rate
  - [ ] Token usage (MCP)
  - [ ] Cache hit rate

- [ ] **Alerts**
  - [ ] High error rate
  - [ ] Slow response time
  - [ ] Database connection issues

### 10.2. Logging

- [ ] **Structured Logging**
  - [ ] Winston or Pino
  - [ ] Log levels
  - [ ] Log format (JSON)

- [ ] **Log Context**
  - [ ] User ID
  - [ ] Project ID
  - [ ] Request ID
  - [ ] Timestamp

---

## Prioritások

**MVP (Minimum Viable Product):**
1. Projekt setup
2. Database integration (Prisma)
3. Authentication (JWT)
4. Basic API (Projects, Features, Todos)
5. Error handling

**Fázis 1 után:**
6. Authorization (RBAC)
7. Caching (Redis)
8. Real-time sync (SignalR)
9. GitHub integration
10. Testing

**Production előtt:**
11. Security hardening
12. Monitoring setup
13. Performance optimization
14. Documentation

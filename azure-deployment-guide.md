# InTracker - Azure Deployment Guide

## 1. Áttekintés

Ez a dokumentum az InTracker Azure-beli telepítését és működtetését részletezi, figyelembe véve:
- **10-15 projekt** párhuzamos kezelése
- **Több felhasználó** egyidejű munkavégzése
- **Különböző méretű projektek** (kicsi → nagy)
- **Fokozatos bevezetés**: DB + Backend + MCP → majd Frontend

---

## 2. Azure Szolgáltatások és Architektúra

### 2.1. Ajánlott Azure Szolgáltatások

```
┌─────────────────────────────────────────────────────────────┐
│                    Azure Cloud Architecture                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Frontend (később)                                    │  │
│  │  - Azure Static Web Apps                              │  │
│  │  - vagy Azure App Service (React)                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                         │                                   │
│                         ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Backend API                                         │  │
│  │  - Azure App Service (Linux)                         │  │
│  │  - vagy Azure Container Apps                         │  │
│  │  - Auto-scaling enabled                              │  │
│  └──────────────────────────────────────────────────────┘  │
│         │                    │                              │
│         ↓                    ↓                              │
│  ┌──────────────┐    ┌──────────────┐                     │
│  │  MCP Server  │    │  Database    │                     │
│  │  (Container) │    │  PostgreSQL  │                     │
│  └──────────────┘    └──────────────┘                     │
│         │                    │                              │
│         └────────┬───────────┘                              │
│                  ↓                                          │
│         ┌──────────────┐                                   │
│         │  Azure Cache │                                   │
│         │  for Redis   │                                   │
│         └──────────────┘                                   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Supporting Services                                 │  │
│  │  - Azure Key Vault (secrets)                        │  │
│  │  - Azure Application Insights (monitoring)         │  │
│  │  - Azure Blob Storage (ha kell file storage)        │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2. Szolgáltatások részletesen

#### 2.2.1. Database: Azure Database for PostgreSQL

**Miért PostgreSQL:**
- ✅ JSONB támogatás (metadata, resume_context)
- ✅ Array típusok (tags, feature_ids)
- ✅ Skálázhatóság (10-15 projekt, több felhasználó)
- ✅ Connection pooling beépítve
- ✅ Backup automatikus
- ✅ High availability opció

**Konfiguráció javaslat:**
```
Tier: General Purpose
vCores: 2-4 (kezdéshez 2, skálázás 4-re)
Storage: 128 GB (auto-grow enabled)
Backup: 7 nap retention
High Availability: Enabled (production)
```

**Költség becslés:**
- Basic tier: ~$50-100/hó (fejlesztés)
- General Purpose: ~$200-400/hó (production, 2-4 vCores)

#### 2.2.2. Backend: Azure App Service (Linux)

**Miért App Service:**
- ✅ Egyszerű deployment (Git, Docker, vagy ZIP)
- ✅ Auto-scaling beépítve
- ✅ Built-in load balancing
- ✅ SSL certificate automatikus
- ✅ Deployment slots (staging/production)
- ✅ Integráció Application Insights-szal

**Konfiguráció javaslat:**
```
Plan: App Service Plan (Linux)
Tier: Standard S1 (kezdés) → Premium P1V2 (production)
Instances: 1-3 (auto-scale based on CPU/memory)
Runtime: Python 3.11+
```

**Alternatíva: Azure Container Apps**
- Ha Docker containerizálni akarjuk
- Jobb izoláció
- Finomabb skálázás
- Költséghatékonyabb (pay-per-use)

**Költség becslés:**
- Standard S1: ~$55/hó (1 instance)
- Premium P1V2: ~$146/hó (1 instance)
- Container Apps: ~$30-80/hó (használat alapján)

#### 2.2.3. MCP Server: Azure Container Apps

**Miért Container Apps:**
- ✅ Könnyű deployment
- ✅ Auto-scaling
- ✅ Költséghatékony (pay-per-use)
- ✅ Jó izoláció
- ✅ Könnyű integráció Backend-del

**Konfiguráció:**
```
Container: Python 3.11 (MCP Server)
CPU: 0.5-1 vCPU
Memory: 1-2 GB
Min replicas: 1
Max replicas: 3 (auto-scale)
```

**Alternatíva: Ugyanaz az App Service-ben**
- Ha egyszerűbb architektúrát akarunk
- Backend és MCP együtt

#### 2.2.4. Real-time Sync: Azure SignalR Service

**Miért SignalR:**
- ✅ Real-time updates több felhasználó között
- ✅ "User X is working on feature Y" notifications
- ✅ Conflict warnings
- ✅ Live collaboration
- ✅ WebSocket-alapú kommunikáció

**Konfiguráció javaslat:**
```
Tier: Standard (production)
Unit count: 1-2 (auto-scale based on connections)
Service mode: Default
```

**Költség becslés:**
- Standard tier: ~$5/unit/hó
- 1-2 unit: ~$5-10/hó (kezdés)
- 2-3 unit: ~$10-15/hó (production, több felhasználó)

#### 2.2.5. Cache: Azure Cache for Redis

**Miért Redis:**
- ✅ Session cache
- ✅ Resume Context cache
- ✅ Feature/Todo cache
- ✅ Rate limiting
- ✅ Real-time sync (pub/sub)

**Konfiguráció javaslat:**
```
Tier: Basic C0 (kezdés) → Standard C1 (production)
Size: 250 MB → 1 GB
High Availability: Enabled (production)
```

**Költség becslés:**
- Basic C0: ~$15/hó
- Standard C1: ~$55/hó

#### 2.2.6. Monitoring: Azure Application Insights

**Funkciók:**
- ✅ Performance monitoring
- ✅ Error tracking
- ✅ Custom metrics (token usage, MCP calls)
- ✅ Log aggregation
- ✅ Alerting

**Költség:**
- Ingyenes: 5 GB log/month
- További: ~$2.30/GB

#### 2.2.7. Secrets: Azure Key Vault

**Tárolt információk:**
- Database connection strings
- GitHub API tokens
- JWT secrets
- MCP API keys

**Költség:**
- Standard tier: ~$0.03/10k operations

---

## 3. Technológiai Stack

### 3.1. Backend Stack

#### 3.1.1. Python/FastAPI (Ajánlott)

**Előnyök:**
- ✅ MCP Server is Python → egységes nyelv
- ✅ Nagy ecosystem (PyPI packages)
- ✅ Kiváló teljesítmény (FastAPI + Uvicorn)
- ✅ Automatikus API dokumentáció (Swagger/OpenAPI)
- ✅ Async/await natív támogatás
- ✅ Pydantic validation (type-safe)

**Stack:**
```python
# Framework
- FastAPI (modern, gyors API framework)
- Uvicorn (ASGI server)
- Python 3.11+

# Database
- SQLAlchemy (ORM)
- Alembic (migrations)
- psycopg2-binary (PostgreSQL driver)
- asyncpg (async PostgreSQL driver)

# Authentication
- python-jose (JWT)
- passlib[bcrypt] (password hashing)

# Validation
- Pydantic (schema validation, type-safe)

# GitHub
- PyGithub (GitHub API)

# MCP
- mcp (Model Context Protocol Python SDK)
```

**Struktur javaslat:**
```
backend/
├── src/
│   ├── api/              # REST API endpoints, controllers, schemas
│   ├── services/         # Business logic
│   ├── database/         # SQLAlchemy models, base
│   ├── utils/            # Utilities
│   └── main.py           # FastAPI app
├── alembic/              # Database migrations
├── tests/
├── requirements.txt
└── Dockerfile
```

#### 3.1.2. Opció 2: Python/FastAPI

**Előnyök:**
- ✅ Gyors fejlesztés
- ✅ Jó dokumentáció
- ✅ Async támogatás
- ✅ Automatikus API dokumentáció (OpenAPI)

**Stack:**
```python
# Framework
- FastAPI
- Pydantic (validation)
- SQLAlchemy (ORM)
- Alembic (migrations)

# Database
- asyncpg (PostgreSQL async driver)
- psycopg2 (sync driver)

# Authentication
- python-jose (JWT)
- passlib (password hashing)

# GitHub
- PyGithub (GitHub API)

# MCP
- mcp Python SDK
```

### 3.2. Database Schema és Migrations

**Prisma példa (TypeScript):**
```prisma
// schema.prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model Project {
  id            String   @id @default(uuid())
  name          String
  description   String?
  status        String
  resumeContext Json?
  // ... további mezők
  features      Feature[]
  todos         Todo[]
  createdAt     DateTime @default(now())
  updatedAt     DateTime @updatedAt
}
```

**Migrations:**
- Prisma Migrate (TypeScript)
- vagy Alembic (Python)
- Azure DevOps Pipeline-ban automatikus futtatás

### 3.3. MCP Server

**Struktur:**
```typescript
// mcp-server/
├── src/
│   ├── server.ts         # MCP Server setup
│   ├── tools/            # MCP Tools
│   │   ├── project.ts
│   │   ├── feature.ts
│   │   ├── todo.ts
│   │   └── github.ts
│   ├── resources/        # MCP Resources
│   └── handlers/         # Request handlers
├── package.json
└── Dockerfile
```

**Deployment:**
- Docker container
- Azure Container Apps
- vagy ugyanaz az App Service-ben (külön process)

### 3.4. Frontend (később)

**Stack javaslat:**
```typescript
// Framework
- React 18 + TypeScript
- Vite (build tool)

// State Management
- Zustand (lightweight)
- vagy TanStack Query (server state)

// UI
- Tailwind CSS
- shadcn/ui (components)

// Routing
- React Router

// API
- Axios vagy fetch
- tRPC client (ha backend tRPC-t használ)
```

**Deployment:**
- Azure Static Web Apps (ingyenes tier)
- vagy Azure App Service (ha SSR kell)

---

## 4. Multi-User Támogatás és Skálázhatóság

### 4.1. Multi-User Architektúra

#### 4.1.1. Felhasználókezelés

**Database Schema:**
```sql
-- Felhasználók
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    password_hash TEXT NOT NULL,
    github_username TEXT,
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Felhasználó-projekt kapcsolatok
CREATE TABLE user_projects (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    role TEXT CHECK(role IN ('owner', 'editor', 'viewer')) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, project_id)
);

-- Session ownership
ALTER TABLE sessions ADD COLUMN user_id UUID REFERENCES users(id);

-- Todo assignment
ALTER TABLE todos ADD COLUMN assigned_to UUID REFERENCES users(id);
ALTER TABLE todos ADD COLUMN created_by UUID REFERENCES users(id);

-- Feature assignment
ALTER TABLE features ADD COLUMN assigned_to UUID REFERENCES users(id);
ALTER TABLE features ADD COLUMN created_by UUID REFERENCES users(id);

-- Indexek
CREATE INDEX idx_user_projects_user ON user_projects(user_id);
CREATE INDEX idx_user_projects_project ON user_projects(project_id);
CREATE INDEX idx_todos_assigned ON todos(assigned_to);
CREATE INDEX idx_features_assigned ON features(assigned_to);
CREATE INDEX idx_sessions_user ON sessions(user_id);
```

#### 4.1.2. Authentication és Authorization

**JWT Token Strategy:**
```typescript
// Token struktúra
interface JWTPayload {
  userId: string;
  email: string;
  role: 'user' | 'admin';
  projects: {
    projectId: string;
    role: 'owner' | 'editor' | 'viewer';
  }[];
  iat: number;
  exp: number;
}

// Access token: 15 perc TTL
// Refresh token: 7 nap TTL
```

**Role-Based Access Control (RBAC):**
```typescript
// Projekt szintű jogosultságok
- owner: Teljes hozzáférés (CRUD minden)
- editor: Létrehozás, szerkesztés (nincs törlés)
- viewer: Csak olvasás

// API middleware
function requireProjectRole(role: 'owner' | 'editor' | 'viewer') {
  return async (req, res, next) => {
    const { projectId } = req.params;
    const userProject = await getUserProject(req.user.id, projectId);
    
    if (!userProject || !hasPermission(userProject.role, role)) {
      return res.status(403).json({ error: 'Forbidden' });
    }
    
    req.userProject = userProject;
    next();
  };
}
```

#### 4.1.3. Egyidejű Munkavégzés és Konfliktuskezelés

**Optimistic Locking:**
```typescript
// Version-based conflict detection
interface Todo {
  id: string;
  version: number; // Increment on update
  // ... other fields
}

// Update with version check
async function updateTodo(todoId: string, updates: TodoUpdate, expectedVersion: number) {
  const todo = await db.todo.findUnique({ where: { id: todoId } });
  
  if (todo.version !== expectedVersion) {
    throw new ConflictError('Todo was modified by another user');
  }
  
  return await db.todo.update({
    where: { id: todoId },
    data: {
      ...updates,
      version: { increment: 1 },
      updated_at: new Date()
    }
  });
}
```

**Real-time Sync (WebSocket):**
```typescript
// Azure SignalR Service
- Real-time updates (todo status changes)
- "User X is working on feature Y" notifications
- Conflict warnings
- Live collaboration

// Implementation
import { Server } from '@azure/signalr';

const signalR = new Server({
  connectionString: process.env.SIGNALR_CONNECTION_STRING
});

// Broadcast todo update
signalR.send('todoUpdated', {
  todoId: todo.id,
  projectId: todo.project_id,
  userId: currentUser.id,
  changes: updates
});
```

#### 4.1.4. Feladat Hozzárendelés

**Todo Assignment:**
```typescript
// Automatikus assignment (AI által)
async function assignTodo(todoId: string, userId: string) {
  // Check user has access to project
  const todo = await getTodo(todoId);
  const hasAccess = await checkProjectAccess(userId, todo.project_id);
  
  if (!hasAccess) {
    throw new ForbiddenError();
  }
  
  return await db.todo.update({
    where: { id: todoId },
    data: { assigned_to: userId }
  });
}

// Load balancing (egyenletes terheléselosztás)
async function assignTodoAutomatically(todoId: string) {
  const todo = await getTodo(todoId);
  const availableUsers = await getProjectUsers(todo.project_id);
  
  // Find user with least assigned todos
  const userLoads = await Promise.all(
    availableUsers.map(async (user) => ({
      user,
      load: await getAssignedTodoCount(user.id, todo.project_id)
    }))
  );
  
  const leastLoadedUser = userLoads.reduce((min, current) =>
    current.load < min.load ? current : min
  );
  
  return await assignTodo(todoId, leastLoadedUser.user.id);
}
```

#### 4.1.5. Csapat Kontextus Megosztás

**Team Resume Context:**
```typescript
interface TeamResumeContext {
  project: Project;
  team_members: {
    user_id: string;
    name: string;
    last_session: SessionSummary;
    active_todos: Todo[];
    current_focus: string;
    working_on_feature: string | null;
  }[];
  shared_blockers: Blocker[];
  team_progress: {
    features_in_progress: Feature[];
    completion_rate: number;
    todos_completed_today: number;
  };
}

// MCP Tool
mcp_get_team_context(projectId: string): TeamResumeContext
```

**Csapat Dashboard API:**
```typescript
GET /api/projects/:id/team-dashboard
Response: {
  activeUsers: User[],
  featuresInProgress: Feature[],
  todosByUser: { [userId: string]: Todo[] },
  blockers: Blocker[],
  progress: ProgressMetrics
}
```

### 4.2. Multi-tenant Architektúra

**10-15 projekt kezelése:**

**1. Database optimalizálás:**
```sql
-- Indexek minden projekt_id-n
CREATE INDEX idx_todos_project ON todos(project_id);
CREATE INDEX idx_features_project ON features(project_id);
CREATE INDEX idx_sessions_project ON sessions(project_id);

-- Partitioning (ha nagyon nagy projektek)
-- PostgreSQL table partitioning project_id alapján
```

**2. Connection Pooling:**
```typescript
// Prisma connection pool
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
  // Connection pool settings
  connection_limit = 20
  pool_timeout = 10
}
```

**3. Caching stratégia:**
```typescript
// Redis cache layers
- Project context cache (TTL: 5 min)
- Resume Context cache (TTL: 1 min)
- Feature list cache (TTL: 2 min)
- Document cache (TTL: 10 min)
```

### 4.3. Auto-scaling Konfiguráció

**Backend (App Service):**
```json
{
  "scale": {
    "minInstances": 1,
    "maxInstances": 3,
    "rules": [
      {
        "metric": "CPU",
        "threshold": 70,
        "scaleUp": "+1 instance",
        "scaleDown": "-1 instance (if < 30%)"
      },
      {
        "metric": "Memory",
        "threshold": 80,
        "scaleUp": "+1 instance"
      },
      {
        "metric": "RequestCount",
        "threshold": 1000,
        "scaleUp": "+1 instance"
      }
    ]
  }
}
```

**MCP Server (Container Apps):**
```yaml
minReplicas: 1
maxReplicas: 3
scale:
  rules:
    - name: http-rule
      http:
        metadata:
          concurrentRequests: "100"
```

### 4.4. Database Skálázhatóság

**Read Replicas (ha kell):**
- Azure PostgreSQL read replicas
- Read-only queries → replica
- Write queries → primary

**Connection Pooling:**
- PgBouncer (Azure-ban beépítve)
- vagy application-level pooling (Prisma)

### 4.5. Token Használat Optimalizálás (Multi-User)

**Caching stratégia (Multi-User):**
```typescript
// Redis cache MCP responses (user-scoped)
- User project context: 5 min TTL (key: user:{userId}:project:{projectId})
- User assigned todos: 2 min TTL
- Team context: 1 min TTL
- Documents: 10 min TTL

// Invalidation
- On todo update → invalidate feature cache + user cache
- On feature update → invalidate project cache + team cache
- On assignment change → invalidate user cache
```

#### 4.1.6. Azure SignalR Service (Real-time Sync)

**Miért SignalR:**
- ✅ Real-time updates több felhasználó között
- ✅ "User X is working on feature Y" notifications
- ✅ Conflict warnings
- ✅ Live collaboration

**Konfiguráció:**
```
Tier: Standard (production)
Unit count: 1-2 (auto-scale)
```

**Költség:**
- Standard tier: ~$5/unit/hó
- 1-2 unit: ~$5-10/hó

**Implementáció:**
```typescript
// Backend SignalR hub
import { Server } from '@azure/signalr';

const signalR = new Server({
  connectionString: process.env.SIGNALR_CONNECTION_STRING
});

// Broadcast todo update
signalR.send('todoUpdated', {
  todoId: todo.id,
  projectId: todo.project_id,
  userId: currentUser.id,
  changes: updates
});

// User activity tracking
signalR.send('userActivity', {
  userId: user.id,
  projectId: project.id,
  action: 'working_on_feature',
  featureId: feature.id
});
```

---

## 5. Deployment Stratégia

### 5.1. Fázis 1: DB + Backend + MCP

**Komponensek:**
1. Azure Database for PostgreSQL
2. Azure App Service (Backend API)
3. Azure Container Apps (MCP Server)
4. Azure Cache for Redis
5. Azure SignalR Service (Real-time sync)
6. Azure Key Vault
7. Azure Application Insights

**Deployment:**
```bash
# 1. Database setup
az postgres flexible-server create \
  --resource-group intracker-rg \
  --name intracker-db \
  --admin-user admin \
  --admin-password <password> \
  --sku-name Standard_D2s_v3 \
  --storage-size 128

# 2. Backend deployment
az webapp create \
  --resource-group intracker-rg \
  --plan intracker-plan \
  --name intracker-api \
  --runtime "NODE:20-lts"

# 3. MCP Server deployment
az containerapp create \
  --resource-group intracker-rg \
  --name intracker-mcp \
  --image <registry>/mcp-server:latest \
  --min-replicas 1 \
  --max-replicas 3

# 4. SignalR Service
az signalr create \
  --resource-group intracker-rg \
  --name intracker-signalr \
  --sku Standard_S1 \
  --unit-count 1
```

### 5.2. Fázis 2: Frontend (később)

**Komponensek:**
- Azure Static Web Apps (ajánlott)
- vagy Azure App Service (ha SSR kell)

**Deployment:**
```bash
# Static Web Apps
az staticwebapp create \
  --resource-group intracker-rg \
  --name intracker-web \
  --source <github-repo> \
  --location "East US 2"
```

### 5.3. CI/CD Pipeline

**Azure DevOps vagy GitHub Actions:**

```yaml
# .github/workflows/deploy.yml
name: Deploy to Azure

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
      - name: Install dependencies
        run: npm ci
      - name: Run migrations
        run: npx prisma migrate deploy
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
      - name: Deploy to Azure
        uses: azure/webapps-deploy@v2
        with:
          app-name: intracker-api
          publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
```

---

## 6. Költségbecslés

### 6.1. Fázis 1 (DB + Backend + MCP)

**Havi költség (kezdés):**
```
Azure Database for PostgreSQL (Basic, 2 vCores):    $50-100
Azure App Service (Standard S1):                    $55
Azure Container Apps (MCP Server):                  $30-50
Azure Cache for Redis (Basic C0):                   $15
Azure Key Vault:                                    $1-5
Azure Application Insights:                         $0-10
────────────────────────────────────────────────────
ÖSSZESEN:                                           ~$150-230/hó
```

**Havi költség (production, 10-15 projekt, multi-user):**
```
Azure Database for PostgreSQL (GP, 4 vCores):       $200-400
Azure App Service (Premium P1V2, 2-3 instances):    $300-450
Azure Container Apps (MCP Server, 2-3 replicas):   $60-120
Azure Cache for Redis (Standard C1):                $55
Azure SignalR Service (Standard, 2 units):          $10-15
Azure Key Vault:                                    $5-10
Azure Application Insights:                         $20-50
────────────────────────────────────────────────────
ÖSSZESEN:                                           ~$650-1100/hó
```

### 6.2. Fázis 2 (+ Frontend)

**Havi költség:**
```
Fázis 1 költség:                                    $640-1085
Azure Static Web Apps (Standard):                    $9
────────────────────────────────────────────────────
ÖSSZESEN:                                           ~$650-1095/hó
```

### 6.3. Költségoptimalizálás

**1. Dev/Test környezet:**
- Dev: Basic tier mindenhol (~$100/hó)
- Production: Standard/Premium tier

**2. Reserved Instances:**
- 1-3 évre előre fizetés → 30-50% kedvezmény

**3. Auto-scaling:**
- Csak használatkor fizetünk
- Időszakos terhelés → csak akkor skálázás

---

## 7. Biztonság

### 7.1. Authentication és Authorization

**Backend:**
```typescript
// JWT token alapú
- Access token (15 min TTL)
- Refresh token (7 nap TTL)
- Role-based access control (RBAC)
```

**Database:**
- Connection string Key Vault-ban
- SSL/TLS kötelező
- Firewall rules (csak App Service IP-k)

### 7.2. Secrets Management

**Azure Key Vault:**
- Database connection strings
- GitHub API tokens
- JWT secrets
- MCP API keys

**Access:**
- Managed Identity (App Service → Key Vault)
- Nincs hardcoded secret

### 7.3. Network Security

**VNet Integration (opcionális):**
- App Service → VNet
- Database → Private endpoint
- Nincs public access

---

## 8. Monitoring és Alerting

### 8.1. Application Insights

**Metrikák:**
- Request count, response time
- Error rate
- Custom metrics (token usage, MCP calls)
- Database query performance

**Alerts:**
- High error rate (> 5%)
- Slow response time (> 2s)
- Database connection issues
- High token usage

### 8.2. Logging

**Strukturált logok:**
```typescript
{
  timestamp: "2024-01-15T10:30:00Z",
  level: "info",
  service: "backend",
  projectId: "proj-123",
  featureId: "feat-456",
  action: "todo_created",
  userId: "user-789"
}
```

**Log aggregation:**
- Application Insights Logs
- vagy Azure Log Analytics

---

## 9. Ajánlott Technológiai Stack Összefoglalás

### 9.1. Backend (Node.js/TypeScript - Ajánlott)

```typescript
✅ Framework: Express.js vagy Fastify
✅ Language: TypeScript
✅ Database ORM: Prisma
✅ Validation: Zod
✅ Authentication: JWT
✅ GitHub: @octokit/rest
✅ MCP: @modelcontextprotocol/sdk
```

### 9.2. Alternatíva (Python/FastAPI)

```python
✅ Framework: FastAPI
✅ Language: Python 3.11+
✅ Database ORM: SQLAlchemy
✅ Validation: Pydantic
✅ Authentication: python-jose
✅ GitHub: PyGithub
✅ MCP: mcp Python SDK
```

### 9.3. Database

```
✅ Azure Database for PostgreSQL
✅ Prisma Migrate (migrations)
✅ Connection pooling
✅ Read replicas (ha kell)
```

### 9.4. Cache

```
✅ Azure Cache for Redis
✅ Session cache
✅ Context cache
✅ Feature/Todo cache
```

### 9.5. Deployment

```
✅ Azure App Service (Backend)
✅ Azure Container Apps (MCP Server)
✅ Azure Static Web Apps (Frontend, később)
✅ GitHub Actions (CI/CD)
```

---

## 10. Implementációs Lépések

### 10.1. Fázis 1: Alapok (1-2 hét)

1. **Azure Resource Group létrehozása**
2. **PostgreSQL database setup**
   - Database létrehozás
   - Connection string Key Vault-ba
   - Initial schema deployment
3. **Backend API setup**
   - App Service létrehozás
   - Code deployment
   - Environment variables
4. **MCP Server setup**
   - Container Apps létrehozás
   - Docker image build & push
   - Deployment
5. **Redis cache setup**
6. **Application Insights konfigurálás**

### 10.2. Fázis 2: Optimalizálás (1 hét)

1. **Auto-scaling konfigurálás**
2. **Caching stratégia implementálása**
3. **Monitoring és alerting**
4. **Performance testing**
5. **Cost optimization**

### 10.3. Fázis 3: Frontend (később, 1-2 hét)

1. **Static Web Apps létrehozás**
2. **Frontend build és deployment**
3. **API integráció**
4. **Testing**

---

## 11. Következtetés

**Ajánlott stack:**
- **Backend:** Node.js/TypeScript + Express.js + Prisma
- **Database:** Azure Database for PostgreSQL
- **Cache:** Azure Cache for Redis
- **Deployment:** Azure App Service + Container Apps
- **Monitoring:** Azure Application Insights

**Költség:**
- Kezdés: ~$150-230/hó
- Production (10-15 projekt): ~$650-1095/hó

**Skálázhatóság:**
- ✅ 10-15 projekt kezelése
- ✅ Több felhasználó egyidejű munkavégzése
- ✅ Auto-scaling beépítve
- ✅ Caching optimalizálás

**Előnyök:**
- ✅ Managed services (kevesebb maintenance)
- ✅ Auto-scaling
- ✅ Built-in monitoring
- ✅ High availability
- ✅ Security best practices

---

## 11. Multi-User Támogatás Összefoglalás

### 11.1. Implementált Funkciók

**Felhasználókezelés:**
- ✅ User registration és authentication (JWT)
- ✅ Project sharing (owner/editor/viewer roles)
- ✅ User-project kapcsolatok
- ✅ Session ownership

**Feladat hozzárendelés:**
- ✅ Todo assignment (manuális és automatikus)
- ✅ Feature assignment
- ✅ Load balancing (egyenletes terheléselosztás)

**Egyidejű munkavégzés:**
- ✅ Optimistic locking (version-based conflict detection)
- ✅ Real-time sync (Azure SignalR Service)
- ✅ User activity tracking
- ✅ Conflict warnings

**Csapat kontextus:**
- ✅ Team dashboard API
- ✅ Shared Resume Context
- ✅ Team progress tracking
- ✅ User activity visibility

### 11.2. Database Schema (Multi-User)

**Új táblák:**
- `users` - Felhasználók
- `user_projects` - Felhasználó-projekt kapcsolatok
- `todos.assigned_to`, `todos.created_by` - Todo assignment
- `features.assigned_to`, `features.created_by` - Feature assignment
- `sessions.user_id` - Session ownership

**Indexek:**
- `idx_user_projects_user`, `idx_user_projects_project`
- `idx_todos_assigned`, `idx_features_assigned`
- `idx_sessions_user`

### 11.3. API Endpoints (Multi-User)

**Új endpointok:**
- `GET /api/projects/:id/team-dashboard` - Csapat dashboard
- `POST /api/todos/:id/assign` - Todo assignment
- `POST /api/features/:id/assign` - Feature assignment
- `GET /api/users/:id/projects` - User's projects
- `GET /api/users/:id/todos` - User's assigned todos

### 11.4. MCP Tools (Multi-User)

**Új tools:**
- `mcp_get_my_todos()` - User's assigned todos
- `mcp_get_team_context()` - Team resume context
- `mcp_assign_todo()` - Todo assignment
- `mcp_assign_feature()` - Feature assignment

**Új resources:**
- `user://{userId}/project/{projectId}/context` - User-scoped context
- `user://{userId}/my-todos` - User's todos

---

## 12. Fejlesztési Todo Listák

A részletes fejlesztési todo listák külön dokumentumokban találhatók:

### 12.1. Database Todo Lista
**Fájl:** `todos-database.md`

**Főbb fázisok:**
1. Core tables (Users, Projects, Features, Todos, etc.)
2. Migrations és constraints
3. Functions és triggers
4. Views és materialized views
5. Indexek optimalizálás
6. Seed data és testing
7. Backup és recovery
8. Monitoring és maintenance

### 12.2. Backend Todo Lista
**Fájl:** `todos-backend.md`

**Főbb fázisok:**
1. Projekt setup és alapok
2. Database integration (Prisma)
3. Authentication és authorization
4. REST API endpoints
5. Caching (Redis)
6. Real-time sync (SignalR)
7. Error handling és validation
8. Testing
9. Security
10. Monitoring és logging

### 12.3. MCP Server Todo Lista
**Fájl:** `todos-mcp.md`

**Főbb fázisok:**
1. MCP Server setup
2. Project context tools
3. Feature kezelés tools
4. Todo kezelés tools
5. Session kezelés tools
6. Dokumentáció tools
7. GitHub integráció tools
8. MCP Resources
9. Caching és optimalizálás
10. Error handling és validation
11. Testing
12. Monitoring és logging
13. Security

### 12.4. Implementációs Prioritás

**MVP (Minimum Viable Product):**
1. Database core tables
2. Backend API alapok (Projects, Features, Todos)
3. Authentication (JWT)
4. MCP Server alapok
5. Basic MCP tools

**Fázis 1 után:**
6. Multi-user support (Users, User_Projects, Assignment)
7. Authorization (RBAC)
8. Real-time sync (SignalR)
9. Caching (Redis)
10. GitHub integration

**Production előtt:**
11. Testing (unit, integration, E2E)
12. Security hardening
13. Monitoring setup
14. Performance optimization
15. Documentation

---

Ez a dokumentum részletesen leírja az InTracker Azure-beli telepítését és működtetését, figyelembe véve a több projekt és több felhasználó követelményeit. A fejlesztési todo listák a `todos-database.md`, `todos-backend.md` és `todos-mcp.md` fájlokban találhatók.

# InTracker - Rendszerarchitektúra és Tervezés

## 1. Áttekintés

Az InTracker egy AI-first projektmenedzsment rendszer, amely a kontextusmegőrzésre és a fejlesztő-AI együttműködésre épül. A rendszer célja, hogy minimalizálja a kontextusvesztést és lehetővé tegye a gyors projektváltást.

---

## 2. Architektúra komponensek

### 2.1. Fő komponensek

```
┌─────────────────────────────────────────────────────────┐
│                    InTracker Application                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Frontend   │  │   Backend    │  │  MCP Server  │ │
│  │   (Web UI)  │  │   (API)      │  │              │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│         │                  │                  │         │
│         └──────────────────┴──────────────────┘         │
│                         │                               │
│                  ┌──────────────┐                       │
│                  │  Database    │                       │
│                  │  (SQLite/    │                       │
│                  │   PostgreSQL) │                       │
│                  └──────────────┘                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
         │                    │
         │                    │
    ┌─────────┐         ┌──────────────┐
    │ GitHub  │         │  AI (Cursor) │
    │   API   │         │   via MCP    │
    └─────────┘         └──────────────┘
```

### 2.2. Technológiai stack javaslat

**Backend:**
- **Nyelv:** Python 3.11+
- **Framework:** FastAPI
- **Adatbázis:** PostgreSQL
- **ORM:** SQLAlchemy
- **Migrations:** Alembic
- **API:** REST API (OpenAPI/Swagger auto-docs)
- **MCP Server:** Python (mcp SDK)

**Frontend:**
- **Framework:** React + TypeScript
- **State Management:** Zustand vagy Redux Toolkit
- **UI Library:** Tailwind CSS + shadcn/ui vagy MUI
- **Routing:** React Router

**Integrációk:**
- **GitHub:** Octokit (GitHub API)
- **MCP:** Model Context Protocol SDK

---

## 3. Adatmodell és entitások

### 3.1. Adatbázis séma

#### 3.1.1. Ideas (Ötletek)

```sql
CREATE TABLE ideas (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT CHECK(status IN ('draft', 'active', 'archived')),
    tags TEXT[], -- Array of tags
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    converted_to_project_id UUID REFERENCES projects(id),
    metadata JSONB -- Flexible storage for additional data
);
```

#### 3.1.2. Projects (Projektek)

```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT CHECK(status IN ('active', 'paused', 'blocked', 'completed', 'archived')),
    tags TEXT[],
    technology_tags TEXT[], -- e.g., ['react', 'typescript', 'node']
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_session_at TIMESTAMP,
    resume_context JSONB, -- Last/Now/Next/Blockers/Constraints
    cursor_instructions TEXT, -- AI working rules for this project
    github_repo_url TEXT,
    github_repo_id TEXT,
    metadata JSONB
);
```

#### 3.1.3. Project Elements (Projekt elemek)

```sql
CREATE TABLE project_elements (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES project_elements(id), -- Hierarchical structure
    type TEXT CHECK(type IN ('module', 'feature', 'component', 'milestone', 'technical_block', 'decision_point')),
    title TEXT NOT NULL,
    description TEXT,
    status TEXT CHECK(status IN ('todo', 'in_progress', 'blocked', 'done')),
    position INTEGER, -- Order within parent
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    definition_of_done TEXT,
    github_issue_number INTEGER,
    github_issue_url TEXT,
    metadata JSONB,
    FOREIGN KEY (parent_id) REFERENCES project_elements(id) ON DELETE CASCADE
);

CREATE INDEX idx_project_elements_project ON project_elements(project_id);
CREATE INDEX idx_project_elements_parent ON project_elements(parent_id);
```

#### 3.1.4. Dependencies (Függőségek)

```sql
CREATE TABLE element_dependencies (
    id UUID PRIMARY KEY,
    element_id UUID NOT NULL REFERENCES project_elements(id) ON DELETE CASCADE,
    depends_on_element_id UUID NOT NULL REFERENCES project_elements(id) ON DELETE CASCADE,
    dependency_type TEXT CHECK(dependency_type IN ('blocks', 'requires', 'related')),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(element_id, depends_on_element_id)
);

CREATE INDEX idx_dependencies_element ON element_dependencies(element_id);
CREATE INDEX idx_dependencies_depends_on ON element_dependencies(depends_on_element_id);
```

#### 3.1.5. Features (Funkciók)

```sql
CREATE TABLE features (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT CHECK(status IN ('todo', 'in_progress', 'blocked', 'done')),
    progress_percentage INTEGER DEFAULT 0, -- Calculated: completed_todos / total_todos
    total_todos INTEGER DEFAULT 0,
    completed_todos INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

CREATE INDEX idx_features_project ON features(project_id);
CREATE INDEX idx_features_status ON features(status);
```

#### 3.1.6. Todos (Feladatok)

```sql
CREATE TABLE todos (
    id UUID PRIMARY KEY,
    element_id UUID NOT NULL REFERENCES project_elements(id) ON DELETE CASCADE,
    feature_id UUID REFERENCES features(id) ON DELETE SET NULL, -- Funkcióhoz kapcsolva
    title TEXT NOT NULL,
    description TEXT,
    status TEXT CHECK(status IN ('todo', 'in_progress', 'blocked', 'done')),
    position INTEGER,
    estimated_effort INTEGER, -- In hours or story points
    blocker_reason TEXT,
    github_issue_number INTEGER,
    github_pr_number INTEGER,
    github_pr_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    metadata JSONB
);

CREATE INDEX idx_todos_element ON todos(element_id);
CREATE INDEX idx_todos_feature ON todos(feature_id);
CREATE INDEX idx_todos_status ON todos(status);
```

#### 3.1.7. Feature Elements (Funkció-Elem kapcsolatok)

```sql
CREATE TABLE feature_elements (
    id UUID PRIMARY KEY,
    feature_id UUID NOT NULL REFERENCES features(id) ON DELETE CASCADE,
    element_id UUID NOT NULL REFERENCES project_elements(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(feature_id, element_id)
);

CREATE INDEX idx_feature_elements_feature ON feature_elements(feature_id);
CREATE INDEX idx_feature_elements_element ON feature_elements(element_id);
```

#### 3.1.8. Documents (Dokumentáció)

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    element_id UUID REFERENCES project_elements(id) ON DELETE SET NULL,
    type TEXT CHECK(type IN ('architecture', 'adr', 'domain', 'constraints', 'runbook', 'ai_instructions')),
    title TEXT NOT NULL,
    content TEXT NOT NULL, -- Markdown format
    tags TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    version INTEGER DEFAULT 1,
    metadata JSONB
);

CREATE INDEX idx_documents_project ON documents(project_id);
CREATE INDEX idx_documents_element ON documents(element_id);
CREATE INDEX idx_documents_type ON documents(type);
```

#### 3.1.9. Sessions (Munkamenetek)

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title TEXT,
    goal TEXT, -- What was the goal of this session
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    summary TEXT, -- Auto-generated session summary
    feature_ids UUID[] REFERENCES features(id), -- Melyik funkciókra fókuszál
    todos_completed INTEGER[] REFERENCES todos(id),
    features_completed UUID[] REFERENCES features(id), -- Befejezett funkciók
    elements_updated INTEGER[] REFERENCES project_elements(id),
    notes TEXT,
    metadata JSONB
);

CREATE INDEX idx_sessions_project ON sessions(project_id);
CREATE INDEX idx_sessions_started ON sessions(started_at);
```

#### 3.1.10. GitHub Branches (Branch kezelés)

```sql
CREATE TABLE github_branches (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    feature_id UUID REFERENCES features(id) ON DELETE SET NULL,
    branch_name TEXT NOT NULL,
    base_branch TEXT DEFAULT 'main',
    status TEXT CHECK(status IN ('active', 'merged', 'deleted')),
    ahead_count INTEGER DEFAULT 0,
    behind_count INTEGER DEFAULT 0,
    has_conflicts BOOLEAN DEFAULT FALSE,
    last_commit_sha TEXT,
    last_commit_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    merged_at TIMESTAMP,
    UNIQUE(project_id, branch_name)
);

CREATE INDEX idx_branches_project ON github_branches(project_id);
CREATE INDEX idx_branches_feature ON github_branches(feature_id);
CREATE INDEX idx_branches_status ON github_branches(status);
```

#### 3.1.11. GitHub Sync (GitHub szinkronizáció)

```sql
CREATE TABLE github_sync (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    entity_type TEXT CHECK(entity_type IN ('element', 'todo', 'feature', 'branch')),
    entity_id UUID NOT NULL,
    github_type TEXT CHECK(github_type IN ('issue', 'pr', 'branch', 'commit')),
    github_id INTEGER, -- NULL lehet commit SHA esetén
    github_url TEXT,
    last_synced_at TIMESTAMP DEFAULT NOW(),
    sync_direction TEXT CHECK(sync_direction IN ('tracker_to_github', 'github_to_tracker', 'bidirectional')),
    UNIQUE(entity_id, github_type, github_id)
);

CREATE INDEX idx_github_sync_project ON github_sync(project_id);
CREATE INDEX idx_github_sync_entity ON github_sync(entity_type, entity_id);
```

---

## 4. API tervezés

### 4.1. REST API végpontok

#### 4.1.1. Ideas

```
GET    /api/ideas                    # List all ideas
POST   /api/ideas                    # Create idea
GET    /api/ideas/:id                # Get idea
PUT    /api/ideas/:id                # Update idea
DELETE /api/ideas/:id                # Delete idea
POST   /api/ideas/:id/convert        # Convert idea to project
```

#### 4.1.2. Projects

```
GET    /api/projects                 # List projects (with filters)
POST   /api/projects                 # Create project
GET    /api/projects/:id             # Get project with full context
PUT    /api/projects/:id             # Update project
DELETE /api/projects/:id             # Delete project
GET    /api/projects/:id/resume      # Get resume context
PUT    /api/projects/:id/resume      # Update resume context
GET    /api/projects/:id/elements    # Get project elements tree
```

#### 4.1.3. Features

```
GET    /api/projects/:id/features    # List features for project
POST   /api/features                 # Create feature
GET    /api/features/:id             # Get feature with todos
PUT    /api/features/:id             # Update feature
DELETE /api/features/:id             # Delete feature
GET    /api/features/:id/todos       # Get todos for feature
GET    /api/features/:id/elements    # Get elements for feature
POST   /api/features/:id/elements    # Link element to feature
```

#### 4.1.4. Project Elements

```
GET    /api/elements/:id             # Get element with todos
POST   /api/elements                 # Create element
PUT    /api/elements/:id             # Update element
DELETE /api/elements/:id             # Delete element
GET    /api/elements/:id/todos       # Get todos for element
POST   /api/elements/:id/dependencies # Add dependency
```

#### 4.1.5. Todos

```
GET    /api/todos                    # List todos (with filters)
POST   /api/todos                    # Create todo
GET    /api/todos/:id                # Get todo
PUT    /api/todos/:id                # Update todo
DELETE /api/todos/:id                # Delete todo
```

#### 4.1.6. Documents

```
GET    /api/projects/:id/documents   # List documents for project
POST   /api/documents                # Create document
GET    /api/documents/:id            # Get document
PUT    /api/documents/:id            # Update document
DELETE /api/documents/:id             # Delete document
```

#### 4.1.7. Sessions

```
GET    /api/projects/:id/sessions    # List sessions for project
POST   /api/sessions                 # Start session
PUT    /api/sessions/:id             # Update session
POST   /api/sessions/:id/end         # End session (generates summary)
GET    /api/sessions/:id             # Get session details
```

#### 4.1.8. GitHub Integration (Repository és Branch)

```
# Repository
POST   /api/projects/:id/github/connect    # Connect GitHub repo
GET    /api/projects/:id/github/repo       # Get repo info

# Branches
GET    /api/projects/:id/branches          # List branches for project
POST   /api/branches                        # Create branch for feature
GET    /api/branches/:id                   # Get branch details
PUT    /api/branches/:id                   # Update branch status
DELETE /api/branches/:id                   # Delete branch
GET    /api/features/:id/branches          # Get branches for feature
GET    /api/projects/:id/active-branch      # Get active branch

# Sync
GET    /api/projects/:id/github/sync       # Sync status
POST   /api/projects/:id/github/sync       # Trigger sync

# Issues and PRs
GET    /api/github/issues/:number          # Get issue details
POST   /api/github/prs                     # Create PR
```

---

## 5. MCP Server specifikáció

### 5.1. MCP Tools (AI által használható funkciók)

#### 5.1.1. Projekt lekérdezés

```typescript
// Get project context
mcp_get_project_context(projectId: string): ProjectContext

// Get resume context
mcp_get_resume_context(projectId: string): ResumeContext

// Get active todos
mcp_get_active_todos(projectId: string): Todo[]

// Get project elements tree
mcp_get_project_structure(projectId: string): ProjectElement[]
```

#### 5.1.2. Feature kezelés

```typescript
// Create feature
mcp_create_feature(projectId: string, feature: CreateFeatureInput): Feature

// Get feature with todos
mcp_get_feature(featureId: string): Feature

// List features
mcp_list_features(projectId: string, filters?: FeatureFilters): Feature[]

// Get todos for feature
mcp_get_feature_todos(featureId: string): Todo[]

// Get elements for feature
mcp_get_feature_elements(featureId: string): ProjectElement[]

// Link element to feature
mcp_link_element_to_feature(featureId: string, elementId: string): void

// Update feature status
mcp_update_feature_status(featureId: string, status: FeatureStatus): Feature
```

#### 5.1.3. Todo kezelés

```typescript
// Create todo (with optional featureId)
mcp_create_todo(elementId: string, todo: CreateTodoInput, featureId?: string): Todo

// Update todo status
mcp_update_todo_status(todoId: string, status: TodoStatus): Todo

// List todos (with optional featureId filter)
mcp_list_todos(projectId: string, filters?: TodoFilters): Todo[]
```

#### 5.1.3. Dokumentáció

```typescript
// Read document
mcp_read_document(documentId: string): Document

// Search documents
mcp_search_documents(projectId: string, query: string): Document[]

// Get document by type
mcp_get_documents_by_type(projectId: string, type: DocumentType): Document[]
```

#### 5.1.5. Session kezelés

```typescript
// Start session (with optional featureIds)
mcp_start_session(projectId: string, goal: string, featureIds?: string[]): Session

// Update session
mcp_update_session(sessionId: string, updates: SessionUpdate): Session

// End session and generate summary
mcp_end_session(sessionId: string): SessionSummary
```

#### 5.1.6. GitHub integráció (Repository és Branch fókusz)

```typescript
// Repository kezelés
mcp_connect_github_repo(projectId: string, repoUrl: string): void
mcp_get_repo_info(projectId: string): RepoInfo

// Branch kezelés (InTracker workflow)
mcp_create_branch_for_feature(
  featureId: string,
  baseBranch?: string
): Branch

mcp_get_active_branch(projectId: string): Branch | null

mcp_link_branch_to_feature(
  featureId: string,
  branchName: string
): void

mcp_get_feature_branches(featureId: string): Branch[]

mcp_get_branch_status(branchName: string): BranchStatus

// Commit kezelés
mcp_get_commits_for_feature(featureId: string): Commit[]
mcp_parse_commit_message(commitMessage: string): CommitMetadata

// Issue és PR kezelés
mcp_link_element_to_issue(elementId: string, issueNumber: number): void
mcp_link_todo_to_pr(todoId: string, prNumber: number): void
mcp_get_github_issue(repo: string, issueNumber: number): GitHubIssue
mcp_create_github_pr(
  branchName: string,
  title: string,
  body: string,
  baseBranch: string
): GitHubPR
```

### 5.2. MCP Resources (AI által elérhető erőforrások)

```
project://{projectId}/context          # Full project context
project://{projectId}/resume           # Resume context package
project://{projectId}/structure        # Project structure tree
project://{projectId}/features         # Active features
project://{projectId}/active-todos     # Active todos
project://{projectId}/documents        # All documents
feature://{featureId}                   # Feature with todos
document://{documentId}                # Specific document
session://{sessionId}                  # Session details
```

---

## 6. Frontend struktúra

### 6.1. Fő komponensek

```
src/
├── components/
│   ├── projects/
│   │   ├── ProjectList.tsx
│   │   ├── ProjectCard.tsx
│   │   ├── ProjectView.tsx
│   │   └── ResumeContext.tsx
│   ├── elements/
│   │   ├── ElementTree.tsx
│   │   ├── ElementCard.tsx
│   │   └── ElementEditor.tsx
│   ├── features/
│   │   ├── FeatureList.tsx
│   │   ├── FeatureCard.tsx
│   │   └── FeatureView.tsx
│   ├── todos/
│   │   ├── TodoList.tsx
│   │   ├── TodoCard.tsx
│   │   └── TodoEditor.tsx
│   ├── documents/
│   │   ├── DocumentList.tsx
│   │   ├── DocumentViewer.tsx
│   │   └── DocumentEditor.tsx
│   ├── sessions/
│   │   ├── SessionPanel.tsx
│   │   └── SessionSummary.tsx
│   └── ideas/
│       ├── IdeaList.tsx
│       └── IdeaCard.tsx
├── pages/
│   ├── Dashboard.tsx
│   ├── ProjectDetail.tsx
│   ├── IdeaBoard.tsx
│   └── Settings.tsx
├── stores/
│   ├── projectStore.ts
│   ├── featureStore.ts
│   ├── todoStore.ts
│   └── sessionStore.ts
├── services/
│   ├── api.ts
│   ├── mcp.ts
│   └── github.ts
└── hooks/
    ├── useProject.ts
    ├── useFeatures.ts
    ├── useTodos.ts
    └── useSession.ts
```

### 6.2. Főbb UI funkciók

- **Dashboard:** Aktív projektek áttekintése, gyors váltás
- **Project View:** Teljes projekt kontextus, hierarchikus struktúra
- **Resume Context Panel:** Last/Now/Next/Blockers gyors áttekintés
- **Session Panel:** Aktív munkamenet kezelése
- **Quick Switch:** Projektváltás 1-2 kattintással
- **Search:** Cross-project keresés

---

## 7. GitHub integráció részletei

### 7.1. Szinkronizációs logika

**Element ↔ Issue:**
- Projekt elem létrehozásakor opcionálisan GitHub issue
- Issue státusz változás visszaszinkronizálása
- Kétirányú kapcsolat: bidirectional sync

**Todo ↔ PR:**
- Todo → PR: PR létrehozásakor automatikus linkelés
- PR merge → Todo done státusz
- PR review comments → Todo notes

**Commit ↔ Context:**
- Commit message-ben projekt/elemenk hivatkozás
- Commit history visszakeresése projekthez

### 7.2. GitHub API használat

```typescript
// Octokit setup
const octokit = new Octokit({ auth: GITHUB_TOKEN });

// Create issue from element
async function createIssueFromElement(element: ProjectElement) {
  const issue = await octokit.rest.issues.create({
    owner: repo.owner,
    repo: repo.name,
    title: element.title,
    body: element.description,
    labels: ['intracker', element.type]
  });
  // Link in database
  await linkElementToIssue(element.id, issue.data.number);
}
```

---

## 8. Resume Context struktúra

### 8.1. Resume Context JSON séma

```typescript
interface ResumeContext {
  last: {
    session_id: string;
    session_summary: string;
    completed_todos: string[];
    updated_elements: string[];
    timestamp: string;
  };
  now: {
    next_todos: Todo[]; // 1-3 todo
    active_elements: ProjectElement[]; // Currently working on
    immediate_goals: string[]; // What to achieve next
  };
  next_blockers: {
    blocked_todos: Todo[];
    waiting_for: string[]; // External dependencies
    technical_blocks: string[];
  };
  constraints: {
    rules: string[]; // "Don't use X", "Always do Y"
    architecture_decisions: string[];
    technical_limits: string[];
  };
  cursor_instructions: string; // How AI should work on this project
}
```

### 8.2. Resume Context generálás

- **Session végén:** Automatikus frissítés
- **Manuális frissítés:** Felhasználó által
- **AI által:** MCP tool segítségével

---

## 9. Session kezelés

### 9.1. Session életciklus

1. **Start:** Felhasználó elindít egy sessiont egy projekten
2. **Work:** Todo-k frissítése, elemek módosítása
3. **End:** Session befejezése, summary generálás
4. **Resume Context Update:** Automatikus frissítés

### 9.2. Session Summary generálás

```typescript
async function generateSessionSummary(sessionId: string): Promise<string> {
  const session = await getSession(sessionId);
  const changes = await getSessionChanges(sessionId);
  
  // AI-generated summary (via MCP or LLM API)
  const summary = await generateSummary({
    goal: session.goal,
    completed: changes.completed_todos,
    updated: changes.updated_elements,
    notes: session.notes
  });
  
  return summary;
}
```

---

## 10. Keresés és szűrés

### 10.1. Cross-project keresés

```sql
-- Search across projects, elements, todos, documents
SELECT 
  'project' as type, id, name as title, description
FROM projects
WHERE name ILIKE '%query%' OR description ILIKE '%query%'
UNION ALL
SELECT 
  'element' as type, id, title, description
FROM project_elements
WHERE title ILIKE '%query%' OR description ILIKE '%query%'
-- ... etc
```

### 10.2. Szűrési lehetőségek

- **Státusz szerint:** active, paused, blocked
- **Technológia szerint:** technology_tags
- **Címkék szerint:** tags
- **Dátum szerint:** last_session_at, created_at

---

## 11. Biztonság és autentikáció

### 11.1. Felhasználókezelés

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE user_projects (
    user_id UUID REFERENCES users(id),
    project_id UUID REFERENCES projects(id),
    role TEXT CHECK(role IN ('owner', 'editor', 'viewer')),
    PRIMARY KEY (user_id, project_id)
);
```

### 11.2. API autentikáció

- JWT token alapú autentikáció
- GitHub OAuth opcionális integráció
- MCP server: API key vagy OAuth

---

## 12. Telepítés és futtatás

### 12.1. Fejlesztési környezet

```bash
# Backend
cd backend
npm install
npm run dev

# Frontend
cd frontend
npm install
npm run dev

# MCP Server
cd mcp-server
npm install
npm run dev
```

### 12.2. Adatbázis migrációk

- Migration rendszer (pl. Knex.js, TypeORM Migrations)
- Seed adatok fejlesztéshez

---

## 13. Következő lépések (MVP prioritás)

### Fázis 1: Alapvető funkcionalitás
1. ✅ Adatbázis séma implementálása
2. ✅ REST API alapok (Projects, Elements, Todos)
3. ✅ Egyszerű frontend (projekt lista, projekt nézet)
4. ✅ Alapvető CRUD műveletek

### Fázis 2: Kontextuskezelés
5. ✅ Resume Context implementáció
6. ✅ Session kezelés
7. ✅ Session Summary generálás

### Fázis 3: AI integráció
8. ✅ MCP Server alapok
9. ✅ MCP Tools implementáció
10. ✅ MCP Resources

### Fázis 4: GitHub integráció
11. ✅ GitHub API kapcsolat
12. ✅ Issue/PR szinkronizáció
13. ✅ Kétirányú sync

### Fázis 5: Dokumentáció és finomítás
14. ✅ Dokumentum kezelés
15. ✅ Keresés és szűrés
16. ✅ UI/UX finomítás

---

## 14. Különleges megfontolások

### 14.1. Teljesítmény

- **Lazy loading:** Projekt elemek fa struktúrája
- **Caching:** Resume Context cache-elése
- **Indexek:** Adatbázis indexek optimalizálása

### 14.2. Skálázhatóság

- **Pagination:** Nagy listák esetén
- **Virtual scrolling:** Frontend-en
- **Database connection pooling**

### 14.3. Offline támogatás (jövőbeli)

- **Service Worker:** Offline működés
- **Local Storage:** Ideiglenes adatok
- **Sync:** Online visszaálláskor

---

## 15. Dokumentáció formátumok

### 15.1. Dokumentumtípusok specifikációja

**Architecture Snapshot:**
- Rendszerarchitektúra pillanatkép
- Komponens diagramok (Markdown + Mermaid)
- Technológiai stack

**ADR (Architecture Decision Record):**
- Döntés kontextusa
- Döntés indoklása
- Következmények

**Domain/Fogalomtár:**
- Domain fogalmak definíciói
- Kapcsolatok közöttük

**Constraints:**
- Mit nem szabad használni
- Milyen szabályokat kell követni

**Runbook:**
- Build, run, deploy lépések
- Környezeti változók
- Troubleshooting

**AI Instructions:**
- Projekt-specifikus AI munkaszabályok
- Coding standards
- Architektúrai elvek

---

Ez a dokumentum az InTracker rendszer teljes architektúráját és tervezését tartalmazza. A megvalósítás során ezt a dokumentumot kell követni, és szükség esetén frissíteni kell.

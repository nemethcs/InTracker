# InTracker - MVP Roadmap és Kezdési Terv

## 🎯 Kezdési Stratégia

A fejlesztést **fokozatosan, MVP-től indulva** érdemes végezni. Itt a logikus sorrend és az első konkrét lépések.

---

## 📋 Fázisok Sorrendje

### **FÁZIS 0: Alapok (1-2 hét)**
**Cél:** Működő alaprendszer, amit lehet tesztelni

#### 1. Database Setup (ELSŐ LÉPÉS) ⭐
**Fájl:** `todos-database.md` - Fázis 1-2

**Első 3 nap:**
- [x] PostgreSQL database létrehozása (Docker)
- [x] Prisma schema létrehozása (reference)
- [x] SQLAlchemy models létrehozása (backend/src/database/models.py)
- [x] Core tables definiálva:
  - [x] `users` table
  - [x] `projects` table
  - [x] `project_elements` table
  - [x] `features` table
  - [x] `todos` table
  - [x] `user_projects` table
- [ ] Alembic migration inicializálás
- [ ] Initial migration futtatása
- [ ] Seed data (2-3 test user, 1-2 test project)

**Miért ezzel kezdünk:**
- ✅ Minden más erre épül
- ✅ Könnyen tesztelhető (SQL queries)
- ✅ Nincs dependency más komponensre
- ✅ Megvan az adatstruktúra, amit a Backend és MCP használ

#### 2. Backend API Alapok
**Fájl:** `todos-backend.md` - Fázis 1-2

**Következő 3-4 nap:**
- [x] Backend projekt setup (Python + FastAPI)
- [x] SQLAlchemy integráció
- [x] Database connection tesztelése
- [x] Authentication (JWT, password hashing)
- [ ] Alapvető CRUD API-k:
  - [ ] `GET /api/projects` - List projects
  - [ ] `POST /api/projects` - Create project
  - [ ] `GET /api/projects/{id}` - Get project
  - [ ] `GET /api/features` - List features
  - [ ] `POST /api/features` - Create feature
  - [ ] `GET /api/todos` - List todos
  - [ ] `POST /api/todos` - Create todo

**Miért ezt következőnek:**
- ✅ Database már kész → használhatjuk
- ✅ API-kkal tesztelhetjük az adatbázist
- ✅ Postman/Insomnia-val könnyen tesztelhető
- ✅ MCP Server erre épül

#### 3. Authentication (Egyszerű verzió)
**Fájl:** `todos-backend.md` - Fázis 3

**1-2 nap:**
- [x] JWT service (create_access_token, verify_token)
- [x] Password hashing (passlib bcrypt)
- [x] `POST /auth/register`
- [x] `POST /auth/login`
- [x] `POST /auth/refresh`
- [x] Auth middleware (FastAPI dependency)
- [x] `GET /auth/me`

**Miért fontos:**
- ✅ Multi-user támogatás alapja
- ✅ API-k védése
- ✅ MCP Server user context-hez kell

---

### **FÁZIS 1: MCP Server Alapok (1 hét)**
**Cél:** MCP Server működik, alapvető tools-okkal

#### 4. MCP Server Setup
**Fájl:** `todos-mcp.md` - Fázis 1-2

**2-3 nap:**
- [ ] MCP Server projekt inicializálása (Python)
- [ ] mcp Python SDK integráció
- [ ] Server setup (stdio transport)
- [ ] Database connection (SQLAlchemy)
- [ ] Alapvető tools:
  - [ ] `mcp_get_project_context` - Projekt kontextus
  - [ ] `mcp_get_resume_context` - Resume context
  - [ ] `mcp_list_features` - Feature lista
  - [ ] `mcp_list_todos` - Todo lista

**Tesztelés:**
- [ ] Cursor-ban MCP Server csatlakoztatása
- [ ] Tool hívások tesztelése
- [ ] Response validálása

---

### **FÁZIS 2: MVP Funkcionalitás (1-2 hét)**
**Cél:** Alapvető workflow működik

#### 5. Feature és Todo Kezelés
**Fájl:** `todos-mcp.md` - Fázis 3-4

**3-4 nap:**
- [ ] `mcp_create_feature` - Feature létrehozás
- [ ] `mcp_create_todo` - Todo létrehozás (feature-hez)
- [ ] `mcp_update_todo_status` - Todo státusz frissítés
- [ ] `mcp_get_feature_todos` - Feature todo-k
- [ ] Feature progress számítás

#### 6. Session Kezelés
**Fájl:** `todos-mcp.md` - Fázis 5

**2-3 nap:**
- [ ] `mcp_start_session` - Session indítás
- [ ] `mcp_update_session` - Session frissítés
- [ ] `mcp_end_session` - Session befejezés + summary
- [ ] Resume Context automatikus frissítés

#### 7. MCP Resources
**Fájl:** `todos-mcp.md` - Fázis 8

**1-2 nap:**
- [ ] `project://{id}/context` resource
- [ ] `project://{id}/resume` resource
- [ ] `feature://{id}` resource

---

### **FÁZIS 3: Optimalizálás (1 hét)**
**Cél:** Teljesítmény és token optimalizálás

#### 8. Caching (Redis)
**Fájl:** `todos-backend.md` - Fázis 5, `todos-mcp.md` - Fázis 9

**2-3 nap:**
- [ ] Redis setup (helyi vagy Azure)
- [ ] Cache service implementálása
- [ ] Project context cache (5 min TTL)
- [ ] Resume context cache (1 min TTL)
- [ ] Feature cache (2 min TTL)
- [ ] Cache invalidation logika

#### 9. Token Optimalizálás
**Fájl:** `todos-mcp.md` - Fázis 9

**1-2 nap:**
- [ ] Lazy loading (csak szükséges resources)
- [ ] Strukturált adatok (ID-k, nem teljes objektumok)
- [ ] Response size minimalizálás

---

### **FÁZIS 4: Multi-User Támogatás (1-2 hét)**
**Cél:** Több felhasználó egyidejű munkavégzése

#### 10. Authorization és Assignment
**Fájl:** `todos-backend.md` - Fázis 3, 4

**3-4 nap:**
- [ ] Role-based access control (RBAC)
- [ ] Project sharing (user_projects)
- [ ] Todo assignment
- [ ] Feature assignment
- [ ] `GET /api/projects/:id/team-dashboard`

#### 11. Optimistic Locking
**Fájl:** `todos-backend.md` - Fázis 4, `todos-database.md` - Fázis 3

**2 nap:**
- [ ] Version mező todos és features táblákban
- [ ] Version check update-nél
- [ ] Conflict error handling

#### 12. Real-time Sync (SignalR)
**Fájl:** `todos-backend.md` - Fázis 6

**2-3 nap:**
- [ ] Azure SignalR Service setup
- [ ] SignalR hub implementálása
- [ ] Todo update broadcasts
- [ ] User activity tracking

---

### **FÁZIS 5: GitHub Integráció (1-2 hét)**
**Cél:** GitHub repository és branch kezelés

#### 13. GitHub API Integráció
**Fájl:** `todos-mcp.md` - Fázis 7

**3-4 nap:**
- [ ] GitHub API connection (@octokit/rest)
- [ ] `mcp_connect_github_repo` - Repo kapcsolat
- [ ] `mcp_create_branch_for_feature` - Branch létrehozás
- [ ] `mcp_link_branch_to_feature` - Branch linkelés
- [ ] `mcp_get_branch_status` - Branch státusz

#### 14. Commit és PR Integráció
**Fájl:** `todos-mcp.md` - Fázis 7

**2-3 nap:**
- [ ] Commit message parsing
- [ ] `mcp_link_todo_to_pr` - PR linkelés
- [ ] `mcp_link_element_to_issue` - Issue linkelés
- [ ] Webhook handler (opcionális)

---

## 🚀 Konkrét Kezdési Terv (Első 2 hét)

### **1. HÉT: Database + Backend Alapok**

**Hétfő-Kedd (2 nap): Database Setup**
```bash
# 1. Prisma schema létrehozása (reference)
# - users, projects, features, todos, stb.

# 2. SQLAlchemy models létrehozása
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Alembic inicializálás
alembic init alembic

# 4. Initial migration
alembic revision --autogenerate -m "init"
alembic upgrade head

# 5. Seed data script
```

**Szerda-Csütörtök (2 nap): Backend API Alapok**
```bash
# 1. Backend projekt setup (már kész)
cd backend
pip install -r requirements.txt

# 2. Alapvető API-k implementálása
# - Projects CRUD
# - Features CRUD
# - Todos CRUD

# 3. FastAPI auto-docs: http://localhost:3000/docs
# 4. API-k tesztelése
```

**Péntek (1 nap): Authentication**
```bash
# 1. JWT service (már kész)
# - python-jose
# - passlib[bcrypt]

# 2. Auth endpoints (már kész)
# - POST /auth/register
# - POST /auth/login
# - POST /auth/refresh
# - GET /auth/me

# 3. Auth middleware (FastAPI dependency)
# 4. API-k védése
```

### **2. HÉT: MCP Server + MVP Funkcionalitás**

**Hétfő-Kedd (2 nap): MCP Server Setup**
```bash
# 1. MCP Server projekt (Python)
cd mcp-server
python3 -m venv venv
source venv/bin/activate
pip install mcp sqlalchemy pydantic

# 2. Server inicializálás
# 3. Alapvető tools:
# - mcp_get_project_context
# - mcp_get_resume_context
# - mcp_list_features
# - mcp_list_todos

# 4. Cursor-ban tesztelés
```

**Szerda-Csütörtök (2 nap): Feature és Todo MCP Tools**
```bash
# 1. Feature tools
# - mcp_create_feature
# - mcp_get_feature
# - mcp_get_feature_todos

# 2. Todo tools
# - mcp_create_todo
# - mcp_update_todo_status
# - mcp_assign_todo

# 3. Feature progress számítás
# 4. Tesztelés Cursor-ban
```

**Péntek (1 nap): Session Kezelés**
```bash
# 1. Session tools
# - mcp_start_session
# - mcp_update_session
# - mcp_end_session

# 2. Resume Context frissítés
# 3. Summary generálás
# 4. End-to-end workflow tesztelés
```

---

## 📊 Progress Tracking

### MVP Definition of Done

**Database:**
- ✅ Core tables létrehozva és migrálva
- ✅ Seed data működik
- ✅ Foreign keys és constraints helyesek

**Backend:**
- ✅ API-k működnek (Projects, Features, Todos)
- ✅ Authentication működik
- ✅ Postman collection tesztelve

**MCP Server:**
- ✅ MCP Server csatlakozik Cursor-hoz
- ✅ Alapvető tools működnek
- ✅ Resources elérhetők
- ✅ End-to-end workflow tesztelve

**Tesztelés:**
- ✅ 1 projekt létrehozása
- ✅ 1 feature létrehozása
- ✅ 3-5 todo létrehozása
- ✅ Session indítása
- ✅ Todo-k frissítése
- ✅ Session befejezése
- ✅ Resume Context frissítése

---

## 🎯 Ajánlott Kezdési Sorrend

### **1. LÉPÉS: Database (todos-database.md - Fázis 1-2)**

**Miért:**
- ✅ Nincs dependency
- ✅ Könnyen tesztelhető
- ✅ Minden más erre épül
- ✅ 2-3 nap alatt kész

**Konkrét feladatok:**
1. ✅ SQLAlchemy models létrehozva
2. Alembic migration inicializálás
3. Initial migration futtatása
4. Seed data script

### **2. LÉPÉS: Backend API Alapok (todos-backend.md - Fázis 1-2)**

**Miért:**
- ✅ Database már kész → használhatjuk
- ✅ API-kkal tesztelhetjük
- ✅ MCP Server erre épül

**Konkrét feladatok:**
1. ✅ Backend projekt setup (Python/FastAPI)
2. ✅ SQLAlchemy integráció
3. ⏳ Alapvető CRUD API-k (Projects, Features, Todos)
4. FastAPI auto-docs tesztelés

### **3. LÉPÉS: MCP Server Alapok (todos-mcp.md - Fázis 1-2)**

**Miért:**
- ✅ Backend API már kész
- ✅ Cursor-ban tesztelhető
- ✅ Látható az eredmény

**Konkrét feladatok:**
1. MCP Server projekt setup
2. Alapvető tools (project context, resume context)
3. Cursor integráció tesztelés

---

## 💡 Gyors Start Script

### Database Setup (5 perc)
```bash
# 1. Docker indítás
docker-compose up -d postgres redis

# 2. SQLAlchemy models (már kész: backend/src/database/models.py)
# 3. Alembic migration
cd backend
alembic upgrade head

# 4. Seed script (később)
```

### Backend Setup (10 perc)
```bash
# 1. Projekt (már kész)
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Dependencies
pip install -r requirements.txt

# 3. Backend indítás
uvicorn src.main:app --reload --port 3000

# 4. API docs: http://localhost:3000/docs
```

### MCP Server Setup (10 perc)
```bash
# 1. Projekt
mkdir mcp-server && cd mcp-server
python3 -m venv venv
source venv/bin/activate

# 2. Dependencies
pip install mcp sqlalchemy pydantic redis

# 3. src/server.py (alap MCP server)
# 4. Cursor MCP config
```

---

## 📝 Következő Lépés

**AJÁNLÁS: Kezdjük a Database-rel!**

1. **Ma:** Prisma projekt setup + core tables
2. **Holnap:** Migration + seed data
3. **Hétfő:** Backend API alapok
4. **Kedd:** MCP Server setup

**Első konkrét feladat:**
- ✅ SQLAlchemy models létrehozva (backend/src/database/models.py)
- ⏳ Alembic migration inicializálás
- ⏳ Initial migration futtatása
- ⏳ Seed data script

---

Ez a roadmap mutatja a logikus fejlesztési sorrendet és a konkrét első lépéseket. A részletes todo listák a `todos-database.md`, `todos-backend.md` és `todos-mcp.md` fájlokban találhatók.

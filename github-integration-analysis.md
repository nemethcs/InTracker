# GitHub integráció, Token használat és Csapatmunka elemzése

## 1. GitHub integráció mélysége

### 1.1. Jelenlegi integrációs lehetőségek

#### 1.1.1. Alapvető integráció (jelenlegi spec)

**Kétirányú szinkronizáció:**
- ✅ Projekt elem ↔ GitHub Issue
- ✅ Todo ↔ GitHub PR
- ✅ Commit ↔ Projekt kontextus
- ✅ Issue státusz → Todo/Element státusz
- ✅ PR merge → Todo "done"

**MCP Tools:**
- `mcp_link_element_to_issue()` - Elem és issue összekapcsolása
- `mcp_link_todo_to_pr()` - Todo és PR összekapcsolása
- `mcp_get_github_issue()` - Issue részletek lekérdezése

#### 1.1.2. Bővíthető integrációs lehetőségek

**1. Automatikus Issue/PR létrehozás:**
```typescript
// Új MCP Tools
mcp_create_github_issue(
  elementId: string,
  title: string,
  body: string,
  labels?: string[]
): GitHubIssue

mcp_create_github_pr(
  todoId: string,
  title: string,
  body: string,
  baseBranch: string,
  headBranch: string
): GitHubPR
```

**2. Webhook-alapú szinkronizáció:**
- GitHub webhook → InTracker Backend
- Issue kommentek → InTracker notes
- PR review comments → Todo notes
- PR status checks → Todo blockers
- Automatikus frissítés valós időben

**3. Branch és commit követés (InTracker workflow-hoz igazítva):**
```typescript
// Branch létrehozás feature alapján
mcp_create_branch_for_feature(
  featureId: string,
  branchName?: string  // Opcionális, ha nincs, AI generálja
): Branch

// Branch linkelés feature-hez
mcp_link_branch_to_feature(
  featureId: string,
  branchName: string
): void

// Aktív branch azonosítása
mcp_get_active_branch(
  projectId: string
): Branch | null

// Feature-hez tartozó branch-ek
mcp_get_feature_branches(
  featureId: string
): Branch[]

// Commit-ok feature alapján
mcp_get_commits_for_feature(
  featureId: string
): Commit[]

// Commit message konvenciók (InTracker-alapú)
// "feat(shopping-cart): Implement cart component [feature:shopping-cart-123]"
// "fix(checkout): Fix payment validation [feature:checkout-456]"
// → Automatikus feature linkelés commit message-ből
```

**Branch naming konvenció (InTracker-alapú):**
```
feature/{feature-slug}              # Feature branch
feature/{feature-slug}-{todo-slug}   # Feature + todo branch
fix/{feature-slug}                  # Bugfix branch
```

**4. GitHub Discussions integráció:**
- ADR dokumentumok ↔ GitHub Discussions
- Architektúra döntések megosztása

**6. GitHub Actions integráció:**
- CI/CD pipeline státusz → Todo blockers
- Test results → Feature progress
- Deployment status → Project status

### 1.2. Branch kezelés InTracker workflow-ban

#### 1.2.1. Branch lifecycle InTracker-ben

**1. Feature indítás → Branch létrehozás:**
```
Felhasználó: "Implementáld a shopping cart funkciót"

AI folyamat:
1. MCP: mcp_create_feature() → Feature létrehozva
2. MCP: mcp_create_branch_for_feature(featureId) → Branch létrehozva
   - Branch név: "feature/shopping-cart" (automatikus generálás)
   - Base branch: "main" (default)
3. AI checkout-olja a branch-t
4. Feature és branch összekapcsolva
```

**2. Todo implementálás → Commit branch-en:**
```
AI implementál egy todo-t:
1. Kód módosítások branch-en
2. Commit message: "feat(shopping-cart): Implement cart component [feature:shopping-cart-123]"
3. MCP: mcp_update_todo_status(todoId, "done")
4. Feature progress frissül
```

**3. PR létrehozás → Branch → PR linkelés:**
```
Amikor minden todo kész vagy részben:
1. AI létrehozza a PR-t
2. MCP: mcp_create_github_pr() → PR létrehozva
3. MCP: mcp_link_todo_to_pr(todoId, prNumber)
4. Branch → PR → Todo → Feature teljes kapcsolat
```

**4. PR merge → Feature "done":**
```
PR merge után:
1. GitHub webhook → InTracker Backend
2. MCP: mcp_update_feature_status(featureId, "done")
3. Minden hozzá tartozó todo "done"
4. Branch törlés (opcionális, automatikus)
```

#### 1.2.2. Branch naming konvenció (InTracker)

**Konvenció:**
```
feature/{feature-slug}              # Feature branch
  Példa: feature/shopping-cart
  Példa: feature/checkout-payment

fix/{feature-slug}                  # Bugfix branch
  Példa: fix/shopping-cart-validation

refactor/{feature-slug}             # Refactoring branch
  Példa: refactor/shopping-cart-state
```

**Automatikus generálás:**
- Feature név → slug konverzió
- Duplikáció ellenőrzés
- Branch létezés ellenőrzés

#### 1.2.3. Commit message konvenció (InTracker)

**Formátum:**
```
{type}({scope}): {description} [feature:{feature-id}]

Típusok:
- feat: Új funkció
- fix: Bugfix
- refactor: Refactoring
- docs: Dokumentáció
- test: Tesztek

Scope: Feature slug vagy modul név

Példák:
feat(shopping-cart): Implement cart component [feature:shopping-cart-123]
fix(checkout): Fix payment validation [feature:checkout-456]
refactor(auth): Simplify JWT handling [feature:auth-789]
```

**Automatikus parsing:**
- Commit message-ből feature ID kinyerése
- Automatikus feature linkelés
- Feature progress frissítés

#### 1.2.4. Branch követés és szinkronizáció

**Aktív branch azonosítás:**
```typescript
// Cursor working directory alapján
mcp_get_active_branch(projectId: string): Branch | null

// Ha branch létezik → Feature azonosítás
// Ha nincs branch → Új feature indítás vagy main branch
```

**Branch státusz követés:**
```typescript
interface BranchStatus {
  name: string;
  featureId: string | null;
  ahead: number;        // Hány commit előrébb
  behind: number;        // Hány commit mögötte
  hasConflicts: boolean;
  lastCommit: Commit;
  todos: Todo[];         // Branch-en lévő todo-k
}
```

**Automatikus szinkronizáció:**
- Branch push → InTracker frissítés
- Branch merge → Feature "done"
- Branch delete → Feature archiválás
- Conflict → Blocker létrehozás

#### 1.2.5. Több branch egy feature-hez

**Forgatókönyv:**
- Nagy feature → Több branch (pl. frontend + backend)
- Feature modulok → Külön branch-ek

**Megoldás:**
```typescript
// Több branch egy feature-hez
mcp_link_branch_to_feature(featureId, "feature/shopping-cart-frontend")
mcp_link_branch_to_feature(featureId, "feature/shopping-cart-backend")

// Feature progress = összes branch progress
// Minden branch PR merge → Feature "done"
```

### 1.3. Integrációs mélység értékelés

**Alapvető integráció: ⭐⭐⭐⭐ (4/5)**
- Kétirányú szinkronizáció működik
- Issue/PR linkelés megoldható
- Manuális létrehozás szükséges (jelenleg)

**Haladó integráció: ⭐⭐⭐⭐ (4/5)**
- Webhook-alapú automatikus szinkronizáció implementálható
- Branch/commit követés InTracker workflow-hoz igazítva
- Automatikus branch létrehozás feature alapján

**Teljes integráció: ⭐⭐⭐⭐⭐ (5/5)**
- Minden GitHub funkció integrálható
- Valós időben szinkronizáció
- Teljes automatizáció

**Következtetés:**
A GitHub integráció **nagyon mélyreható lehet**, mivel:
- GitHub API teljes funkcionalitást nyújt (repository, branches, commits, PRs)
- Webhook rendszer lehetővé teszi a valós idejű szinkronizációt
- MCP protokoll rugalmas, bármilyen tool hozzáadható
- InTracker struktúra jól illeszkedik a GitHub repository és branch koncepcióihoz
- **Branch kezelés központi**: Feature → Branch → PR → Merge workflow
- **Nincs szükség GitHub Projects-re**: InTracker saját projektkezelést nyújt

---

## 2. Token használat hatása a Cursor-nál

### 2.1. Token használat forrásai

#### 2.1.1. MCP Server hívások

**Alapvető műveletek (alacsony token használat):**
- `mcp_get_project_context()` - ~500-1000 tokens
- `mcp_get_resume_context()` - ~200-500 tokens
- `mcp_list_todos()` - ~300-800 tokens
- `mcp_list_features()` - ~400-1000 tokens

**Közepes műveletek:**
- `mcp_get_project_structure()` - ~1000-3000 tokens
- `mcp_get_feature_todos()` - ~500-1500 tokens
- `mcp_search_documents()` - ~500-2000 tokens

**Nagy műveletek:**
- `mcp_read_document()` - ~1000-5000 tokens (dokumentum méretétől függ)
- Teljes projekt kontextus - ~2000-8000 tokens

#### 2.1.2. MCP Resources (automatikus betöltés)

**Resource betöltés token költsége:**
```
project://{id}/context     → ~2000-8000 tokens
project://{id}/resume      → ~500-2000 tokens
project://{id}/structure   → ~1000-5000 tokens
project://{id}/features    → ~1000-4000 tokens
project://{id}/documents   → ~2000-10000 tokens (összes dokumentum)
```

**Probléma:**
- Ha minden resource automatikusan betöltődik → **nagy token használat**
- Nagy projekteknél (100+ todo, 50+ dokumentum) → **10k-20k+ tokens**

### 2.2. Token optimalizálási stratégiák

#### 2.2.1. Lazy Loading

**Probléma megoldás:**
```typescript
// NE: Minden resource automatikusan betöltve
project://{id}/context  // 8000 tokens
project://{id}/features // 4000 tokens
project://{id}/documents // 10000 tokens
// ÖSSZESEN: 22000 tokens minden session-ben

// IGEN: Csak szükséges resource-ok
project://{id}/resume   // 2000 tokens (csak Resume Context)
// További resource-ok csak explicit kérésre
```

**Implementáció:**
- Resume Context mindig betöltve (kis token költség)
- További resource-ok csak explicit MCP tool hívással
- AI dönt, mikor kell teljes kontextus

#### 2.2.2. Kompressziós stratégiák

**1. Strukturált adatok:**
```json
// NE: Teljes szöveg
{
  "description": "Ez egy nagyon hosszú leírás, amely tartalmazza minden részletet..."
}

// IGEN: Strukturált, tömör
{
  "desc": "Shopping cart implementálása",
  "status": "in_progress",
  "todos": ["todo-1", "todo-2"]  // ID-k, nem teljes objektumok
}
```

**2. Incremental updates:**
- Csak változások küldése
- Delta diff formátum

**3. Caching:**
- MCP Server cache-elheti a gyakran használt adatokat
- Csak változások esetén frissítés

#### 2.2.3. Intelligens kontextus kezelés

**Stratégia:**
```typescript
// 1. Session indítás: Csak Resume Context
mcp_start_session() → Resume Context (~2000 tokens)

// 2. Feature munka: Csak releváns feature
mcp_get_feature_todos(featureId) → ~1500 tokens

// 3. Dokumentáció: Csak releváns dokumentumok
mcp_search_documents(query) → ~2000 tokens

// ÖSSZESEN: ~5500 tokens (vs. 22000 tokens)
```

### 2.3. Token használat becslés

#### 2.3.1. Alapvető használat (optimalizált)

**Egy session alatt:**
- Resume Context betöltés: ~2000 tokens
- 3-5 MCP tool hívás: ~3000-5000 tokens
- Dokumentáció olvasás: ~2000-4000 tokens
- **ÖSSZESEN: ~7000-11000 tokens/session**

**Napi használat (8 session):**
- ~56000-88000 tokens/nap
- **Következtetés: Közepes token használat**

#### 2.3.2. Optimalizálatlan használat

**Egy session alatt:**
- Minden resource automatikusan betöltve: ~20000 tokens
- Redundáns hívások: ~5000 tokens
- **ÖSSZESEN: ~25000 tokens/session**

**Napi használat:**
- ~200000 tokens/nap
- **Következtetés: Magas token használat**

### 2.4. Token használat növelésének hatása

#### 2.4.1. Pozitív hatások

**1. Jobb kontextus:**
- AI több információt lát
- Kevesebb találgatás
- Jobb minőségű kód

**2. Kevesebb iteráció:**
- AI elsőre jobb megoldást ad
- Kevesebb "próbáld újra" kérés
- **Végső soron: kevesebb token használat**

**3. Automatikus műveletek:**
- AI automatikusan frissíti a todo-kat
- Nincs manuális bevitel
- **Időmegtakarítás → több produktív munka**

#### 2.4.2. Negatív hatások

**1. Költség:**
- Nagyobb token használat → nagyobb költség
- Cursor Pro: ~$20/hó (korlátozott token)
- Nagy projekteknél problémás lehet

**2. Lassabb válaszidő:**
- Nagy kontextus → lassabb feldolgozás
- Hosszabb várakozási idő

**3. Kontextus limit:**
- Cursor token limit: ~1M tokens
- Nagy projekteknél elérhető a limit

### 2.5. Ajánlások

**1. Optimalizált használat:**
- ✅ Lazy loading
- ✅ Csak szükséges resource-ok
- ✅ Strukturált adatok
- ✅ Caching

**2. Intelligens kontextus:**
- ✅ Resume Context mindig (kis költség, nagy érték)
- ✅ Feature-specifikus kontextus
- ✅ Dokumentáció csak szükség esetén

**3. Monitoring:**
- Token használat követése
- Figyelmeztetések nagy használatnál
- Optimalizálási javaslatok

**Következtetés:**
Az InTracker **közepes token használatot** eredményez optimalizálással, de **jelentősen növelheti a produktivitást**, ami végső soron **kevesebb token használatot** jelent (kevesebb iteráció).

---

## 3. Csapatmunka támogatása nagy projekteken

### 3.1. Jelenlegi képesség (single user)

**Alapvető funkcionalitás:**
- ✅ Egy felhasználó, több projekt
- ✅ Projektváltás
- ✅ Kontextus megőrzés

**Korlátok:**
- ❌ Nincs multi-user támogatás
- ❌ Nincs egyidejű munkavégzés
- ❌ Nincs konfliktus kezelés

### 3.2. Csapatmunka támogatás bővítése

#### 3.2.1. Multi-user architektúra

**Adatbázis bővítés:**
```sql
-- Felhasználók
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    github_username TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Felhasználó-projekt kapcsolatok
CREATE TABLE user_projects (
    user_id UUID REFERENCES users(id),
    project_id UUID REFERENCES projects(id),
    role TEXT CHECK(role IN ('owner', 'editor', 'viewer')),
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, project_id)
);

-- Session ownership
ALTER TABLE sessions ADD COLUMN user_id UUID REFERENCES users(id);

-- Todo assignment
ALTER TABLE todos ADD COLUMN assigned_to UUID REFERENCES users(id);
ALTER TABLE todos ADD COLUMN created_by UUID REFERENCES users(id);
```

#### 3.2.2. Egyidejű munkavégzés

**Probléma:**
- Több fejlesztő dolgozik ugyanazon a projekten
- Konfliktusok lehetnek (todo státusz, feature progress)

**Megoldás:**
```typescript
// Optimistic locking
interface Todo {
  id: string;
  status: TodoStatus;
  version: number; // Version number for conflict detection
  last_modified_by: string;
  last_modified_at: timestamp;
}

// Conflict resolution
mcp_update_todo_status(
  todoId: string,
  status: TodoStatus,
  expectedVersion: number
): Todo | ConflictError
```

**Real-time sync:**
- WebSocket kapcsolat
- Valós idejű frissítések
- "X dolgozik ezen a todo-n" jelzés

#### 3.2.3. Feladat hozzárendelés

**Todo assignment:**
```typescript
mcp_assign_todo(
  todoId: string,
  userId: string
): Todo

mcp_get_my_todos(
  projectId: string,
  userId: string
): Todo[]

// Feature assignment
mcp_assign_feature(
  featureId: string,
  userId: string
): Feature
```

**Automatikus assignment:**
- AI dönt, ki dolgozzon egy todo-n
- Terheléselosztás
- Szakértelem alapján

#### 3.2.4. Csapat kontextus megosztás

**Resume Context megosztás:**
```typescript
interface TeamResumeContext {
  project: Project;
  team_members: {
    user_id: string;
    last_session: SessionSummary;
    active_todos: Todo[];
    current_focus: string;
  }[];
  shared_blockers: Blocker[];
  team_progress: {
    features_in_progress: Feature[];
    completion_rate: number;
  };
}
```

**Csapat dashboard:**
- Ki mit csinál
- Hol vannak blokkolva
- Melyik funkciókban van még munka
- Csapat progress

#### 3.2.5. GitHub integráció csapatmunkához

**1. PR review integráció:**
```typescript
mcp_get_pr_reviews(
  prNumber: number
): PRReview[]

// PR review → Todo notes
// Review comments → Blocker identification
```

**2. Code ownership:**
- GitHub CODEOWNERS → InTracker assignment
- Automatikus todo assignment
- Review assignment

**3. Branch követés (InTracker workflow integráció):**
```typescript
// Branch létrehozás feature indításakor
mcp_create_branch_for_feature(
  featureId: string,
  baseBranch?: string  // Default: main/master
): Branch

// Aktív branch azonosítása (working directory alapján)
mcp_get_active_branch(
  projectId: string
): Branch | null

// Branch linkelés feature-hez
mcp_link_branch_to_feature(
  featureId: string,
  branchName: string
): void

// Feature-hez tartozó branch-ek
mcp_get_feature_branches(
  featureId: string
): Branch[]

// Branch státusz követés
mcp_get_branch_status(
  branchName: string
): BranchStatus  // ahead, behind, conflicts, etc.

// Automatikus branch naming (InTracker konvenció)
// feature/shopping-cart
// feature/checkout-payment
// fix/shopping-cart-validation
```

**Branch workflow InTracker-ben:**
1. Feature indítás → Automatikus branch létrehozás
2. Todo implementálás → Commit branch-en
3. PR létrehozás → Branch → PR linkelés
4. PR merge → Feature "done" státusz
5. Branch törlés → Feature archiválás

**4. Conflict detection:**
- Git merge conflicts → Blocker
- PR conflicts → Todo blocker
- Automatikus észlelés

### 3.3. Nagy projektek támogatása

#### 3.3.1. Skálázhatóság

**Problémák nagy projekteknél:**
- 1000+ todo
- 100+ feature
- 50+ fejlesztő
- Nagy token használat

**Megoldások:**

**1. Pagination:**
```typescript
mcp_list_todos(
  projectId: string,
  filters: TodoFilters,
  page: number,
  pageSize: number
): PaginatedTodos
```

**2. Lazy loading:**
- Csak aktív feature-k betöltése
- Csak assigned todo-k
- Csak releváns dokumentáció

**3. Caching:**
- Redis cache nagy projekteknél
- CDN dokumentációkhoz
- Aggregált statisztikák

**4. Sharding:**
- Projekt modulok szerint
- Feature-k szerint
- Felhasználók szerint

#### 3.3.2. Teljesítmény optimalizálás

**Database indexek:**
```sql
CREATE INDEX idx_todos_project_status ON todos(project_id, status);
CREATE INDEX idx_todos_feature_status ON todos(feature_id, status);
CREATE INDEX idx_todos_assigned ON todos(assigned_to, status);
CREATE INDEX idx_features_project_status ON features(project_id, status);
```

**Query optimalizálás:**
- Aggregált lekérdezések
- Materialized views
- Background jobs statisztikákhoz

#### 3.3.3. Kontextus kezelés nagy projekteknél

**Probléma:**
- Teljes projekt kontextus → 50k+ tokens
- Nem praktikus

**Megoldás:**
```typescript
// Feature-scoped context
mcp_get_feature_context(
  featureId: string
): FeatureContext  // ~5000 tokens

// Module-scoped context
mcp_get_module_context(
  elementId: string
): ModuleContext  // ~3000 tokens

// User-scoped context
mcp_get_my_context(
  userId: string,
  projectId: string
): UserContext  // ~2000 tokens
```

### 3.4. Csapatmunka értékelés

#### 3.4.1. Alapvető támogatás (jelenlegi)

**Single user: ⭐⭐⭐⭐⭐ (5/5)**
- Teljes funkcionalitás
- Optimális token használat
- Gyors működés

**Multi-user: ⭐ (1/5)**
- Nincs támogatás
- Konfliktusok lehetnek
- Nincs koordináció

#### 3.4.2. Bővített támogatás (implementálható)

**Multi-user alap: ⭐⭐⭐ (3/5)**
- Felhasználók kezelése
- Assignment
- Alapvető koordináció

**Csapatmunka: ⭐⭐⭐⭐ (4/5)**
- Real-time sync
- Conflict resolution
- Csapat dashboard
- GitHub integráció

**Nagy projektek: ⭐⭐⭐⭐⭐ (5/5)**
- Skálázhatóság
- Teljesítmény optimalizálás
- Kontextus kezelés
- Pagination, caching

### 3.5. Implementációs prioritás

#### Fázis 1: Alapvető multi-user (MVP)
1. User management
2. Project sharing
3. Todo assignment
4. Basic conflict detection

#### Fázis 2: Csapatmunka
5. Real-time sync
6. Team dashboard
7. Shared Resume Context
8. Collaboration features

#### Fázis 3: Nagy projektek
9. Pagination
10. Caching
11. Performance optimization
12. Advanced context management

#### Fázis 4: GitHub integráció (Repository és Branch fókusz)
13. Branch létrehozás feature alapján
14. Commit message parsing és feature linkelés
15. Branch követés és státusz szinkronizáció
16. PR review integration
17. Code ownership
18. Conflict detection
19. Webhook-alapú automatikus szinkronizáció

### 3.6. Következtetés

**Csapatmunka támogatás:**
- ✅ **Alapvetően implementálható** (user management, assignment)
- ✅ **Haladó funkciók lehetségesek** (real-time sync, team dashboard)
- ✅ **Nagy projektek kezelhetők** (skálázhatóság, optimalizálás)
- ⚠️ **Komplex implementáció** (conflict resolution, real-time sync)

**Nagy projektek:**
- ✅ **Jól kezelhetők** optimalizálással
- ✅ **Token használat kontrollálható** (lazy loading, scoped context)
- ✅ **Teljesítmény megoldható** (caching, pagination)
- ⚠️ **Architektúra fontos** (skálázhatóság tervezés)

---

## 4. Összefoglalás és ajánlások

### 4.1. GitHub integráció

**Mélység: ⭐⭐⭐⭐⭐ (5/5)**
- Teljes GitHub API elérhető
- Webhook-alapú valós idejű szinkronizáció
- Bármilyen GitHub funkció integrálható
- **Ajánlás: Fokozatos bővítés, kezdés webhook-alapú sync-cel**

### 4.2. Token használat

**Hatás: ⭐⭐⭐ (3/5) - Közepes növekedés, de optimalizálható**
- Optimalizált használat: ~7-11k tokens/session
- Optimalizálatlan: ~25k tokens/session
- **Ajánlás: Lazy loading, strukturált adatok, caching**
- **Végső hatás: Pozitív** (kevesebb iteráció → kevesebb token)

### 4.3. Csapatmunka

**Támogatás: ⭐⭐⭐⭐ (4/5) - Jól implementálható**
- Alapvető multi-user: Könnyen implementálható
- Csapatmunka: Lehetséges, de komplex
- Nagy projektek: Kezelhető optimalizálással
- **Ajánlás: Fokozatos implementáció, kezdés user management-tel**

### 4.4. Prioritások

**1. Token optimalizálás (azonnal):**
- Lazy loading implementálása
- Strukturált adatok
- Caching

**2. GitHub integráció bővítés (rövid táv):**
- Branch létrehozás feature alapján
- Commit message parsing és feature linkelés
- Branch követés és státusz szinkronizáció
- Webhook-alapú automatikus szinkronizáció
- Automatikus issue/PR létrehozás

**3. Multi-user támogatás (közép táv):**
- User management
- Assignment
- Basic collaboration

**4. Csapatmunka (hosszú táv):**
- Real-time sync
- Team dashboard
- Advanced collaboration

---

## 5. Fontos megjegyzés: GitHub Projects nincs benne

**Kulcsfontosságú döntés:**
- ❌ **Nincs GitHub Projects integráció** - Az InTracker saját projektkezelést nyújt
- ✅ **Csak Repository és Branch kezelés** - GitHub repository és branch-ek integrálása
- ✅ **InTracker = Projektkezelés** - GitHub = Kód tárolás és verziókezelés

**Miért:**
- InTracker saját projekt struktúrája (Projects, Features, Elements, Todos)
- GitHub Projects redundáns lenne
- Fókusz a repository és branch workflow-on
- Feature → Branch → PR → Merge workflow központi

**GitHub integráció célja:**
- Repository kapcsolat (kód tárolás)
- Branch kezelés (feature-alapú workflow)
- Commit követés (feature linkelés)
- Issue/PR linkelés (todo-k és elemek)
- **NEM projektkezelés** (az InTracker kezeli)

---

Ez a dokumentum részletesen elemzi a GitHub integráció mélységét (repository és branch fókusz), a token használat hatását és a csapatmunka támogatás lehetőségeit az InTracker rendszerben.

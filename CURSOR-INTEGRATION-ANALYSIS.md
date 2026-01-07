# InTracker - Cursor MCP Integráció Elemzés és Javítási Javaslatok

## Áttekintés

Ez a dokumentum elemzi, hogy az InTracker projekt megfelelően fel van-e készítve a Cursor MCP-vel való együttműködésre, és azonosítja a hiányosságokat.

---

## 1. Ötletek (Ideas) Rögzítése és Kezelése

### ✅ Jelenlegi állapot
- **Adatbázis:** `Idea` modell létezik a Prisma sémában és SQLAlchemy modellben
- **Kapcsolat:** `converted_to_project_id` mezővel kapcsolódik a projektekhez

### ❌ Hiányosságok

#### 1.1. Backend API hiányzik
- **Nincs** `idea_controller.py` a backend-ben
- **Nincs** API endpoint az Ideas kezelésére:
  - `GET /api/ideas` - Ötletek listázása
  - `POST /api/ideas` - Új ötlet létrehozása
  - `GET /api/ideas/:id` - Ötlet részletei
  - `PUT /api/ideas/:id` - Ötlet frissítése
  - `DELETE /api/ideas/:id` - Ötlet törlése
  - `POST /api/ideas/:id/convert` - Ötlet → Projekt konverzió

#### 1.2. MCP Tools hiányoznak
- **Nincs** MCP tool az Ideas kezelésére:
  - `mcp_create_idea` - Ötlet létrehozása
  - `mcp_list_ideas` - Ötletek listázása
  - `mcp_get_idea` - Ötlet lekérdezése
  - `mcp_update_idea` - Ötlet frissítése
  - `mcp_convert_idea_to_project` - Ötlet → Projekt konverzió

#### 1.3. Service réteg hiányzik
- **Nincs** `idea_service.py` a backend-ben

### 🔧 Javítási javaslatok

1. **Backend API implementálása:**
   ```python
   # backend/src/api/controllers/idea_controller.py
   # backend/src/services/idea_service.py
   # backend/src/api/schemas/idea_schema.py
   ```

2. **MCP Tools implementálása:**
   ```python
   # mcp-server/src/tools/idea.py
   ```

3. **Idea → Project konverzió automatikus:**
   - Cursor automatikusan konvertálhatja az ötletet projektté
   - Template alapú projekt létrehozás

---

## 2. Projektek 100% Kezelése Cursor MCP-n Keresztül

### ✅ Jelenlegi állapot
- **Lekérdezés:** Van MCP tool projekt kontextus lekérdezésére
- **Resume Context:** Van MCP tool a resume context lekérdezésére
- **Struktúra:** Van MCP tool a projekt struktúrához

### ❌ Hiányosságok

#### 2.1. Projekt létrehozás/frissítés MCP-n keresztül
- **Nincs** MCP tool a projekt létrehozására:
  - `mcp_create_project` - Új projekt létrehozása
  - `mcp_update_project` - Projekt frissítése
  - `mcp_delete_project` - Projekt törlése

#### 2.2. Projekt lista lekérdezés
- **Nincs** MCP tool a projektek listázására:
  - `mcp_list_projects` - Összes projekt listázása (szűrőkkel)

#### 2.3. Projekt kontextus automatikus betöltés
- **Nincs** automatikus projekt azonosítás working directory alapján
- **Nincs** MCP tool a projekt automatikus azonosítására:
  - `mcp_identify_project_by_path` - Projekt azonosítás working directory alapján

### 🔧 Javítási javaslatok

1. **MCP Tools hozzáadása:**
   ```python
   # mcp-server/src/tools/project.py - bővítés
   - mcp_create_project
   - mcp_update_project
   - mcp_list_projects
   - mcp_identify_project_by_path
   ```

2. **Automatikus projekt azonosítás:**
   - Working directory alapján projekt azonosítás
   - GitHub repo URL alapján projekt keresés
   - Projekt könyvtár `.intracker` config fájl alapján

---

## 3. Gyors Kontextus Visszaállítás

### ✅ Jelenlegi állapot
- **Resume Context:** Van MCP tool a resume context lekérdezésére
- **Project Context:** Van MCP tool a teljes projekt kontextushoz

### ❌ Hiányosságok

#### 3.1. Automatikus projekt azonosítás
- **Nincs** mechanizmus, ami automatikusan azonosítja a projektet:
  - Working directory alapján
  - GitHub repo alapján
  - Projekt könyvtár config alapján

#### 3.2. Cursor rules automatikus betöltés
- **Nincs** automatikus betöltés a projekt `cursor_instructions` mezőjéből
- **Nincs** projekt-specifikus `.cursor/rules` fájl generálása/kezelése

### 🔧 Javítási javaslatok

1. **Automatikus projekt azonosítás:**
   ```python
   # mcp-server/src/tools/project.py
   async def handle_identify_project_by_path(path: str) -> dict:
       """Identify project by working directory path."""
       # 1. Check for .intracker/config.json
       # 2. Check for GitHub repo URL
       # 3. Check for project name in path
   ```

2. **Cursor rules automatikus betöltés:**
   - MCP Resource: `intracker://project/{id}/cursor-rules`
   - Automatikus generálás a projekt `cursor_instructions` mezőjéből
   - Projekt könyvtárban `.cursor/rules/intracker-project-rules.mdc` fájl

---

## 4. Cursor Rules - Projekt-Specifikus Munkarend

### ✅ Jelenlegi állapot
- **Adatbázis:** `cursor_instructions` mező létezik a `Project` modellben
- **Rules fájl:** Van `.cursor/rules/intracker-dev-rules.mdc` (fejlesztési szabályok)

### ❌ Hiányosságok

#### 4.1. Projekt-specifikus rules automatikus generálás
- **Nincs** automatikus generálás projekt-specifikus rules fájlból
- **Nincs** MCP Resource a cursor rules-hoz:
  - `intracker://project/{id}/cursor-rules`

#### 4.2. Rules tartalma
- A jelenlegi rules fájl csak **fejlesztési szabályokat** tartalmaz
- **Hiányzik** a projekt-specifikus munkarend:
  - InTracker folyamatos naprakészen tartása
  - GitHub naprakészen tartása MCP-n keresztül
  - Automatikus session kezelés
  - Automatikus todo/funkció frissítés

### 🔧 Javítási javaslatok

1. **Projekt-specifikus rules generálás:**
   ```markdown
   # .cursor/rules/intracker-project-rules.mdc
   # Automatikusan generálva a projekt cursor_instructions mezőjéből
   
   ## InTracker Munkarend
   
   ### Folyamatos Naprakészen Tartás
   - Minden változás automatikusan szinkronizálódik az InTracker-be
   - Session automatikus kezelés
   - Todo/funkció státusz automatikus frissítés
   
   ### GitHub Szinkronizáció
   - GitHub issues/PRs automatikus linkelés
   - Branch követés MCP-n keresztül
   - Commit message alapú kontextus frissítés
   ```

2. **MCP Resource hozzáadása:**
   ```python
   # mcp-server/src/resources/project_resources.py
   Resource(
       uri=f"intracker://project/{id}/cursor-rules",
       name=f"Cursor Rules: {project.name}",
       mimeType="text/markdown"
   )
   ```

3. **Rules fájl automatikus generálás:**
   - Cursor automatikusan generálja a rules fájlt a projekt könyvtárban
   - Frissítés a projekt `cursor_instructions` mezője alapján

---

## 5. GitHub Naprakészen Tartása MCP-n Keresztül

### ✅ Jelenlegi állapot
- **Branch lekérdezés:** Van MCP tool a GitHub branches lekérdezésére
- **Adatbázis:** `GitHubBranch` és `GitHubSync` modellek léteznek

### ❌ Hiányosságok

#### 5.1. Teljes GitHub szinkronizáció
- **Nincs** MCP tool a GitHub issues kezelésére:
  - `mcp_link_element_to_issue` - Element → Issue linkelés
  - `mcp_get_github_issue` - Issue lekérdezése
  - `mcp_create_github_issue` - Issue létrehozása

#### 5.2. PR kezelés
- **Nincs** MCP tool a PR kezelésére:
  - `mcp_link_todo_to_pr` - Todo → PR linkelés
  - `mcp_get_github_pr` - PR lekérdezése
  - `mcp_create_github_pr` - PR létrehozása

#### 5.3. Automatikus szinkronizáció
- **Nincs** automatikus GitHub szinkronizáció:
  - Issue státusz változás → Element/Todo frissítés
  - PR merge → Todo done státusz
  - Commit message alapú kontextus frissítés

#### 5.4. Repository kezelés
- **Nincs** MCP tool a GitHub repo kezelésére:
  - `mcp_connect_github_repo` - Repo kapcsolás
  - `mcp_get_repo_info` - Repo információk

### 🔧 Javítási javaslatok

1. **GitHub MCP Tools bővítése:**
   ```python
   # mcp-server/src/tools/github.py - bővítés
   - mcp_connect_github_repo
   - mcp_get_repo_info
   - mcp_link_element_to_issue
   - mcp_get_github_issue
   - mcp_create_github_issue
   - mcp_link_todo_to_pr
   - mcp_get_github_pr
   - mcp_create_github_pr
   - mcp_sync_github_status
   ```

2. **Automatikus szinkronizáció:**
   - Webhook alapú GitHub események kezelése
   - Periodikus szinkronizáció (cron job)
   - Commit message parsing

---

## 6. Összefoglaló - Hiányzó Funkcionalitások

### Backend API
- [ ] `idea_controller.py` - Ideas kezelés
- [ ] `idea_service.py` - Ideas service réteg
- [ ] `idea_schema.py` - Ideas schemas

### MCP Tools
- [ ] **Ideas:**
  - [ ] `mcp_create_idea`
  - [ ] `mcp_list_ideas`
  - [ ] `mcp_get_idea`
  - [ ] `mcp_update_idea`
  - [ ] `mcp_convert_idea_to_project`

- [ ] **Projects:**
  - [ ] `mcp_create_project`
  - [ ] `mcp_update_project`
  - [ ] `mcp_list_projects`
  - [ ] `mcp_identify_project_by_path`

- [ ] **GitHub:**
  - [ ] `mcp_connect_github_repo`
  - [ ] `mcp_get_repo_info`
  - [ ] `mcp_link_element_to_issue`
  - [ ] `mcp_get_github_issue`
  - [ ] `mcp_create_github_issue`
  - [ ] `mcp_link_todo_to_pr`
  - [ ] `mcp_get_github_pr`
  - [ ] `mcp_create_github_pr`
  - [ ] `mcp_sync_github_status`

### MCP Resources
- [ ] `intracker://project/{id}/cursor-rules` - Cursor rules resource

### Automatizáció
- [ ] Automatikus projekt azonosítás (working directory alapján)
- [ ] Automatikus cursor rules generálás
- [ ] Automatikus GitHub szinkronizáció
- [ ] Automatikus session kezelés (már részben van)

---

## 7. Prioritás szerinti Implementációs Terv

### Fázis 1: Alapvető Funkcionalitások (Kritikus)
1. **Ideas kezelés:**
   - Backend API (`idea_controller.py`, `idea_service.py`)
   - MCP Tools (create, list, get, update, convert)

2. **Projekt kezelés MCP-n:**
   - `mcp_create_project`
   - `mcp_update_project`
   - `mcp_list_projects`
   - `mcp_identify_project_by_path`

### Fázis 2: Kontextus és Automatizáció (Fontos)
3. **Automatikus projekt azonosítás:**
   - Working directory alapján
   - GitHub repo alapján

4. **Cursor rules automatikus generálás:**
   - MCP Resource: `intracker://project/{id}/cursor-rules`
   - Automatikus fájl generálás projekt könyvtárban

### Fázis 3: GitHub Integráció (Kiegészítő)
5. **GitHub teljes szinkronizáció:**
   - Issues kezelés
   - PR kezelés
   - Automatikus szinkronizáció

---

## 8. Következő Lépések

1. **Azonnali teendők:**
   - Ideas backend API implementálása
   - Ideas MCP Tools implementálása
   - Projekt MCP Tools bővítése (create, update, list)

2. **Következő sprint:**
   - Automatikus projekt azonosítás
   - Cursor rules automatikus generálás

3. **Jövőbeli fejlesztések:**
   - GitHub teljes szinkronizáció
   - Webhook alapú automatikus frissítés

---

**Dátum:** 2025-01-05
**Státusz:** Elemzés kész, implementáció szükséges

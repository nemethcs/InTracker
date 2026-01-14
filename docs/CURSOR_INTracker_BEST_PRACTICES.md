# Cursor + InTracker Best Practices Guide

Ez a dokumentum részletes útmutatót ad arról, hogyan használd a Cursor-t az InTracker-rel való projektek hatékony kezeléséhez. Minden lépéshez copy-paste ready példákat találsz, amiket közvetlenül használhatsz.

## 🚀 Quick Start - Első Lépések

### 1. Session Kezdés (KÖTELEZŐ!)

**MINDEN session elején KÖTELEZŐ ezt a tool-t használni:**

```cursor
Use the mcp_enforce_workflow tool to start the session
```

**Vagy közvetlenül a Cursor chat-ben:**
```
mcp_enforce_workflow()
```

**Mit csinál:**
- ✅ Automatikusan azonosítja a projektet
- ✅ Betölti a resume context-et (Last/Now/Blockers/Constraints)
- ✅ Betölti a cursor rules-t
- ✅ Visszaadja a workflow checklist-et

**Visszatérési érték:**
```json
{
  "workflow_enforced": true,
  "project": {
    "id": "project-uuid",
    "name": "Project Name",
    "status": "active"
  },
  "resume_context": {
    "last": {...},
    "now": {
      "todos": [...],
      "active_elements": [...]
    },
    "blockers": [...],
    "constraints": {...}
  },
  "cursor_rules_loaded": true,
  "workflow_checklist": [...],
  "next_todos": [...]
}
```

---

## 📋 Workflow Lépések - Copy-Paste Ready Commands

### 2. Projekt Azonosítás (ha nincs automatikus)

**Ha az `enforce_workflow` nem találta meg a projektet:**

```cursor
Use mcp_identify_project_by_path with path="/Users/yourname/projects/your-project"
```

**Vagy közvetlenül:**
```
mcp_identify_project_by_path(path="/Users/yourname/projects/your-project")
```

---

### 3. Resume Context Lekérése

**Aktuális projekt állapot lekérése:**

```cursor
Use mcp_get_resume_context with projectId="your-project-id"
```

**Vagy közvetlenül:**
```
mcp_get_resume_context(projectId="your-project-id")
```

**Mit tartalmaz:**
- `last`: Utolsó session összefoglaló
- `now`: Következő todo-k, aktív elemek, közvetlen célok
- `blockers`: Blokkolók, amik várnak
- `constraints`: Szabályok, architektúra döntések

---

### 4. Cursor Rules Betöltése

**Projekt specifikus Cursor rules betöltése:**

```cursor
Use mcp_load_cursor_rules with projectId="your-project-id" and projectPath="/Users/yourname/projects/your-project"
```

**Vagy közvetlenül:**
```
mcp_load_cursor_rules(projectId="your-project-id", projectPath="/Users/yourname/projects/your-project")
```

**Mit csinál:**
- Generálja a projekt cursor rules-t
- Elmenti `.cursor/rules/intracker-project-rules.mdc` fájlba
- Visszaadja a teljes tartalmat

---

## 🔀 Branch Ellenőrzés (KRITIKUS!)

### 5. Branch Ellenőrzés Feature Munkához

**MINDIG ellenőrizd a branch-et, mielőtt elkezdesz dolgozni egy feature-n!**

**Terminal command (Cursor terminal):**
```bash
git branch --show-current
```

**Ha feature-n dolgozol, KÖTELEZŐEN:**

**1. Kérdezd le a feature-t:**
```cursor
Use mcp_get_feature with featureId="your-feature-id"
```

**2. Kérdezd le a feature branch-eket:**
```cursor
Use mcp_get_feature_branches with featureId="your-feature-id"
```

**3a. Ha VAN feature branch:**
```bash
git checkout feature/feature-name
git pull origin feature/feature-name
```

**3b. Ha NINCS feature branch:**
```cursor
Use mcp_create_branch_for_feature with featureId="your-feature-id"
```

**Aztán:**
```bash
git checkout feature/feature-name
git pull origin feature/feature-name
```

**4. Ha NEM feature-n dolgozol:**
```bash
git checkout develop
git pull origin develop
```

---

## ✅ Todo Státusz Workflow

### 6. Todo Munkakezdés

**Amikor elkezdesz dolgozni egy todo-n:**

```cursor
Use mcp_update_todo_status with todoId="todo-uuid" and status="in_progress" and expectedVersion=1
```

**Fontos:** Az `expectedVersion` az előző olvasásból jön (optimistic locking).

**Példa teljes flow:**
```cursor
1. Get todo: Use mcp_get_active_todos with projectId="project-uuid" and status="new"
2. Start work: Use mcp_update_todo_status with todoId="todo-uuid" and status="in_progress" and expectedVersion=1
3. Work on implementation...
4. After testing: Use mcp_update_todo_status with todoId="todo-uuid" and status="tested" and expectedVersion=2
5. After merge: Use mcp_update_todo_status with todoId="todo-uuid" and status="done" and expectedVersion=3
```

---

## 🔧 Git Workflow - Copy-Paste Commands

### 7. Git Workflow (KÖTELEZŐ Sorrend!)

**MINDIG kövesd ezt a sorrendet:**

**1. Branch ellenőrzés (lásd fent)**

**2. Munkavégzés közben:**
- Végezd el a kód módosításokat
- Teszteld a változtatásokat
- Ellenőrizd a hibákat

**3. Commit előtt (Terminal commands):**
```bash
git status
git diff
git add -A
git status
```

**4. Commit (Terminal command):**
```bash
git commit -m "feat(scope): Description [feature:feature-uuid]

- [x] Todo item 1
- [x] Todo item 2"
```

**5. Push (Terminal command):**
```bash
git push origin feature/feature-name
```

**6. Todo státusz frissítés (MCP tool):**
```cursor
Use mcp_update_todo_status with todoId="todo-uuid" and status="tested" and expectedVersion=2
```

**7. Merge után (Terminal + MCP):**
```bash
git checkout develop
git pull origin develop
```

```cursor
Use mcp_update_todo_status with todoId="todo-uuid" and status="done" and expectedVersion=3
```

---

## 🛠️ MCP Tool-ok Használati Példák

### 8. Projekt Kontextus Lekérése

**Teljes projekt információ:**

```cursor
Use mcp_get_project_context with projectId="project-uuid"
```

**Nagy projekteknél (optimalizált):**
```cursor
Use mcp_get_project_context with projectId="project-uuid" and featuresLimit=10 and todosLimit=20
```

**Csak összefoglaló:**
```cursor
Use mcp_get_project_context with projectId="project-uuid" and summaryOnly=true
```

---

### 9. Feature Kezelés

**Feature létrehozása:**
```cursor
Use mcp_create_feature with projectId="project-uuid" and name="Feature Name" and description="Feature description"
```

**Feature státusz frissítése:**
```cursor
Use mcp_update_feature_status with featureId="feature-uuid" and status="in_progress"
```

**Feature todo-k lekérése:**
```cursor
Use mcp_get_feature_todos with featureId="feature-uuid"
```

---

### 10. Todo Kezelés

**Todo létrehozása:**
```cursor
Use mcp_create_todo with elementId="element-uuid" and title="Todo Title" and description="Todo description" and featureId="feature-uuid"
```

**Todo státusz frissítése (optimistic locking):**
```cursor
Use mcp_update_todo_status with todoId="todo-uuid" and status="in_progress" and expectedVersion=1
```

**Aktív todo-k lekérése:**
```cursor
Use mcp_get_active_todos with projectId="project-uuid" and status="new"
```

---

### 11. Projekt Setup (Új Projekt)

**1. Projekt létrehozása:**
```cursor
Use mcp_create_project with name="Project Name" and teamId="team-uuid" and description="Project description"
```

**2. File structure parse-olása:**
```cursor
Use mcp_parse_file_structure with projectId="project-uuid" and projectPath="/Users/yourname/projects/your-project" and maxDepth=3
```

**3. GitHub repo kapcsolása:**
```cursor
Use mcp_connect_github_repo with projectId="project-uuid" and owner="github-owner" and repo="repo-name"
```

**4. Cursor rules betöltése:**
```cursor
Use mcp_load_cursor_rules with projectId="project-uuid" and projectPath="/Users/yourname/projects/your-project"
```

---

## ⚠️ Gyakori Hibák és Megoldások

### 12. Rossz Branch-en Dolgozás

**Probléma:** Feature-n dolgozol, de `develop` branch-en vagy.

**Megoldás:**
```bash
# 1. Ellenőrizd a branch-et
git branch --show-current

# 2. Ha rossz branch-en vagy, válts feature branch-re
git checkout feature/feature-name
git pull origin feature/feature-name
```

**Prevenció:** MINDIG ellenőrizd a branch-et munkakezdés előtt!

---

### 13. Todo Státusz Rossz Frissítése

**Probléma:** `tested` státuszra frissítettél, de még nincs tesztelve.

**Megoldás:**
- Csak akkor frissítsd `tested`-ra, ha tényleg tesztelted!
- Workflow: `in_progress` → (implementálás) → `tested` (ha tesztelted) → `done` (ha merge-olódott)

**Példa:**
```cursor
# Implementálás után (még nincs tesztelve)
Use mcp_update_todo_status with todoId="todo-uuid" and status="in_progress" and expectedVersion=1

# Tesztelés után
Use mcp_update_todo_status with todoId="todo-uuid" and status="tested" and expectedVersion=2

# Merge után
Use mcp_update_todo_status with todoId="todo-uuid" and status="done" and expectedVersion=3
```

---

### 14. Commit Message Formátum Hibák

**Probléma:** Rossz commit message formátum.

**Helyes formátum:**
```
{type}({scope}): {description} [feature:{featureId}]

- [x] Todo item 1
- [x] Todo item 2
```

**Típusok:**
- `feat`: Új funkció
- `fix`: Bug javítás
- `refactor`: Kód refaktorálás
- `docs`: Dokumentáció
- `test`: Tesztek
- `chore`: Karbantartási feladatok

**Példa:**
```bash
git commit -m "feat(real-time): Implement SignalR updates [feature:a0441bbc-078b-447c-8c73-c3dd96de8789]

- [x] Integrate SignalR client
- [x] Implement real-time updates"
```

---

### 15. MCP Tool Hiba - Optimistic Locking

**Probléma:** `expectedVersion` hiba todo státusz frissítésnél.

**Megoldás:**
1. Először olvasd be a todo-t:
```cursor
Use mcp_get_active_todos with projectId="project-uuid" and status="in_progress"
```

2. Használd a kapott `version` számot:
```cursor
Use mcp_update_todo_status with todoId="todo-uuid" and status="tested" and expectedVersion={version_from_previous_read}
```

---

## 🎯 Quick Actions - Copy-Paste Ready

### Session Kezdés (Teljes Flow)

```cursor
# 1. Enforce workflow (KÖTELEZŐ!)
Use mcp_enforce_workflow

# 2. Ha nincs projekt, hozd létre
Use mcp_create_project with name="Project Name" and teamId="team-uuid"

# 3. Resume context lekérése
Use mcp_get_resume_context with projectId="project-uuid"

# 4. Cursor rules betöltése
Use mcp_load_cursor_rules with projectId="project-uuid" and projectPath="/Users/yourname/projects/your-project"
```

---

### Feature Munkakezdés (Teljes Flow)

```cursor
# 1. Branch ellenőrzés (Terminal)
git branch --show-current

# 2. Feature lekérése
Use mcp_get_feature with featureId="feature-uuid"

# 3. Feature branch-ek lekérése
Use mcp_get_feature_branches with featureId="feature-uuid"

# 4. Ha nincs branch, hozd létre
Use mcp_create_branch_for_feature with featureId="feature-uuid"

# 5. Válts feature branch-re (Terminal)
git checkout feature/feature-name
git pull origin feature/feature-name

# 6. Feature todo-k lekérése
Use mcp_get_feature_todos with featureId="feature-uuid"

# 7. Todo munkakezdés
Use mcp_update_todo_status with todoId="todo-uuid" and status="in_progress" and expectedVersion=1
```

---

### Git Commit Workflow (Teljes Flow)

```bash
# 1. Branch ellenőrzés
git branch --show-current

# 2. Status ellenőrzés
git status

# 3. Diff átnézése
git diff

# 4. Staging
git add -A

# 5. Status újraellenőrzés
git status

# 6. Commit (helyes formátummal!)
git commit -m "feat(scope): Description [feature:feature-uuid]

- [x] Todo item 1
- [x] Todo item 2"

# 7. Push
git push origin feature/feature-name

# 8. Todo státusz frissítés (MCP tool)
# Use mcp_update_todo_status with todoId="todo-uuid" and status="tested" and expectedVersion=2
```

---

## 📚 További Források

- [MCP Tools Dokumentáció](./MCP_TOOLS.md) - Teljes MCP tool lista
- [Onboarding Flow](./ONBOARDING_FLOW.md) - Felhasználó onboarding
- [Real-time Update Patterns](./REALTIME_UPDATE_PATTERNS.md) - SignalR integráció

---

## 💡 Tippek

1. **MINDIG használd az `mcp_enforce_workflow`-t session elején!**
2. **MINDIG ellenőrizd a branch-et feature munkához!**
3. **MINDIG használd az `expectedVersion`-t todo státusz frissítésnél!**
4. **MINDIG kövesd a git workflow sorrendet!**
5. **MINDIG teszteld a változtatásokat commit előtt!**

---

**Utolsó frissítés:** 2026-01-14
**Verzió:** 1.0

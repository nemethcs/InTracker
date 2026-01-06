# GitHub Integráció - Részletes Működés

## 📋 Áttekintés

Az InTracker GitHub integrációja lehetővé teszi, hogy a projekteket GitHub repository-khoz kapcsoljuk, és a feature-öket branch-ekkel szinkronizáljuk. **Nem** GitHub Projects-et használunk, hanem közvetlenül a repository-t és branch-eket kezeljük.

## 🏗️ Architektúra

### Komponensek

1. **GitHubService** (`backend/src/services/github_service.py`)
   - PyGithub library használata
   - GitHub API kommunikáció
   - Repository, branch, issue, PR műveletek

2. **BranchService** (`backend/src/services/branch_service.py`)
   - Branch-ek kezelése InTracker-ben
   - Feature ↔ Branch kapcsolatok
   - Szinkronizáció GitHub-bal

3. **GitHubController** (`backend/src/api/controllers/github_controller.py`)
   - REST API endpoint-ok
   - Webhook kezelés (jövőbeli)

4. **Database Models**
   - `Project.github_repo_url` - Repository URL
   - `Project.github_repo_id` - Repository ID
   - `GitHubBranch` - Branch tárolás
   - `GitHubSync` - Szinkronizációs státusz

## 🔑 Konfiguráció

### 1. GitHub Token beállítása

```bash
# .env fájlban vagy environment változóként
GITHUB_TOKEN=ghp_your_personal_access_token_here
```

**Token jogosultságok szükségesek:**
- `repo` - Teljes repository hozzáférés
- `workflow` - GitHub Actions (opcionális)

### 2. Token létrehozása

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token (classic)
3. Válaszd ki: `repo` scope
4. Másold ki a tokent és add hozzá a `.env` fájlhoz

## 🔄 Működési folyamat

### 1. Repository csatlakoztatása

**API Endpoint:**
```
POST /github/projects/{project_id}/connect
```

**Request:**
```json
{
  "owner": "username",
  "repo": "repository-name"
}
```

**Folyamat:**
1. ✅ Validálja a felhasználó jogosultságát (owner kell)
2. ✅ Ellenőrzi a GitHub token hozzáférését
3. ✅ Lekéri a repository információkat GitHub API-ból
4. ✅ Frissíti a `Project` táblát:
   - `github_repo_url` = `https://github.com/owner/repo`
   - `github_repo_id` = GitHub repository ID

**Response:**
```json
{
  "id": 123456789,
  "name": "repository-name",
  "full_name": "username/repository-name",
  "owner": "username",
  "private": false,
  "default_branch": "main",
  "url": "https://github.com/username/repository-name"
}
```

### 2. Branch létrehozása Feature-hez

**API Endpoint:**
```
POST /github/branches
```

**Request:**
```json
{
  "feature_id": "uuid-here",
  "branch_name": "feature/shopping-cart",
  "from_branch": "main"
}
```

**Folyamat:**
1. ✅ Lekéri a feature-t és a project-et
2. ✅ Ellenőrzi a project GitHub kapcsolatát
3. ✅ Parse-olja a repository owner/name-t az URL-ből
4. ✅ Létrehozza a branch-et GitHub-on:
   ```python
   # GitHub API hívás
   source_branch = repository.get_branch("main")
   ref = repository.create_git_ref(
       ref="refs/heads/feature/shopping-cart",
       sha=source_branch.commit.sha
   )
   ```
5. ✅ Létrehozza a `GitHubBranch` rekordot az adatbázisban:
   - `project_id` - Projekt ID
   - `feature_id` - Feature ID
   - `branch_name` - Branch neve
   - `last_commit_sha` - Utolsó commit SHA
   - `status` - "active"

**Response:**
```json
{
  "id": "branch-uuid",
  "name": "feature/shopping-cart",
  "sha": "abc123...",
  "feature_id": "feature-uuid",
  "status": "active"
}
```

### 3. Branch-ek listázása

**API Endpoint:**
```
GET /github/projects/{project_id}/branches
GET /github/features/{feature_id}/branches
```

**Folyamat:**
1. ✅ Lekéri a `GitHubBranch` rekordokat az adatbázisból
2. ✅ Szűrhető project_id vagy feature_id alapján
3. ✅ Visszaadja a branch információkat

**Response:**
```json
{
  "branches": [
    {
      "id": "branch-uuid",
      "name": "feature/shopping-cart",
      "sha": "abc123...",
      "feature_id": "feature-uuid",
      "status": "active"
    }
  ],
  "count": 1
}
```

### 4. Branch szinkronizáció

**API Endpoint:**
```
POST /github/projects/{project_id}/sync-branches
```

**Folyamat:**
1. ✅ Lekéri az összes branch-et GitHub API-ból
2. ✅ Összehasonlítja az adatbázisban lévő branch-ekkel
3. ✅ Frissíti a meglévő branch-eket (SHA)
4. ✅ Létrehozza az új branch-eket az adatbázisban

**Használat:**
- Manuális szinkronizáció
- Webhook-alapú automatikus szinkronizáció (jövőbeli)

## 📊 Adatbázis struktúra

### Project tábla

```python
class Project(Base):
    github_repo_url = Column(String, nullable=True)  # "https://github.com/owner/repo"
    github_repo_id = Column(String, nullable=True)   # GitHub repository ID
```

### GitHubBranch tábla

```python
class GitHubBranch(Base):
    id = Column(UUID, primary_key=True)
    project_id = Column(UUID, ForeignKey("projects.id"))
    feature_id = Column(UUID, ForeignKey("features.id"), nullable=True)
    branch_name = Column(String, nullable=False)      # "feature/shopping-cart"
    last_commit_sha = Column(String, nullable=False)  # "abc123..."
    status = Column(String, default="active")        # "active", "merged", "deleted"
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

### GitHubSync tábla (jövőbeli)

```python
class GitHubSync(Base):
    id = Column(UUID, primary_key=True)
    project_id = Column(UUID, ForeignKey("projects.id"))
    sync_type = Column(String)  # "branches", "issues", "prs"
    last_sync_at = Column(DateTime)
    status = Column(String)     # "success", "error"
    error_message = Column(Text, nullable=True)
```

## 🔐 Biztonság és jogosultságok

### Jogosultság ellenőrzés

1. **Repository csatlakoztatás:**
   - Csak **owner** szerepkörrel lehet
   - `project_service.check_user_access(required_role="owner")`

2. **Branch létrehozás:**
   - **editor** vagy **owner** szerepkör kell
   - `project_service.check_user_access(required_role="editor")`

3. **Branch listázás:**
   - Bármilyen hozzáférési szint (owner/editor/viewer)

### GitHub Token validáció

```python
def validate_repo_access(self, owner: str, repo: str) -> bool:
    """Validálja a GitHub token hozzáférését."""
    try:
        repository = self.client.get_repo(f"{owner}/{repo}")
        _ = repository.name  # Próbálja elérni
        return True
    except GithubException:
        return False
```

## 🎯 Használati példák

### 1. Projekt GitHub-hoz csatlakoztatása

```bash
curl -X POST http://localhost:3000/github/projects/{project_id}/connect \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "username",
    "repo": "my-repo"
  }'
```

### 2. Feature branch létrehozása

```bash
curl -X POST http://localhost:3000/github/branches \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "feature_id": "feature-uuid",
    "branch_name": "feature/shopping-cart",
    "from_branch": "main"
  }'
```

### 3. Feature branch-ek lekérdezése

```bash
curl -X GET http://localhost:3000/github/features/{feature_id}/branches \
  -H "Authorization: Bearer {token}"
```

## 🚀 Jövőbeli fejlesztések

### 1. Webhook integráció

**Cél:** Automatikus szinkronizáció GitHub események alapján

**Webhook események:**
- `push` - Branch frissítés → `last_commit_sha` frissítése
- `pull_request` - PR létrehozás/merge → Todo státusz frissítés
- `issues` - Issue létrehozás/lezárás → Element státusz frissítés

**Implementáció:**
```python
@router.post("/webhook")
async def github_webhook(payload: dict):
    event_type = payload.get("action") or payload.get("ref")
    
    if event_type == "push":
        # Frissítsd a branch SHA-t
    elif event_type == "pull_request":
        # Frissítsd a PR státuszt
    elif event_type == "issues":
        # Frissítsd az issue státuszt
```

### 2. Issue és PR integráció

**Cél:** Automatikus Issue/PR létrehozás és linkelés

**Műveletek:**
- Element létrehozás → GitHub Issue automatikus létrehozás
- Todo létrehozás → GitHub PR automatikus létrehozás (feature branch-en)
- Issue kommentek → InTracker notes
- PR review → Todo notes

### 3. Commit message konvenciók

**Cél:** Automatikus feature linkelés commit message-ből

**Formátum:**
```
feat(shopping-cart): Implement cart component [feature:shopping-cart-123]
fix(checkout): Fix payment validation [feature:checkout-456]
```

**Parsing:**
- `[feature:feature-id]` → Automatikus feature linkelés
- `[todo:todo-id]` → Automatikus todo linkelés

### 4. Branch lifecycle kezelés

**Státuszok:**
- `active` - Aktív fejlesztés
- `merged` - Merge-elve main-be
- `deleted` - Törölve GitHub-on

**Automatikus frissítés:**
- PR merge → `status = "merged"`
- Branch törlés → `status = "deleted"`

## ⚠️ Korlátok és megjegyzések

### 1. GitHub API Rate Limit

- **Authenticated:** 5,000 requests/hour
- **Unauthenticated:** 60 requests/hour

**Megoldás:**
- Caching (Redis) használata
- Batch műveletek minimalizálása
- Webhook használata (csökkenti API hívásokat)

### 2. Token biztonság

- **NE** commit-old a tokent a repository-ba
- Használj environment változókat
- Azure Key Vault használata production-ben

### 3. Hiba kezelés

```python
try:
    branch_info = github_service.create_branch(...)
except GithubException as e:
    # GitHub API hiba
    raise HTTPException(status_code=500, detail=str(e))
except ValueError as e:
    # Validációs hiba
    raise HTTPException(status_code=400, detail=str(e))
```

## 📝 Összefoglaló

A GitHub integráció lehetővé teszi:

✅ **Repository kapcsolódás** - Projekt ↔ GitHub repo  
✅ **Branch kezelés** - Feature ↔ Branch automatikus kapcsolat  
✅ **Szinkronizáció** - GitHub ↔ InTracker kétirányú sync  
✅ **Biztonság** - Jogosultság-alapú hozzáférés  
✅ **Skálázhatóság** - Webhook-alapú automatikus frissítés (jövőbeli)

**Következő lépések:**
1. Webhook implementáció
2. Issue/PR automatikus létrehozás
3. Commit message parsing
4. Branch lifecycle automatikus kezelés

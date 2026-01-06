# GitHub Repository Létrehozás - Útmutató

## 📋 Lépések

### 1. Repository létrehozása GitHub-on

1. Menj a **https://github.com/new** oldalra
2. Töltsd ki az adatokat:
   - **Repository name:** `InTracker`
   - **Description:** `AI-driven project management system for Cursor`
   - **Visibility:** Public vagy Private (ahogy szeretnéd)
   - **Initialize repository:**
     - ✅ Add a README file
     - ✅ Add .gitignore (Python)
     - ✅ Choose a license (opcionális)
3. Kattints a **"Create repository"** gombra

### 2. Repository csatlakoztatása az InTracker projekthez

Miután létrehoztad a repository-t, futtasd ezt a parancsot:

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:3000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['tokens']['access_token'])")

# 2. Csatlakoztatás (cseréld ki a PROJECT_ID-t)
PROJECT_ID="a0a187d0-be08-4f29-bb2d-d2c53dd140eb"
OWNER="nemethcs"  # Vagy a te GitHub username-od

curl -X POST http://localhost:3000/github/projects/$PROJECT_ID/connect \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"owner\":\"$OWNER\",\"repo\":\"InTracker\"}"
```

### 3. Alternatíva: GitHub Token frissítése

Ha a token nem rendelkezik megfelelő jogosultságokkal:

1. Menj a **https://github.com/settings/tokens** oldalra
2. Kattints a **"Generate new token (classic)"** gombra
3. Válaszd ki a jogosultságokat:
   - ✅ **repo** - Full control of private repositories
4. Generáld a tokent és másold ki
5. Frissítsd a `.env` fájlban:
   ```bash
   GITHUB_TOKEN=ghp_your_new_token_here
   ```
6. Indítsd újra a Docker konténereket:
   ```bash
   docker-compose restart backend mcp-server
   ```

### 4. Repository automatikus létrehozás (ha a token rendelkezik jogosultsággal)

Ha a token frissítve van, futtasd:

```bash
docker-compose exec -T backend python -c "
from src.services.github_service import github_service
if github_service.client:
    user = github_service.client.get_user()
    try:
        repo = user.create_repo(
            name='InTracker',
            description='AI-driven project management system',
            private=False,
            auto_init=True,
            gitignore_template='Python'
        )
        print(f'✅ Repository létrehozva: {repo.html_url}')
    except Exception as e:
        print(f'❌ Hiba: {e}')
"
```

## ✅ Ellenőrzés

Miután létrehoztad és csatlakoztattad a repository-t:

```bash
# Repository információk
curl -X GET http://localhost:3000/github/projects/{project_id}/repo \
  -H "Authorization: Bearer $TOKEN"

# Branch-ek listázása
curl -X GET http://localhost:3000/github/projects/{project_id}/branches \
  -H "Authorization: Bearer $TOKEN"
```

## 🔗 Hasznos linkek

- GitHub Repository létrehozás: https://github.com/new
- GitHub Token kezelés: https://github.com/settings/tokens
- GitHub API dokumentáció: https://docs.github.com/en/rest

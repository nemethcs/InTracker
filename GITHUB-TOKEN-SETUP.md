# GitHub Token Létrehozás - Részletes Útmutató

## 🔑 Szükséges Jogosultságok (Scopes)

Az InTracker GitHub integrációhoz a következő jogosultságokra van szükség:

### ✅ Kötelező Scope-ok:

1. **`repo`** - Full control of private repositories
   - ✅ Repository létrehozás
   - ✅ Repository olvasás
   - ✅ Branch létrehozás és kezelés
   - ✅ Issue létrehozás és kezelés
   - ✅ Pull Request létrehozás és kezelés
   - ✅ Commit és ref műveletek

### 📋 Használt GitHub API műveletek:

- `create_repo()` - Repository létrehozás
- `get_repo()` - Repository információk lekérdezése
- `create_git_ref()` - Branch létrehozás
- `get_branches()` - Branch-ek listázása
- `get_branch()` - Branch információk
- `create_issue()` - Issue létrehozás
- `create_pull()` - Pull Request létrehozás

**Minden ezekhez a `repo` scope szükséges!**

## 📝 Lépésről lépésre: Token létrehozás

### 1. Lépés: Menj a GitHub Token oldalra

Nyisd meg a böngészőben:
**https://github.com/settings/tokens**

Vagy:
1. GitHub → Jobb felső sarok → **Settings**
2. Bal oldali menü → **Developer settings**
3. **Personal access tokens** → **Tokens (classic)**

### 2. Lépés: Új token generálása

1. Kattints a **"Generate new token"** gombra
2. Válaszd a **"Generate new token (classic)"** opciót
3. GitHub jelszó megerősítés szükséges

### 3. Lépés: Token beállítások

**Note (Megjegyzés):**
```
InTracker - AI-driven project management
```
*(Ez csak egy leírás, segít azonosítani a tokent)*

**Expiration (Lejárat):**
- **90 days** - Ajánlott (biztonságos)
- **No expiration** - Csak ha biztonságos környezetben használod

**Scopes (Jogosultságok):**

✅ **Pipáld be ezt:**
- [x] **`repo`** - Full control of private repositories
  - [x] repo:status
  - [x] repo_deployment
  - [x] public_repo
  - [x] repo:invite
  - [x] security_events

**⚠️ Fontos:** 
- A `repo` scope **minden** al-scope-ot tartalmaz
- Nincs szükség más scope-okra (pl. `workflow`, `admin:repo`)

### 4. Lépés: Token generálása

1. Görgess le az oldal aljára
2. Kattints a **"Generate token"** gombra
3. **⚠️ FONTOS:** Másold ki a tokent **azonnal**, mert csak egyszer látható!
   - Formátum: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 5. Lépés: Token mentése

**Biztonságos módon:**

1. Nyisd meg a `.env` fájlt a projekt root-ban
2. Frissítsd a `GITHUB_TOKEN` értékét:
   ```bash
   GITHUB_TOKEN=ghp_your_token_here
   ```
3. **NE** commit-old a `.env` fájlt! (Már a `.gitignore`-ban van)

### 6. Lépés: Docker konténerek újraindítása

```bash
docker-compose restart backend mcp-server
```

Vagy teljes újraindítás:
```bash
docker-compose down
docker-compose up -d
```

## ✅ Token ellenőrzése

### 1. Backend-ben:

```bash
docker-compose exec -T backend python -c "
from src.services.github_service import github_service
if github_service.client:
    user = github_service.client.get_user()
    print(f'✅ GitHub User: {user.login}')
    print('✅ Token működik!')
else:
    print('❌ GitHub client nincs inicializálva')
"
```

### 2. Repository létrehozás teszt:

```bash
docker-compose exec -T backend python -c "
from src.services.github_service import github_service
if github_service.client:
    user = github_service.client.get_user()
    try:
        # Próbáljuk meg lekérni egy repository-t
        repo = user.get_repo('InTracker')
        print(f'✅ Repository hozzáférés: OK')
        print(f'   URL: {repo.html_url}')
    except:
        print('⚠️  Repository még nem létezik, de a token működik')
        print('   Most már létrehozhatod a repository-t!')
"
```

## 🔒 Biztonsági Tippek

1. **Token védelme:**
   - ❌ NE commit-old a tokent
   - ❌ NE oszd meg publikus helyen
   - ✅ Használj environment változókat
   - ✅ Production-ben használj Azure Key Vault-ot

2. **Token rotáció:**
   - 90 naponta generálj új tokent
   - Töröld a régi tokent

3. **Scope minimalizálás:**
   - Csak a szükséges scope-okat pipáld be
   - Jelenleg csak `repo` kell

## 🐛 Hibaelhárítás

### Hiba: "Resource not accessible by personal access token"

**Ok:** A token nem rendelkezik megfelelő jogosultságokkal.

**Megoldás:**
1. Ellenőrizd, hogy a `repo` scope be van-e pipálva
2. Generálj új tokent `repo` scope-pal
3. Frissítsd a `.env` fájlt
4. Indítsd újra a konténereket

### Hiba: "Bad credentials"

**Ok:** A token helytelen vagy lejárt.

**Megoldás:**
1. Ellenőrizd a token formátumát (kezdődik `ghp_`-vel)
2. Generálj új tokent
3. Frissítsd a `.env` fájlt

### Hiba: "Repository not found"

**Ok:** A repository nem létezik vagy nincs hozzáférésed hozzá.

**Megoldás:**
1. Ellenőrizd, hogy a repository létezik-e
2. Ellenőrizd, hogy van-e hozzáférésed a repository-hoz
3. Public repository esetén csak olvasás működik

## 📚 További információk

- GitHub Token dokumentáció: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token
- GitHub API dokumentáció: https://docs.github.com/en/rest
- Scope-ok listája: https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/scopes-for-oauth-apps

## ✅ Összefoglalás

**Szükséges scope:**
- ✅ `repo` - Full control of private repositories

**Token formátum:**
```
ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Beállítás:**
1. Generálj tokent `repo` scope-pal
2. Másold a `.env` fájlba: `GITHUB_TOKEN=ghp_...`
3. Indítsd újra a Docker konténereket
4. Kész! 🎉

# Cursor MCP Server Beállítás - Útmutató

## 📋 Áttekintés

Az InTracker MCP Server lehetővé teszi, hogy a Cursor AI közvetlenül kommunikáljon az InTracker backend-del, így hozzáférhet a projektekhez, feature-ökhöz, todo-khoz és dokumentumokhoz.

## 🔧 Előfeltételek

1. ✅ Docker konténerek futnak (PostgreSQL, Redis, Backend, MCP Server)
2. ✅ `.env` fájl beállítva a projekt root-ban
3. ✅ MCP Server működik (tesztelhető: `docker-compose logs mcp-server`)

## 📝 Cursor MCP Konfiguráció

### 1. Lépés: Cursor Settings megnyitása

1. Nyisd meg a **Cursor** alkalmazást
2. Menj a **Settings**-be:
   - **macOS:** `Cmd + ,` vagy `Cursor → Settings`
   - **Windows/Linux:** `Ctrl + ,` vagy `File → Preferences → Settings`
3. Keress rá: **"MCP"** vagy **"Model Context Protocol"**

### 2. Lépés: MCP Server konfiguráció hozzáadása

A Cursor MCP konfigurációja általában egy JSON fájlban van. Két módon lehet hozzáadni:

#### Opció A: Cursor Settings UI-n keresztül

1. Settings → **Features** → **Model Context Protocol**
2. Kattints az **"Add Server"** vagy **"Configure Servers"** gombra
3. Add hozzá az InTracker MCP Server konfigurációját

#### Opció B: Konfigurációs fájl szerkesztése

A Cursor MCP konfiguráció általában itt található:

**macOS/Linux/Windows:**
```
~/.cursor/mcp.json
```

**Alternatív helyek (régebbi verziók):**
- macOS: `~/Library/Application Support/Cursor/User/globalStorage/mcp.json`
- Windows: `%APPDATA%\Cursor\User\globalStorage\mcp.json`
- Linux: `~/.config/Cursor/User/globalStorage/mcp.json`

### 3. Lépés: Konfigurációs JSON hozzáadása

**⚠️ FONTOS:** Docker exec **NEM megfelelő** az MCP stdio transport-hoz! Minden híváskor új folyamatot indít, ami megszakítja a kapcsolatot. **Lokális futtatást használj!**

Add hozzá ezt a konfigurációt a `mcp.json` fájlhoz:

```json
{
  "mcpServers": {
    "intracker": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/Users/ncs/Desktop/projects/InTracker/mcp-server",
      "env": {
        "DATABASE_URL": "postgresql://intracker:intracker_dev@localhost:5433/intracker",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379",
        "REDIS_DB": "0"
      }
    }
  }
}
```

**❌ NE használd Docker exec-et (kapcsolat megszakad):**
```json
// ROSSZ - Kapcsolat megszakad
{
  "command": "docker",
  "args": ["exec", "-i", "intracker-mcp-server", "python", "-m", "src.server"]
}
```

### 4. Lépés: Environment változók beállítása

Ha environment változókat szeretnél használni, a Cursor automatikusan betölti a `.env` fájlt, vagy explicit módon add meg:

```json
{
  "mcpServers": {
    "intracker": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/Users/ncs/Desktop/projects/InTracker/mcp-server",
      "env": {
        "DATABASE_URL": "postgresql://intracker:intracker_dev@localhost:5433/intracker",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379",
        "REDIS_DB": "0"
      },
      "envFile": "/Users/ncs/Desktop/projects/InTracker/.env"
    }
  }
}
```

## 🔍 Alternatív: Cursor Settings JSON

Ha a Cursor nem támogatja a fenti formátumot, próbáld meg a Cursor Settings JSON-t:

1. Nyisd meg a Command Palette-t: `Cmd+Shift+P` (macOS) vagy `Ctrl+Shift+P` (Windows/Linux)
2. Írd be: **"Preferences: Open User Settings (JSON)"**
3. Add hozzá:

```json
{
  "mcp.servers": {
    "intracker": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "intracker-mcp-server",
        "python",
        "-m",
        "src.server"
      ]
    }
  }
}
```

## ✅ Ellenőrzés

### 1. MCP Server működés ellenőrzése

```bash
# Docker konténer ellenőrzése
docker-compose ps mcp-server

# Logok ellenőrzése
docker-compose logs mcp-server --tail=50

# Manuális tesztelés
docker-compose exec -T mcp-server python -c "from src.server import server; print('✅ MCP Server OK')"
```

### 2. Cursor-ban ellenőrzés

1. Nyisd meg a Cursor-t
2. Nyisd meg a Command Palette-t: `Cmd+Shift+P` / `Ctrl+Shift+P`
3. Keress rá: **"MCP"** vagy **"Model Context Protocol"**
4. Nézd meg a **"MCP Servers"** listát
5. Az **"intracker"** szervernak **"Connected"** státuszban kell lennie

### 3. MCP Tools tesztelése

A Cursor AI-ben próbáld ki:

```
"Kérlek, listázd az InTracker projekteket"
"Mutasd meg a GitHub Integration Test feature-t"
"Hozz létre egy új todo-t a GitHub Integration Test feature-hez"
```

## 🐛 Hibaelhárítás

### Hiba: "MCP Server not found"

**Ok:** A konfigurációs fájl helytelen vagy hiányzik.

**Megoldás:**
1. Ellenőrizd a konfigurációs fájl elérési útját
2. Ellenőrizd, hogy a `command` és `args` helyesek-e
3. Indítsd újra a Cursor-t

### Hiba: "Connection refused"

**Ok:** A Docker konténer nem fut vagy a MCP Server nem elérhető.

**Megoldás:**
```bash
# Ellenőrizd a konténereket
docker-compose ps

# Indítsd el, ha nem fut
docker-compose up -d mcp-server

# Ellenőrizd a logokat
docker-compose logs mcp-server
```

### Hiba: "Database connection failed"

**Ok:** A DATABASE_URL helytelen vagy a PostgreSQL nem elérhető.

**Megoldás:**
1. Ellenőrizd a `.env` fájlban a `DATABASE_URL`-t
2. Ellenőrizd, hogy a PostgreSQL konténer fut-e: `docker-compose ps postgres`
3. Teszteld a kapcsolatot: `docker-compose exec -T postgres psql -U intracker -d intracker -c "SELECT 1"`

### Hiba: "Module not found"

**Ok:** A Python függőségek nincsenek telepítve.

**Megoldás:**
```bash
# Telepítsd a függőségeket
cd mcp-server
pip install -r requirements.txt

# Vagy Docker-ben
docker-compose exec mcp-server pip install -r requirements.txt
```

## 📚 MCP Server Funkciók

Az InTracker MCP Server a következő funkciókat biztosítja:

### Tools (Műveletek)

**Project:**
- `get_project_context` - Projekt kontextus lekérdezése
- `get_resume_context` - Resume kontextus (folytatás)
- `get_project_structure` - Projekt struktúra
- `get_active_todos` - Aktív todo-k

**Feature:**
- `create_feature` - Feature létrehozása
- `get_feature` - Feature információk
- `list_features` - Feature-ök listázása
- `update_feature_status` - Feature státusz frissítése
- `get_feature_todos` - Feature todo-k
- `get_feature_elements` - Feature elemek
- `link_element_to_feature` - Elem linkelése feature-hez

**Todo:**
- `create_todo` - Todo létrehozása
- `update_todo_status` - Todo státusz frissítése
- `list_todos` - Todo-k listázása
- `assign_todo` - Todo hozzárendelése
- `get_my_todos` - Saját todo-k

**Session:**
- `start_session` - Session indítása
- `update_session` - Session frissítése
- `end_session` - Session befejezése
- `get_session` - Session információk

**Document:**
- `read_document` - Dokumentum olvasása
- `search_documents` - Dokumentumok keresése
- `get_documents_by_type` - Dokumentumok típus szerint
- `create_document` - Dokumentum létrehozása
- `update_document` - Dokumentum frissítése

**GitHub:**
- `connect_github_repo` - GitHub repository csatlakoztatása
- `get_repo_info` - Repository információk
- `create_branch_for_feature` - Branch létrehozása feature-hez
- `get_active_branch` - Aktív branch
- `link_branch_to_feature` - Branch linkelése feature-hez
- `get_feature_branches` - Feature branch-ek
- `get_branch_status` - Branch státusz
- `get_commits_for_feature` - Feature commit-ok

### Resources (Erőforrások)

- `project://{project_id}` - Projekt adatok
- `feature://{feature_id}` - Feature adatok
- `document://{document_id}` - Dokumentum tartalom

## 🔐 Biztonság

- Az `MCP_API_KEY` opcionális, de ajánlott production-ben
- A `GITHUB_TOKEN` csak akkor szükséges, ha GitHub integrációt használsz
- A `DATABASE_URL` tartalmazhat érzékeny adatokat, ne oszd meg!

## 📝 Példa használat

Miután beállítottad az MCP szervert, a Cursor AI-ben használhatod:

```
"Kérlek, mutasd meg az összes projektet"
"Hozz létre egy új feature-t a 'User Authentication' néven"
"Listázd a 'GitHub Integration Test' feature todo-jait"
"Frissítsd a todo státuszát 'done'-ra"
```

## ✅ Összefoglalás

1. ✅ Docker konténerek futnak
2. ✅ MCP Server konfiguráció hozzáadva a Cursor-hoz
3. ✅ Environment változók beállítva
4. ✅ Cursor újraindítva
5. ✅ MCP Server "Connected" státuszban
6. ✅ Tesztelés sikeres

**🔗 További információk:**
- MCP Server README: `mcp-server/README.md`
- GitHub integráció: `GITHUB-INTEGRATION-GUIDE.md`

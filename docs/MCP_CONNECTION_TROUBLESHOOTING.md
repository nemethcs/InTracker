# MCP Connection Troubleshooting Guide

## Probléma: MCP szerver nem csatlakozik / Method Not Allowed / Backend nem indul el

Ha az MCP szerver nem működik (Cursor nem tud csatlakozni, vagy a backend nem indul el), kövesd ezeket a lépéseket:

---

## Gyors megoldás (Quick Fix)

### 1. Ellenőrizd a backend indulását

```bash
docker-compose logs backend --tail=30
```

**Ha ezt a hibát látod:**
```
TypeError: FastApiMCP.__init__() got an unexpected keyword argument 'server'
# vagy
AttributeError: module 'src.api.controllers.mcp_controller' has no attribute 'setup_mcp_server'
```

**Akkor a main.py a probléma!**

### 2. Állítsd vissza az MCP fájlokat a develop ágról

```bash
# Állítsd vissza az MCP controller-t és a main.py-t
git checkout develop -- backend/src/api/controllers/mcp_controller.py
git checkout develop -- backend/src/main.py

# FONTOS: Töröld a setup_mcp hívást a main.py-ból (ha véletlenül megmaradt)
sed -i '' '/mcp_controller.setup_mcp(app)/d' backend/src/main.py
sed -i '' '/Setup MCP server/d' backend/src/main.py

# Indítsd újra a backend-et
docker-compose restart backend
```

### 3. Ellenőrizd, hogy működik-e

```bash
# Nézd meg a backend logokat
docker-compose logs backend --tail=20

# Ha ezt látod, akkor működik:
# "✅ Database migrations completed successfully"
# "INFO:     Application startup complete."

# Teszteld a Cursor-ban:
# @MCP user-intracker_local
```

---

## Mi okozza a problémát?

### A `main.py`-ban hibás MCP setup hívás

**ROSSZ (ne legyen a main.py-ban):**
```python
# Include routers
app.include_router(mcp_controller.router)
...

# Setup MCP server (NE legyen ilyen!)
mcp_controller.setup_mcp(app)
```

**JÓ (így kell):**
```python
# Include routers
app.include_router(mcp_controller.router)
...
# És semmi más MCP-vel kapcsolatos hívás!
```

### A helyes MCP konfiguráció

Az MCP szerver **automatikusan elindul** amikor a `mcp_controller.router` be van include-olva a FastAPI app-ba.

**Nem kell külön setup hívás!**

---

## Mit NE próbálj

❌ **Ne használd a `fastapi-mcp` library-t** - ez FastAPI endpoint-okból generál MCP toolokat, de nekünk már van custom MCP szerverünk!

❌ **Ne próbáld meg módosítani az SSE transport path-ot** - a `/mcp/messages/` működik

❌ **Ne adj hozzá extra POST endpoint-okat** (`/mcp/messages`, `/mcp/messages/`, stb.) - ezek már benne vannak a working verzióban

---

## Részletes debug folyamat

Ha a gyors megoldás nem működik, kövesd ezeket:

### 1. Ellenőrizd a fájlokat

```bash
# Nézd meg mi van a main.py-ban
grep -A5 "mcp_controller.router" backend/src/main.py

# Nem szabad benne lennie:
# - setup_mcp
# - setup_mcp_server
# - FastApiMCP
```

### 2. Ellenőrizd a requirements.txt-et

```bash
grep fastapi-mcp backend/requirements.txt
```

**Ha megtalálta**, töröld ki:
```bash
sed -i '' '/fastapi-mcp/d' backend/requirements.txt
docker-compose build --no-cache backend
```

### 3. Ellenőrizd a mcp_controller.py-t

```bash
head -20 backend/src/api/controllers/mcp_controller.py
```

**Ennek kell lennie az első sorokban:**
```python
"""MCP Server HTTP/SSE transport controller for FastAPI."""
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from starlette.types import Receive, Send, Scope
from mcp.server.sse import SseServerTransport
```

**NEM ez:**
```python
from fastapi_mcp import FastApiMCP  # ❌ ROSSZ!
```

---

## Összefoglalás

**A megoldás 99%-ban:**
1. `git checkout develop -- backend/src/main.py`
2. Töröld a `setup_mcp` hívást
3. `docker-compose restart backend`

**Megjegyzés:** Az MCP controller (`mcp_controller.py`) általában nem okoz problémát, de ha bizonytalan vagy, azt is állítsd vissza a develop ágról.

---

## Kapcsolódó issue-k

- **2026-01-16**: MCP connection broke during backend refactoring - Fixed by reverting main.py to develop branch
  - Root cause: Accidentally added `mcp_controller.setup_mcp(app)` call during fastapi-mcp experimentation
  - Solution: Remove the setup call, MCP router auto-initializes when included

---

**Utolsó frissítés:** 2026-01-16  
**Státusz:** Verified working ✅

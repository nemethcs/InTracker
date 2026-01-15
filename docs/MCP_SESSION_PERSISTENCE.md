# MCP Session Persistence - Redis-based Solution

## 🎯 Probléma

Amikor a backend újraindul (fejlesztés közben vagy deployment során), az MCP kapcsolat megszakad:
- Cursor "Disconnected" állapotba kerül
- Manuálisan kell toggle-ni az MCP kapcsolatot (Settings → MCP → Toggle off/on)
- Ez frusztráló fejlesztés közben és problémás production-ben

## ✅ Megoldás: Redis Session Persistence

A session state-et Redis-ben tároljuk, így a backend restart után is megmaradnak a sessionök.

### Architektúra

```
Cursor → MCP SSE Endpoint → Redis Session Store
                ↓
         Backend restart
                ↓
Cursor → MCP SSE Endpoint → Redis Session Store (session még létezik!)
                ↓
         ✅ Graceful session rehydration
```

### Fő komponensek

1. **`mcp_session_service.py`** - Redis-based session manager
   - Session létrehozás/lekérés/törlés
   - Session TTL: 24 óra
   - Graceful session rehydration
   
2. **`mcp_controller.py`** - Frissített MCP controller
   - Connection ID generálás/kezelés
   - Session persistence használata
   - Graceful reconnection támogatás

### Működés

#### 1. Session létrehozás (első csatlakozás)

```python
# Cursor csatlakozik → új connection_id generálás
connection_id = str(uuid.uuid4())

# Session mentés Redis-be (TTL: 24 óra)
mcp_session_service.create_session(
    connection_id=connection_id,
    metadata={
        "user_id": user_id,
        "api_key_prefix": api_key[:12],
    }
)
```

#### 2. Session rehydration (backend restart után)

```python
# Cursor reconnect → ugyanaz a connection_id
existing_session = mcp_session_service.get_session(connection_id)

if existing_session:
    # ✅ Régi session még létezik → rehydration
    logger.info(f"✅ Rehydrating MCP session: {connection_id}")
    mcp_session_service.update_session_activity(connection_id)
else:
    # Új session létrehozás
    mcp_session_service.create_session(connection_id, metadata)
```

#### 3. Session activity tracking

```python
# Minden MCP kérés → activity frissítés
mcp_session_service.update_session_activity(connection_id)
# Ez meghosszabbítja a TTL-t (24 óra)
```

### Session TTL

- **Alapértelmezett TTL: 24 óra** (86400 másodperc)
- Minden activity frissítés meghosszabbítja a TTL-t
- Redis automatikusan törli az expired sessionöket
- Nincs szükség manuális cleanup-ra

### Előnyök

✅ **Backend restart után nincs Cursor disconnect**
- Session megmarad Redis-ben
- Graceful reconnection
- Nincs szükség manuális toggle-re

✅ **Stabil fejlesztői élmény**
- Backend módosítások után gyors restart
- Cursor automatikusan reconnectel
- Nincs megszakítás a workflow-ban

✅ **Production-ready**
- Scaling: több backend instance is ugyanazt a Redis-t használja
- High availability: Redis persistence/replication
- Monitoring: session metrikák Redis-ben

✅ **Automatikus cleanup**
- Redis TTL automatikusan törli az expired sessionöket
- Nincs szükség háttér cleanup job-ra

### Redis kulcsok

```
mcp:session:{connection_id}
```

Például:
```
mcp:session:a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

### Session struktúra

```json
{
  "connection_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "created_at": "2026-01-15T10:00:00.000000",
  "last_activity_at": "2026-01-15T10:05:00.000000",
  "metadata": {
    "user_id": "user-123",
    "api_key_prefix": "intracker_mcp"
  }
}
```

## 🧪 Tesztelés

### Backend restart teszt

```bash
# 1. Létrehozunk egy test session-t
docker exec -i intracker-backend python3 << EOF
from src.services.mcp_session_service import mcp_session_service
connection_id = "test-session-123"
mcp_session_service.create_session(connection_id, {"test": "restart"})
print(f"✅ Session created: {connection_id}")
EOF

# 2. Backend restart
docker-compose restart backend

# 3. Ellenőrizzük, hogy a session megmaradt-e
docker exec -i intracker-backend python3 << EOF
from src.services.mcp_session_service import mcp_session_service
session = mcp_session_service.get_session("test-session-123")
print(f"✅ Session persisted: {session is not None}")
mcp_session_service.delete_session("test-session-123")
EOF
```

### Session monitoring

```bash
# Összes aktív session listázása
docker exec -i intracker-backend python3 << EOF
from src.services.mcp_session_service import mcp_session_service
sessions = mcp_session_service.get_all_sessions()
print(f"Active sessions: {len(sessions)}")
for session in sessions:
    print(f"  - {session['connection_id'][:8]}... (created: {session['created_at']})")
EOF
```

## 🔧 Konfiguráció

### Redis beállítások

A Redis konfiguráció a `docker-compose.yml`-ben:

```yaml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  command: redis-server --maxmemory 100mb --maxmemory-policy allkeys-lru
```

### Session TTL módosítása

A `backend/src/services/mcp_session_service.py`-ben:

```python
# Session TTL: 24 hours (in seconds)
SESSION_TTL = 86400  # 24 * 60 * 60

# Módosítás:
SESSION_TTL = 43200  # 12 óra
SESSION_TTL = 172800  # 48 óra
```

## 📊 Monitoring és Debug

### Session metrikák

```python
from src.services.mcp_session_service import mcp_session_service

# Összes aktív session
all_sessions = mcp_session_service.get_all_sessions()
print(f"Active sessions: {len(all_sessions)}")

# Session részletek
session = mcp_session_service.get_session(connection_id)
print(f"Created: {session['created_at']}")
print(f"Last activity: {session['last_activity_at']}")
```

### Logok

Az MCP controller részletes logokat ír:

```
🆕 New MCP connection, generated ID: a1b2c3d4...
✅ MCP session created/updated: a1b2c3d4... (TTL: 86400s)
🚀 MCP server running for connection: a1b2c3d4...

# Backend restart után:
🔄 Reconnecting MCP session: a1b2c3d4...
✅ Rehydrating MCP session: a1b2c3d4... (created: 2026-01-15T10:00:00)
```

## 🚀 Future Improvements

### 1. Connection pooling
- Ha több Cursor client csatlakozik ugyanazzal a user_id-val
- Connection pool kezelés

### 2. Session statistics
- Csatlakozási idő tracking
- Tool call statisztikák
- Performance metrikák

### 3. Distributed tracing
- Session ID propagálás minden MCP tool call-ban
- End-to-end tracing Cursor → MCP → Backend → DB

## 📝 Változtatások összefoglalója

### Új fájlok

- `backend/src/services/mcp_session_service.py` - Redis session manager

### Módosított fájlok

- `backend/src/api/controllers/mcp_controller.py` - Session persistence integráció

### Dokumentáció

- `docs/MCP_SESSION_PERSISTENCE.md` - Ez a dokumentum

## ✅ Eredmény

**Az MCP csatlakozás most már stabil backend restart után is!**

- ✅ Session persistence Redis-ben
- ✅ Graceful session rehydration
- ✅ 24 órás session TTL
- ✅ Automatikus cleanup
- ✅ Nincs szükség manuális Cursor toggle-re

**Tesztelve:**
- Backend restart után session megmarad ✅
- Connection rehydration működik ✅
- Redis TTL automatikus expiry működik ✅

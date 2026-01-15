# MCP Hot Reload + Tool Notifications

## 🎯 Probléma

Amikor új MCP tool-t adunk hozzá a szerverhez:
1. **Backend restart** → Tool list frissül, de connection megszakad
2. **Kézi toggle szükséges** a Cursor-ban az új tool láthatóságához

## ✅ Megoldás: Hot Reload + Tool List Changed Notification

Az MCP Python SDK támogatja a `notifications/tools/list_changed` notification-t, ami lehetővé teszi, hogy a Cursor **automatikusan** újrakérje a tool listát **disconnect nélkül**.

### Feltétel

⚠️ **Csak akkor működik, ha a backend folyamat ÉL** (nincs restart)!

- ✅ **Hot reload** (fájl változás → tool reload → backend él) → Notification működik
- ❌ **Backend restart** → Connection megszakad → Notification NEM működik

## Architektúra

```
1. watchfiles figyeli a tool fájlokat
   ↓
2. Fájl változás észlelése (új tool hozzáadva)
   ↓
3. Tool registry újratöltése (backend process él!)
   ↓
4. send_tool_list_changed() hívása
   ↓
5. Cursor megkapja a notification-t
   ↓
6. Cursor automatikusan újrakéri a tool listát
   ↓
7. ✅ Új tool megjelenik - DISCONNECT NÉLKÜL!
```

## Implementáció

### 1. Tool Notification Sender Service

```python
"""src/services/mcp_tool_notification_service.py"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class MCPToolNotificationService:
    """Service for sending MCP tool list changed notifications."""
    
    @staticmethod
    async def notify_tool_list_changed() -> bool:
        """Send tool list changed notification to all connected clients.
        
        This notifies clients that the tool list has changed and they should
        re-fetch the tool list using list_tools().
        
        Returns:
            True if notification was sent successfully, False otherwise.
        """
        try:
            from src.mcp.server import server
            
            # Get the active session from request context
            if not hasattr(server, 'request_context') or server.request_context is None:
                logger.warning("⚠️  No active MCP session - cannot send tool notification")
                return False
            
            session = server.request_context.session
            
            # Send notification using MCP SDK method
            await session.send_tool_list_changed()
            
            logger.info("✅ Tool list changed notification sent to client")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send tool list changed notification: {e}")
            return False
    
    @staticmethod
    async def notify_resource_list_changed() -> bool:
        """Send resource list changed notification to all connected clients."""
        try:
            from src.mcp.server import server
            
            if not hasattr(server, 'request_context') or server.request_context is None:
                logger.warning("⚠️  No active MCP session - cannot send resource notification")
                return False
            
            session = server.request_context.session
            await session.send_resource_list_changed()
            
            logger.info("✅ Resource list changed notification sent to client")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send resource list changed notification: {e}")
            return False
    
    @staticmethod
    async def notify_prompt_list_changed() -> bool:
        """Send prompt list changed notification to all connected clients."""
        try:
            from src.mcp.server import server
            
            if not hasattr(server, 'request_context') or server.request_context is None:
                logger.warning("⚠️  No active MCP session - cannot send prompt notification")
                return False
            
            session = server.request_context.session
            await session.send_prompt_list_changed()
            
            logger.info("✅ Prompt list changed notification sent to client")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send prompt list changed notification: {e}")
            return False


# Global instance
mcp_tool_notification_service = MCPToolNotificationService()
```

### 2. Hot Reload Watcher

```python
"""src/services/mcp_hot_reload_service.py"""
import asyncio
import logging
from pathlib import Path
from typing import Set
from watchfiles import awatch, Change
from src.services.mcp_tool_notification_service import mcp_tool_notification_service

logger = logging.getLogger(__name__)


class MCPHotReloadService:
    """Service for watching tool files and reloading on change."""
    
    def __init__(self, watch_paths: list[str]):
        """Initialize hot reload service.
        
        Args:
            watch_paths: List of directories to watch for changes
        """
        self.watch_paths = watch_paths
        self._running = False
        self._task: asyncio.Task | None = None
    
    async def start(self):
        """Start watching for file changes."""
        if self._running:
            logger.warning("Hot reload service already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._watch_loop())
        logger.info(f"🔥 Hot reload service started, watching: {self.watch_paths}")
    
    async def stop(self):
        """Stop watching for file changes."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 Hot reload service stopped")
    
    async def _watch_loop(self):
        """Watch for file changes and reload tools."""
        try:
            async for changes in awatch(*self.watch_paths):
                if not self._running:
                    break
                
                # Filter for Python files
                python_changes = {
                    (change, path) 
                    for change, path in changes 
                    if path.endswith('.py') and '__pycache__' not in path
                }
                
                if not python_changes:
                    continue
                
                logger.info(f"🔄 Detected changes in {len(python_changes)} file(s)")
                
                # Reload tool registry
                await self._reload_tools(python_changes)
                
                # Send notification to clients
                await mcp_tool_notification_service.notify_tool_list_changed()
                
        except asyncio.CancelledError:
            logger.info("Hot reload watch loop cancelled")
        except Exception as e:
            logger.error(f"❌ Error in hot reload watch loop: {e}", exc_info=True)
    
    async def _reload_tools(self, changes: Set[tuple[Change, str]]):
        """Reload tool registry after file changes.
        
        Args:
            changes: Set of (Change, path) tuples
        """
        try:
            # Import modules to reload
            import importlib
            import sys
            
            # Get list of modules to reload
            modules_to_reload = set()
            for change, path in changes:
                # Convert file path to module path
                if 'src/mcp/tools' in path:
                    rel_path = path.split('src/mcp/tools/')[-1]
                    module_name = rel_path.replace('/', '.').replace('.py', '')
                    modules_to_reload.add(f'src.mcp.tools.{module_name}')
                elif 'src/mcp/server_handlers' in path:
                    rel_path = path.split('src/mcp/server_handlers/')[-1]
                    module_name = rel_path.replace('/', '.').replace('.py', '')
                    modules_to_reload.add(f'src.mcp.server_handlers.{module_name}')
            
            # Reload modules
            for module_name in modules_to_reload:
                if module_name in sys.modules:
                    logger.info(f"♻️  Reloading module: {module_name}")
                    importlib.reload(sys.modules[module_name])
            
            logger.info("✅ Tool registry reloaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to reload tools: {e}", exc_info=True)


# Global instance (initialized on startup)
hot_reload_service: MCPHotReloadService | None = None
```

### 3. Integration with Backend Startup

```python
"""src/main.py - Add to lifespan"""

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    
    # ... existing startup code ...
    
    # Start hot reload service (development only)
    if settings.NODE_ENV == "development":
        from src.services.mcp_hot_reload_service import MCPHotReloadService
        
        watch_paths = [
            str(Path(__file__).parent / "mcp" / "tools"),
            str(Path(__file__).parent / "mcp" / "server_handlers"),
        ]
        
        global hot_reload_service
        hot_reload_service = MCPHotReloadService(watch_paths)
        await hot_reload_service.start()
        logger.info("🔥 MCP hot reload enabled")
    
    yield
    
    # Shutdown: Stop hot reload service
    if settings.NODE_ENV == "development" and hot_reload_service:
        await hot_reload_service.stop()
```

### 4. Requirements

Add to `backend/requirements.txt`:

```txt
watchfiles>=0.21.0  # For hot reload file watching
```

## Használat

### Fejlesztés közben

1. **Backend indítása** (development mode):
   ```bash
   docker-compose up backend
   ```

2. **Új tool hozzáadása** (pl. `src/mcp/tools/new_feature.py`):
   ```python
   from mcp.types import Tool
   
   def get_new_tool() -> Tool:
       """New tool definition."""
       return Tool(
           name="new_tool",
           description="A brand new tool",
           inputSchema={
               "type": "object",
               "properties": {},
           }
       )
   ```

3. **Regisztráció** (`src/mcp/server.py`):
   ```python
   from src.mcp.tools import new_feature
   
   @server.list_tools()
   async def list_tools() -> list[Tool]:
       return [
           # ... existing tools ...
           new_feature.get_new_tool(),  # ← Új tool
       ]
   ```

4. **Automatikus frissítés**:
   - watchfiles észleli a változást
   - Tool registry újratöltődik
   - Notification küldése: `notifications/tools/list_changed`
   - Cursor automatikusan újrakéri a tool listát
   - ✅ Új tool megjelenik - **DISCONNECT NÉLKÜL!**

## Limitációk

### ⚠️ Csak fejlesztésben használható

- **Development**: Hot reload + notification működik ✅
- **Production**: Nem ajánlott (stability, security)

### ❌ Backend restart esetén NEM működik

- Backend restart → SSE connection megszakad
- Notification NEM küldhető (nincs aktív connection)
- Kell manuális toggle a Cursor-ban

### ✅ Mit old meg

| Scenario                      | Backend restart | Hot Reload működik? | Notification? | Toggle? |
|-------------------------------|-----------------|---------------------|---------------|---------|
| **Backend restart**           | ✅ Igen          | ❌ Nem              | ❌ Nem        | ✅ Kell |
| **Új tool (backend él)**      | ❌ Nem           | ✅ Igen             | ✅ Igen       | ❌ Nem! |

## Monitoring

### Logok

```bash
# Hot reload események
docker-compose logs backend | grep "Hot reload\|Tool list changed\|Reloading module"
```

Példa logok:

```
🔥 Hot reload service started, watching: ['src/mcp/tools', 'src/mcp/server_handlers']
🔄 Detected changes in 1 file(s)
♻️  Reloading module: src.mcp.tools.new_feature
✅ Tool registry reloaded successfully
✅ Tool list changed notification sent to client
```

### Cursor logok

```bash
# Cursor MCP logok
tail -f ~/Library/Logs/Claude/mcp*.log | grep "tools/list_changed\|list_tools"
```

## Jövőbeli fejlesztések

### 1. Smart reload
- Csak a változott modulok reload-ja
- Dependency graph analízis

### 2. Graceful error handling
- Ha reload sikertelen, rollback az előző verzióra
- Error notification küldése a client-nek

### 3. Production-ready hot reload
- Blue-green deployment
- Canary releases
- Zero-downtime tool updates

## Összefoglalás

✅ **Hot Reload + Notifications = Gyorsabb fejlesztés**

- Új tool hozzáadása → **AUTOMATIKUS** client frissítés
- Nincs backend restart szükséges
- Nincs manuális toggle a Cursor-ban
- **Session persistence** továbbra is működik (backend restart esetén)

**Használat**:
- Development: ✅ Ajánlott
- Production: ⚠️ Nem ajánlott (stability concerns)

**Limitáció**:
- Backend restart esetén továbbra is kell toggle (ezt nem tudjuk megoldani SSE-vel)

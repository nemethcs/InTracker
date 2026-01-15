"""MCP server section for cursor rules."""
from ..rules_section import RulesSection


def create_mcp_server_section() -> RulesSection:
    """Create MCP server section."""
    return RulesSection(
        name="mcp_server",
        content="""### MCP Server Connection & Auto-Reconnect

**Automatic Reconnection:**
- Cursor MCP client **automatically reconnects** when backend restarts
- No manual reload needed after backend restart
- Connection is handled gracefully - "terminated: other side closed" is normal during restart

**Manual Reload (only needed for new tools/resources):**
- After adding new MCP tools/resources → Cursor Settings → MCP Servers → Reload connection
- Or restart Cursor to reload MCP connections
- **Note:** Backend restart alone does NOT require manual reload - auto-reconnect handles it

### Code Rebuild Requirements

**When to rebuild/restart:**
- **Backend:** After adding new files, modules, or imports → `docker-compose restart backend`
  - MCP connection will auto-reconnect (no manual action needed)
- **MCP Server:** After adding new tools, resources, or imports → `docker-compose restart mcp-server` + **user reload**
  - New tools/resources require manual reload in Cursor
- **Frontend:** Auto-reloads with Vite (no restart needed)

**Always check logs after restart:**
- `docker-compose logs backend --tail=50`
- `docker-compose logs mcp-server --tail=50`
""",
        conditions={"technology_tags": "mcp"}
    )

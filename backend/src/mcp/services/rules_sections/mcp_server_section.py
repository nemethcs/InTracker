"""MCP server section for cursor rules."""
from ..rules_section import RulesSection


def create_mcp_server_section() -> RulesSection:
    """Create MCP server section."""
    return RulesSection(
        name="mcp_server",
        content="""### MCP Server Reload (CRITICAL)

**After restarting MCP server:**
1. MCP server restart: `docker-compose restart mcp-server`
2. **User MUST reload MCP connection in Cursor:**
   - Cursor Settings → MCP Servers → Reload connection
   - Or restart Cursor to reload MCP connections
3. **Without reload, new MCP tools/resources won't be available!**

### Code Rebuild Requirements

**When to rebuild/restart:**
- **Backend:** After adding new files, modules, or imports → `docker-compose restart backend`
- **MCP Server:** After adding new tools, resources, or imports → `docker-compose restart mcp-server` + **user reload**
- **Frontend:** Auto-reloads with Vite (no restart needed)

**Always check logs after restart:**
- `docker-compose logs backend --tail=50`
- `docker-compose logs mcp-server --tail=50`
""",
        conditions={"technology_tags": "mcp"}
    )

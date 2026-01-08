"""Docker section for cursor rules."""
from ..rules_section import RulesSection


def create_docker_section() -> RulesSection:
    """Create docker section."""
    return RulesSection(
        name="docker",
        content="""### Docker Setup

```yaml
# docker-compose.yml
services:
{DOCKER_SERVICES}
```

**Commands:**
- Start: `docker-compose up -d`
- Stop: `docker-compose down`
- Restart service: `docker-compose restart [service]`
- Reset: `docker-compose down -v && docker-compose up -d`
- Logs: `docker-compose logs -f [service]`
- Check status: `docker-compose ps`
- Health check: `curl http://localhost:3000/health`

**Important:** After code changes, restart the affected service:
{BACKEND_RESTART_INFO}
{FRONTEND_RESTART_INFO}
{MCP_RESTART_INFO}
""",
        conditions={"technology_tags": "docker"}
    )

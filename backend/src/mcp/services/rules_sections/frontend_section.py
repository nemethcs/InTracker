"""Frontend section for cursor rules."""
from ..rules_section import RulesSection


def create_frontend_section() -> RulesSection:
    """Create frontend section."""
    return RulesSection(
        name="frontend",
        content="""### Frontend Development

**Frontend changes:** 
  - Auto-reloads with Vite (no restart needed)
  - If issues: `docker-compose restart frontend`
  - Dev server: `http://localhost:5173`
  - Check console for errors
  - Test UI interactions
""",
        conditions={"technology_tags": ["react", "vue", "angular", "svelte", "frontend"]}
    )

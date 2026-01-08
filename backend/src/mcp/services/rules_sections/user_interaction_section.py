"""User interaction section for cursor rules."""
from ..rules_section import RulesSection


def create_user_interaction_section() -> RulesSection:
    """Create user interaction section."""
    return RulesSection(
        name="user_interaction",
        content="""### When to Ask the User

**ALWAYS ask the user before:**
1. **Creating new projects** - User must approve project creation
2. **Deploying to production** - Never deploy without explicit user approval
3. **Making breaking changes** - Ask if breaking changes are acceptable
4. **Deleting data** - Never delete without explicit confirmation
5. **Changing architecture** - Major architectural decisions need approval
6. **External API calls** - Ask before making external API calls (costs, rate limits)
7. **Long-running operations** - Inform user about operations that take >30 seconds

**NEVER ask the user for:**
1. **Routine development tasks** - Just do them (implementing todos, fixing bugs)
2. **InTracker updates** - Automatically update todos/features as you work
3. **GitHub maintenance** - Keep GitHub synced automatically
4. **Code formatting** - Use linters/formatters automatically
5. **Testing** - Test your changes automatically
6. **Service restarts** - Restart services when needed automatically
"""
    )

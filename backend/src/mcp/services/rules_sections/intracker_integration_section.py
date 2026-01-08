"""InTracker integration section for cursor rules."""
from ..rules_section import RulesSection


def create_intracker_integration_section() -> RulesSection:
    """Create InTracker integration section."""
    return RulesSection(
        name="intracker_integration",
        content="""### InTracker Integration (MANDATORY)

**ALWAYS use InTracker to track progress - this is NOT optional!**

**Todo Management:**
1. **Create todos:** `mcp_create_todo(elementId, title, description, featureId?, priority?)`
2. **Update status:** `mcp_update_todo_status(todoId, status, expectedVersion?)`
   - Statuses: `new` → `in_progress` → `tested` → `done`
   - **CRITICAL:** Use optimistic locking with `expectedVersion` to prevent conflicts
   - **Workflow rules:**
     - `new`: Not started yet
     - `in_progress`: Currently working on it
     - `tested`: Implemented and tested, but NOT in dev branch yet
     - `done`: Tested AND merged to dev branch (only after merge!)

**Feature Management:**
- Track features: `mcp_update_feature_status(featureId, status)`
- Feature statuses: `new` → `in_progress` → `tested` → `done`
- Feature progress auto-calculated from todos

**Session Management:**
- Start session: `mcp_start_session(projectId, goal, featureIds?)`
- Update session: `mcp_update_session(sessionId, completedTodos, completedFeatures, notes)`
- End session: `mcp_end_session(sessionId, summary?)`
"""
    )

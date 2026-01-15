"""InTracker integration section for cursor rules."""
from ..rules_section import RulesSection


def create_intracker_integration_section() -> RulesSection:
    """Create InTracker integration section."""
    return RulesSection(
        name="intracker_integration",
        content="""### InTracker Integration (MANDATORY)

**ALWAYS use InTracker to track progress - this is NOT optional!**

**Language Requirements (CRITICAL):**
- **{LANG:language_requirement}**
- **{LANG:language_requirement_detail}**
- **{LANG:language_examples}**

**Todo Management:**
1. **Create todos:** `mcp_create_todo(elementId, title, description, featureId?, priority?)`
   - **{LANG:todo_language_note}**
2. **Update status:** `mcp_update_todo_status(todoId, status, expectedVersion?)`
   - Statuses: `new` → `in_progress` → `tested` → `done`
   - **CRITICAL:** Use optimistic locking with `expectedVersion` to prevent conflicts
   - **Workflow rules:**
     - `new`: Not started yet
     - `in_progress`: Currently working on it
     - `tested`: Implemented and tested, but NOT in dev branch yet
     - `done`: Tested AND merged to dev branch (only after merge!)

**If user requests new work on a feature:**
   - **CRITICAL: You work BOTH locally (git commands) AND via MCP (InTracker tracking)!**
   - Create todo (MCP): `mcp_create_todo(elementId, title, description, featureId?, priority?)`
   - Update status (MCP): `mcp_update_todo_status(todoId, "in_progress", expectedVersion)`
   - Implement changes (LOCAL - edit files, test)
   - Commit (LOCAL): `git commit -m "feat(scope): description [feature:featureId]"`
   - Push (LOCAL): `git push origin feature/{feature-name}`
   - Update status (MCP): `mcp_update_todo_status(todoId, "tested", expectedVersion)` (only if tested!)
   - After merge: `mcp_update_todo_status(todoId, "done", expectedVersion)` (only after tested AND merged!)
   - **REMEMBER: Git commands run LOCALLY, InTracker updates via MCP!**

**Feature Management:**
- **Create features:** `mcp_create_feature(projectId, name, description, elementIds?)`
  - **{LANG:feature_language_note}**
- Track features: `mcp_update_feature_status(featureId, status)`
- Feature statuses: `new` → `in_progress` → `tested` → `done`
- Feature progress auto-calculated from todos

**Idea Management:**
- **Create ideas:** `mcp_create_idea(title, teamId, description, status?, tags?)`
  - **{LANG:idea_language_note}**

**Session Management:**
- Start session: `mcp_start_session(projectId, goal, featureIds?)`
- Update session: `mcp_update_session(sessionId, completedTodos, completedFeatures, notes)`
- End session: `mcp_end_session(sessionId, summary?)`
"""
    )

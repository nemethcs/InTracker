"""Cursor Rules Generator Service - Dynamic rules generation based on project configuration."""
from typing import Dict, List, Optional, Set
from datetime import datetime
from uuid import UUID
from src.database.models import Project


class RulesSection:
    """Represents a rules section that can be conditionally included."""
    
    def __init__(self, name: str, content: str, conditions: Optional[Dict] = None):
        self.name = name
        self.content = content
        self.conditions = conditions or {}
    
    def should_include(self, project: Project) -> bool:
        """Check if this section should be included based on project configuration."""
        if not self.conditions:
            return True
        
        # Check technology tags
        if "technology_tags" in self.conditions:
            required_tags = self.conditions["technology_tags"]
            if isinstance(required_tags, str):
                required_tags = [required_tags]
            project_tags = [tag.lower() for tag in (project.technology_tags or [])]
            if not any(tag.lower() in project_tags for tag in required_tags):
                return False
        
        # Check tags
        if "tags" in self.conditions:
            required_tags = self.conditions["tags"]
            if isinstance(required_tags, str):
                required_tags = [required_tags]
            project_tags = [tag.lower() for tag in (project.tags or [])]
            if not any(tag.lower() in project_tags for tag in required_tags):
                return False
        
        # Check status
        if "status" in self.conditions:
            if project.status not in self.conditions["status"]:
                return False
        
        return True


class RulesGenerator:
    """Generates cursor rules dynamically based on project configuration."""
    
    def __init__(self):
        self.sections: List[RulesSection] = []
        self._register_default_sections()
    
    def _register_default_sections(self):
        """Register default rules sections."""
        
        # Core workflow section (always included)
        self.sections.append(RulesSection(
            name="core_workflow",
            content="""### Development Workflow (MANDATORY)

**Every agent MUST follow this workflow:**

1. **Project Identification (first time only):**
   - Use `mcp_identify_project_by_path` or `mcp_list_projects`
   - If no project exists, create: `mcp_create_project`
   - Save project ID for session

2. **Resume Context & Cursor Rules (first time only):**
   - Get resume context: `mcp_get_resume_context(projectId)`
     - Shows: Last session, next todos, active elements, blockers, constraints
   - Load cursor rules: `mcp_load_cursor_rules(projectId)`
     - Only needed first time or when rules change
     - Rules are saved to `.cursor/rules/intracker-project-rules.mdc`

3. **Work on Next Todo:**
   - Get next todos from resume context
   - Update status: `mcp_update_todo_status(todoId, "in_progress")`
   - Implement changes
   - Check for errors: `read_lints` tool
   - Fix syntax/import errors
   - Restart affected service if needed
   - Test functionality

4. **Update Todo Status:**
   - After implementation: `mcp_update_todo_status(todoId, "tested")` (only if tested!)
   - After merge to dev: `mcp_update_todo_status(todoId, "done")` (only after tested AND merged!)

5. **Git Workflow (MANDATORY - See detailed Git Workflow section below):**
   - Before work: Check branch, create feature branch if needed, pull latest
   - During work: Make changes, test, fix errors
   - Before commit: Check status, review changes, stage files
   - Commit: Use format `{type}({scope}): {description} [feature:{featureId}]`
   - After commit: Push to remote, update todo to `tested` (if tested)
   - After merge: Update todo to `done` (only after tested AND merged!)

6. **GitHub Maintenance (MANDATORY):**
   - Keep GitHub up-to-date with local changes
   - Link todos to GitHub issues: `mcp_link_element_to_issue(elementId, issueNumber)`
   - Link PRs to todos: `mcp_link_todo_to_pr(todoId, prNumber)`
   - Create feature branches: `mcp_create_branch_for_feature(featureId)`
   - Link branches to features: `mcp_link_branch_to_feature(featureId, branchName)`

6. **Git Workflow (MANDATORY - Follow this order!):**
   - **Before starting work:**
     - Check current branch: `git branch --show-current`
     - If working on a feature, ensure you're on the feature branch: `git checkout feature/{feature-name}`
     - If no feature branch exists, create it: `mcp_create_branch_for_feature(featureId)`
     - Pull latest changes: `git pull origin {branch-name}`
   
   - **During work:**
     - Make code changes
     - Test your changes
     - Check for errors: `read_lints` tool
     - Fix any issues
   
   - **Before committing:**
     - Check git status: `git status`
     - Review changes: `git diff`
     - Stage all changes: `git add -A`
     - Verify staged changes: `git status`
   
   - **Commit (MANDATORY format):**
     - Format: `{type}({scope}): {description} [feature:{featureId}]`
     - Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`
     - Scope: Feature slug or module name
     - Include completed todos in commit message body:
       ```
       {type}({scope}): {description} [feature:{featureId}]
       
       - [x] Todo item 1
       - [x] Todo item 2
       ```
     - Example: `git commit -m "feat(real-time): Implement SignalR updates [feature:a0441bbc-078b-447c-8c73-c3dd96de8789]"`
   
   - **After committing:**
     - Push to remote: `git push origin {branch-name}`
     - Update todo status to `tested`: `mcp_update_todo_status(todoId, "tested")` (only if tested!)
     - Link todo to PR if PR exists: `mcp_link_todo_to_pr(todoId, prNumber)`
   
   - **After merge to dev:**
     - Update todo status to `done`: `mcp_update_todo_status(todoId, "done")` (only after tested AND merged!)
     - Switch back to dev: `git checkout develop`
     - Pull latest: `git pull origin develop`
   
   **CRITICAL Git Rules:**
   - **NEVER commit without testing first!**
   - **NEVER commit to main/master directly!** Always use feature branches
   - **ALWAYS check git status before committing** to avoid committing wrong files
   - **ALWAYS use the commit message format** with feature ID
   - **ALWAYS push after committing** to keep remote in sync
   - **ALWAYS update todo status** after committing (tested) and after merge (done)
   - **NEVER mark todo as `done`** until it's tested AND merged to dev branch!
"""
        ))
        
        # Git Workflow section (always included if GitHub repo connected)
        self.sections.append(RulesSection(
            name="git_workflow",
            content="""### Git Workflow (MANDATORY)

**CRITICAL: Follow this exact order for every change!**

#### 1. Before Starting Work

```bash
# Check current branch
git branch --show-current

# If working on a feature, ensure you're on the feature branch
git checkout feature/{feature-name}

# If no feature branch exists, create it via MCP:
# mcp_create_branch_for_feature(featureId)

# Pull latest changes
git pull origin {branch-name}
```

#### 2. During Work

- Make code changes
- Test your changes
- Check for errors: `read_lints` tool
- Fix any issues
- Update todo status: `mcp_update_todo_status(todoId, "in_progress")`

#### 3. Before Committing

```bash
# Check git status
git status

# Review changes
git diff

# Stage all changes
git add -A

# Verify staged changes
git status
```

#### 4. Commit (MANDATORY Format)

**Format:**
```
{type}({scope}): {description} [feature:{featureId}]

- [x] Todo item 1
- [x] Todo item 2
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring
- `docs`: Documentation
- `test`: Tests
- `chore`: Maintenance tasks

**Examples:**
```bash
git commit -m "feat(real-time): Implement SignalR updates [feature:a0441bbc-078b-447c-8c73-c3dd96de8789]

- [x] Integrate SignalR client
- [x] Implement real-time updates"
```

#### 5. After Committing

```bash
# Push to remote
git push origin {branch-name}

# Update todo status to tested (only if tested!)
mcp_update_todo_status(todoId, "tested")

# Link todo to PR if PR exists
mcp_link_todo_to_pr(todoId, prNumber)
```

#### 6. After Merge to Dev

```bash
# Switch back to dev
git checkout develop

# Pull latest
git pull origin develop

# Update todo status to done (only after tested AND merged!)
mcp_update_todo_status(todoId, "done")
```

#### Git Rules (CRITICAL)

**ALWAYS:**
- ✅ Check git status before committing
- ✅ Use feature branches (never commit to main/master directly)
- ✅ Use the commit message format with feature ID
- ✅ Push after committing
- ✅ Update todo status after committing (tested) and after merge (done)
- ✅ Test before committing

**NEVER:**
- ❌ Commit without testing first
- ❌ Commit to main/master directly
- ❌ Commit without checking git status
- ❌ Mark todo as `done` until it's tested AND merged to dev branch
- ❌ Skip pushing after committing
- ❌ Commit with wrong message format
"""
            , conditions={"has_github_repo": True}
        ))
        
        # Docker section (if docker in technology_tags)
        self.sections.append(RulesSection(
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
        ))
        
        # MCP Server section (if mcp in technology_tags)
        self.sections.append(RulesSection(
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
        ))
        
        # Frontend section (if react, vue, angular, etc. in technology_tags)
        self.sections.append(RulesSection(
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
        ))
        
        # GitHub section (if github_repo_url exists)
        self.sections.append(RulesSection(
            name="github",
            content="""### GitHub Branch Strategy

**Branch naming:**
- Feature branches: `feature/{{feature-name}}`
- Fix branches: `fix/{{issue-description}}`
- Create via: `mcp_create_branch_for_feature(featureId)`

**Workflow:**
1. Create feature branch from `develop`
2. Work on todos in feature branch
3. Create PR when todos are `tested`
4. Merge to `develop` when PR approved
5. Update todos to `done` after merge

**Example branch names:**
- `feature/shopping-cart`
- `feature/user-authentication`
- `fix/payment-validation-bug`
""",
            conditions={"has_github_repo": True}
        ))
        
        # InTracker integration section (always included if using InTracker)
        self.sections.append(RulesSection(
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
        ))
        
        # When to ask user section (always included)
        self.sections.append(RulesSection(
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
        ))
    
    def generate_rules(self, project: Project, custom_instructions: Optional[str] = None) -> str:
        """Generate cursor rules for a project."""
        cursor_instructions = custom_instructions or project.cursor_instructions or ""
        
        # Build project-specific service list
        docker_services = self._get_docker_services(project)
        mcp_service = "  mcp-server: MCP Server (port 3001)" if self._uses_mcp(project) else ""
        frontend_service = "  frontend: React + Vite (port 5173)" if self._has_frontend(project) else ""
        uses_mcp = self._uses_mcp(project)
        
        # Build restart info sections
        backend_restart = self._get_backend_restart_info(project)
        frontend_restart = self._get_frontend_restart_info(project)
        mcp_restart = self._get_mcp_restart_info(project)
        
        # Generate rules content
        rules_content = f"""---
name: intracker-project-rules
description: Cursor AI instructions for {project.name}
version: {datetime.utcnow().isoformat()}
---

# Cursor Rules for {project.name}

{project.description or ''}

## Project Information

- **Project ID:** {project.id}
- **Status:** {project.status}
- **Tags:** {', '.join(project.tags) if project.tags else 'None'}
- **Technology Tags:** {', '.join(project.technology_tags) if project.technology_tags else 'None'}
- **GitHub:** {project.github_repo_url or 'Not connected'}

## Cursor Instructions

{cursor_instructions}

## Development Rules

### Environment Strategy

- **MVP Phase:** All development in local Docker environment
- **Post-MVP:** Deploy to Azure (staging → production)
- **Never deploy to Azure during MVP development**

"""
        
        # Add conditional sections
        for section in self.sections:
            if section.should_include(project):
                content = section.content
                # Replace placeholders
                content = content.replace("{DOCKER_SERVICES}", docker_services)
                content = content.replace("{FRONTEND_SERVICE}", frontend_service)
                content = content.replace("{MCP_SERVICE}", mcp_service)
                content = content.replace("{BACKEND_RESTART_INFO}", backend_restart)
                content = content.replace("{FRONTEND_RESTART_INFO}", frontend_restart)
                content = content.replace("{MCP_RESTART_INFO}", mcp_restart)
                # Replace conditional placeholders (for f-string-like behavior in sections)
                if "{uses_mcp}" in content:
                    content = content.replace("{uses_mcp}", str(uses_mcp))
                rules_content += content + "\n"
        
        # Add project-specific information
        rules_content += f"""
### Project-Specific Information

**This section is dynamically generated for each project:**
- Project ID: {project.id}
- Current status: {project.status}
- Active features: Check resume context
- Next todos: Check resume context
- Blockers: Check resume context
- Constraints: Check resume context

**To get latest project state:**
- `mcp_get_resume_context(projectId)` - Full current state
- `mcp_get_project_context(projectId)` - Complete project info
- `mcp_get_active_todos(projectId)` - Current todos

---

**Generated by InTracker MCP Server**
**Last updated:** {project.updated_at.isoformat() if project.updated_at else 'Unknown'}
**Project:** {project.name}
"""
        
        return rules_content
    
    def _uses_mcp(self, project: Project) -> bool:
        """Check if project uses MCP."""
        return project.technology_tags and "mcp" in [tag.lower() for tag in project.technology_tags]
    
    def _has_frontend(self, project: Project) -> bool:
        """Check if project has frontend."""
        frontend_tags = ["react", "vue", "angular", "svelte", "frontend"]
        if not project.technology_tags:
            return False
        return any(tag.lower() in [t.lower() for t in project.technology_tags] for tag in frontend_tags)
    
    def _get_docker_services(self, project: Project) -> str:
        """Get Docker services list based on project."""
        services = []
        if "postgres" in [tag.lower() for tag in (project.technology_tags or [])]:
            services.append("  postgres: postgres:16 (port 5433 → 5432)")
        if "redis" in [tag.lower() for tag in (project.technology_tags or [])]:
            services.append("  redis: redis:7-alpine (port 6379)")
        if "fastapi" in [tag.lower() for tag in (project.technology_tags or [])] or "python" in [tag.lower() for tag in (project.technology_tags or [])]:
            services.append("  backend: FastAPI (port 3000)")
        return "\n".join(services) if services else "  # No services defined"
    
    def _get_backend_restart_info(self, project: Project) -> str:
        """Get backend restart information."""
        if "fastapi" in [tag.lower() for tag in (project.technology_tags or [])] or "python" in [tag.lower() for tag in (project.technology_tags or [])]:
            return """- **Backend changes:** 
  - `docker-compose restart backend` (restarts container)
  - Backend code is mounted, but Python imports may need restart
  - Always restart after adding new files/modules
  - Check logs: `docker-compose logs backend --tail=50`"""
        return ""
    
    def _get_frontend_restart_info(self, project: Project) -> str:
        """Get frontend restart information."""
        if self._has_frontend(project):
            return """- **Frontend changes:** 
  - Auto-reloads with Vite (no restart needed)
  - If issues: `docker-compose restart frontend`"""
        return ""
    
    def _get_mcp_restart_info(self, project: Project) -> str:
        """Get MCP server restart information."""
        if self._uses_mcp(project):
            return """- **MCP server changes:**
  - `docker-compose restart mcp-server` (restarts container)
  - **CRITICAL:** After MCP server restart, user MUST reload MCP connection in Cursor
  - MCP server code is mounted, but Python imports may need restart
  - Check logs: `docker-compose logs mcp-server --tail=50`"""
        return ""
    
    def add_custom_section(self, section: RulesSection):
        """Add a custom rules section."""
        self.sections.append(section)
    
    def update_section(self, name: str, content: str, conditions: Optional[Dict] = None):
        """Update an existing section."""
        for section in self.sections:
            if section.name == name:
                section.content = content
                if conditions:
                    section.conditions = conditions
                return
        # If not found, add as new section
        self.sections.append(RulesSection(name, content, conditions))


# Global instance
rules_generator = RulesGenerator()

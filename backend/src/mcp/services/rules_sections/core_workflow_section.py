"""Core workflow section for cursor rules."""
from ..rules_section import RulesSection


def create_core_workflow_section() -> RulesSection:
    """Create core workflow section."""
    return RulesSection(
        name="core_workflow",
        content="""### Development Workflow (MANDATORY)

**Every agent MUST follow this workflow:**

1. **Project Identification (first time only):**
   - Use `mcp_identify_project_by_path` or `mcp_list_projects`
   - If no project exists, create: `mcp_create_project`
   - Save project ID for session

2. **Project Setup (NEW/EXISTING PROJECTS - first time only):**
   - **For NEW projects (no existing codebase):**
     - Project structure will be created manually as you work
     - Create elements and todos as needed: `mcp_create_todo(elementId, title, description)`
   
   - **For EXISTING projects (already has codebase):**
     - **Option A: Auto-parse file structure (RECOMMENDED):**
       - Use `mcp_parse_file_structure(projectId, projectPath?, maxDepth?, ignorePatterns?)`
       - Automatically creates hierarchical project elements from directory structure
       - Creates modules/components based on folders (max depth: 3 by default)
       - Ignores common patterns (node_modules, .git, __pycache__, etc.)
       - Only works if project has NO existing elements
     
     - **Option B: Import from GitHub (if GitHub repo connected):**
       - Connect GitHub repo first: `mcp_connect_github_repo(projectId, owner, repo)`
       - Import GitHub issues as todos: `mcp_import_github_issues(projectId, labels?, state?, createElements?)`
       - Import GitHub milestones as features: `mcp_import_github_milestones(projectId, state?)`
       - Issues become todos, milestones become features
     
     - **Option C: Analyze and get suggestions:**
       - Use `mcp_analyze_codebase(projectId, projectPath?)` to analyze codebase
       - Get suggestions for modules, components, tech stack detection
       - Then manually create elements or use `mcp_parse_file_structure`
   
   - **After setup:**
     - Project structure is ready with elements
     - Todos are imported or ready to be created
     - Continue with normal workflow

3. **Resume Context & Cursor Rules (first time only):**
   - Get resume context: `mcp_get_resume_context(projectId)`
     - Shows: Last session, next todos, active elements, blockers, constraints
   - Load cursor rules: `mcp_load_cursor_rules(projectId)`
     - Only needed first time or when rules change
     - Rules are saved to `.cursor/rules/intracker-project-rules.mdc`

4. **Branch Check (MANDATORY for feature work!):**
   - **🚨 CRITICAL: ALWAYS check branch before starting work on a feature!**
   - Check current branch: `git branch --show-current`
   - If working on a feature:
     - Get feature: `mcp_get_feature(featureId)`
     - Get feature branches: `mcp_get_feature_branches(featureId)`
     - If feature branch exists: `git checkout feature/{feature-name}` then `git pull origin feature/{feature-name}`
     - If NO feature branch: `mcp_create_branch_for_feature(featureId)` then `git checkout feature/{feature-name}`
   - If NOT working on a feature: Use `develop` branch
   - **NEVER start working on a feature without checking the branch first!**

5. **Work on Next Todo:**
   - Get next todos from resume context
   - **🚨 VERIFY BRANCH FIRST!** (see step 4 above)
   - Update status: `mcp_update_todo_status(todoId, "in_progress")`
   - Implement changes
   - Check for errors: `read_lints` tool
   - Fix syntax/import errors
   - Restart affected service if needed
   - Test functionality

6. **Update Todo Status:**
   - After implementation: `mcp_update_todo_status(todoId, "tested")` (only if tested!)
   - After merge to dev: `mcp_update_todo_status(todoId, "done")` (only after tested AND merged!)

7. **Git Workflow (MANDATORY - Follow this order!):**
   - **🚨 Before starting work - BRANCH CHECK (MANDATORY!):**
     - **ALWAYS check branch before starting work on a feature!**
     - Check current branch: `git branch --show-current`
     - If working on a feature:
       - Get feature: `mcp_get_feature(featureId)`
       - Get feature branches: `mcp_get_feature_branches(featureId)`
       - If feature branch exists:
         - Switch to it: `git checkout feature/{feature-name}`
         - Pull latest: `git pull origin feature/{feature-name}`
       - If NO feature branch exists:
         - Create it: `mcp_create_branch_for_feature(featureId)`
         - Switch to it: `git checkout feature/{feature-name}`
         - Pull latest: `git pull origin feature/{feature-name}`
     - If NOT working on a feature:
       - Use develop branch: `git checkout develop`
       - Pull latest: `git pull origin develop`
     - **NEVER start working on a feature without checking the branch first!**
   
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
   - **🚨 ALWAYS check branch before starting work on a feature!**
   - **NEVER start working on a feature without checking the branch first!**
   - **NEVER commit without testing first!**
   - **NEVER commit to main/master directly!** Always use feature branches
   - **NEVER commit on wrong branch** (e.g., develop when working on a feature)
   - **ALWAYS check git status before committing** to avoid committing wrong files
   - **ALWAYS use the commit message format** with feature ID
   - **ALWAYS push after committing** to keep remote in sync
   - **ALWAYS update todo status** after committing (tested) and after merge (done)
   - **NEVER mark todo as `done`** until it's tested AND merged to dev branch!
"""
    )

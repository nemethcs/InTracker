"""Git workflow section for cursor rules."""
from ..rules_section import RulesSection


def create_git_workflow_section() -> RulesSection:
    """Create git workflow section."""
    return RulesSection(
        name="git_workflow",
        content="""### Git Workflow (MANDATORY)

**CRITICAL: Follow this exact order for every change!**

#### 🚨 1. Before Starting Work - BRANCH CHECK (MANDATORY!)

**ALWAYS check branch before starting work on a feature!**

**CRITICAL: In Cursor + InTracker workflow, you work BOTH locally (git commands) AND via MCP (InTracker tracking)!**

```bash
# 1. Check current branch (LOCAL git command)
git branch --show-current

# 2. If working on a feature, MANDATORY:
#    a) Get feature info (MCP): mcp_get_feature(featureId)
#    b) Get feature branches (MCP): mcp_get_feature_branches(featureId)
#    c) If feature branch exists:
#       - Switch to it (LOCAL): git checkout feature/{feature-name}
#       - Pull latest (LOCAL): git pull origin feature/{feature-name}
#    d) If NO feature branch exists:
#       - Create it LOCALLY: git checkout -b feature/{feature-name} develop
#       - Push to GitHub (LOCAL): git push -u origin feature/{feature-name}
#       - Link to feature (MCP): mcp_link_branch_to_feature(featureId, "feature/{feature-name}")

# 3. If NOT working on a feature:
#    - Use develop branch (LOCAL): git checkout develop
#    - Pull latest (LOCAL): git pull origin develop
```

**NEVER start working on a feature without checking the branch first!**
**REMEMBER: Git commands run LOCALLY, MCP tools track progress in InTracker!**

#### 2. During Work

**CRITICAL: You work BOTH locally (code changes) AND via MCP (tracking)!**

- Make code changes (LOCAL - edit files)
- Test your changes (LOCAL - run tests)
- Check for errors: `read_lints` tool
- Fix any issues (LOCAL - edit files)
- Update todo status (MCP): `mcp_update_todo_status(todoId, "in_progress")`

**If user requests new work on a feature:**
- Create todo (MCP): `mcp_create_todo(elementId, title, description, featureId?, priority?)`
- Update todo status (MCP): `mcp_update_todo_status(todoId, "in_progress")`
- Implement changes (LOCAL - edit files)
- Test changes (LOCAL - run tests)
- Commit (LOCAL): `git commit -m "feat(scope): description [feature:featureId]"`
- Push (LOCAL): `git push origin feature/{feature-name}`
- Update todo status (MCP): `mcp_update_todo_status(todoId, "tested")` (only if tested!)
- After merge: `mcp_update_todo_status(todoId, "done")` (only after tested AND merged!)

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
# Push to remote (LOCAL git command)
git push origin {branch-name}

# Update todo status to tested (MCP - only if tested!)
mcp_update_todo_status(todoId, "tested")

# Link todo to PR if PR exists (MCP)
mcp_link_todo_to_pr(todoId, prNumber)
```

**REMEMBER:**
- Git commands (commit, push) run LOCALLY
- InTracker updates (todo status, PR linking) via MCP
- You work BOTH locally AND via MCP!

#### 6. After Merge to Dev

```bash
# Switch back to dev (LOCAL git command)
git checkout develop

# Pull latest (LOCAL git command)
git pull origin develop

# Update todo status to done (MCP - only after tested AND merged!)
mcp_update_todo_status(todoId, "done")
```

**REMEMBER:**
- Git merge happens LOCALLY (or via GitHub PR merge)
- InTracker status updates via MCP
- You work BOTH locally AND via MCP!

#### Git Rules (CRITICAL)

**ALWAYS:**
- ✅ **Check branch before starting work on a feature!**
- ✅ **Work BOTH locally (git commands) AND via MCP (InTracker tracking)!**
- ✅ Create branches LOCALLY: `git checkout -b feature/{name} develop`
- ✅ Link branches via MCP: `mcp_link_branch_to_feature(featureId, branchName)`
- ✅ Commit LOCALLY: `git commit -m "..."` then `git push`
- ✅ Update todo status via MCP: `mcp_update_todo_status(todoId, status)`
- ✅ Check git status before committing
- ✅ Use feature branches (never commit to main/master directly)
- ✅ Use the commit message format with feature ID
- ✅ Push after committing
- ✅ Update todo status after committing (tested) and after merge (done)
- ✅ Test before committing

**NEVER:**
- ❌ **Start working on a feature without checking the branch first!**
- ❌ Use `mcp_create_branch_for_feature` - create branches LOCALLY instead
- ❌ Commit without testing first
- ❌ Commit to main/master directly
- ❌ Commit on wrong branch (e.g., develop when working on a feature)
- ❌ Commit without checking git status
- ❌ Mark todo as `done` until it's tested AND merged to dev branch
- ❌ Skip pushing after committing
- ❌ Commit with wrong message format
- ❌ Forget to update InTracker via MCP after local git operations
""",
        conditions={"has_github_repo": True}
    )

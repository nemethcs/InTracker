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

```bash
# 1. Check current branch
git branch --show-current

# 2. If working on a feature, MANDATORY:
#    a) Get feature: mcp_get_feature(featureId)
#    b) Get feature branches: mcp_get_feature_branches(featureId)
#    c) If feature branch exists:
#       - Switch to it: git checkout feature/{feature-name}
#       - Pull latest: git pull origin feature/{feature-name}
#    d) If NO feature branch exists:
#       - Create it: mcp_create_branch_for_feature(featureId)
#       - Switch to it: git checkout feature/{feature-name}
#       - Pull latest: git pull origin feature/{feature-name}

# 3. If NOT working on a feature:
#    - Use develop branch: git checkout develop
#    - Pull latest: git pull origin develop
```

**NEVER start working on a feature without checking the branch first!**

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
- ✅ **Check branch before starting work on a feature!**
- ✅ Check git status before committing
- ✅ Use feature branches (never commit to main/master directly)
- ✅ Use the commit message format with feature ID
- ✅ Push after committing
- ✅ Update todo status after committing (tested) and after merge (done)
- ✅ Test before committing

**NEVER:**
- ❌ **Start working on a feature without checking the branch first!**
- ❌ Commit without testing first
- ❌ Commit to main/master directly
- ❌ Commit on wrong branch (e.g., develop when working on a feature)
- ❌ Commit without checking git status
- ❌ Mark todo as `done` until it's tested AND merged to dev branch
- ❌ Skip pushing after committing
- ❌ Commit with wrong message format
""",
        conditions={"has_github_repo": True}
    )

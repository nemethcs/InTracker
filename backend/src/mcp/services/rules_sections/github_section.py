"""GitHub section for cursor rules."""
from ..rules_section import RulesSection


def create_github_section() -> RulesSection:
    """Create GitHub section."""
    return RulesSection(
        name="github",
        content="""### GitHub Branch Strategy

**CRITICAL: In Cursor + InTracker workflow, you work BOTH locally (git commands) AND via MCP (InTracker tracking)!**

**Branch naming:**
- Feature branches: `feature/{{feature-name}}`
- Fix branches: `fix/{{issue-description}}`

**Branch Creation (LOCAL git + MCP linking):**
1. Create branch LOCALLY: `git checkout -b feature/{feature-name} develop`
2. Push to GitHub (LOCAL): `git push -u origin feature/{feature-name}`
3. Link to feature (MCP): `mcp_link_branch_to_feature(featureId, "feature/{feature-name}")`

**Workflow:**
1. Create feature branch LOCALLY from `develop`
2. Link branch to feature via MCP: `mcp_link_branch_to_feature(featureId, branchName)`
3. Work on todos in feature branch (LOCAL code changes + MCP status updates)
4. Commit LOCALLY: `git commit -m "feat(scope): description [feature:featureId]"`
5. Push LOCALLY: `git push origin feature/{feature-name}`
6. Update todo status via MCP: `mcp_update_todo_status(todoId, "tested")` (only if tested!)
7. Create PR via MCP: `mcp_create_github_pr(projectId, title, head, base, todoId?)`
8. Link todos to PR via MCP: `mcp_link_todo_to_pr(todoId, prNumber)`
9. After PR merge: Update todos to `done` via MCP: `mcp_update_todo_status(todoId, "done")`

**Branch Status Check (MCP):**
- Check branch status: `mcp_get_branch_status(projectId, branchName)`
- Get feature branches: `mcp_get_feature_branches(featureId)`

**Example branch names:**
- `feature/shopping-cart`
- `feature/user-authentication`
- `fix/payment-validation-bug`

**REMEMBER:**
- Git operations (branch creation, commits, push) run LOCALLY
- InTracker tracking (branch linking, todo status, PR creation) via MCP
- You work BOTH locally AND via MCP!
""",
        conditions={"has_github_repo": True}
    )

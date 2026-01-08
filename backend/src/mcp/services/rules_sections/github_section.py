"""GitHub section for cursor rules."""
from ..rules_section import RulesSection


def create_github_section() -> RulesSection:
    """Create GitHub section."""
    return RulesSection(
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
    )

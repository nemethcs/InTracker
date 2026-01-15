"""GitHub integration controller."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database.base import get_db
from src.api.middleware.auth import get_current_user
from src.services.project_service import project_service
from src.services.github_service import github_service
from src.services.branch_service import branch_service
from src.services.github_access_service import github_access_service
from src.api.schemas.github import (
    GitHubConnectRequest,
    GitHubRepoResponse,
    BranchResponse,
    BranchCreateRequest,
    CursorDeeplinkRequest,
    CursorDeeplinkResponse,
)

router = APIRouter(prefix="/github", tags=["github"])


@router.get("/repositories")
async def list_user_repositories(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all GitHub repositories accessible to the current user.
    
    Uses the user's GitHub OAuth token to fetch repositories.
    """
    from src.services.github_service import GitHubService
    
    user_id = UUID(current_user["user_id"])
    
    # Create GitHubService with user_id to use user's OAuth token
    user_github_service = GitHubService(user_id=user_id)
    
    if not user_github_service.client:
        print(f"⚠️  GitHub OAuth token not found for user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub OAuth token not configured. Please connect your GitHub account in Settings.",
        )
    
    print(f"✅ Fetching repositories for user {user_id}")
    repositories = user_github_service.list_user_repositories()
    print(f"✅ Found {len(repositories)} repositories for user {user_id}")
    
    return {
        "repositories": repositories,
        "count": len(repositories),
    }


@router.post("/generate-cursor-deeplink", response_model=CursorDeeplinkResponse)
async def generate_cursor_deeplink(
    request: CursorDeeplinkRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate a Cursor chat deeplink for importing a GitHub project.
    
    Args:
        request: Request containing repo_url and optional team_id
    """
    repo_url = request.repo_url
    team_id = request.team_id
    from src.services.github_service import GitHubService
    from src.services.cursor_deeplink_service import cursor_deeplink_service
    
    user_id = UUID(current_user["user_id"])
    
    # Parse repo owner and name from URL
    if not repo_url.startswith("https://github.com/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid GitHub repository URL. Must start with https://github.com/",
        )
    
    repo_parts = repo_url.replace("https://github.com/", "").split("/")
    if len(repo_parts) != 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid GitHub repository URL format. Expected: https://github.com/owner/repo",
        )
    
    owner, repo_name = repo_parts
    
    # Create GitHubService with user_id to use user's OAuth token
    user_github_service = GitHubService(user_id=user_id)
    
    if not user_github_service.client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub OAuth token not configured. Please connect your GitHub account in Settings.",
        )
    
    # Get repository branches
    branches = user_github_service.list_branches(owner=owner, repo=repo_name)
    
    # Identify feature branches (feature/*, feat/*, etc.)
    feature_branches = []
    feature_patterns = ["feature/", "feat/", "feature-", "feat-"]
    for branch in branches:
        branch_name = branch.get("name", "")
        if any(branch_name.startswith(pattern) for pattern in feature_patterns):
            feature_branches.append(branch_name)
    
    # Generate deeplink
    deeplink = cursor_deeplink_service.generate_project_import_deeplink(
        repo_url=repo_url,
        repo_owner=owner,
        repo_name=repo_name,
        team_id=str(team_id) if team_id else None,
        feature_branches=feature_branches if feature_branches else None,
    )
    
    return {
        "deeplink": deeplink,
        "repo_url": repo_url,
        "owner": owner,
        "repo_name": repo_name,
        "feature_branches": feature_branches,
    }


@router.post("/projects/{project_id}/connect", response_model=GitHubRepoResponse)
async def connect_github_repo(
    project_id: UUID,
    connect_data: GitHubConnectRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Connect a GitHub repository to a project."""
    # Check project access (owner only)
    if not project_service.check_user_access(
        db=db,
        user_id=UUID(current_user["user_id"]),
        project_id=project_id,
        required_role="owner",
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can connect GitHub repositories",
        )

    # Validate repo access
    if not github_service.validate_repo_access(
        owner=connect_data.owner,
        repo=connect_data.repo,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access GitHub repository. Check your token permissions.",
        )

    # Get repo info
    repo_info = github_service.get_repo_info(
        owner=connect_data.owner,
        repo=connect_data.repo,
    )

    if not repo_info:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch repository information",
        )

    # Update project with GitHub info
    project = project_service.get_project_by_id(db=db, project_id=project_id)
    if project:
        project.github_repo_url = repo_info["url"]
        project.github_repo_id = str(repo_info["id"])
        db.commit()

    return GitHubRepoResponse(**repo_info)


@router.get("/projects/{project_id}/repo", response_model=GitHubRepoResponse)
async def get_github_repo(
    project_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get GitHub repository information for a project."""
    # Check project access
    if not project_service.check_user_access(
        db=db,
        user_id=UUID(current_user["user_id"]),
        project_id=project_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this project",
        )

    project = project_service.get_project_by_id(db=db, project_id=project_id)
    if not project or not project.github_repo_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project does not have a connected GitHub repository",
        )

    # Parse repo owner and name
    repo_parts = project.github_repo_url.replace("https://github.com/", "").split("/")
    if len(repo_parts) != 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid GitHub repository URL format",
        )

    owner, repo = repo_parts

    repo_info = github_service.get_repo_info(owner=owner, repo=repo)
    if not repo_info:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch repository information",
        )

    return GitHubRepoResponse(**repo_info)


@router.get("/projects/access")
async def get_projects_access(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get list of projects with GitHub OAuth token access validation.
    
    Returns all projects the user has access to via team membership,
    along with information about whether the user's GitHub OAuth token
    has access to each project's GitHub repository.
    
    NOTE: This endpoint must be defined BEFORE /projects/{project_id}/branches
    to avoid path parameter conflicts.
    """
    user_id = UUID(current_user["user_id"])
    
    accessible_projects = github_access_service.validate_project_access_for_user(
        db=db,
        user_id=user_id,
    )
    
    return accessible_projects


@router.get("/projects/{project_id}/branches")
async def list_project_branches(
    project_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List branches for a project."""
    # Check project access
    if not project_service.check_user_access(
        db=db,
        user_id=UUID(current_user["user_id"]),
        project_id=project_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this project",
        )

    branches = branch_service.get_branches_by_project(db=db, project_id=project_id)

    return {
        "branches": [
            {
                "id": str(branch.id),
                "name": branch.branch_name,
                "sha": branch.last_commit_sha,
                "feature_id": str(branch.feature_id) if branch.feature_id else None,
                "status": branch.status,
            }
            for branch in branches
        ],
        "count": len(branches),
    }


@router.post("/branches", status_code=status.HTTP_201_CREATED)
async def create_branch(
    branch_data: BranchCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a branch for a feature."""
    # Get feature to get project_id
    from src.database.models import Feature
    feature = db.query(Feature).filter(Feature.id == branch_data.feature_id).first()
    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature not found",
        )

    # Check project access (editor or owner)
    if not project_service.check_user_access(
        db=db,
        user_id=UUID(current_user["user_id"]),
        project_id=feature.project_id,
        required_role="editor",
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create branches in this project",
        )

    try:
        branch = branch_service.create_branch_for_feature(
            db=db,
            project_id=feature.project_id,
            feature_id=branch_data.feature_id,
            branch_name=branch_data.branch_name,
            from_branch=branch_data.from_branch,
        )

        if not branch:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create branch",
            )

        return {
            "id": str(branch.id),
            "name": branch.branch_name,
            "sha": branch.last_commit_sha,
            "feature_id": str(branch.feature_id),
            "status": branch.status,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/branches/{branch_id}")
async def get_branch(
    branch_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get branch details."""
    branch = branch_service.get_branch_by_id(db=db, branch_id=branch_id)
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Branch not found",
        )

    # Check project access
    if not project_service.check_user_access(
        db=db,
        user_id=UUID(current_user["user_id"]),
        project_id=branch.project_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this branch's project",
        )

    # Get branch info from GitHub if available
    project = project_service.get_project_by_id(db=db, project_id=branch.project_id)
    branch_info = None
    if project and project.github_repo_url:
        repo_parts = project.github_repo_url.replace("https://github.com/", "").split("/")
        if len(repo_parts) == 2:
            owner, repo = repo_parts
            branch_info = github_service.get_branch(
                owner=owner,
                repo=repo,
                branch_name=branch.branch_name,
            )

    return {
        "id": str(branch.id),
        "name": branch.branch_name,
        "sha": branch.last_commit_sha,
        "feature_id": str(branch.feature_id) if branch.feature_id else None,
        "status": branch.status,
        "github_info": branch_info,
    }


@router.get("/features/{feature_id}/branches")
async def get_feature_branches(
    feature_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get branches for a feature."""
    from src.database.models import Feature
    feature = db.query(Feature).filter(Feature.id == feature_id).first()
    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature not found",
        )

    # Check project access
    if not project_service.check_user_access(
        db=db,
        user_id=UUID(current_user["user_id"]),
        project_id=feature.project_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this feature's project",
        )

    branches = branch_service.get_branches_by_feature(db=db, feature_id=feature_id)

    return {
        "branches": [
            {
                "id": str(branch.id),
                "name": branch.branch_name,
                "sha": branch.last_commit_sha,
                "status": branch.status,
            }
            for branch in branches
        ],
        "count": len(branches),
    }


@router.post("/webhook")
async def github_webhook(
    payload: dict,
    db: Session = Depends(get_db),
):
    """Handle GitHub webhook events."""
    # This is a simplified webhook handler
    # In production, you'd want to:
    # 1. Verify webhook signature
    # 2. Handle different event types (push, pull_request, issues, etc.)
    # 3. Update database accordingly

    event_type = payload.get("action") or payload.get("ref")
    print(f"📥 GitHub webhook received: {event_type}")

    # TODO: Implement webhook handling logic
    # - PR events: Update todo.github_pr_number
    # - Issue events: Update element.github_issue_number
    # - Branch events: Sync branches

    return {"status": "received"}

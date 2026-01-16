"""GitHub access validation service for projects."""
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.orm import Session
from src.database.models import Project, TeamMember, Team
from src.services.github_token_service import github_token_service
from src.services.github_service import GitHubService
from src.database.base import SessionLocal
import logging

logger = logging.getLogger(__name__)


class GitHubAccessService:
    """Service for validating GitHub OAuth token access to projects."""
    
    @staticmethod
    def validate_project_access_for_user(
        db: Session,
        user_id: UUID,
    ) -> List[Dict[str, Any]]:
        """Check GitHub OAuth token access for all projects in all teams the user belongs to.
        
        Args:
            db: Database session
            user_id: User UUID
            
        Returns:
            List of dictionaries with:
                - project_id: Project UUID
                - project_name: Project name
                - team_id: Team UUID
                - team_name: Team name
                - github_repo_url: GitHub repository URL (if connected)
                - has_access: Boolean indicating if user's token has access
                - access_level: Access level (read, write, admin, or None if no access)
        """
        # Get user's GitHub token
        token = github_token_service.get_user_token(db, user_id)
        logger.debug(f"GitHubAccessService: user_id={user_id}, token={'exists' if token else 'None'}")
        if not token:
            # User has no GitHub token, return all projects with has_access=False
            logger.warning(f"User {user_id} has no GitHub OAuth token, returning projects with has_access=False")
            return GitHubAccessService._get_all_user_projects_without_access(db, user_id)
        
        # Initialize GitHub service with user's token
        github_service = GitHubService(user_id=user_id)
        if not github_service.client:
            # GitHub client initialization failed, return all projects with has_access=False
            logger.warning(f"GitHub client initialization failed for user {user_id}")
            return GitHubAccessService._get_all_user_projects_without_access(db, user_id)
        
        # Get all teams the user belongs to
        user_teams = (
            db.query(Team)
            .join(TeamMember, Team.id == TeamMember.team_id)
            .filter(TeamMember.user_id == user_id)
            .all()
        )
        
        accessible_projects = []
        
        for team in user_teams:
            # Get all projects in this team
            team_projects = (
                db.query(Project)
                .filter(Project.team_id == team.id)
                .all()
            )
            
            for project in team_projects:
                project_info = {
                    "project_id": str(project.id),
                    "project_name": project.name,
                    "team_id": str(team.id),
                    "team_name": team.name,
                    "github_repo_url": project.github_repo_url,
                    "has_access": False,
                    "access_level": None,
                }
                
                # If project has no GitHub repo, mark as accessible (no GitHub dependency)
                if not project.github_repo_url:
                    project_info["has_access"] = True
                    project_info["access_level"] = "read"  # Default for non-GitHub projects
                    accessible_projects.append(project_info)
                    continue
                
                # Parse GitHub repo URL to get owner and repo name
                try:
                    owner, repo = GitHubService.parse_github_url(project.github_repo_url)
                    if owner and repo:
                        # Check repository access using GitHub API
                        has_access = github_service.validate_repo_access(owner, repo)
                        
                        if has_access:
                            # Try to get more detailed access level
                            repo_info = github_service.get_repo_info(owner, repo)
                            if repo_info:
                                # Determine access level based on repository permissions
                                # For now, we'll use a simple check - if we can read, it's at least read
                                # In the future, we could check if user has write/admin permissions
                                project_info["has_access"] = True
                                project_info["access_level"] = "read"  # Default, could be enhanced
                            else:
                                project_info["has_access"] = False
                        else:
                            project_info["has_access"] = False
                    else:
                        project_info["has_access"] = False
                except Exception as e:
                    logger.warning(f"Error validating access for project {project.id}: {e}")
                    project_info["has_access"] = False
                
                accessible_projects.append(project_info)
        
        return accessible_projects
    
    @staticmethod
    def _get_all_user_projects_without_access(
        db: Session,
        user_id: UUID,
    ) -> List[Dict[str, Any]]:
        """Get all projects for user without GitHub access validation.
        
        Used when user has no GitHub token or GitHub client initialization fails.
        """
        user_teams = (
            db.query(Team)
            .join(TeamMember, Team.id == TeamMember.team_id)
            .filter(TeamMember.user_id == user_id)
            .all()
        )
        
        projects = []
        for team in user_teams:
            team_projects = (
                db.query(Project)
                .filter(Project.team_id == team.id)
                .all()
            )
            
            for project in team_projects:
                projects.append({
                    "project_id": str(project.id),
                    "project_name": project.name,
                    "team_id": str(team.id),
                    "team_name": team.name,
                    "github_repo_url": project.github_repo_url,
                    "has_access": False,
                    "access_level": None,
                })
        
        return projects
    
    @staticmethod
    def validate_single_project_access(
        db: Session,
        user_id: UUID,
        project_id: UUID,
    ) -> Dict[str, Any]:
        """Validate GitHub OAuth token access for a single project.
        
        Args:
            db: Database session
            user_id: User UUID
            project_id: Project UUID
            
        Returns:
            Dictionary with:
                - has_access: Boolean indicating if user's token has access
                - access_level: Access level (read, write, admin, or None if no access)
                - error: Error message if validation failed
        """
        # Get project
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {
                "has_access": False,
                "access_level": None,
                "error": "Project not found",
            }
        
        # Check if user is member of project's team
        team_member = (
            db.query(TeamMember)
            .filter(
                TeamMember.team_id == project.team_id,
                TeamMember.user_id == user_id,
            )
            .first()
        )
        
        if not team_member:
            return {
                "has_access": False,
                "access_level": None,
                "error": "User is not a member of the project's team",
            }
        
        # If project has no GitHub repo, user has access (no GitHub dependency)
        if not project.github_repo_url:
            return {
                "has_access": True,
                "access_level": "read",
                "error": None,
            }
        
        # Get user's GitHub token
        token = github_token_service.get_user_token(db, user_id)
        if not token:
            return {
                "has_access": False,
                "access_level": None,
                "error": "User has no GitHub OAuth token",
            }
        
        # Initialize GitHub service with user's token
        github_service = GitHubService(user_id=user_id)
        if not github_service.client:
            return {
                "has_access": False,
                "access_level": None,
                "error": "Failed to initialize GitHub client",
            }
        
        # Parse GitHub repo URL
        try:
            owner, repo = GitHubService.parse_github_url(project.github_repo_url)
            if owner and repo:
                # Check repository access
                has_access = github_service.validate_repo_access(owner, repo)
                
                if has_access:
                    return {
                        "has_access": True,
                        "access_level": "read",  # Default, could be enhanced
                        "error": None,
                    }
                else:
                    return {
                        "has_access": False,
                        "access_level": None,
                        "error": "User's GitHub token does not have access to this repository",
                    }
            else:
                return {
                    "has_access": False,
                    "access_level": None,
                    "error": "Invalid GitHub repository URL format",
                }
        except Exception as e:
            return {
                "has_access": False,
                "access_level": None,
                "error": f"Error validating access: {str(e)}",
            }


# Global instance
github_access_service = GitHubAccessService()
